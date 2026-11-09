"""Evaluator-owned consumer tests against actual copied merchant methods and SQLite.

Only fake payment, clock, signatures, trusted context and scheduling are fixtures.
No candidate verifier, policy or claim implementation is provided here.
"""
import argparse
import asyncio
from contextlib import closing
import copy
import hashlib
import json
import sqlite3
import sys
import tempfile
import uuid
from pathlib import Path
from RUNTIME import TASK, ROOT, bootstrap, load_parent_tests
bootstrap()
from FIXTURES import NOW, MERCHANT, PAYEE, keys, public, context, envelope, b64

P = load_parent_tests()
CASES = [
    "T01_NORMAL_CACHED_REPLAY", "T02_PROJECTED_AMOUNT", "T03_PROJECTED_CURRENCY",
    "T04_PROJECTED_PAYEE", "T05_PROJECTED_ROOT", "T06_CHECKOUT_SIGNATURE_TAMPER",
    "T07_RESIGNED_CHECKOUT_STALE_PAYMENT", "T08_UNTRUSTED_ROOT", "T09_EXPIRED_TOKEN",
    "T10_WRONG_AUDIENCE", "T11_WRONG_NONCE", "T12_MISSING_CONFIRMATION",
    "T13_FORGED_CONFIRMATION", "T14_REVOKED_CONFIRMATION", "T15_MISSING_AUTHORIZATION",
    "T16_DIRECT_CLAIM_WITHOUT_AUTHORIZATION", "T17_UPDATE_BEFORE_CLAIM", "T18_UNKNOWN_FIELD_CHANGED",
    "T19_DIFFERENT_CHECKOUT", "T20_CONCURRENT_COMPLETE", "T21_ORDER_FAILURE_RECOVERY",
    "T22_EXPIRED_CONFIRMATION", "T23_NO_CONTROL", "T24_SIGNED_AMOUNT_CONFLICT",
    "T25_SIGNED_CURRENCY_CONFLICT", "T26_SIGNED_PAYEE_CONFLICT", "T27_ENVELOPE_MUTATED_BEFORE_CLAIM",
    "T28_UNKNOWN_FIELD_INTACT"]
POSITIVE = {"T01_NORMAL_CACHED_REPLAY", "T20_CONCURRENT_COMPLETE", "T21_ORDER_FAILURE_RECOVERY", "T28_UNKNOWN_FIELD_INTACT"}

def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def checkout_row(env):
    with closing(sqlite3.connect(env.directory / "transactions.db")) as conn:
        return json.loads(conn.execute("SELECT data FROM checkouts WHERE id=?", (env.cid,)).fetchone()[0])

def replace_checkout(env, raw):
    with closing(sqlite3.connect(env.directory / "transactions.db")) as conn:
        conn.execute("UPDATE checkouts SET data=? WHERE id=?", (json.dumps(raw, ensure_ascii=False), env.cid))
        conn.commit()

def evidence_rows(env):
    with closing(sqlite3.connect(env.directory / "transactions.db")) as conn:
        conn.row_factory = sqlite3.Row
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='h53_authorizations'").fetchone():
            return []
        return [dict(row) for row in conn.execute("SELECT * FROM h53_authorizations")]

class Env(P.Env):
    async def open(self, seed=True):
        await super().open(seed)
        from services.execution_control import ExecutionControl
        import inspect
        assert Path(inspect.getfile(self.service_cls)).resolve() == (TASK / "merchant/services/checkout_service.py").resolve()
        assert Path(inspect.getfile(ExecutionControl)).resolve() == (TASK / "merchant/services/execution_control.py").resolve()
        self.signers = keys()
        self.trusted = context(self.signers)
        self.control = ExecutionControl(str(self.directory / "transactions.db"), self.psp,
            now=lambda: NOW, hook=self.hook, merchant=MERCHANT, payee=PAYEE,
            authorization_context=self.trusted)
        await self.control.initialize()
        return self

    async def authorized_complete(self, auth, *, key="h53-pay", ref="default", no_control=False):
        signals = {} if ref is None else {"h50_confirmation_ref": self.ref if ref == "default" else ref}
        if auth is not None:
            signals["h53_authorization"] = auth
        return await self.service_call("complete_checkout", self.cid, self.payment_cls(**P.payment()), signals,
                                       key, no_control=no_control)

