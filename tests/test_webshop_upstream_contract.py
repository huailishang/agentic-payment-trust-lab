from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validation.webshop.check_webshop_upstream import (
    EXPECTED_COMMIT,
    EXPECTED_ORIGIN,
    inspect_checkout,
)


ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CHECKOUT = ROOT / "local_sources" / "third_party" / "webshop"


README_TEXT = """# Minimal WebShop source contract

Create the small data path with `./setup.sh -d small`.
The small path uses a subset of 1000 random products.
The text environment is `WebAgentTextEnv-v0` and accepts `search[...]` and `click[...]` actions.
"""

LICENSE_TEXT = """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files.
"""

SETUP_TEXT = """#!/usr/bin/env bash
if [ "$1" = "small" ]; then
  echo "prepare 1000 products"
fi
"""

INIT_TEXT = """from gym.envs.registration import register

register(
    id='WebAgentTextEnv-v0',
    entry_point='web_agent_site.envs:WebAgentTextEnv',
)
"""

TEXT_ENV_TEXT = '''class WebAgentTextEnv:
    def step(self, action):
        """Actions use search[keywords] and click[value]."""
        return action

    def reset(self, session=None):
        return session


class SimServer:
    def done(self, session_id, **kwargs):
        session = self.user_sessions[session_id]
        session["actions"]["purchase"] += 1
        reward, info = get_reward(session, kwargs)
        self.user_sessions[session_id]["done"] = True
        self.user_sessions[session_id]["reward"] = reward
        return "html", "url", reward

    def receive(self, session_id, current_url, **kwargs):
        status = {"reward": 0.0, "done": False}
        clickable_name = kwargs.get("clickable_name", "").lower()
        if clickable_name == END_BUTTON.lower():
            html, url, reward = self.done(session_id, **kwargs)
            status["reward"] = reward
            status["done"] = True
        return status
'''

ENGINE_TEXT = """END_BUTTON = 'Buy Now'
"""


