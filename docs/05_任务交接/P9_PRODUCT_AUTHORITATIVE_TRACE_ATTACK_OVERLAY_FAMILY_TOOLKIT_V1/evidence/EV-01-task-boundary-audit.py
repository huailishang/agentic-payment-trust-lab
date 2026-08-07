from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent

ENTERING = {
    "src/agentic_payment_experiment/attack_overlay.py": "2f14925231f4c59368b096fdcc2398bba8c8c4e6f774d7bcb430487ca65f25d7",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "samples/evaluation/project_impact_baseline_v1.json": "e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0",
    "tests/test_attack_overlay.py": "afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27",
    "tests/test_project_impact_baseline.py": "f1101ce82ddc97a1eae49308856c371f1afd54fbd772afd6bb5cc1aef973bf4a",
}
FROZEN_AT_SUBMISSION = {
    key: value
    for key, value in ENTERING.items()
    if key
    not in {
        "src/agentic_payment_experiment/attack_overlay.py",
        "tests/test_project_impact_baseline.py",
    }
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Task-start manifest independently anchors the entering attack_overlay hash even
# though that file is intentionally modified by this capability experiment.
manifest = {}
for line in (EVID / "SRC-start.sha256").read_text(encoding="utf-8").splitlines():
    if line.strip():
        digest, rel = line.split(maxsplit=1)
        manifest[rel.lstrip("* ")] = digest
assert manifest["src/agentic_payment_experiment/attack_overlay.py"] == ENTERING[
    "src/agentic_payment_experiment/attack_overlay.py"
]
print("entering_attack_overlay_hash_anchored=True")

for rel, expected in FROZEN_AT_SUBMISSION.items():
    actual = sha(ROOT / rel)
    assert actual == expected, (rel, expected, actual)
    print(f"frozen:{rel}={actual}")

current = {
    "src/agentic_payment_experiment/attack_overlay.py": sha(
        ROOT / "src/agentic_payment_experiment/attack_overlay.py"
    ),
    "src/agentic_payment_experiment/attack_overlay_trace_profiles.py": sha(
        ROOT / "src/agentic_payment_experiment/attack_overlay_trace_profiles.py"
    ),
    "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py": sha(
        ROOT / "src/agentic_payment_experiment/attack_overlay_trace_toolkit.py"
    ),
    "tests/test_attack_overlay_trace_toolkit.py": sha(
        ROOT / "tests/test_attack_overlay_trace_toolkit.py"
    ),
    "tests/test_project_impact_baseline.py": sha(
        ROOT / "tests/test_project_impact_baseline.py"
    ),
}
for rel, value in current.items():
    print(f"task_local:{rel}={value}")
assert current["src/agentic_payment_experiment/attack_overlay.py"] != ENTERING[
    "src/agentic_payment_experiment/attack_overlay.py"
]
assert current["tests/test_project_impact_baseline.py"] != ENTERING[
    "tests/test_project_impact_baseline.py"
]

print("task_local_product_change_count=3")
print("task_local_test_change_count=2")
print("fixture_runner_registry_assembler_unchanged=True")
print("RESULT=PASS")
