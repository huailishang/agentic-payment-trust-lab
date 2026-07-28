from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SANDBOX_PATH = PROJECT_ROOT / "experiments" / "trusted_execution" / "ui" / "learning_sandbox.html"


class LearningSandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = SANDBOX_PATH.read_text(encoding="utf-8")

    def test_sandbox_exists_and_is_offline(self) -> None:
        self.assertTrue(SANDBOX_PATH.is_file())
        self.assertNotIn('src="http', self.html)
        self.assertNotIn("src='http", self.html)
        self.assertNotIn('href="http', self.html)
        self.assertNotIn("href='http", self.html)

    def test_contains_first_five_ui_lessons(self) -> None:
        for lesson_id in ("UI-01", "UI-02", "UI-03", "UI-04", "UI-05"):
            self.assertIn(f'id: "{lesson_id}"', self.html)
        self.assertNotIn('id: "UI-06"', self.html)

    def test_marks_demo_as_fixed_and_not_real_backend(self) -> None:
        self.assertIn("固定教学演示 · 不调用真实底层组件", self.html)
        self.assertIn("运行固定教学检查", self.html)
        self.assertIn("预设结果", self.html)

    def test_uses_shared_learning_page_skeleton(self) -> None:
        for element_id in (
            "whatHappened",
            "whyDangerous",
            "verificationGoal",
            "resultValue",
            "nextAction",
            "plainExplanation",
            "mechanismExplanation",
            "technicalBoundary",
            "blockchainRelation",
        ):
            self.assertIn(f'id="{element_id}"', self.html)

    def test_only_one_detail_panel_is_kept_open(self) -> None:
        self.assertIn('if (other !== item) other.open = false;', self.html)


if __name__ == "__main__":
    unittest.main()
