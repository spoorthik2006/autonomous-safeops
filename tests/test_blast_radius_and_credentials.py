import unittest
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from test_db import create_test_session
from app.models.safety import SafetyState
from app.engine.policy_engine import policy_engine, PolicyDecision

class TestBlastRadiusAndCredentials(unittest.TestCase):
    def setUp(self):
        self.db = create_test_session()

    def tearDown(self):
        self.db.close()

    def test_blast_radius_host_limit_enforced(self):
        """Setting max_hosts_per_action to 1 denies runbooks attempting multi-host operations"""
        safety = self.db.query(SafetyState).filter(SafetyState.id == 1).first()
        safety.max_hosts_per_action = 1
        self.db.commit()

        # rb-queue-scaling requires max_hosts = 2
        incident = {
            "title": "Scale Queue",
            "service": "worker-cluster",
            "trigger_type": "queue_backlog",
            "runbook_id": "rb-queue-scaling"
        }
        res = policy_engine.evaluate(self.db, incident, {})
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "BLAST_RADIUS_MAX_HOSTS_EXCEEDED")

    def test_least_privilege_credential_scope_enforced(self):
        """An action submitted with an unauthorized token must be DENIED"""
        incident = {
            "title": "Stuck Worker Restart",
            "service": "worker-cluster",
            "trigger_type": "stuck_worker",
            "runbook_id": "rb-stuck-worker" # requires 'worker:restart'
        }
        # Provide token-read-only which only has 'disk:read_only'
        res = policy_engine.evaluate(
            self.db,
            incident,
            {},
            token_id="token-read-only"
        )
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "LEAST_PRIVILEGE_SCOPE_MISMATCH")
        self.assertIn("Least-privilege violation", res["reason"])

    def test_service_pause_blocks_remediation(self):
        """When an operator pauses a service, all remediations on that service must be DENIED"""
        safety = self.db.query(SafetyState).filter(SafetyState.id == 1).first()
        safety.paused_services_json = json.dumps(["worker-cluster"])
        self.db.commit()

        incident = {
            "title": "Stuck Worker Restart",
            "service": "worker-cluster",
            "trigger_type": "stuck_worker",
            "runbook_id": "rb-stuck-worker"
        }
        res = policy_engine.evaluate(self.db, incident, {})
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "SERVICE_PAUSED")

if __name__ == "__main__":
    unittest.main()
