import base64
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sys
import unittest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agentic_payment_experiment.models import AgentIdentity
from agentic_payment_experiment.trusted_execution import (
    IdentityAssuranceLevel,
    VerificationStatus,
    verify_agent_executor_identity,
    verify_x509_svid_credential_possession,
)


ROOT = Path(__file__).resolve().parents[2]
VECTOR_PATH = ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1/evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json"


class CredentialPossessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vector = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))

    def frozen_verify(self, **overrides):
        vector = self.vector
        challenge = vector["challenge"]
        values = {
            "leaf_svid_pem": vector["leaf_svid_pem"],
            "trusted_ca_pem": vector["trusted_ca_pem"],
            "expected_trust_domain": vector["trust_domain"],
            "expected_agent_ref": vector["expected_agent_ref"],
            "expected_executor_instance_ref": vector["expected_executor_instance_ref"],
            "credential_ref": vector["credential_ref"],
            "challenge_payload": base64.b64decode(challenge["payload_b64"]),
            "challenge_signature": base64.b64decode(challenge["signature_b64"]),
            "nonce_ref": challenge["nonce_ref"],
            "issued_at_epoch": challenge["issued_at_epoch"],
            "observed_at_epoch": challenge["observed_at_epoch"],
            "max_age_seconds": challenge["max_age_seconds"],
            "consumed_nonce_refs": (),
        }
        values.update(overrides)
        return verify_x509_svid_credential_possession(**values)

    def test_frozen_valid_vector_verifies_all_four_conditions(self) -> None:
        fact = self.frozen_verify()
        self.assertEqual(VerificationStatus.VALID, fact.status)
        self.assertEqual(("credential_possession_verified",), fact.reason_codes)
        self.assertTrue(fact.credential_valid)
        self.assertTrue(fact.subject_binding_valid)
        self.assertTrue(fact.proof_of_possession_valid)
        self.assertTrue(fact.freshness_valid)
        self.assertFalse(fact.replay_detected)
        self.assertEqual(self.vector["leaf_sha256"], fact.leaf_certificate_sha256)

    def test_frozen_negative_families_fail_closed(self) -> None:
        signature = base64.b64decode(self.vector["challenge"]["signature_b64"])
        cases = (
            (
                "wrong trust",
                {"trusted_ca_pem": self.vector["untrusted_ca_pem"]},
                VerificationStatus.INVALID,
                "credential_trust_invalid",
            ),
            (
                "wrong subject",
                {"expected_executor_instance_ref": "executor-other"},
                VerificationStatus.INVALID,
                "credential_subject_binding_mismatch",
            ),
            (
                "missing proof",
                {"challenge_signature": None},
                VerificationStatus.MISSING_EVIDENCE,
                "credential_possession_proof_missing",
            ),
            (
                "bad proof",
                {"challenge_signature": signature[:-1] + bytes([signature[-1] ^ 1])},
                VerificationStatus.INVALID,
                "credential_possession_signature_invalid",
            ),
            (
                "replay",
                {"consumed_nonce_refs": {self.vector["challenge"]["nonce_ref"]}},
                VerificationStatus.INVALID,
                "credential_possession_replay_detected",
            ),
            (
                "stale",
                {
                    "observed_at_epoch": self.vector["challenge"]["issued_at_epoch"]
                    + self.vector["challenge"]["max_age_seconds"]
                    + 1
                },
                VerificationStatus.INVALID,
                "credential_possession_challenge_stale",
            ),
            (
                "negative age",
                {
                    "observed_at_epoch": self.vector["challenge"]["issued_at_epoch"] - 1
                },
                VerificationStatus.INVALID,
                "credential_possession_challenge_time_invalid",
            ),
        )
        for label, overrides, expected_status, expected_reason in cases:
            with self.subTest(label=label):
                fact = self.frozen_verify(**overrides)
                self.assertEqual(expected_status, fact.status)
                self.assertIn(expected_reason, fact.reason_codes)

    def test_malformed_certificate_fails_closed(self) -> None:
        fact = self.frozen_verify(leaf_svid_pem="not a certificate")
        self.assertEqual(VerificationStatus.INVALID, fact.status)
        self.assertEqual(("credential_certificate_malformed",), fact.reason_codes)

    def test_structural_svid_profile_rejects_bad_san_ca_keyusage_and_time(self) -> None:
        observed = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
        observed_epoch = int(observed.timestamp())
        base_uri = "spiffe://agentic-payment.test/agent/agent-1/executor/executor-1"
        structural_cases = (
            ("no uri san", [], False, True, False, False, -60, 3600),
            (
                "multiple uri san",
                [base_uri, "spiffe://agentic-payment.test/agent/agent-2/executor/executor-2"],
                False,
                True,
                False,
                False,
                -60,
                3600,
            ),
            ("non spiffe", ["https://example.test/agent-1"], False, True, False, False, -60, 3600),
            (
                "wrong trust domain",
                ["spiffe://other.test/agent/agent-1/executor/executor-1"],
                False,
                True,
                False,
                False,
                -60,
                3600,
            ),
            ("leaf ca", [base_uri], True, True, False, False, -60, 3600),
            ("no digital signature", [base_uri], False, False, False, False, -60, 3600),
            ("key cert sign", [base_uri], False, True, True, False, -60, 3600),
            ("crl sign", [base_uri], False, True, False, True, -60, 3600),
            ("not yet valid", [base_uri], False, True, False, False, 60, 3600),
            ("expired", [base_uri], False, True, False, False, -3600, -60),
        )
        for (
            label,
            uris,
            leaf_ca,
            digital_signature,
            key_cert_sign,
            crl_sign,
            leaf_not_before_offset,
            leaf_not_after_offset,
        ) in structural_cases:
            with self.subTest(label=label):
                material = self._make_material(
                    observed=observed,
                    uris=uris,
                    leaf_ca=leaf_ca,
                    digital_signature=digital_signature,
                    key_cert_sign=key_cert_sign,
                    crl_sign=crl_sign,
                    leaf_not_before_offset=leaf_not_before_offset,
                    leaf_not_after_offset=leaf_not_after_offset,
                )
                fact = verify_x509_svid_credential_possession(
                    leaf_svid_pem=material["leaf_pem"],
                    trusted_ca_pem=material["root_pem"],
                    expected_trust_domain="agentic-payment.test",
                    expected_agent_ref="agent-1",
                    expected_executor_instance_ref="executor-1",
                    credential_ref="credential-1",
                    challenge_payload=material["payload"],
                    challenge_signature=material["signature"],
                    nonce_ref="nonce-1",
                    issued_at_epoch=observed_epoch - 10,
                    observed_at_epoch=observed_epoch,
                    max_age_seconds=300,
                    consumed_nonce_refs=(),
                )
                self.assertNotEqual(VerificationStatus.VALID, fact.status)
                self.assertFalse(fact.credential_valid)

    def test_valid_credential_promotes_only_valid_bound_base(self) -> None:
        credential_fact = self.frozen_verify()
        identity = AgentIdentity(
            agent_id="agent-1",
            provider="offline-provider-1",
            executor_instance_id="executor-1",
            status="active",
            credential_ref=self.vector["credential_ref"],
        )
        verified = verify_agent_executor_identity(
            authorized_agent_ref="agent-1",
            request_agent_ref="agent-1",
            execution_agent_ref="agent-1",
            identity=identity,
            current_provider_ref="offline-provider-1",
            current_executor_instance_ref="executor-1",
            current_credential_ref=self.vector["credential_ref"],
            credential_possession_fact=credential_fact,
        )
        self.assertEqual(VerificationStatus.VALID, verified.status)
        self.assertEqual(IdentityAssuranceLevel.VERIFIED, verified.assurance_level)

        invalid_base = verify_agent_executor_identity(
            authorized_agent_ref="agent-1",
            request_agent_ref="agent-other",
            execution_agent_ref="agent-1",
            identity=identity,
            current_provider_ref="offline-provider-1",
            current_executor_instance_ref="executor-1",
            current_credential_ref=self.vector["credential_ref"],
            credential_possession_fact=credential_fact,
        )
        self.assertEqual(VerificationStatus.INVALID, invalid_base.status)
        self.assertEqual(IdentityAssuranceLevel.DECLARED, invalid_base.assurance_level)

    @staticmethod
    def _make_material(
        *,
        observed: datetime,
        uris: list[str],
        leaf_ca: bool,
        digital_signature: bool,
        key_cert_sign: bool,
        crl_sign: bool,
        leaf_not_before_offset: int,
        leaf_not_after_offset: int,
    ) -> dict:
        root_key = ec.generate_private_key(ec.SECP256R1())
        root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test root")])
        root = (
            x509.CertificateBuilder()
            .subject_name(root_name)
            .issuer_name(root_name)
            .public_key(root_key.public_key())
            .serial_number(1)
            .not_valid_before(observed - timedelta(days=1))
            .not_valid_after(observed + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .sign(root_key, hashes.SHA256())
        )

        leaf_key = ec.generate_private_key(ec.SECP256R1())
        builder = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "leaf")]))
            .issuer_name(root_name)
            .public_key(leaf_key.public_key())
            .serial_number(2)
            .not_valid_before(observed + timedelta(seconds=leaf_not_before_offset))
            .not_valid_after(observed + timedelta(seconds=leaf_not_after_offset))
            .add_extension(x509.BasicConstraints(ca=leaf_ca, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=digital_signature,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=key_cert_sign,
                    crl_sign=crl_sign,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        )
        general_names = [x509.UniformResourceIdentifier(uri) for uri in uris]
        if general_names:
            builder = builder.add_extension(x509.SubjectAlternativeName(general_names), critical=False)
        leaf = builder.sign(root_key, hashes.SHA256())
        payload = b"credential-possession-test"
        signature = leaf_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        return {
            "root_pem": root.public_bytes(serialization.Encoding.PEM),
            "leaf_pem": leaf.public_bytes(serialization.Encoding.PEM),
            "payload": payload,
            "signature": signature,
        }


if __name__ == "__main__":
    unittest.main()
