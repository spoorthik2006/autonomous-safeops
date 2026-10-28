import asyncio
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.simulator.infra_sandbox import sandbox
from app.simulator.fault_injector import fault_injector
from app.models.incident import Incident
from app.models.approval import ApprovalRequest
from app.schemas.schemas import FaultInjectionRequest
from app.engine.policy_engine import policy_engine, PolicyDecision
from app.engine.execution_engine import execution_engine
from app.engine.audit_chain import record_audit_event
from app.engine.runbook_loader import runbook_registry
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/api/simulator", tags=["Simulator & Fault Injector"])

@router.get("/infra")
def get_infra_telemetry():
    return sandbox.get_state()

@router.post("/reset")
async def reset_infra(db: Session = Depends(get_db)):
    sandbox.reset()
    record_audit_event(
        db,
        event_type="INFRA_RESET",
        actor="OPS_ADMIN",
        payload={"message": "Infrastructure simulator reset to pristine nominal state"}
    )
    await ws_manager.broadcast({
        "event": "INFRA_RESET",
        "data": sandbox.get_state()
    })
    return {"success": True, "message": "Infrastructure reset to pristine nominal state"}

async def process_fault_injection(
    db: Session,
    fault_type: str,
    host: str = "host-01",
    service: Optional[str] = None,
    custom_params: Optional[dict] = None
) -> dict:
    # 1. Inject fault into sandbox
    meta, diag = fault_injector.inject_fault(fault_type, host, service, custom_params)

    # 2. Persist Incident
    inc = Incident(
        id=meta["id"],
        title=meta["title"],
        service=meta["service"],
        host=meta["host"],
        trigger_type=meta["trigger_type"],
        status="DETECTED",
        risk_tier=meta.get("risk_tier", 1),
        runbook_id=meta.get("runbook_id"),
        diagnostic_details=json.dumps(diag)
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    record_audit_event(
        db,
        event_type="INCIDENT_DETECTED",
        incident_id=inc.id,
        service=inc.service,
        host=inc.host,
        payload={"title": inc.title, "diagnostics": diag},
        actor="MONITORING_DAEMON"
    )

    await ws_manager.broadcast({
        "event": "INCIDENT_DETECTED",
        "data": inc.to_dict()
    })

    # 3. Policy Evaluation
    policy_res = policy_engine.evaluate(
        db=db,
        incident=inc.to_dict(),
        diagnostics=diag,
        token_id=custom_params.get("token_id") if custom_params else None
    )

    inc.decision = policy_res["decision"]
    inc.decision_reason = policy_res["reason"]
    inc.risk_tier = policy_res["risk_tier"]
    db.commit()

    record_audit_event(
        db,
        event_type="POLICY_EVALUATED",
        incident_id=inc.id,
        service=inc.service,
        host=inc.host,
        payload=policy_res,
        actor="POLICY_ENGINE"
    )

    # 4. Handle Decision
    decision = policy_res["decision"]

    if decision == PolicyDecision.ALLOW:
        inc.status = "EXECUTING"
        db.commit()
        await ws_manager.broadcast({
            "event": "INCIDENT_UPDATED",
            "data": inc.to_dict()
        })

        # Run execution engine
        exec_res = execution_engine.execute_remediation(
            db=db,
            incident_id=inc.id,
            approver_name="PolicyEngine/Autonomous",
            approver_type="POLICY_ENGINE"
        )
        db.refresh(inc)
        await ws_manager.broadcast({
            "event": "INCIDENT_UPDATED",
            "data": inc.to_dict()
        })
        return {
            "incident": inc.to_dict(),
            "policy": policy_res,
            "execution": exec_res
        }

    elif decision == PolicyDecision.REQUIRE_APPROVAL:
        inc.status = "PENDING_APPROVAL"
        db.commit()

        runbook = runbook_registry.get_runbook(inc.runbook_id) or {}
        approval = ApprovalRequest(
            id=f"APR-{uuid.uuid4().hex[:8].upper()}",
            incident_id=inc.id,
            runbook_id=inc.runbook_id or "unknown",
            service=inc.service,
            host=inc.host,
            proposed_action=f"Execute Runbook: {runbook.get('name', inc.runbook_id)}",
            action_steps_json=json.dumps(runbook.get("action_steps", [])),
            risk_tier=policy_res["risk_tier"],
            blast_radius_summary=f"Targets {runbook.get('blast_radius', {}).get('max_hosts', 1)} host(s) within service '{inc.service}'",
            rollback_plan_summary=f"Automated reversion available ({len(runbook.get('rollback_steps', []))} rollback steps defined)",
            status="PENDING"
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)

        record_audit_event(
            db,
            event_type="APPROVAL_REQUESTED",
            incident_id=inc.id,
            service=inc.service,
            host=inc.host,
            payload={"approval_id": approval.id, "proposed_action": approval.proposed_action},
            actor="POLICY_ENGINE"
        )

        await ws_manager.broadcast({
            "event": "APPROVAL_REQUESTED",
            "data": approval.to_dict()
        })
        await ws_manager.broadcast({
            "event": "INCIDENT_UPDATED",
            "data": inc.to_dict()
        })

        return {
            "incident": inc.to_dict(),
            "policy": policy_res,
            "approval": approval.to_dict()
        }

    elif decision == PolicyDecision.ESCALATE:
        inc.status = "ESCALATED"
        db.commit()

        record_audit_event(
            db,
            event_type="INCIDENT_ESCALATED",
            incident_id=inc.id,
            service=inc.service,
            host=inc.host,
            payload={"reason": policy_res["reason"]},
            actor="POLICY_ENGINE"
        )

        await ws_manager.broadcast({
            "event": "INCIDENT_UPDATED",
            "data": inc.to_dict()
        })

        return {
            "incident": inc.to_dict(),
            "policy": policy_res
        }

    else: # DENY
        inc.status = "DENIED"
        db.commit()

        record_audit_event(
            db,
            event_type="INCIDENT_DENIED",
            incident_id=inc.id,
            service=inc.service,
            host=inc.host,
            payload={"reason": policy_res["reason"]},
            actor="POLICY_ENGINE"
        )

        await ws_manager.broadcast({
            "event": "INCIDENT_UPDATED",
            "data": inc.to_dict()
        })

        return {
            "incident": inc.to_dict(),
            "policy": policy_res
        }

@router.post("/inject")
async def inject_fault_endpoint(payload: FaultInjectionRequest, db: Session = Depends(get_db)):
    result = await process_fault_injection(
        db=db,
        fault_type=payload.fault_type,
        host=payload.host or "host-01",
        service=payload.service,
        custom_params=payload.custom_params
    )
    return result

@router.post("/run-demo-scenario")
async def run_demo_scenario(db: Session = Depends(get_db)):
    """
    Executes a curated 10-fault end-to-end demonstration showcasing every aspect of NightShift:
    1. Routine log overflow -> Auto-remediation (ALLOW Tier 0)
    2. Ambiguous disk spike (Core dumps) -> ESCALATE (never guess)
    3. Protected target tamper (/etc/sudoers) -> DENY (Tier 3)
    4. Stuck background worker -> Auto-restart & verify (ALLOW Tier 1)
    5. Failing worker fix -> Pre-check -> Snapshot -> Execute -> Post-verify FAILS -> Auto-Rollback!
    6. Queue consumer backlog -> Scale consumers (ALLOW Tier 1)
    7. Expiring TLS cert -> High-impact -> REQUIRE_APPROVAL (Tier 2)
    8. Zombie process saturation -> Auto-reap (ALLOW Tier 0)
    9. Unknown root cause disk full -> ESCALATE (Ambiguity guard)
    10. Service 5xx spike -> Rolling restart -> REQUIRE_APPROVAL (Tier 2)
    """
    scenario_faults = [
        {"fault": "routine_log_overflow", "host": "host-01", "name": "1. Routine Log Overflow (Auto Tier 0)"},
        {"fault": "ambiguous_disk_full", "host": "host-02", "name": "2. Ambiguous Core Dumps (Escalate Guard)"},
        {"fault": "protected_path_tamper", "host": "host-03", "name": "3. Protected /etc Modification (Tier 3 Deny)"},
        {"fault": "stuck_worker", "host": "host-01", "name": "4. Stuck Worker Restart (Auto Tier 1)"},
        {"fault": "failed_fix_worker", "host": "host-02", "name": "5. Failing Worker Remediation (Auto-Rollback)"},
        {"fault": "queue_backlog", "host": "host-01", "name": "6. Kafka Queue Backlog Scaling (Auto Tier 1)"},
        {"fault": "cert_expiring", "host": "host-01", "name": "7. TLS Certificate Expiry (Tier 2 Approval)"},
        {"fault": "zombie_leak", "host": "host-03", "name": "8. Zombie Process Cleanup (Auto Tier 0)"},
        {"fault": "unknown_disk_full", "host": "host-02", "name": "9. Unclassified Spike (Ambiguity Escalate)"},
        {"fault": "service_5xx_spike", "host": "host-01", "name": "10. API Gateway 5xx Degraded (Tier 2 Approval)"}
    ]

    results = []
    for item in scenario_faults:
        res = await process_fault_injection(
            db=db,
            fault_type=item["fault"],
            host=item["host"]
        )
        results.append({
            "name": item["name"],
            "result": res
        })
        # Brief pause between scenario steps for smooth real-time stream
        await asyncio.sleep(0.3)

    return {
        "success": True,
        "scenario_count": len(results),
        "results": results
    }
