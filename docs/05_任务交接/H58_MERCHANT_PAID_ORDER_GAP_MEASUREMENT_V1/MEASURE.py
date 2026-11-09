"""H58 independent, read-only measurement of accepted paid-without-order evidence.

This module deliberately does not import CHECK or any merchant application code.
No checkout, payment, recovery or database write is performed.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure_once(lock):
    observations = load(ROOT / lock["observations"])
    summary = []
    for row in observations["cases"]:
        if not row["case"].startswith(("M01_", "M06_")):
            continue
        summary.append({
            "case": row["case"],
            "http_statuses": [c["response_status"] for c in row["calls"]],
            "payment_calls": len(row["psp_calls"]),
            "orders": len(row["state"]["orders"]),
            "inventory": row["state"]["inventory"],
            "attempts": row["state"]["attempts"],
            "recovery": row.get("recovery"),
            "authorization_records": row["authorization_records"],
        })
    assert len(summary) == 2 and summary[0]["case"].startswith("M01_")
    assert summary[1]["case"].startswith("M06_")

    tables = {}
    for relpath, expected_hash in lock["databases"].items():
        path = ROOT / relpath
        assert path.is_file() and digest(path) == expected_hash, relpath
        assert not Path(str(path) + "-wal").exists(), "Active WAL is forbidden"
        assert not Path(str(path) + "-shm").exists(), "Active shared-memory file"
        # immutable=1 is safe here only because frozen input checks confirmed
        # the database was cleanly closed and its content hash is pinned.
        connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            names = [r[0] for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )]
            tables[relpath] = {}
            for name in names:
                quoted = '"' + name.replace('"', '""') + '"'
                rows = [dict(r) for r in connection.execute("SELECT * FROM " + quoted)]
                tables[relpath][name] = sorted(
                    rows, key=lambda row: json.dumps(row, sort_keys=True)
                )
        finally:
            connection.close()
        assert digest(path) == expected_hash, "DB changed during read"
    return {"cases": summary, "m06_persisted_tables": tables}


def execute(role, repeat):
    assert repeat == 2, "Frozen task permits exactly two independent passes per run"
    folder = TASK / "evidence" / role
    folder.mkdir(parents=True, exist_ok=True)
    lock = load(TASK / "INPUTS.json")
    assert lock["head"] and len(lock["databases"]) == 2
    # Preserve any existing completed attempt artifacts without overwriting.
    targets = [folder / f"measurement_{index}.json" for index in (1, 2)]
    if any(p.exists() for p in targets):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        archived = folder / ("history_" + stamp)
        archived.mkdir(exist_ok=False)
        for path in targets:
            if path.exists():
                path.rename(archived / path.name)

    ledger_path = folder / "MEASUREMENT_ATTEMPTS.jsonl"
    results = []
    for index in (1, 2):
        existing = []
        if ledger_path.exists():
            existing = [json.loads(line) for line in
                        ledger_path.read_text(encoding="utf-8").splitlines() if line]
        assert len(existing) < (8 if role == "executor" else 4), "Measurement budget exhausted"
        attempt_id = "h58-" + uuid.uuid4().hex
        assert attempt_id not in {a["attempt_id"] for a in existing}
        reservation = {
            "attempt_id": attempt_id,
            "role": role,
            "utc": datetime.now(timezone.utc).isoformat(),
        }
        with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(reservation, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        observed = measure_once(lock)
        save_new(targets[index - 1], observed)
        results.append(observed)
    assert results[0] == results[1], "Independent passes drifted"
    if role == "executor":
        final = TASK / "MEASUREMENT.json"
        if final.exists():
            assert load(final) == results[0], "Previous accepted measurement differs"
        else:
            save_new(final, results[0])
        attempt_count = len(ledger_path.read_text(encoding="utf-8").splitlines())
        cost_path = TASK / "ATTEMPT_LEDGER.json"
        if cost_path.exists():
            ledger = load(cost_path)
            assert attempt_count <= 8
            ledger["measurement_passes"] = attempt_count
            ledger["formal_l2_attempts"] = len(list((TASK / "evidence").glob("l2_executor_*")))
            assert ledger["formal_l2_attempts"] <= 2
            # This JSON file is a report artifact, not a source database.
            cost_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"role": role, "repeat": 2, "case_count": 2,
                      "tables": sum(len(x) for x in results[0]["m06_persisted_tables"].values()),
                      "consistent": True, "business_calls": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True, choices=("executor", "evaluator"))
    parser.add_argument("--repeat", type=int, required=True)
    args = parser.parse_args()
    execute(args.role, args.repeat)
