from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPECTED = {
    "src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py": "0d5824eee57cac1c6b494c5beeb47a020f8bbca99f6fea674522e9fbae4cca28",
    "src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py": "572bc38b61f993674bd2060fad1d1fdc0c5f2b7aba343c383a0fed1c82852348",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8",
    "src/agentic_payment_experiment/webshop_runtime_gate.py": "3414df3d986d105a3832ae354c7e0a6cd8c4909192ba052b42ec3b895c886fc3",
    "samples/evaluation/project_impact_baseline_v1.json": "75e1682742e1eb576f62da89437bff766decde87d87ac73ad45de0ee59650ab5",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


actual = {path: digest(ROOT / path) for path in EXPECTED}
assert actual == EXPECTED, {k: (EXPECTED[k], actual[k]) for k in EXPECTED if actual[k] != EXPECTED[k]}
for path, value in actual.items():
    print(f"{path}={value}")
print("frozen_boundary_count=7")
print("RESULT=PASS")
