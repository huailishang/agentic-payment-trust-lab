from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class AttackOverlayEntrypointTest(unittest.TestCase):
    def test_cli_runs_attack_overlay_v1_and_writes_report(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "attack_overlay_report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/validation/run_attack_overlays.py",
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
        self.assertIn("Attack Overlay v1: total=6 passed=6 failed=0", completed.stdout)
        self.assertEqual("PASS", report["status"])
        self.assertEqual(5, report["summary"]["attack_cases"])
        self.assertEqual(4, report["summary"]["blocked_attack_cases"])
        self.assertEqual(0, report["summary"]["decision_drifts"])
        self.assertEqual(1, report["summary"]["trusted_state_mutations"])
        self.assertTrue(report["limitations"]["does_not_execute_llm"])
        provider = next(
            item for item in report["results"] if item["attack_id"] == "A05_PROVIDER_STATUS"
        )
        self.assertEqual(
            ["payment_status_observation.status"], provider["applied_paths"]
        )
        self.assertEqual("PAYMENT_PROVIDER_OBSERVED", provider["source_type"])
        self.assertIn("policy_version", provider)


if __name__ == "__main__":
    unittest.main()
