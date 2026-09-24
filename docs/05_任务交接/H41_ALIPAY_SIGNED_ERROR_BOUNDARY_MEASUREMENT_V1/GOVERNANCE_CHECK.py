"""Task-owned offline validation entry; no product or central runner changes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
FROZEN = {
    "scripts/h41_alipay_signed_error_probe.py": "09733850937776f5d286454504e01d54bdfebd0b4915e3189104b68583a19b69",
    "tests/test_h41_alipay_signed_error_probe.py": "b2d8bb9f546a2f421d6a895e5b86e57c2efba0193c60619b1a8061aa711323e5",
    str((PACKAGE / "EVALUATOR_CHECK.py").relative_to(ROOT)): "46090bf1cc42b885bf26785adfb95e7be2167c83093680ed389e010d0242f2ca",
}


def run(args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONUTF8="1")
    return subprocess.run(args, cwd=ROOT, env=env, check=False).returncode


def main():
    mode = sys.argv[1]
    if mode == "baseline":
        baseline = json.loads((PACKAGE / "BASELINE.json").read_text(encoding="utf-8"))
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        if head != baseline["head"]:
            raise ValueError("HEAD drift")
        files = dict(baseline["protected_files"], **FROZEN)
        results = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                   for name, digest in files.items()}
        print(json.dumps({"protected_files": results}, ensure_ascii=True))
        return 0 if all(results.values()) else 1
    runtime = os.environ.get("H41_TEST_PYTHON")
    if not runtime or not Path(runtime).is_file():
        raise ValueError("H41_TEST_PYTHON must identify an existing test runtime")
    tests = {
        "h41": ["tests", "test_h41_alipay_signed_error_probe.py"],
        "gate": ["tests", "test_h38_authorization_gate.py"],
        "adapter": ["tests", "test_alipay_agent_pay_sandbox.py"],
        "observer": ["docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks", "test_*.py"],
    }
    if mode in tests:
        directory, pattern = tests[mode]
        return run([runtime, "-m", "unittest", "discover", "-s", directory, "-p", pattern, "-v"])
    if mode == "independent":
        return run([runtime, str(PACKAGE / "EVALUATOR_CHECK.py")])
    if mode == "report":
        report = (PACKAGE / "REPORT.md").read_text(encoding="utf-8")
        if "OFFLINE_READY_FOR_REVIEW" not in report or "NOT_MEASURED" not in report:
            raise ValueError("missing report phase or measurement limitation")
        if any(digest not in report for digest in FROZEN.values()):
            raise ValueError("report missing frozen hash")
        sys.path.insert(0, str(ROOT / "scripts"))
        from h38_authorization_gate import parse_current_workflow
        fields, raw = parse_current_workflow((ROOT / "CURRENT.md").read_text(encoding="utf-8"))
        if fields.get("execution_phase") != "H41_OFFLINE_PREPARATION":
            raise ValueError("P0 required")
        for key in ("authorization_api_call", "authorization_commit", "authorization_push", "authorization_history_rewrite"):
            if raw.get(key) != "false":
                raise ValueError("zero authorization required")
        if (PACKAGE / "evidence/H41_DIAGNOSTIC.reserved").exists():
            raise ValueError("unexpected live reservation")
        commands = [
            [runtime, "scripts/h41_alipay_signed_error_probe.py"],
            [runtime, "-m", "unittest", "discover", "-s", "tests", "-p", "test_h41_alipay_signed_error_probe.py", "-k", "secret", "-v"],
            ["git", "diff", "--check"],
        ]
        codes = [run(command) for command in commands]
        print(json.dumps({"report_hashes": True, "p0_zero_authorization": True, "check_exit_codes": codes}))
        return 0 if all(code == 0 for code in codes) else 1
    raise ValueError("unknown check")


if __name__ == "__main__":
    raise SystemExit(main())
