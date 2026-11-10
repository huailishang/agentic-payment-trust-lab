"""H65: bounded source-only unit / consent-checkout bridge evidence audit.

Never import CartTrace/Payment application code or prior H64/H64R extractors.
Read only INPUTS.readonly, six frozen episodes, no network/replay/products.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = Path("docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1")
H64R = Path("docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1")
TASK_ID = TASK.name
TURN = OLD / "acquired/data/turns/validation-00000-of-00001.parquet"
WIRE = OLD / "acquired/data/wire/validation-00000-of-00001.parquet"
SCHEMA = OLD / "references/DATA_SCHEMA_md"
WALLET = OLD / "references/CODE_src__carttrace__agents__wallet.py"


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8"))


def write(relative, doc):
    path = TASK / relative
    path.parent.mkdir(exist_ok=True, parents=True)
    temp = TASK / "derived" / (path.name + ".incomplete")
    temp.parent.mkdir(exist_ok=True)
    with temp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def textcite(rel, first, last):
    source = ROOT / rel
    lines = source.read_bytes().splitlines(keepends=True)
    return {
        "file": rel.as_posix(),
        "line_start": first,
        "line_end": last,
        "text_sha256": sha(b"".join(lines[first - 1:last])),
    }


def pqcite(rec, field, embedded=None, inner=None):
    row = rec["row"]
    obj = {
        "file": rec["file"].as_posix(),
        "row_group": rec["row_group"],
        "row_index": rec["row_index"],
        "pointer": "/" + field,
        "value_sha256": canon(row[field]),
    }
    if embedded:
        obj.update({"embedded_pointer": "/" + "/".join(str(i) for i in embedded),
                    "decoded_value_sha256": canon(inner)})
    return obj


def safe_load(value):
    if not isinstance(value, str):
        return value if isinstance(value, dict) else None
    try:
        parsed = json.loads(value)
    except ValueError:
        return None
    # Strictly no guessed double decoding of opaque source strings.
    return parsed if isinstance(parsed, dict) else None


def episode_rows(rel, eid):
    import pyarrow.parquet as pq
    file = ROOT / rel
    parquet = pq.ParquetFile(file)
    for group in range(parquet.num_row_groups):
        for index, row in enumerate(parquet.read_row_group(group).to_pylist()):
            if row.get("episode_id") == eid:
                yield {"file": rel, "row_group": group, "row_index": index,
                       "row": row}


def output_sample(eid, old_measure, rows):
    messages, turns, wire = rows
    confirmation_evidence = []
    for t in turns:
        r = t["row"]
        if r.get("actor") != "shopper" or r.get("kind") != "message":
            continue
        spoken = r.get("text")
        if not isinstance(spoken, str):
            continue
        if re.search(r"\b(go ahead|place the order)\b", spoken, re.I):
            amt = re.search(r"\$([0-9]+\.[0-9]{2})\b", spoken)
            if amt:
                confirmation_evidence.append({
                    "seq": r["seq"],
                    "amount_spoken": amt.group(1),
                    "currency_spoken": "USD",
                    "checkout_literal_in_message": bool(re.search(r"checkout-[a-f0-9]+", spoken)),
                    "citation": pqcite(t, "text"),
                })
    metadata = []
    for m in messages:
        for field in ("checkout_open_seq", "consent_seq", "payment_seq",
                      "completion_seq", "final_cart"):
            if m["row"].get(field) is not None:
                raw = m["row"][field]
                metadata.append({"field": field,
                                 "value": raw if field != "final_cart" else "source_json_present",
                                 "citation": pqcite(m, field),
                                 "semantic_limit": "publish_metadata_not_authority_proof"})
    raw = old_measure.get("raw_payment_observations", [])
    requests = old_measure.get("request_observations", [])
    native_chains = old_measure.get("call_chains", [])
    results = [{"call_id": e["call_id"], "raw_amount": e["raw_amount"],
                "currency_raw": e["currency_raw"], "checkout_id": e["checkout_id"],
                "phase": e["phase"],
                "amount_citation": e["amount_citation"],
                "currency_citation": e["currency_citation"],
                "checkout_citation": e["checkout_citation"]} for e in raw]
    allowance = [{"call_id": e["call_id"], "raw_amount": e["raw_amount"],
                  "currency_raw": e["currency_raw"], "checkout_id": e["checkout_id"],
                  "phase": e["phase"],
                  "amount_citation": e["amount_citation"]} for e in requests]
    checkout_refs = [e["checkout_citation"] for e in raw if e.get("checkout_citation")]
    checkout_refs += [e["checkout_citation"] for e in requests if e.get("checkout_citation")]
    notes = []
    if confirmation_evidence:
        notes.append("原始用户确认带美元金额，但确认消息没有显式checkout标识；不能依据同额或相邻顺序认为其授权绑定已直接证明。")
    else:
        notes.append("该episode未观察到明确的带金额下单确认；不能把初始预算、选品或后续工具调用当作用户授权确认。")
    if raw:
        notes.append("协议或工具的金额、币种与checkout已有逐字段源引用，但它们不是用户确认对象的显式连接。")
    if any(c["status"] == "PARTIAL" for c in native_chains):
        notes.append("至少一个原生call缺对应wire或结果，不能挪用同episode其他call来填补。")
    # Source-unit scope: final_cart documented in minor units, NOT every
    # wire/protocol total or allowance. No leap across unproved transformations.
    final_cart = next((m for m in messages if m["row"].get("final_cart")), None)
    unit_refs = [textcite(SCHEMA, 56, 59)]
    if final_cart is not None:
        unit_refs.append(pqcite(final_cart, "final_cart"))
    if raw or allowance:
        status_unit = "PARTIAL"
        unit_reason = ("已存在原生金额、币种、checkout原字段引用；DATA_SCHEMA仅声明final_cart的价格是最小货币单位，"
                       "钱包Money转换见静态代码。但现有证据未直接把这一定义连接到本例每项协议付款/令牌额度字段，"
                       "也未证明最终金额在执行路径上遵循同一单位契约，所以付款金额单位只能PARTIAL。")
    else:
        status_unit = "UNKNOWN"
        unit_reason = ("本例没有可用于支付单位校验的原生付款/额度金额观察。静态schema对final_cart价格有最小单位说明，"
                       "并不能无中生有成为本例付款协议total的单位证明；不以美元口语金额反算单位。")
    binding_edges = []
    for c in confirmation_evidence:
        binding_edges.append({
            "from": "shopper_explicit_spoken_total",
            "to": "checkout_id",
            "origin": "INFERENCE",
            "citation": c["citation"],
            "status": "UNPROVEN",
            "reason": "用户说出了金额，未在同一来源提供checkout id；金额相等和相邻时序不是直接桥接。",
        })
    for c in checkout_refs:
        binding_edges.append({
            "from": "native_call_or_protocol",
            "to": "checkout_id",
            "origin": "SOURCE_OBSERVATION",
            "citation": c,
            "status": "OBSERVED",
            "reason": "源数据显式记录原生checkout，但不能由此证明用户授权对应这一checkout。",
        })
    # Code-level intent is kept visibly separate from source observations.
    binding_edges.append({
        "from": "wallet_approve_and_issue_model",
        "to": "checkout_amount_matching_intent",
        "origin": "CODE_INTENT",
        "citation": textcite(WALLET, 878, 935),
        "status": "DESIGN_ONLY",
        "reason": "代码约束同一checkout和amount，不等于该episode实际运行时签发/消费Consent的可回指记录。",
    })
    binding_refs = [e["citation"] for e in binding_edges]
    if confirmation_evidence and checkout_refs:
        binding_status = "PARTIAL"
        binding_reason = ("同一episode有用户原文金额确认及原生checkout/协议结果，可分别回指来源；"
                          "钱包代码中也有Consent(checkout_id,amount,seq)的预期行为。"
                          "但已发布source未呈现用户确认到该原生checkout的一条直接、共同标识的观察记录，"
                          "metadata序号或金额相等都不能补足这一连接，故保持PARTIAL。")
    else:
        binding_status = "UNKNOWN"
        binding_reason = ("至少缺少带金额的明确用户确认或原生checkout付款观察，无法形成用户到checkout的闭合链。"
                          "钱包代码设计的同一checkout金额审批不能代替本episode真实来源观察，"
                          "故保持UNKNOWN，不推测用户已授权或者商户付款已发生。")
    return {
        "episode_id": eid,
        "unit": {"status": status_unit, "citations": unit_refs, "reason": unit_reason,
                 "target_scope": "protocol_reported_payment_and_token_allowance",
                 "documented_scope": "final_cart prices, not auto-proven protocol totals"},
        "binding": {"status": binding_status, "citations": binding_refs,
                    "reason": binding_reason, "edges": binding_edges},
        "confirmed_user_amounts": confirmation_evidence,
        "source_payment_observations": results,
        "source_request_allowances": allowance,
        "native_call_chains": native_chains,
        "source_metadata": metadata,
        "notes": notes,
        "independent_backend_settlement_observed": False,
    }


def main():
    inputs = read(Path("docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/INPUTS.json"))
    ids = inputs["episode_ids"]
    prior_path = H64R / "MEASUREMENT.json"
    h64r = read(prior_path)
    by_id = {r["episode_id"]: r for r in h64r["samples"]}
    selected = read(OLD / "SELECTED.json")
    assert ids == [s["episode_id"] for s in selected["samples"]]
    assert set(by_id) == set(ids)

    if (TASK / "RESULT.json").exists() or (TASK / "ATTEMPT_LEDGER.json").exists():
        raise RuntimeError("H65 first version already exists; do not reset the task budget")
    sys.path.insert(0, str(ROOT / ".task_envs/H64/parquet_reader"))
    import pyarrow as pa
    assert pa.__version__ == "26.0.0"
    ledger = {"task_id": TASK_ID, "active_minutes": 1, "measurement_versions": 1,
              "formal_l2_attempts": 0, "sample_reads": 0,
              "network_calls": 0, "installation_calls": 0, "model_calls": 0,
              "product_calls": 0, "upstream_replay_calls": 0, "payment_calls": 0,
              "attempts": [{
                  "id": "M-01", "kind": "measurement_version",
                  "started_at": utc(), "finished_at": utc(), "status": "SUCCEEDED"
              }]}
    write("ATTEMPT_LEDGER.json", ledger)
    started = time.monotonic()
    samples = []
    for i, eid in enumerate(ids, 1):
        attempt = {"id": f"S-{i:02d}", "kind": "sample", "episode_id": eid,
                   "started_at": utc(), "finished_at": None, "status": "RESERVED"}
        ledger["sample_reads"] += 1
        ledger["attempts"].append(attempt)
        write("ATTEMPT_LEDGER.json", ledger)
        try:
            source_rows = (
                [row for rel in inputs["readonly"] if
                 rel.endswith("validation-00000-of-00001.parquet") and
                 "/data/messages/" in rel
                 for row in episode_rows(Path(rel), eid)],
                list(episode_rows(TURN, eid)),
                list(episode_rows(WIRE, eid)),
            )
            samples.append(output_sample(eid, by_id[eid], source_rows))
            attempt["status"] = "SUCCEEDED"
        except Exception as exc:
            attempt["status"] = "FAILED"
            attempt["reason"] = type(exc).__name__ + ": " + str(exc)[:240]
            raise
        finally:
            attempt["finished_at"] = utc()
            ledger["active_minutes"] = max(1, int((time.monotonic() - started) / 60) + 1)
            write("ATTEMPT_LEDGER.json", ledger)

    complete = [s for s in samples if s["unit"]["status"] ==
                s["binding"]["status"] == "PROVEN"]
    verdict = "CONTINUE_TO_REPLAY_BASELINE" if complete else "STOP_SOURCE_VIEW"
    result = {
        "task_id": TASK_ID,
        "classification": "REFERENCE_ONLY",
        "samples": samples,
        "verdict": verdict,
        "reason": (
            "固定的六例已经完成源字段、原生checkout、钱包代码意图、final_cart金额单位说明和"
            "用户口头确认逐边清点。没有一例同时在原生支付金额单位与用户确认到checkout的直接桥接上"
            "提供完整同episode来源证明，故本六例静态来源视图停止；这不构成产品安全或真实清算裁决。"
        ),
        "replay_executed": False,
        "product_effect_measured": False,
        "missing_world_ids": ["env-bd45a7e9be19"],
    }
    write("RESULT.json", result)
    write("derived/SUMMARY.json", {
        "task_id": TASK_ID, "verdict": verdict,
        "episodes": [{"episode_id": s["episode_id"],
                      "unit": s["unit"]["status"], "binding": s["binding"]["status"],
                      "responses": len(s["source_payment_observations"]),
                      "requests": len(s["source_request_allowances"]),
                      "confirmations": len(s["confirmed_user_amounts"])}
                     for s in samples]})
    print(json.dumps({"verdict": verdict,
                      "summary": [{"episode": s["episode_id"],
                                   "unit": s["unit"]["status"],
                                   "binding": s["binding"]["status"]}
                                  for s in samples]}, ensure_ascii=True))


def reserve_l2():
    ledger = read(Path("docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/ATTEMPT_LEDGER.json"))
    if "l2_reserved" in ledger or ledger["formal_l2_attempts"] >= 2:
        raise RuntimeError("L2 already reserved or budget exceeded")
    index = ledger["formal_l2_attempts"] + 1
    ledger["formal_l2_attempts"] = index
    ledger["l2_reserved"] = {"id": f"L2-{index:02d}", "kind": "formal_l2",
                            "started_at": utc(), "status": "RESERVED"}
    write("ATTEMPT_LEDGER.json", ledger)


def finish_l2(passed):
    ledger = read(Path("docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/ATTEMPT_LEDGER.json"))
    attempt = ledger.pop("l2_reserved")
    attempt["status"] = "SUCCEEDED" if passed else "FAILED"
    attempt["finished_at"] = utc()
    ledger["attempts"].append(attempt)
    write("ATTEMPT_LEDGER.json", ledger)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()
    elif sys.argv[1:] == ["--reserve-l2"]:
        reserve_l2()
    elif sys.argv[1:] == ["--l2-success"]:
        finish_l2(True)
    elif sys.argv[1:] == ["--l2-failed"]:
        finish_l2(False)
    else:
        raise SystemExit("unsupported H65 command")
