from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class PayBenchEntrypointTest(unittest.TestCase):
    def test_cli_scores_external_attempts_without_touching_internal_suite(self) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = json.loads(
            (
                root / "samples" / "external" / "paybench" / "phase1_selected_10.json"
            ).read_text(encoding="utf-8")
        )
        attempts = {
            item["scenario_id"]: {
                "decision": {
                    "purchase": "ALLOW",
                    "ask_approval": "CONFIRMATION_REQUIRED",
                    "refuse": "DENY",
                }[item["local_primary_action"]],
                "observed_effects": [],
            }
            for item in fixture["challenges"]
        }

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            attempts_path = tmp_path / "attempts.json"
            output_path = tmp_path / "paybench_report.json"
            attempts_path.write_text(
                json.dumps({"attempts": attempts}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_paybench_challenges.py",
                    "--attempts",
                    str(attempts_path),
                    "--output",
                    str(output_path),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("PayBench: total=10 passed=10 failed=0", completed.stdout)
        self.assertIn("unsafe_proceed=0", completed.stdout)
        self.assertIn("refused_when_safe=0", completed.stdout)
        self.assertEqual("PASS", report["status"])
        self.assertNotIn("internal_regression", report)

    def test_cli_can_run_current_rules_and_report_partial_coverage(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "current_rules_report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_paybench_challenges.py",
                    "--current-rules",
                    "--output",
                    str(output_path),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("supported=6 unsupported=4", completed.stdout)
        self.assertIn("supported_passed=6 supported_failed=0", completed.stdout)
        self.assertEqual("PARTIAL", report["status"])
        self.assertEqual(6, report["summary"]["supported"])
        self.assertEqual(4, report["summary"]["unsupported"])
        self.assertEqual(
            4,
            len(report["unsupported_scenario_ids"]),
        )


if __name__ == "__main__":
    unittest.main()
