"""Windows entry for the ONE accepted Evaluator run. Importing does no work."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]


def need(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identifier(value):
    need(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{32}", value), "expected 32 lowercase hex")
    return value


def output_path(root, task, run_id, relative):
    identifier(run_id)
    rel = PurePosixPath(relative)
    need(not rel.is_absolute() and "\\" not in relative and ":" not in relative and ".." not in rel.parts, "unsafe output")
    expected = task / "evidence/evaluator_runs" / run_id
    actual = root / relative
    need(actual == expected and actual.resolve() == expected.absolute(), "output must be exact non-symlink evaluator directory")
    for path in (actual, *actual.parents):
        need(not path.is_symlink() and not getattr(path, "is_junction", lambda: False)(), "output link/junction")
        if path == root:
            break
    need(actual.is_dir() and not any(actual.iterdir()), "CHECK must create a fresh empty output")
    return actual


def authorize(run_id, nonce, relative):
    import yaml
    identifier(run_id)
    identifier(nonce)
    out = output_path(ROOT, P, run_id, relative)
    router = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    need((router["task_id"], router["state"], router["current_role"]) == (P.name, "READY_FOR_REVIEW", "Evaluator"), "accepted Evaluator only")
    for key in ("authorization_local_service", "authorization_existing_wsl", "authorization_ephemeral_test_credentials"):
        need(router.get(key) is True, "authority missing: " + key)
    marker = read(P / "evidence/INDEPENDENT_ISSUANCE_ATTEMPT.json")
    need(marker["run_id"] == run_id and marker["nonce"] == nonce and marker["budget_consumed"] == 1, "CHECK attempt marker mismatch")
    accepted = read(P / "evidence/ACCEPTED.json")
    required = {str((P / name).relative_to(ROOT).as_posix()) for name in ("RUN.py", "WORKLOAD.py", "TASK_TESTS.py", "REPORT.md", "SUBMISSION.json")}
    need(required.issubset(accepted["files"]), "incomplete accepted implementation snapshot")
    for rel, expected in accepted["files"].items():
        path = (ROOT / rel).resolve()
        need(path.is_relative_to(ROOT) and digest(path) == expected, "accepted input changed: " + rel)
    gate_path = (ROOT / accepted["l2_gate_path"]).resolve()
    need(gate_path in [(P / "evidence" / name / "L2-GATE.json").resolve() for name in ("l2", "l2_retry_02")], "invalid L2 location")
    need(gate_path.relative_to(ROOT).as_posix() in accepted["files"], "unsealed L2")
    gate = read(gate_path)
    need(gate["result"] == "PASS" and gate["mandatory_failures"] == 0, "L2 not passing")
    from CHECK import preservation
    preservation()
    return out


def wsl_path(path):
    text = str(path.absolute()).replace("\\", "/")
    need(re.match(r"^[A-Za-z]:/", text), "expected Windows drive path")
    return "/mnt/" + text[0].lower() + text[2:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("collect",))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = authorize(args.run_id, args.nonce, args.out)
    # A second invocation can never replay the accepted attempt.
    with (out / "DISPATCH.json").open("x", encoding="utf-8") as stream:
        json.dump({"run_id": args.run_id, "nonce": args.nonce, "at_utc": datetime.now(timezone.utc).isoformat(), "distribution": "Ubuntu"}, stream)
    command = ["wsl.exe", "--distribution", "Ubuntu", "--exec", "/usr/bin/python3", "-B", wsl_path(P / "WORKLOAD.py"), "issuer", "--run-id", args.run_id, "--nonce", args.nonce, "--out", wsl_path(out)]
    # No wrapper timeout kills the cleanup supervisor. WORKLOAD enforces the
    # 1100-second live timer, each command <=180 seconds; cleanup is exempt.
    with (out / "dispatcher.stdout.log").open("xb") as stdout, (out / "dispatcher.stderr.log").open("xb") as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
    index_path = out / "PUBLIC_INDEX.json"
    if index_path.is_file():
        index = read(index_path)
        index["files"] = {path.relative_to(out).as_posix(): digest(path) for path in sorted(out.rglob("*")) if path.is_file() and path != index_path}
        index["excluded"] = {"PUBLIC_INDEX.json": "no self-hash"}
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
