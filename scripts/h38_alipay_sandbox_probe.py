"""One-shot sandbox probe. Missing inputs never trigger network activity.

Persistent per-case reservations prevent accidental replay; no automatic retries.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import GATEWAY, sign_request, verify_response
from h38_authorization_gate import AuthorizationGateError, require_h38_live_authorization
from h38_inspect_local_keys import inspect

PACKAGE = ROOT / "docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1"
sys.path.insert(0, str(PACKAGE / "evaluator_checks"))
from response_observer import observe
from fact_schema import validate


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["valid", "tampered-proof"], required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--key-file", help="Explicitly authorized local sandbox key file")
    parser.add_argument("--execute", action="store_true", help="Consume one reserved sandbox call")
    args = parser.parse_args()
    if args.execute:
        try:
            require_h38_live_authorization(ROOT)
        except AuthorizationGateError:
            print("BLOCKED current task authorization gate")
            return 1
    names = ["AIPAY_APP_ID", "H38_TRADE_NO", "H38_PAYMENT_PROOF", "H38_EXPECTED_OUT_TRADE_NO",
             "H38_EXPECTED_AMOUNT", "H38_EXPECTED_RESOURCE_ID"]
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        print("BLOCKED missing input names: " + ", ".join(missing))
        return 1
    if not args.key_file:
        print("BLOCKED explicit local sandbox key file required")
        return 1
    if os.environ.get("AIPAY_GATEWAY", GATEWAY) != GATEWAY:
        print("BLOCKED non-sandbox gateway")
        return 1
    proof = os.environ["H38_PAYMENT_PROOF"]
    if len(proof) != 64:
        print("BLOCKED fixture proof must have frozen 64-character shape")
        return 1
    expected = dict(trade_no=os.environ["H38_TRADE_NO"],
                    out_trade_no=os.environ["H38_EXPECTED_OUT_TRADE_NO"],
                    amount=os.environ["H38_EXPECTED_AMOUNT"], resource_id=os.environ["H38_EXPECTED_RESOURCE_ID"])
    if verify_response(b"", None, expected=expected)["reason_codes"] == ["MISSING_EXPECTATION"]:
        print("BLOCKED invalid trusted expectation")
        return 1
    if verify_response(b"", None, expected=expected)["reason_codes"] == ["MISSING_EXPECTATION"]:
        print("BLOCKED invalid trusted expectation")
        return 1
    if args.case == "tampered-proof":
        proof = ("0" if proof[0] != "0" else "1") + proof[1:]
        control_path = PACKAGE / "evidence/H38_LIVE_VALID_FACT.json"
        import hashlib
        try:
            control = json.loads(control_path.read_text(encoding="utf-8"))
            if control["status"] != "VALID" or control["trade_no_sha256"] != hashlib.sha256(expected["trade_no"].encode()).hexdigest():
                raise ValueError()
        except (OSError, ValueError, KeyError):
            print("BLOCKED matching valid control required before negative")
            return 1
    keys = inspect(args.key_file, return_keys=True)
    if not isinstance(keys, dict):
        return 1
    params = sign_request(app_id=os.environ["AIPAY_APP_ID"], private_key=keys["app_private"],
                          trade_no=expected["trade_no"], payment_proof=proof,
                          timestamp=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
                          client_session=os.environ.get("H38_CLIENT_SESSION"))
    if not args.execute:
        print("READY request signed in memory; no network call (requires --execute)")
        return 0
    output = Path(args.output).resolve()
    if output.parent != (PACKAGE / "evidence").resolve() or output.exists():
        print("BLOCKED output must be a new file in task evidence directory")
        return 1
    try:
        require_h38_live_authorization(ROOT)
    except AuthorizationGateError:
        print("BLOCKED current task authorization gate")
        return 1
    output.parent.mkdir(exist_ok=True)
    reservation = output.parent / ("H38_" + args.case + ".reserved")
    try:
        with reservation.open("x", encoding="utf-8") as handle:
            handle.write("One call reserved. Do not clear or retry without evaluator review.\n")
    except FileExistsError:
        print("BLOCKED call already reserved; no replay")
        return 1
    request = Request(GATEWAY, data=urlencode(params).encode("utf-8"),
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with build_opener(NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(1_000_001)
        observation = observe(raw, keys["alipay_public"])
        fact = verify_response(raw, keys["alipay_public"], expected=expected)
    except Exception:
        print("BLOCKED network/response failure; reservation retained; no automatic retry")
        return 1
    with output.open("x", encoding="utf-8") as handle:
        json.dump(fact, handle, indent=2)
    with output.with_suffix(".observation.json").open("x", encoding="utf-8") as handle:
        json.dump(observation, handle, indent=2)
    print("Sanitized fact written; independent evaluator review still required")
    return 0 if observation["signature_verified"] and validate(fact, args.case) is None else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("BLOCKED local probe error; no exception details emitted")
        raise SystemExit(1)
