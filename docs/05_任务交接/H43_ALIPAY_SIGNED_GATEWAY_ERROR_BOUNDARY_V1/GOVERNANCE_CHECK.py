"""Offline H43 L2/L3 entry. No sandbox key reading or network calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
BASELINE = json.loads((PACKAGE / "BASELINE.json").read_text(encoding="utf-8"))


def run(argv):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONUTF8="1")
    return subprocess.run(argv, cwd=ROOT, env=env, check=False).returncode


def main():
    if len(sys.argv) != 2:
        raise SystemExit("one mode required")
    mode = sys.argv[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASELINE["head"]:
        raise ValueError("baseline HEAD drift")
    protected = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                 for name, digest in BASELINE["protected_files"].items()}
    if not all(protected.values()):
        raise ValueError("protected hash drift")
    if mode == "baseline":
        print(json.dumps({"head_match": True, "protected_hashes": protected}, ensure_ascii=True))
        return 0
    for flag in ("authorization_api_call", "authorization_commit", "authorization_push", "authorization_history_rewrite"):
        if f"{flag}: false" not in (ROOT / "CURRENT.md").read_text(encoding="utf-8"):
            raise ValueError("authority drift")
    runtime = os.environ.get("H43_TEST_PYTHON")
    if not runtime or not Path(runtime).is_file():
        raise ValueError("H43_TEST_PYTHON must be an existing runtime with cryptography")
    if mode == "focused":
        return run([runtime, "-m", "unittest", "discover", "-s", "tests", "-p", "test_alipay_agent_pay_sandbox.py", "-v"])
    if mode == "independent":
        return run([runtime, str(PACKAGE / "EVALUATOR_CHECK.py"), "after"])
    if mode == "guardrails":
        commands = [
            [runtime, "-m", "pytest", "-p", "no:cacheprovider", "-q", "tests/test_h41_alipay_signed_error_probe.py", "-k", "not test_actual_current_p0_blocked"],
            [runtime, "-m", "unittest", "discover", "-s", "docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks", "-p", "test_response_observer.py", "-v"],
            ["git", "diff", "--check"],
        ]
        codes = [run(command) for command in commands]
        print(json.dumps({"guardrail_exit_codes": codes}))
        return 0 if all(code == 0 for code in codes) else 1
    raise ValueError("unknown mode")


if __name__ == "__main__":
    raise SystemExit(main())
