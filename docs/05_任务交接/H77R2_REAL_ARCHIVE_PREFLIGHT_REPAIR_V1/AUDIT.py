"""Evaluator read-only audit of H76; writes only new H77 preparation evidence."""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OLD = P.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"
SOURCE = OLD / "evidence/wsl_experiment/d446ee01ee70"
sys.path.insert(0, str(ROOT / "src"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def need(value, message):
    if not value:
        raise ValueError(message)


def crypto(directory):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from agentic_payment_experiment.trusted_execution.credential_possession import verify_x509_svid_credential_possession

    data = read(directory / "RESULT.json")
    root_pem = (directory / "root.pem").read_bytes()
    leaf_pem = (directory / "leaf.pem").read_bytes()
    root = x509.load_pem_x509_certificate(root_pem)
    leaf = x509.load_pem_x509_certificate(leaf_pem)
    payload = (directory / "payload.bin").read_bytes()
    signature = base64.b64decode((directory / "signature.b64").read_bytes().strip(), validate=True)
    need(root_pem.count(b"BEGIN CERTIFICATE") == leaf_pem.count(b"BEGIN CERTIFICATE") == 1, "single root and leaf")
    need(isinstance(root.public_key(), ec.EllipticCurvePublicKey) and isinstance(leaf.public_key(), ec.EllipticCurvePublicKey), "EC profile")
    need(root.subject == root.issuer and leaf.issuer == root.subject, "direct root chain")
    root.public_key().verify(root.signature, root.tbs_certificate_bytes, ec.ECDSA(root.signature_hash_algorithm))
    root.public_key().verify(leaf.signature, leaf.tbs_certificate_bytes, ec.ECDSA(leaf.signature_hash_algorithm))
    leaf.public_key().verify(signature, payload, ec.ECDSA(hashes.SHA256()))
    need(root.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, "root CA")
    need(not leaf.extensions.get_extension_for_class(x509.BasicConstraints).value.ca, "non-CA leaf")
    usage = leaf.extensions.get_extension_for_class(x509.KeyUsage).value
    need(usage.digital_signature and not usage.key_cert_sign and not usage.crl_sign, "leaf key usage")
    need(leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.UniformResourceIdentifier) == ["spiffe://h76.test/agent/h76-agent/executor/h76-executor"], "SPIFFE subject")
    issued, nonce = data["issued_at_epoch"], data["nonce"]
    need(payload == (f"agentic-payment-possession/v1\nnonce={nonce}\nagent=h76-agent\nprovider=h76-provider\nexecutor=h76-executor\nissued_at={issued}\n").encode(), "canonical challenge")
    observed = data.get("observed_at_epoch", issued + 1)
    values = dict(leaf_svid_pem=leaf_pem, trusted_ca_pem=root_pem, expected_trust_domain="h76.test", expected_agent_ref="h76-agent", expected_provider_ref="h76-provider", expected_executor_instance_ref="h76-executor", credential_ref="h77:public-audit:" + data["run_id"], challenge_payload=payload, challenge_signature=signature, nonce_ref=nonce, issued_at_epoch=issued, observed_at_epoch=observed, max_age_seconds=300)
    valid = verify_x509_svid_credential_possession(**values)
    need(valid.status.name == "VALID" and all((valid.credential_valid, valid.subject_binding_valid, valid.proof_of_possession_valid, valid.freshness_valid)) and not valid.replay_detected, "original verifier positive")
    def epoch(cert, field):
        value = getattr(cert, field + "_utc", None)
        if value is None:
            value = getattr(cert, field).replace(tzinfo=timezone.utc)
        return int(value.timestamp())
    stale, expired = issued + 301, epoch(leaf, "not_valid_after") + 1
    need(epoch(leaf, "not_valid_before") <= stale <= epoch(leaf, "not_valid_after"), "stale isolates freshness")
    need(epoch(root, "not_valid_before") <= expired <= epoch(root, "not_valid_after"), "expiry isolates leaf")
    vector = read(ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json")
    variants = {
        "wrong_root": {"trusted_ca_pem": vector["untrusted_ca_pem"]},
        "wrong_trust_domain": {"expected_trust_domain": "wrong.h76.test"},
        "wrong_agent": {"expected_agent_ref": "wrong-agent"},
        "wrong_executor": {"expected_executor_instance_ref": "wrong-executor"},
        "wrong_provider": {"expected_provider_ref": "wrong-provider"},
        "wrong_nonce_binding": {"nonce_ref": "different-nonce"},
        "damaged_signature": {"challenge_signature": b"damaged-signature"},
        "nonce_replay": {"consumed_nonce_refs": (nonce,)},
        "stale_challenge": {"observed_at_epoch": stale},
        "expired_leaf_observation": {"observed_at_epoch": expired},
    }
    oracles = read(OLD / "NEGATIVE_ORACLES.json")["cases"]
    outcomes = {}
    for name, override in variants.items():
        fact = verify_x509_svid_credential_possession(**{**values, **override})
        need(fact.status.name != "VALID" and oracles[name] in fact.reason_codes, "negative: " + name)
        outcomes[name] = {"status": fact.status.name, "reasons": list(fact.reason_codes)}
    return {"positive": "VALID", "negative_cases": outcomes, "negative_valid": 0, "root_der_sha256": root.fingerprint(hashes.SHA256()).hex(), "nonce": nonce, "observation": "recorded actual observation" if "observed_at_epoch" in data else "historical issued_at+1; not current-time authentication"}


def main():
    out = P / "evidence/preparation"
    out.mkdir(parents=True, exist_ok=False)
    refs = P / "references/before_h77"
    refs.mkdir(parents=True, exist_ok=False)
    aliases = {}
    for name, rel in (("CURRENT.md", "CURRENT.md"), ("REMOTE_HANDOFF.md", "REMOTE_HANDOFF.md"), ("PROJECT_BOTTLENECK_MAP_r128.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md")):
        (refs / name).write_bytes((ROOT / rel).read_bytes())
        aliases[rel] = {"sha256": sha(ROOT / rel), "snapshot": (refs / name).relative_to(ROOT).as_posix()}
    baseline = read(OLD / "BASELINE.json")
    drift = [rel for rel, digest in baseline["protected"].items() if not (ROOT / rel).is_file() or sha(ROOT / rel) != digest]
    frozen_drift = [rel for rel, digest in read(OLD / "FREEZE.json")["files"].items() if sha(OLD / rel) != digest]
    need(not drift and not frozen_drift, "H76 baseline/freeze drift")
    index = read(SOURCE / "EVIDENCE_INDEX.json")["public_files"]
    for rel, digest in index.items():
        path = (SOURCE / rel).resolve()
        need(path.is_relative_to(SOURCE.resolve()) and path.is_file() and sha(path) == digest, "indexed evidence: " + rel)
        need(b"PRIVATE KEY-----" not in path.read_bytes(), "private key marker in indexed evidence")
    result = crypto(SOURCE)
    need(b"PermissionDenied" in (SOURCE / "nonmatching.stderr.log").read_bytes(), "raw RPC refusal")
    runs = []
    for directory in sorted((OLD / "evidence/wsl_experiment").iterdir()):
        if directory.is_dir() and (directory / "RESULT.json").is_file():
            item = read(directory / "RESULT.json")
            runs.append({"run_id": directory.name, "status": item["status"], "tmpfs_removed": item.get("tmpfs_removed"), "processes_terminated": item.get("spire_processes_terminated")})
    h76_files = {f.relative_to(ROOT).as_posix(): sha(f) for f in OLD.rglob("*") if f.is_file() and "__pycache__" not in f.parts and "runtime" not in f.relative_to(OLD).parts}
    (out / "H76_INPUT_SEAL.json").write_text(json.dumps({"files": h76_files}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    command = [sys.executable, "-B", str(ROOT.parent / "localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py"), "--repo", str(ROOT), "--current", "CURRENT.md"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True)
    (out / "old_workflow.stdout.log").write_bytes(completed.stdout)
    (out / "old_workflow.stderr.log").write_bytes(completed.stderr)
    (out / "workspace_status.txt").write_bytes(subprocess.check_output(["git", "-c", "core.quotepath=false", "status", "--short"], cwd=ROOT))
    (out / "workspace.diff").write_bytes(subprocess.check_output(["git", "diff", "--no-ext-diff"], cwd=ROOT))
    summary = {"schema": "h77-evaluator-preparation/v1", "at_utc": datetime.now(timezone.utc).isoformat(), "baseline_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "protected_files": len(baseline["protected"]), "protected_drift": drift, "frozen_drift": frozen_drift, "indexed_files_verified": len(index), "historical_crypto": result, "historical_wsl_runs": runs, "h76_input_files": len(h76_files), "workflow_exit_code": completed.returncode, "historical_governance": aliases, "formal_h76_l2": "NOT_RUN", "independent_live_l3": "NOT_RUN", "public_audit_is_fresh_issuance": False, "historical_retry_deviation": "WSL supplement says initial+one repair; three RESULT records observed. Owner quote does not set a numerical ceiling. Do not retroactively accept the supplement.", "provenance_limits": ["archive digest alone does not bind cached extracted executables", "old parent/entry provenance includes log fallback and self-reported flags", "old matching/nonmatching PID and kernel UID observations incomplete", "WSL_VERIFY.py rewrites source output; was not invoked", "Docker-only isolation and dependency lock not satisfied by native WSL"]}
    (out / "ASSESSMENT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("protected_files", "indexed_files_verified", "h76_input_files", "workflow_exit_code", "formal_h76_l2", "independent_live_l3")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
