from __future__ import annotations

import ast
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FROZEN = {
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    "src/agentic_payment_experiment/webshop_sidecar_trace_profiles.py": "eb03ed375c3cb5c0b2a80ad248b4de00e833c007e8dfb687f742d97cca643941",
    "src/agentic_payment_experiment/webshop_sidecar_trace_toolkit.py": "1ccf37b62f6eedc0eff41216ec983ddaea74aed7a0e0529be686f6b15aefbbf3",
    "src/agentic_payment_experiment/webshop_payment_sidecar.py": "e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8",
    "src/agentic_payment_experiment/webshop_authoritative_trace.py": "9653277777d06ce8d2c65862765ec57c17874a9d311d2c5c9c117993a0feeac8",
    "samples/evaluation/project_impact_baseline_v1.json": "4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5",
}

for relative, expected in FROZEN.items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    print(f"frozen_sha256 {relative} {actual}")
    assert actual == expected, (relative, actual, expected)

runtime_path = ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py"
toolkit_path = ROOT / "src/agentic_payment_experiment/webshop_prepayment_trace_toolkit.py"
profiles_path = ROOT / "src/agentic_payment_experiment/webshop_prepayment_trace_profiles.py"
runtime = runtime_path.read_text(encoding="utf-8")
toolkit = toolkit_path.read_text(encoding="utf-8")
profiles = profiles_path.read_text(encoding="utf-8")
runtime_tree = ast.parse(runtime)
toolkit_tree = ast.parse(toolkit)

runtime_imports = 0
runtime_calls = 0
for node in ast.walk(runtime_tree):
    if isinstance(node, ast.ImportFrom):
        runtime_imports += sum(
            alias.name == "build_prepayment_product_trace" for alias in node.names
        )
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        runtime_calls += node.func.id == "build_prepayment_product_trace"

toolkit_assembly_calls = sum(
    isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "assemble_product_trace"
    for node in ast.walk(toolkit_tree)
)
print(f"runtime_toolkit_imports={runtime_imports}")
print(f"runtime_toolkit_calls={runtime_calls}")
print(f"toolkit_assembly_calls={toolkit_assembly_calls}")
print(f"toolkit_validate_request_mentions={toolkit.count('validate_request')}")
print(f"profile_literal_count={profiles.count('PrepaymentTraceProfile(')}")
print(f"dynamic_eval_mentions={toolkit.count('eval(') + profiles.count('eval(')}")
print(f"dynamic_exec_mentions={toolkit.count('exec(') + profiles.count('exec(')}")
assert runtime_imports == 1
assert runtime_calls == 1
assert toolkit_assembly_calls == 1
assert "validate_request" not in toolkit
assert profiles.count("PrepaymentTraceProfile(") == 3
assert "eval(" not in toolkit + profiles
assert "exec(" not in toolkit + profiles
print("RESULT=PASS_FROZEN_BOUNDARIES_AND_SINGLE_PATH")
