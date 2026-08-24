from __future__ import print_function

import ast
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[4]
POLICY = ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"
DRIVER = ROOT / "scripts" / "validation" / "webshop" / "run_autonomous_prebuy_behavior.py"

ALLOWED_INPUT_FIELDS = {
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
}
FORBIDDEN_POLICY_TOKENS = {
    "b099231v35",
    "b06y3vldfb",
    "vhomes lights reclaimed",
    "expected_asin",
    "expected_option",
    "expected_price",
    "goal_index",
    "user_sessions",
    "product_item_dict",
    "evaluator_label",
}
FORBIDDEN_DRIVER_LITERALS = {
    "b099231v35",
    "b06y3vldfb",
    "vhomes lights reclaimed",
}


def fail(message):
    raise AssertionError(message)


def annotated_fields(class_node):
    fields = set()
    for node in class_node.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            fields.add(node.target.id)
    return fields


def main():
    if not POLICY.is_file() or not DRIVER.is_file():
        fail("required policy/driver source is missing")

    policy_text = POLICY.read_text(encoding="utf-8")
    driver_text = DRIVER.read_text(encoding="utf-8")
    policy_lower = policy_text.lower()
    driver_lower = driver_text.lower()

    for token in sorted(FORBIDDEN_POLICY_TOKENS):
        if token in policy_lower:
            fail("forbidden policy token: {}".format(token))
    for literal in sorted(FORBIDDEN_DRIVER_LITERALS):
        if literal in driver_lower:
            fail("frozen target/smoke literal embedded in runtime driver: {}".format(literal))

    tree = ast.parse(policy_text, filename=str(POLICY))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    if "AgentPolicyInput" not in classes:
        fail("AgentPolicyInput class is missing")
    actual_fields = annotated_fields(classes["AgentPolicyInput"])
    if actual_fields != ALLOWED_INPUT_FIELDS:
        fail("policy input fields differ: {}".format(sorted(actual_fields)))

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    chooser = functions.get("choose_webshop_action")
    if chooser is None:
        fail("choose_webshop_action is missing")
    argument_names = [argument.arg for argument in chooser.args.args]
    if argument_names != ["state"]:
        fail("choose_webshop_action must accept only state")

    print("PASS: frozen policy input and source boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
