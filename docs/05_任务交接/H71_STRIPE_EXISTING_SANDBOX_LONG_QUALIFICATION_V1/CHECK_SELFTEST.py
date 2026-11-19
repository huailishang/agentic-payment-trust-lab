"""Offline counterexamples: a stopped probe must never turn into permission success."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PACK=Path(__file__).resolve().parent
item=importlib.util.spec_from_file_location("h71_check_selftest",PACK/"CHECK.py")
check=importlib.util.module_from_spec(item); item.loader.exec_module(check)
KEY="rkcs_test_synthetic_fixture"
ACCOUNT="acct_synthetic_fixture"
OLD="a"*64

def fixture(private):
    raw=b'{"error":{"type":"synthetic_denial"}}'
    (private/"denied.bin").write_bytes(raw)
    phases={name:{"status":"PASS","reason":"MEASURED"} for name in check.spec()["phases"]}
    phases["readonly"]={"status":"INPUT_LIMIT","reason":"HTTP_403"}
    for name in ("download","listen","browser_local"): phases[name]={"status":"NOT_RUN","reason":"PREVIOUS_LIMIT"}
    result={"schema":"h71-long-qualification-result/v1","task_id":PACK.name,"run_id":"synthetic",
        "decision":"INPUT_LIMIT","reason_code":"READ_HTTP_403","stage":"readonly","private_snapshot_sha256":"c"*64,
        "account_ref":check.sha(ACCOUNT.encode()),"account_assurance":"PROVISION_CREDENTIAL_CONTEXT_ONLY",
        "checkout_write_permission":"NOT_MEASURED","checkout_sessions":0,"payments":0}
    material={"schema":"h71-long-qualification-private/v1","run_id":"synthetic","h69_snapshot_sha256":OLD,
        "key_sha256":check.sha(KEY.encode()),"account_ref":result["account_ref"],"phases":phases,
        "http":[{"method":"GET","url":check.spec()["urls"][0],"started_at":"2026-11-12T14:00:00Z",
        "finished_at":"2026-11-12T14:00:01Z","status":403,"error":None,"body_file":"denied.bin",
        "body_sha256":check.sha(raw),"key_sha256":check.sha(KEY.encode())}],
        "listener":{"attempted":False,"ready":False},"browser":{"attempted":False}}
    return result,material

class Counterexamples(unittest.TestCase):
    def test_authentic_stopped_probe_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve(); result,material=fixture(p)
            check.validate_material(result,material,p,KEY,ACCOUNT,OLD)

    def test_unexpected_objects_are_a_valid_stop_not_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve(); result,material=fixture(p)
            raw=b'{"object":"list","has_more":false,"data":[{"id":"synthetic_unexpected"}]}'
            (p/"objects.bin").write_bytes(raw)
            material["http"][0].update(status=200,body_file="objects.bin",body_sha256=check.sha(raw))
            check.validate_material(result,material,p,KEY,ACCOUNT,OLD)

    def test_twelve_false_success_or_boundary_mutations_rejected(self):
        def ready(r,m): r.update(decision="READ_AND_LISTEN_READY",stage="complete")
        def continued(r,m): m["phases"]["download"]["status"]="PASS"
        def wrong_source(r,m): m["h69_snapshot_sha256"]="b"*64
        def wrong_key(r,m): m["key_sha256"]="b"*64
        def paid(r,m): r["payments"]=1
        def wrong_endpoint(r,m): m["http"][0]["url"]="https://api.stripe.com/v1/account"
        def write(r,m): m["http"][0]["method"]="POST"
        def repeated(r,m): m["http"].append(copy.deepcopy(m["http"][0]))
        def browser(r,m): m["browser"]["attempted"]=True
        def strong_identity(r,m): r["account_assurance"]="INDEPENDENT_ACCOUNT_VERIFIED"
        def digest(r,m): m["http"][0]["body_sha256"]="b"*64
        def unsupported_claim(r,m): r["checkout_write_permission"]="ALLOW"
        for mutation in (ready,continued,wrong_source,wrong_key,paid,wrong_endpoint,write,repeated,browser,strong_identity,digest,unsupported_claim):
            with self.subTest(mutation=mutation.__name__),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp).resolve(); result,material=fixture(p); mutation(result,material)
                with self.assertRaises(ValueError): check.validate_material(result,material,p,KEY,ACCOUNT,OLD)

if __name__=="__main__": unittest.main(verbosity=2)
