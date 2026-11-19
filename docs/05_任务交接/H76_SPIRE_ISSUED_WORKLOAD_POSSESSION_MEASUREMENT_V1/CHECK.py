"""Evaluator-frozen checks; runtime acquisition is an Executor task implementation."""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
PHASE = os.environ.get("H76_PHASE", "executor")
ORACLES = json.loads((P / "NEGATIVE_ORACLES.json").read_text(encoding="utf-8"))["cases"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def preservation(authority=True):
    baseline = read(P / "BASELINE.json")
    for rel, digest in baseline["protected"].items():
        need(sha(ROOT / rel) == digest, "protected drift: " + rel)
    for rel, digest in read(P / "FREEZE.json")["files"].items():
        need(sha(P / rel) == digest, "frozen drift: " + rel)
    need(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == baseline["head"], "HEAD drift")
    if authority:
        need((P / "AUTHORIZATION.md").is_file(), "runtime authority missing")
        import yaml
        route = yaml.safe_load((ROOT / "CURRENT.md").read_text(encoding="utf-8").split("```yaml", 1)[1].split("```", 1)[0])
        need(route["task_id"] == P.name and route["active_bottleneck_id"] == "B-15" and route["hypothesis_id"] == "H-76", "routing")
        need(route["state"] in ("CONTRACT_FROZEN", "EXECUTING", "READY_FOR_REVIEW"), "runtime state")
        for key in ("authorization_local_service", "authorization_artifact_download", "authorization_container_dependency_install", "authorization_ephemeral_test_credentials"):
            need(route.get(key) is True, "missing authority: " + key)
        for key in ("authorization_commit", "authorization_push", "authorization_history_rewrite", "authorization_api_call", "authorization_install", "authorization_test_payments"):
            need(route.get(key) is False, "excess authority: " + key)
    return {"protected": len(baseline["protected"]), "authority_checked": authority}


def current_output():
    index = read(P / "evidence" / (PHASE + "_current.json"))
    out = (P / index["output"]).resolve()
    need(out.is_relative_to((P / "evidence").resolve()), "output escape")
    return out


def live():
    preservation()
    run_id, nonce = uuid.uuid4().hex, uuid.uuid4().hex
    issued = int(datetime.now(timezone.utc).timestamp())
    out = P / "evidence" / (PHASE + "_runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    # RUN implements all acquisition and unconditional cleanup. Its stdout never carries keys.
    cmd = [sys.executable, "-B", str(P / "RUN.py"), "collect", "--phase", PHASE, "--run-id", run_id, "--nonce", nonce, "--issued-at", str(issued), "--out", str(out.relative_to(ROOT))]
    result = subprocess.run(cmd, cwd=ROOT, timeout=1250, check=False)
    need(result.returncode == 0, "actual acquisition failed; preserve branch evidence")
    data = read(out / "PUBLIC.json")
    need((data["run_id"], data["nonce"], data["issued_at_epoch"], data["phase"]) == (run_id, nonce, issued, PHASE), "fresh host challenge mismatch")
    (P / "evidence" / (PHASE + "_current.json")).write_text(json.dumps({"output": out.relative_to(P).as_posix(), "run_id": run_id, "nonce": nonce}) + "\n", encoding="utf-8")
    return public_checks(out)


def public_checks(out):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    data = read(out / "PUBLIC.json")
    required = ("root.pem", "leaf.pem", "signature.b64", "payload.bin", "server.conf", "agent.conf", "entry.json", "versions.json", "docker_inspect.json", "COMMANDS.jsonl", "CLEANUP.json", "server.redacted.log", "agent.redacted.log", "matching_fetch.stdout.log", "matching_fetch.stderr.log", "nonmatching_fetch.stdout.log", "nonmatching_fetch.stderr.log", "NONMATCHING.json")
    for name in required:
        need(sha(out / name) == data["files"][name], "public artifact digest: " + name)
    need(data["schema"] == "h76-public/v1" and data["matching_uid"] == data["signing_uid"] == 1001 and data["nonmatching_uid"] == 1002, "holder boundary")
    need(all(type(data[k]) is int and data[k] > 0 for k in ("matching_pid", "signing_pid", "nonmatching_pid")), "process evidence")
    need(data["matching_svid_count"] == 1 and data["private_key_export_count"] == data["payment_callback_count"] == 0, "identity/effect count")
    need(data["management_bundle_captured_before_fetch"] is True and bool(data["root_export_command_ref"]), "root bootstrap origin")
    roots = x509.load_pem_x509_certificates((out / "root.pem").read_bytes())
    leaves = x509.load_pem_x509_certificates((out / "leaf.pem").read_bytes())
    need(len(roots) == len(leaves) == 1, "requires direct root and single leaf; retain actual incompatible chain")
    root, leaf = roots[0], leaves[0]
    need(root.fingerprint(hashes.SHA256()).hex() == data["management_root_sha256"], "management root fingerprint")
    need(isinstance(root.public_key(), ec.EllipticCurvePublicKey) and isinstance(leaf.public_key(), ec.EllipticCurvePublicKey), "EC profile")
    need(root.issuer == root.subject and leaf.issuer == root.subject, "issuer chain")
    root.public_key().verify(root.signature, root.tbs_certificate_bytes, ec.ECDSA(root.signature_hash_algorithm))
    root.public_key().verify(leaf.signature, leaf.tbs_certificate_bytes, ec.ECDSA(leaf.signature_hash_algorithm))
    need(root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, "root CA profile")
    need(not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, "leaf CA prohibited")
    usage = leaf.extensions.get_extension_for_class(x509.KeyUsage).value
    need(usage.digital_signature and not usage.key_cert_sign and not usage.crl_sign, "leaf key usage")
    sans = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.UniformResourceIdentifier)
    need(sans == ["spiffe://h76.test/agent/h76-agent/executor/h76-executor"], "actual SPIFFE subject")
    expected = ("agentic-payment-possession/v1\nnonce=" + data["nonce"] + "\nagent=h76-agent\nprovider=h76-provider\nexecutor=h76-executor\nissued_at=" + str(data["issued_at_epoch"]) + "\n").encode()
    need((out / "payload.bin").read_bytes() == expected, "canonical payload bytes")
    leaf.public_key().verify(base64.b64decode((out / "signature.b64").read_bytes().strip(), validate=True), expected, ec.ECDSA(hashes.SHA256()))
    denied = read(out / "NONMATCHING.json")
    need(denied["uid"] == 1002 and denied["socket_connected"] is True and denied["write_directory_accessible"] is True and denied["rpc_status"] == "PermissionDenied" and denied["svid_count"] == 0, "actual selector rejection, not transport/OS failure")
    inspect = read(out / "docker_inspect.json")
    if isinstance(inspect, list):
        need(len(inspect) == 1, "inspect cardinality")
        inspect = inspect[0]
    host = inspect["HostConfig"]
    need(host["NetworkMode"] == "none" and host["ReadonlyRootfs"] is True and host["Privileged"] is False, "container isolation")
    need(not host.get("Binds") and all(m.get("Type") == "tmpfs" and m.get("Destination") in {"/run", "/tmp"} for m in inspect.get("Mounts", [])) and host.get("PidMode", "") != "host" and host.get("IpcMode", "") != "host" and not host.get("PortBindings"), "host access prohibited")
    need(set(host.get("Tmpfs", {})) == {"/run", "/tmp"}, "private tmpfs profile")
    need("ALL" in [x.upper() for x in host.get("CapDrop", [])] and {x.upper().removeprefix("CAP_") for x in host.get("CapAdd", [])} <= {"CHOWN", "SETUID", "SETGID"}, "capability profile")
    need(host.get("Memory", 0) <= 1073741824 and host.get("Memory", 0) > 0 and host.get("PidsLimit", 0) <= 128 and host.get("PidsLimit", 0) > 0, "resource limits")
    need(inspect["Config"]["Labels"].get("agentic-payment-task") == P.name, "container ownership")
    need(0 < host.get("NanoCpus", 0) <= 2000000000 and any(x.startswith("no-new-privileges") for x in host.get("SecurityOpt", [])), "CPU/security profile")
    versions, lock = read(out / "versions.json"), read(P / "ASSET_LOCK.json")
    need(versions["spire_server"] == versions["spire_agent"] == lock["spire_version"] and versions["python"] == "3.12.13", "actual runtime versions")
    need(versions["base_reference"] == lock["image_reference"] and versions["built_image_id"] == inspect["Image"], "actual image identity")
    for item in lock["files"]:
        need(versions["downloaded_files"][item["filename"]] == item["sha256"], "actual asset digest")
        if "package" in item:
            need(versions[item["package"]] == item["version"], "signing dependency version")
    for name in ("server.conf", "agent.conf"):
        need("dummy_" not in (out / name).read_text(encoding="utf-8") and "UpstreamAuthority" not in (out / name).read_text(encoding="utf-8"), "fresh local authority config")
    if PHASE == "evaluator":
        old = read(P / "evidence" / "executor_current.json")
        prior = read(P / old["output"] / "PUBLIC.json")
        need(data["management_root_sha256"] != prior["management_root_sha256"] and data["nonce"] != prior["nonce"], "independent issuance required")
    return {"run_id": data["run_id"], "root_sha256": data["management_root_sha256"], "uid_boundary": [1001, 1002], "independent_certificate_and_signature": True}


def negatives(out):
    from cryptography import x509
    from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession
    data = read(out / "PUBLIC.json")
    leaf = x509.load_pem_x509_certificate((out / "leaf.pem").read_bytes())
    root = x509.load_pem_x509_certificate((out / "root.pem").read_bytes())
    values = dict(leaf_svid_pem=(out / "leaf.pem").read_bytes(), trusted_ca_pem=(out / "root.pem").read_bytes(), expected_trust_domain="h76.test", expected_agent_ref="h76-agent", expected_provider_ref="h76-provider", expected_executor_instance_ref="h76-executor", credential_ref="h76:" + data["run_id"], challenge_payload=(out / "payload.bin").read_bytes(), challenge_signature=base64.b64decode((out / "signature.b64").read_bytes().strip(), validate=True), nonce_ref=data["nonce"], issued_at_epoch=data["issued_at_epoch"], observed_at_epoch=data["observed_at_epoch"], max_age_seconds=300)
    valid = verify_x509_svid_credential_possession(**values)
    need(valid.status.name == "VALID" and all((valid.credential_valid, valid.subject_binding_valid, valid.proof_of_possession_valid, valid.freshness_valid)) and not valid.replay_detected, "original verifier actual positive")
    vector = read(ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json")
    stale, expiry = data["issued_at_epoch"] + 301, int(leaf.not_valid_after_utc.timestamp()) + 1
    need(leaf.not_valid_before_utc.timestamp() <= stale <= leaf.not_valid_after_utc.timestamp() and root.not_valid_before_utc.timestamp() <= expiry <= root.not_valid_after_utc.timestamp(), "time mutation must isolate targeted boundary")
    variants = {"wrong_root": {"trusted_ca_pem": vector["untrusted_ca_pem"]}, "wrong_trust_domain": {"expected_trust_domain": "wrong.h76.test"}, "wrong_agent": {"expected_agent_ref": "wrong-agent"}, "wrong_executor": {"expected_executor_instance_ref": "wrong-executor"}, "wrong_provider": {"expected_provider_ref": "wrong-provider"}, "wrong_nonce_binding": {"nonce_ref": "different-nonce"}, "damaged_signature": {"challenge_signature": b"damaged-signature"}, "nonce_replay": {"consumed_nonce_refs": (data["nonce"],)}, "stale_challenge": {"observed_at_epoch": stale}, "expired_leaf_observation": {"observed_at_epoch": expiry}}
    result = {}
    for name, override in variants.items():
        fact = verify_x509_svid_credential_possession(**{**values, **override})
        need(fact.status.name != "VALID" and ORACLES[name] in fact.reason_codes, "negative oracle: " + name + ": " + repr(fact.reason_codes))
        result[name] = {"status": fact.status.name, "reasons": fact.reason_codes}
    (out.parent / (data["run_id"] + "_independent_verification.json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"actual_positive": "VALID", "negative_cases": len(result), "negative_valid": 0}


def regressions():
    commands = [[sys.executable, "-B", "-m", "unittest", "tests.trusted_execution.test_credential_possession", "tests.trusted_execution.test_identity_assurance", "tests.test_stripe_authority_context"], [sys.executable, "-B", "docs/05_任务交接/H74_DURABLE_AUTHORITY_CONTEXT_V1/CHECK.py", "regressions"]]
    for cmd in commands:
        subprocess.run(cmd, cwd=ROOT, check=True)
    return {"identity_and_context": "PASS", "original_stripe_safety_business": "PASS"}


def closeout():
    out = current_output()
    cleanup = read(out / "CLEANUP.json")
    need(cleanup["container_removed"] is True and cleanup["private_tmpfs_removed"] is True and cleanup["host_private_key_files"] == 0, "cleanup statement")
    cid = cleanup["container_id"]
    need(len(cid) == 64 and all(x in "0123456789abcdef" for x in cid), "full container ID")
    cmd = ["docker", "--host", "npipe:////./pipe/dockerDesktopLinuxEngine", "container", "inspect", cid]
    check = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=30)
    need(check.returncode != 0 and "No such" in check.stderr, "independent container absence; daemon error is not absence")
    events = [json.loads(x) for ledger in (P / "ATTEMPT_LEDGER.jsonl", P / "evidence/evaluator_ATTEMPT_LEDGER.jsonl") if ledger.exists() for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]
    need(len({e["event_id"] for e in events}) == len(events), "duplicate attempt event")
    for kind, cap in (("asset_file_attempt", 8), ("image_pull", 2), ("build", 2), ("actual_container", 4), ("formal_l2", 2), ("formal_l3", 1)):
        need(sum(e["kind"] == kind for e in events) <= cap, "attempt cap: " + kind)
    results = [e for e in events if e["kind"] == "result"]
    need(len({e["ref_event_id"] for e in results}) == len(results), "duplicate attempt result")
    completed = {e["ref_event_id"]: e for e in results}
    attempts = [e for e in events if e["kind"] == "asset_file_attempt"]
    permitted = {x["filename"] for x in read(P / "ASSET_LOCK.json")["files"]}
    total = 0
    for attempt in attempts:
        need(attempt["filename"] in permitted and attempt["event_id"] in completed, "asset identity or missing result")
        received = completed[attempt["event_id"]]["received_body_bytes"]
        need(type(received) is int and received >= 0, "file byte evidence unknown")
        total += received
    need(all(sum(a["filename"] == name for a in attempts) <= 2 for name in permitted), "per asset attempt ceiling")
    need(total <= 160 * 1024 * 1024, "file transfer budget")
    for run_id in {e.get("run_id") for e in events if e["kind"] == "actual_container"}:
        need(sum(e["kind"] == "matching_fetch" and e.get("run_id") == run_id for e in events) <= 3 and sum(e["kind"] == "nonmatching_fetch" and e.get("run_id") == run_id for e in events) <= 1, "per run fetch ceiling")
    for path in out.rglob("*"):
        if path.is_file():
            need(b"PRIVATE KEY-----" not in path.read_bytes(), "private key in public evidence: " + path.name)
    return {"independent_container_absence": True, "events": len(events)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("preflight", "preservation", "live", "verify", "regressions", "closeout", "final"))
    args = parser.parse_args()
    if args.check == "preflight":
        result = preservation(False)
    elif args.check == "preservation":
        result = preservation()
    elif args.check == "live":
        result = live()
    elif args.check == "verify":
        result = {**public_checks(current_output()), **negatives(current_output())}
    elif args.check == "regressions":
        result = regressions()
    elif args.check == "closeout":
        result = closeout()
    else:
        result = {**preservation(), **closeout()}
    print(json.dumps({"check": args.check, "phase": PHASE, "result": result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
