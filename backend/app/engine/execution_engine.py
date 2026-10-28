import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.models.change_record import ChangeRecord
from app.simulator.infra_sandbox import sandbox
from app.engine.audit_chain import record_audit_event
from app.engine.runbook_loader import runbook_registry

class ExecutionEngine:
    def __init__(self, sandbox_instance=sandbox):
        self.sb = sandbox_instance

    def execute_remediation(
        self,
        db: Session,
        incident_id: str,
        approver_name: Optional[str] = None,
        approver_type: str = "POLICY_ENGINE"
    ) -> Dict[str, Any]:
        """
        Executes runbook remediation with Pre-check -> Snapshot -> Execute -> Verify -> Auto-Rollback
        """
        start_time = time.time()
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return {"success": False, "error": f"Incident {incident_id} not found"}

        runbook = runbook_registry.get_runbook(inc.runbook_id)
        if not runbook:
            return {"success": False, "error": f"Runbook {inc.runbook_id} not found"}

        host_id = inc.host
        service = inc.service

        # 1. PRE-CHECK
        inc.status = "EXECUTING"
        db.commit()
        record_audit_event(
            db,
            event_type="PRE_CHECK",
            incident_id=inc.id,
            service=service,
            host=host_id,
            payload={"runbook_id": inc.runbook_id, "host": host_id, "service": service},
            actor=approver_name or "SYSTEM"
        )

        # 2. STATE SNAPSHOT
        primary_target = runbook.get("action_steps", [{}])[0].get("target", "/var/log")
        snapshot_obj = self.sb.snapshot(host_id, primary_target)
        inc.snapshot_data = json.dumps(snapshot_obj)
        db.commit()

        record_audit_event(
            db,
            event_type="SNAPSHOT_TAKEN",
            incident_id=inc.id,
            service=service,
            host=host_id,
            payload={"target": primary_target, "snapshot_summary": snapshot_obj.get("type")},
            actor="SYSTEM_ENGINE"
        )

        # 3. EXECUTE ACTION STEPS
        executed_steps = []
        diagnostics = json.loads(inc.diagnostic_details or "{}")
        simulated_failure = diagnostics.get("will_fail", False)

        for step in runbook.get("action_steps", []):
            executed_steps.append({
                "step": step.get("step"),
                "name": step.get("name"),
                "action": step.get("action"),
                "target": step.get("target"),
                "status": "COMPLETED"
            })

        # Apply mutations to the simulated sandbox
        self._apply_runbook_mutation(runbook, host_id, simulated_failure)

        inc.execution_details = json.dumps(executed_steps)
        db.commit()

        record_audit_event(
            db,
            event_type="ACTION_EXECUTED",
            incident_id=inc.id,
            service=service,
            host=host_id,
            payload={"steps_count": len(executed_steps), "steps": executed_steps},
            actor=approver_name or "SYSTEM_ENGINE"
        )

        # 4. POST-VERIFICATION
        inc.status = "VERIFYING"
        db.commit()

        verification_passed = not simulated_failure

        if not verification_passed:
            # 5. AUTOMATIC ROLLBACK
            failure_reason = diagnostics.get("failure_reason", "Post-action verification failed: Target metric did not improve to nominal threshold")
            inc.status = "ROLLED_BACK"
            inc.rollback_status = "EXECUTED"
            inc.rollback_reason = f"Automatic Rollback Triggered: {failure_reason}"
            db.commit()

            record_audit_event(
                db,
                event_type="VERIFICATION_FAILED",
                incident_id=inc.id,
                service=service,
                host=host_id,
                payload={"reason": failure_reason, "target": primary_target},
                actor="SYSTEM_ENGINE"
            )

            record_audit_event(
                db,
                event_type="ROLLBACK_INITIATED",
                incident_id=inc.id,
                service=service,
                host=host_id,
                payload={"reason": failure_reason, "snapshot_type": snapshot_obj.get("type")},
                actor="SYSTEM_ENGINE"
            )

            # Restore sandbox from snapshot
            self.sb.restore_snapshot(host_id, primary_target, snapshot_obj)

            record_audit_event(
                db,
                event_type="ROLLBACK_COMPLETED",
                incident_id=inc.id,
                service=service,
                host=host_id,
                payload={"restored_target": primary_target, "status": "PRISTINE_SNAPSHOT_RESTORED"},
                actor="SYSTEM_ENGINE"
            )

            # Generate ITIL Change Record (Rolled Back)
            duration_ms = int((time.time() - start_time) * 1000)
            chg = self._create_change_record(
                db=db,
                inc=inc,
                runbook=runbook,
                approver_type=approver_type,
                approver_name=approver_name or "PolicyEngine/Autonomous",
                execution_result="ROLLED_BACK",
                verification_outcome=f"FAILED: {failure_reason}. State safely reverted to pre-action snapshot.",
                rollback_executed=True,
                rollback_details=f"Automated rollback to snapshot {snapshot_obj.get('type')}",
                duration_ms=duration_ms
            )

            return {
                "success": False,
                "status": "ROLLED_BACK",
                "change_id": chg.id,
                "reason": failure_reason,
                "duration_ms": duration_ms
            }

        else:
            # 6. VERIFICATION PASSED & RESOLVED
            inc.status = "RESOLVED"
            inc.rollback_status = "NONE"
            db.commit()

            record_audit_event(
                db,
                event_type="VERIFICATION_PASSED",
                incident_id=inc.id,
                service=service,
                host=host_id,
                payload={"metric_status": "NOMINAL", "target": primary_target},
                actor="SYSTEM_ENGINE"
            )

            duration_ms = int((time.time() - start_time) * 1000)
            chg = self._create_change_record(
                db=db,
                inc=inc,
                runbook=runbook,
                approver_type=approver_type,
                approver_name=approver_name or "PolicyEngine/Autonomous",
                execution_result="SUCCESS",
                verification_outcome="PASS: All operational parameters verified within nominal thresholds.",
                rollback_executed=False,
                rollback_details="None (Remediation succeeded)",
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "status": "RESOLVED",
                "change_id": chg.id,
                "duration_ms": duration_ms
            }

    def manual_rollback(self, db: Session, incident_id: str, operator_name: str = "ops-admin", reason: str = "Operator requested manual reversion") -> Dict[str, Any]:
        """
        Manual rollback triggered by an operator from the UI.
        """
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return {"success": False, "error": "Incident not found"}

        snapshot_str = inc.snapshot_data
        if not snapshot_str or snapshot_str == "{}":
            return {"success": False, "error": "No snapshot available for manual rollback"}

        snapshot_obj = json.loads(snapshot_str)
        primary_target = snapshot_obj.get("target", "/var/log")
        
        # Restore sandbox
        self.sb.restore_snapshot(inc.host, primary_target, snapshot_obj)

        inc.status = "ROLLED_BACK"
        inc.rollback_status = "MANUAL_EXECUTED"
        inc.rollback_reason = reason
        db.commit()

        record_audit_event(
            db,
            event_type="MANUAL_ROLLBACK_EXECUTED",
            incident_id=inc.id,
            service=inc.service,
            host=inc.host,
            payload={"reason": reason, "restored_target": primary_target},
            actor=operator_name
        )

        return {"success": True, "status": "ROLLED_BACK", "reason": reason}

    def _apply_runbook_mutation(self, runbook: Dict[str, Any], host_id: str, will_fail: bool):
        if will_fail:
            return # Leave state broken so verification detects failure

        rb_id = runbook.get("id")
        host = self.sb.get_host(host_id)

        if rb_id == "rb-disk-full":
            if host and "/var/log" in host["disks"]:
                host["disks"]["/var/log"]["utilization_pct"] = 38.5
                host["disks"]["/var/log"]["used_gb"] = 38.5
                host["disks"]["/var/log"]["cause"] = "nominal"

        elif rb_id == "rb-stuck-worker":
            if host:
                host["workers"]["worker_process"]["status"] = "HEALTHY"
                host["workers"]["worker_process"]["heartbeat_age_sec"] = 1.5
                host["workers"]["worker_process"]["pid"] = 4920

        elif rb_id == "rb-queue-scaling":
            svc = self.sb.get_service("worker-cluster")
            if svc:
                svc["queue"]["replicas"] = 6
                svc["queue"]["drain_rate"] = 650
                svc["queue"]["queue_depth"] = 180

        elif rb_id == "rb-cert-rotation":
            svc = self.sb.get_service("api-gateway")
            if svc:
                svc["tls"]["cert_days_remaining"] = 90
                svc["tls"]["tls_handshake_status"] = "SUCCESS"
                svc["tls"]["cert_serial"] = f"ROT-{uuid.uuid4().hex[:8].upper()}"

        elif rb_id == "rb-log-rotation":
            if host and "/var/log" in host["disks"]:
                host["disks"]["/var/log"]["utilization_pct"] = 30.0

        elif rb_id == "rb-cache-flush":
            svc = self.sb.get_service("cache-cluster")
            if svc:
                svc["fragmentation_pct"] = 12.0
                svc["cache_hit_ratio"] = 96.0

        elif rb_id == "rb-db-pool-reset":
            svc = self.sb.get_service("database-cluster")
            if svc:
                svc["pool_utilization_pct"] = 28.0
                svc["idle_connections"] = 4
                svc["locks"] = 0

        elif rb_id == "rb-zombie-cleanup":
            if host:
                host["zombies"]["count"] = 0
                host["zombies"]["pids"] = []

        elif rb_id == "rb-failed-cron-retry":
            svc = self.sb.get_service("cron-scheduler")
            if svc:
                svc["last_exit_code"] = 0
                svc["failure_count"] = 0
                svc["locked"] = False

        elif rb_id == "rb-service-restart":
            svc = self.sb.get_service("api-gateway")
            if svc:
                svc["http_5xx_rate_pct"] = 0.08
                svc["latency_p95_ms"] = 38.0

    def _create_change_record(
        self,
        db: Session,
        inc: Incident,
        runbook: Dict[str, Any],
        approver_type: str,
        approver_name: str,
        execution_result: str,
        verification_outcome: str,
        rollback_executed: bool,
        rollback_details: str,
        duration_ms: int
    ) -> ChangeRecord:
        year = datetime.now(timezone.utc).year
        chg_id = f"CHG-{year}-{uuid.uuid4().hex[:6].upper()}"
        
        change_type = "STANDARD"
        if runbook.get("risk_tier", 1) >= 2:
            change_type = "NORMAL"
        if "EMERGENCY" in inc.title.upper():
            change_type = "EMERGENCY"

        record = ChangeRecord(
            id=chg_id,
            incident_id=inc.id,
            title=f"Automated Remediation: {runbook.get('name')} for {inc.id}",
            service=inc.service,
            host=inc.host,
            change_type=change_type,
            trigger_reason=inc.title,
            risk_tier=runbook.get("risk_tier", 1),
            approver_type=approver_type,
            approver_name=approver_name,
            planned_actions=json.dumps(runbook.get("action_steps", [])),
            execution_result=execution_result,
            verification_outcome=verification_outcome,
            rollback_executed=rollback_executed,
            rollback_details=rollback_details,
            duration_ms=duration_ms
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

execution_engine = ExecutionEngine()
