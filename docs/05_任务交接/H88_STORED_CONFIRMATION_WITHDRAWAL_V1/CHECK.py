"""Frozen local checks for H88 using the H87 business inputs and regressions."""

from contextlib import closing, redirect_stdout
from dataclasses import replace
from datetime import datetime, timedelta
import hashlib
from importlib import machinery, util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name("H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1")
MUTABLE = {
    "src/agentic_payment_experiment/adapters/stripe_checkout.py",
    "src/agentic_payment_experiment/stripe_checkout_lab.py",
}
BASELINE = TASK / "BASELINE.json"
FREEZE = TASK / "FREEZE.json"
EVENT = "h88-local-withdrawal"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def put_json(path, value):
    with path.open("x", encoding="utf-8") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")


def prepare_imports():
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]
    os.environ["PYTHONPATH"] = str(ROOT / "src")
    spec = machinery.ModuleSpec("tests", loader=None, is_package=True)
    spec.submodule_search_locations = [str(ROOT / "tests")]
    sys.modules["tests"] = util.module_from_spec(spec)
    spec = util.spec_from_file_location("h87_frozen_check", PARENT / "CHECK.py")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def head():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(parent):
    old = read_json(PARENT / "INPUTS.json")
    assert head() == old["head"]
    assert parent.source_files() == old["source_files"]
    accepted = read_json(PARENT / "evidence/evaluator/ACCEPTANCE.json")
    prior_map = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r146.md"
    map_name = "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"
    assert sha(prior_map) == accepted["map_sha256"] == old["files"][map_name]
    assert set(MUTABLE).issubset(old["files"])
    files = {}
    for name, expected in old["files"].items():
        path = prior_map if name == map_name else ROOT / name
        assert sha(path) == expected, name
        if name not in MUTABLE:
            files[path.relative_to(ROOT).as_posix()] = expected
    assert len(files) == 196
    for name, value in accepted["submission"].items():
        assert sha(ROOT / name) == value, name
        files[name] = value
    extra = [
        *(PARENT / "evidence/evaluator/l3").iterdir(),
        PARENT / "REVIEW.md",
        PARENT / "evidence/evaluator/ACCEPTANCE.json",
        ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md",
        prior_map,
        BASELINE,
        TASK / "CHECK.py",
        TASK / "CONTRACT.md",
        TASK / "EXECUTOR_START.md",
        TASK / "VALIDATION_PLAN.yaml",
    ]
    for path in extra:
        assert path.is_file(), path
        files[path.relative_to(ROOT).as_posix()] = sha(path)
    put_json(FREEZE, {"head": head(), "source_files": parent.source_files(),
                     "mutable": sorted(MUTABLE), "files": dict(sorted(files.items()))})


def preserve(parent):
    lock = read_json(FREEZE)
    assert head() == lock["head"]
    assert parent.source_files() == lock["source_files"], "source set changed"
    assert set(lock["mutable"]) == MUTABLE
    for name, expected in lock["files"].items():
        assert sha(ROOT / name) == expected, name
    print(json.dumps({"protected_files": len(lock["files"]), "preservation": "PASS"}))


def original_row(database):
    with closing(sqlite3.connect(database)) as con:
        return con.execute(
            "SELECT snapshot_sha256, payload_json FROM authority_contexts"
        ).fetchone()


def normal(fixture, store=None):
    from tests.test_stripe_authority_context import OP
    from agentic_payment_experiment.adapters.stripe_checkout import CheckoutReceipt

    store = store or fixture.reopened()
    created = fixture.stored_create(store)
    assert isinstance(created, CheckoutReceipt)
    store.bind_session(OP, fixture.session())
    clicks = []
    paid = fixture.stored_pay(fixture.reopened(), clicked=clicks)
    result = {"create_decision": created.gate.final_decision.value,
              "payment_decision": paid.final_decision.value,
              "create": len(fixture.client.created), "get": len(fixture.client.queries),
              "click": len(clicks)}
    assert result == {"create_decision": "ALLOW", "payment_decision": "ALLOW",
                      "create": 1, "get": 1, "click": 1}, result
    return result


def original_write_rejects(fixture):
    from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
    from agentic_payment_experiment.trusted_execution.confirmation import ConfirmationStatus

    revoked = replace(fixture.ctx, confirmation_record=replace(
        fixture.ctx.confirmation_record, status=ConfirmationStatus.REVOKED))
    try:
        fixture.recorded(revoked)
    except StripeCheckoutError as error:
        assert str(error) == "authority_original_gate_not_allowed", str(error)
        return str(error)
    raise AssertionError("original approval writer accepted a revoked replacement")


