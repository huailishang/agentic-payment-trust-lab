"""H65R: source-grounded repair of structured consent and field-specific allowance unit.

Only frozen local sources. No network, product execution, replay, payment, or
H65/H64R extraction import. Evidence citations use physical Parquet row indices
and canonical hashes verified by the separate frozen CHECK.py.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
LOCK = json.loads((TASK / "INPUTS.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((TASK / "EXPECTED.json").read_text(encoding="utf-8"))
PRIOR = json.loads((ROOT / LOCK["prior_result"]).read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / ".task_envs/H64/parquet_reader"))
import pyarrow.parquet as pq  # noqa: E402

ROW_GROUPS = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def row_for(file, row_group, row_index, eid):
    key = (file, row_group)
    if key not in ROW_GROUPS:
        assert file in LOCK["readonly"], "unfrozen data source"
        ROW_GROUPS[key] = pq.ParquetFile(ROOT / file).read_row_group(row_group).to_pylist()
    row = ROW_GROUPS[key][row_index]
    assert row["episode_id"] == eid, "cross-episode evidence"
    return row


def pointer(obj, path):
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        obj = obj[int(seg)] if isinstance(obj, list) else obj[seg]
    return obj


def cite(file, group, index, eid, path, embedded=None):
    row = row_for(file, group, index, eid)
    raw = pointer(row, path)
    out = {"file": file, "row_group": group, "row_index": index,
           "pointer": path, "value_sha256": sha(raw)}
    if embedded:
        decoded = json.loads(raw)
        out.update({"embedded_pointer": embedded,
                    "decoded_value_sha256": sha(pointer(decoded, embedded))})
    return out


def rewrite_sibling_cite(original, eid, suffix):
    """Cite checkout from the exact same native request as an old amount."""
    field = original["embedded_pointer"].rsplit("/", 1)[0] + "/" + suffix
    return cite(original["file"], original["row_group"], original["row_index"],
                eid, original["pointer"], field)


def unique_citations(cites):
    seen, out = set(), []
    for item in cites:
        k = (item["file"], item["row_group"], item["row_index"],
             item["pointer"], item.get("embedded_pointer"))
        if k not in seen:
            seen.add(k)
            out.append(item)
    return out


def read_consent(e):
    eid = e["episode_id"]
    r = row_for(e["file"], e["row_group"], e["row_index"], eid)
    assert r["kind"] == "message" and r["actor"] == "shopper"
    assert r["seq"] == e["seq"] and isinstance(r["text"], str)
    args = json.loads(r["arguments"])
    consent = args["consent"]
    assert consent["given"] is True
    assert (consent["checkout_id"], consent["amount"], consent["currency"]) == (
        e["checkout_id"], e["raw_amount"], e["currency"])
    return {
        "seq": r["seq"], "actor": r["actor"], "kind": r["kind"],
        "given": consent["given"], "checkout_id": consent["checkout_id"],
        "raw_amount": consent["amount"], "currency": consent["currency"],
        "source_citation": cite(e["file"], e["row_group"], e["row_index"],
                                eid, "/arguments", "/consent"),
        "text_citation": cite(e["file"], e["row_group"], e["row_index"], eid, "/text"),
        "origin": "PUBLISHED_STRUCTURED_MESSAGE",
        "semantic_limit": "published_shopper_record_not_identity_or_signature_proof",
    }


def validate_no_other_consents(episodes):
    """Full six-episode inspection, not a text-only heuristic."""
    target_file = EXPECTED["consents"][0]["file"]
    turn_group = ROW_GROUPS[(target_file, 0)]
    seen = {eid: [] for eid in episodes}
    for i, row in enumerate(turn_group):
        eid = row.get("episode_id")
        if eid not in seen or row.get("actor") != "shopper" or row.get("kind") != "message":
            continue
        raw = row.get("arguments")
        if not isinstance(raw, str):
            continue
        try:
            parsed = json.loads(raw)
        except (ValueError, TypeError):
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("consent"), dict):
            seen[eid].append((i, row["seq"]))
    expected_by_id = {e["episode_id"]: [(e["row_index"], e["seq"])]
                      for e in EXPECTED["consents"]}
    for eid in episodes:
        assert seen[eid] == expected_by_id.get(eid, []), (
            f"unexpected consent shape/position: {eid}, {seen[eid]}"
        )
    return {eid: len(events) for eid, events in seen.items()}


def native_checkout_sources(eid, old):
    records = []
    for obs in old["source_payment_observations"]:
        if obs.get("checkout_citation"):
            assert obs["checkout_id"]
            records.append(obs["checkout_citation"])
    for obs in old["source_request_allowances"]:
        amount_cite = obs["amount_citation"]
        if "/allowance/max_amount" in amount_cite.get("embedded_pointer", ""):
            records.append(rewrite_sibling_cite(amount_cite, eid, "checkout_session_id"))
    out = unique_citations(records)
    for c in out:
        native = pointer(json.loads(pointer(
            row_for(c["file"], c["row_group"], c["row_index"], eid), c["pointer"]
        )), c["embedded_pointer"])
        expected_values = {a["checkout_id"] for a in
                           old["source_payment_observations"] + old["source_request_allowances"]}
        assert native in expected_values, "not native checkout"
    return out


def unit_fact_for_fourth(eid, old):
    target = EXPECTED["unit"]
    r = row_for(target["file"], target["row_group"], target["row_index"], eid)
    declaration = json.loads(r["tools"][8])
    assert declaration["function"]["name"] == "delegate_payment"
    assert pointer(declaration, target["embedded_pointer"]) == target["definition"]
    relevant = [o for o in old["source_request_allowances"]
                if o["call_id"] in ("call-32", "call-34")]
    assert {o["call_id"] for o in relevant} == {"call-32", "call-34"}
    assert len(relevant) == 3
    return {
        "field": "allowance.max_amount",
        "tool_name": "delegate_payment",
        "scope": "delegate_payment.request.allowance.max_amount",
        "status": "PROVEN", "definition": target["definition"],
        "unit": "minor_units",
        "applicable_call_ids": ["call-32", "call-34"],
        "definition_citation": cite(target["file"], target["row_group"],
                                    target["row_index"], eid,
                                    target["pointer"], target["embedded_pointer"]),
        "application_citations": [o["amount_citation"] for o in relevant],
        "non_applicable": ["wire.response_body.total", "pay.response.total",
                           "final_cart amount by analogy", "settled payment"],
        "reason": "官方工具字段定义直接说明delegate_payment.allowance.max_amount为最小货币单位，仅约束对应请求额度；不外推到支付回执total或资金完成。",
    }


def token_chain(eid, old, consent, checkouts, unit):
    """Trace the ACP delegate_payment call-34 without turning token into payment."""
    chain32 = next(c for c in old["native_call_chains"] if c["call_id"] == "call-32")
    chain34 = next(c for c in old["native_call_chains"] if c["call_id"] == "call-34")
    assert chain32["status"] == "PARTIAL" and not chain32["wire_citations"]
    assert chain34["status"] == "COMPLETE" and chain34["wire_citations"]
    assert chain34["result_citations"]
    request = next(o for o in old["source_request_allowances"]
                   if o["call_id"] == "call-34" and o["amount_citation"]["file"].endswith("wire/validation-00000-of-00001.parquet"))
    assert (request["raw_amount"], request["checkout_id"], request["currency_raw"].lower()) == (
        consent["raw_amount"], consent["checkout_id"], consent["currency"].lower())
    wire_ref = chain34["wire_citations"][0]
    wire = row_for(wire_ref["file"], wire_ref["row_group"], wire_ref["row_index"], eid)
    assert wire["source_call_id"] == "call-34" and wire["protocol"] == "acp"
    assert int(wire["status"]) == 201
    response = json.loads(wire["response_body"])
    assert isinstance(response.get("id"), str) and response["id"].startswith("vt-")
    assert "paid" not in response and "settled" not in response
    tool_ref = chain34["result_citations"][0]
    tool = row_for(tool_ref["file"], tool_ref["row_group"], tool_ref["row_index"], eid)
    assert tool["tool_call_id"] == "call-34" and tool["kind"] == "tool_result"
    # Preserve result as an observed delegate/token outcome, not financial settlement.
    citations = unique_citations([
        consent["text_citation"], consent["source_citation"], checkouts[0],
        unit["definition_citation"], request["amount_citation"],
        chain34["call_citation"], tool_ref, wire_ref,
        cite(wire_ref["file"], wire_ref["row_group"], wire_ref["row_index"],
             eid, "/response_body", "/id"),
    ])
    return {
        "complete_chain": True,
        "chain_citations": citations,
        "chain_edges": [
            {"from": "shopper.arguments.consent", "to": "native.checkout_session_id",
             "status": "PROVEN", "evidence": [consent["source_citation"], checkouts[0]]},
            {"from": "native.checkout_session_id", "to": "delegate_payment.call-34.allowance.max_amount",
             "status": "PROVEN", "evidence": [request["amount_citation"], unit["definition_citation"]]},
            {"from": "delegate_payment.call-34", "to": "acp.response.token_id",
             "status": "PROVEN", "evidence": [chain34["call_citation"], tool_ref, wire_ref]},
        ],
        "call_distinction": {
            "call-32": "harness request + tool result, wire absent; not the ACP wire path",
            "call-34": "ACP request, wire 201, tool result; token/allowance only",
        },
        "protocol_result_kind": "TOKEN_OR_ALLOWANCE",
        "protocol_result_evidence": {"protocol": "acp", "http_status": 201,
                                     "token_id_citation": citations[-1],
                                     "not_evidence_of_payment": True},
    }


def make_sample(eid, old, expected_consent):
    consents = [read_consent(expected_consent)] if expected_consent else []
    native = native_checkout_sources(eid, old)
    if consents:
        assert native, f"missing native checkout: {eid}"
        checkout_value = consents[0]["checkout_id"]
        for c in native:
            row = row_for(c["file"], c["row_group"], c["row_index"], eid)
            value = pointer(json.loads(pointer(row, c["pointer"])), c["embedded_pointer"])
            assert value == checkout_value, f"checkout mismatch: {eid}"
    unit_facts = [unit_fact_for_fourth(eid, old)] if eid == EXPECTED["unit"]["episode_id"] else []
    if consents:
        binding = {
            "scope": "published_episode_consent_record_to_checkout",
            "status": "PROVEN",
            "reason": "同一episode的shopper结构化arguments.consent明确给出given、checkout_id、amount和currency；原生checkout观察逐值相同。仅证实发布轨迹来源记录的绑定，不证明真实身份、签名或清算。",
        }
    else:
        binding = {
            "scope": "published_episode_consent_record_to_checkout",
            "status": "UNKNOWN",
            "reason": "已按原始turns对本episode逐条检查shopper.message.arguments.consent，未观察到已给定的结构化支付确认；不可从预算、金额相等或其他episode借用。",
        }
    if unit_facts:
        unit = {
            "status": "PROVEN",
            "target_scope": "delegate_payment.request.allowance.max_amount",
            "reason": "原始工具定义直接写明allowance.max_amount以minor units表示，并和call-32、call-34逐项请求引用相连；只证明该额度字段单位，不证明付款响应total的单位。",
        }
    elif old["source_payment_observations"]:
        unit = {
            "status": "PARTIAL",
            "target_scope": "reported_payment_or_completion_amount",
            "reason": "虽有该episode原生支付/完成报告的raw total、currency和checkout字段，但没有该具体response.total字段的直接单位契约；不得用final_cart或同额间接推定。",
        }
    else:
        unit = {
            "status": "UNKNOWN",
            "target_scope": "payment_or_allowance",
            "reason": "没有适用于该episode实际支付金额或额度字段的直接单位定义和足够原生支付结果，不能从静态final_cart规则推断已支付的币种单位。",
        }
    trace = {
        "complete_chain": False, "chain_citations": [],
        "chain_edges": [], "protocol_result_kind": (
            "REPORTED_COMPLETION" if old["source_payment_observations"] else "NONE"
        ),
    }
    if unit_facts:
        trace = token_chain(eid, old, consents[0], native, unit_facts[0])
    sample = {
        "episode_id": eid,
        "consent_records": consents,
        "native_checkout_citations": native,
        "field_units": unit_facts,
        "binding": binding,
        "unit": unit,
        **trace,
        "source_payment_observations": old["source_payment_observations"],
        "source_request_allowances": old["source_request_allowances"],
        "native_call_statuses": [
            {"call_id": chain["call_id"], "status": chain["status"], "tool": chain["tool"]}
            for chain in old["native_call_chains"]
        ],
        "missing_dimensions": (
            [] if trace["complete_chain"] else
            ["field_specific_protocol_result_unit" if consents else
             "structured_consent_and_native_payment_chain"]
        ),
        "independent_real_identity_verified": False,
        "independent_backend_settlement_observed": False,
    }
    return sample


def write_json(path, payload):
    file = TASK / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    started = now()
    mono = time.monotonic()
    result_path = TASK / "RESULT.json"
    assert not result_path.exists(), "one result version permitted"
    episode_ids = LOCK["episode_ids"]
    assert [s["episode_id"] for s in PRIOR["samples"]] == episode_ids
    # The only full six-episode scan is one frozen turns row group; exact
    # unit and native checkout source rows are read from frozen parquet refs.
    turn = EXPECTED["consents"][0]
    row_for(turn["file"], turn["row_group"], turn["row_index"], turn["episode_id"])
    count = validate_no_other_consents(episode_ids)
    consent_by_id = {e["episode_id"]: e for e in EXPECTED["consents"]}
    samples = [make_sample(eid, old, consent_by_id.get(eid))
               for eid, old in zip(episode_ids, PRIOR["samples"])]
    complete = [s["episode_id"] for s in samples if s["complete_chain"]]
    verdict = "CONTINUE_TO_REPLAY_BASELINE" if complete else "STOP_SOURCE_VIEW"
    result = {
        "task_id": TASK.name,
        "classification": "REFERENCE_ONLY",
        "source_scope": "published six CartTrace validation episodes",
        "samples": samples,
        "verdict": verdict,
        "reason": (
            "第4例可逐源闭合结构化确认→同例checkout→call-34额度请求与字段单位"
            "→ACP 201令牌/授权额度结果，但不是实付或真实清算。只建议另冻回放基线。"
            if complete else
            "四条确认与一个字段单位已恢复，但无单例跨全部边的直接证据链；停止本来源视图。"
        ),
        "complete_source_chain_episodes": complete,
        "consent_count_by_episode": count,
        "replay_executed": False,
        "product_effect_measured": False,
        "real_payment_or_settlement_verified": False,
    }
    # Writes one measurement version only; report and L2 are separate steps.
    write_json("RESULT.json", result)
    duration_min = max((time.monotonic() - mono) / 60, 0.01)
    ledger = {
        "task_id": TASK.name, "active_minutes": round(duration_min, 3),
        "sample_reads": len(episode_ids), "measurement_versions": 1,
        "formal_l2_attempts": 1,
        "network_calls": 0, "installation_calls": 0, "model_calls": 0,
        "product_calls": 0, "upstream_replay_calls": 0, "payment_calls": 0,
        "attempts": [
            {"kind": "frozen_source_analysis", "started_at": started,
             "finished_at": now(), "status": "SUCCEEDED",
             "result": "one RESULT.json; six frozen episodes; no replay"}
        ],
        "scope_note": "L2 attempt count reserved for immediate single official runner; validate after execution.",
    }
    write_json("ATTEMPT_LEDGER.json", ledger)
    write_json("derived/EDGE_AUDIT.json", {
        "consent_count_by_episode": count,
        "complete_source_chain_episodes": complete,
        "call32_wire_present": False, "call34_wire_present": True,
        "allowance_minimum_unit_field_only": True,
        "reported_payment_not_same_as_allowance_token": True,
    })
    print(json.dumps({"verdict": verdict, "source_chain_count": len(complete),
                      "consent_count": sum(count.values()), "episode_reads": len(episode_ids),
                      "status": "SUCCEEDED"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