class WebShopUpstreamContractTest(unittest.TestCase):
    def run_git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repo), *args),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail(
                f"git command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        return result.stdout.strip()

    def write_source_fixture(self, repo: Path) -> None:
        files = {
            "README.md": README_TEXT,
            "LICENSE.md": LICENSE_TEXT,
            "setup.sh": SETUP_TEXT,
            "requirements.txt": "gym==0.23.1\n",
            "web_agent_site/envs/__init__.py": INIT_TEXT,
            "web_agent_site/envs/web_agent_text_env.py": TEXT_ENV_TEXT,
            "web_agent_site/engine/engine.py": ENGINE_TEXT,
        }
        for relative, content in files.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def commit_all(self, repo: Path, message: str) -> str:
        self.run_git(repo, "add", "-A")
        self.run_git(repo, "commit", "-m", message)
        return self.run_git(repo, "rev-parse", "HEAD")

    def create_fixture(self, directory: Path) -> tuple[Path, str]:
        repo = directory / "webshop"
        repo.mkdir(parents=True)
        self.run_git(repo, "init")
        self.run_git(repo, "config", "user.name", "WebShop Contract Test")
        self.run_git(repo, "config", "user.email", "webshop-contract@example.invalid")
        self.run_git(repo, "remote", "add", "origin", EXPECTED_ORIGIN)
        self.write_source_fixture(repo)
        commit = self.commit_all(repo, "minimal source fixture")
        self.run_git(repo, "checkout", "--detach", commit)
        return repo, commit

    @staticmethod
    def checks_by_name(report) -> dict[str, object]:
        return {item.name: item for item in report.contracts}

    def test_valid_minimal_source_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, commit = self.create_fixture(Path(temp_dir))
            report = inspect_checkout(
                repo,
                expected_origin=EXPECTED_ORIGIN,
                expected_commit=commit,
            )

        self.assertTrue(report.overall_pass)
        self.assertEqual("MIT", report.license)
        self.assertTrue(report.detached_head)
        self.assertTrue(all(report.required_files[name]["exists"] for name in report.required_files))

    def test_missing_web_agent_text_env_fails_with_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, _ = self.create_fixture(Path(temp_dir))
            path = repo / "web_agent_site/envs/web_agent_text_env.py"
            path.write_text(TEXT_ENV_TEXT.replace("class WebAgentTextEnv:", "class RemovedTextEnv:"), encoding="utf-8")
            commit = self.commit_all(repo, "remove text environment class")
            report = inspect_checkout(repo, expected_commit=commit)

        check = self.checks_by_name(report)["web_agent_text_env_class"]
        self.assertFalse(check.passed)
        self.assertIn("web_agent_text_env.py", check.detail)

    def test_missing_text_environment_registration_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, _ = self.create_fixture(Path(temp_dir))
            path = repo / "web_agent_site/envs/__init__.py"
            path.write_text(INIT_TEXT.replace("WebAgentTextEnv-v0", "OtherEnv-v0"), encoding="utf-8")
            commit = self.commit_all(repo, "remove text environment registration")
            report = inspect_checkout(repo, expected_commit=commit)

        check = self.checks_by_name(report)["text_environment_registration"]
        self.assertFalse(check.passed)
        self.assertIn("envs/__init__.py", check.detail)

    def test_changed_end_button_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, _ = self.create_fixture(Path(temp_dir))
            path = repo / "web_agent_site/engine/engine.py"
            path.write_text("END_BUTTON = 'Purchase'\n", encoding="utf-8")
            commit = self.commit_all(repo, "change end button")
            report = inspect_checkout(repo, expected_commit=commit)

        check = self.checks_by_name(report)["end_button"]
        self.assertFalse(check.passed)
        self.assertIn("Buy Now", check.detail)

    def test_missing_buy_now_to_done_route_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, _ = self.create_fixture(Path(temp_dir))
            path = repo / "web_agent_site/envs/web_agent_text_env.py"
            path.write_text(TEXT_ENV_TEXT.replace("self.done(session_id", "self.finish(session_id"), encoding="utf-8")
            commit = self.commit_all(repo, "remove buy-now done route")
            report = inspect_checkout(repo, expected_commit=commit)

        check = self.checks_by_name(report)["buy_now_routes_to_done"]
        self.assertFalse(check.passed)
        self.assertIn("SimServer.receive", check.detail)

    def test_missing_required_upstream_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, _ = self.create_fixture(Path(temp_dir))
            (repo / "requirements.txt").unlink()
            commit = self.commit_all(repo, "remove requirements")
            report = inspect_checkout(repo, expected_commit=commit)

        check = self.checks_by_name(report)["required_file:requirements.txt"]
        self.assertFalse(check.passed)
        self.assertIn("requirements.txt", check.detail)

    def test_wrong_origin_or_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo, commit = self.create_fixture(Path(temp_dir))

            wrong_origin = inspect_checkout(
                repo,
                expected_origin="https://github.com/example/not-webshop.git",
                expected_commit=commit,
            )
            wrong_commit = inspect_checkout(
                repo,
                expected_origin=EXPECTED_ORIGIN,
                expected_commit="0" * 40,
            )

        self.assertFalse(self.checks_by_name(wrong_origin)["official_origin"].passed)
        self.assertFalse(self.checks_by_name(wrong_commit)["pinned_commit"].passed)

    def test_actual_pinned_checkout_passes(self) -> None:
        self.assertTrue(ACTUAL_CHECKOUT.is_dir(), f"actual checkout absent: {ACTUAL_CHECKOUT}")

        report = inspect_checkout(
            ACTUAL_CHECKOUT,
            expected_origin=EXPECTED_ORIGIN,
            expected_commit=EXPECTED_COMMIT,
        )

        failed = [item for item in report.contracts if not item.passed]
        self.assertTrue(report.overall_pass, failed)
        self.assertEqual(EXPECTED_COMMIT, report.actual_commit)
        self.assertEqual(EXPECTED_ORIGIN, report.actual_origin)


if __name__ == "__main__":
    unittest.main()
