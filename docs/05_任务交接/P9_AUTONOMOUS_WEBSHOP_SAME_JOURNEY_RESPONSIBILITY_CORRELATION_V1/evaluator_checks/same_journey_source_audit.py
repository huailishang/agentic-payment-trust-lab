from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "scripts/validation/webshop/run_same_journey_responsibility.py"
PROTECTED = {
    ROOT / "src/agentic_payment_experiment/webshop_agent_behavior.py": "6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "95ef06d6d396f9c912f321df907ed198908f629abf93c296ce0f9bf3d68439a6",
    ROOT / "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    ROOT / "src/agentic_payment_experiment/webshop_runtime_gate.py": "3414df3d986d105a3832ae354c7e0a6cd8c4909192ba052b42ec3b895c886fc3",
    ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py": "e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json": "cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0",
}
FORBIDDEN_IMPORT_ROOTS = {"requests", "httpx", "urllib", "socket", "selenium", "playwright"}
FORBIDDEN_TOKENS = {
    "runtime.step(\"click[buy now]\")",
    "runtime.step('click[buy now]')",
    "requests.",
    "httpx.",
    "socket.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        observed = sha256(path)
        require(observed == expected, f"protected file changed: {path} observed={observed} expected={expected}")

    require(RUNNER.is_file(), f"same-journey runner missing: {RUNNER}")
    text = RUNNER.read_text(encoding="utf-8")
    lower = text.lower()
    for token in FORBIDDEN_TOKENS:
        require(token.lower() not in lower, f"forbidden real-side-effect/network token in runner: {token}")

    tree = ast.parse(text, filename=str(RUNNER))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                require(alias.name.split(".", 1)[0] not in FORBIDDEN_IMPORT_ROOTS, f"forbidden network import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            require(root not in FORBIDDEN_IMPORT_ROOTS, f"forbidden network import: {node.module}")

    print("PASS: H-16 is integration/evidence-only; H-13, shopping policy, Adapter, Runtime Gate, Payment Sidecar and authoritative trace product code remain frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