def baseline(parent):
    from tests.test_stripe_authority_context import _Fixture, graph_sha
    from tests.test_stripe_checkout_adapter import NOW

    with redirect_stdout(io.StringIO()):
        parent.preserve()
    fixture = _Fixture()
    fixture.setUp()
    try:
        fixture.ref = fixture.recorded()
        assert not hasattr(fixture.store, "record_confirmation_withdrawal")
        with closing(sqlite3.connect(fixture.db)) as con:
            legacy_schema = [row[0] for row in con.execute(
                "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY rowid"
            )]
        result = {"classification": "PREPARATION_BASELINE", "head": head(),
                  "fixed_time": NOW.isoformat(), "graph_sha256": graph_sha(fixture.ctx),
                  "withdrawal_entry_available": False,
                  "original_writer_rejection": original_write_rejects(fixture),
                  "normal": normal(fixture), "legacy_schema": legacy_schema}
    finally:
        fixture.doCleanups()
        assert not fixture.db.exists()
    put_json(BASELINE, result)
    print(json.dumps({k: v for k, v in result.items() if k != "legacy_schema"}))


def event_args(fixture):
    from tests.test_stripe_checkout_adapter import NOW

    return {
        "expected_sha256": fixture.ref,
        "confirmation_id": fixture.ctx.confirmation_record.confirmation_id,
        "subject_ref": fixture.ctx.mandate.user_id,
        "event_id": EVENT,
        "received_at": NOW,
    }


def assert_blocked(result):
    assert result.final_decision.value == "CONFIRMATION_REQUIRED", result
    assert result.callback_count == 0 and not result.callback_executed
    return result.final_decision.value


def run_withdrawn(fixture, precreate):
    from tests.test_stripe_authority_context import OP, graph_sha

    before = original_row(fixture.db)
    if not precreate:
        created = fixture.stored_create()
        assert created.gate.final_decision.value == "ALLOW"
        fixture.store.bind_session(OP, fixture.session())
    role = fixture.reopened()
    args = event_args(fixture)
    receipt = role.record_confirmation_withdrawal(OP, **args)
    assert receipt["operation_id"] == OP
    assert receipt["snapshot_sha256"] == args["expected_sha256"]
    for key in ("confirmation_id", "subject_ref", "event_id"):
        assert receipt[key] == args[key], key
    assert receipt["source"] == "LOCAL_USER_CONTROL"
    received = datetime.fromisoformat(receipt["received_at"])
    assert received == args["received_at"] and received.utcoffset() == timedelta(0)
    cold = fixture.reopened()
    assert cold.record_confirmation_withdrawal(OP, **args) == receipt
    assert cold.get_confirmation_withdrawal(OP, expected_sha256=fixture.ref) == receipt
    clicks = []
    counts_before = len(fixture.client.created), len(fixture.client.queries)
    result = fixture.stored_create(cold) if precreate else fixture.stored_pay(cold, clicked=clicks)
    counts_after = len(fixture.client.created), len(fixture.client.queries)
    assert counts_after == counts_before and not clicks
    decision = assert_blocked(result)
    assert original_row(fixture.db) == before
    original = cold.load_authority(OP, expected_sha256=fixture.ref)
    assert original == fixture.ctx and original.confirmation_record.status.value == "CONFIRMED"
    assert graph_sha(original) == read_json(BASELINE)["graph_sha256"]
    return {"decision": decision, "create_get_click_delta": [0, 0, 0], "receipt": receipt}


def rejected_bindings(fixture):
    from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
    from tests.test_stripe_authority_context import OP
    from tests.test_stripe_checkout_adapter import NOW

    store = fixture.reopened()
    args = event_args(fixture)
    rejected = {}
    for label, operation, variation in (
        ("wrong_subject", OP, {"subject_ref": "other-synthetic-user"}),
        ("wrong_confirmation", OP, {"confirmation_id": "other-confirmation"}),
        ("wrong_snapshot", OP, {"expected_sha256": "a" * 64}),
        ("wrong_operation", "other-operation", {}),
        ("naive_time", OP, {"received_at": NOW.replace(tzinfo=None)}),
        ("before_approval", OP, {"received_at": NOW - timedelta(seconds=1)}),
    ):
        try:
            store.record_confirmation_withdrawal(operation, **(args | variation))
        except (StripeCheckoutError, ValueError) as error:
            rejected[label] = str(error)
        else:
            raise AssertionError(label)
        assert store.get_confirmation_withdrawal(OP, expected_sha256=fixture.ref) is None
    return rejected


def rejected_conflicts(fixture, receipt):
    from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
    from tests.test_stripe_authority_context import OP

    store = fixture.reopened()
    args = event_args(fixture)
    for variation in ({"event_id": "other-event"},
                      {"received_at": args["received_at"] + timedelta(seconds=1)}):
        try:
            store.record_confirmation_withdrawal(OP, **(args | variation))
        except (StripeCheckoutError, ValueError):
            pass
        else:
            raise AssertionError("conflicting withdrawal accepted")
    assert store.get_confirmation_withdrawal(OP, expected_sha256=fixture.ref) == receipt
    return 2


