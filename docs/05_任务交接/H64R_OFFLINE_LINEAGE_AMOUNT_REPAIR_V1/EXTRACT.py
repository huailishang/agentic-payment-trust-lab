"""H64R: bounded, offline, source-cited extraction from six frozen CartTrace episodes.

No network, SDK, application, model, payment, acquisition, or replay operations.
Only reads the frozen H64 SELECTED.json and its already-acquired Parquet files.
The original H64 CHECK/MEASURE/ACQUIRE scripts are never imported or executed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = TASK.parent / "H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1"
sys.path.insert(0, str(ROOT / ".task_envs/H64/parquet_reader"))
import pyarrow as pa
import pyarrow.parquet as pq

assert pa.__version__ == "26.0.0"
TOOLS = {"pay", "send_payment_mandate", "delegate_payment", "shop_pay_payment_request"}
TURN_PATH = "data/turns/validation-00000-of-00001.parquet"
WIRE_PATH = "data/wire/validation-00000-of-00001.parquet"
TASK_ID = TASK.name


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":")).encode("utf-8")).hexdigest()


def json_read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_write(path, data):
    """Write via derived temporary path then replace; no old/frozen file writes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = TASK / "derived" / (path.name + ".write-in-progress")
    temp.parent.mkdir(parents=True, exist_ok=True)
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def citation(record, field, embedded=None, value=None):
    original = record["row"][field]
    c = {
        "file": (OLD.relative_to(ROOT) / "acquired" / record["rel"]).as_posix(),
        "kind": "parquet",
        "row_group": record["row_group"],
        "row_index": record["row_index"],
        "pointer": "/" + field.replace("~", "~0").replace("/", "~1"),
        "value_sha256": digest(original),
    }
    if embedded is not None:
        c["embedded_pointer"] = "/" + "/".join(
            str(k).replace("~", "~0").replace("/", "~1") for k in embedded)
        c["decoded_value_sha256"] = digest(value)
    return c


def source_rows(relative, episode_id):
    """Single pre-reserved episode read; keep native row-group positions."""
    path = OLD / "acquired" / relative
    reader = pq.ParquetFile(path)
    for group in range(reader.num_row_groups):
        for index, row in enumerate(reader.read_row_group(group).to_pylist()):
            if row.get("episode_id") == episode_id:
                yield {"rel": relative, "row_group": group,
                       "row_index": index, "row": row}


def decode_one(value):
    if not isinstance(value, str):
        return value if isinstance(value, dict) else None
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return None
    # A doubly encoded JSON string cannot be cited with one embedded_pointer,
    # and therefore must not be treated as a directly sourced object.
    return parsed if isinstance(parsed, dict) else None


def ancestors_for_numeric(data):
    """Yield numeric fields with dict ancestors, never infer currency or ID."""
    money_names = {"total", "amount", "max_amount", "amount_total",
                   "total_amount", "amount_due", "grand_total"}
    def walk(obj, path, parents):
        if isinstance(obj, dict):
            current = (obj, path)
            for k, v in obj.items():
                child_path = path + (k,)
                if k in money_names and type(v) in (int, float) and v >= 0:
                    yield child_path, v, (current,) + parents
                if isinstance(v, (dict, list)):
                    yield from walk(v, child_path, (current,) + parents)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, (dict, list)):
                    yield from walk(v, path + (i,), parents)
    yield from walk(data, (), ())


def nearest_field(parents, names):
    for obj, base in parents:
        for name in names:
            if name in obj and isinstance(obj[name], str) and obj[name]:
                return base + (name,), obj[name]
        # This fallback is only for a checkout object with an actual checkout- ID.
        if isinstance(obj.get("id"), str) and obj["id"].startswith("checkout-"):
            if "checkout" in names or "checkout_id" in names:
                return base + ("id",), obj["id"]
    return None, None


def get_path(data, path):
    for key in path:
        data = data[key]
    return data


