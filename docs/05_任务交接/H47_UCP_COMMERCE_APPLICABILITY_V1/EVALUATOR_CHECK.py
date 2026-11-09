"""Frozen H47 evidence checks. Executor implementation is intentionally absent.

L2/L3 execute the submitted driver against fresh real upstream state; responses
and SQLite state are observed by this harness, never accepted from driver output.
Native expected-behavior disagreements are measurements, not automatic repairs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
SPEC = json.loads((TASK / "CASE_SPEC.json").read_text(encoding="utf-8"))
MAPPING_FIELDS = ["user_authority", "confirmation_origin", "checkout_id", "final_order_id",
                  "order_version", "amount_minor_units", "currency", "merchant_identity", "payee",
                  "agent_identity", "credential_possession", "request_payment_binding",
                  "payment_result", "idempotency", "query_recovery", "execution_seam", "trace_consumer"]
DOCS = ["SOURCE_AUDIT.md", "SEMANTIC_MAPPING.md", "EXECUTION_SEAMS.md", "NATIVE_BASELINE.md",
        "TEAM_SCREENING.md", "DECISION.md", "LIMITATIONS.md", "REPORT.md"]
MUTABLE = set(DOCS + ["MEASUREMENT.py", "MAPPING.json", "TEAM_SCREENING.json", "DECISION.json", "ATTEMPT_LEDGER.json"])


def require(value, message):
    if not value:
        raise AssertionError(message)


def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def meaningful(value):
    return isinstance(value, str) and len(value.strip()) >= 12 and "TODO" not in value and "待填写" not in value


def workspace_files():
    raw = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT)
    return {name.decode("utf-8") for name in raw.split(b"\0") if name}


def baseline():
    lock = read("BASELINE.json")
    import yaml
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
    route = yaml.safe_load(current.split("```yaml", 1)[1].split("```", 1)[0])
    require(route.get("task_id") == "H47_UCP_COMMERCE_APPLICABILITY_V1"
            and route.get("task_kind") == "one_off"
            and route.get("project_map_revision") == "2026-10-15-r75"
            and route.get("active_bottleneck_id") == "B-17"
            and route.get("hypothesis_id") == "H-47", "routing drift")
    require((route.get("state"), route.get("current_role")) in {
        ("CONTRACT_FROZEN", "Executor"), ("EXECUTING", "Executor"), ("READY_FOR_REVIEW", "Evaluator")}, "wrong task phase/role")
    require(all(route.get("authorization_" + name) is False for name in ["commit", "push", "history_rewrite", "api_call"]), "authorization drift")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == lock["head"], "HEAD drift")
    for path, expected in lock["protected_files"].items():
        require((ROOT / path).is_file() and sha(ROOT / path) == expected, "protected drift: " + path)
    task_rel = TASK.relative_to(ROOT).as_posix() + "/"
    unexpected = workspace_files() - set(lock["workspace_files"])
    require(all(path.startswith(task_rel) for path in unexpected), "new file outside H47 scope")
    for path in TASK.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(TASK).as_posix()
        require(relative == "BASELINE.json" or relative in lock["frozen_files"] or relative in MUTABLE or relative.startswith("evidence/")
                or "__pycache__/" in relative, "unlisted task file: " + relative)
    for name, expected in lock["frozen_files"].items():
        require(sha(TASK / name) == expected, "frozen task drift: " + name)
    for item in read("SOURCE_LOCK.json")["files"] + read("TEAM_SOURCE_LOCK.json")["files"]:
        require(sha(TASK / item["path"]) == item["sha256"], "source drift")
    environment = read("ENVIRONMENT.json")
    require(sys.version_info[:2] == (3, 12), "pinned Python 3.12 environment required")
    for name, version in environment["packages"].items():
        require(importlib.metadata.version(name) == version, "dependency drift: " + name)
    require(sys.prefix != sys.base_prefix, "task-local venv required")
    print("baseline, inherited workspace, source locks and isolated environment verified")


def load_driver():
    path = TASK / "MEASUREMENT.py"
    require(path.is_file(), "Executor must implement MEASUREMENT.py")
    module_spec = importlib.util.spec_from_file_location("h47_executor_measurement", path)
    module = importlib.util.module_from_spec(module_spec)
    from FROZEN_RUNTIME import deny_socket, synthetic_dns
    from unittest.mock import patch
    with patch("socket.socket.connect", deny_socket), patch("socket.create_connection", deny_socket), patch("socket.getaddrinfo", synthetic_dns):
        module_spec.loader.exec_module(module)
    require(callable(getattr(module, "run_case", None)), "run_case(ctx, case) is required")
    return module


def validate_case(case, calls, state, confirmed):
    require(len(calls) == len(case["steps"]), "wrong request count")
    for row, step in zip(calls, case["steps"]):
        require(row["operation"] == step["operation"] and row["key"] == step.get("key"), "wrong request sequence/key")
        require(type(row["response_status"]) is int and 100 <= row["response_status"] <= 599, "invalid status")
        require(isinstance(row["merchant_response"], dict), "missing raw merchant observation")
        require(row["before"]["payment_calls"] <= row["after"]["payment_calls"], "counter decreased")
        if "quantity" in step:
            require(row["request_body"]["line_items"][0]["quantity"] == step["quantity"], "wrong changed quantity")
        if row["operation"] in {"complete", "complete_drop_response"}:
            instrument = row["request_body"]["payment"]["instruments"][0]
            require(instrument["handler_id"] == "mock_payment_handler", "non-mock handler")
            require(instrument["credential"]["token"] == step.get("token", "success_token"), "wrong mock token")
        if row["operation"] == "complete_drop_response":
            require(row["response_withheld"] is True and row["client_observed_response"] is None, "client saw withheld result")
        else:
            require(row["response_withheld"] is False and row["client_observed_response"] == row["merchant_response"], "observation changed")
    require(state == calls[-1]["after"], "final state differs from observed state")
    created = next((row for row in calls if row["operation"] == "create" and row["response_status"] == 201), None)
    if created:
        require(confirmed == created["merchant_response"], "trusted fixture confirmation was rebuilt")
        require(confirmed["line_items"][0]["quantity"] == 1 and confirmed["currency"] == "USD", "fixture confirmation changed")
    return summarize(case, calls, state)


def summarize(case, calls, state):
    quantities = []
    totals = []
    statuses = []
    for row in calls:
        response = row["merchant_response"]
        quantities.append([line["quantity"] for line in response.get("line_items", [])])
        totals.append([(total["type"], total["amount"]) for total in response.get("totals", [])])
        statuses.append(response.get("status", response.get("ucp", {}).get("status")))
    inventory = sorted((row["product_id"], row["quantity"]) for row in state["inventory"])
    actual = {"case": case["id"], "response_statuses": [row["response_status"] for row in calls],
              "order_count": len(state["orders"]), "inventory": inventory,
              "payment_calls": state["payment_calls"], "quantities": quantities, "totals": totals,
              "statuses": statuses, "response_withheld_count": sum(row["response_withheld"] for row in calls)}
    actual["source_expectation_matches"] = (actual["response_statuses"] == case["expected_statuses"]
        and actual["order_count"] == case["expected_orders"]
        and inventory == [("rose", case["expected_stock"])]
        and actual["payment_calls"] == case["expected_payment_calls"])
    return actual


def measurement(out):
    baseline()
    from FROZEN_RUNTIME import Merchant
    module = load_driver()
    observations = []
    for repeat in range(SPEC["repeats"]):
        for case in SPEC["cases"]:
            with Merchant() as ctx:
                result = module.run_case(ctx, copy.deepcopy(case))
                require(result is None, "driver must not return claimed evidence")
                final = ctx.state()
                summary = validate_case(case, ctx.calls, final, ctx.confirmed)
                observations.append({"case": case["id"], "repeat": repeat, "calls": ctx.calls,
                    "confirmed_snapshot": ctx.confirmed, "summary": summary})
    for i in range(len(SPEC["cases"])):
        require(observations[i]["summary"] == observations[i + len(SPEC["cases"])]["summary"], "semantic repeat mismatch")
    # Positive and security canaries are prerequisites for interpretable measurement.
    for observation in observations:
        if observation["case"] in {"C01_NORMAL", "C08_BODY_TAMPER_AFTER_SIGNING", "C09_UNSIGNED_REQUEST"}:
            require(observation["summary"]["source_expectation_matches"], "mandatory runtime canary failed")
    output = {"schema": "h47-measurements/v1", "boundary": SPEC["boundary"], "cases": observations,
              "full_product_gate_comparison": "NOT_MEASURED", "real_provider_calls": 0,
              "real_model_calls": 0, "product_modified": False}
    destination = ROOT / out
    destination.resolve().relative_to((TASK / "evidence").resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    destination.write_text(encoded, encoding="utf-8")
    # Keep each attempt even when the fixed latest-result alias is refreshed.
    stamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = TASK / "evidence/measurement_runs" / (destination.stem + "_" + stamp + ".json")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_text(encoded, encoding="utf-8")
    baseline()
    print(json.dumps({"cases": len(observations), "source_expectation_differences": [row["case"] for row in observations if not row["summary"]["source_expectation_matches"]], "out": out}))


def source_ref(reference):
    require(isinstance(reference, dict), "source reference object required")
    path = reference.get("path", "")
    resolved = (TASK / path).resolve()
    resolved.relative_to((TASK / "sources").resolve())
    require(resolved.is_file(), "source reference absent")
    line = reference.get("line")
    require(type(line) is int and 1 <= line <= len(resolved.read_text(encoding="utf-8").splitlines()), "invalid source line")


def validate_mapping(data):
    require(isinstance(data, dict) and data.get("schema") == "h47-mapping/v1", "mapping schema")
    rows = data.get("fields", [])
    require(len(rows) == len(MAPPING_FIELDS) and {row["field"] for row in rows} == set(MAPPING_FIELDS), "mapping fields")
    for row in rows:
        require(row.get("status") in {"NATIVE", "DERIVED", "ABSENT", "UNVERIFIED"}, "mapping status")
        require(meaningful(row.get("reason")) and meaningful(row.get("project_target")), "mapping rationale")
        require(row.get("source_refs"), "source refs required even for absence audit")
        for reference in row["source_refs"]:
            source_ref(reference)
        require(isinstance(row.get("observation_refs"), list), "observation refs")
    require(data.get("full_product_gate_comparison") == "NOT_MEASURED", "measurement cannot claim product gate effect")
    require(data.get("checkout_id_is_final_order_id") is False, "checkout/order identity conflated")
    require(data.get("mock_result_is_provider_proof") is False, "mock result promoted to payment proof")


def validate_teams(data):
    lock = read("TEAM_SOURCE_LOCK.json")
    sources = {row["repo"]: row for row in lock["files"]}
    rows = data.get("teams", [])
    require(data.get("schema") == "h47-team-screening/v1" and len(rows) == 3 and {row["repo"] for row in rows} == set(sources), "team set")
    for row in rows:
        source = sources[row["repo"]]
        text = (TASK / source["path"]).read_text(encoding="utf-8")
        require(row.get("source_commit") == source["commit"], "team source commit")
        require(isinstance(row.get("workflow_quotes"), list) and 1 <= len(row["workflow_quotes"]) <= 2, "workflow quotes")
        require(all(isinstance(quote, str) and 8 <= len(quote) <= 160 and quote in text for quote in row["workflow_quotes"]), "unsupported public workflow quote")
        require(row.get("customer_demand") == "UNKNOWN" and row.get("budget") == "UNKNOWN" and row.get("contacted") is False, "public code is not customer validation")
        for field in ["workflow", "existing_controls", "unverified_pain_hypothesis", "next_question", "fit_reason"]:
            require(meaningful(row.get(field)), "missing team analysis: " + field)


def validate_decision(data):
    require(data.get("schema") == "h47-decision/v1", "decision schema")
    require(data.get("classification") in {"BOUNDED_ADAPTER_CANDIDATE", "CORE_SEMANTIC_GAP", "NO_INCREMENTAL_VALUE", "ENVIRONMENT_OR_EVIDENCE_GAP"}, "decision classification")
    require(meaningful(data.get("reason")) and meaningful(data.get("strongest_alternative")), "decision rationale")
    for key in ["product_improved", "third_party_verified", "provider_proof_verified", "model_attack_measured", "customer_demand_validated", "production_authentication_proven"]:
        require(data.get(key) is False, "unearned claim: " + key)
    require(data.get("full_product_gate_comparison") == "NOT_MEASURED", "unearned product comparison")


def artifacts(measurement_path):
    for name in DOCS:
        text = (TASK / name).read_text(encoding="utf-8")
        require(len(text.strip()) >= 160 and "TODO" not in text and "待填写" not in text, "incomplete document: " + name)
    validate_mapping(read("MAPPING.json"))
    validate_teams(read("TEAM_SCREENING.json"))
    validate_decision(read("DECISION.json"))
    measured = json.loads((ROOT / measurement_path).read_text(encoding="utf-8"))
    require(len(measured["cases"]) == 18, "need all 9 cases repeat 2")
    differences = sorted({row["case"] for row in measured["cases"] if not row["summary"]["source_expectation_matches"]})
    require(read("DECISION.json").get("source_expectation_differences") == differences, "decision omitted native disagreements")
    ledger = read("ATTEMPT_LEDGER.json")
    require(ledger.get("schema") == "h47-attempt-ledger/v1", "ledger schema")
    require(type(ledger.get("formal_l2_attempts")) is int and 1 <= ledger["formal_l2_attempts"] <= 3, "L2 budget")
    require(type(ledger.get("active_work_minutes")) in {int, float} and 0 <= ledger["active_work_minutes"] <= 720, "active work ceiling")
    require(type(ledger.get("asgi_requests")) is int and 0 < ledger["asgi_requests"] <= 500, "ASGI budget")
    require(ledger.get("external_runtime_calls") == 0 and ledger.get("model_calls") == 0 and ledger.get("provider_calls") == 0, "call budget")
    print("document structure, cited sources, bounded claims and ledger verified; semantic mapping still requires manual L3 review")


def selftest():
    from FROZEN_RUNTIME import Merchant
    case = SPEC["cases"][0]
    with Merchant() as ctx:
        for step in case["steps"]:
            ctx.request(**step)
        calls, state, confirmed = copy.deepcopy(ctx.calls), ctx.state(), copy.deepcopy(ctx.confirmed)
    validate_case(case, calls, state, confirmed)
    mutations = []
    bad = copy.deepcopy(calls); bad[0]["key"] = "other"; mutations.append((bad, state, confirmed))
    bad = copy.deepcopy(calls); bad.pop(); mutations.append((bad, state, confirmed))
    bad = copy.deepcopy(calls); bad[0]["response_status"] = "201"; mutations.append((bad, state, confirmed))
    bad = copy.deepcopy(calls); bad[0]["client_observed_response"] = {}; mutations.append((bad, state, confirmed))
    bad = copy.deepcopy(confirmed); bad["line_items"][0]["quantity"] = 2; mutations.append((calls, state, bad))
    bad = copy.deepcopy(state); bad["payment_calls"] += 1; mutations.append((calls, bad, confirmed))
    rejected = 0
    for args in mutations:
        try:
            validate_case(case, *args)
        except (AssertionError, KeyError, ValueError):
            rejected += 1
    require(rejected == len(mutations), "counterexample accepted")
    for validator, value in [(validate_mapping, {}), (validate_teams, {}), (validate_decision, {"schema":"h47-decision/v1", "classification":"BOUNDED_ADAPTER_CANDIDATE", "reason":"x" * 20, "strongest_alternative":"x" * 20, "product_improved": True})]:
        try:
            validator(value)
        except (AssertionError, KeyError, ValueError):
            rejected += 1
        else:
            raise AssertionError("malformed/overclaim evidence accepted")
    print(json.dumps({"positive_native_case": True, "rejected_counterexamples": rejected}))


def regressions():
    baseline()
    for folder, pattern in [("tests", "test_webshop_runtime_gate.py"), ("tests/trusted_execution", "test_payment_binding.py")]:
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", folder, "-p", pattern],
            cwd=ROOT, check=True, capture_output=True, text=True,
            env=__import__("os").environ | {"PYTHONPATH": "src"})
        text = result.stdout + result.stderr
        print(text)
        match = __import__("re").search(r"Ran (\d+) tests?", text)
        require(match and int(match.group(1)) > 0, "empty regression selection")
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    baseline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["baseline", "measurement", "artifacts", "selftest", "regressions"])
    parser.add_argument("--out")
    parser.add_argument("--measurements")
    args = parser.parse_args()
    {"baseline": baseline, "measurement": lambda: measurement(args.out),
     "artifacts": lambda: artifacts(args.measurements), "selftest": selftest, "regressions": regressions}[args.mode]()
