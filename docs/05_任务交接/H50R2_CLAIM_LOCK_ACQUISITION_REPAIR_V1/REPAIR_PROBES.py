"""Frozen repair acceptance: late contention and supported payment branch routing."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
spec = importlib.util.spec_from_file_location("h50r_frozen_harness", TASK / "FROZEN_TESTS.py")
h = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h
spec.loader.exec_module(h)

async def contention(directory, revocation=False):
    arrived, release = asyncio.Event(), asyncio.Event()
    claims = 0
    beats = []
    def heartbeat():
        began = time.perf_counter()
        asyncio.get_running_loop().call_soon(lambda: beats.append(time.perf_counter()-began))
    async def hook(event, cid):
        nonlocal claims
        if event == "before_claim":
            claims += 1
            if claims == 2:
                release.set()
                heartbeat()
        elif event == "after_payment":
            arrived.set()
            await asyncio.wait_for(release.wait(), 20)
    env = await h.Env(directory, hook=hook).open()
    try:
        await env.create()
        first = asyncio.create_task(env.complete(key="repair-first"))
        await asyncio.wait_for(arrived.wait(),10)
        if revocation:
            async def revoke():
                heartbeat()
                asyncio.get_running_loop().call_soon(release.set)
                try:
                    await env.control.revoke(env.ref)
                    return {"ok": True}
                except Exception as exc:
                    return {"ok": False, "error": type(exc).__name__, "status": getattr(exc,"status_code",None)}
            follower = asyncio.create_task(revoke())
        else:
            follower = asyncio.create_task(env.complete(key="repair-follower"))
        a, b = await asyncio.wait_for(asyncio.gather(first,follower),30)
        await asyncio.sleep(0)
        declared = b["ok"] if revocation else False
        declared = declared or (not b["ok"] and b.get("status") in {202,400,403,409})
        state = env.state()
        passed = a["ok"] and declared and bool(beats) and max(beats) < 2.0 and len(env.psp.calls()) == 1 and len(state["orders"]) == 1
        return {"case": "R02_REVOKE_DURING_ORDER_WRITE" if revocation else "R01_FOLLOWER_DURING_ORDER_WRITE",
            "passed": passed, "first_completed": a["ok"],
            "follower": {k:v for k,v in b.items() if k!="value"}, "heartbeat_delays": beats,
            "payment_calls": len(env.psp.calls()), "orders": len(state["orders"]), "events": env.events}
    finally:
        release.set()
        await env.close()

async def branch(directory, handler):
    env = await h.Env(directory).open()
    try:
        await env.create()
        body=h.payment(); body["instruments"][0]["handler_id"]=handler
        result=await env.service_call("complete_checkout",env.cid,env.payment_cls(**body),
            {"h50_confirmation_ref":env.ref},"repair-"+handler)
        calls=env.psp.calls(); state=env.state()
        passed=result["ok"] and len(calls)==1 and len(state["orders"])==1 and json.loads(calls[0]["snapshot_json"])==env.confirmed
        return {"case": "R03_GOOGLE_PAY" if handler=="google_pay" else "R04_SHOP_PAY", "passed":passed,
            "method_completed":result["ok"],"payment_calls":len(calls),"orders":len(state["orders"]),
            "error":{k:v for k,v in result.items() if k!="value"}}
    finally:
        await env.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    parser.add_argument("--diagnostic",action="store_true",help="Preparation only: record expected inherited failures without claiming acceptance")
    args=parser.parse_args()
    h.setup_imports(False)
    scratch=ROOT/".task_envs/H50/runs"; scratch.mkdir(parents=True,exist_ok=True)
    observations=[]
    with patch("socket.socket.connect",h.deny_socket),patch("socket.create_connection",h.deny_socket):
        for kind in ("follower","revocation","google_pay","shop_pay"):
            with tempfile.TemporaryDirectory(prefix="h50r-",dir=scratch) as directory:
                if kind in {"follower","revocation"}:
                    result=asyncio.run(contention(directory,kind=="revocation"))
                else:
                    result=asyncio.run(branch(directory,kind))
                observations.append(result)
    out=(ROOT/args.out).resolve(); assert out.is_relative_to((TASK/"evidence").resolve())
    out.parent.mkdir(parents=True,exist_ok=True)
    data={"schema":"h50r-repair-observations/v1","diagnostic_only":args.diagnostic,
        "cases":observations,"passed":all(x["passed"] for x in observations),"network_calls":0}
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"cases":len(observations),"passed":data["passed"],"diagnostic_only":args.diagnostic,
        "results":[{"case":x["case"],"passed":x["passed"]} for x in observations]}))
    if not args.diagnostic:
        assert data["passed"], "frozen H50R counterexamples remain"

if __name__=="__main__":
    main()
