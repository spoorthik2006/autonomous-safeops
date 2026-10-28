import io
import time
import unittest
import sys
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/tests", tags=["Backend Test Suite"])

@router.post("/run")
def execute_backend_tests():
    """
    Executes the comprehensive backend test suite (18 safety and governance unit tests)
    and returns live execution telemetry and logs.
    """
    # Ensure paths
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    tests_dir = base_dir / "tests"
    backend_dir = base_dir / "backend"
    
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))

    from test_policy_engine import TestPolicyEngine
    from test_judgment_ambiguity import TestJudgmentAmbiguity
    from test_execution_and_rollback import TestExecutionAndRollback
    from test_blast_radius_and_credentials import TestBlastRadiusAndCredentials
    from test_audit_hash_chain import TestAuditHashChain

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestJudgmentAmbiguity))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionAndRollback))
    suite.addTests(loader.loadTestsFromTestCase(TestBlastRadiusAndCredentials))
    suite.addTests(loader.loadTestsFromTestCase(TestAuditHashChain))

    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)

    start_time = time.time()
    result = runner.run(suite)
    duration = round(time.time() - start_time, 3)

    output = stream.getvalue()
    passed_count = result.testsRun - len(result.failures) - len(result.errors)

    return {
        "success": result.wasSuccessful(),
        "total_tests": result.testsRun,
        "passed": passed_count,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "duration_sec": duration,
        "log_output": output,
        "summary": "ALL TESTS PASSED: Safety invariants, automatic rollback, ambiguity escalation, and cryptographic audit verified." if result.wasSuccessful() else "TESTS FAILED"
    }

@router.get("/status")
def get_test_status():
    return {
        "suite_name": "NightShift Safety Verification Suite",
        "registered_test_cases": 18,
        "coverage": [
            "Tier 0/1/2/3 Policy Enforcement",
            "Core Dump Ambiguity Guard (Never Guess)",
            "Pre-Check -> Snapshot -> Auto-Rollback Guarantee",
            "Hardware Global Kill-Switch & Per-Service Pause",
            "Blast-Radius Bounds & Least-Privilege Credential Scopes",
            "Tamper-Evident SHA-256 Audit Chain Verification"
        ]
    }
