"""Independent L3 inputs; reuse only the Executor's fake-transport harness."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests"))
from test_h38_authorization_gate import H38AuthorizationGateTests

FENCE = chr(96) * 3
VALID = FENCE + "yaml\n" + "\n".join([
    "workflow: evaluator-executor-workflow/v2.2",
    "task_id: H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1",
    "state: EXECUTING", "current_role: Executor",
    "authorization_api_call: true",
    "contract_path: docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md",
]) + "\n" + FENCE + "\n"


def main():
    wrong = VALID.replace("task_id: H38_", "task_id: H40_")
    cases = {
        "valid_control": (VALID, None, True),
        "wrong_task": (wrong, None, False),
        "quoted_true": (VALID.replace("call: true", 'call: "true"'), None, False),
        "prose_spoof": (wrong + "authorization_api_call: true\n", None, False),
        "mid_run_wrong_task": (VALID, wrong, False),
        "commented_out_authorization": ("<!--\n" + VALID + "-->\n", None, False),
        "example_in_outer_fence": (FENCE + "`text\n" + VALID + FENCE + "`\n", None, False),
        "second_unclosed_state": (VALID + FENCE + "yaml\nauthorization_api_call: false\n", None, False),
        "python_string_concatenation": (VALID.replace("state: EXECUTING", 'state: "EXEC" "UTING"'), None, False),
        "malformed_metadata": (VALID.replace("state: EXECUTING", 'metadata: "unterminated\nstate: EXECUTING'), None, False),
    }
    results = {}
    harness = H38AuthorizationGateTests()
    for name, (content, replacement, allow) in cases.items():
        with contextlib.redirect_stdout(io.StringIO()):
            actual = harness._run(content, mutate_after_sign=replacement)
        passed = (actual["rc"] == 0 and actual["network"] == 1) if allow else (
            actual["rc"] != 0 and actual["network"] == 0 and not actual["reservation"]
            and (replacement is not None or actual["inspect"] == actual["sign"] == 0))
        results[name] = dict(expected_allow=allow, passed=passed, **actual)
    baseline = json.loads((Path(__file__).resolve().parents[1] / "BASELINE.json").read_text(encoding="utf-8"))
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
              for name, digest in baseline["files"].items() if name != baseline["allowed_change"]}
    report = dict(cases=results, protected_hashes_match=hashes, live_calls=0, real_key_reads=0)
    text = json.dumps(report, indent=2)
    print(text)
    return 0 if all(r["passed"] for r in results.values()) and all(hashes.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
