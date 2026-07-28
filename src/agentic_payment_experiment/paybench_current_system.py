from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .models import Decision, IntentMandate, TransactionRequest, ValidationResult
from .paybench_challenges import (
    PayBenchAttempt,
    PayBenchChallenge,
    PayBenchChallengeEvaluation,
    PayBenchChallengeSet,
    evaluate_paybench_attempt,
)
from .validator import validate_request


_SUPPORTED_CATEGORIES = {
    "spend_limits",
    "authorization_scope",
    "consent_escalation",
}


@dataclass(frozen=True)
class CurrentRulesChallengeResult:
    scenario_id: str
    support_status: str
    attempt: PayBenchAttempt | None
    evaluation: PayBenchChallengeEvaluation | None
    reason_codes: tuple[str, ...] = ()
    selected_merchant: str | None = None
    unsupported_reason: str | None = None


@dataclass(frozen=True)
class CurrentRulesPayBenchResult:
    results: tuple[CurrentRulesChallengeResult, ...]
    total: int
    supported: int
    unsupported: int
    supported_passed: int
    supported_failed: int
    unsupported_scenario_ids: tuple[str, ...]


def run_current_rules_on_paybench(
    challenge_set: PayBenchChallengeSet,
) -> CurrentRulesPayBenchResult:
    results = tuple(_run_one(challenge) for challenge in challenge_set.challenges)
    supported_results = tuple(
        result for result in results if result.support_status == "SUPPORTED"
    )
    supported_passed = sum(
        result.evaluation is not None and result.evaluation.evaluation.status == "PASS"
        for result in supported_results
    )
    unsupported_ids = tuple(
        result.scenario_id for result in results if result.support_status == "UNSUPPORTED"
    )
    return CurrentRulesPayBenchResult(
        results=results,
        total=len(results),
        supported=len(supported_results),
        unsupported=len(unsupported_ids),
        supported_passed=supported_passed,
        supported_failed=len(supported_results) - supported_passed,
        unsupported_scenario_ids=unsupported_ids,
    )


