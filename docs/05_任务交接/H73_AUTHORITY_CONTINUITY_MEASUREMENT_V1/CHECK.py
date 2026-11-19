"""Frozen structural controls. Historical truth still requires independent source review."""
from __future__ import annotations
import copy
import hashlib
import json
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
TASK = P.name

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def need(condition, label):
    if not condition:
        raise ValueError(label)

def pointer(obj, path):
    need(isinstance(path, str) and path.startswith("/"), "json_pointer_required")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj

def sources():
    return read(P / "INPUTS.json")["sources"]

def private_materials():
    spec = read(P / "SPEC.json")
    ref = ROOT / read(P / "INPUTS.json")["private_ref"]
    base = Path(read(ref)["path"]).resolve()
    need(not base.is_relative_to(ROOT), "private_root_boundary")
    jpath, dbpath = base / "n01_operation_private.json", base / "merchant.sqlite3"
    locks = read(P / "INPUTS.json")["private_sha256"]
    need(digest(jpath) == locks["PRIVATE:n01_operation"], "private_json_drift")
    need(digest(dbpath) == locks["PRIVATE:merchant_operations"], "private_db_drift")
    obj = read(jpath)
    with closing(sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        columns = [r[1] for r in conn.execute("PRAGMA table_info(operations)")]
        selected = spec["private_sqlite_columns"]
        need(all(c in columns for c in selected), "operations_schema_input_limit")
        # Column names come only from frozen SPEC, never submitted data.
        rows = conn.execute("SELECT " + ",".join(selected) + " FROM operations").fetchall()
    by_case = {}
    for row in rows:
        value = dict(zip(selected, row))
        case = value["case_id"]
        need(case in spec["cases"] and case not in by_case, "operations_case_identity")
        by_case[case] = value
    return obj, columns, by_case

def check_ref(ref, catalog=None):
    catalog = catalog or sources()
    source = ref["source"]
    if source == "PRIVATE:n01_operation":
        obj, _, _ = private_materials()
        ptr = ref["pointer"]
        top = ptr.split("/")[1].replace("~1", "/").replace("~0", "~")
        need(top in read(P / "SPEC.json")["private_json_allowed_top_keys"], "private_pointer_not_allowed")
        pointer(obj, ptr)
        return "private_json"
    if source == "PRIVATE:merchant_operations":
        _, _, rows = private_materials()
        parts = ref["pointer"].split("/")
        need(len(parts) == 4 and parts[1] == "operations", "private_sqlite_pointer")
        need(parts[2] in rows and parts[3] in rows[parts[2]], "private_sqlite_missing")
        return "private_sqlite"
    need(source in catalog, "unlocked_source")
    entry = catalog[source]
    path = ROOT / entry["path"]
    need(digest(path) == entry["sha256"], "source_drift")
    if path.suffix == ".json":
        pointer(read(path), ref["pointer"])
    else:
        lines = ref.get("lines")
        need(isinstance(lines, list) and len(lines) == 2 and all(type(x) is int for x in lines), "line_range_required")
        count = len(path.read_text(encoding="utf-8").splitlines())
        need(1 <= lines[0] <= lines[1] <= count, "line_range_invalid")
    return entry["kind"]

def validate_matrix(data):
    spec = read(P / "SPEC.json")
    need(data.get("schema") == "h73-matrix/v1", "matrix_schema")
    expected = {(c, b) for c in spec["cases"] for b in spec["boundaries"]}
    cells = data.get("cells", [])
    pairs = [(c["case"], c["boundary"]) for c in cells]
    need(len(pairs) == len(expected) and set(pairs) == expected, "exact_boundary_coverage")
    for cell in cells:
        need(type(cell.get("applicable")) is bool and bool(cell.get("reason")), "applicability_reason")
        need(set(cell.get("fields", {})) == set(spec["fields"]), "exact_field_coverage")
        need(cell.get("time_evaluation") in spec["matrix_structure"]["time_evaluation"], "time_status")
        need(isinstance(cell.get("time_evidence"), list), "time_evidence_required")
        for ref in cell["time_evidence"]:
            check_ref(ref)
        for field in cell["fields"].values():
            need(field.get("status") in spec["statuses"] and field.get("layer") in spec["layers"], "field_status_layer")
            need(isinstance(field.get("refs"), list) and bool(field.get("reason")), "field_refs_reason")
            kinds = [check_ref(r) for r in field["refs"]]
            if field["status"] in {"ORIGINAL_OBSERVED", "EXPLICIT_REAUTH"}:
                need(field.get("direct_binding") is True and bool(kinds), "direct_evidence_required")
                allowed = {"observation", "private_json", "private_sqlite"} if field["status"] == "ORIGINAL_OBSERVED" else {"owner_permission", "observation", "private_json"}
                need(any(k in allowed for k in kinds), "code_cannot_be_original_authority")
            if field["status"] == "CODE_RECONSTRUCTED":
                need("code" in kinds, "code_reference_required")
    return cells

def validate_semantics(data):
    cells = validate_matrix(data)
    for cell in cells:
        fields = cell["fields"]
        if (cell["case"], cell["boundary"]) == ("C01", "PRE_PAYMENT"):
            need(cell["applicable"] is False and all(f["status"] == "NOT_APPLICABLE" for f in fields.values()), "c01_no_payment")
            need(cell["time_evaluation"] == "NOT_APPLICABLE", "c01_no_payment_time")
        if cell["time_evaluation"] in {"VALID", "EXPIRED", "RENEWED"}:
            need(bool(cell["time_evidence"]) and fields["validity_times"]["status"] in {"ORIGINAL_OBSERVED", "EXPLICIT_REAUTH"}, "historical_time_must_be_observed")
    return cells

def validate_decision(result, matrix, check_inventory=True):
    spec = read(P / "SPEC.json")
    cells = validate_semantics(matrix)
    need(result.get("schema") == "h73-result/v1" and result.get("task_id") == TASK, "result_identity")
    need(result.get("decision") in spec["decisions"] and bool(result.get("rationale")), "decision_required")
    need(result.get("identity_assurance") == "UNKNOWN_REAL_SOURCE" and result.get("product_delta") == "NOT_APPLICABLE", "claim_boundary")
    need(result.get("historical_verdicts_preserved") is True and bool(result.get("stop_or_unblock_condition")), "historical_and_stop_boundary")
    if check_inventory:
        obj, columns, rows = private_materials()
        expected = {"n01_top_keys": sorted(obj), "operations_columns": columns, "cases_present": sorted(rows)}
        need(result.get("private_inventory") == expected, "private_inventory_mismatch")
    breaks = result.get("common_breaks")
    need(isinstance(breaks, list), "common_breaks_list_required")
    indexed = {(c["case"], c["boundary"]): c for c in cells}
    groups = {}
    for item in breaks:
        pair = (item["case"], item["boundary"])
        need(pair in indexed and item["field"] in spec["fields"], "break_location")
        need(item.get("kind") in {"AUDIT_EVIDENCE_GAP", "UNSAFE_ALLOW"} and bool(item.get("reason")), "break_kind_reason")
        kinds = [check_ref(r) for r in item.get("refs", [])]
        need(any(k in {"observation", "private_json", "private_sqlite"} for k in kinds), "break_needs_historical_observation")
        groups.setdefault(item["family"], set()).add(pair)
    if any(item["kind"] == "UNSAFE_ALLOW" for item in breaks):
        need(result["decision"] == "STOP_ESCALATE", "zero_tolerance_escalation")
    if result["decision"] == "RECOMMEND_MINIMAL_CAPABILITY":
        need(any(len(pairs) >= 2 for pairs in groups.values()), "common_break_threshold")
        proposal = result.get("next_package")
        keys = {"capability", "consumer", "seam", "same_baseline_controls", "estimated_cost", "residual_risks"}
        need(isinstance(proposal, dict) and keys <= set(proposal) and all(proposal[k] for k in keys), "minimal_next_package_required")
    else:
        need(result.get("next_package") is None, "no_automatic_capability_dispatch")

def preservation():
    inputs, frozen = read(P / "INPUTS.json"), read(P / "FREEZE.json")
    for rel, expected in inputs["protected"].items():
        need(digest(ROOT / rel) == expected, "protected_drift:" + rel)
    for rel, expected in frozen["files"].items():
        need(digest(P / rel) == expected, "frozen_drift:" + rel)
    private_materials()
    tracked = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    existing = set(inputs["protected"])
    prefix = P.relative_to(ROOT).as_posix() + "/"
    for rel in filter(None, tracked):
        if rel.startswith(prefix):
            local = rel[len(prefix):]
            allowed = local in frozen["files"] or local in {"FREEZE.json", "ANALYZE.py", "RESULT.json", "MATRIX.json", "ATTEMPT_LEDGER.json", "REPORT.md", "SUBMISSION.json", "REVIEW.md"} or local.startswith(("derived/", "evidence/"))
            need(allowed, "task_output_not_allowed:" + local)
        else:
            need(rel == "CURRENT.md" or rel in existing, "outside_task_new_file:" + rel)
    import yaml
    current = (ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0]
    route = yaml.safe_load(current)
    need(route["task_id"] == TASK and route["project_map_revision"] == "2026-11-15-r124", "router_task_map")
    need(route["task_kind"] == "one_off" and route["baseline_commit"] == inputs["head"], "router_kind_baseline")
    for key, suffix in (("contract_path", "CONTRACT.md"), ("executor_report_path", "REPORT.md"), ("evaluator_review_path", "REVIEW.md")):
        need(route[key] == prefix + suffix, "router_artifact_binding")
    need(route["active_bottleneck_id"] == "B-22" and route["hypothesis_id"] == "H-73", "router_strategy")
    states = {"CONTRACT_FROZEN": "Executor", "EXECUTING": "Executor", "READY_FOR_REVIEW": "Evaluator", "PASS": "Evaluator", "REJECTED": "Evaluator", "HUMAN_REQUIRED": "Human"}
    need(states.get(route["state"]) == route["current_role"], "router_role")
    required_auth = {"authorization_" + key for key in ("commit", "push", "history_rewrite", "api_call", "reference_read", "install", "local_service", "browser_test_only", "test_payments")}
    need(required_auth <= set(route) and all(route[key] is False for key in required_auth), "router_permissions")
    need(all(value is False for key, value in route.items() if key.startswith("authorization_")), "router_extra_permissions")

def package():
    frozen = read(P / "FREEZE.json")
    for rel, expected in frozen["files"].items():
        need(digest(P / rel) == expected, "frozen_drift:" + rel)
    need(frozen["task_id"] == TASK, "packet_identity")

def budget():
    ledger = read(P / "ATTEMPT_LEDGER.json")
    need(all(w["role"] == "Executor" for w in ledger["windows"]), "executor_cost_role")
    evaluator_cost = P / "evidence/l3_review/COST.json"
    if evaluator_cost.exists():
        extra = read(evaluator_cost)
        need(extra.get("schema") == "h73-cost/v1" and bool(extra["windows"]) and all(w["role"] == "Evaluator" for w in extra["windows"]), "evaluator_cost_extension")
        need(extra["l2_attempts"] == 0 and ledger["l3_attempts"] == 0, "cost_role_attempts")
        need(extra["external_actions"] == ledger["external_actions"], "evaluator_side_effects")
        ledger = dict(ledger, windows=ledger["windows"] + extra["windows"], l3_attempts=extra["l3_attempts"])
    need(ledger.get("schema") == "h73-cost/v1", "cost_schema")
    windows = ledger.get("windows", [])
    need(bool(windows), "cost_windows_required")
    totals = {"Executor": 0.0, "Evaluator": 0.0}
    spans = {}
    now, previous_end, open_count = datetime.now(timezone.utc), None, 0
    for win in windows:
        role = win["role"]
        need(role in totals, "cost_role")
        need("end_utc" in win, "cost_end_key_required")
        begin = datetime.fromisoformat(win["begin_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(win["end_utc"].replace("Z", "+00:00")) if win.get("end_utc") else now
        need(begin.utcoffset() is not None and end.utcoffset() is not None and begin <= end <= now, "cost_times")
        need(previous_end is None or begin >= previous_end, "cost_window_overlap")
        previous_end = end
        open_count += win.get("end_utc") is None
        totals[role] += (end - begin).total_seconds() / 60
        spans.setdefault(role, [begin, end])[1] = end
    need(open_count <= 1 and (not open_count or windows[-1].get("end_utc") is None), "open_window_order")
    need(totals["Executor"] <= 105 and totals["Evaluator"] <= 45 and sum(totals.values()) <= 150, "role_cost_budget")
    need(all((end - begin).total_seconds() <= (4 if role == "Executor" else 2) * 3600 for role, (begin, end) in spans.items()), "wall_span_budget")
    for key, limit in (("l2_attempts", 2), ("l3_attempts", 1)):
        need(type(ledger.get(key)) is int and 0 <= ledger[key] <= limit, "attempt_budget:" + key)
    l2_dirs = sorted(p.name for p in (P / "evidence").glob("l2_attempt_*") if p.is_dir())
    l3_dirs = sorted(p.name for p in (P / "evidence/l3_review").glob("gate_*") if p.is_dir())
    need(l2_dirs == [f"l2_attempt_{i:03d}" for i in range(1, ledger["l2_attempts"] + 1)], "l2_attempt_directory_count")
    need(l3_dirs == [f"gate_{i:03d}" for i in range(1, ledger["l3_attempts"] + 1)], "l3_attempt_directory_count")
    need(ledger.get("external_actions") == {k: 0 for k in ("api", "network", "install", "service", "browser", "payment", "model")}, "side_effect_budget")
    print(json.dumps({"charged_role_window_minutes": totals, "actual_active_time_claimed": False}))

def submission():
    data = read(P / "SUBMISSION.json")
    files = data["files"]
    required = {"ANALYZE.py", "MATRIX.json", "RESULT.json", "ATTEMPT_LEDGER.json", "REPORT.md"}
    required.update(p.relative_to(P).as_posix() for base in (P / "derived", P / "evidence") if base.exists() for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts and (base.name == "derived" or p.relative_to(base).parts[0].startswith("l2_attempt_")))
    need(required <= set(files), "submission_coverage")
    for rel, expected in files.items():
        path = (P / rel).resolve()
        need(path.is_relative_to(P) and digest(path) == expected, "submission_drift")
    gate = data["l2_gate"]
    need(gate["path"] in files and gate["sha256"] == files[gate["path"]], "submission_l2_gate_binding")
    summary = read(P / gate["path"])
    need(summary.get("result") == "PASS", "submitted_l2_not_pass")

def guards():
    spec, catalog = read(P / "SPEC.json"), sources()
    cells = []
    for case in spec["cases"]:
        for boundary in spec["boundaries"]:
            applicable = (case, boundary) != ("C01", "PRE_PAYMENT")
            field = {"status": "UNKNOWN" if applicable else "NOT_APPLICABLE", "layer": "DOMAIN_AUTHORITY", "refs": [], "reason": "synthetic checker control; not a historical finding"}
            cells.append({"case": case, "boundary": boundary, "applicable": applicable, "reason": "checker control", "fields": {k: copy.deepcopy(field) for k in spec["fields"]}, "time_evaluation": "UNKNOWN" if applicable else "NOT_APPLICABLE", "time_evidence": []})
    matrix = {"schema": "h73-matrix/v1", "cells": cells}
    # Real source references exercise legal direct-observation/renewal shapes.
    # This fixture tests the checker; it does not publish a historical finding.
    cells[0]["fields"]["operation_binding"].update(status="ORIGINAL_OBSERVED", layer="EXTERNAL_PAYMENT", direct_binding=True, refs=[{"source": "resumed:journey_N01.json", "pointer": "/original_session_sha256"}])
    cells[0]["fields"]["renewal_or_recovery_basis"].update(status="EXPLICIT_REAUTH", layer="TASK_PERMISSION", direct_binding=True, refs=[{"source": "owner:resume", "pointer": "/human_quote"}])
    result = {"schema": "h73-result/v1", "task_id": TASK, "decision": "STOP_VIEW", "rationale": "synthetic schema control", "identity_assurance": "UNKNOWN_REAL_SOURCE", "product_delta": "NOT_APPLICABLE", "historical_verdicts_preserved": True, "common_breaks": [], "next_package": None, "stop_or_unblock_condition": "checker control only"}
    validate_decision(result, matrix, check_inventory=False)
    tests = []
    broken = copy.deepcopy(matrix); broken["cells"].pop(); tests.append(("missing_boundary", result, broken))
    broken = copy.deepcopy(matrix); broken["cells"][0]["fields"].pop("validity_times"); tests.append(("missing_field", result, broken))
    observed = next(k for k, v in catalog.items() if v["kind"] == "observation" and v["path"].endswith(".json"))
    broken = copy.deepcopy(matrix); broken["cells"][0]["fields"]["operation_binding"]["refs"] = [{"source": observed, "pointer": "/H73_nonexistent_pointer"}]; tests.append(("invalid_pointer", result, broken))
    code = next(k for k, v in catalog.items() if v["kind"] == "code")
    broken = copy.deepcopy(matrix); broken["cells"][0]["fields"]["confirmation_binding"].update(status="ORIGINAL_OBSERVED", direct_binding=True, refs=[{"source": code, "lines": [1, 1]}]); tests.append(("code_as_original", result, broken))
    broken = copy.deepcopy(matrix); next(c for c in broken["cells"] if c["case"] == "C01" and c["boundary"] == "PRE_PAYMENT")["applicable"] = True; tests.append(("invented_c01_payment", result, broken))
    bad_result = copy.deepcopy(result); bad_result["decision"] = "RECOMMEND_MINIMAL_CAPABILITY"; tests.append(("unsupported_capability", bad_result, matrix))
    for label, value, view in tests:
        try:
            validate_decision(value, view, check_inventory=False)
        except (ValueError, KeyError, IndexError) as exc:
            print(json.dumps({"control": label, "rejected": True, "reason": str(exc)}))
        else:
            raise ValueError("guard_accepted:" + label)
    print(json.dumps({"positive_controls": 1, "negative_controls": len(tests), "scope": "checker integrity only"}))

def main():
    command = sys.argv[1]
    if command == "package": package()
    elif command == "preservation": preservation()
    elif command == "matrix": validate_matrix(read(P / "MATRIX.json"))
    elif command == "semantics": validate_semantics(read(P / "MATRIX.json"))
    elif command == "decision": validate_decision(read(P / "RESULT.json"), read(P / "MATRIX.json"))
    elif command == "guards": guards()
    elif command == "final":
        preservation(); budget()
        import yaml
        route_text = (ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0]
        if yaml.safe_load(route_text)["current_role"] == "Evaluator":
            need((P / "evidence/l3_review/COST.json").is_file(), "evaluator_cost_required")
            submission()
    else: raise ValueError("unknown check")
    print(json.dumps({"check": command, "status": "PASS", "historical_semantic_review_still_required": True}))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not print a traceback that could disclose private filesystem paths.
        print(json.dumps({"status": "FAIL", "error_category": type(exc).__name__, "reason": str(exc) if isinstance(exc, ValueError) else "source_or_structure_unavailable"}))
        sys.exit(1)