async def scenario(name, directory):
    entered = asyncio.Event()
    release = asyncio.Event()
    env = None
    auth = None
    fired = False

    async def hook(event, cid):
        nonlocal fired
        if event == "before_claim" and not fired:
            fired = True
            if name == "T17_UPDATE_BEFORE_CLAIM":
                assert (await env.update())["ok"]
            if name == "T18_UNKNOWN_FIELD_CHANGED":
                current = checkout_row(env)
                current["h53_unknown"] = {"terms": "changed-after-signature"}
                replace_checkout(env, current)
            if name == "T27_ENVELOPE_MUTATED_BEFORE_CLAIM":
                auth["projection"]["payment_mandate"]["payment_amount"]["amount"] = 1500
        if event == "before_order_commit" and name == "T20_CONCURRENT_COMPLETE":
            entered.set()
            await asyncio.wait_for(release.wait(), timeout=8)
        if event == "before_order_commit" and name == "T21_ORDER_FAILURE_RECOVERY":
            raise RuntimeError("H53 injected order commit failure")

    env = Env(directory, hook=hook)
    try:
        await env.open()
        await env.create()
        raw = checkout_row(env)
        if name in {"T18_UNKNOWN_FIELD_CHANGED", "T28_UNKNOWN_FIELD_INTACT"}:
            raw["h53_unknown"] = {"terms": "synthetic-\u82b1\u5e97", "nested": [1, {"x": "keep"}]}
            replace_checkout(env, raw)
        if name == "T19_DIFFERENT_CHECKOUT":
            original = copy.deepcopy(raw)
            result = await env.service_call("create_checkout", env.models.UnifiedCheckoutCreateRequest(**P.payload()), "h53-create-second")
            assert result["ok"]
            env.checkout = result["value"]
            env.cid = str(env.checkout.id).split("/")[-1]
            env.ref = await env.control.issue(P.snapshot(env.checkout), expires_at=NOW+100)
            raw = original
        if name == "T22_EXPIRED_CONFIRMATION":
            env.ref = await env.control.issue(env.confirmed, expires_at=NOW-1)
        options = {}
        if name == "T08_UNTRUSTED_ROOT": options["issuer"] = "attacker"
        if name == "T09_EXPIRED_TOKEN": options["expired"] = True
        if name == "T10_WRONG_AUDIENCE": options["audience"] = "h53-other"
        if name == "T11_WRONG_NONCE": options["nonce"] = "h53-other"
        if name == "T24_SIGNED_AMOUNT_CONFLICT": options["amount"] = 1500
        if name == "T25_SIGNED_CURRENCY_CONFLICT": options["currency"] = "EUR"
        if name == "T26_SIGNED_PAYEE_CONFLICT": options["payee"] = "h53-other-payee"
        auth = envelope(raw, env.ref, env.signers, **options)
        if name == "T02_PROJECTED_AMOUNT": auth["projection"]["payment_mandate"]["payment_amount"]["amount"] = 1500
        if name == "T03_PROJECTED_CURRENCY": auth["projection"]["payment_mandate"]["payment_amount"]["currency"] = "EUR"
        if name == "T04_PROJECTED_PAYEE": auth["projection"]["payment_mandate"]["payee"]["id"] = "h53-other-payee"
        if name == "T05_PROJECTED_ROOT": auth["projection"]["open_payment_mandate"]["constraints"][0]["max"] = 999999
        if name == "T06_CHECKOUT_SIGNATURE_TAMPER":
            pieces = auth["checkout_jws"].split(".")
            changed = copy.deepcopy(raw)
            changed["currency"] = "EUR"
            pieces[1] = b64(json.dumps(changed, sort_keys=True, separators=(",", ":")).encode())
            auth["checkout_jws"] = ".".join(pieces)
        if name == "T07_RESIGNED_CHECKOUT_STALE_PAYMENT":
            changed = copy.deepcopy(raw)
            next(t for t in changed["totals"] if t["type"] == "total")["amount"] = 1500
            auth["checkout_jws"] = envelope(changed, env.ref, env.signers)["checkout_jws"]
        if name == "T14_REVOKED_CONFIRMATION": await env.control.revoke(env.ref)
        used_ref = None if name == "T12_MISSING_CONFIRMATION" else "h53-forged" if name == "T13_FORGED_CONFIRMATION" else "default"
        outcomes = []
        recovery = None
        if name == "T16_DIRECT_CLAIM_WITHOUT_AUTHORIZATION":
            try:
                await env.control.claim(env.cid, env.ref, "direct-key", "direct-hash")
                outcomes.append({"ok": True})
            except Exception as exc:
                outcomes.append({"ok": False, "error": type(exc).__name__, "status": getattr(exc, "status_code", None), "code": getattr(exc, "code", None)})
        elif name == "T20_CONCURRENT_COMPLETE":
            first = asyncio.create_task(env.authorized_complete(auth))
            try:
                await asyncio.wait_for(entered.wait(), timeout=8)
                during = env.state()
                assert during["payment_calls"] == 1 and len(during["orders"]) == 0
                outcomes.append(await asyncio.wait_for(env.authorized_complete(auth, key="second"), timeout=4))
            finally:
                release.set()
                outcomes.append(await first)
        else:
            outcomes.append(await env.authorized_complete(None if name == "T15_MISSING_AUTHORIZATION" else auth,
                ref=used_ref, no_control=name == "T23_NO_CONTROL"))
            if name == "T01_NORMAL_CACHED_REPLAY":
                outcomes.append(await env.authorized_complete(auth))
            if name == "T21_ORDER_FAILURE_RECOVERY":
                from services.execution_control import ExecutionControl
                restarted = ExecutionControl(str(env.directory / "transactions.db"), env.psp, now=lambda: NOW,
                    hook=env.hook, merchant=MERCHANT, payee=PAYEE, authorization_context=env.trusted)
                await restarted.initialize()
                recovery = await restarted.recover(env.cid)
                outcomes.append(await env.authorized_complete(auth, key="retry-after-failure"))
        state = env.state()
        observations = {"case": name, "raw_checkout_signed": raw, "confirmation_ref": env.ref,
            "authorization": auth, "public_key_registry": public(env.signers), "trusted_context": env.trusted,
            "results": [{k: v for k, v in result.items() if k != "value"} for result in outcomes],
            "state": state, "psp_calls": env.psp.calls(), "authorization_records": evidence_rows(env),
            "events": env.events, "sessions": env.sessions, "recovery": recovery}
        return observations
    except BaseException as exc:
        failure = {"case": name, "error": type(exc).__name__, "detail": str(exc), "authorization": auth}
        for key in ("raw", "outcomes", "recovery"):
            if key in locals(): failure[key] = locals()[key]
        if hasattr(env, "signers"):
            failure["public_key_registry"] = public(env.signers)
        try:
            failure["state"] = env.state()
            failure["psp_calls"] = env.psp.calls()
        except Exception:
            failure["state_unavailable"] = True
        json_write(TASK / "evidence/failures" / (name + "-" + uuid.uuid4().hex + ".json"), failure)
        raise
    finally:
        if hasattr(env, "manager"):
            await env.close()

