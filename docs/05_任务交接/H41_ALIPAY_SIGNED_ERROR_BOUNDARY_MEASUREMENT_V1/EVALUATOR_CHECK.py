"""Independent offline L3: actual main/transport, only urllib opener is faked."""
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import h41_alipay_signed_error_probe as probe
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

SENTINEL = "H41_INDEPENDENT_SYNTHETIC_SECRET"
CURRENT = "\n".join([
    "```yaml", "workflow: evaluator-executor-workflow/v2.2",
    "task_id: H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1",
    "state: EXECUTING", "current_role: Executor", "authorization_api_call: true",
    "execution_phase: H41_SINGLE_DIAGNOSTIC",
    "contract_path: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/CONTRACT.md",
    "```", "",
])


def exercise(status=200, *, wrong_phase=False, revoke=False, tamper=False, unsigned=False):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    body = json.dumps({"code": "40004", "sub_code": "TRADE_NOT_FOUND",
                       "msg": SENTINEL, "nested": {"secret": SENTINEL}}, indent=2).encode()
    signature = base64.b64encode(key.sign(body, padding.PKCS1v15(), hashes.SHA256()))
    raw = b'{"alipay_aipay_agent_payment_verify_response":' + body + b',"sign":"' + signature + b'"}'
    if tamper:
        raw = raw.replace(b"40004", b"20000")
    if unsigned:
        raw = b'{"error":"' + SENTINEL.encode() + b'"}'
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        directory = root / probe.PACKAGE_REL / "evidence"
        directory.mkdir(parents=True)
        state = root / "CURRENT.md"
        state.write_text(CURRENT.replace("H41_SINGLE_DIAGNOSTIC", "H41_OFFLINE_PREPARATION")
                         if wrong_phase else CURRENT, encoding="utf-8")
        output = directory / "fact.json"
        stream = io.BytesIO(raw)
        opener = Mock()
        if status >= 400:
            opener.open.side_effect = HTTPError(probe.GATEWAY, status, SENTINEL, {}, stream)
        else:
            response = Mock(status=status)
            response.read.side_effect = stream.read
            opener.open.return_value = contextlib.nullcontext(response)
        inspector = Mock(return_value={"app_private": key, "alipay_public": key.public_key()})
        real_sign = probe.sign_request

        def sign(**kwargs):
            if revoke:
                state.write_text(CURRENT.replace("call: true", "call: false"), encoding="utf-8")
            return real_sign(**kwargs)

        signer = Mock(side_effect=sign)
        console = io.StringIO()
        with patch.object(probe, "ROOT", root), patch.object(probe, "inspect", inspector), \
                patch.object(probe, "sign_request", signer), \
                patch.object(probe, "build_opener", return_value=opener), \
                patch.dict(os.environ, {"AIPAY_APP_ID": "123456"}, clear=True), \
                contextlib.redirect_stdout(console), contextlib.redirect_stderr(console):
            rc = probe.main(["--execute", "--key-file", "unused-synthetic", "--output", str(output)])
        saved = output.read_text(encoding="utf-8") if output.exists() else ""
        fact = json.loads(saved) if saved else {}
        result = dict(rc=rc, inspect=inspector.call_count, sign=signer.call_count,
                      fake_attempts=opener.open.call_count,
                      reservation=(directory / "H41_DIAGNOSTIC.reserved").exists(),
                      classification=fact.get("classification"), http_status=fact.get("http_status"),
                      signature_verified=fact.get("signature_verified"),
                      response_digest_present=fact.get("response_sha256") is not None,
                      secret_safe=SENTINEL not in console.getvalue() + saved)
        stream.close()
        return result


def main():
    cases = {
        "signed_200": ({}, "SIGNED_BUSINESS_ERROR"),
        "wrong_phase": ({"wrong_phase": True}, None),
        "mid_run_revoke": ({"revoke": True}, "LOCAL_BLOCKED"),
        "tampered_200": ({"tamper": True}, "UNVERIFIED_RESPONSE"),
        "signed_400": ({"status": 400}, "SIGNED_BUSINESS_ERROR"),
        "signed_500": ({"status": 500}, "SIGNED_BUSINESS_ERROR"),
        "unsigned_400": ({"status": 400, "unsigned": True}, "UNVERIFIED_RESPONSE"),
    }
    results = {}
    for name, (kwargs, expected) in cases.items():
        actual = exercise(**kwargs)
        passed = actual["classification"] == expected and actual["secret_safe"]
        if "wrong_phase" in kwargs:
            passed &= actual["inspect"] == actual["sign"] == actual["fake_attempts"] == 0 and not actual["reservation"]
        elif "revoke" in kwargs:
            passed &= actual["fake_attempts"] == 0 and not actual["reservation"]
        else:
            passed &= actual["fake_attempts"] == 1 and actual["reservation"]
            passed &= actual["http_status"] == kwargs.get("status", 200) and actual["response_digest_present"]
            passed &= actual["signature_verified"] == (expected == "SIGNED_BUSINESS_ERROR")
        results[name] = dict(passed=passed, **actual)
    baseline = json.loads((Path(__file__).parent / "BASELINE.json").read_text(encoding="utf-8"))
    hashes_match = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                   for name, digest in baseline["protected_files"].items()}
    print(json.dumps(dict(cases=results, protected_hashes=hashes_match, real_network=0, real_key_reads=0), indent=2))
    return 0 if all(case["passed"] for case in results.values()) and all(hashes_match.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
