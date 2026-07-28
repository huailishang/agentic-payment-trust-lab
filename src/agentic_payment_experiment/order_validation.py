from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from .models import (
    Decision,
    EvidenceRef,
    IntentMandate,
    Order,
    OrderDifference,
    OrderItem,
    TransactionRequest,
    ValidationIssue,
)
from .trusted_execution import canonical_hash, verify_binding


ORDER_RULE_VERSION = "order-change-rules-v0.3"
ORDER_LIMITATIONS = (
    "simulation_only",
    "not_a_production_payment_authorization",
    "binding_fact_does_not_define_payment_decision",
    "order_change_v0.3_does_not_verify_signatures_or_payee_identity",
)
MISSING = "<missing>"


@dataclass(frozen=True)
class OrderValidationOutcome:
    decision: Decision | None
    issues: tuple[ValidationIssue, ...]
    evidence: tuple[EvidenceRef, ...]
    differences: tuple[OrderDifference, ...]
    rule_version: str = ORDER_RULE_VERSION
    limitations: tuple[str, ...] = ORDER_LIMITATIONS


def validate_order(
    mandate: IntentMandate,
    request: TransactionRequest,
    authorized_order: Order | None,
    final_order: Order | None,
) -> OrderValidationOutcome | None:
    """Compare two protocol-neutral order snapshots in deterministic stages.

    No snapshots means the caller is running a pre-S09 scenario. Once either
    snapshot is supplied, this function owns order-specific decisions and
    returns the v0.2 machine contract.
    """

    if authorized_order is None and final_order is None:
        return None
    if authorized_order is None or final_order is None:
        missing_path = "authorized_order" if authorized_order is None else "final_order"
        return _outcome(
            Decision.INDETERMINATE,
            (ValidationIssue("order_snapshot_missing", "both order snapshots are required"),),
            (EvidenceRef("order_snapshot_missing", missing_path, MISSING, "order snapshot"),),
        )

    authorized_digest = canonical_hash(authorized_order)
    binding = verify_binding(authorized_digest, final_order)
    refs = (
        EvidenceRef(
            "authorized_order_ref",
            "authorized_order.order_version",
            authorized_order.order_version,
            authorized_order.order_id,
        ),
        EvidenceRef(
            "final_order_ref",
            "final_order.order_version",
            final_order.order_version,
            final_order.order_id,
        ),
        EvidenceRef(
            "authorized_order_digest",
            "trusted_execution.expected_digest",
            authorized_digest,
        ),
        EvidenceRef(
            "final_order_digest",
            "trusted_execution.actual_digest",
            binding.actual_digest or MISSING,
            authorized_digest,
        ),
        EvidenceRef(
            "order_binding_status",
            "trusted_execution.binding_status",
            binding.status.value,
            "VALID",
        ),
        EvidenceRef(
            "order_binding_reason",
            "trusted_execution.binding_reason",
            binding.reason_code,
        ),
    )

    comparability = _comparability_problems(mandate, request, authorized_order, final_order)
    if comparability:
        return _outcome_from_problems(Decision.INDETERMINATE, comparability, refs)

    structural = _structural_problems(authorized_order, final_order)
    if structural:
        return _outcome_from_problems(Decision.INDETERMINATE, structural, refs)

    differences = _find_differences(request, authorized_order, final_order)
    hard_boundary = _category_problems(mandate, final_order)
    if hard_boundary:
        return _outcome_from_problems(
            Decision.DENY,
            hard_boundary,
            refs,
            differences=tuple(differences),
        )

    if differences:
        issues = _issues_for_differences(differences)
        difference_evidence = tuple(
            EvidenceRef(item.code, item.field_path, item.after, item.before)
            for item in differences
        )
        return _outcome(
            Decision.CONFIRMATION_REQUIRED,
            issues,
            refs + difference_evidence,
            tuple(differences),
        )

    return _outcome(None, (), refs)


