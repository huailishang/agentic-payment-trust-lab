from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODULE = ROOT / "src/agentic_payment_experiment/action_origin.py"
TESTS = ROOT / "tests/test_action_origin.py"

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/webshop_agent_behavior.py": "6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f",
    ROOT / "tests/test_webshop_agent_behavior.py": "36f51bbec44313e8e6fde98ec35d2d0a16ee2730e81e0e2b6916387da2e28b20",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    ROOT / "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json": "cb11bdc27e514118c8e9ae69384be16d188ec08bba7c1d4514d6b3c50e316dd0",
    ROOT / "docs/05_任务交接/P9_AUTHORITATIVE_TRACE_READ_MODEL_PLAYER_V1/evidence/EV-03-T01.payload.json": "7663a7c0f6387197d3d7bf6054a74025ff4a1f975b62482a99dff2fa4a7c6cca",
}

FORBIDDEN_IMPORT_ROOTS = {
    "requests",
    "subprocess",
    "gym",
    "web_agent_site",
    "selenium",
    "playwright",
}
FORBIDDEN_PRODUCT_TOKENS = {
    "buy_now",
    "execute_payment",
    "payment_callback",
    "runtime.server",
    "user_sessions",
    "expected_asin",
    "goal_index",
    "reward_target",
    "legal_liability",
    "regulatory_liability",
    "compensation_liability",
}
EXPECTED_ORIGINS = {
    "USER_AUTHORITY",
    "AGENT_DECISION",
    "RUNTIME_DECISION",
    "EXTERNAL_FACT",
    "EXECUTION_RESULT",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        if not path.is_file():
            fail(f"protected file missing: {path}")
        observed = sha256(path)
        if observed != expected:
            fail(f"protected pre-H13 asset changed: {path} observed={observed} expected={expected}")

    if not MODULE.is_file():
        fail(f"H-13 module missing: {MODULE}")
    if not TESTS.is_file():
        fail(f"H-13 dedicated tests missing: {TESTS}")

    module_text = MODULE.read_text(encoding="utf-8")
    lower = module_text.lower()
    for token in sorted(FORBIDDEN_PRODUCT_TOKENS):
        if token in lower:
            fail(f"forbidden behavior/payment/legal token in read-only H-13 module: {token}")

    tree = ast.parse(module_text, filename=str(MODULE))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    fail(f"forbidden runtime/network import in H-13 module: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"forbidden runtime/network import in H-13 module: {node.module}")

    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    if "ActionOrigin" not in classes:
        fail("ActionOrigin closed enum is missing")

    string_values = set()
    action_origin_class = classes["ActionOrigin"]
    for node in action_origin_class.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            string_values.add(node.value.value)
    if string_values != EXPECTED_ORIGINS:
        fail(f"ActionOrigin enum values are not the frozen five-value set: {sorted(string_values)}")

    print("PASS: H-13 remains a read-only Action Origin projection; shopping policy, core authoritative trace contract/consumer and frozen evidence fixtures are unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
