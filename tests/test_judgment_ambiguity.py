import unittest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from test_db import create_test_session
from app.engine.policy_engine import policy_engine, PolicyDecision

class TestJudgmentAmbiguity(unittest.TestCase):
    def setUp(self):
        self.db = create_test_session()

    def tearDown(self):
        self.db.close()

    def test_disk_full_routine_logs_is_allowed(self):
        """When cause is confirmed to be rotation-eligible logs, engine allows remediation"""
        incident = {
            "title": "Disk Full /var/log",
            "service": "host-system",
            "trigger_type": "disk_full",
            "runbook_id": "rb-disk-full"
        }
        diagnostics = {
            "target_path": "/var/log",
            "cause": "logs",
            "confidence": 0.98
        }
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.ALLOW)

    def test_disk_full_core_dump_must_escalate(self):
        """When disk full is caused by core dumps, engine must ESCALATE to prevent erasing crash dumps"""
        incident = {
            "title": "Disk Full /data/core",
            "service": "host-system",
            "trigger_type": "disk_full",
            "runbook_id": "rb-disk-full"
        }
        diagnostics = {
            "target_path": "/data/core",
            "cause": "core_dump",
            "confidence": 0.95
        }
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.ESCALATE)
        self.assertEqual(res["rule_name"], "JUDGMENT_CORE_DUMP_ESCALATE")
        self.assertIn("crash core dumps", res["reason"])

    def test_disk_full_unknown_cause_must_escalate(self):
        """When cause is unknown or low confidence, engine MUST NOT guess; must ESCALATE"""
        incident = {
            "title": "Disk Full Mystery",
            "service": "host-system",
            "trigger_type": "disk_full",
            "runbook_id": "rb-disk-full"
        }
        diagnostics = {
            "target_path": "/var/log",
            "cause": "unknown",
            "confidence": 0.35
        }
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.ESCALATE)
        self.assertEqual(res["rule_name"], "JUDGMENT_AMBIGUOUS_CAUSE_ESCALATE")
        self.assertIn("never guesses", res["reason"])

if __name__ == "__main__":
    unittest.main()
