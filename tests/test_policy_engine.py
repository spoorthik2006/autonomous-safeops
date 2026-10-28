import unittest
from datetime import datetime, timezone
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from test_db import create_test_session
from app.models.safety import SafetyState
from app.models.change_record import ChangeRecord
from app.engine.policy_engine import policy_engine, PolicyDecision

class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.db = create_test_session()

    def tearDown(self):
        self.db.close()

    def test_tier_0_auto_allow(self):
        """Tier 0 (e.g. routine log rotation or zombie reaping) should be ALLOWed automatically"""
        incident = {
            "title": "Log Rotation",
            "service": "host-system",
            "trigger_type": "disk_full",
            "runbook_id": "rb-log-rotation"
        }
        diagnostics = {"target_path": "/var/log", "cause": "logs", "confidence": 0.99}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.ALLOW)
        self.assertEqual(res["risk_tier"], 0)

    def test_tier_1_auto_allow(self):
        """Tier 1 (e.g. stuck worker) should be ALLOWed under rate limits"""
        incident = {
            "title": "Worker Hung",
            "service": "worker-cluster",
            "trigger_type": "stuck_worker",
            "runbook_id": "rb-stuck-worker"
        }
        diagnostics = {"status": "UNRESPONSIVE", "confidence": 0.95}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.ALLOW)
        self.assertEqual(res["risk_tier"], 1)

    def test_tier_2_requires_approval(self):
        """Tier 2 (e.g. cert rotation or service restart) MUST require human approval"""
        incident = {
            "title": "TLS Cert Expiry",
            "service": "api-gateway",
            "trigger_type": "cert_expiring",
            "runbook_id": "rb-cert-rotation"
        }
        diagnostics = {"cert_days_remaining": 5}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.REQUIRE_APPROVAL)
        self.assertEqual(res["risk_tier"], 2)

    def test_tier_3_protected_target_denied(self):
        """Tier 3 protected targets (/etc, prod-db-primary) MUST be strictly DENIED"""
        incident = {
            "title": "Modify System Config",
            "service": "prod-db-primary",
            "trigger_type": "security_violation",
            "runbook_id": "rb-disk-full"
        }
        diagnostics = {"target_path": "/etc/sudoers"}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "PROTECTED_TARGET_TIER_3")

    def test_global_kill_switch_blocks_all(self):
        """Engaging the kill-switch halts all automated actions instantaneously"""
        safety = self.db.query(SafetyState).filter(SafetyState.id == 1).first()
        safety.kill_switch_active = True
        safety.kill_switch_reason = "Test emergency halt"
        self.db.commit()

        incident = {
            "title": "Routine Cleanup",
            "service": "host-system",
            "trigger_type": "disk_full",
            "runbook_id": "rb-log-rotation"
        }
        diagnostics = {"target_path": "/var/log", "cause": "logs"}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "GLOBAL_KILL_SWITCH_ACTIVE")

    def test_service_rate_limit(self):
        """Exceeding 5 actions per hour on a single service must be DENIED"""
        # Seed 5 recent actions for 'worker-cluster'
        now = datetime.now(timezone.utc)
        for i in range(5):
            chg = ChangeRecord(
                id=f"CHG-RATE-TEST-{i}",
                incident_id=f"INC-{i}",
                title="Past action",
                service="worker-cluster",
                host="host-01",
                trigger_reason="Test rate limit",
                created_at=now
            )
            self.db.add(chg)
        self.db.commit()

        incident = {
            "title": "Worker Hung",
            "service": "worker-cluster",
            "trigger_type": "stuck_worker",
            "runbook_id": "rb-stuck-worker"
        }
        diagnostics = {"status": "UNRESPONSIVE"}
        res = policy_engine.evaluate(self.db, incident, diagnostics)
        self.assertEqual(res["decision"], PolicyDecision.DENY)
        self.assertEqual(res["rule_name"], "SERVICE_RATE_LIMIT_EXCEEDED")

if __name__ == "__main__":
    unittest.main()
