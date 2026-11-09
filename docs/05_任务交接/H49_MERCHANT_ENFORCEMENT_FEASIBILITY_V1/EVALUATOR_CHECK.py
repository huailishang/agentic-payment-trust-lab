"""H49 static source/design checks. No merchant, provider, or model execution.

These checks validate references and evidence boundaries. Human L3 still decides
whether the proposed mechanism, transaction ordering and business claim follow.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.parent / "H47_UCP_COMMERCE_APPLICABILITY_V1"
SOURCE = PARENT / "sources/ucp/rest/python/server"
TASK_ID = "H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1"
UNITS = ["create_checkout", "get_checkout", "update_checkout", "complete_checkout", "cancel_checkout",
         "create_cart", "update_cart", "cancel_cart", "update_order", "ship_order", "order_event_webhook"]
MECHANISMS = ["CLIENT_RECHECK", "MERCHANT_ATOMIC_GUARD", "EXTERNAL_AUTHORITY_GATE"]
CASES = ["T01_NORMAL", "T02_CHANGED_BEFORE", "T03_UPDATE_DURING_EXECUTION", "T04_MISSING_CONFIRMATION",
         "T05_FORGED_CONFIRMATION", "T06_REVOKED", "T07_EXPIRED", "T08_SAME_KEY_REPEAT",
         "T09_SAME_KEY_DIFFERENT_BODY", "T10_NEW_KEY_AFTER_COMPLETE", "T11_UNKNOWN_THEN_QUERY",
         "T12_CONCURRENT_COMPLETE", "T13_PAYMENT_BEFORE_COMMIT_FAILURE", "T14_DIRECT_ENTRY"]
DOCS = ["SOURCE_AUDIT.md", "COMPARISON.md", "BOUNDARY_DESIGN.md", "VALIDATION_DESIGN.md", "BUSINESS_CHECK.md", "REPORT.md"]
MUTABLE = set(DOCS + ["SEAM_MAP.json", "MECHANISM_COMPARISON.json", "BOUNDARY_DESIGN.json",
                     "VALIDATION_DESIGN.json", "DECISION.json", "ATTEMPT_LEDGER.json"])


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def workspace():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    return {x.decode("utf-8") for x in raw.split(b"\0") if x}


def meaningful(value):
    return isinstance(value, str) and len(value.strip()) >= 12 and "TODO" not in value and "待填写" not in value


def symbols(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    def visit(node, parents):
        for item in ast.iter_child_nodes(node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                key = ".".join(parents + [item.name])
                found[key] = (item.lineno, item.end_lineno, item)
                visit(item, parents + [item.name])
            else:
                visit(item, parents)
    visit(tree, [])
    return found


def native_facts():
    path = SOURCE / "services/checkout_service.py"
    start, end, method = symbols(path)["CheckoutService.complete_checkout"]
    tracked = {"get_idempotency_record", "_get_and_validate_checkout", "_process_payment", "reserve_stock", "commit"}
    calls = sorted([{"call": node.func.attr, "line": node.lineno} for node in ast.walk(method)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in tracked], key=lambda x: x["line"])
    positions = {x["call"]: x["line"] for x in calls}
    require(positions["get_idempotency_record"] < positions["_get_and_validate_checkout"]
            < positions["_process_payment"] < positions["reserve_stock"] < positions["commit"], "native call order changed")
    uses = sorted({node.lineno for node in ast.walk(method) if isinstance(node, ast.Name) and node.id == "checkout_complete"})
    return {"schema": "h49-native-facts/v1", "source": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
        "symbol": "CheckoutService.complete_checkout", "start_line": start, "end_line": end,
        "ordered_call_sites": calls, "checkout_complete_reference_lines": uses,
        "evidence_kind": "STATIC_SOURCE_NOT_RUNTIME_OR_CONCURRENCY_TEST"}


def baseline():
    import yaml
    lock = read("BASELINE.json")
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(current.split("```yaml", 1)[1].split("```", 1)[0])
    require(route["task_id"] == TASK_ID and route["task_kind"] == "one_off"
        and route["project_map_revision"] == "2026-10-18-r77" and route["hypothesis_id"] == "H-49"
        and route["active_bottleneck_id"] == "B-17", "routing drift")
    require((route["state"], route["current_role"]) in {("CONTRACT_FROZEN", "Executor"),
        ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}, "wrong role/state")
    require(all(route["authorization_" + key] is False for key in ["api_call", "commit", "push", "history_rewrite"]), "authority drift")
    require(hashlib.sha256(current.split("## Global position", 1)[1].encode()).hexdigest() == lock["current_history_sha256"], "history changed")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"], "HEAD drift")
    for name, expected in lock["protected_files"].items():
        require((ROOT / name).is_file() and sha(ROOT / name) == expected, "protected drift: " + name)
    for name, expected in lock["frozen_files"].items():
        require(sha(TASK / name) == expected, "frozen drift: " + name)
    prefix = TASK.relative_to(ROOT).as_posix() + "/"
    require(all(name.startswith(prefix) for name in workspace() - set(lock["workspace_files"])), "new file outside task")
    for path in TASK.rglob("*"):
        if path.is_file():
            name = path.relative_to(TASK).as_posix()
            require(name == "BASELINE.json" or name in lock["frozen_files"] or name in MUTABLE
                    or name.startswith("evidence/") or "__pycache__/" in name, "unlisted task file: " + name)
    env = json.loads((PARENT / "ENVIRONMENT.json").read_text(encoding="utf-8"))
    require(sys.version_info[:2] == (3, 12) and sys.prefix != sys.base_prefix, "existing isolated Python required")
    for name, version in env["packages"].items():
        require(importlib.metadata.version(name) == version, "environment drift: " + name)
    require(native_facts() == read("NATIVE_FACTS.json"), "native facts drift")
    print(json.dumps({"baseline": "PASS", "protected_files": len(lock["protected_files"]), "frozen_files": len(lock["frozen_files"])}))


def validate_ref(ref):
    path = (ROOT / ref["path"]).resolve()
    require(path.is_relative_to(SOURCE.resolve()) and path.suffix == ".py", "reference outside fixed source")
    entry = symbols(path).get(ref["symbol"])
    require(entry is not None, "unknown symbol")
    require(type(ref.get("start_line")) is int and type(ref.get("end_line")) is int
        and entry[0] <= ref["start_line"] <= ref["end_line"] <= entry[1], "line range outside symbol")


def validate_seams(value):
    require(value.get("schema") == "h49-seam-map/v1", "seam schema")
    rows = value.get("units", [])
    require(len(rows) == 11 and sorted(x["operation"] for x in rows) == sorted(UNITS), "11 units required")
    for row in rows:
        require(all(meaningful(row.get(k)) for k in ["read_set", "write_set", "effect", "payment_relevance", "bypass_reason", "proposed_treatment"]), "incomplete seam")
        require(bool(row.get("source_refs")), "source evidence required")
        for ref in row["source_refs"]:
            validate_ref(ref)


def validate_future(value):
    require(value.get("schema") == "h49-validation-design/v1", "future design schema")
    rows = value.get("cases", [])
    require(len(rows) == 14 and sorted(x["id"] for x in rows) == sorted(CASES), "14 future cases required")
    for row in rows:
        require(row.get("executed") is False, "future design is not an executed test")
        require(all(meaningful(row.get(k)) for k in ["setup", "independent_oracle", "expected_decision",
            "expected_persisted_state", "required_trace", "residual_risk"]), "incomplete case")
        require(isinstance(row.get("steps"), list) and len(row["steps"]) >= 2 and all(meaningful(x) for x in row["steps"]), "missing case schedule")
        require(type(row.get("expected_payment_calls")) is int and row["expected_payment_calls"] in {0, 1}
                or row.get("expected_payment_calls") == "UNKNOWN", "unbounded payment expectation")
    normal = next(x for x in rows if x["id"] == "T01_NORMAL")
    require(normal["expected_payment_calls"] == 1, "all-blocked design forbidden")


def validate_decision(value):
    require(value.get("schema") == "h49-decision/v1" and value.get("classification") in {
        "BOUNDED_SERVICE_PROTOTYPE_CANDIDATE", "SERVICE_CONTRACT_CHANGE_REQUIRED", "NO_SAFE_SEAM"}, "decision classification")
    require(all(meaningful(value.get(x)) for x in ["reason", "strongest_alternative", "next_step", "stop_condition", "customer_question"]), "missing decision reasoning")
    require(all(value.get(x) is False for x in ["product_improved", "server_guard_implemented", "race_closed",
        "provider_verified", "customer_validated", "third_party_verified", "servicenow_payment_binding_verified"]), "unverified capability upgraded")
    require(value.get("customer_demand") == "UNKNOWN" and value.get("external_classification") == "REFERENCE_ONLY"
        and value.get("full_product_gate_comparison") == "NOT_MEASURED", "unsupported scope claim")


def artifacts():
    validate_seams(read("SEAM_MAP.json"))
    validate_future(read("VALIDATION_DESIGN.json"))
    validate_decision(read("DECISION.json"))
    mechanisms = read("MECHANISM_COMPARISON.json")
    require(mechanisms.get("schema") == "h49-mechanisms/v1", "mechanism schema")
    rows = mechanisms.get("mechanisms", [])
    require(len(rows) == 3 and sorted(x["id"] for x in rows) == sorted(MECHANISMS), "3 mechanisms required")
    for row in rows:
        require(row.get("classification") in {"ABSORB", "REFERENCE_ONLY", "REJECT", "DEFER"}, "mechanism label")
        require(all(meaningful(row.get(k)) for k in ["existing_controls", "covers", "does_not_cover", "trusted_inputs",
            "server_control_required", "change_location", "cost", "strongest_objection"]), "mechanism comparison incomplete")
    boundary = read("BOUNDARY_DESIGN.json")
    require(boundary.get("schema") == "h49-boundary-design/v1", "boundary schema")
    for key in ["mechanism", "entrypoint", "trusted_inputs", "assumptions", "write_coordination", "idempotency_ordering",
                "revocation_ordering", "unknown_recovery", "trace_requirements", "minimal_changes", "rollback", "unresolved"]:
        require(meaningful(boundary.get(key)), "boundary description missing: " + key)
    require(boundary.get("server_guard_implemented") is False and boundary.get("race_closed") is False, "design implementation overclaim")
    for name in DOCS:
        value = (TASK / name).read_text(encoding="utf-8")
        require(len(value.strip()) >= 200 and "TODO" not in value, "incomplete document: " + name)
    report = (TASK / "REPORT.md").read_text(encoding="utf-8")
    require(TASK_ID in report and "SUBMITTED_FOR_REVIEW" in report and "7831d232" in report, "report identity/status")
    ledger = read("ATTEMPT_LEDGER.json")
    require(1 <= ledger.get("formal_l2_attempts", 0) <= 2 and 0 <= ledger.get("active_work_minutes", -1) <= 360, "budget exceeded")
    require(all(ledger.get(x) == 0 for x in ["asgi_requests", "model_calls", "provider_calls", "external_runtime_calls"]), "runtime budget zero")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    baseline()
    print("Static references, design completeness and bounded claims PASS; mechanism semantics require manual L3.")


def selftest():
    base = {"schema": "h49-validation-design/v1", "cases": [{"id": key, "executed": False,
        "setup": "synthetic setup placeholder for checker selftest", "steps": ["prepare an explicit synthetic state", "observe the declared transition"],
        "independent_oracle": "independent observation source for selftest", "expected_decision": "ALLOW only in the normal design case",
        "expected_payment_calls": 1 if key == "T01_NORMAL" else 0, "expected_persisted_state": "explicit synthetic state for checker selftest",
        "required_trace": "synthetic trace requirement for checker selftest", "residual_risk": "selftest only; no executable case is created"} for key in CASES]}
    validate_future(base)
    variants = []
    bad = copy.deepcopy(base); bad["cases"][0]["executed"] = True; variants.append(bad)
    bad = copy.deepcopy(base); bad["cases"][0]["expected_payment_calls"] = 0; variants.append(bad)
    bad = copy.deepcopy(base); bad["cases"].pop(); variants.append(bad)
    bad = copy.deepcopy(base); bad["cases"][0]["independent_oracle"] = ""; variants.append(bad)
    bad = copy.deepcopy(base); bad["cases"][0]["steps"] = []; variants.append(bad)
    rejected = 0
    for value in variants:
        try:
            validate_future(value)
        except (AssertionError, KeyError):
            rejected += 1
    require(rejected == 5, "checker accepted invalid design")
    print(json.dumps({"checker_positive": True, "rejected_design_mutations": rejected,
                      "boundary": "CHECKER_ONLY_NOT_FUTURE_TEST_EXECUTION"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "artifacts", "selftest", "facts"])
    args = parser.parse_args()
    if args.mode == "facts":
        path = TASK / "NATIVE_FACTS.json"
        require(not path.exists(), "initial preparation only")
        path.write_text(json.dumps(native_facts(), indent=2) + "\n", encoding="utf-8")
    else:
        {"baseline": baseline, "artifacts": artifacts, "selftest": selftest}[args.mode]()
