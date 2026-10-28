import unittest
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from test_db import create_test_session
from app.models.incident import Incident
from app.models.safety import SafetyState
from app.simulator.infra_sandbox import sandbox
from app.engine.execution_engine import execution_engine

class TestExecutionAndRollback(unittest.TestCase):
    def setUp(self):
        self.db = create_test_session()
        sandbox.reset()

    def tearDown(self):
        self.db.close()

    def test_successful_remediation_lifecycle(self):
        """Pre-check -> Snapshot -> Execute -> Verify PASS -> RESOLVED"""
        # Inject hung worker state into sandbox
        host = sandbox.get_host("host-01")
        host["workers"]["worker_process"]["status"] = "UNRESPONSIVE"

        inc = Incident(
            id="INC-TEST-SUCCESS",
            title="Hung Worker Test",
            service="worker-cluster",
            host="host-01",
            trigger_type="stuck_worker",
            runbook_id="rb-stuck-worker",
            status="DETECTED",
            risk_tier=1,
            diagnostic_details=json.dumps({"will_fail": False})
        )
        self.db.add(inc)
        self.db.commit()

        res = execution_engine.execute_remediation(self.db, inc.id)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "RESOLVED")

        # Verify incident DB record
        self.db.refresh(inc)
        self.assertEqual(inc.status, "RESOLVED")
        self.assertEqual(inc.rollback_status, "NONE")
        self.assertNotEqual(inc.snapshot_data, "{}")

        # Verify sandbox updated to HEALTHY
        self.assertEqual(host["workers"]["worker_process"]["status"], "HEALTHY")

    def test_failed_verification_triggers_automatic_rollback(self):
        """When post-check verification fails, execution engine MUST auto-rollback and restore snapshot"""
        host = sandbox.get_host("host-02")
        original_pid = 7711
        host["workers"]["worker_process"]["pid"] = original_pid
        host["workers"]["worker_process"]["status"] = "UNRESPONSIVE"

        # will_fail = True simulates condition where the restart fails or panics
        inc = Incident(
            id="INC-TEST-FAIL-ROLLBACK",
            title="Deadlocked Worker Test",
            service="worker-cluster",
            host="host-02",
            trigger_type="stuck_worker",
            runbook_id="rb-stuck-worker",
            status="DETECTED",
            risk_tier=1,
            diagnostic_details=json.dumps({
                "will_fail": True,
                "failure_reason": "Process exited with code 127 during post-restart probe"
            })
        )
        self.db.add(inc)
        self.db.commit()

        res = execution_engine.execute_remediation(self.db, inc.id)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "ROLLED_BACK")

        # Verify incident status is ROLLED_BACK
        self.db.refresh(inc)
        self.assertEqual(inc.status, "ROLLED_BACK")
        self.assertEqual(inc.rollback_status, "EXECUTED")
        self.assertIn("Automatic Rollback Triggered", inc.rollback_reason)

        # Verify sandbox snapshot was restored back to original_pid
        self.assertEqual(host["workers"]["worker_process"]["pid"], original_pid)

    def test_manual_operator_rollback(self):
        """An operator can manually trigger rollback on an incident with a saved snapshot"""
        # First create a resolved incident with a snapshot
        host = sandbox.get_host("host-01")
        initial_disk = {"total_gb": 100.0, "used_gb": 85.0, "utilization_pct": 85.0}
        host["disks"]["/var/log"] = initial_disk

        snapshot_obj = {"type": "disk", "target": "/var/log", "data": initial_disk}

        inc = Incident(
            id="INC-MANUAL-RB",
            title="Log Cleanup",
            service="host-system",
            host="host-01",
            trigger_type="disk_full",
            runbook_id="rb-disk-full",
            status="RESOLVED",
            snapshot_data=json.dumps(snapshot_obj)
        )
        self.db.add(inc)
        self.db.commit()

        # Mutate disk to something else
        host["disks"]["/var/log"]["utilization_pct"] = 35.0

        # Trigger manual rollback
        res = execution_engine.manual_rollback(
            self.db,
            incident_id=inc.id,
            operator_name="ops-director",
            reason="Suspected regression in log collector pipeline"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "ROLLED_BACK")

        # Verify disk restored back to 85.0%
        self.assertEqual(host["disks"]["/var/log"]["utilization_pct"], 85.0)

if __name__ == "__main__":
    unittest.main()
