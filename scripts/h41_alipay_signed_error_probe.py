"""H41 bounded diagnostic. Default is offline; CURRENT alone releases execution."""
import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agentic_payment_experiment.adapters.alipay_agent_pay_sandbox import (
    GATEWAY, sign_request, signed_response_parts,
)
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from h38_authorization_gate import parse_current_workflow
from h38_inspect_local_keys import inspect

TASK = "H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1"
PACKAGE_REL = "docs/05_任务交接/" + TASK
EXPECTED = dict(workflow="evaluator-executor-workflow/v2.2", task_id=TASK,
                state="EXECUTING", current_role="Executor",
                contract_path=PACKAGE_REL + "/CONTRACT.md",
                execution_phase="H41_SINGLE_DIAGNOSTIC")
CODES = {"10000", "20000", "40004"}
SUB_CODES = {"INVALID_PARAMETER", "CLIENT_SESSION_IS_EMPTY", "PAYMENT_PROOF_INVALID",
             "PAYMENT_PROOF_NOT_FOUND", "TRADE_NOT_FOUND", "TRADE_NO_INVALID"}


def authorize():
    fields, raw = parse_current_workflow((ROOT / "CURRENT.md").read_text(encoding="utf-8"))
    if any(fields.get(k) != v for k, v in EXPECTED.items()) or raw.get("authorization_api_call") != "true":
        raise ValueError("authorization")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def transport(request):
    # urllib's normal TLS checks remain enabled; no HTTP retry or redirect.
    try:
        response = build_opener(NoRedirect()).open(request, timeout=30)
    except HTTPError as error:
        # Error status can still carry signed evidence. Redirects remain blocked.
        if 300 <= error.code < 400:
            error.close()
            raise
        response = error
    with response as response:
        return response.status, response.read(1_000_001)


def classify(raw, public_key):
    result = dict(signature_verified=False, classification="UNVERIFIED_RESPONSE",
                  reason="INVALID_RESPONSE", code=None, sub_code=None)
    try:
        if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size < 2048:
            return result
        payload, signed, signature = signed_response_parts(raw)
        public_key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        return result
    result["signature_verified"] = True
    code = payload.get("code")
    if type(code) is not str or not code.strip():
        result["reason"] = "MISSING_CODE"
        return result
    sub = payload.get("sub_code")
    result.update(code=code if code in CODES else "OTHER",
                  sub_code="ABSENT" if "sub_code" not in payload else
                  sub if type(sub) is str and sub in SUB_CODES else "OTHER",
                  classification="SIGNED_UNEXPECTED_SUCCESS" if code == "10000" else "SIGNED_BUSINESS_ERROR",
                  reason="STOP_UNEXPECTED_SUCCESS" if code == "10000" else "ERROR_LAYER_UNDETERMINED")
    return result


def evidence():
    return dict(schema="h41-signed-error/v1", task=TASK,
                observed_at=datetime.now(timezone.utc).isoformat(),
                implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                gateway="ALIPAY_SANDBOX_HTTPS", attempt_count=0, http_status=None,
                response_sha256=None, signature_verified=False, classification="LOCAL_BLOCKED",
                reason="LOCAL_CHECK_FAILED", code=None, sub_code=None,
                observation_scope="SAME_PROCESS_SHARED_H38_PARSER_NO_INDEPENDENT_OBSERVER",
                synthetic_input=True, payment_success_proven=False, binding_proven=False)


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("invalid arguments")


def _run(argv):
    parser = QuietParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--key-file")
    args = parser.parse_args(argv)
    if not args.execute:
        print("DRY_RUN synthetic diagnostic plan; key_reads=0; attempts=0")
        return 0
    authorize()  # Before any key inspection or signing.
    directory = (ROOT / PACKAGE_REL / "evidence").resolve()
    if not args.output or not args.key_file:
        raise ValueError("missing input")
    output = Path(args.output).absolute()
    reservation = directory / "H41_DIAGNOSTIC.reserved"
    if (output.parent.resolve() != directory or output.name == reservation.name
            or output.is_symlink() or os.path.lexists(output) or os.path.lexists(reservation)):
        raise ValueError("output or reservation")
    app_id = os.environ.get("AIPAY_APP_ID", "")
    if not app_id or len(app_id) > 32 or not app_id.isascii() or not app_id.isdigit():
        raise ValueError("app id")
    # Inspector diagnostics are not part of H41's allowlisted evidence.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        keys = inspect(args.key_file, return_keys=True)
        if not isinstance(keys, dict):
            raise ValueError("keys")
        params = sign_request(app_id=app_id, private_key=keys["app_private"],
                              trade_no="0" * 32, payment_proof="0" * 64,
                              timestamp=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"))
    request = Request(GATEWAY, data=urlencode(params).encode("utf-8"), method="POST",
                      headers={"Content-Type": "application/x-www-form-urlencoded"})
    fact = evidence()
    directory.mkdir(exist_ok=True)
    # Claim the output before network as well as the fixed global attempt slot.
    with output.open("x", encoding="utf-8") as handle:
        try:
            authorize()  # Immediately before the exclusive reservation.
            with reservation.open("x", encoding="utf-8") as slot:
                slot.write("H41 single attempt reserved; retain even on failure.\n")
        except Exception:
            json.dump(fact, handle, indent=2)
            print("LOCAL_BLOCKED attempts=0")
            return 1
        fact["attempt_count"] = 1
        try:
            status, raw = transport(request)
            fact["http_status"] = status if type(status) is int and 100 <= status <= 599 else None
            fact["response_sha256"] = hashlib.sha256(raw).hexdigest()
            fact.update(classify(raw, keys["alipay_public"]))
        except Exception:
            fact.update(classification="TRANSPORT_INCONCLUSIVE", reason="TRANSPORT_FAILURE")
        json.dump(fact, handle, indent=2)
    print(fact["classification"] + " attempts=1; STOP; evaluator review required")
    return 0 if fact["classification"] == "SIGNED_BUSINESS_ERROR" else 1


def main(argv=None):
    try:
        return _run(argv)
    except Exception:
        # Includes parser, key, filesystem and output errors; never echo details.
        print("LOCAL_BLOCKED_OR_EVIDENCE_INCOMPLETE; STOP; no retry")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
