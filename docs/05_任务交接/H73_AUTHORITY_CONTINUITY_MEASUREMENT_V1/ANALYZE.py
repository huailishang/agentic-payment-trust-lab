"""H73: one offline, allowlisted measurement method; never import payment code."""
from __future__ import annotations
import hashlib
import ast
from collections import Counter
import json
import os
import sqlite3
import subprocess
import sys
import importlib.util
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def write(name, data):
    path = P / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def budget_estimate(action, estimate=2):
    ledger = read(P / "ATTEMPT_LEDGER.json")
    used = sum((datetime.fromisoformat(w["end_utc"]) if w["end_utc"] else datetime.now(timezone.utc)).timestamp() - datetime.fromisoformat(w["begin_utc"]).timestamp() for w in ledger["windows"]) / 60
    if used + estimate + 10 > 105:
        raise ValueError("insufficient_executor_budget_with_10_minute_closeout")
    print(json.dumps({"action": action, "charged_minutes": round(used, 4), "estimated_next_minutes": estimate, "closeout_reserved_minutes": 10, "remaining_minutes": round(105-used, 4)}))

def begin():
    if (P / "ATTEMPT_LEDGER.json").exists():
        raise ValueError("do_not_overwrite_cost_window")
    # Include all startup reading conservatively, before the first observed clock.
    write("ATTEMPT_LEDGER.json", {"schema": "h73-cost/v1", "windows": [{"role": "Executor", "begin_utc": "2026-11-16T00:40:00+00:00", "end_utc": None}], "l2_attempts": 0, "l3_attempts": 0, "external_actions": {k: 0 for k in ("api", "network", "install", "service", "browser", "payment", "model")}, "begin_basis": "Conservative startup upper bound preceding first observed clock at 00:44:17Z; includes initial reading. Actual active time UNKNOWN.", "events": [{"at_utc": now(), "event": "BEGIN_RECORDED"}]})
    status = subprocess.check_output(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=ROOT).decode("utf-8")
    (P / "derived").mkdir(exist_ok=True)
    (P / "derived/INITIAL_STATUS.txt").write_text(status, encoding="utf-8")
    budget_estimate("allowlisted_source_inventory", 4)

def private():
    inputs, spec = read(P / "INPUTS.json"), read(P / "SPEC.json")
    base = Path(read(ROOT / inputs["private_ref"])["path"]).resolve()
    if base.is_relative_to(ROOT):
        raise ValueError("private_boundary")
    jp, db = base / "n01_operation_private.json", base / "merchant.sqlite3"
    if sha(jp) != inputs["private_sha256"]["PRIVATE:n01_operation"] or sha(db) != inputs["private_sha256"]["PRIVATE:merchant_operations"]:
        raise ValueError("private_input_drift")
    obj = read(jp)
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as conn:
        conn.execute("PRAGMA query_only=ON")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(operations)")]
        selected = spec["private_sqlite_columns"]
        rows = [dict(zip(selected, r)) for r in conn.execute("SELECT " + ",".join(selected) + " FROM operations")]
    if len(rows) != 4 or {r["case_id"] for r in rows} != set(spec["cases"]):
        raise ValueError("private_case_inventory")
    return obj, cols, {r["case_id"]: r for r in rows}