def withdrawal_store_table(database):
    with closing(sqlite3.connect(database)) as con:
        expected = {"operations", "webhook_receipts", "delivery_attempts",
                    "recoveries", "authority_contexts"}
        current = {row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )}
        assert len(current - expected) == 1, current
        (name,) = current - expected
        indexes = con.execute("SELECT name FROM pragma_index_list(?) WHERE [unique]=1", (name,))
        indexed = list(indexes)
        assert any([r[0] for r in con.execute(
            "SELECT name FROM pragma_index_info(?) ORDER BY seqno", (index,)
        )] == ["event_id"] for (index,) in indexed), "event ID has no unique constraint"
    return name


def unreadable_state(fixture, precreate):
    from agentic_payment_experiment.adapters.stripe_checkout import StripeCheckoutError
    from tests.test_stripe_authority_context import OP

    store = fixture.reopened()
    if not precreate:
        assert fixture.stored_create().gate.final_decision.value == "ALLOW"
        store.bind_session(OP, fixture.session())
    table = withdrawal_store_table(fixture.db).replace('"', '""')
    with closing(sqlite3.connect(fixture.db)) as con:
        con.execute(f'DROP TABLE "{table}"')
        con.commit()
    clicks = []
    before = len(fixture.client.created), len(fixture.client.queries)
    try:
        gate = fixture.stored_create(store) if precreate else fixture.stored_pay(store, clicked=clicks)
    except (StripeCheckoutError, sqlite3.Error):
        gate = None
    if gate is not None:
        assert not gate.callback_executed and gate.final_decision.value != "ALLOW"
    assert (len(fixture.client.created), len(fixture.client.queries)) == before
    assert not clicks


def legacy(fixture, baseline_data):
    from agentic_payment_experiment.stripe_checkout_lab import StripeLabLedger
    from tests.test_stripe_authority_context import OP

    legacy_db = fixture.db.with_name("legacy.sqlite3")
    with closing(sqlite3.connect(legacy_db)) as target, closing(sqlite3.connect(fixture.db)) as source:
        for statement in baseline_data["legacy_schema"]:
            target.execute(statement)
        for name in ("operations", "authority_contexts"):
            row = source.execute(f"SELECT * FROM {name}").fetchone()
            placeholders = ", ".join("?" for _ in row)
            target.execute(f"INSERT INTO {name} VALUES ({placeholders})", row)
        target.commit()
    before = original_row(legacy_db)
    old_db = fixture.db
    fixture.db = legacy_db
    try:
        store = StripeLabLedger(legacy_db)
        assert store.get_confirmation_withdrawal(OP, expected_sha256=fixture.ref) is None
        result = normal(fixture, store)
        assert original_row(legacy_db) == before == original_row(old_db)
    finally:
        fixture.db = old_db
    return result


def behavior(parent):
    from tests.test_stripe_authority_context import _Fixture

    preserve(parent)
    baseline_data = read_json(BASELINE)
    results = {}
    for scenario in ("normal", "before_create", "before_pay",
                     "unreadable_create", "unreadable_pay", "legacy"):
        fixture = _Fixture()
        fixture.setUp()
        try:
            fixture.ref = fixture.recorded()
            if scenario == "normal":
                results["rejections"] = rejected_bindings(fixture)
                results[scenario] = normal(fixture)
                assert results[scenario] == baseline_data["normal"]
                assert original_write_rejects(fixture) == baseline_data["original_writer_rejection"]
            elif scenario in {"before_create", "before_pay"}:
                results[scenario] = run_withdrawn(fixture, precreate=scenario == "before_create")
                results[scenario]["conflicts_rejected"] = rejected_conflicts(
                    fixture, results[scenario]["receipt"]
                )
            elif scenario.startswith("unreadable"):
                unreadable_state(fixture, precreate=scenario == "unreadable_create")
                results[scenario] = "FAIL_CLOSED"
            else:
                results[scenario] = legacy(fixture, baseline_data)
        finally:
            fixture.doCleanups()
            assert not fixture.db.parent.exists(), "temporary directory was not cleaned"
    print(json.dumps(results, ensure_ascii=False, indent=2))
    preserve(parent)


def regressions(parent):
    preserve(parent)
    total = 0
    for name, expected in parent.SUITES.items():
        suite = unittest.defaultTestLoader.loadTestsFromName(name)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        assert result.wasSuccessful() and not result.skipped and result.testsRun == expected, name
        total += result.testsRun
    assert total == 124
    print(json.dumps({"passed": total, "skipped": 0}))


def main():
    if sys.flags.optimize:
        raise RuntimeError("frozen assertions require an unoptimized Python interpreter")
    parent = prepare_imports()
    command, = sys.argv[1:]
    if command == "preflight":
        assert sys.version_info[:2] == (3, 12)
        parent.preflight()
        if FREEZE.is_file():
            preserve(parent)
    else:
        commands = {"baseline": baseline, "freeze": freeze, "preserve": preserve,
                    "behavior": behavior, "regressions": regressions}
        commands[command](parent)


if __name__ == "__main__":
    main()