def money_observations(record, field, call_id, origin, source_direction):
    body = decode_one(record["row"].get(field))
    if not isinstance(body, dict):
        return []
    status = str(body.get("status", "")).lower()
    output = []
    for amount_path, amount, parents in ancestors_for_numeric(body):
        currency_path, currency = nearest_field(parents, ("currency", "currency_code"))
        checkout_path, checkout = nearest_field(
            parents, ("checkout_id", "checkout_session_id", "cart_id", "checkout"))
        if not currency_path or not checkout_path or not isinstance(checkout, str):
            continue
        if not checkout.startswith("checkout-"):
            continue
        phase = "REQUEST" if source_direction == "request" else "UNKNOWN"
        if "allowance" in amount_path or amount_path[-1] == "max_amount":
            phase = "TOKEN_ALLOWANCE"
        if source_direction == "response" and status in {
                "completed", "paid", "success", "succeeded"}:
            phase = "REPORTED_COMPLETION"
        # A request is explicitly distinguished from a response; don't mislabel
        # request-side data as a tool/protocol response in the main observation set.
        observation = {
            "call_id": call_id,
            "seq": record["row"].get("seq"),
            "origin": origin if source_direction == "response" else "request_source",
            "phase": phase,
            "raw_amount": amount,
            "currency_raw": currency,
            "checkout_id": checkout,
            "amount_citation": citation(record, field, amount_path, amount),
            "currency_citation": citation(record, field, currency_path, currency),
            "checkout_citation": citation(record, field, checkout_path, checkout),
            "call_id_citation": citation(
                record, "source_call_id" if record["rel"] == WIRE_PATH
                else "tool_call_id" if source_direction == "response" else "call_id"),
            "unit_status": "UNKNOWN",
            "amount_minor": None,
            "unit_citations": [],
            "source_field": field,
        }
        output.append(observation)
    # Deduplicate overlapping traversal and preserve every distinct amount field.
    seen = set()
    unique = []
    for item in output:
        key = (item["amount_citation"]["embedded_pointer"],
               item["currency_citation"]["embedded_pointer"],
               item["checkout_citation"]["embedded_pointer"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def build_episode(choice):
    episode_id = choice["episode_id"]
    turns = list(source_rows(TURN_PATH, episode_id))
    wire = list(source_rows(WIRE_PATH, episode_id))
    calls = [item for item in turns
             if item["row"].get("kind") == "tool_call"
             and item["row"].get("tool") in TOOLS]
    results = [item for item in turns if item["row"].get("kind") == "tool_result"]
    chain_rows = []
    responses = []
    requests = []
    for call in calls:
        call_id = call["row"]["call_id"]
        exact_results = [r for r in results if r["row"].get("tool_call_id") == call_id]
        exact_wire = [r for r in wire if r["row"].get("source_call_id") == call_id]
        chain_rows.append({
            "call_id": call_id,
            "tool": call["row"]["tool"],
            "call_citation": citation(call, "call_id"),
            "result_citations": [citation(r, "tool_call_id") for r in exact_results],
            "wire_citations": [citation(r, "source_call_id") for r in exact_wire],
            "status": "COMPLETE" if exact_results and exact_wire else "PARTIAL",
        })
        requests.extend(money_observations(
            call, "arguments", call_id, "tool_response", "request"))
        for result in exact_results:
            responses.extend(money_observations(
                result, "result", call_id, "tool_response", "response"))
        for event in exact_wire:
            requests.extend(money_observations(
                event, "request_body", call_id, "protocol_response", "request"))
            responses.extend(money_observations(
                event, "response_body", call_id, "protocol_response", "response"))
    # Use factual reported response when available, never clear it because
    # consent-to-checkout linkage is insufficient.
    completed = next((x for x in responses if x["phase"] == "REPORTED_COMPLETION"), None)
    candidate = completed or (responses[0] if responses else None)
    payment = None
    if candidate:
        payment = {
            "origin": candidate["origin"],
            "checkout_id": candidate["checkout_id"],
            "currency": str(candidate["currency_raw"]).upper(),
            "amount_minor": candidate["amount_minor"],
            "seq": candidate["seq"],
        }
    dimensions = []
    if not chain_rows:
        dimensions.append("payment_tool_call_not_observed")
    if any(x["status"] == "PARTIAL" for x in chain_rows):
        dimensions.append("one_or_more_native_result_or_wire_links_missing")
    if not responses:
        dimensions.append("complete_reported_payment_amount_currency_checkout_missing")
    if candidate and candidate["unit_status"] != "PROVEN":
        dimensions.append("amount_unit_not_independently_proven")
    dimensions.extend([
        "user_confirmation_to_exact_checkout_id_not_proven",
        "independent_backend_settlement_not_observed",
    ])
    oracle_input = {
        "exact_link": False,
        "consent": None,
        "payment": payment,
    }
    explanation = (
        "已按每个原生call id分别保留调用、结果与wire引用；"
        "金额观察只来自有源字段的响应，不以用户话语邻接来补造授权绑定。"
        "协议状态不等于真实清算，未证明的最小金额单位保持UNKNOWN。"
    )
    return {
        "episode_id": episode_id,
        "world_id": choice["world_id"],
        "call_chains": chain_rows,
        "raw_payment_observations": responses,
        "request_observations": requests,
        "binding_status": "AMBIGUOUS" if chain_rows else "MISSING",
        "binding_citations": [],
        "missing_dimensions": dimensions,
        "reason": explanation,
        "oracle_input": oracle_input,
        "source_verdict": "NOT_JUDGEABLE",
        "observed_turns": len(turns),
        "observed_wire": len(wire),
    }


def main():
    target = TASK / "MEASUREMENT.json"
    ledger_path = TASK / "ATTEMPT_LEDGER.json"
    if target.exists() or ledger_path.exists():
        raise RuntimeError("H64R output/ledger already exists: no silent reruns")
    selected = json_read(OLD / "SELECTED.json")["samples"]
    assert len(selected) == 6
    ledger = {
        "task_id": TASK_ID, "active_minutes": 1,
        "measurement_versions": 1, "formal_l2_attempts": 0,
        "network_calls": 0, "installation_calls": 0,
        "model_calls": 0, "payment_calls": 0, "product_calls": 0,
        "upstream_replay_calls": 0,
        "attempts": [{
            "id": "V-01", "kind": "measurement_version",
            "started_at": now(), "finished_at": now(), "status": "SUCCEEDED",
        }],
    }
    json_write(ledger_path, ledger)
    began = time.monotonic()
    samples = []
    for index, choice in enumerate(selected, 1):
        attempt = {
            "id": "S-%02d" % index, "kind": "sample",
            "episode_id": choice["episode_id"],
            "started_at": now(), "finished_at": None, "status": "RESERVED",
        }
        ledger["attempts"].append(attempt)
        json_write(ledger_path, ledger)  # durable reservation BEFORE sample read
        try:
            sample = build_episode(choice)
            samples.append(sample)
            attempt["status"] = "SUCCEEDED"
        except Exception as error:
            attempt["status"] = "FAILED"
            attempt["reason"] = type(error).__name__ + ": " + str(error)[:200]
            raise
        finally:
            attempt["finished_at"] = now()
            ledger["active_minutes"] = max(
                1, min(90, int((time.monotonic() - began) / 60) + 1))
            json_write(ledger_path, ledger)
    output = {
        "task_id": TASK_ID,
        "classification": "REFERENCE_ONLY",
        "replay_executed": False,
        "product_effect_measured": False,
        "samples": samples,
        "access_limit": {
            "missing_world_ids": ["env-bd45a7e9be19"],
            "meaning": "Previously reported failed acquisition; no new GET permitted.",
        },
        "assessment": (
            "离线提取已按原生调用id分链，保留源已报告的金额、币种和checkout。"
            "本结果仅评价原始来源事实能否支持独立判定；金额单位、授权绑定、"
            "真实后台清算及外部控制效果未经证实。未执行回放、产品或支付操作。"
        ),
    }
    json_write(target, output)
    summary = {
        "task_id": TASK_ID,
        "episodes": [{
            "episode_id": s["episode_id"], "calls": len(s["call_chains"]),
            "complete_chains": sum(c["status"] == "COMPLETE" for c in s["call_chains"]),
            "response_amount_observations": len(s["raw_payment_observations"]),
            "request_amount_observations": len(s["request_observations"]),
            "verdict": s["source_verdict"],
        } for s in samples],
        "no_external_side_effects": True,
    }
    json_write(TASK / "derived" / "EXTRACTION_SUMMARY.json", summary)
    print(json.dumps(summary, ensure_ascii=True))


def refine_existing():
    """Second bounded analysis version from persisted evidence, no new sample reads."""
    import re
    from decimal import Decimal
    ledger_path = TASK / "ATTEMPT_LEDGER.json"
    ledger = json_read(ledger_path)
    if ledger["measurement_versions"] != 1 or len([
            a for a in ledger["attempts"] if a["kind"] == "sample"]) != 6:
        raise RuntimeError("Revision requires exactly one completed six-sample pass")
    checkpoint = TASK / "derived" / "V1_MEASUREMENT.json"
    if checkpoint.exists():
        raise RuntimeError("Version 1 already backed up: no repeated revision")
    attempt = {
        "id": "V-02", "kind": "measurement_version",
        "started_at": now(), "finished_at": None, "status": "RESERVED",
    }
    ledger["measurement_versions"] = 2
    ledger["attempts"].append(attempt)
    json_write(ledger_path, ledger)
    try:
        current = json_read(TASK / "MEASUREMENT.json")
        json_write(checkpoint, current)
        prior = json_read(OLD / "derived" / "INSPECT.json")
        previous = {x["episode_id"]: x for x in prior["samples"]}
        for sample in current["samples"]:
            eid = sample["episode_id"]
            observed = []
            for turn in previous[eid]["turns"]:
                if turn["actor"] != "shopper" or turn["kind"] != "message":
                    continue
                raw = turn.get("text")
                if not isinstance(raw, str):
                    continue
                if not re.search(r"\b(go ahead|place the order)\b", raw, re.I):
                    continue
                amount = re.search(r"\$(\d+\.\d{2})\b", raw)
                if not amount:
                    continue
                cents = int(Decimal(amount.group(1)) * 100)
                observed.append({
                    "seq": turn["seq"], "raw_user_message": raw,
                    "spoken_amount_minor_from_dollars": cents,
                    "currency": "USD",
                    "checkout_id_in_message": None,
                    "source_citation": {
                        "file": (OLD.relative_to(ROOT) / "acquired" / TURN_PATH).as_posix(),
                        "kind": "parquet",
                        "row_group": turn["rg"],
                        "row_index": turn["ri"],
                        "pointer": "/text",
                        "value_sha256": digest(raw),
                    },
                    "scope": "user_spoken_cap_only_not_authority_binding",
                })
            sample["user_confirmation_evidence"] = observed
            if observed:
                latest = observed[-1]
                sample["oracle_input"]["consent"] = {
                    "origin": "user_message",
                    "amount_minor": latest["spoken_amount_minor_from_dollars"],
                    "currency": "USD",
                    "seq": latest["seq"],
                    "checkout_id": None,
                }
                sample["missing_dimensions"] = [
                    d for d in sample["missing_dimensions"]
                    if d != "user_confirmation_to_exact_checkout_id_not_proven"
                ] + ["spoken_consent_lacks_explicit_native_checkout_binding"]
                sample["reason"] += (
                    "用户原话中的美元上限已作为独立证据保留；"
                    "自然语言确认未明确证明该上限与原生checkout id相同。"
                )
            else:
                sample["missing_dimensions"] += ["explicit_user_amount_confirmation_missing"]
            for item in sample["raw_payment_observations"]:
                pointer = item["amount_citation"].get("embedded_pointer", "")
                if "/totals/" in pointer and item["phase"] == "REPORTED_COMPLETION":
                    # Totals include subtotal/tax/shipping components, not all paid totals.
                    item["phase"] = "UNKNOWN"
                    item["component_classification"] = "checkout_totals_breakdown_not_individual_payment"
            completed = next(
                (item for item in sample["raw_payment_observations"]
                 if item["phase"] == "REPORTED_COMPLETION"), None)
            # No first-element fallback masquerading as an authoritative payment.
            sample["oracle_input"]["payment"] = ({
                "origin": completed["origin"],
                "checkout_id": completed["checkout_id"],
                "currency": str(completed["currency_raw"]).upper(),
                "amount_minor": completed["amount_minor"],
                "seq": completed["seq"],
            } if completed else None)
            sample["source_verdict"] = "NOT_JUDGEABLE"
        current["measurement_version"] = 2
        current["assessment"] += (
            " 第二分析版特别区分checkout totals分项与付款完成，"
            "另保留用户口头金额上限；未使用无显式标识的相邻消息补造绑定。"
        )
        json_write(TASK / "MEASUREMENT.json", current)
        json_write(TASK / "derived" / "V2_SEMANTIC_REFINEMENT.json", {
            "reason": "Avoid treating subtotal/tax/shipping as individually completed payments.",
            "sample_reads_added": 0,
            "user_confirmation_sources": [
                {"episode_id": s["episode_id"],
                 "count": len(s["user_confirmation_evidence"])}
                for s in current["samples"]
            ],
        })
        attempt["status"] = "SUCCEEDED"
    except Exception as exc:
        attempt["status"] = "FAILED"
        attempt["reason"] = type(exc).__name__ + ": " + str(exc)[:200]
        raise
    finally:
        attempt["finished_at"] = now()
        ledger["active_minutes"] = max(2, ledger["active_minutes"])
        json_write(ledger_path, ledger)


def l2_reserve():
    ledger_path = TASK / "ATTEMPT_LEDGER.json"
    ledger = json_read(ledger_path)
    if ledger.get("l2_reservation") or ledger["formal_l2_attempts"] >= 2:
        raise RuntimeError("L2 already reserved or budget exhausted")
    count = ledger["formal_l2_attempts"] + 1
    ledger["formal_l2_attempts"] = count
    ledger["l2_reservation"] = {
        "id": "L2-%02d" % count, "kind": "formal_l2",
        "started_at": now(), "status": "RESERVED",
        "out_path": ("docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/"
                     "evidence/l2_executor_%02d" % count),
    }
    json_write(ledger_path, ledger)
    print(json.dumps(ledger["l2_reservation"], ensure_ascii=True))


def l2_finish(succeeded):
    ledger_path = TASK / "ATTEMPT_LEDGER.json"
    ledger = json_read(ledger_path)
    reservation = ledger.pop("l2_reservation", None)
    if not reservation:
        raise RuntimeError("No L2 reservation to finish")
    reservation["status"] = "SUCCEEDED" if succeeded else "FAILED"
    reservation["finished_at"] = now()
    ledger["attempts"].append(reservation)
    json_write(ledger_path, ledger)
    print(json.dumps(reservation, ensure_ascii=True))


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--refine-existing":
        refine_existing()
    elif len(sys.argv) == 2 and sys.argv[1] == "--reserve-l2":
        l2_reserve()
    elif len(sys.argv) == 2 and sys.argv[1] in ("--l2-success", "--l2-failed"):
        l2_finish(sys.argv[1] == "--l2-success")
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("unsupported extraction / ledger operation")
