"""Evaluator-only, write-once preparation; Executor must never refresh baseline."""
import hashlib
import json
from pathlib import Path
import subprocess

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
PRODUCT = ["src/agentic_payment_experiment/adapters/stripe_checkout.py",
           "src/agentic_payment_experiment/stripe_checkout_lab.py",
           "tests/test_stripe_checkout_adapter.py", "tests/test_stripe_checkout_lab.py"]
GOVERNANCE = ["CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def files(*args):
    raw = subprocess.run(["git", "ls-files", "-z", *args], cwd=ROOT,
                         capture_output=True, check=True).stdout
    return sorted(x.decode("utf-8") for x in raw.split(b"\0") if x)

if __name__ == "__main__":
    tracked = set(files()) - set(PRODUCT) - set(GOVERNANCE)
    untracked = files("--others", "--exclude-standard")
    prefix = PACK.relative_to(ROOT).as_posix() + "/"
    inherited = [p for p in untracked if not p.startswith(prefix)]
    protected = tracked | (set(inherited) - set(PRODUCT) - set(GOVERNANCE))
    # Evidence/INPUTS/ledger may be git-ignored; they remain authoritative inputs.
    parent_pack = PACK.parent / "H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1"
    parent_files = sorted(p.relative_to(ROOT).as_posix() for p in parent_pack.rglob("*")
                          if p.is_file() and "__pycache__" not in p.parts)
    protected.update(parent_files)
    shared = ["../localagent-common/skills/evaluator-executor-workflow/scripts/" + p
              for p in ("validate_workflow.py", "run_validation.py", "capture_evidence.py")]
    data = {
        "schema": "h68r-offline-repair-baseline/v1",
        "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip(),
        "allowed_product": PRODUCT, "governance": GOVERNANCE,
        "tracked_files": sorted(tracked), "inherited_untracked": inherited,
        "parent_files": parent_files,
        "protected": {p: sha(ROOT / p) for p in sorted(protected)},
        "before_product": {p: sha(ROOT / p) for p in PRODUCT},
        "package_files": {p: sha(PACK / p) for p in
                          ("CONTRACT.md", "CHECK.py", "VALIDATION_PLAN.yaml", "FIXTURES.py", "PREPARE_BASELINE.py")},
        "shared_tools": {p: sha(ROOT / p) for p in shared},
    }
    with (PACK / "BASELINE.json").open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=True, indent=2)
        stream.write("\n")
    print(json.dumps({"protected_files": len(protected), "tracked_files": len(tracked)}))
