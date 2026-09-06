from __future__ import print_function

import ast
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[4]
POLICY = ROOT / "src" / "agentic_payment_experiment" / "webshop_agent_behavior.py"

ALLOWED_INPUT_FIELDS = {
    "instruction_text",
    "observation",
    "available_actions",
    "step_index",
    "previous_actions",
}

FORBIDDEN_TARGET_LITERALS = {
    "b09mw563kn",
    "b07s7hdc88",
    "b09hx5cd2d",
    "b09kp78g37",
    "b099231v35",
    "black1901",
    "heather charcoal",
    "vancilin mens casual leather",
    "cleveland state university vikings property",
    "swagofkgys travel toothbrushes",
}

FORBIDDEN_POLICY_TOKENS = {
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

FORBIDDEN_IMPORT_ROOTS = {
    "gym",
    "web_agent_site",
    "requests",
    "subprocess",
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
    if not POLICY.is_file():
        fail("policy source is missing")

    text = POLICY.read_text(encoding="utf-8")
    lower = text.lower()

    for literal in sorted(FORBIDDEN_TARGET_LITERALS):
        if literal in lower:
            fail("target-specific literal embedded in policy: {}".format(literal))

    for token in sorted(FORBIDDEN_POLICY_TOKENS):
        if token in lower:
            fail("forbidden hidden-truth/runtime token in policy: {}".format(token))

    tree = ast.parse(text, filename=str(POLICY))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    fail("forbidden runtime/data import: {}".format(alias.name))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                fail("forbidden runtime/data import: {}".format(node.module))

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

    print("PASS: multi-goal policy source remains instruction/observation bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
