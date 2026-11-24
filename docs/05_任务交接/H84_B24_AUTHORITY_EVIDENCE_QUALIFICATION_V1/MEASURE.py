"""H84 task-only source-transition measurement. Never call live payments."""
from __future__ import annotations
import base64
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
H83 = TASK.parent / "H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1"
BASELINE = "69a0512d9b4235b01acec173765a35ab2939f827"
WINDOW_SECONDS = 90
MAX_PROBES = 12
sys.path.insert(0, str(ROOT / "src"))

def need(condition, message):
    if not condition:
        raise AssertionError(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def authorize(collector):
    import yaml
    import subprocess
    role = os.environ.get("H84_ROLE")
    route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
    need(role in ("executor", "evaluator"), "role missing")
    expected = ("EXECUTING", "Executor") if role == "executor" else ("READY_FOR_REVIEW", "Evaluator")
    need((route["state"], route["current_role"]) == expected and route["task_id"] == TASK.name, "H84 frozen active route required")
    grant = read(TASK / "AUTHORIZATION.json")
    need(grant["status"] == "GRANTED", "owner grant missing")
    for key in ("authorization_existing_wsl", "authorization_local_service", "authorization_ephemeral_test_credentials"):
        need(route.get(key) is True and grant["flags"].get(key) is True, "missing scoped authority " + key)
    for key in ("authorization_commit", "authorization_push", "authorization_history_rewrite", "authorization_api_call", "authorization_install", "authorization_artifact_download", "authorization_test_payments", "authorization_container_dependency_install"):
        need(route.get(key) is False, "forbidden authority " + key)
    need(sys.platform == "linux" and re.fullmatch(r"[0-9a-f]{32}", collector.args.run_id) and re.fullmatch(r"[0-9a-f]{32}", collector.args.nonce), "isolated Linux run required")
    need(subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip() == BASELINE, "HEAD drift")
    freeze = read(TASK / "FREEZE.json")
    for rel, sha in freeze["frozen_sha256"].items():
        need(digest(ROOT / rel) == sha, "frozen file drift: " + rel)
    marker = TASK / "evidence" / (role + "_ATTEMPT.json")
    dispatch = read(marker)
    need(dispatch["run_id"] == collector.args.run_id and dispatch["nonce"] == collector.args.nonce and dispatch["budget_consumed"] == 1, "one-use dispatch mismatch")
    expected_dir = TASK / "evidence" / (role + "_runs") / collector.args.run_id
    need(collector.out == expected_dir and collector.out.resolve() == collector.out and not collector.out.is_symlink(), "output boundary")
    with (collector.out / "ISSUER_STARTED.json").open("x", encoding="utf-8") as f:
        json.dump({"role":role,"run_id":collector.args.run_id,"started_epoch":time.time()}, f)

def fixture(fact):
    spec = spec_from_file_location("h84_h83_fixture", H83 / "CHECK.py")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fixture(fact)

def observe(case, values, fact, at, action_id, expected, out):
    from agentic_payment_experiment import payment_execution
    real_gate = payment_execution.execute_with_payment_binding_gate
    observations = []
    def observed(*args, **kwargs):
        result = real_gate(*args, **kwargs)
        observations.append(result)
        return result
    execution = replace(values["execution_candidate"], payment_id=action_id, occurred_at=datetime.fromtimestamp(at, timezone.utc))
    with patch.object(payment_execution, "execute_with_payment_binding_gate", side_effect=observed):
        result, calls = case.invoke(**(values | {"execution_candidate":execution, "credential_possession_fact":fact, "credential_use_at_epoch":at}))
    row = {"action_id":action_id,"action_epoch":at,"order_digest":sha256(json.dumps(asdict(values["adaptation"].order),sort_keys=True,default=str).encode()).hexdigest(),
           "assurance":observations[0].identity_fact.assurance_level.name if len(observations)==1 else "UNKNOWN",
           "decision":result.decision.name,"callback_count":result.callback_count,"actual_test_callbacks":len(calls),"core_gate_calls":len(observations),
           "reason_codes":list(result.reason_codes),"fact_supplied":fact is not None}
    write(out, row)
    need(len(observations)==1 and row["assurance"]==expected and row["decision"]=="ALLOW" and row["callback_count"]==len(calls)==1, "unexpected identity or payment guard: " + str(row))
    return row

def transition(c, server, management, entry_id, processes):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession
    out = c.out
    data = c.state
    leaf = (out / "leaf.pem").read_bytes()
    cert = x509.load_pem_x509_certificate(leaf)
    fingerprint = cert.fingerprint(hashes.SHA256()).hex()
    at = data["observed_at_epoch"]
    fact = verify_x509_svid_credential_possession(
        leaf_svid_pem=leaf, trusted_ca_pem=(out/"root.pem").read_bytes(),
        expected_trust_domain="h76.test", expected_agent_ref="h76-agent",
        expected_provider_ref="h76-provider", expected_executor_instance_ref="h76-executor",
        credential_ref="h84:"+c.args.run_id, challenge_payload=(out/"payload.bin").read_bytes(),
        challenge_signature=base64.b64decode((out/"signature.b64").read_bytes().strip(),validate=True),
        nonce_ref=data["nonce"], issued_at_epoch=data["issued_at_epoch"],
        observed_at_epoch=at, max_age_seconds=300)
    need(fact.status.name=="VALID" and fact.observed_at_epoch==at,"fresh possession not VALID")
    case, values = fixture(fact)
    before = observe(case, values, fact, at, "h84-"+c.args.run_id+"-before", "VERIFIED", out/"BEFORE.json")
    before.update(source_status="ISSUED",certificate_sha256=fingerprint,nonce=c.args.nonce,source_observed_epoch=at,
                  source_response=processes["matching"]["raw"],holder_uid=processes["matching"]["kernel_uid"])
    write(out/"BEFORE.json", before)
    c.event("h84_registration_delete_start",entry_id=entry_id)
    deleted, raw = c.call("h84_entry_delete",[server,"entry","delete","-socketPath",management,"-entryID",entry_id],check=False)
    need(deleted.returncode==0,"isolated registration delete failed")
    # Management success is not proof that the workload API has caught up.
    deleted_at=time.time()
    deadline=time.monotonic()+WINDOW_SECONDS
    probes=[]
    denial=None
    for i in range(1,MAX_PROBES+1):
        if time.monotonic()>=deadline:
            break
        started=time.monotonic()
        response, proof=c.uid("transition",1001)
        message=(response.stdout+response.stderr).decode(errors="replace")
        observed_epoch=int(time.time())
        elapsed=time.monotonic()-started
        exact_denial=response.returncode!=0 and "PermissionDenied" in message and "no identity issued" in message and not any(s in message.lower() for s in ("connect: permission denied","connection refused","no such file","deadline exceeded"))
        result={"probe":i,"exit_code":response.returncode,"raw":proof["raw"],"holder_uid":proof["kernel_uid"],"observed_epoch":observed_epoch,
                "source_status":"DENIED" if exact_denial else ("ISSUED" if response.returncode==0 else "UNKNOWN"),"duration_seconds":elapsed}
        probes.append(result)
        write(out/"SOURCE_TRANSITION.json",{"entry_id":entry_id,"delete_raw":raw,"delete_epoch":deleted_at,"window_seconds":WINDOW_SECONDS,"probes":probes})
        if exact_denial and time.monotonic()<=deadline:
            denial=result
            break
        if response.returncode!=0:
            break
        time.sleep(min(5,max(0,deadline-time.monotonic())))
    if denial is None:
        data.update(status="SOURCE_TRANSITION_UNKNOWN")
        raise AssertionError("no explicit same-UID source denial within frozen observation window")
    after_at=denial["observed_epoch"]
    not_before=cert.not_valid_before.replace(tzinfo=timezone.utc).timestamp()
    not_after=cert.not_valid_after.replace(tzinfo=timezone.utc).timestamp()
    need(after_at>at and not_before<=after_at<=not_after,"old cert validity or observation ordering failed")
    # Never relabel the old signed fact as a fresh source response. The test
    # boundary withholds it because the current Workload API explicitly denied.
    after=observe(case,values,None,after_at,"h84-"+c.args.run_id+"-after","BOUND",out/"AFTER.json")
    after.update(source_status="DENIED",source_observation=denial,certificate_sha256=fingerprint,
                 old_certificate_still_in_validity=True,old_fact_observed_epoch=at,old_certificate_not_after_epoch=not_after,
                 evidence_scope="current issuance eligibility only; no claim of universal certificate revocation or forced payment deny")
    write(out/"AFTER.json",after)
    need(before["order_digest"]==after["order_digest"] and before["action_id"]!=after["action_id"],"comparison changed")
    data.update(status="H84_TRANSITION_OBSERVED",before=before,after=after,production_authority="UNKNOWN")