def structure(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(structure(v, prefix + "/" + k.replace("~", "~0").replace("/", "~1")))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(structure(v, prefix + "/" + str(i)))
    else:
        out.append({"pointer": prefix, "type": type(obj).__name__, "present": obj is not None})
    return out

def inventory():
    budget_estimate("inventory_all_frozen_sources", 4)
    inputs = read(P / "INPUTS.json")
    catalog = []
    for sid, entry in inputs["sources"].items():
        path = ROOT / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("public_source_drift:" + sid)
        item = {"source": sid, **entry}
        if path.suffix == ".json":
            item["structure"] = structure(read(path))
        else:
            item["line_count"] = len(path.read_text(encoding="utf-8").splitlines())
        catalog.append(item)
    obj, cols, rows = private()
    spec = read(P / "SPEC.json")
    private_summary = {"n01_top_keys": sorted(obj), "operations_columns": cols, "cases_present": sorted(rows), "n01_allowed_key_presence": {k: k in obj for k in spec["private_json_allowed_top_keys"]}, "n01_allowed_structure": {k: structure(obj[k], "/" + k) for k in spec["private_json_allowed_top_keys"] if k in obj}, "operations_rows": {case: {k: {"present": v is not None, "type": type(v).__name__} for k, v in row.items()} for case, row in rows.items()}}
    write("derived/SOURCE_INVENTORY.json", {"schema": "h73-source-inventory/v1", "at_utc": now(), "sources": catalog, "private": private_summary})
    print(json.dumps({"sources": len(catalog), "private_top_keys": sorted(obj), "private_columns": cols, "cases_present": sorted(rows)}, ensure_ascii=False))

def inspect():
    budget_estimate("sanitized_allowlisted_source_read", 3)
    catalog = read(P / "INPUTS.json")["sources"]
    selected = sys.argv[2:]
    for sid in selected or list(catalog):
        entry = catalog[sid]
        path = ROOT / entry["path"]
        print("SOURCE", sid, entry["path"])
        if path.suffix != ".json":
            continue
        def redact(value, key=""):
            if isinstance(value, dict):
                return {k: redact(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [redact(v, key) for v in value]
            if isinstance(value, str):
                if ("sha256" in key or "digest" in key or key.endswith("_id") or key.endswith("_ref") or key in {"id", "uid", "path", "url"}) and key not in {"task_id", "case_id"}:
                    return "<present>" if value else "<empty>"
                if any(token in value for token in ("cs_test_", "pi_", "ch_", "http://", "https://", "D:\\", "C:\\")):
                    return "<redacted string>"
            return value
        print(json.dumps(redact(read(path)), ensure_ascii=False, indent=2))

def ref(source, pointer):
    return {"source": source, "pointer": pointer}

def code(source, start, end):
    return {"source": source, "lines": [start, end]}

def field(status, layer, reason, refs):
    item = {"status": status, "layer": layer, "reason": reason, "refs": refs}
    if status in {"ORIGINAL_OBSERVED", "EXPLICIT_REAUTH"}:
        item["direct_binding"] = True
    return item

def build():
    budget_estimate("complete_four_journey_measurement", 6)
    inputs, spec = read(P / "INPUTS.json"), read(P / "SPEC.json")
    catalog = inputs["sources"]
    public = {sid: read(ROOT / entry["path"]) for sid, entry in catalog.items() if entry["path"].endswith(".json")}
    obj, cols, rows = private()
    if set(obj) != {"operation_id", "run_id", "order_id", "request_id", "payment_id", "resource_sha256"}:
        raise ValueError("unexpected_private_inventory_reassess_without_expansion")
    joins = {}
    timeline = []
    resume = public["owner:resume"]
    auth = public["h72:AUTHORIZATION.json"]
    parse = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
    for case in spec["cases"]:
        row = rows[case]
        journey = public[f"resumed:journey_{case}.json"]
        session_digest = hashlib.sha256(row["session_id"].encode()).hexdigest()
        tests = {"case_exact": row["case_id"] == case,
                 "session_to_journey_exact_sha256": session_digest == journey["original_session_sha256"],
                 "amount_currency_fixed": row["amount_minor"] == 100 and row["currency"] == "usd",
                 "ledger_created_before_journey": parse(row["created_at"]) < parse(journey["at"])}
        if case != "C01":
            click = public[f"resumed:payment_click_{case}.json"]
            tests.update(session_to_click_exact_sha256=session_digest == click["original_session_sha256"],
                         click_before_journey=parse(click["at"]) < parse(journey["at"]),
                         click_amount_currency_match=click["amount_minor"] == row["amount_minor"] and click["currency"] == row["currency"],
                         click_one_allow=click["gate_final_decision"] == "ALLOW" and click["gate_callback_count"] == 1,
                         resource_to_client_exact_sha256=row["resource_sha256"] == journey["delivery"]["client_sha256"],
                         intent_to_journey_exact_sha256=hashlib.sha256(row["intent_id"].encode()).hexdigest() == journey["intent_sha256"],
                         charge_to_journey_exact_sha256=hashlib.sha256(row["charge_id"].encode()).hexdigest() == journey["charge_sha256"],
                         owner_resume_precedes_click=parse(resume["human_message_at_utc"]) < parse(click["at"]) < parse(auth["expires_at_utc"]))
        else:
            tests.update(no_payment_or_delivery=journey["hosted_test_payments_clicked"] == 0 and journey["delivery_attempt_count"] == 0,
                         no_intent_or_charge=row["intent_id"] is None and row["charge_id"] is None,
                         provider_cancelled_unpaid=journey["provider_status"] == "expired" and journey["payment_status"] == "unpaid")
        if case == "N01":
            tests.update({"private_json_to_row_"+k: obj[k] == row[k] for k in obj})
            tests["session_to_original_readback"] = session_digest == public["p1:N01_ORIGINAL_SESSION_READBACK.json"]["checkout_session_sha256"]
            tests["initial_create_before_resume"] = parse(row["created_at"]) < parse(resume["human_message_at_utc"])
        else:
            tests["new_create_after_resume"] = parse(row["created_at"]) > parse(resume["human_message_at_utc"])
        if not all(tests.values()):
            raise ValueError("historical_join_or_timing_conflict:" + case)
        joins[case] = {"checks": tests, "amount_minor": row["amount_minor"], "currency": row["currency"], "final_ledger_state": row["state"],
                       "ledger_created_at": row["created_at"], "ledger_updated_at": row["updated_at"],
                       "timestamp_semantics": "operations表写入/状态更新时间；绝不代替mandate、confirmation或quote时间。",
                       "refs": [ref("PRIVATE:merchant_operations", f"/operations/{case}/{k}") for k in spec["private_sqlite_columns"]] + [ref(f"resumed:journey_{case}.json", "/original_session_sha256")]}
        timeline.extend([{"case": case, "event": "LEDGER_CREATED_NOT_AUTHORITY_TIME", "at_utc": row["created_at"], "refs": [ref("PRIVATE:merchant_operations", f"/operations/{case}/created_at")]},
                         {"case": case, "event": "JOURNEY_TERMINAL_OBSERVED", "at_utc": journey["at"], "refs": [ref(f"resumed:journey_{case}.json", "/at")]}])
        if case != "C01":
            timeline.append({"case": case, "event": "PAYMENT_CLICK_RECEIPT_POST_CALLBACK", "at_utc": click["at"], "refs": [ref(f"resumed:payment_click_{case}.json", "/at")]})
    timeline.extend([{"case": "ALL", "event": "OWNER_INITIAL_TASK_GRANT", "at_utc": auth["granted_at_utc"], "refs": [ref("h72:AUTHORIZATION.json", "/granted_at_utc")]},
                     {"case": "ALL", "event": "OWNER_EXPLICIT_TASK_RESUME", "at_utc": resume["human_message_at_utc"], "refs": [ref("owner:resume", "/human_message_at_utc")]},
                     {"case": "ALL", "event": "OWNER_TASK_PERMISSION_END", "at_utc": auth["expires_at_utc"], "refs": [ref("h72:AUTHORIZATION.json", "/expires_at_utc")]}])
    write("derived/JOINS_AND_TIMELINE.json", {"schema": "h73-joins/v1", "joins": joins, "timeline": sorted(timeline, key=lambda e: e["at_utc"]), "original_domain_expiry": "UNKNOWN", "real_identity_source": "UNKNOWN_REAL_SOURCE", "no_private_identifiers_exported": True})
    # Full inspection, not keyword hits alone: catalog the JSON documents' key shapes.
    authority_keys = {"mandate", "confirmation", "confirmation_record", "gate_context", "context", "authority_ref", "authority_version", "mandate_id", "confirmation_id", "confirmed_at", "quote_expires_at", "authorized_order_hash"}
    json_audit = []
    for sid, value in public.items():
        leaves = structure(value)
        json_audit.append({"source": sid, "kind": catalog[sid]["kind"], "top_keys": sorted(value) if isinstance(value, dict) else [],
                           "domain_authority_named_leaves": [v["pointer"] for v in leaves if any(t in authority_keys for t in v["pointer"].split("/"))],
                           "role": "任务许可，不是用户领域确认" if catalog[sid]["kind"] == "owner_permission" else "历史观察；不把结果标志当完整输入快照"})
    write("derived/OBSERVATION_SHAPES.json", {"schema": "h73-observation-shapes/v1", "public_json": json_audit,
          "private_json_top_keys": sorted(obj), "operations_columns": cols,
          "absence_scope": "仅冻结公共JSON、白名单完整JSON和operations固定列；其他私有原件未读，不声称全局不存在。"})
    if any(item["domain_authority_named_leaves"] for item in json_audit) or authority_keys.intersection(cols):
        raise ValueError("domain_snapshot_candidate_requires_in_method_semantic_review")
    functions = []
    for sid, entry in catalog.items():
        if entry["kind"] != "code":
            continue
        tree = ast.parse((ROOT / entry["path"]).read_text(encoding="utf-8"))
        functions.append({"source": sid, "path": entry["path"], "definitions": [{"name": node.name, "lines": [node.lineno, node.end_lineno]} for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))]})
    write("derived/STATIC_PATH.json", {"schema": "h73-static-path/v1", "method": "AST/text inspection only; no import or execution of historical/product modules", "definitions": functions,
          "path": [
              {"step": "工厂在调用时合成领域对象和确认", "refs": [code("h72_operation", 16, 65), code("product:models.py", 91, 103), code("product:trusted_execution/confirmation.py", 96, 119)]},
              {"step": "初次N01先存六个标识后调用创建gate；记录URL校验失败，原会话后来被直接读回", "refs": [code("h72_listener_n01", 176, 208), ref("p1:LISTENER_AND_N01_RESULT.json", "/n01_precreate_original_binding_checked"), ref("p1:N01_ORIGINAL_SESSION_READBACK.json", "/session_present")]},
              {"step": "N01恢复用原operation后缀调用同工厂，静态保留order标识但重建时间", "refs": [code("h72_four_journeys", 49, 69), code("h72_operation", 16, 65)]},
              {"step": "另三例登记、创建并绑定会话；同对象用于付款前复核", "refs": [code("h72_four_journeys", 82, 110), code("h72_four_journeys", 122, 198), code("product:adapters/stripe_checkout.py", 105, 157)]},
              {"step": "ledger保存操作/会话/金额/资源及结果，表中没有原确认、授权版本或领域有效期", "refs": [code("product:stripe_checkout_lab.py", 39, 51), code("product:stripe_checkout_lab.py", 102, 139)]},
              {"step": "R01只读原付款恢复；D01成功收字节后的收据故障恢复", "refs": [code("h72_four_journeys", 332, 388), code("product:stripe_checkout_lab.py", 287, 347)]}
          ], "historical_execution_proof": "只来自冻结观察/白名单记录；AST存在不代表当时执行。"})
    cells = []
    for case in spec["cases"]:
        journey_sid = f"resumed:journey_{case}.json"
        jr = [ref(journey_sid, "/original_session_sha256")]
        dbrefs = [ref("PRIVATE:merchant_operations", f"/operations/{case}/{key}") for key in ("operation_id", "order_id", "request_id", "payment_id", "session_id")]
        for boundary in spec["boundaries"]:
            applicable = (case, boundary) != ("C01", "PRE_PAYMENT")
            if not applicable:
                reason = "C01创建后取消且零付款、零交付，没有实际付款前边界；provider expired是会话取消，不是领域确认过期。"
                fields = {key: field("NOT_APPLICABLE", "EXTERNAL_PAYMENT", reason, [ref(journey_sid, "/hosted_test_payments_clicked"), ref(journey_sid, "/delivery_attempt_count")]) for key in spec["fields"]}
                cells.append({"case": case, "boundary": boundary, "applicable": False, "reason": reason, "fields": fields, "time_evaluation": "NOT_APPLICABLE", "time_evidence": []})
                continue
            reasons = {
                "SESSION_CREATE": "原创建边界；后存操作行和原会话收据可精确联结，但不是执行前完整领域对象快照。",
                "PRE_PAYMENT": "实际付款点击边界；收据是回调后的历史观察，不能据其ALLOW倒推所有原输入。",
                "RECOVERY_OR_TERMINAL": {"N01": "续行原会话后付款与交付终态；不创建第二会话。", "C01": "原会话取消/未付终态，不要求新的付款确认。", "R01": "付款后UNKNOWN→商户重启→只读原付款对账，不要求重新付款或另续付费授权。", "D01": "交付记账/收据故障恢复与通知重放去重；不外推HTTP传输重试。"}[case]
            }
            fields = {
                "operation_binding": field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", "当前保留历史操作行的order/request/payment/session与该旅程会话摘要精确联结；仅证明原业务操作/会话身份，未保存该边界执行前的完整授权关系。", dbrefs + jr),
                "authority_scope_version": field("CODE_RECONSTRUCTED", "CODE_STRUCTURE", "工厂定义USD1、合成merchant/digital、agent及v1默认；选定历史JSON与operations没有mandate/authority_version快照。只可静态说明构造规则，不能还原当时实际授权对象。", [code("h72_operation", 16, 40), code("product:models.py", 91, 103), code("product:stripe_checkout_lab.py", 39, 51)]),
                "amount_currency_payee_resource": field("CODE_RECONSTRUCTED", "CODE_STRUCTURE", "该历史行直接保留100 minor/usd/resource摘要且与实收资源联结；完整tuple中的payee仅在工厂静态合成，故全字段不标原始观察。会话相等/金额相同不代替收款方和授权绑定。", [ref("PRIVATE:merchant_operations", f"/operations/{case}/{key}") for key in ("amount_minor", "currency", "resource_sha256")] + [code("h72_operation", 23, 40)]),
                "confirmation_binding": field("MISSING", "DOMAIN_AUTHORITY", "在已完整清点的公共JSON、N01六键JSON及operations固定列中，未保存该边界的confirmation_id、原确认内容/hash、authority/order版本绑定；代码能构造但不代表原确认存在或不存在于其他未授权来源。", [code("h72_operation", 58, 65), code("product:stripe_checkout_lab.py", 39, 51)] + jr + [ref("PRIVATE:merchant_operations", f"/operations/{case}/order_id")]),
                "validity_times": field("CODE_RECONSTRUCTED", "CODE_STRUCTURE", "仅代码给出调用时t、mandate=t+1h、quote/confirmation=t+30min、confirmed=t-2s；没有原领域时间，operations created_at/updated_at及收据at不是原确认时间，expiry只能UNKNOWN。", [code("h72_operation", 19, 24), code("h72_operation", 26, 29), code("h72_operation", 58, 62), ref("PRIVATE:merchant_operations", f"/operations/{case}/created_at")]),
                "provenance_origin": field("CODE_RECONSTRUCTED", "CODE_STRUCTURE", "工厂构造local-test主体和USER_CONFIRMED/PROTOCOL_VERIFIED标签；这是受控合成标记。无原发行者、真实用户认证、持有证明或签名信任源的直接证据；负责人运行许可与真实身份分开。", [code("h72_operation", 41, 57), code("product:models.py", 82, 87)]),
            }
            if boundary == "SESSION_CREATE":
                if case == "N01":
                    fields["execution_observation"] = field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", "初次创建运行记录报URL校验失败且native_created=false；稍后精确原操作匹配读回1个open/unpaid会话，区分本地收据失败和外部已建事实，不改旧报告。", [ref("p1:LISTENER_AND_N01_RESULT.json", "/reason_code"), ref("p1:LISTENER_AND_N01_RESULT.json", "/native_checkout_created"), ref("p1:N01_ORIGINAL_SESSION_READBACK.json", "/matched_operation_count"), ref("p1:N01_ORIGINAL_SESSION_READBACK.json", "/session_status")] + jr)
                    fields["renewal_or_recovery_basis"] = field("NOT_APPLICABLE", "TASK_PERMISSION", "初次创建在08:54:39Z续行前，由初始任务许可覆盖，不倒套后来的续授。此处不是原领域授权或用户确认充分性的结论。", [ref("h72:AUTHORIZATION.json", "/granted_at_utc"), ref("h72:AUTHORIZATION.json", "/expires_at_utc"), ref("owner:resume", "/human_message_at_utc"), ref("PRIVATE:merchant_operations", "/operations/N01/created_at")])
                else:
                    fields["execution_observation"] = field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", "本例历史operations行保存唯一session，精确联结旅程终态；只能后验确认会话存在和操作绑定，未保存独立创建gate的完整原输入。", jr + [ref("PRIVATE:merchant_operations", f"/operations/{case}/session_id"), ref("PRIVATE:merchant_operations", f"/operations/{case}/created_at")])
                    fields["renewal_or_recovery_basis"] = field("EXPLICIT_REAUTH", "TASK_PERMISSION", "负责人明确续行同H72四旅程且保留原预算/截止；续授早于本例登记。只认任务运行层，不将原话提升为真实用户领域确认或身份认证。", [ref("owner:resume", "/human_quote"), ref("owner:resume", "/scope"), ref("owner:resume", "/human_message_at_utc"), ref("owner:resume", "/original_authorization_expires_at_utc"), ref("PRIVATE:merchant_operations", f"/operations/{case}/created_at")])
            elif boundary == "PRE_PAYMENT":
                click_sid = f"resumed:payment_click_{case}.json"
                fields["execution_observation"] = field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", "原付款点击收据记录同会话、100 minor/usd、ALLOW、callback_count=1。收据产生在回调后，是执行观察而不是执行前授权快照。", [ref(click_sid, "/" + key) for key in ("at", "original_session_sha256", "amount_minor", "currency", "gate_final_decision", "gate_callback_count")])
                fields["renewal_or_recovery_basis"] = field("EXPLICIT_REAUTH", "TASK_PERMISSION", "08:54:39Z负责人明确继续原任务，发生在本点击前且原任务截止内；N01原会话沿用合法。该任务许可不补造领域确认、版本、收款方或有效期，也不能据缺记录认定越权。", [ref("owner:resume", "/human_quote"), ref("owner:resume", "/scope"), ref("owner:resume", "/human_message_at_utc"), ref("owner:resume", "/original_authorization_expires_at_utc"), ref(click_sid, "/at")] + jr)
            else:
                obs = {"N01": ["provider_payment_status", "new_checkout_sessions", "hosted_test_payments_clicked", "delivery/successful_delivery_count"], "C01": ["provider_status", "payment_status", "hosted_test_payments_clicked", "delivery_attempt_count"], "R01": ["unknown_before_restart", "actual_merchant_restarts", "recovery_status", "retry_allowed", "delivery/successful_delivery_count"], "D01": ["same_signed_event_replay_deduplicated", "successful_delivery_once", "delivery/delivery_attempts", "delivery/successful_delivery_count"]}[case]
                fields["execution_observation"] = field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", reasons[boundary] + "仅本例历史收据和精确操作联结支持该窄范围终态。", [ref(journey_sid, "/"+key) for key in obs] + jr)
                fields["renewal_or_recovery_basis"] = field("ORIGINAL_OBSERVED", "EXTERNAL_PAYMENT", reasons[boundary] + "历史记录不显示第二付款；不是领域授权重新生效。任务许可另见owner:resume。", [ref(journey_sid, "/"+key) for key in obs] + [ref("owner:resume", "/human_quote")])
            cells.append({"case": case, "boundary": boundary, "applicable": True, "reason": reasons[boundary], "fields": fields,
                          "time_evaluation": "UNKNOWN", "time_evidence": [ref("PRIVATE:merchant_operations", f"/operations/{case}/created_at"), ref(journey_sid, "/at"), code("h72_operation", 19, 24)],
                          "time_reason": "领域原确认/授权/报价时间未观察；本边界expiry未知。任务许可时序独立可核；恢复不引入新付款确认义务。"})
    matrix = {"schema": "h73-matrix/v1", "task_id": P.name, "method_version": "one-off-offline-v1", "cells": cells,
              "status_interpretation": "ORIGINAL_OBSERVED且EXTERNAL_PAYMENT仅原历史执行/标识观察（可后于边界）；EXPLICIT_REAUTH且TASK_PERMISSION仅负责人运行许可。DOMAIN_AUTHORITY没有任何ORIGINAL_OBSERVED/EXPLICIT_REAUTH声明；完整领域绑定必须有执行前原件，不能用ALLOW结果替代。"}
    write("MATRIX.json", matrix)
    breaks = []
    for case in ("N01", "R01", "D01"):
        sid = f"resumed:payment_click_{case}.json"
        breaks.append({"family": "ORIGINAL_DOMAIN_AUTHORITY_SNAPSHOT_NOT_RETRACEABLE_IN_SELECTED_STORES", "kind": "AUDIT_EVIDENCE_GAP", "case": case, "boundary": "PRE_PAYMENT", "field": "confirmation_binding",
                       "refs": [ref(sid, "/original_session_sha256"), ref(sid, "/gate_final_decision"), ref(sid, "/gate_callback_count"), ref("PRIVATE:merchant_operations", f"/operations/{case}/session_id"), ref("PRIVATE:merchant_operations", f"/operations/{case}/order_id")],
                       "reason": "此独立历史点击收据ALLOW/1与本例操作行精确联结，但完整收据键和operations列均没有其所消费原confirmation/authority版本/时间快照引用；完整白名单私有清点已完成。断点是该已存审计链无法回指原领域事实，不是错误放行；其他私有原件未读，不声称全局无记录。"})
    result = {"schema": "h73-result/v1", "task_id": P.name, "decision": "RECOMMEND_MINIMAL_CAPABILITY",
              "rationale": "已完整清点33个公共源及两白名单私有材料；N01/R01/D01三个不同旅程的真实历史ALLOW/1点击收据均与对应唯一操作行精确联结，而这些已存执行审计记录缺少所消费原领域确认/授权版本/有效期的可回查快照引用。这是测得的重复审计事实断点（3个独立历史边界），不是仅重复同工厂代码或已知合成身份。明确08:54:39Z负责人续行许可有效覆盖任务运行；无法核原领域时刻，不能认定过期、无确认或越权。建议后续仅建设原授权事实保存和读取接缝，由Evaluator另冻合同；不扩大为真实身份或生产支付。",
              "identity_assurance": "UNKNOWN_REAL_SOURCE", "product_delta": "NOT_APPLICABLE", "historical_verdicts_preserved": True,
              "private_inventory": {"n01_top_keys": sorted(obj), "operations_columns": cols, "cases_present": sorted(rows)}, "common_breaks": breaks,
              "next_package": {
                  "capability": "仅使受控Stripe操作保存并回查实际消费的原领域授权/确认快照及明确续授关系；不可用重建对象回填历史原件。",
                  "consumer": "现有StripeLabLedger操作读取、StripeCheckoutAdapter付款前校验和N01恢复加载调用点；R01只读原付款对账继续独立。",
                  "seam": "在现有操作登记/执行前保存一个最小不可变authority事实对象或内容摘要引用，绑定operation、order及version、authority及version、amount/currency/payee/resource、confirmation内容/hash与confirmed_at/expires_at/quote期限、来源类别；恢复加载验证原对象。明确续授另建新事实并关联旧事实及任务许可，缺原件返回明确未知/需确认，不默默按当前时间重建。最终形态待Evaluator合同决策，不在H73实现。",
                  "same_baseline_controls": "同一冻结基线、隔离离线副本：原对象保存→恢复一致为正对照；改版本/收款方/金额/内容/资源及原确认到期、缺快照、仅改当前时间重建为负对照；真实明确续授另对象方可恢复新执行资格。R01已付只读查询不要求新付费确认、C01零付款、D01仅记账恢复作为守护边界。历史H72原件不回填、不重付。",
                  "estimated_cost": "估计单一最小能力包Executor约90分钟、独立Evaluator约45分钟；0新增外部/模型服务费用，不继承H73或H72权限。实施与必要回归必须重新冻结预算、AC和来源，超出即停止。",
                  "residual_risks": "原合成确认无法追溯还原；未授权私有材料是否另含快照未知，需独立Evaluator回查本包允许源后判断是否值得建设。持久化不证明真实用户同意、强认证、签名发行者、密钥治理、生产结算或合规；新增事实对象需最小化数据和完整性保护。"
              },
              "stop_or_unblock_condition": "本轮取证充分即停止，不继续加样本或产品实现。Evaluator独立逐源核三历史断点及既有消费者；若只是既知边界或找到充分原始事实则STOP_VIEW，缺必要来源则INPUT_LIMIT；只有共同断点成立才另冻上述单一能力，潜在UNSAFE_ALLOW则STOP_ESCALATE。",
              "measurements": {"cases": 4, "boundaries": 12, "field_entries": 96, "applicable_boundaries": 11, "observed_payment_clicks": 3, "clicks_exactly_joined_to_operations": 3, "direct_original_domain_authority_snapshots_in_allowed_records": 0, "snapshot_count_scope": "仅冻结源内可回查原件；不是历史原对象实际存在数或全局存在数", "unsafe_allow_proved": False, "domain_expiry": "UNKNOWN", "statuses": dict(Counter(f["status"] for c in cells for f in c["fields"].values()))},
              "competing_explanations": ["合法负责人续行解释任务为何继续，不补造领域原快照，也不是越权证据。", "工厂每次以当前时间合成是已知测试机制；本次新增测量是三份独立历史点击收据与实际白名单操作行联结后的缺引用，不能单凭该机制宣称漏洞。", "其他未授权私有输入可能保存额外事实；未读取不等于不存在。推荐限于已观察审计链，若独立复核必须依赖那些材料则INPUT_LIMIT。"],
              "external_requirement_impact": {"profile": "PCAC-AGENTPAY", "requirement_ids": ["PCAC-07", "PCAC-08", "PCAC-09", "PCAC-12", "PCAC-15", "PCAC-20"], "applicability": "CORE/ADAPTER/EVIDENCE_ONLY按冻结合同", "maturity_before": "UNCHANGED_PRODUCT_MATURITY", "maturity_after": "UNCHANGED_PRODUCT_MATURITY", "measurement_before": "unknown", "measurement_after": "measured scoped audit gap; original expiry and real identity unknown", "test_evidence": "冻结六VP及六损坏控制；正式成绩见L2，独立L3待Evaluator", "trace_evidence": ["MATRIX.json", "derived/JOINS_AND_TIMELINE.json", "derived/SOURCE_INVENTORY.json"], "residual_risk": "不构成产品增量、真实身份/凭据治理/签名能力或监管合规结论。"}}
    write("RESULT.json", result)
    print(json.dumps({"decision": result["decision"], "measurements": result["measurements"]}, ensure_ascii=False))

def checker():
    spec = importlib.util.spec_from_file_location("h73_frozen_checker", P / "CHECK.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def l1():
    budget_estimate("task_local_L1_reference_and_claim_check", 2)
    c = checker()
    matrix, result = read(P / "MATRIX.json"), read(P / "RESULT.json")
    c.validate_decision(result, matrix)
    refs = []
    def walk(value):
        if isinstance(value, dict):
            if "source" in value and ("pointer" in value or "lines" in value):
                c.check_ref(value)
                refs.append(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
    for name in ("MATRIX.json", "RESULT.json", "derived/STATIC_PATH.json", "derived/JOINS_AND_TIMELINE.json"):
        walk(read(P / name))
    for cell in matrix["cells"]:
        if cell["time_evaluation"] not in {"UNKNOWN", "NOT_APPLICABLE"}:
            raise ValueError("unobserved_original_expiry_claim")
        for value in cell["fields"].values():
            if value["layer"] == "DOMAIN_AUTHORITY" and value["status"] in {"ORIGINAL_OBSERVED", "EXPLICIT_REAUTH"}:
                raise ValueError("no_direct_domain_original_available")
    write("derived/L1_REFERENCE_CHECK.json", {"schema": "h73-l1/v1", "at_utc": now(), "exit_code": 0, "references_resolved": len(refs), "role": "Executor self-check only; not L3", "domain_original_claims": 0, "expiry_known_claims": 0, "product_imports": 0})
    print(json.dumps({"L1": "PASS", "references_resolved": len(refs), "not_L3": True}))

def l2():
    budget_estimate("formal_public_L2", 4)
    ledger = read(P / "ATTEMPT_LEDGER.json")
    attempt = ledger["l2_attempts"] + 1
    if attempt > 2:
        raise ValueError("l2_limit")
    out = P / f"evidence/l2_attempt_{attempt:03d}"
    if out.exists():
        raise ValueError("never_overwrite_formal_attempt")
    ledger["l2_attempts"] = attempt
    ledger["events"].append({"event": "L2_BEGIN", "at_utc": now(), "attempt": attempt})
    write("ATTEMPT_LEDGER.json", ledger)
    out.mkdir(parents=True)
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py"), "--repo", ".", "--plan", (P / "VALIDATION_PLAN.yaml").relative_to(ROOT).as_posix(), "--out", out.relative_to(ROOT).as_posix(), "--mode", "executor"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=480)
    # Runner outputs are kept raw locally; never rewrite meta/stdout/stderr triplets.
    (P / f"derived/L2_RUNNER_{attempt:03d}.stdout.log").write_bytes(proc.stdout)
    (P / f"derived/L2_RUNNER_{attempt:03d}.stderr.log").write_bytes(proc.stderr)
    ledger = read(P / "ATTEMPT_LEDGER.json")
    ledger["events"].append({"event": "L2_END", "at_utc": now(), "attempt": attempt, "exit_code": proc.returncode})
    write("ATTEMPT_LEDGER.json", ledger)
    gate = read(out / "L2-GATE.json") if (out / "L2-GATE.json").exists() else {}
    print(json.dumps({"attempt": attempt, "exit_code": proc.returncode, "gate_result": gate.get("result"), "checks_total": gate.get("checks_total"), "mandatory_failures": gate.get("mandatory_failures")}))
    if proc.returncode:
        raise ValueError("formal_L2_failed_preserve_attempt")

def report():
    ledger = read(P / "ATTEMPT_LEDGER.json")
    attempt = ledger["l2_attempts"]
    gate_rel = f"evidence/l2_attempt_{attempt:03d}/L2-GATE.json"
    gate = read(P / gate_rel)
    if gate["result"] != "PASS" or gate["checks_total"] != 6:
        raise ValueError("report_requires_six_check_public_L2")
    status = subprocess.check_output(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=ROOT).decode("utf-8")
    (P / "derived/FINAL_STATUS.txt").write_text(status, encoding="utf-8")
    diff = subprocess.check_output(["git", "diff", "--", "CURRENT.md"], cwd=ROOT)
    (P / "derived/CURRENT_WORKSPACE_DIFF.patch").write_bytes(diff)
    frozen = read(P / "FREEZE.json")["files"]
    files = sorted(p.relative_to(P).as_posix() for p in P.rglob("*") if p.is_file() and "__pycache__" not in p.parts and (p.relative_to(P).as_posix() in {"ANALYZE.py", "MATRIX.json", "RESULT.json", "ATTEMPT_LEDGER.json", "REPORT.md", "SUBMISSION.json"} or p.relative_to(P).parts[0] == "derived" or (p.relative_to(P).parts[0] == "evidence" and p.relative_to(P).parts[1].startswith("l2_attempt_"))))
    write("derived/CHANGED_FILE_MANIFEST.json", {"schema": "h73-changed-files/v1", "task_local_outputs": sorted(set(files) | {"REPORT.md", "SUBMISSION.json", "derived/CHANGED_FILE_MANIFEST.json"}), "router": "CURRENT.md", "router_changes": "仅H73状态、角色、阶段、报告/复核路由及执行状态说明", "preexisting_unrelated_changes": "preserved; see INITIAL_STATUS/FINAL_STATUS", "hash_authority": "SUBMISSION.json files; excludes itself and CURRENT", "frozen_task_files_unchanged": len(frozen)})
    used = sum(((datetime.fromisoformat(w["end_utc"]) if w["end_utc"] else datetime.now(timezone.utc)) - datetime.fromisoformat(w["begin_utc"])).total_seconds() / 60 for w in ledger["windows"])
    prefix = P.relative_to(ROOT).as_posix()
    principal = "\n".join(f"| {name} | 新增 | {sha(P / name)} | {why} |" for name, why in [
        ("ANALYZE.py", "唯一离线方法、白名单读取、精确联结与交付"), ("MATRIX.json", "四旅程×三边界×八字段"), ("RESULT.json", "有界审计缺口与下一步建议"), ("ATTEMPT_LEDGER.json", "整窗成本和正式次数")])
    evidence = []
    for item in gate["checks"]:
        ev = item["evidence_id"]
        evidence.append(f"## {ev}\n\n- AC: {' '.join(item['ac'])}\n- Meta: {item['meta']}\n- Stdout: {item['stdout']}\n- Stderr: {item['stderr']}\n- Observed result: 退出{item['observed_exit_code']}，本项结构检查通过；不代替独立语义验收。\n")
    text = f"""# H73 Executor Report / 执行者报告

Task ID: {P.name}
Executor status: SUBMITTED_FOR_REVIEW
Baseline HEAD: {read(P / 'INPUTS.json')['head']}
Implementation commit: NONE

## Global position / 全局位置

项目目标是授权→绑定→受治理执行→恢复→审计可独立复核。r124：A–D本地阶段关闭，E受控本地代表闭合，F受控Stripe切片关闭；真实身份、凭据治理、签名信任源及生产PSP仍未知。第一瓶颈B-22是E–F接缝原授权事实能否连续回查，尚非已证实漏洞；比再加付款案例更接近信任链输入，也不依赖真实发行者/钱包的新权限。本轮H73仅measurement-only(只测量)，不建设产品能力。完成依据是固定来源、12边界、96字段及有证据四分支；独立Evaluator(评估者)核共同断点后才可另冻最小能力包，记录充分则STOP_VIEW(停止当前视图)，来源不足则INPUT_LIMIT(输入受限)，潜在零容忍反例则STOP_ESCALATE(停止并升级)。

## Workspace snapshot / 工作区快照

- 初始状态：derived/INITIAL_STATUS.txt；开窗时保留已有AGENTS/CURRENT/REMOTE/地图修改和历史未跟踪文件，未暂存。
- 最终状态：derived/FINAL_STATUS.txt；唯一任务外写入是CURRENT的本任务路由/状态说明。
- Saved diff: derived/CURRENT_WORKSPACE_DIFF.patch；SHA-256 {sha(P / 'derived/CURRENT_WORKSPACE_DIFF.patch')}。它是相对Git的整个CURRENT差异，包含此前制包变化，不能全部归因本轮。
- 本轮新增文件清单：derived/CHANGED_FILE_MANIFEST.json；每份交付原字节摘要以SUBMISSION.json为准。报告自身摘要仅放SUBMISSION，避免自引用。
- 首次及L2输入保护通过；保护清单2549项、冻结文件{len(frozen)}项与两个私有材料保持。最终路由变更后另作只读保护检查。
- 环境：既有Conda agent Python 3.12.13及PyYAML；PYTHONDONTWRITEBYTECODE=1。未导入或运行H72/产品/支付SDK，AST(静态语法树)和文本只读分析。

## Changed files / 改动文件

| File | Action | SHA-256 | Factual change |
| --- | --- | --- | --- |
{principal}

另新增derived中的清点、精确联结/时序、静态调用路径、引用自检、原/最终状态、差异/新增清单及检查原始输出；evidence/l2_attempt_001保留公共runner(公共验收运行器)六组三件套和原始Gate(门禁)。详细文件和摘要见SUBMISSION.json。src、tests、旧任务、地图、REMOTE、公共工具及本包冻结文件只读。

## Findings / 测量事实与限定

四旅程/三个边界共12格、96项全部完成，C01付款前八项均不适用；其余11边界原领域有效期均UNKNOWN(未知)。状态计数：原历史执行/标识观察26、仅代码重建44、指定记录缺确认字段11、不适用9、任务明确续授6。原始观察仅为外部记录及商户操作身份，不声称完整执行前领域授权；完整原领域授权/确认无任何ORIGINAL_OBSERVED或EXPLICIT_REAUTH声明。

两个白名单私有源均完整检查：N01 JSON仅operation_id/order_id/payment_id/request_id/resource_sha256/run_id六键；operations表15列且N01/C01/R01/D01四行存在。只在内存比较原标识，对外输出键/结构、必要时间金额及相等布尔值。N01六键逐项与操作行相等；四例session摘要与各旅程精确相等；三例点击摘要、金额/币种、原intent/charge及实收资源也逐例相等；C01无intent/charge。结果详见derived/JOINS_AND_TIMELINE.json，不用同额或相邻记录替代原对象。

N01最初创建记录报URL校验失败且native_created=false，08:33原操作匹配读回证明实际唯一会话open/unpaid；这些事实并存，不回写旧失败。08:54:39Z负责人明确继续原H72，三次实际点击均在续行之后和原任务截止前，收据记录ALLOW/1。该许可使任务层续行有来源，不是领域确认、真实身份认证或签名证明。

本次建议RECOMMEND_MINIMAL_CAPABILITY(建议另冻最小能力)：N01/R01/D01三份不同历史点击收据与对应操作行已精确联结，但完整收据结构和已读私有存储缺少所消费原confirmation/authority版本/有效期的快照引用。这是三处AUDIT_EVIDENCE_GAP(审计证据缺口)，不是UNSAFE_ALLOW(错误放行)。依据包括三份历史原收据及实际操作行，不能只靠同一工厂代码或合成身份标签计共同断点。其他未授权私有材料是否另有原件仍未知；本结论仅限已选审计链，不能推成全局不存在。

最小后继建议已放RESULT.next_package：沿现有操作登记/读取、付款前校验及N01恢复加载接缝，保存实际消费的最小不可变原授权/确认事实，明确续授另建并关联；不得当前时间重建后回填旧历史。正反对照、既有消费者、估计90+45分钟和残余风险均已列明，只供Evaluator(评估者)冻结下一合同，不构成实施授权。

恢复语义保持：R01是已付原交易UNKNOWN后只读对账，不能要求另付或新付款确认；D01仅成功收到字节后的交付记账/收据故障恢复，不外推HTTP传输重试；C01取消终态不构造付款。工厂给出的t±时长是代码规则，operations创建时间和session创建时间均不能填补原确认时间；未判定原授权有效或过期。

## L2 Task Gate

- Gate result: PASS
- Gate summary: {prefix}/{gate_rel}
- Validation plan: {prefix}/VALIDATION_PLAN.yaml
- Mandatory failures: 0；公共runner(公共验收运行器)六项均退出0，共{attempt}次L2。旧失败不覆盖，L3运行0次。
- VP-05的合法结构正对照通过，缺边界、缺字段、无效Pointer(对象定位引用)、代码冒充原证据、C01虚构付款、无共同断点建议能力六项损坏均由冻结真实检查函数拒绝，异常原因保留EV-05.stdout。内层检查是函数异常，无独立进程返回码；聚合VP-05进程退出码在meta中，不虚构六个子进程。
- L1(执行者自检)：derived/L1_REFERENCE_CHECK.json，521个决定性引用可解析；不是L3或逐AC验收。

{chr(10).join(evidence)}
## Acceptance mapping / 执行者逐AC证据索引

| AC | 执行证据 | 待独立复核事项 |
| --- | --- | --- |
| AC-01 | EV-01/06、INPUTS/FREEZE、最终只读保护 | 锁定字节/范围及全false权限 |
| AC-02 | EV-02、MATRIX、SOURCE_INVENTORY、JOINS | 12格96项及两私有源全部决定性引用 |
| AC-03 | EV-03、时序、STATIC_PATH、负责人续行原话 | 三层事实/原时间未知/C01/R01/D01适用语义 |
| AC-04 | EV-04、RESULT.common_breaks/next_package | 三独立历史审计断点是否足以另冻能力，而非仅旧边界 |
| AC-05 | EV-05、六项真实损坏拒绝原始输出 | 结构通过不能替代来源和语义判断 |
| AC-06 | EV-06、ATTEMPT_LEDGER、SUBMISSION | 角色整窗/次数/全0外部动作/提交摘要 |

## Impact comparison

- Measurement evidence: MATRIX.json、RESULT.json、derived/JOINS_AND_TIMELINE.json及EV-01至06。
- Before: 原授权事实充分性unknown(未知)，不得预填0/4失败；H72/H72R拒收及H72R2最终PASS/NOT_APPLICABLE/STOP保持。
- After: 固定12边界/96字段完成清点，三个独立点击在所选审计链缺原领域事实快照引用；合法任务续授可回查；原领域时刻、真实身份仍未知。
- Delta: 测量信息增加；产品能力、付款事实和合规成熟度不变。本任务one_off(一次测量)，产品增量NOT_APPLICABLE。
- Guardrail result: 2549保护输入、冻结文件及两私有输入保持；六项L2通过；未出现已证明错误放行，不重跑或改判旧包。
- Scope caveat: 只限四原旅程和冻结源。未读其他私有原件不等于不存在；真实用户授权、强认证、凭据/密钥治理和密码学签名信任源未覆盖。

## Iteration ledger / 迭代与成本

一次测量方法；预算内修正引用行和补全精确资源/收款摘要联结属于同方法自检，未改变字段、样本、来源或AC。首次尝试读取SPEC.md得到文件不存在，随后使用实际冻结SPEC.json，未将该命名探针当输入缺失；CodexPro连接不可用后使用本地工具；未增加来源或外部动作。这些读取/修正时间均计入整窗。

- Budget consumed / ceiling: Executor {used:.6f}/105分钟保守整窗；{'已关闭，包含报告与快照收尾预留上界' if ledger['windows'][-1]['end_utc'] else '当前开窗已逝，提交前将关闭并封存最终上界'}。从00:40Z开始保守覆盖最初读取，实际主动时间UNKNOWN(未知)，不以主动时间抵扣。
- 累计150分钟中Evaluator(评估者)独立45分钟完整保留；执行者上限余量{105-used:.6f}分钟，不能作为外部权限或续期。
- 正式次数：L2 {attempt}/2；L3 0/1。所有正式尝试和返回码见ATTEMPT_LEDGER；不另加无关测试。
- 外部api/network/install/service/browser/payment/model均0；模型项指额外模型服务。未提交、推送或改写历史。
- 独立制包费用见冻结PREPARATION及READINESS，不混入旧H72预算；本报告不冒称评估者费用已发生或最终任务通过。

## External requirement impact / 外部要求影响

profile=PCAC-AGENTPAY；PCAC-07/08/09/12、适用PCAC-15及PCAC-20按CORE/ADAPTER/EVIDENCE_ONLY(核心、承载外部事实、仅证据)区分。对象为本测量合同及原operation/mandate/order/confirmation；代码为锁定工厂/adapter/ledger的静态读取和ANALYZE；Test(验证)=六VP/六损坏/待独立语义回查；Evidence(证据)=本包L2、矩阵与时序。before/after产品成熟度不变，仅把指定审计链的事实充分性测为有界缺口；真实身份、强认证、凭据治理、签名和合规结论均不升级。逐项残余风险见RESULT.external_requirement_impact。

## Deviations and unresolved items / 偏差与未解决项

- 无合同语义、样本、来源、预算或权限扩张；未运行产品、旧门禁或外部服务。
- 其他未授权私有材料保持未读；这部分是否另含原事实UNKNOWN(未知)。若Evaluator(评估者)判定必须读取才能决策，应走INPUT_LIMIT(输入受限)，不能宣称全局不存在或扩大白名单。
- 原始确认时间及真实身份来源无法由当前代码补造；无已证实UNSAFE_ALLOW(错误放行)，不倒推付款未授权，不改旧窄范围成绩。
- 公共runner(公共验收运行器)原始meta的cwd等机器元数据在本地evidence中原样保存；不复制私有路径、原始外部标识、密钥、URL或webhook原文到公开测量视图/报告，未发布或提交原始证据。
- 独立L3及逐AC验收尚未执行；Executor(执行者)不签发任务PASS。按本包EXECUTOR_START将CURRENT交READY_FOR_REVIEW/Evaluator，下一产物REVIEW.md。
"""
    (P / "REPORT.md").write_text(text, encoding="utf-8")

def capture_local(label, command):
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8"))
    (P / f"derived/{label}.stdout.log").write_bytes(proc.stdout)
    (P / f"derived/{label}.stderr.log").write_bytes(proc.stderr)
    write(f"derived/{label}.meta.json", {"label": label, "at_utc": now(), "exit_code": proc.returncode, "role": "Executor", "scope": "local closeout check, not formal L2 or L3"})
    if proc.returncode:
        raise ValueError("closeout_check_failed:" + label)

def seal():
    budget_estimate("report_validation_snapshot_and_handoff", 5)
    ledger = read(P / "ATTEMPT_LEDGER.json")
    if ledger["windows"][-1]["end_utc"] is not None:
        raise ValueError("already_closed_no_silent_reopen")
    current_path = ROOT / "CURRENT.md"
    before = current_path.read_text(encoding="utf-8")
    if "state: EXECUTING" not in before or "current_role: Executor" not in before:
        raise ValueError("executor_handoff_role_required")
    report()
    validator = ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"
    capture_local("VALIDATOR_EXECUTING", [sys.executable, "-B", str(validator), "--repo", ".", "--current", "CURRENT.md"])
    after = before.replace("state: EXECUTING", "state: READY_FOR_REVIEW", 1).replace("current_role: Executor", "current_role: Evaluator", 1).replace("execution_phase: H73_OFFLINE_MEASUREMENT_EXECUTING", "execution_phase: H73_L2_COMPLETE_AWAITING_INDEPENDENT_L3", 1)
    after = after.replace(f"next_artifact_path: {P.relative_to(ROOT).as_posix()}/REPORT.md", f"next_artifact_path: {P.relative_to(ROOT).as_posix()}/REVIEW.md", 1)
    start = after.index("## Current action / 当前动作")
    end = after.index("## Historical preservation / 历史保护")
    after = after[:start] + "## Current action / 当前动作\n\nH73 Executor已完成冻结离线测量及六项公共L2，REPORT与SUBMISSION交独立Evaluator；当前为READY_FOR_REVIEW，不是任务PASS。Evaluator先核SUBMISSION，再按L3_PROCEDURE完成逐源语义回查与唯一L3。Executor已关闭成本窗，Evaluator另开独立COST；不修改接受快照。\n\n所有外部权限保持false；不得继承旧支付/运行预算。下一产物为本包REVIEW.md，是否另冻能力包由Evaluator依测量证据判断。\n\n" + after[end:]
    current_path.write_text(after, encoding="utf-8")
    try:
        report()
        capture_local("VALIDATOR_READY", [sys.executable, "-B", str(validator), "--repo", ".", "--current", "CURRENT.md"])
        capture_local("FINAL_PRESERVATION", [sys.executable, "-B", str(P / "CHECK.py"), "preservation"])
        capture_local("FINAL_DIFF_CHECK", ["git", "diff", "--check", "--", "CURRENT.md"])
        live_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        if live_head != read(P / "INPUTS.json")["head"]:
            raise ValueError("head_drift_stop")
    except Exception:
        current_path.write_text(before, encoding="utf-8")
        raise
    # A short conservative closure bound includes final serialization/hashing.
    close_at = datetime.now(timezone.utc).timestamp() + 3
    core_names = ["ANALYZE.py", "MATRIX.json", "RESULT.json", f"evidence/l2_attempt_{ledger['l2_attempts']:03d}/L2-GATE.json"]
    ledger["submission_artifact_sha256"] = {name: sha(P / name) for name in core_names}
    ledger["digest_scope"] = "Core measured artifacts and final passing L2; final report/ledger and all raw/derived digests are in SUBMISSION.json to avoid circular self-hashes."
    ledger["windows"][-1]["end_utc"] = datetime.fromtimestamp(close_at, timezone.utc).isoformat()
    ledger["events"].append({"event": "END", "at_utc": ledger["windows"][-1]["end_utc"], "basis": "conservative closeout bound including final report/snapshot serialization; wait until reached before returning"})
    write("ATTEMPT_LEDGER.json", ledger)
    report()
    files = {}
    for name in ("ANALYZE.py", "MATRIX.json", "RESULT.json", "ATTEMPT_LEDGER.json", "REPORT.md"):
        files[name] = sha(P / name)
    for base in (P / "derived", P / "evidence"):
        for path in base.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and (base.name == "derived" or path.relative_to(base).parts[0].startswith("l2_attempt_")):
                files[path.relative_to(P).as_posix()] = sha(path)
    final_attempt = ledger["l2_attempts"]
    gate_path = f"evidence/l2_attempt_{final_attempt:03d}/L2-GATE.json"
    write("SUBMISSION.json", {"schema": "h73-submission/v1", "task_id": P.name, "executor_status": "SUBMITTED_FOR_REVIEW", "baseline_head": live_head,
          "l2_gate": {"path": gate_path, "sha256": files[gate_path]}, "files": dict(sorted(files.items())),
          "submitted_at_utc": ledger["windows"][-1]["end_utc"], "executor_charged_minutes": (close_at - datetime.fromisoformat(ledger["windows"][0]["begin_utc"]).timestamp()) / 60,
          "l3_executed_by_executor": False, "independent_review": "PENDING; follow L3_PROCEDURE.md", "public_original_identifiers_exported": False})
    checker().submission()
    if datetime.now(timezone.utc).timestamp() > close_at:
        raise ValueError("closure_bound_exceeded_snapshot_not_ready")
    time.sleep(max(0, close_at - datetime.now(timezone.utc).timestamp()))
    print(json.dumps({"state": "READY_FOR_REVIEW", "role": "Evaluator", "L2": "6/6 PASS", "L3": "NOT_RUN", "snapshot_files": len(files), "submission_sha256": sha(P / "SUBMISSION.json"), "executor_charged_minutes": (close_at - datetime.fromisoformat(ledger["windows"][0]["begin_utc"]).timestamp()) / 60, "external_actions": ledger["external_actions"]}))

if __name__ == "__main__":
    try:
        {"begin": begin, "inventory": inventory, "inspect": inspect, "build": build, "l1": l1, "l2": l2, "report": report, "seal": seal}[sys.argv[1]]()
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "category": type(exc).__name__, "reason": str(exc) if isinstance(exc, ValueError) else "allowlisted_input_or_structure_unavailable"}))
        sys.exit(1)