def _comparability_problems(
    mandate: IntentMandate,
    request: TransactionRequest,
    authorized: Order,
    final: Order,
) -> list[tuple[str, str, str, str, str]]:
    checks = (
        (
            "order_id_mismatch",
            "final_order.order_id",
            final.order_id,
            authorized.order_id,
            "order snapshots do not identify the same order",
        ),
        (
            "authorized_order_mandate_mismatch",
            "authorized_order.mandate_ref",
            authorized.mandate_ref,
            mandate.mandate_id,
            "authorized order is not bound to the mandate",
        ),
        (
            "order_mandate_mismatch",
            "final_order.mandate_ref",
            final.mandate_ref,
            mandate.mandate_id,
            "final order is not bound to the mandate",
        ),
        (
            "authorized_order_merchant_mismatch",
            "authorized_order.merchant",
            authorized.merchant,
            final.merchant,
            "order snapshots identify different merchants",
        ),
        (
            "authorized_order_currency_mismatch",
            "authorized_order.currency",
            authorized.currency,
            final.currency,
            "order snapshots use different currencies",
        ),
        (
            "order_request_amount_mismatch",
            "request.amount",
            request.amount,
            final.total_amount,
            "payment request amount does not match the final order",
        ),
        (
            "order_request_currency_mismatch",
            "request.currency",
            request.currency,
            final.currency,
            "payment request currency does not match the final order",
        ),
        (
            "order_request_merchant_mismatch",
            "request.merchant",
            request.merchant,
            final.merchant,
            "payment request merchant does not match the final order",
        ),
    )
    return [
        (code, path, str(observed), str(expected), message)
        for code, path, observed, expected, message in checks
        if observed != expected
    ]


def _structural_problems(
    authorized: Order,
    final: Order,
) -> list[tuple[str, str, str, str, str]]:
    problems: list[tuple[str, str, str, str, str]] = []
    if authorized.payee != final.payee:
        problems.append(
            (
                "order_payee_changed",
                "final_order.payee",
                final.payee,
                authorized.payee,
                "the payee changed and its identity cannot be verified locally",
            )
        )
    for snapshot_name, order in (("authorized_order", authorized), ("final_order", final)):
        counts = Counter(item.item_id for item in order.items)
        for item_id in sorted(item_id for item_id, count in counts.items() if count > 1):
            problems.append(
                (
                    "duplicate_order_item_id",
                    _item_path(snapshot_name, item_id),
                    item_id,
                    "unique item_id",
                    "duplicate item_id makes order comparison ambiguous",
                )
            )
    return problems


def _category_problems(
    mandate: IntentMandate,
    final: Order,
) -> list[tuple[str, str, str, str, str]]:
    if not mandate.allowed_categories:
        return []
    expected = ", ".join(sorted(mandate.allowed_categories))
    return [
        (
            "order_item_category_out_of_scope",
            f"{_item_path('final_order', item.item_id)}.category",
            item.category,
            expected,
            "final order item category is outside the mandate",
        )
        for item in sorted(final.items, key=lambda value: value.item_id)
        if item.category not in mandate.allowed_categories
    ]


def _find_differences(
    request: TransactionRequest,
    authorized: Order,
    final: Order,
) -> list[OrderDifference]:
    differences: list[OrderDifference] = []
    if authorized.total_amount != final.total_amount:
        differences.append(
            _difference(
                "order_total_changed",
                "final_order.total_amount",
                authorized.total_amount,
                final.total_amount,
            )
        )

    authorized_items = {item.item_id: item for item in authorized.items}
    final_items = {item.item_id: item for item in final.items}
    for item_id in sorted(set(authorized_items) | set(final_items)):
        before_item = authorized_items.get(item_id)
        after_item = final_items.get(item_id)
        if before_item is None:
            path = _item_path("final_order", item_id)
            differences.append(_difference("order_items_changed", path, MISSING, item_id))
            if after_item is not None and after_item.kind != "product":
                differences.append(_difference("unauthorized_addon_added", f"{path}.kind", MISSING, after_item.kind))
            continue
        if after_item is None:
            differences.append(
                _difference(
                    "order_items_changed",
                    _item_path("final_order", item_id),
                    item_id,
                    MISSING,
                )
            )
            continue
        differences.extend(_item_differences(item_id, before_item, after_item))

    if authorized.service_id != final.service_id:
        differences.append(
            _difference(
                "order_service_changed",
                "final_order.service_id",
                _optional_text(authorized.service_id),
                _optional_text(final.service_id),
            )
        )
    if authorized.fulfilment_terms != final.fulfilment_terms:
        differences.append(
            _difference(
                "order_fulfilment_terms_changed",
                "final_order.fulfilment_terms",
                authorized.fulfilment_terms,
                final.fulfilment_terms,
            )
        )
    if request.occurred_at > final.quote_expires_at:
        differences.append(
            _difference(
                "order_quote_expired",
                "request.occurred_at",
                final.quote_expires_at.isoformat(),
                request.occurred_at.isoformat(),
            )
        )
    return differences