def check(row):
    name, state = row["case"], row["state"]
    assert name in CASES
    expected = 1 if name in POSITIVE else 0
    assert state["payment_calls"] == len(row["psp_calls"]) == expected, name
    assert len(state["orders"]) == (0 if name == "T21_ORDER_FAILURE_RECOVERY" else expected), name
    assert len(state["attempts"]) == len(row["authorization_records"]) == expected, name
    if name not in POSITIVE:
        assert all(not result["ok"] and result["status"] in {400, 403, 409} for result in row["results"]), row["results"]
        assert state["inventory"][0]["quantity"] == 5
    else:
        assert state["inventory"][0]["quantity"] == (5 if name == "T21_ORDER_FAILURE_RECOVERY" else 4)
        record = row["authorization_records"][0]
        assert record["checkout_id"] == state["attempts"][0]["checkout_id"]
        assert record["confirmation_ref"] == row["confirmation_ref"] and record["decision"] == "ALLOW"
        assert record["token_sha256"] == hashlib.sha256(row["authorization"]["payment_token"].encode()).hexdigest()
        assert record["checkout_sha256"] == hashlib.sha256(row["authorization"]["checkout_jws"].encode()).hexdigest()
        paid_snapshot = json.loads(row["psp_calls"][0]["snapshot_json"])
        assert paid_snapshot == json.loads(state["attempts"][0]["snapshot_json"])
        assert paid_snapshot == P.snapshot(row["raw_checkout_signed"])
        if name == "T21_ORDER_FAILURE_RECOVERY":
            assert row["recovery"]["decision"] == "QUERY" and row["recovery"]["payment_state"] == "SUCCEEDED"
            assert row["recovery"]["payment_ref"] == row["psp_calls"][0]["payment_ref"]
            assert all(not result["ok"] for result in row["results"])
        elif name == "T20_CONCURRENT_COMPLETE":
            assert sorted(result["ok"] for result in row["results"]) == [False, True]
            assert len({s["connection_id"] for s in row["sessions"] if s["method"] == "complete_checkout"}) == 2
        else:
            assert all(result["ok"] for result in row["results"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    assert out.is_relative_to((TASK / "evidence").resolve())
    import yaml
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    assert route["task_id"] == TASK.name
    evaluator = route["current_role"] == "Evaluator"
    assert ("l3" in out.stem) == evaluator
    ledger_path = TASK / ("evidence/evaluator_attempt_ledger.json" if evaluator else "ATTEMPT_LEDGER.json")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"artifact_cases_run": 0, "runs": []}
    assert ledger["artifact_cases_run"] + len(CASES) <= (102 if evaluator else 272)
    ledger["artifact_cases_run"] += len(CASES)
    attempt = {"output": out.relative_to(ROOT).as_posix(), "cases_reserved": len(CASES), "status": "RESERVED"}
    ledger.setdefault("runs", []).append(attempt)
    json_write(ledger_path, ledger)
    if out.exists():
        raw = out.read_bytes()
        archive = TASK / "evidence/archive" / (out.stem + "-" + hashlib.sha256(raw).hexdigest() + ".json")
        if archive.exists(): assert archive.read_bytes() == raw
        else:
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(raw)
    value = {"schema": "h53-claim-consumer-observations/v1", "boundary": "LOCAL_METHOD_EXACT_BYTES_SYNTHETIC_TRUST_FAKE_PSP",
             "network_calls": 0, "asgi_requests": 0, "real_payment_calls": 0, "cases": []}
    scratch = ROOT / ".task_envs/H53R/runs"
    try:
        P.setup_imports(False)
        # setup_imports inserts its old task path; force candidate merchant first.
        sys.path.insert(0, str(TASK / "merchant"))
        for name in CASES:
            with tempfile.TemporaryDirectory(prefix="consumer-", dir=scratch) as directory:
                value["cases"].append(asyncio.run(scenario(name, directory)))
            json_write(out, value)
            check(value["cases"][-1])
        attempt["status"] = "OBSERVED"
    except BaseException as exc:
        attempt.update(status="FAILED", error=type(exc).__name__, detail=str(exc))
        value["failure"] = copy.deepcopy(attempt)
        json_write(out, value)
        raise
    finally:
        json_write(ledger_path, ledger)
    print(json.dumps({"cases": len(value["cases"]), "fake_payment_invocations": sum(c["state"]["payment_calls"] for c in value["cases"]), "real_payment_calls": 0}))

if __name__ == "__main__":
    main()
