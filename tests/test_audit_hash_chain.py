import unittest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from test_db import create_test_session
from app.models.audit import AuditEvent
from app.engine.audit_chain import record_audit_event, verify_chain_integrity, GENESIS_HASH

class TestAuditHashChain(unittest.TestCase):
    def setUp(self):
        self.db = create_test_session()

    def tearDown(self):
        self.db.close()

    def test_empty_chain_is_valid(self):
        """Empty audit ledger is valid by default"""
        res = verify_chain_integrity(self.db)
        self.assertTrue(res["valid"])
        self.assertEqual(res["total_events"], 0)

    def test_chain_continuity(self):
        """Sequential audit events form an unbroken cryptographic chain"""
        ev1 = record_audit_event(self.db, "EVENT_1", payload={"step": 1})
        self.assertEqual(ev1.prev_hash, GENESIS_HASH)

        ev2 = record_audit_event(self.db, "EVENT_2", payload={"step": 2})
        self.assertEqual(ev2.prev_hash, ev1.curr_hash)

        ev3 = record_audit_event(self.db, "EVENT_3", payload={"step": 3})
        self.assertEqual(ev3.prev_hash, ev2.curr_hash)

        # Verify integrity
        res = verify_chain_integrity(self.db)
        self.assertTrue(res["valid"])
        self.assertEqual(res["total_events"], 3)
        self.assertEqual(res["latest_hash"], ev3.curr_hash)

    def test_tamper_detection(self):
        """Tampering with an existing audit event's payload MUST break chain integrity"""
        ev1 = record_audit_event(self.db, "INIT", payload={"status": "nominal"})
        ev2 = record_audit_event(self.db, "MUTATION", payload={"status": "modified"})
        ev3 = record_audit_event(self.db, "VERIFY", payload={"status": "verified"})

        # Initial check passes
        res_initial = verify_chain_integrity(self.db)
        self.assertTrue(res_initial["valid"])

        # Adversary attempts to tamper with ev2's payload retroactively
        ev2.payload_json = '{"status": "falsified_by_attacker"}'
        self.db.commit()

        # Chain verification MUST fail
        res_tampered = verify_chain_integrity(self.db)
        self.assertFalse(res_tampered["valid"])
        self.assertEqual(res_tampered["broken_at_id"], ev2.id)
        self.assertIn("Cryptographic integrity failure", res_tampered["error"])

if __name__ == "__main__":
    unittest.main()
