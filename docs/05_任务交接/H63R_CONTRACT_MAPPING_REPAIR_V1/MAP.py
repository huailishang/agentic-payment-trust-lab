"""H63R: remap fixed H63 transcript facts onto the repository's original P1-P5 contracts.

No imports of product/H63 executors, no network, models, payments or replay.
H63 facts and source citations remain read-only. This file emits *input
availability*, not a product compliance judgment.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(__file__).resolve().parent
OLD = TASK.parent / "H63_EXTERNAL_TRACE_QUALIFICATION_V1"
OUT = TASK / "MAPPING.json"
LEDGER = TASK / "ATTEMPT_LEDGER.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_new(path: Path, data: dict) -> None:
    """Never overwrite an earlier mapping version or its attempt ledger."""
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def present(facts: dict, *names: str) -> list[str]:
    """Only explicitly PRESENT transcript observations are named as inputs."""
    return [name for name in names if facts[name]["status"] == "PRESENT"]


def map_contract(code: str, facts: dict, rule: dict) -> dict:
    has_confirm = facts["explicit_confirmation"]["status"] == "PRESENT"
    checkout = facts["checkout_snapshot"]["status"] == "PRESENT"
    payment = facts["payment_request"]["status"] == "PRESENT"
    correlated = facts["correlation"]["status"] == "PRESENT"
    if code == "P1":
        keys = present(facts, "explicit_confirmation", "checkout_snapshot", "order_tool_result")
        state = "PARTIAL" if keys else "MISSING"
        if has_confirm:
            reason = ("Price/order consent text can be located, but there is no durable confirmation "
                      "record with an authority version, canonical confirmed-order digest and expiry. "
                      "Transcript consent does not constitute P1 binding verification.")
        elif checkout:
            reason = ("A checkout snapshot exists without a clearly priced user payment confirmation. "
                      "It supplies only a possible order-side observation, not a valid P1 confirmation record.")
        else:
            reason = ("No valid priced-order confirmation or independently bound order snapshot is observable. "
                      "Shopping intent or ambiguous selection agreement does not satisfy P1.")
    elif code == "P2":
        keys = present(facts, "checkout_snapshot", "payment_request", "payment_tool_result",
                       "order_tool_result", "correlation")
        state = "PARTIAL" if keys else "MISSING"
        if payment and correlated:
            reason = ("Call IDs, checkout IDs and returned tool/order observations can be compared inside "
                      "the simulated transcript, but no mandate, authority version, authorized agent or "
                      "payee binding is evidenced; this cannot establish the P2 authority-to-execution chain.")
        elif facts["payment_tool_result"]["status"] == "AMBIGUOUS":
            reason = ("Wallet-data or checkout tool results are not proof of a direct payment invocation. "
                      "The simulated checkout/order references are partial observations; the mandate "
                      "and authorization-to-execution chain remain unavailable.")
        else:
            reason = ("At most a checkout/request fragment is available, without a verified original "
                      "mandate and bound agent/payee/execution references. No complete P2 chain is established.")
    elif code == "P3":
        keys = []
        state = "MISSING"
        reason = ("Session roles, call IDs and payment references are not authenticated agent/executor "
                  "identity evidence. No authorized-agent binding, executor instance identity or fresh "
                  "credential-possession verification is present in this simulated source.")
    elif code == "P4":
        keys = []
        state = "MISSING"
        reason = ("The transcript labels user/assistant/tool messages but contains no P4 source-by-domain "
                  "write policy, authenticated source provenance, trusted-state change record or context "
                  "write history. A message role or tool response cannot substitute for these inputs.")
    elif code == "P5":
        keys = []
        state = "MISSING"
        reason = ("No actual RuntimeGateRecord with P1-P4 decisions, replayable governed event/receipt "
                  "chain or independently established payment-provider outcome is present. A get_order "
                  "result, wallet token or simulated payment receipt is not a P5 governance receipt.")
    else:
        raise ValueError(f"Unexpected contract: {code}")
    return {
        "contract_name": rule["name"],
        "contract_ref": rule["ref"],
        "input_status": state,
        "fact_keys": keys,
        "missing_inputs": list(rule["missing"]),
        "reason": reason,
    }


def main() -> None:
    if OUT.exists() or LEDGER.exists():
        raise FileExistsError("Mapping/ledger already exists; preserve first version and use a bounded revision.")
    old = read(OLD / "MEASUREMENT.json")
    spec = read(TASK / "SPEC.json")
    assert len(old["samples"]) == 6
    assert list(spec["contracts"]) == ["P1", "P2", "P3", "P4", "P5"]
    mapped = []
    for original in old["samples"]:
        facts = original["facts"]
        assert set(facts) == {
            "user_request", "explicit_confirmation", "checkout_snapshot",
            "payment_request", "payment_tool_result", "order_tool_result", "correlation",
        }
        mapped.append({
            "sample_id": original["sample_id"],
            "contracts": {
                code: map_contract(code, facts, rule)
                for code, rule in spec["contracts"].items()
            },
        })
    # The six known, synthetic transcripts do not expose P1-P5 authoritative
    # prerequisites. Further analysis would re-label observed call sequences,
    # not test a product security control against an independent oracle.
    decision = {
        "candidate_classification": "REFERENCE_ONLY",
        "evidence_level": "TRANSCRIPT_ONLY",
        "view_decision": "STOP_PREVIEW_VIEW",
        "question": None,
        "limits": list(spec["limits"]),
        "reason": (
            "After remapping to the real P1-P5 contracts, no preview contains a complete "
            "durable confirmation binding, mandate-to-execution authority, verified executor "
            "identity, trusted context-policy history, or runtime-gate receipt chain. "
            "S03/S06 permit only in-transcript linkage, already observed by H63; a further "
            "comparison of these six seen synthetic traces would not independently measure "
            "our product controls. Stop this preview view; reconsider only with new "
            "authorized, independently checkable evidence."
        ),
    }
    result = {"task_id": spec["task_id"], "samples": mapped, "decision": decision}
    now = datetime.now(timezone.utc).isoformat()
    ledger = {
        "task_id": spec["task_id"],
        "started_at_utc": now,
        "mapping_versions": 1,
        "formal_l2_attempts": 0,
        "active_minutes": 1,
        "network_calls": 0,
        "model_calls": 0,
        "payment_calls": 0,
        "installation_calls": 0,
        "product_calls": 0,
        "entries": [{"type": "MAPPING_V1", "started_at_utc": now,
                     "status": "CREATED", "samples": 6, "contracts_per_sample": 5}],
    }
    save_new(LEDGER, ledger)
    save_new(OUT, result)
    counts = {s: sum(v["input_status"] == s for sample in mapped
                    for v in sample["contracts"].values()) for s in ("PARTIAL", "MISSING")}
    print(json.dumps({"samples": len(mapped), "contracts": 30,
                      "statuses": counts, "decision": decision["view_decision"]}))


if __name__ == "__main__":
    main()
