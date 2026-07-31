import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class EntrypointTest(unittest.TestCase):
    def test_run_experiment_entrypoint(self) -> None:
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "run_experiment.py"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Summary: total=13 passed=13 failed=0", completed.stdout)
        self.assertIn("实验模块总览：部分覆盖", completed.stdout)
        self.assertIn("内部回归: PASS passed=13 failed=0 gaps=0", completed.stdout)
        self.assertIn("PayBench 外部挑战: PARTIAL passed=8 failed=0 gaps=2", completed.stdout)
        self.assertIn("AP2 官方最小流程: PASS passed=2 failed=0 gaps=0", completed.stdout)
        self.assertIn("Attack Overlay: PASS passed=6 failed=0 gaps=0", completed.stdout)
        self.assertIn("内部回归基线：PASS", completed.stdout)
        self.assertTrue((root / "artifacts" / "scenario_report.html").exists())
        self.assertTrue((root / "artifacts" / "scenario_result_card.json").exists())
        regression_report = json.loads(
            (root / "artifacts" / "internal_regression_report.json").read_text(encoding="utf-8")
        )
        self.assertEqual("PASS", regression_report["status"])
        self.assertEqual(13, regression_report["scenario_count"])
        self.assertEqual([], regression_report["differences"])

    def test_run_experiment_fails_when_internal_baseline_drifts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        baseline = json.loads(
            (root / "samples" / "regression" / "internal_baseline_v1.json").read_text(
                encoding="utf-8"
            )
        )
        baseline["scenarios"]["S01"]["actual"]["decision"] = "DENY"

        with TemporaryDirectory() as tmp:
            changed_baseline = Path(tmp) / "changed_baseline.json"
            changed_baseline.write_text(
                json.dumps(baseline, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, "run_experiment.py", "--baseline", str(changed_baseline)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )

        self.assertEqual(1, completed.returncode)
        self.assertIn("内部回归基线：FAIL", completed.stdout)
        self.assertIn("scenarios.S01.actual.decision", completed.stdout)

    def test_cli_help_uses_stable_current_scenario_set_wording(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script_help = subprocess.run(
            [sys.executable, "run_experiment.py", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, script_help.returncode, script_help.stderr)
        self.assertIn("当前固定智能体支付离线场景集", script_help.stdout)
        self.assertNotIn("S01-S09", script_help.stdout)

        env = dict(os.environ)
        env["PYTHONPATH"] = str(root / "src")
        module_help = subprocess.run(
            [sys.executable, "-m", "agentic_payment_experiment", "--help"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(0, module_help.returncode, module_help.stderr)
        self.assertNotIn("S01-S09", module_help.stdout)


if __name__ == "__main__":
    unittest.main()
