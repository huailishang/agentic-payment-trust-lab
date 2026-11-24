"""H85 caller experiment. Offline proofs are synthetic, never live evidence."""
import argparse
from datetime import datetime, timezone, timedelta
import io
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
P9 = TASK.parent / "P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1"
sys.path[:0] = [str(ROOT / "scripts/validation/webshop"), str(ROOT / "src")]
import run_same_journey_responsibility as caller
import action_time_authority as authority
from agentic_payment_experiment import payment_execution


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


def inputs(out):
    parent = read(P9 / "evidence/SAME_JOURNEY_RESULT.json")
    replay, accepted = parent["replay"], parent["accepted_behavior"]
    assert replay["matches_accepted"] and replay["purchase_count"] == 0
    bridge = {
        "accepted_fixture_sha256": accepted["fixture_sha256"],
        "accepted_trace_sha256": accepted["normalized_trace_sha256"],
        "replay_trace_sha256": replay["normalized_trace_sha256"],
        **{k: replay[k] for k in ("goal_index", "seed", "repeat", "repeat_identical")},
        "first_run": {k: replay[k] for k in ("score", "purchase_count")},
        "facts": {k: replay[k] for k in ("session_id", "instruction_text", "actions_executed", "product")},
    }
    original_context = P9 / "evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json"
    context = read(original_context)
    context["authority"]["expected_agent_id"] = "h76-agent"
    context["runtime_identity"].update(provider="h76-provider", executor_instance_id="h76-executor",
                                       credential_ref="h85-experiment-credential")
    mapped = out / "MAPPED_CONTEXT.json"
    save(mapped, context)
    save(out / "BRIDGE.json", bridge)
    return bridge, original_context, mapped


def run_entry(out, name, bridge, context, source=None, baseline=False):
    original = payment_execution.execute_with_payment_binding_gate
    observed = []
    def observe(*args, **kwargs):
        result = original(*args, **kwargs)
        observed.append(result.identity_fact.assurance_level.name)
        return result
    output = out / (name + ".json")
    args = argparse.Namespace(experiment_context=str(context), output=str(output),
                              action_time_source=source, action_time_baseline=baseline)
    with patch("sys.stdin", io.StringIO(json.dumps(bridge))), patch.object(
        payment_execution, "execute_with_payment_binding_gate", side_effect=observe
    ):
        assert caller.integration_phase(args) == 0
    result = read(output)
    assert len(observed) == 1
    assert all(x["equal"] for x in result["correlations"])
    assert not result["execution"]["real_payment_executed"]
    assert result["trace"]["validation_status"] == "VALID"
    gate = result["runtime_gate"]
    row = {"assurance": observed[0], "decision": gate["decision"],
           "callback_count": gate["callback_count"], "trace_validation": result["trace"]["validation_status"]}
    if source is not None:
        row.update(result["action_time_authority"])
        assert row["governed_action_binding"] == "VALID"
    elif baseline:
        row.update(result["action_time_baseline"])
    return row


class OfflineSource:
    trust_domain = "h76.test"

    def __init__(self):
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import NameOID
        now = datetime.now(timezone.utc)
        root_key = ec.generate_private_key(ec.SECP256R1())
        root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "H85 synthetic root")])
        root = (x509.CertificateBuilder().subject_name(root_name).issuer_name(root_name)
                .public_key(root_key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(hours=1)).not_valid_after(now + timedelta(hours=1))
                .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                .sign(root_key, hashes.SHA256()))
        self.key = ec.generate_private_key(ec.SECP256R1())
        leaf = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "H85 synthetic leaf")]))
                .issuer_name(root_name).public_key(self.key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(minutes=5))
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.KeyUsage(True, False, False, False, False, False, False, False, False), critical=True)
                .add_extension(x509.SubjectAlternativeName([x509.UniformResourceIdentifier(
                    "spiffe://h76.test/agent/h76-agent/executor/h76-executor")]), critical=False)
                .sign(root_key, hashes.SHA256()))
        self.root = root.public_bytes(serialization.Encoding.PEM)
        self.leaf = leaf.public_bytes(serialization.Encoding.PEM)
        self.calls = 0

    def observe(self, payload):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec
        self.calls += 1
        return {"status": "ISSUED", "root_pem": self.root, "leaf_pem": self.leaf,
                "signature": self.key.sign(payload, ec.ECDSA(hashes.SHA256())),
                "evidence": {"classification": "SYNTHETIC_OFFLINE", "source_call": self.calls}}


class UnavailableSource:
    trust_domain = "h76.test"
    def observe(self, payload):
        raise OSError("synthetic offline source unavailable")


def offline(out):
    bridge, original, mapped = inputs(out)
    p9 = run_entry(out, "P9_ORIGINAL", bridge, original)
    assert (p9["assurance"], p9["decision"], p9["callback_count"]) == ("BOUND", "ALLOW", 1)
    baseline = run_entry(out, "BASELINE", bridge, mapped, baseline=True)
    source = OfflineSource()
    issued = run_entry(out, "ISSUED", bridge, mapped, source)
    unavailable = run_entry(out, "UNAVAILABLE", bridge, mapped, UnavailableSource())
    verifier = authority.verify_x509_svid_credential_possession
    def delayed(*args, **kwargs):
        result = verifier(*args, **kwargs)
        time.sleep(1.1)
        return result
    with patch.object(authority, "verify_x509_svid_credential_possession", side_effect=delayed):
        mismatch = run_entry(out, "TIME_MISMATCH", bridge, mapped, source)
    rows = {"baseline": baseline, "issued": issued, "unavailable": unavailable, "time_mismatch": mismatch}
    save(out / "OBSERVATIONS.json", rows)
    assert len({v["business_digest"] for v in rows.values()}) == 1
    assert [v["assurance"] for v in rows.values()] == ["BOUND", "VERIFIED", "BOUND", "BOUND"]
    assert unavailable["source_status"] == "UNKNOWN" and mismatch["fact_supplied"] is False
    assert source.calls == 2
    assert all(v["decision"] == "ALLOW" and v["callback_count"] == 1 for v in rows.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("offline", "live"))
    parser.add_argument("--role", required=True, choices=("executor", "evaluator"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.phase == "offline":
        offline(args.out.resolve())
    else:
        sys.path.insert(0, str(TASK / "candidate"))
        from LIVE import live
        live(args.role, args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
