from __future__ import annotations

import sys
from typing import Any, Mapping

from ..trusted_execution import VerificationStatus
from .ap2_protocol_boundary import (
    AP2VerifiedAdaptation,
    adapt_verified_ap2_v020_snapshot,
)

_OPEN_PAYMENT_CLASS = (
    "ap2.sdk.generated.open_payment_mandate",
    "OpenPaymentMandate",
)
_PAYMENT_CLASS = (
    "ap2.sdk.generated.payment_mandate",
    "PaymentMandate",
)
_CHECKOUT_CLASS = (
    "ap2.sdk.generated.checkout_mandate",
    "CheckoutMandate",
)


def adapt_verified_ap2_v020_sdk_objects(
    open_payment_mandate: Any,
    payment_mandate: Any,
    checkout_mandate: Any,
    *,
    experiment_context: Mapping[str, Any],
) -> AP2VerifiedAdaptation:
    """Bridge exact official AP2 generated objects into the existing H-34 gate.

    The SDK remains an optional dependency: this module never imports the AP2
    package or pydantic. Official classes must already be loaded by the caller.
    """

    if not _is_exact_loaded_class(open_payment_mandate, *_OPEN_PAYMENT_CLASS):
        return _blocked(
            VerificationStatus.INVALID,
            "ap2_sdk_open_payment_object_invalid",
        )
    if not _is_exact_loaded_class(payment_mandate, *_PAYMENT_CLASS):
        return _blocked(
            VerificationStatus.INVALID,
            "ap2_sdk_payment_object_invalid",
        )
    if not _is_exact_loaded_class(checkout_mandate, *_CHECKOUT_CLASS):
        return _blocked(
            VerificationStatus.INVALID,
            "ap2_sdk_checkout_object_invalid",
        )
    if not isinstance(experiment_context, Mapping):
        return _blocked(
            VerificationStatus.MISSING_EVIDENCE,
            "ap2_sdk_experiment_context_invalid",
            missing_fields=("experiment_context",),
        )

    try:
        open_snapshot = _model_dump(open_payment_mandate)
        payment_snapshot = _model_dump(payment_mandate)
        checkout_snapshot = _model_dump(checkout_mandate)
    except Exception:
        return _blocked(
            VerificationStatus.INVALID,
            "ap2_sdk_model_dump_invalid",
        )

    if not all(
        isinstance(item, Mapping)
        for item in (open_snapshot, payment_snapshot, checkout_snapshot)
    ):
        return _blocked(
            VerificationStatus.INVALID,
            "ap2_sdk_model_dump_invalid",
        )

    snapshot = {
        "protocol_version": "AP2-v0.2.0-official-sdk-bridge",
        "open_payment_mandate": open_snapshot,
        "payment_mandate": payment_snapshot,
        "checkout_mandate": checkout_snapshot,
        "experiment_context": experiment_context,
    }
    return adapt_verified_ap2_v020_snapshot(snapshot)


def _is_exact_loaded_class(value: Any, module_name: str, class_name: str) -> bool:
    cls = type(value)
    if cls.__module__ != module_name or cls.__name__ != class_name:
        return False
    module = sys.modules.get(module_name)
    return module is not None and getattr(module, class_name, None) is cls


def _model_dump(value: Any) -> Mapping[str, Any]:
    dump = getattr(value, "model_dump", None)
    if not callable(dump):
        raise TypeError("official generated object does not expose model_dump")
    result = dump(mode="python", exclude_none=True)
    if not isinstance(result, Mapping):
        raise TypeError("model_dump result is not a mapping")
    return result


def _blocked(
    status: VerificationStatus,
    reason_code: str,
    *,
    missing_fields: tuple[str, ...] = (),
) -> AP2VerifiedAdaptation:
    return AP2VerifiedAdaptation(
        boundary_status=status,
        reason_codes=(reason_code,),
        verified_checkout_hash=None,
        mandate=None,
        request=None,
        missing_fields=missing_fields,
    )
