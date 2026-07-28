from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class AP2FlowEntrypointTest(unittest.TestCase):
    def test_cli_runs_hp_and_hnp_offline_fixtures(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "ap2_report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_ap2_protocol_samples.py",
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
        self.assertIn("AP2 v0.2.0: total=2 passed=2 failed=0", completed.stdout)
        self.assertEqual("PASS", report["status"])
        self.assertEqual("b4587ac", report["source"]["commit"])
        self.assertEqual("v0.2.0", report["source"]["release"])
        self.assertEqual(2, report["summary"]["passed"])
        self.assertEqual(
            {"HUMAN_PRESENT", "HUMAN_NOT_PRESENT"},
            {item["flow_mode"] for item in report["results"]},
        )
        self.assertTrue(report["limitations"]["cryptographic_signatures_not_verified"])
        self.assertTrue(report["limitations"]["not_ap2_conformance_test"])


if __name__ == "__main__":
    unittest.main()
