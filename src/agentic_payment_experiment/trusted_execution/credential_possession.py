"""Protocol-neutral X.509-SVID credential and proof-of-possession verification.

This module intentionally implements only a bounded offline profile: one trusted
synthetic root directly signs one leaf SVID. It does not perform generic RFC
5280 path building, revocation checking, federation, or production identity
proofing.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from urllib.parse import urlparse

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from .execution_facts import VerificationStatus


X509_SVID_FORMAT = "X509-SVID"


@dataclass(frozen=True)
class CredentialPossessionVerificationFact:
    """Replayable evidence for one bounded credential-possession verification."""

    status: VerificationStatus
    reason_codes: tuple[str, ...]
    credential_format: str
    credential_ref: str | None
    subject_ref: str | None
    trust_domain_ref: str | None
    leaf_certificate_sha256: str | None
    credential_valid: bool
    subject_binding_valid: bool
    proof_of_possession_valid: bool
    freshness_valid: bool
    replay_detected: bool
    nonce_ref: str | None
    challenge_payload_sha256: str | None
    issued_at_epoch: int | None
    observed_at_epoch: int | None
    max_age_seconds: int


def verify_x509_svid_credential_possession(
    *,
    leaf_svid_pem: str | bytes | None,
    trusted_ca_pem: str | bytes | None,
    expected_trust_domain: str,
    expected_agent_ref: str,
    expected_executor_instance_ref: str,
    credential_ref: str | None,
    challenge_payload: bytes | None,
    challenge_signature: bytes | None,
    nonce_ref: str | None,
    issued_at_epoch: int | None,
    observed_at_epoch: int | None,
    max_age_seconds: int,
    consumed_nonce_refs: Collection[str] = (),
) -> CredentialPossessionVerificationFact:
    """Verify the frozen direct-root X.509-SVID possession profile.

    The credential is accepted only when the leaf is directly signed by the
    supplied trusted root, is valid at ``observed_at_epoch``, has exactly one
    SPIFFE URI SAN matching the expected Agent/Executor path, satisfies the leaf
    BasicConstraints/KeyUsage profile, verifies the challenge signature with the
    leaf public key, and passes freshness/replay checks.
    """

    if max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")

    leaf_digest = _pem_digest(leaf_svid_pem)
    payload_digest = (
        hashlib.sha256(challenge_payload).hexdigest()
        if isinstance(challenge_payload, bytes)
        else None
    )
    common = {
        "credential_ref": _optional_ref(credential_ref),
        "nonce_ref": _optional_ref(nonce_ref),
        "challenge_payload_sha256": payload_digest,
        "issued_at_epoch": issued_at_epoch,
        "observed_at_epoch": observed_at_epoch,
        "max_age_seconds": max_age_seconds,
        "leaf_certificate_sha256": leaf_digest,
    }

    missing_reasons: list[str] = []
    if leaf_svid_pem is None or leaf_svid_pem == b"" or leaf_svid_pem == "":
        missing_reasons.append("credential_certificate_missing")
    if trusted_ca_pem is None or trusted_ca_pem == b"" or trusted_ca_pem == "":
        missing_reasons.append("credential_trust_bundle_missing")
    if not _normalized_ref(credential_ref):
        missing_reasons.append("credential_ref_missing")
    if challenge_payload is None:
        missing_reasons.append("credential_possession_challenge_missing")
    if challenge_signature is None or challenge_signature == b"":
        missing_reasons.append("credential_possession_proof_missing")
    if not _normalized_ref(nonce_ref):
        missing_reasons.append("credential_possession_nonce_missing")
    if issued_at_epoch is None or observed_at_epoch is None:
        missing_reasons.append("credential_possession_timestamp_missing")
    if missing_reasons:
        return _fact(
            status=VerificationStatus.MISSING_EVIDENCE,
            reason_codes=tuple(missing_reasons),
            subject_ref=None,
            trust_domain_ref=None,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=False,
            replay_detected=False,
            **common,
        )

    leaf = _load_certificate(leaf_svid_pem)
    if leaf is None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_certificate_malformed",),
            subject_ref=None,
            trust_domain_ref=None,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=False,
            replay_detected=False,
            **common,
        )
    common["leaf_certificate_sha256"] = leaf.fingerprint(hashes.SHA256()).hex()
    trusted_ca = _load_certificate(trusted_ca_pem)
    if trusted_ca is None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_trust_invalid",),
            subject_ref=None,
            trust_domain_ref=None,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=False,
            replay_detected=False,
            **common,
        )

    observed_at = datetime.fromtimestamp(observed_at_epoch, tz=UTC)
    trust_valid = _trusted_root_profile_valid(trusted_ca, observed_at) and _direct_leaf_signature_valid(
        leaf, trusted_ca
    )
    if not trust_valid:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_trust_invalid",),
            subject_ref=None,
            trust_domain_ref=None,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    leaf_profile_reason = _leaf_profile_failure_reason(leaf, observed_at)
    if leaf_profile_reason is not None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=(leaf_profile_reason,),
            subject_ref=None,
            trust_domain_ref=None,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    spiffe_id, trust_domain = _single_spiffe_uri(leaf)
    if spiffe_id is None or trust_domain is None:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_spiffe_san_invalid",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    credential_valid = trust_domain == expected_trust_domain
    if not credential_valid:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_trust_domain_mismatch",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=False,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    expected_spiffe_id = (
        f"spiffe://{expected_trust_domain}/agent/{expected_agent_ref}"
        f"/executor/{expected_executor_instance_ref}"
    )
    subject_binding_valid = spiffe_id == expected_spiffe_id
    if not subject_binding_valid:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_subject_binding_mismatch",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=True,
            subject_binding_valid=False,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    proof_valid = _possession_signature_valid(
        leaf,
        challenge_payload,
        challenge_signature,
    )
    if not proof_valid:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_possession_signature_invalid",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=True,
            subject_binding_valid=True,
            proof_of_possession_valid=False,
            freshness_valid=_freshness_valid(issued_at_epoch, observed_at_epoch, max_age_seconds),
            replay_detected=_normalized_ref(nonce_ref) in set(consumed_nonce_refs),
            **common,
        )

    age = observed_at_epoch - issued_at_epoch
    if age < 0:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_possession_challenge_time_invalid",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=True,
            subject_binding_valid=True,
            proof_of_possession_valid=True,
            freshness_valid=False,
            replay_detected=False,
            **common,
        )
    if age > max_age_seconds:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_possession_challenge_stale",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=True,
            subject_binding_valid=True,
            proof_of_possession_valid=True,
            freshness_valid=False,
            replay_detected=False,
            **common,
        )

    replay_detected = _normalized_ref(nonce_ref) in {
        _normalized_ref(value) for value in consumed_nonce_refs
    }
    if replay_detected:
        return _fact(
            status=VerificationStatus.INVALID,
            reason_codes=("credential_possession_replay_detected",),
            subject_ref=spiffe_id,
            trust_domain_ref=trust_domain,
            credential_valid=True,
            subject_binding_valid=True,
            proof_of_possession_valid=True,
            freshness_valid=True,
            replay_detected=True,
            **common,
        )

    return _fact(
        status=VerificationStatus.VALID,
        reason_codes=("credential_possession_verified",),
        subject_ref=spiffe_id,
        trust_domain_ref=trust_domain,
        credential_valid=True,
        subject_binding_valid=True,
        proof_of_possession_valid=True,
        freshness_valid=True,
        replay_detected=False,
        **common,
    )


def _fact(
    *,
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    credential_ref: str | None,
    subject_ref: str | None,
    trust_domain_ref: str | None,
    leaf_certificate_sha256: str | None,
    credential_valid: bool,
    subject_binding_valid: bool,
    proof_of_possession_valid: bool,
    freshness_valid: bool,
    replay_detected: bool,
    nonce_ref: str | None,
    challenge_payload_sha256: str | None,
    issued_at_epoch: int | None,
    observed_at_epoch: int | None,
    max_age_seconds: int,
) -> CredentialPossessionVerificationFact:
    return CredentialPossessionVerificationFact(
        status=status,
        reason_codes=reason_codes,
        credential_format=X509_SVID_FORMAT,
        credential_ref=credential_ref,
        subject_ref=subject_ref,
        trust_domain_ref=trust_domain_ref,
        leaf_certificate_sha256=leaf_certificate_sha256,
        credential_valid=credential_valid,
        subject_binding_valid=subject_binding_valid,
        proof_of_possession_valid=proof_of_possession_valid,
        freshness_valid=freshness_valid,
        replay_detected=replay_detected,
        nonce_ref=nonce_ref,
        challenge_payload_sha256=challenge_payload_sha256,
        issued_at_epoch=issued_at_epoch,
        observed_at_epoch=observed_at_epoch,
        max_age_seconds=max_age_seconds,
    )


def _load_certificate(pem: str | bytes | None) -> x509.Certificate | None:
    if pem is None:
        return None
    raw = pem.encode("utf-8") if isinstance(pem, str) else pem
    try:
        return x509.load_pem_x509_certificate(raw)
    except (TypeError, ValueError):
        return None


def _pem_digest(pem: str | bytes | None) -> str | None:
    if pem is None:
        return None
    raw = pem.encode("utf-8") if isinstance(pem, str) else pem
    if not raw:
        return None
    return hashlib.sha256(raw).hexdigest()


def _trusted_root_profile_valid(certificate: x509.Certificate, observed_at: datetime) -> bool:
    try:
        constraints = certificate.extensions.get_extension_for_class(
            x509.BasicConstraints
        ).value
    except x509.ExtensionNotFound:
        return False
    if not constraints.ca or not _certificate_valid_at(certificate, observed_at):
        return False
    public_key = certificate.public_key()
    try:
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                certificate.signature,
                certificate.tbs_certificate_bytes,
                ec.ECDSA(certificate.signature_hash_algorithm),
            )
        elif isinstance(public_key, rsa.RSAPublicKey):
            return False
        else:
            return False
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def _direct_leaf_signature_valid(leaf: x509.Certificate, trusted_ca: x509.Certificate) -> bool:
    if leaf.issuer != trusted_ca.subject:
        return False
    public_key = trusted_ca.public_key()
    try:
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                leaf.signature,
                leaf.tbs_certificate_bytes,
                ec.ECDSA(leaf.signature_hash_algorithm),
            )
        else:
            return False
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def _leaf_profile_failure_reason(
    leaf: x509.Certificate,
    observed_at: datetime,
) -> str | None:
    if not _certificate_valid_at(leaf, observed_at):
        return "credential_certificate_time_invalid"
    try:
        constraints = leaf.extensions.get_extension_for_class(x509.BasicConstraints).value
        key_usage = leaf.extensions.get_extension_for_class(x509.KeyUsage).value
    except x509.ExtensionNotFound:
        return "credential_leaf_profile_invalid"
    if constraints.ca:
        return "credential_leaf_profile_invalid"
    if not key_usage.digital_signature or key_usage.key_cert_sign or key_usage.crl_sign:
        return "credential_leaf_profile_invalid"
    return None


def _single_spiffe_uri(leaf: x509.Certificate) -> tuple[str | None, str | None]:
    try:
        san = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        return None, None
    uris = san.get_values_for_type(x509.UniformResourceIdentifier)
    if len(uris) != 1:
        return None, None
    uri = uris[0]
    parsed = urlparse(uri)
    if (
        parsed.scheme != "spiffe"
        or not parsed.netloc
        or parsed.params
        or parsed.query
        or parsed.fragment
        or "@" in parsed.netloc
        or ":" in parsed.netloc
    ):
        return uri, None
    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) != 4 or segments[0] != "agent" or segments[2] != "executor":
        return uri, parsed.netloc
    if not segments[1] or not segments[3]:
        return uri, parsed.netloc
    canonical = f"spiffe://{parsed.netloc}/agent/{segments[1]}/executor/{segments[3]}"
    if uri != canonical:
        return uri, parsed.netloc
    return uri, parsed.netloc


def _possession_signature_valid(
    leaf: x509.Certificate,
    challenge_payload: bytes,
    challenge_signature: bytes,
) -> bool:
    public_key = leaf.public_key()
    try:
        if isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                challenge_signature,
                challenge_payload,
                ec.ECDSA(hashes.SHA256()),
            )
        else:
            return False
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def _certificate_valid_at(certificate: x509.Certificate, observed_at: datetime) -> bool:
    not_before = getattr(certificate, "not_valid_before_utc", None)
    not_after = getattr(certificate, "not_valid_after_utc", None)
    if not_before is None:
        not_before = certificate.not_valid_before.replace(tzinfo=UTC)
    if not_after is None:
        not_after = certificate.not_valid_after.replace(tzinfo=UTC)
    return not_before <= observed_at <= not_after


def _freshness_valid(
    issued_at_epoch: int,
    observed_at_epoch: int,
    max_age_seconds: int,
) -> bool:
    age = observed_at_epoch - issued_at_epoch
    return 0 <= age <= max_age_seconds


def _normalized_ref(value: object | None) -> str:
    return str(value or "").strip()


def _optional_ref(value: object | None) -> str | None:
    normalized = _normalized_ref(value)
    return normalized or None
