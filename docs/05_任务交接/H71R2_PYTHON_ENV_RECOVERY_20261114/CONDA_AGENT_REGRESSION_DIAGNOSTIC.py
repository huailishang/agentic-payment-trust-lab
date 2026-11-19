"""Offline Windows conda agent diagnostic. Not an official L3 Gate.

Only the current Python process gets a temporary local 'tests' package.
No changes to installed packages, project source/tests, or frozen runners.
"""
from __future__ import annotations
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
assert (ROOT / "tests" / "test_stripe_checkout_adapter.py").is_file()
sys.path.insert(0, str(ROOT / "src"))
package = types.ModuleType("tests")
package.__path__ = [str(ROOT / "tests")]
package.__package__ = "tests"
sys.modules["tests"] = package
MODULES = [
    "tests.test_stripe_checkout_adapter",
    "tests.test_stripe_checkout_lab",
    "tests.test_order_validation",
    "tests.test_payment_recovery",
    "tests.test_lifecycle",
    "tests.trusted_execution.test_governed_action",
    "tests.trusted_execution.test_context_policy",
]
if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
