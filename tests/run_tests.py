import unittest
import sys
from pathlib import Path

# Add backend and tests to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "tests"))

def run_all_tests():
    print("=" * 70)
    print(" NIGHTSHIFT COMPREHENSIVE TEST SUITE (AO-04 OPERATIONAL SAFETY)")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    from test_policy_engine import TestPolicyEngine
    from test_judgment_ambiguity import TestJudgmentAmbiguity
    from test_execution_and_rollback import TestExecutionAndRollback
    from test_blast_radius_and_credentials import TestBlastRadiusAndCredentials
    from test_audit_hash_chain import TestAuditHashChain

    suite.addTests(loader.loadTestsFromTestCase(TestPolicyEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestJudgmentAmbiguity))
    suite.addTests(loader.loadTestsFromTestCase(TestExecutionAndRollback))
    suite.addTests(loader.loadTestsFromTestCase(TestBlastRadiusAndCredentials))
    suite.addTests(loader.loadTestsFromTestCase(TestAuditHashChain))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 70)
    if result.wasSuccessful():
        print(f" ALL {result.testsRun} TESTS PASSED! NightShift safety engine verified.")
        return 0
    else:
        print(f" FAILED: {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
