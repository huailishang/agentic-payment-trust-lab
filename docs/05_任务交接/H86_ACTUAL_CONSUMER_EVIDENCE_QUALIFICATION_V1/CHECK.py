"""H86 frozen read-only repository inventory."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
T = Path(__file__).resolve().parent
R = T.parents[2]
NAMES = {"gate_webshop_buy_now", "observe_payment_execution_gate", "execute_with_payment_binding_gate", "verify_x509_svid_credential_possession"}
SOURCES = [
    "docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/REVIEW.md",
    "docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/POSTCHECK.json",
    "docs/05_任务交接/H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1/REVIEW_OWNER_DECISION.md",
    "docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1/REPORT.md",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    paths = {p.relative_to(R).as_posix() for d in ("src", "scripts")
             for p in (R / d).rglob("*.py") if "__pycache__" not in p.parts}
    for name in ("CHECK.py", "CONTRACT.md", "VALIDATION_PLAN.yaml"):
        paths.add((T / name).relative_to(R).as_posix())
    return sorted(paths | set(SOURCES))


def preserve():
    lock = json.loads((T / "INPUTS.json").read_text(encoding="utf-8"))
    assert inputs() == sorted(lock["files"])
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=R, text=True).strip() == lock["head"]
    for name, expected in lock["files"].items():
        assert sha(R / name) == expected, name
    print(json.dumps({"locked_inputs": len(lock["files"]), "drift": 0}))


def scan():
    preserve()
    rows = []
    for name in inputs():
        if not name.startswith(("src/", "scripts/")) or not name.endswith(".py"):
            continue
        tree = ast.parse((R / name).read_text(encoding="utf-8-sig"), filename=name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if called in NAMES:
                rows.append({"file": name, "line": node.lineno, "called": called,
                             "explicit_keywords": sorted(k.arg for k in node.keywords if k.arg is not None),
                             "dynamic_keywords": [ast.unparse(k.value) for k in node.keywords if k.arg is None]})
    rows.sort(key=lambda row: (row["file"], row["line"]))
    for name in ("src/agentic_payment_experiment/adapters/stripe_checkout.py",
                 "src/agentic_payment_experiment/runner.py",
                 "scripts/validation/webshop/run_same_journey_responsibility.py"):
        assert any(row["file"] == name for row in rows)
    print(json.dumps({"scope": "LOCKED_REPOSITORY_DIRECT_CALLS", "external_adoption": "UNKNOWN",
                      "calls": rows, "evidence_sha256": {p: sha(R / p) for p in SOURCES}},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    {"preserve": preserve, "scan": scan}[sys.argv[1]]()
