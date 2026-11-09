"""Frozen HTTP observation assertions. Does not implement HTTP or merchant behavior."""
import copy
import json

SPEC = {
    "C01_NORMAL_REPLAY": ([201, 200, 200], None, 1),
    "C02_CHANGED_AFTER_CONFIRM": ([201, 200, 409], "H50_SNAPSHOT_MISMATCH", 0),
    "C03_MISSING_CONFIRMATION": ([201, 403], "H50_CONFIRMATION_MISSING", 0),
    "C04_FORGED_CONFIRMATION": ([201, 403], "H50_CONFIRMATION_INVALID", 0),
    "C05_UNSIGNED_COMPLETE": ([201, 401], "signature_missing", 0),
    "C06_BODY_TAMPERED": ([201, 400], "digest_mismatch", 0),
    "C07_NO_CONTROL_INJECTION": ([201, 409], "H50_EXECUTION_DENIED", 0),
    "C08_CONCURRENT_COMPLETE": ([201, 200, 409], "H50_EXECUTION_DENIED", 1),
}
FALSE_FIELDS = ("production_ready", "real_identity_verified", "cross_system_revocation_verified",
    "provider_verified", "customer_validated", "global_race_closed", "product_core_changed")

def validate(value):
    assert value["schema"] == "h51-http-observations/v1"
    assert value["boundary"] == "FULL_PINNED_ASGI_APP_TASK_LOCAL_DEPENDENCY_OVERRIDE"
    assert value["require_signatures"] is True and value["network_calls"] == 0
    cases = value["cases"]
    assert len(cases) == 8 and {c["case"] for c in cases} == set(SPEC)
    request_count = 0
    for case in cases:
        ident = case["case"]
        expected_statuses, error, paid = SPEC[ident]
        calls = case["calls"]
        request_count += len(calls)
        statuses = [c["response_status"] for c in calls]
        if ident == "C08_CONCURRENT_COMPLETE":
            assert statuses[0] == 201 and sorted(statuses[1:]) == [200, 409]
        else:
            assert statuses == expected_statuses, (ident, statuses)
        assert calls[0]["method"] == "POST" and calls[0]["path"] == "/checkout-sessions"
        assert calls[-1]["method"] == "POST" and calls[-1]["path"].startswith("/checkout-sessions/") and calls[-1]["path"].endswith("/complete")
        assert all(isinstance(c["request_body"], dict) and isinstance(c["response_body"], dict) for c in calls)
        for index, call in enumerate(calls):
            headers = {k.lower(): v for k, v in call["headers"].items()}
            assert headers.get("ucp-agent") and headers.get("request-id") and headers.get("idempotency-key")
            if ident == "C05_UNSIGNED_COMPLETE" and index == len(calls) - 1:
                assert "signature" not in headers or "signature-input" not in headers
            else:
                assert headers.get("signature") and headers.get("signature-input") and headers.get("content-digest")
        if error:
            refused = next(c for c in reversed(calls) if c["response_status"] >= 400)
            assert refused["response_body"]["ucp"]["status"] == "error"
            assert error in {x["code"] for x in refused["response_body"]["messages"]}, ident
        if ident == "C01_NORMAL_REPLAY":
            assert calls[1]["response_body"] == calls[2]["response_body"]
            assert calls[1]["request_body"] == calls[2]["request_body"]
            keys = [{k.lower(): v for k, v in x["headers"].items()}["idempotency-key"] for x in calls[1:]]
            assert keys[0] == keys[1]
        if ident == "C02_CHANGED_AFTER_CONFIRM":
            assert calls[1]["method"] == "PUT" and calls[1]["response_status"] == 200
            assert calls[1]["request_body"]["line_items"][0]["quantity"] == 2
            assert case["confirmation"]["line_items"][0]["quantity"] == 1
        assert case["control_injected"] is (ident != "C07_NO_CONTROL_INJECTION")
        state, ledger = case["state"], case["psp_calls"]
        assert len(state["orders"]) == paid and len(ledger) == paid
        assert len(state["inventory"]) == 1 and state["inventory"][0]["quantity"] == 5 - paid
        if paid:
            confirmation = case["confirmation"]
            assert {"checkout_id", "merchant", "payee", "currency", "line_items", "totals", "fulfillment"} <= confirmation.keys()
            assert all(json.loads(row["snapshot_json"]) == confirmation and row["payment_ref"] for row in ledger)
        if ident == "C08_CONCURRENT_COMPLETE":
            sessions = case["completion_sessions"]
            assert len(sessions) == 2
            for key in ("request_id", "session_id", "connection_id"):
                assert len({x[key] for x in sessions}) == 2, key
            assert case["heartbeat_delays"] and max(case["heartbeat_delays"]) < 2
            assert any(x["event"] == "after_payment" for x in case["events"])
    assert value["asgi_requests"] == request_count and 0 < request_count <= 40

