from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Any, Mapping

from ..models import IntentMandate, TransactionRequest
from ..trusted_execution import VerificationStatus
from .ap2 import adapt_ap2_snapshot

AP2_V020_OPEN_PAYMENT_VCT = "mandate.payment.open.1"
AP2_V020_PAYMENT_VCT = "mandate.payment.1"
AP2_V020_CHECKOUT_VCT = "mandate.checkout.1"
AP2_V020_CHECKOUT_HASH_ALGORITHM = "sha-256"


@dataclass(frozen=True)
class AP2VerifiedAdaptation:
    """Result of the bounded AP2 v0.2.0 protocol-boundary gate."""

    boundary_status: VerificationStatus
    reason_codes: tuple[str, ...]
    verified_checkout_hash: str | None
    mandate: IntentMandate | None
    request: TransactionRequest | None
    missing_fields: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return (
            self.boundary_status is VerificationStatus.VALID
            and self.mandate is not None
            and self.request is not None
        )


def adapt_verified_ap2_v020_snapshot(
    snapshot: Mapping[str, Any],
) -> AP2VerifiedAdaptation:
    """Verify the frozen AP2 v0.2.0 boundary before canonical adaptation.

    This gate intentionally verifies only exact object identities, the default
    sha-256 binding of the raw checkout JWT to checkout_hash, and the closed
    PaymentMandate transaction_id binding to that independently verified hash.
    It does not verify JWT signatures, SD-JWT delegation, holder proof, receipts,
    provider provenance, or AP2 conformance.
    """

    open_payment = _mapping(snapshot.get("open_payment_mandate"))
    payment = _mapping(snapshot.get("payment_mandate"))
    checkout = _mapping(snapshot.get("checkout_mandate"))

    vct_reasons: list[str] = []
    missing_fields: list[str] = []
    _check_vct(
        open_payment,
        "open_payment_mandate.vct",
        AP2_V020_OPEN_PAYMENT_VCT,
        "ap2_open_payment_vct_invalid",
        vct_reasons,
        missing_fields,
    )
    _check_vct(
        payment,
        "payment_mandate.vct",
        AP2_V020_PAYMENT_VCT,
        "ap2_payment_vct_invalid",
        vct_reasons,
        missing_fields,
    )
    _check_vct(
        checkout,
        "checkout_mandate.vct",
        AP2_V020_CHECKOUT_VCT,
        "ap2_checkout_vct_invalid",
        vct_reasons,
        missing_fields,
    )
    if vct_reasons:
        return _blocked(
            VerificationStatus.INVALID,
            tuple(vct_reasons),
            missing_fields=tuple(missing_fields),
        )

    declared_algorithm = checkout.get("_sd_alg")
    if (
        declared_algorithm not in (None, "")
        and str(declared_algorithm) != AP2_V020_CHECKOUT_HASH_ALGORITHM
    ):
        return _blocked(
            VerificationStatus.MISSING_EVIDENCE,
            ("ap2_checkout_hash_algorithm_unsupported",),
        )

    raw_checkout_jwt = checkout.get("checkout_jwt")
    declared_checkout_hash = checkout.get("checkout_hash")
    checkout_missing: list[str] = []
    if raw_checkout_jwt in (None, ""):
        checkout_missing.append("checkout_mandate.checkout_jwt")
    if declared_checkout_hash in (None, ""):
        checkout_missing.append("checkout_mandate.checkout_hash")
    if checkout_missing:
        return _blocked(
            VerificationStatus.MISSING_EVIDENCE,
            ("ap2_checkout_evidence_missing",),
            missing_fields=tuple(checkout_missing),
        )
    if not isinstance(raw_checkout_jwt, str) or not isinstance(
        declared_checkout_hash, str
    ):
        return _blocked(
            VerificationStatus.INVALID,
            ("ap2_checkout_evidence_type_invalid",),
        )

    calculated_checkout_hash = _checkout_hash(raw_checkout_jwt)
    if calculated_checkout_hash != declared_checkout_hash:
        return _blocked(
            VerificationStatus.INVALID,
            ("ap2_checkout_hash_mismatch",),
        )

    transaction_id = payment.get("transaction_id")
    if transaction_id in (None, ""):
        return _blocked(
            VerificationStatus.MISSING_EVIDENCE,
            ("ap2_payment_checkout_binding_missing",),
            verified_checkout_hash=calculated_checkout_hash,
            missing_fields=("payment_mandate.transaction_id",),
        )
    if not isinstance(transaction_id, str):
        return _blocked(
            VerificationStatus.INVALID,
            ("ap2_payment_checkout_binding_type_invalid",),
            verified_checkout_hash=calculated_checkout_hash,
        )
    if transaction_id != calculated_checkout_hash:
        return _blocked(
            VerificationStatus.INVALID,
            ("ap2_payment_checkout_binding_mismatch",),
            verified_checkout_hash=calculated_checkout_hash,
        )

    adapted = adapt_ap2_snapshot(snapshot)
    if not adapted.ready or adapted.mandate is None or adapted.request is None:
        return _blocked(
            VerificationStatus.MISSING_EVIDENCE,
            ("ap2_canonical_mapping_not_ready",),
            verified_checkout_hash=calculated_checkout_hash,
            missing_fields=adapted.missing_fields,
        )

    return AP2VerifiedAdaptation(
        boundary_status=VerificationStatus.VALID,
        reason_codes=("ap2_v020_protocol_boundary_verified",),
        verified_checkout_hash=calculated_checkout_hash,
        mandate=adapted.mandate,
        request=adapted.request,
        missing_fields=(),
    )


def _check_vct(
    obj: Mapping[str, Any],
    path: str,
    expected: str,
    reason_code: str,
    reasons: list[str],
    missing_fields: list[str],
) -> None:
    actual = obj.get("vct")
    if actual in (None, ""):
        missing_fields.append(path)
    if actual != expected:
        reasons.append(reason_code)


def _checkout_hash(raw_checkout_jwt: str) -> str:
    digest = hashlib.sha256(raw_checkout_jwt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _blocked(
    status: VerificationStatus,
    reason_codes: tuple[str, ...],
    *,
    verified_checkout_hash: str | None = None,
    missing_fields: tuple[str, ...] = (),
) -> AP2VerifiedAdaptation:
    return AP2VerifiedAdaptation(
        boundary_status=status,
        reason_codes=reason_codes,
        verified_checkout_hash=verified_checkout_hash,
        mandate=None,
        request=None,
        missing_fields=missing_fields,
    )
