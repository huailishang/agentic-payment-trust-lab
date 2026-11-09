"""H64 scoped, deterministic Parquet selection and bounded evidence inspection.

No source table beyond the frozen two category partitions is used for choosing
episodes. Full turn/wire and outcomes are never inspected before SELECTED exists.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
sys.path.insert(0, str(ROOT / ".task_envs/H64/parquet_reader"))
import pyarrow as pa
import pyarrow.parquet as pq
assert pa.__version__ == "26.0.0"


def read(name):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select():
    path = TASK / "SELECTED.json"
    if path.exists():
        raise FileExistsError("SELECTED is immutable once written")
    frozen = read("SOURCE_INPUTS.json")
    result = []
    for rel in frozen["message_paths"]:
        original = TASK / "acquired" / rel
        if sha(original) != frozen["expected_sha256"][frozen["dataset_base"] + rel]:
            raise ValueError("message partition SHA mismatch")
        reader = pq.ParquetFile(original)
        if not set(frozen["selection_columns"]) <= set(reader.schema_arrow.names):
            raise ValueError("selection columns are not all present")
        for batch in reader.iter_batches(columns=frozen["selection_columns"]):
            for row in batch.to_pylist():
                if (row["boundary"] == "order"
                    and row["currency"] == "USD"
                    and "webmcp" not in (row["surface"] or "").lower()
                    and row["episode_id"] not in frozen["excluded_episode_ids"]):
                    result.append({"episode_id": row["episode_id"], "world_id": row["world_id"]})
    result.sort(key=lambda s:s["episode_id"])
    if len({s["episode_id"] for s in result}) != len(result):
        raise ValueError("non-unique candidate episode")
    chosen=result[:6]
    data={"task_id":TASK.name,"selected_at_utc":datetime.now(timezone.utc).isoformat(),
          "rule":"boundary=order,currency=USD,no webmcp,exclude H63 six,sort episode_id ascending",
          "source_files":[{"file":"acquired/"+p,"sha256":sha(TASK/"acquired"/p)} for p in frozen["message_paths"]],
          "sample_list_sha256":hashlib.sha256(json.dumps(chosen,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest(),
          "samples":chosen}
    with path.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print(json.dumps({"selected":len(chosen),"candidates_total":len(result),"samples":chosen},ensure_ascii=False))


def schema():
    if not (TASK/"SELECTED.json").exists():
        raise ValueError("selection must be locked before inspecting full schemas")
    frozen=read("SOURCE_INPUTS.json")
    for relative in frozen["parquet_paths"]:
        filename=TASK/"acquired"/relative
        if filename.is_file():
            table=pq.ParquetFile(filename)
            print(json.dumps({"file":relative,"rows":table.metadata.num_rows,
                              "row_groups":table.num_row_groups,
                              "columns":[str(f) for f in table.schema_arrow]},ensure_ascii=False))



def source_rows(relative, episode_id, fields=None):
    """Read only data for already selected episodes; retain original row location."""
    path=TASK/"acquired"/relative
    reader=pq.ParquetFile(path)
    if not path.is_file():
        raise FileNotFoundError(relative)
    columns=fields or reader.schema_arrow.names
    if "episode_id" not in columns: columns=["episode_id"]+list(columns)
    for group in range(reader.num_row_groups):
        rows=reader.read_row_group(group,columns=columns).to_pylist()
        for index,row in enumerate(rows):
            if row["episode_id"]==episode_id:
                yield {"file":"acquired/"+relative,"row_group":group,
                       "row_index":index,"row":row}


def store_ledger(ledger):
    path=TASK/"ATTEMPT_LEDGER.json"
    temp=path.with_suffix(".tmp")
    with temp.open("w",encoding="utf-8") as f:
        json.dump(ledger,f,ensure_ascii=False,indent=2)
        f.write(chr(10))
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp,path)


def inspect():
    selected=read("SELECTED.json")["samples"]
    inputs=read("SOURCE_INPUTS.json")
    ledger=read("ATTEMPT_LEDGER.json")
    folder=TASK/"derived"
    folder.mkdir(exist_ok=True)
    output={"task_id":TASK.name,"read_scope":"six preselected episodes only","samples":[]}
    for choice in selected:
        eid=choice["episode_id"]
        attempt={"id":f"S-{len([x for x in ledger['attempts'] if x['kind']=='sample'])+1:02d}",
                 "kind":"sample","started_at":datetime.now(timezone.utc).isoformat(),
                 "finished_at":None,"status":"RESERVED","episode_id":eid}
        ledger["attempts"].append(attempt)
        store_ledger(ledger)
        try:
            m=[]
            for rel in inputs["message_paths"]:
                m.extend(source_rows(rel,eid))
            ts=list(source_rows("data/turns/validation-00000-of-00001.parquet",eid))
            wire=list(source_rows("data/wire/validation-00000-of-00001.parquet",eid))
            def short(v,size=600):
                if v is None: return None
                if not isinstance(v,str): v=json.dumps(v,ensure_ascii=False,default=str)
                return v[:size] + ("…" if len(v)>size else "")
            mshort=[{"source":x["file"],"rg":x["row_group"],"ri":x["row_index"],
                     "message_seq":[{"index":i,"role":k.get("role"),"text":short(k.get("content"),260),
                                     "tool_calls":[c.get("function",{}).get("name") for c in (k.get("tool_calls") or [])]}
                                    for i,k in enumerate(x["row"].get("messages") or [])]}
                    for x in m]
            tsh=[{"rg":x["row_group"],"ri":x["row_index"],"seq":x["row"].get("seq"),
                  "actor":x["row"].get("actor"),"kind":x["row"].get("kind"),
                  "tool":x["row"].get("tool"),"call_id":x["row"].get("call_id"),
                  "tool_call_id":x["row"].get("tool_call_id"),
                  "text":short(x["row"].get("text"),220),
                  "arguments":short(x["row"].get("arguments"),400),
                  "result":short(x["row"].get("result"),480)}
                 for x in ts]
            wsh=[{"rg":x["row_group"],"ri":x["row_index"],"seq":x["row"].get("seq"),
                  "method":x["row"].get("method"),"url":short(x["row"].get("url"),180),
                  "protocol":x["row"].get("protocol"),"status":x["row"].get("status"),
                  "source_call_id":x["row"].get("source_call_id"),
                  "request_body":short(x["row"].get("request_body"),430),
                  "response_body":short(x["row"].get("response_body"),430)}
                 for x in wire]
            output["samples"].append({"episode_id":eid,"world_id":choice["world_id"],
                                      "messages":mshort,"turns":tsh,"wire":wsh})
            attempt["status"]="SUCCEEDED"
        except Exception as exc:
            attempt["status"]="FAILED"
            attempt["reason"]=type(exc).__name__+":"+str(exc)[:150]
            raise
        finally:
            attempt["finished_at"]=datetime.now(timezone.utc).isoformat()
            store_ledger(ledger)
    with (folder/"INSPECT.json").open("x",encoding="utf-8") as f:
        json.dump(output,f,ensure_ascii=False,indent=2)
        f.write(chr(10))
    for s in output["samples"]:
        t=s["turns"]
        print(json.dumps({"episode":s["episode_id"],
                          "turns":len(t),"wire":len(s["wire"]),
                          "customer_utterances":[(v["seq"],v["text"]) for v in t if v["actor"]=="shopper" and v["kind"]=="message"][:12],
                          "pay_tools":[(v["seq"],v["tool"],v["call_id"]) for v in t if v["kind"]=="tool_call" and any(k in (v["tool"] or "").lower() for k in ["pay","checkout"])]},
                         ensure_ascii=False))


def money():
    if not (TASK/"SELECTED.json").exists():
        raise ValueError("selection must be frozen")
    data=read("derived/INSPECT.json")
    for sample in data["samples"]:
        print("EPISODE",sample["episode_id"], "WORLD",sample["world_id"])
        turns=sample["turns"]
        for row in turns:
            tool=(row.get("tool") or "").lower()
            is_payment=any(word in tool for word in ("pay","mandate","checkout","order","wallet"))
            text=(row.get("text") or "").lower()
            is_consent=row.get("actor")=="shopper" and any(k in text for k in ("order for","place the order","go ahead","pay for"))
            if is_payment or is_consent:
                print(json.dumps({"seq":row["seq"],"rg":row["rg"],"ri":row["ri"],
                                  "actor":row["actor"],"kind":row["kind"],"tool":row["tool"],
                                  "call_id":row["call_id"],"parent_call":row["tool_call_id"],
                                  "text":row["text"],"args":row["arguments"],
                                  "result":row["result"]},ensure_ascii=False))
                related=[v for v in turns if v.get("tool_call_id")==row.get("call_id") and row.get("call_id")]
                for result in related:
                    print("MATCHED_RESULT",json.dumps({"seq":result["seq"],"ri":result["ri"],
                           "tool_call_id":result["tool_call_id"],"text":result["text"],
                           "result":result["result"]},ensure_ascii=False))
                for wire in sample["wire"]:
                    if row.get("call_id") and wire.get("source_call_id")==row.get("call_id"):
                        print("MATCHED_WIRE",json.dumps(wire,ensure_ascii=False))
        print("END_EPISODE")

def value_sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
                                      separators=(",",":")).encode("utf-8")).hexdigest()


def parquet_cite(record,field):
    value=record["row"][field]
    return {"file":record["file"],"kind":"parquet",
            "row_group":record["row_group"],"row_index":record["row_index"],
            "pointer":"/"+field,"value_sha256":value_sha(value)}


def world_cite(filename):
    path=TASK/filename
    doc=json.loads(path.read_text(encoding="utf-8"))
    field="market" if "market" in doc else ("rows" if "rows" in doc else next(iter(doc)))
    return {"file":filename,"kind":"json","pointer":"/"+field,
            "value_sha256":value_sha(doc[field])}


def source_code_cite():
    relative="references/CODE_src__carttrace__repro__dataset.py"
    line=12
    value=(TASK/relative).read_text(encoding="utf-8").splitlines()[line-1]
    return {"file":relative,"kind":"text","line":line,
            "value_sha256":value_sha(value)}


def fact(status,reason,citations=None):
    assert status in ("PRESENT","ABSENT","AMBIGUOUS")
    assert len(reason)>=20
    cites=list(citations or [])
    if status=="PRESENT": assert cites
    if status=="ABSENT": assert not cites
    return {"status":status,"reason":reason,"citations":cites}


def create_measurement():
    import re
    from ORACLE import evaluate
    output=TASK/"MEASUREMENT.json"
    if output.exists():
        raise FileExistsError("Preserve existing measurement; only separate bounded revision is permitted.")
    selected=read("SELECTED.json")["samples"]
    inputs=read("SOURCE_INPUTS.json")
    ledger=read("ATTEMPT_LEDGER.json")
    if ledger["measurement_versions"] >= 2:
        raise ValueError("measurement budget exhausted")
    ledger["measurement_versions"]+=1
    measure_attempt={"id":f"M-{ledger['measurement_versions']:02d}",
                     "kind":"measurement","started_at":datetime.now(timezone.utc).isoformat(),
                     "finished_at":None,"status":"RESERVED"}
    ledger["attempts"].append(measure_attempt)
    store_ledger(ledger)
    samples=[]
    try:
        for choice in selected:
            eid=choice["episode_id"]
            sid=len([x for x in ledger["attempts"] if x["kind"]=="sample"])+1
            if sid>12:raise ValueError("six samples x two readings budget exhausted")
            attempt={"id":f"S-{sid:02d}","kind":"sample",
                     "started_at":datetime.now(timezone.utc).isoformat(),
                     "finished_at":None,"status":"RESERVED","episode_id":eid}
            ledger["attempts"].append(attempt)
            store_ledger(ledger)
            try:
                messages=[]
                for rel in inputs["message_paths"]:
                    messages.extend(source_rows(rel,eid))
                turns=list(source_rows("data/turns/validation-00000-of-00001.parquet",eid))
                wire=list(source_rows("data/wire/validation-00000-of-00001.parquet",eid))
                if len(messages)!=1:
                    raise ValueError("expected exactly one selected messages record")
                # Only explicit shopper *order approval*, never original shopping budget/selection.
                shop=[]
                for row in turns:
                    val=row["row"]
                    if val.get("actor")=="shopper" and val.get("kind")=="message":
                        text=val.get("text") or ""
                        if ("place the order" in text.lower() or "place order" in text.lower() or "approve payment" in text.lower()) and re.search(r"[$][0-9][0-9,]*[.][0-9]{2}",text):
                            shop.append(row)
                # Allowed payment-execution entry points are distinct from wallet query/checkout preparation.
                executable={"pay","send_payment_mandate","delegate_payment","shop_pay_payment_request"}
                calls=[x for x in turns if x["row"].get("kind")=="tool_call"
                       and x["row"].get("tool") in executable
                       and isinstance(x["row"].get("call_id"),str)
                       and x["row"].get("call_id")]
                results=[]
                matching_wires=[]
                for call in calls:
                    cid=call["row"]["call_id"]
                    results.extend(x for x in turns if x["row"].get("kind")=="tool_result"
                                   and x["row"].get("tool_call_id")==cid)
                    matching_wires.extend(x for x in wire if x["row"].get("source_call_id")==cid)
                # Uniqueness is checked by exact native call_id, no nearest-call fallback.
                def unique(rows):
                    seen=set()
                    ans=[]
                    for row in rows:
                        key=(row["file"],row["row_group"],row["row_index"])
                        if key not in seen:seen.add(key);ans.append(row)
                    return ans
                results=unique(results)
                matching_wires=unique(matching_wires)
                fs={}
                if shop:
                    cites=[parquet_cite(x,"text") for x in shop]
                    fs["confirmation"]=fact("PRESENT",
                         "A shopper explicitly approved a price to place an order in the published conversation; this is text only, not authenticated P1 confirmation or checkout-id binding.",
                         cites)
                else:
                    fs["confirmation"]=fact("ABSENT",
                         "No explicit shopper pre-execution consent to a specifically priced order was found; original budget and option selection are not approval.")
                if calls:
                    fs["payment_call"]=fact("PRESENT",
                        "Published turns contain an explicit payment/delegation tool invocation with a native call ID; it is a simulated instruction, not a bank debit.",
                        [parquet_cite(x,"tool") for x in calls]+[parquet_cite(x,"call_id") for x in calls])
                else:
                    fs["payment_call"]=fact("ABSENT",
                        "No direct pay/delegate/send-mandate/shop-pay execution call occurs in this selected episode; preparatory checkout calls do not prove payment.")
                if results:
                    fs["payment_result"]=fact("PRESENT",
                        "A simulated tool returned a result linked to a payment call by the exact native tool_call_id; the source does not independently certify PSP settlement.",
                        [parquet_cite(x,"result") for x in results]+[parquet_cite(x,"tool_call_id") for x in results])
                elif calls:
                    fs["payment_result"]=fact("AMBIGUOUS",
                        "Payment-related tool calls are visible but a complete native-call-ID tool result has not been observed in the selected turns.",
                        [parquet_cite(x,"call_id") for x in calls])
                else:
                    fs["payment_result"]=fact("ABSENT",
                        "No response to an explicit payment execution call is available in the selected episode.")
                msg=messages[0]
                world_id=choice["world_id"]
                env_rel=f"acquired/worlds/envpacks/{world_id}.json"
                manifest_rel=f"acquired/worlds/manifests/{world_id}.json"
                env=(TASK/env_rel).is_file()
                manifest=(TASK/manifest_rel).is_file()
                final=msg["row"].get("final_state")
                if final:
                    fs["business_state"]=fact("PRESENT",
                        "Published final_state is only a replay target/digest and not an independently observed transaction ledger or live backend event.",
                        [parquet_cite(msg,"final_state")])
                    level="FINAL_STATE_DIGEST"
                elif env:
                    fs["business_state"]=fact("PRESENT",
                        "Only published redacted initial world contents are accessible, not a post-payment backend state or event.",
                        [world_cite(env_rel)])
                    level="PUBLISHED_INITIAL_STATE"
                else:
                    fs["business_state"]=fact("ABSENT",
                        "Neither a published final state digest nor accessible initial world state is available for the selected episode.")
                    level="MISSING"
                if calls and results and matching_wires:
                    fs["correlation"]=fact("PRESENT",
                         "Turn invocation, tool result, and HTTP exchange share explicit native call IDs. This is tool-level lineage, not a proven checkout-authority or money-side-effect chain.",
                         [parquet_cite(calls[0],"call_id"),
                          parquet_cite(results[0],"tool_call_id"),
                          parquet_cite(matching_wires[0],"source_call_id")])
                elif calls:
                    fs["correlation"]=fact("AMBIGUOUS",
                         "Payment invocation exists, but exact source call IDs do not span all returned tool and HTTP exchange observations. Positional fallback is prohibited.",
                         [parquet_cite(calls[0],"call_id")])
                else:
                    fs["correlation"]=fact("ABSENT",
                         "Without an explicit payment execution call there can be no exact payment-call-to-wire correlation in this selected record.")
                replay_cites=[parquet_cite(msg,"world_id"),source_code_cite()]
                if env:replay_cites.append(world_cite(env_rel))
                if manifest:replay_cites.append(world_cite(manifest_rel))
                if env and manifest:
                    fs["replay_inputs"]=fact("PRESENT",
                         "Published messages/turns/wire, world envpack and manifest, and static reconstruction code are present as offline replay inputs; no replay has been executed.",
                         replay_cites)
                else:
                    fs["replay_inputs"]=fact("AMBIGUOUS",
                         "Cross-table records and static code are available, but at least one selected published world document could not be acquired under the fixed network budget.",
                         replay_cites)
                consent=None
                if shop:
                    selected_consent=shop[-1]
                    price=re.search(r"[$]([0-9][0-9,]*[.][0-9]{2})",
                                    selected_consent["row"]["text"])
                    if price:
                        from decimal import Decimal
                        amount=int(Decimal(price.group(1).replace(",",""))*100)
                        consent={"checkout_id":None,"amount_minor":amount,"currency":"USD",
                                 "seq":selected_consent["row"]["seq"],"origin":"user_message"}
                # Even if the transcript contains exact *tool* call IDs, the shopper text
                # does not itself contain a signed/ref-bound checkout ID. Do not infer
                # exact checkout-to-consent binding from adjacency or a model's summary.
                oracle_in={"consent":consent,"payment":None,"exact_link":False}
                verdict=evaluate(oracle_in)
                samples.append({"episode_id":eid,"world_id":world_id,
                                "facts":fs,"oracle_input":oracle_in,
                                "observed_verdict":verdict,"business_state_level":level,
                                "unit_and_link_reason":(
                                    "USD user quote may be parsed as cents, but the shopper message lacks a native "
                                    "checkout ID/authority binding and the payment provider amount and units are "
                                    "not independently linked to that consent; exact_link remains false. "
                                    "This does not assert that the real payment amount differs."),
                                "unit_citations":[]})
                attempt["status"]="SUCCEEDED"
            except Exception as exc:
                attempt["status"]="FAILED"
                attempt["reason"]=type(exc).__name__+":"+str(exc)[:150]
                raise
            finally:
                attempt["finished_at"]=datetime.now(timezone.utc).isoformat()
                store_ledger(ledger)
        missing_world=[s["world_id"] for s in selected if not (TASK/f"acquired/worlds/envpacks/{s['world_id']}.json").is_file()
                       or not (TASK/f"acquired/worlds/manifests/{s['world_id']}.json").is_file()]
        failed_gets=[a["id"] for a in ledger["attempts"] if a["kind"]=="public_get" and a["status"] in {"FAILED","LIMIT"}]
        if missing_world:
            decision_kind="INPUT_LIMIT"
            reason=("The exact frozen six-episode Parquet selection and most published worlds are available, "
                    "but one fixed world envpack failed on its maximum two allowed public GET attempts. "
                    "This is an access limit, not evidence that CartTrace lacks suitable source facts; "
                    "the release cannot qualify as a complete six-world offline replay bundle under this task.")
        else:
            decision_kind="STOP_SOURCE_VIEW"
            reason=("The selected transcript observations do not independently establish a checkout-ID-bound "
                    "user monetary authorization and a settled amount under an independent backend oracle; "
                    "no bounded replay baseline claim can be made from these materials alone.")
        output_data={"task_id":TASK.name,
                     "dataset_revision":inputs["dataset_revision"],"code_revision":inputs["code_revision"],
                     "replay_executed":False,"product_effect_measured":False,
                     "candidate_classification":"REFERENCE_ONLY",
                     "evidence_level":"SOURCE_READINESS_ONLY",
                     "samples":samples,
                     "backend_access_citations":[source_code_cite()],
                     "decision":{"kind":decision_kind,"reason":reason,
                                 "next_question":None,"missing_world_ids":missing_world,
                                 "failed_acquisition_attempts":failed_gets}}
        with output.open("x",encoding="utf-8") as out:
            json.dump(output_data,out,ensure_ascii=False,indent=2)
            out.write(chr(10))
        measure_attempt["status"]="SUCCEEDED"
    except Exception as exc:
        measure_attempt["status"]="FAILED"
        measure_attempt["reason"]=type(exc).__name__+":"+str(exc)[:160]
        raise
    finally:
        measure_attempt["finished_at"]=datetime.now(timezone.utc).isoformat()
        start=datetime.fromisoformat(ledger["started_at"])
        ledger["active_minutes"]=min(180,max(1,int((datetime.now(timezone.utc)-start).total_seconds()/60)+1))
        store_ledger(ledger)
    print(json.dumps({"samples":len(samples),"decision":output_data["decision"]["kind"],
                      "missing_worlds":len(output_data["decision"]["missing_world_ids"]),
                      "verdicts":[x["observed_verdict"] for x in samples]},ensure_ascii=False))


def reserve_l2():
    ledger=read("ATTEMPT_LEDGER.json")
    if ledger["formal_l2_attempts"] >= 2:
        raise ValueError("formal L2 budget exhausted")
    ledger["formal_l2_attempts"]+=1
    ident=f"L2-{ledger['formal_l2_attempts']:02d}"
    if any(x["id"]==ident for x in ledger.get("l2_reservations",[])):
        raise ValueError("L2 id already reserved")
    ledger.setdefault("l2_reservations",[]).append({
        "id":ident,"started_at":datetime.now(timezone.utc).isoformat(),
        "status":"RESERVED","expected_plan":"H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1"})
    store_ledger(ledger)
    print(json.dumps({"reserved":ident,"formal_l2_attempts":ledger["formal_l2_attempts"]}))


def finalize_l2():
    ledger=read("ATTEMPT_LEDGER.json")
    pending=[x for x in ledger.get("l2_reservations",[]) if x["status"]=="RESERVED"]
    if len(pending)!=1:raise ValueError("expected one L2 reservation")
    reservation=pending[0]
    n=ledger["formal_l2_attempts"]
    gate_path=TASK/f"evidence/l2_executor_{n:02d}/L2-GATE.json"
    if gate_path.is_file():
        gate=json.loads(gate_path.read_text(encoding="utf-8"))
        status="SUCCEEDED" if gate.get("result")=="PASS" else "FAILED"
        gate_result=gate.get("result")
    else:
        status="FAILED"
        gate_result="NO_GATE"
    ended=datetime.now(timezone.utc)
    reservation["status"]=status
    reservation["finished_at"]=ended.isoformat()
    ledger["attempts"].append({"id":reservation["id"],"kind":"l2",
                               "started_at":reservation["started_at"],
                               "finished_at":ended.isoformat(),
                               "status":status,"gate_result":gate_result})
    ledger["active_minutes"]=min(180,max(1,int((ended-datetime.fromisoformat(ledger["started_at"])).total_seconds()/60)+1))
    store_ledger(ledger)
    print(json.dumps({"gate":gate_result,"attempt":reservation["id"],
                      "elapsed_minutes_recorded":ledger["active_minutes"]}))


if __name__=="__main__":
    if sys.argv[1]=="select":select()
    elif sys.argv[1]=="schema":schema()
    elif sys.argv[1]=="inspect":inspect()
    elif sys.argv[1]=="money":money()
    elif sys.argv[1]=="measure":create_measurement()
    elif sys.argv[1]=="reserve_l2":reserve_l2()
    elif sys.argv[1]=="finalize_l2":finalize_l2()
    else:raise ValueError("usage select/schema/inspect/money/measure/reserve_l2/finalize_l2")