def _item_differences(
    item_id: str,
    before: OrderItem,
    after: OrderItem,
) -> list[OrderDifference]:
    path = _item_path("final_order", item_id)
    fields = (
        ("order_item_name_changed", "name", before.name.strip(), after.name.strip()),
        ("order_item_category_changed", "category", before.category, after.category),
        ("order_item_quantity_changed", "quantity", before.quantity, after.quantity),
        ("order_item_unit_amount_changed", "unit_amount", before.unit_amount, after.unit_amount),
        ("order_item_kind_changed", "kind", before.kind, after.kind),
    )
    return [
        _difference(code, f"{path}.{field}", old, new)
        for code, field, old, new in fields
        if old != new
    ]


def _issues_for_differences(
    differences: list[OrderDifference],
) -> tuple[ValidationIssue, ...]:
    messages = {
        "order_total_changed": "final order total differs from the authorized order",
        "order_items_changed": "the order item set changed",
        "unauthorized_addon_added": "a new non-product add-on was added",
        "order_item_name_changed": "an item name changed",
        "order_item_category_changed": "an item category changed",
        "order_item_quantity_changed": "an item quantity changed",
        "order_item_unit_amount_changed": "an item unit amount changed",
        "order_item_kind_changed": "an item kind changed",
        "order_service_changed": "the order service changed",
        "order_fulfilment_terms_changed": "the fulfilment terms changed",
        "order_quote_expired": "the final order quote expired before the request",
    }
    seen: set[str] = set()
    issues: list[ValidationIssue] = []
    for item in differences:
        if item.code not in seen:
            issues.append(ValidationIssue(item.code, messages[item.code]))
            seen.add(item.code)
    return tuple(issues)


def _outcome_from_problems(
    decision: Decision,
    problems: list[tuple[str, str, str, str, str]],
    prefix_evidence: tuple[EvidenceRef, ...],
    *,
    differences: tuple[OrderDifference, ...] = (),
) -> OrderValidationOutcome:
    issues: list[ValidationIssue] = []
    seen_codes: set[str] = set()
    evidence = list(prefix_evidence)
    for code, path, observed, expected, message in problems:
        if code not in seen_codes:
            issues.append(ValidationIssue(code, message))
            seen_codes.add(code)
        evidence.append(EvidenceRef(code, path, observed, expected))
    return _outcome(decision, tuple(issues), tuple(evidence), differences)


def _outcome(
    decision: Decision | None,
    issues: tuple[ValidationIssue, ...],
    evidence: tuple[EvidenceRef, ...],
    differences: tuple[OrderDifference, ...] = (),
) -> OrderValidationOutcome:
    return OrderValidationOutcome(decision, issues, evidence, differences)


def _item_path(snapshot_name: str, item_id: str) -> str:
    return f"{snapshot_name}.items[item_id={item_id}]"


def _optional_text(value: str | None) -> str:
    return value if value is not None else MISSING


def _difference(code: str, path: str, before: object, after: object) -> OrderDifference:
    return OrderDifference(code, path, _stable_text(before), _stable_text(after))


def _stable_text(value: object) -> str:
    if value is None:
        return MISSING
    if isinstance(value, Decimal):
        return str(value)
    return str(value)
