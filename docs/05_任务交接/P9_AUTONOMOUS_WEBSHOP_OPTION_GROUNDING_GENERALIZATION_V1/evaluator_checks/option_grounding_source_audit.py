from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs" / "05_任务交接" / "P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1"
POLICY = ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"
TESTS = ROOT / "tests" / "test_webshop_agent_behavior.py"
BASELINE_POLICY = TASK / "evaluator_baseline" / "H14_BASELINE_webshop_agent_behavior.py.snapshot"

ALLOWED_INPUT_FIELDS = {
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
}

PROTECTED_FUNCTIONS = {
    "_search_query",
    "_significant_terms",
    "_budget",
    "_choose_result",
}

REVEALED_HOLDOUT_LITERALS = {
    "b003i567w4",
    "b09ntccvgx",
    "b07fypsnh8",
    "b09r4rjsfp",
    "b08g14b779",
    "b09py89b1s",
    "b005x7ixtk",
    "b087y28xlm",
    "pecan",
    "60x40x40cm",
    "120ml",
    "pink",
    "1pcs",
    "woody scent",
    "1.6 ounce (pack of 1)",
    "fresh",
}

FORBIDDEN_HIDDEN_TOKENS = {
    "expected_asin",
    "expected_option",
    "expected_price",
    "goal_index",
    "goal_idx",
    "user_sessions",
    "product_item_dict",
    "evaluator_label",
    "reward_target",
    "server.goals",
    "server.product",
    "items_shuffle_1000",
    "items_ins_v2_1000",
    "human_goals.json",
}

FORBIDDEN_IMPORT_ROOTS = {"gym", "web_agent_site", "requests", "subprocess"}


def fail(message: str) -> None:
    raise AssertionError(message)


def function_sources(text: str) -> dict[str, str]:
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    result: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = "".join(lines[node.lineno - 1 : node.end_lineno])
    return result


def annotated_fields(class_node: ast.ClassDef) -> set[str]:
    fields: set[str] = set()
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            fields.add(node.target.id)
    return fields


def main() -> int:
    for path in (POLICY, TESTS, BASELINE_POLICY):
        if not path.is_file():
            fail(f"required file missing: {path}")

    policy_text = POLICY.read_text(encoding="utf-8")
    tests_text = TESTS.read_text(encoding="utf-8")
    baseline_text = BASELINE_POLICY.read_text(encoding="utf-8")
    combined_lower = (policy_text + "\n" + tests_text).lower()

    for literal in sorted(REVEALED_HOLDOUT_LITERALS):
        if literal in combined_lower:
            fail(f"revealed holdout literal entered product policy/dedicated tests: {literal}")

    policy_lower = policy_text.lower()
    for token in sorted(FORBIDDEN_HIDDEN_TOKENS):
        if token in policy_lower:
            fail(f"forbidden hidden-truth/runtime token in policy: {token}")

    tree = ast.parse(policy_text, filename=str(POLICY))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    fail(f"forbidden runtime/data import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail(f"forbidden runtime/data import: {node.module}")

    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    if "AgentPolicyInput" not in classes:
        fail("AgentPolicyInput class is missing")
    if annotated_fields(classes["AgentPolicyInput"]) != ALLOWED_INPUT_FIELDS:
        fail("AgentPolicyInput fields changed outside frozen five-field boundary")

    current_functions = function_sources(policy_text)
    baseline_functions = function_sources(baseline_text)
    for name in sorted(PROTECTED_FUNCTIONS):
        if name not in current_functions or name not in baseline_functions:
            fail(f"protected function missing: {name}")
        current_hash = hashlib.sha256(current_functions[name].encode("utf-8")).hexdigest()
        baseline_hash = hashlib.sha256(baseline_functions[name].encode("utf-8")).hexdigest()
        if current_hash != baseline_hash:
            fail(f"protected search/ranking function changed: {name}")

    print("PASS: H-14 source remains option-grounding-only and avoids revealed holdout truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
