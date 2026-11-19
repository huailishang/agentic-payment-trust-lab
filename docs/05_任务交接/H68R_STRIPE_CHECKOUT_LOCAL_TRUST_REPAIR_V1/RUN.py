"""H68R offline-only, append-only bounded attempt ledger.

This runner never starts network, browser, servers, installation or payment.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[2]
LEDGER = PACK / "ATTEMPT_LEDGER.jsonl"
ALLOWED_KINDS = {"active_work", "implementation", "l2", "l3"}


def rows():
    if not LEDGER.is_file():
        return []
    data = [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [r["seq"] for r in data] != list(range(1, len(data) + 1)):
        raise RuntimeError("ledger_sequence_invalid")
    return data


def append(kind, event, attempt_id, status=None, **values):
    if kind not in ALLOWED_KINDS or event not in {"BEGIN", "END"}:
        raise RuntimeError("not_a_local_repair_attempt")
    if not (ROOT / "CURRENT.md").read_text(encoding="utf-8").find(
        "task_id: H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1"
    ) >= 0:
        raise RuntimeError("wrong_router")
    data = rows()
    previous = [r for r in data if r["attempt_id"] == attempt_id]
    if event == "BEGIN":
        if previous:
            raise RuntimeError("attempt_already_exists")
        caps = {"implementation":2, "l2":2, "l3":1}
        if kind in caps and sum(r["kind"] == kind and r["event"] == "BEGIN" for r in data) >= caps[kind]:
            raise RuntimeError("attempt_budget_exhausted")
    elif len(previous) != 1 or previous[0]["event"] != "BEGIN" or previous[0]["kind"] != kind:
        raise RuntimeError("attempt_not_open")
    if event == "END" and status not in {"SUCCEEDED", "FAILED", "INPUT_LIMIT"}:
        raise RuntimeError("invalid_attempt_status")
    row = {"seq":len(data)+1, "event":event,"attempt_id":attempt_id,"kind":kind,
           "at":datetime.now(timezone.utc).isoformat(),**values}
    if event == "END":
        row["status"] = status
    with LEDGER.open("ab") as f:
        f.write((json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",",":"))+"\n").encode())
        f.flush()
        os.fsync(f.fileno())
    print("H68R attempt:", kind, event, status or attempt_id)


def main(args):
    if len(args) not in (3,4):
        raise RuntimeError("usage RUN.py KIND BEGIN|END ID [STATUS]")
    kind,event,identifier,*rest = args
    append(kind,event,identifier,rest[0] if rest else None)


if __name__ == "__main__":
    main(sys.argv[1:])
