"""Run the eight frozen HTTP scenarios, preserving actual transport observations."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from HTTP_RUNTIME import Merchant, TASK, ROOT
from HTTP_CHECKER import SPEC, validate


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


class Budget:
    """Persist every scheduled request, including attempts that fail before response."""
    def __init__(self, out):
        self.evaluator = "l3" in out.stem
        # L3 must preserve the accepted Executor ledger, keeping its own evidence.
        self.path = TASK / "evidence/evaluator_http_attempt_ledger.json" if self.evaluator else TASK / "ATTEMPT_LEDGER.json"
        self.value = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"http_runs": []}
        self.counter = "evaluator_asgi_requests" if self.evaluator else "asgi_requests"
        self.value.setdefault(self.counter, 0)
        self.run = {"output": out.relative_to(ROOT).as_posix(), "role": "evaluator" if self.evaluator else "executor",
            "started_at": datetime.now(timezone.utc).isoformat(), "scheduled_requests": 0, "status": "RUNNING"}
        self.value.setdefault("http_runs", []).append(self.run)
        self.save()

    def save(self):
        write_json(self.path, self.value)

    def request(self):
        assert self.run["scheduled_requests"] < 40
        assert self.value[self.counter] < (80 if self.evaluator else 160)
        self.value[self.counter] += 1
        self.run["scheduled_requests"] += 1
        self.save()


async def scenario(name, on_request):
    blocked = asyncio.Event()
    release = asyncio.Event()
    delays = []

    async def hook(event, checkout_id):
        if name == "C08_CONCURRENT_COMPLETE" and event == "before_order_commit":
            blocked.set()
            await asyncio.wait_for(release.wait(), timeout=8)

    async with Merchant(injected=name != "C07_NO_CONTROL_INJECTION", hook=hook, on_request=on_request) as merchant:
        await merchant.create()
        if name != "C03_MISSING_CONFIRMATION":
            await merchant.confirm()
        if name == "C02_CHANGED_AFTER_CONFIRM":
            response = await merchant.update()
            assert response.status_code == 200, response.text
        if name == "C08_CONCURRENT_COMPLETE":
            first = asyncio.create_task(merchant.complete(key="first"))
            heartbeat_stop = asyncio.Event()

            async def heartbeat():
                while not heartbeat_stop.is_set():
                    start = time.monotonic()
                    await asyncio.sleep(0.001)
                    delays.append(time.monotonic() - start)

            beat = asyncio.create_task(heartbeat())
            try:
                await asyncio.wait_for(blocked.wait(), timeout=8)
                # Independent DB reader sees A durable, payment made, B uncommitted.
                state = merchant.observation(name, delays)
                assert len(state["psp_calls"]) == 1 and not state["state"]["orders"]
                merchant.events.append({"event": "independent_reader_before_followup", "orders": 0, "charges": 1})
                second = await asyncio.wait_for(merchant.complete(key="second"), timeout=4)
                assert second.status_code == 409, second.text
            finally:
                release.set()
                await first
                heartbeat_stop.set()
                await beat
        else:
            await merchant.complete(ref=None if name == "C03_MISSING_CONFIRMATION" else
                "h51-forged-reference" if name == "C04_FORGED_CONFIRMATION" else "default",
                signed=name != "C05_UNSIGNED_COMPLETE", tamper=name == "C06_BODY_TAMPERED")
            if name == "C01_NORMAL_REPLAY":
                await merchant.complete()
        return merchant.observation(name, delays)


async def run(out):
    budget = Budget(out)
    value = {"schema": "h51-http-observations/v1",
        "boundary": "FULL_PINNED_ASGI_APP_TASK_LOCAL_DEPENDENCY_OVERRIDE",
        "require_signatures": True, "network_calls": 0, "asgi_requests": 0, "cases": []}
    try:
        for name in SPEC:
            value["cases"].append(await scenario(name, budget.request))
            value["asgi_requests"] = budget.run["scheduled_requests"]
            write_json(out, value)
        validate(value)
        budget.run["status"] = "OBSERVED"
        print(json.dumps({"case_count": len(value["cases"]), "asgi_requests": value["asgi_requests"],
            "statuses": {c["case"]: [x["response_status"] for x in c["calls"]] for c in value["cases"]},
            "heartbeat_max_seconds": max(value["cases"][-1]["heartbeat_delays"])}))
    except BaseException as exc:
        budget.run.update(status="FAILED", error=type(exc).__name__, detail=str(exc))
        value["asgi_requests"] = budget.run["scheduled_requests"]
        write_json(out, value)
        raise
    finally:
        budget.run["finished_at"] = datetime.now(timezone.utc).isoformat()
        budget.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    target = (ROOT / args.out).resolve()
    assert target.is_relative_to((TASK / "evidence").resolve())
    asyncio.run(run(target))
