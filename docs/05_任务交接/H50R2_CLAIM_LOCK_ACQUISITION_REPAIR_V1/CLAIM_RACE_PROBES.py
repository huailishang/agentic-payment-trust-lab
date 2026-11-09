"""Evaluator-owned stale-precheck and shared-writer-lock acceptance schedules."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
spec = importlib.util.spec_from_file_location("h50r2_frozen_harness", TASK / "FROZEN_TESTS.py")
h = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h
spec.loader.exec_module(h)

async def race(directory, different_checkout):
    first_arrived, both_arrived, paid, release = [asyncio.Event() for _ in range(4)]
    arrivals, beats = 0, []
    async def hook(event, cid):
        nonlocal arrivals
        if event == "before_claim":
            arrivals += 1
            if arrivals == 1:
                first_arrived.set()
                await asyncio.wait_for(both_arrived.wait(), 10)
            elif arrivals == 2:
                both_arrived.set()
                await asyncio.wait_for(paid.wait(), 15)
                release.set()
                began = time.perf_counter()
                asyncio.get_running_loop().call_soon(lambda: beats.append(time.perf_counter() - began))
        elif event == "after_payment":
            paid.set()
            await asyncio.wait_for(release.wait(), 20)
    env = await h.Env(directory, hook=hook).open()
    try:
        await env.create()
        cid2, ref2 = env.cid, env.ref
        confirmed = {env.confirmed["checkout_id"]: env.confirmed}
        if different_checkout:
            created = await env.service_call("create_checkout", env.models.UnifiedCheckoutCreateRequest(**h.payload()), "race-create-second")
            assert created["ok"], created
            snap2 = h.snapshot(created["value"])
            cid2 = str(created["value"].id).split("/")[-1]
            ref2 = await env.control.issue(snap2, expires_at=h.NOW + 100)
            confirmed[snap2["checkout_id"]] = snap2
        async def second_call():
            return await env.service_call("complete_checkout", cid2, env.payment_cls(**h.payment()),
                {"h50_confirmation_ref": ref2}, "race-second")
        first = asyncio.create_task(env.complete(key="race-first"))
        await asyncio.wait_for(first_arrived.wait(), 10)
        second = asyncio.create_task(second_call())
        a, b = await asyncio.wait_for(asyncio.gather(first, second), 35)
        await asyncio.sleep(0)
        state, calls = env.state(), env.psp.calls()
        declared_denial = not b["ok"] and b.get("status") in {202, 400, 403, 409}
        # A different checkout may either receive a declared refusal/wait or
        # proceed after asynchronous acquisition. A duplicate may not charge.
        accepted_result = declared_denial or (different_checkout and b["ok"])
        expected_effects = 2 if different_checkout and b["ok"] else 1
        snapshots = [json.loads(x["snapshot_json"]) for x in calls]
        binding_ok = all(x == confirmed.get(x.get("checkout_id")) for x in snapshots)
        refs_unique = len({x["payment_ref"] for x in calls}) == len(calls)
        per_checkout_unique = len({x["checkout_id"] for x in snapshots}) == len(calls)
        completed_sessions = [x for x in env.sessions if x["method"] == "complete_checkout"]
        independent = len({x["session_id"] for x in completed_sessions}) == 2 and len({x["connection_id"] for x in completed_sessions}) == 2
        stock = state["inventory"][0]["quantity"]
        passed = (arrivals == 2 and a["ok"] and accepted_result and bool(beats) and max(beats) < 2
            and len(calls) == expected_effects and len(state["orders"]) == expected_effects
            and stock == 5 - expected_effects and binding_ok and refs_unique and per_checkout_unique and independent)
        return {"case": "S02_DIFFERENT_CHECKOUT_SHARED_WRITER" if different_checkout else "S01_SAME_CHECKOUT_STALE_PRECHECK",
            "passed": passed, "before_claim_arrivals": arrivals, "first_completed": a["ok"],
            "second": {k: v for k, v in b.items() if k != "value"}, "heartbeat_delays": beats,
            "payment_calls": len(calls), "orders": len(state["orders"]), "stock": stock,
            "binding_ok": binding_ok, "unique_references": refs_unique, "per_checkout_unique": per_checkout_unique,
            "independent_connections": independent, "events": env.events, "sessions": env.sessions}
    finally:
        release.set()
        await env.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--diagnostic", action="store_true", help="Preparation only; never acceptance")
    args = parser.parse_args()
    h.setup_imports(False)
    scratch = ROOT / ".task_envs/H50/runs"
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with patch("socket.socket.connect", h.deny_socket), patch("socket.create_connection", h.deny_socket):
        for different in (False, True):
            with tempfile.TemporaryDirectory(prefix="h50r2-race-", dir=scratch) as directory:
                results.append(asyncio.run(race(directory, different)))
    out = (ROOT / args.out).resolve()
    assert out.is_relative_to((TASK / "evidence").resolve())
    out.parent.mkdir(parents=True, exist_ok=True)
    value = {"schema": "h50r2-claim-races/v1", "diagnostic_only": args.diagnostic,
        "cases": results, "passed": all(x["passed"] for x in results), "network_calls": 0}
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": value["passed"], "diagnostic_only": args.diagnostic,
        "results": [{"case": x["case"], "passed": x["passed"], "second": x["second"],
            "heartbeat_delays": x["heartbeat_delays"]} for x in results]}))
    if not args.diagnostic:
        assert value["passed"], "claim acquisition contract still fails"

if __name__ == "__main__":
    main()