def validate_result(value):
    assert value["schema"] == "h51-result/v1"
    assert value["classification"] in {"LOCAL_HTTP_SLICE_OBSERVED", "CONTRACT_CHANGE_REQUIRED"}
    assert value["customer_demand"] == "UNKNOWN" and all(value[x] is False for x in FALSE_FIELDS)
    if value["classification"] == "CONTRACT_CHANGE_REQUIRED":
        assert value.get("contract_gaps")

def selftest():
    cases = []
    snap = {"checkout_id": "synthetic", "merchant": "synthetic", "payee": "synthetic", "currency": "USD",
        "line_items": [{"quantity": 1}], "totals": [], "fulfillment": None}
    for name, (statuses, error, paid) in SPEC.items():
        calls = []
        for index, status in enumerate(statuses):
            body = {"line_items": [{"quantity": 2 if name == "C02_CHANGED_AFTER_CONFIRM" and index == 1 else 1}]}
            headers = {"UCP-Agent": "synthetic", "Request-Id": str(index), "Idempotency-Key": "replay" if index else "create",
                "Signature": "CHECKER_FIXTURE_ONLY", "Signature-Input": "CHECKER_FIXTURE_ONLY", "Content-Digest": "CHECKER_FIXTURE_ONLY"}
            if name == "C05_UNSIGNED_COMPLETE" and index:
                del headers["Signature"]
            calls.append({"method": "PUT" if name == "C02_CHANGED_AFTER_CONFIRM" and index == 1 else "POST",
                "path": "/checkout-sessions" if index == 0 else "/checkout-sessions/synthetic/complete",
                "request_body": body, "headers": headers, "response_status": status,
                "response_body": {"ucp": {"status": "error"}, "messages": [{"code": error}]} if status >= 400 else {"id": "synthetic"}})
        cases.append({"case": name, "calls": calls, "control_injected": name != "C07_NO_CONTROL_INJECTION",
            "state": {"orders": [{}] * paid, "inventory": [{"quantity": 5 - paid}]}, "confirmation": snap,
            "psp_calls": [{"snapshot_json": json.dumps(snap), "payment_ref": "fixture"}] * paid,
            "completion_sessions": [{"request_id": 1, "session_id": 1, "connection_id": 1}, {"request_id": 2, "session_id": 2, "connection_id": 2}],
            "heartbeat_delays": [0.01], "events": [{"event": "after_payment"}]})
    good = {"schema": "h51-http-observations/v1", "boundary": "FULL_PINNED_ASGI_APP_TASK_LOCAL_DEPENDENCY_OVERRIDE",
        "require_signatures": True, "network_calls": 0, "asgi_requests": sum(len(c["calls"]) for c in cases), "cases": cases}
    validate(good)
    variants = []
    bad = copy.deepcopy(good); bad["cases"].pop(); variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][0]["psp_calls"] = []; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][0]["psp_calls"] *= 2; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][0]["psp_calls"][0]["snapshot_json"] = "{}"; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][4]["calls"][-1]["response_status"] = 200; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][6]["control_injected"] = True; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][-1]["completion_sessions"][1]["connection_id"] = 1; variants.append(bad)
    bad = copy.deepcopy(good); bad["cases"][-1]["heartbeat_delays"] = [11]; variants.append(bad)
    rejected = 0
    for bad in variants:
        try:
            validate(bad)
        except AssertionError:
            rejected += 1
    assert rejected == len(variants)
    result = {"schema": "h51-result/v1", "classification": "LOCAL_HTTP_SLICE_OBSERVED", "customer_demand": "UNKNOWN",
        **{key: False for key in FALSE_FIELDS}}
    validate_result(result)
    overclaim_rejected = 0
    for key in FALSE_FIELDS:
        bad = copy.deepcopy(result); bad[key] = True
        try:
            validate_result(bad)
        except AssertionError:
            overclaim_rejected += 1
    assert overclaim_rejected == len(FALSE_FIELDS)
    print(json.dumps({"boundary": "CHECKER_SELFTEST_NOT_HTTP_RUNTIME", "positive": True,
        "observation_mutations_rejected": rejected, "overclaim_mutations_rejected": overclaim_rejected}))

if __name__ == "__main__":
    selftest()