def write_current_rules_paybench_report(
    challenge_set: PayBenchChallengeSet,
    result: CurrentRulesPayBenchResult,
    path: Path,
) -> None:
    status = "FAIL" if result.supported_failed else ("PARTIAL" if result.unsupported else "PASS")
    report = {
        "benchmark": challenge_set.name,
        "status": status,
        "mode": "current_protocol_neutral_rules",
        "source": {
            "repository": challenge_set.source_repository,
            "commit": challenge_set.source_commit,
            "license": challenge_set.license,
            "accessed_at": challenge_set.accessed_at,
        },
        "summary": {
            "total": result.total,
            "supported": result.supported,
            "unsupported": result.unsupported,
            "supported_passed": result.supported_passed,
            "supported_failed": result.supported_failed,
        },
        "unsupported_scenario_ids": list(result.unsupported_scenario_ids),
        "results": [
            {
                "scenario_id": item.scenario_id,
                "support_status": item.support_status,
                "decision": item.attempt.decision.value if item.attempt else None,
                "evaluation_status": (
                    item.evaluation.evaluation.status if item.evaluation else None
                ),
                "reason_codes": list(item.reason_codes),
                "selected_merchant": item.selected_merchant,
                "unsupported_reason": item.unsupported_reason,
            }
            for item in result.results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _run_one(challenge: PayBenchChallenge) -> CurrentRulesChallengeResult:
    if challenge.category not in _SUPPORTED_CATEGORIES or challenge.runtime_input is None:
        return CurrentRulesChallengeResult(
            scenario_id=challenge.scenario_id,
            support_status="UNSUPPORTED",
            attempt=None,
            evaluation=None,
            unsupported_reason=(
                "current protocol-neutral validator has no execution fact model "
                f"for category {challenge.category}"
            ),
        )

    if challenge.category == "authorization_scope":
        return _run_authorization_scope(challenge)

    validation = _validate_single_request(challenge)
    attempt = PayBenchAttempt(decision=validation.decision)
    return CurrentRulesChallengeResult(
        scenario_id=challenge.scenario_id,
        support_status="SUPPORTED",
        attempt=attempt,
        evaluation=evaluate_paybench_attempt(challenge, attempt),
        reason_codes=tuple(issue.code for issue in validation.issues),
        selected_merchant=str(challenge.runtime_input["merchant"]),
    )


def _run_authorization_scope(
    challenge: PayBenchChallenge,
) -> CurrentRulesChallengeResult:
    runtime = challenge.runtime_input or {}
    candidates = runtime.get("candidate_offers")
    if not isinstance(candidates, list) or not candidates:
        return CurrentRulesChallengeResult(
            scenario_id=challenge.scenario_id,
            support_status="UNSUPPORTED",
            attempt=None,
            evaluation=None,
            unsupported_reason="authorization challenge has no candidate_offers",
        )

    evaluated: list[tuple[dict[str, object], ValidationResult]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        evaluated.append((candidate, _validate_candidate_offer(challenge, candidate)))
    if not evaluated:
        return CurrentRulesChallengeResult(
            scenario_id=challenge.scenario_id,
            support_status="UNSUPPORTED",
            attempt=None,
            evaluation=None,
            unsupported_reason="authorization challenge has no valid candidate offer",
        )

    selected_candidate, validation = next(
        (
            (candidate, result)
            for candidate, result in evaluated
            if result.decision is Decision.ALLOW
        ),
        evaluated[0],
    )
    attempt = PayBenchAttempt(decision=validation.decision)
    return CurrentRulesChallengeResult(
        scenario_id=challenge.scenario_id,
        support_status="SUPPORTED",
        attempt=attempt,
        evaluation=evaluate_paybench_attempt(challenge, attempt),
        reason_codes=tuple(issue.code for issue in validation.issues),
        selected_merchant=str(selected_candidate["merchant"]),
    )


def _validate_single_request(challenge: PayBenchChallenge) -> ValidationResult:
    runtime = challenge.runtime_input or {}
    amount = Decimal(str(runtime["amount"]))
    merchant = str(runtime["merchant"])
    category = str(runtime["category"])

    if challenge.category == "spend_limits":
        max_amount = Decimal(str(challenge.source_policy["max_total_spend"]))
        confirmation_above = None
        allowed_merchants = frozenset[str]()
    elif challenge.category == "consent_escalation":
        max_amount = Decimal(str(runtime["hard_limit"]))
        confirmation_above = Decimal(str(challenge.source_policy["approval_threshold"]))
        allowed_merchants = frozenset[str]()
    else:
        raise ValueError(f"unsupported single-request category: {challenge.category}")

    mandate, request = _build_payment_input(
        challenge,
        amount=amount,
        merchant=merchant,
        category=category,
        max_amount=max_amount,
        confirmation_above=confirmation_above,
        allowed_merchants=allowed_merchants,
    )
    return validate_request(mandate, request)


def _validate_candidate_offer(
    challenge: PayBenchChallenge,
    candidate: dict[str, object],
) -> ValidationResult:
    runtime = challenge.runtime_input or {}
    amount = Decimal(str(candidate["amount"]))
    merchant = str(candidate["merchant"])
    category = str(runtime["category"])
    allowed_merchants = frozenset(
        str(item) for item in challenge.source_policy.get("allowed_merchants", [])
    )
    mandate, request = _build_payment_input(
        challenge,
        amount=amount,
        merchant=merchant,
        category=category,
        max_amount=Decimal("1000000"),
        confirmation_above=None,
        allowed_merchants=allowed_merchants,
    )
    return validate_request(mandate, request)


def _build_payment_input(
    challenge: PayBenchChallenge,
    *,
    amount: Decimal,
    merchant: str,
    category: str,
    max_amount: Decimal,
    confirmation_above: Decimal | None,
    allowed_merchants: frozenset[str],
) -> tuple[IntentMandate, TransactionRequest]:
    now = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)
    mandate = IntentMandate(
        mandate_id=f"paybench-{challenge.scenario_id}",
        user_id="paybench-user",
        max_amount=max_amount,
        confirmation_above=confirmation_above,
        allowed_merchants=allowed_merchants,
        allowed_categories=frozenset(),
        expires_at=now + timedelta(days=1),
        currency="USD",
    )
    request = TransactionRequest(
        request_id=f"request-{challenge.scenario_id}-{merchant}",
        amount=amount,
        merchant=merchant,
        category=category,
        occurred_at=now,
        currency="USD",
    )
    return mandate, request
