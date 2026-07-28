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
                    "run_attack_overlays.py",
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
        self.assertIn("Attack Overlay v1: total=5 passed=5 failed=0", completed.stdout)
        self.assertEqual("PASS", report["status"])
        self.assertEqual(4, report["summary"]["attack_cases"])
        self.assertEqual(4, report["summary"]["blocked_attack_cases"])
        self.assertEqual(0, report["summary"]["decision_drifts"])
        self.assertEqual(0, report["summary"]["trusted_state_mutations"])
        self.assertTrue(report["limitations"]["does_not_execute_llm"])


if __name__ == "__main__":
    unittest.main()
