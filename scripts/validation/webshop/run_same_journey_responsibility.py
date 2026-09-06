from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPOSITORY_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# This helper is Python-3.8-compatible and does not import the newer product stack.
import run_autonomous_prebuy_behavior as autonomous


SCHEMA = "webshop-same-journey-responsibility/v1"
EXPECTED_ORIGINS = {
    "USER_AUTHORITY",
    "AGENT_DECISION",
    "RUNTIME_DECISION",
    "EXTERNAL_FACT",
    "EXECUTION_RESULT",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--goal-index", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--accepted-behavior", required=True)
    parser.add_argument("--experiment-context", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--integration-json-stdin", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def mapping(value: object, label: str) -> Mapping[str, Any]:
    require(isinstance(value, Mapping), f"{label} must be a mapping")
    return value  # type: ignore[return-value]


def iso_datetime(value: object, label: str) -> datetime:
    require(isinstance(value, str) and bool(value), f"{label} must be text")
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, f"{label} must have timezone")
    return parsed


def decimal_text(value: object) -> str:
    return format(Decimal(str(value)), "f")


def product_title(runtime: Any, asin: str) -> str:
    table = runtime.server.product_item_dict
    item = None
    for key in (asin, asin.upper(), asin.lower()):
        if key in table:
            item = table[key]
            break
    require(isinstance(item, Mapping), f"runtime product missing for {asin}")
    assert isinstance(item, Mapping)
    for key in ("Title", "title", "name"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise RuntimeError(f"runtime product title missing for {asin}")


def replay_score(
    runtime: Any,
    session_id: str,
    accepted_score: Mapping[str, Any],
) -> dict[str, object]:
    session = runtime.server.user_sessions[str(session_id)]
    selected_asin = session.get("asin")
    selected_options = session.get("options", {})
    require(isinstance(selected_options, Mapping), "runtime selected options must be mapping")
    assert isinstance(selected_options, Mapping)
    option_values = [str(value) for value in selected_options.values()]
    selected_price = None
    if selected_asin is not None:
        raw_price = runtime.server.product_prices.get(str(selected_asin).upper())
        if raw_price is not None:
            selected_price = float(raw_price)

    expected_asin = str(accepted_score.get("selected_asin") or "")
    expected_options_raw = accepted_score.get("selected_option_values", [])
    expected_options = (
        [str(value).lower() for value in expected_options_raw]
        if isinstance(expected_options_raw, list)
        else []
    )
    expected_price = float(accepted_score.get("selected_price"))
    return {
        "selected_asin": selected_asin,
        "selected_option_values": option_values,
        "selected_price": selected_price,
        "target_match": str(selected_asin or "").upper() == expected_asin.upper(),
        "required_option_match": all(
            expected in [value.lower() for value in option_values]
            for expected in expected_options
        ),
        "price_match": selected_price is not None
        and abs(float(selected_price) - expected_price) < 0.0001,
    }


def replay_once(
    policy: Any,
    checkout: Path,
    goal_index: int,
    seed: int,
    accepted_score: Mapping[str, Any],
) -> tuple[dict[str, object], dict[str, object]]:
    runtime = autonomous.make_runtime(checkout, seed)
    initial = runtime.reset(session=goal_index)
    observation = autonomous.normalise_observation(initial)
    instruction = str(runtime.instruction_text)
    previous_actions: list[str] = []
    steps: list[dict[str, object]] = []
    stopped = False

    for step_index in range(10):
        available = autonomous.normalise_actions(runtime.get_available_actions())
        state = policy.AgentPolicyInput(
            instruction_text=instruction,
            observation=observation,
            available_actions=available,
            step_index=step_index,
            previous_actions=tuple(previous_actions),
        )
        decision = policy.choose_webshop_action(state)
        if decision.stop:
            stopped = True
            break
        require(bool(decision.action), "policy returned neither action nor stop")
        action = str(decision.action)
        require(
            action.strip().lower() != "click[buy now]",
            "policy attempted forbidden Buy Now action",
        )

        observation_hash = hashlib.sha256(observation.encode("utf-8")).hexdigest()
        result = runtime.step(action)
        require(
            isinstance(result, tuple) and len(result) == 4,
            "unexpected WebShop step result",
        )
        next_observation, reward, done, _info = result
        steps.append(
            {
                "sequence": step_index,
                "observation_sha256": observation_hash,
                "available_actions": available,
                "chosen_action": action,
                "reason_summary": decision.reason_summary,
                "reward": float(reward),
                "done": bool(done),
                "source": "WEBSHOP_RUNTIME_OBSERVATION",
            }
        )
        previous_actions.append(action)
        observation = autonomous.normalise_observation(next_observation)
        require(not done, "runtime ended before pre-purchase stop")

    require(stopped, "policy did not reach bounded stop condition")
    final_actions = autonomous.normalise_actions(runtime.get_available_actions())
    buy_now_available = any(
        str(item).lower() == "buy now"
        for item in final_actions.get("clickables", [])
    )
    session_id = str(runtime.session)
    session = runtime.server.user_sessions[session_id]
    purchase_count = int(session.get("actions", {}).get("purchase", 0))
    score = replay_score(runtime, session_id, accepted_score)
    run: dict[str, object] = {
        "steps": steps,
        "buy_now_available": buy_now_available,
        "buy_now_executed": False,
        "purchase_count": purchase_count,
        "score": score,
    }
    run["normalized_trace_sha256"] = autonomous.trace_hash(run)

    selected_asin = str(session.get("asin") or "")
    selected_options_raw = session.get("options", {})
    require(
        isinstance(selected_options_raw, Mapping),
        "selected options are not mapping",
    )
    assert isinstance(selected_options_raw, Mapping)
    selected_options = {
        str(key): str(value) for key, value in selected_options_raw.items()
    }
    unit_price = runtime.server.product_prices.get(selected_asin.upper())
    require(unit_price is not None, "selected product price missing")
    facts: dict[str, object] = {
        "session_id": session_id,
        "instruction_text": instruction,
        "actions_executed": [step["chosen_action"] for step in steps],
        "product": {
            "asin": selected_asin.upper(),
            "title": product_title(runtime, selected_asin),
            "selected_options": selected_options,
            "quantity": 1,
            "unit_price": decimal_text(unit_price),
        },
    }
    return run, facts


def find_modern_python() -> Path:
    current = Path(sys.executable).resolve()
    for ancestor in current.parents:
        candidate = ancestor / "install" / "python.exe"
        if candidate.is_file() and candidate != current:
            return candidate
    raise RuntimeError("local modern Python interpreter not found")


def replay_phase(args: argparse.Namespace) -> int:
    require(args.repeat == 2, "frozen H-16 repeat must be 2")
    checkout = Path(args.checkout).resolve()
    accepted_path = (REPOSITORY_ROOT / args.accepted_behavior).resolve()
    accepted = mapping(
        json.loads(accepted_path.read_text(encoding="utf-8")),
        "accepted behavior",
    )
    accepted_runs = accepted.get("runs")
    require(
        isinstance(accepted_runs, list) and bool(accepted_runs),
        "accepted runs missing",
    )
    assert isinstance(accepted_runs, list)
    accepted_trace_sha = str(
        mapping(accepted_runs[0], "accepted run0")["normalized_trace_sha256"]
    )
    accepted_score = mapping(accepted.get("score"), "accepted score")
    require(
        args.goal_index == accepted.get("goal_index"),
        "goal index differs from accepted evidence",
    )
    require(args.seed == accepted.get("seed"), "seed differs from accepted evidence")
    require(
        autonomous.checkout_head(checkout) == accepted.get("checkout_head"),
        "checkout HEAD differs from accepted evidence",
    )

    autonomous.setup_local_jvm()
    policy = autonomous.load_policy_module()
    replay_runs: list[dict[str, object]] = []
    replay_facts: list[dict[str, object]] = []
    for _ in range(args.repeat):
        run, facts = replay_once(
            policy,
            checkout,
            args.goal_index,
            args.seed,
            accepted_score,
        )
        replay_runs.append(run)
        replay_facts.append(facts)

    digests = [str(run["normalized_trace_sha256"]) for run in replay_runs]
    require(len(set(digests)) == 1, "replay repeats are not identical")
    require(
        digests[0] == accepted_trace_sha,
        "replay normalized trace differs from accepted trace",
    )
    require(
        replay_facts[0] == replay_facts[1],
        "same replay produced different runtime candidate facts",
    )
    first_run = replay_runs[0]
    score = mapping(first_run["score"], "replay score")
    require(first_run["buy_now_executed"] is False, "real Buy Now executed")
    require(first_run["purchase_count"] == 0, "WebShop purchase count is non-zero")
    require(score.get("target_match") is True, "replay product mismatch")
    require(score.get("required_option_match") is True, "replay option mismatch")
    require(score.get("price_match") is True, "replay price mismatch")

    bridge_payload = {
        "accepted_fixture_sha256": sha256(accepted_path),
        "accepted_trace_sha256": accepted_trace_sha,
        "replay_trace_sha256": digests[0],
        "goal_index": args.goal_index,
        "seed": args.seed,
        "repeat": args.repeat,
        "repeat_identical": True,
        "first_run": first_run,
        "facts": replay_facts[0],
    }

    modern_python = find_modern_python()
    command = [
        str(modern_python),
        str(Path(__file__).resolve()),
        "--checkout",
        args.checkout,
        "--goal-index",
        str(args.goal_index),
        "--seed",
        str(args.seed),
        "--repeat",
        str(args.repeat),
        "--accepted-behavior",
        args.accepted_behavior,
        "--experiment-context",
        args.experiment_context,
        "--output",
        args.output,
        "--integration-json-stdin",
    ]
    completed = subprocess.run(
        command,
        cwd=str(REPOSITORY_ROOT),
        input=json.dumps(bridge_payload, ensure_ascii=False),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    require(
        completed.returncode == 0,
        f"modern integration phase failed with exit={completed.returncode}",
    )
    return 0


def product_imports() -> dict[str, object]:
    # Delayed until the Python-3.12 integration phase. The WebShop runtime is
    # intentionally pinned to Python 3.8 and cannot import the modern trace stack.
    from agentic_payment_experiment.action_origin import (
        action_origin_records_to_primitive,
        project_authoritative_trace_origins,
    )
    from agentic_payment_experiment.adapters.webshop import (
        EXPECTED_ASSET_HASHES,
        WEBSHOP_COMMIT,
        WEBSHOP_FIXTURE_SCHEMA,
        WEBSHOP_SMOKE_EVIDENCE_PATH,
        WEBSHOP_SMOKE_SHA256,
        adapt_webshop_purchase_candidate,
    )
    from agentic_payment_experiment.authoritative_trace import (
        TraceValidationStatus,
        validate_product_authoritative_trace,
    )
    from agentic_payment_experiment.authoritative_trace_consumer import (
        TraceConsumerStatus,
        consume_authoritative_trace,
        trace_read_model_to_primitive,
    )
    from agentic_payment_experiment.models import (
        AgentIdentity,
        FulfillmentRecord,
        FulfillmentStatus,
        IntentMandate,
        PaymentExecutionRecord,
        PaymentStatus,
    )
    from agentic_payment_experiment.payment_execution import (
        PAYMENT_CONTEXT_ACTION,
        PAYMENT_REQUIRED_SOURCE_PATHS,
    )
    from agentic_payment_experiment.trusted_execution import (
        POLICY_VERSION,
        ActionReversibility,
        GovernedActionType,
        GovernedPaymentAction,
        SideEffectClass,
        SourceType,
        create_confirmation_record,
        evaluate_context_policy,
    )
    from agentic_payment_experiment.webshop_payment_sidecar import (
        assess_webshop_payment_fulfilment,
    )
    from agentic_payment_experiment.webshop_runtime_gate import gate_webshop_buy_now

    return locals()


def source_scaffold(api: Mapping[str, object]) -> dict[str, object]:
    return {
        "webshop_commit": api["WEBSHOP_COMMIT"],
        "smoke_result_sha256": api["WEBSHOP_SMOKE_SHA256"],
        "evidence_path": api["WEBSHOP_SMOKE_EVIDENCE_PATH"],
        "provenance": {"kind": "local_p9_a2_evidence", "immutable": True},
        "asset_hashes": dict(api["EXPECTED_ASSET_HASHES"]),  # type: ignore[arg-type]
    }


def build_candidate(
    facts: Mapping[str, Any],
    experiment_context: Mapping[str, Any],
    api: Mapping[str, object],
) -> dict[str, object]:
    product = mapping(facts.get("product"), "replay product")
    quantity = int(product["quantity"])
    unit_price = Decimal(str(product["unit_price"]))
    return {
        "fixture_schema": api["WEBSHOP_FIXTURE_SCHEMA"],
        "fixture_version": "same-journey-v1",
        "source": source_scaffold(api),
        "session_id": facts["session_id"],
        "task_identifier": f"webshop-session-{facts['session_id']}",
        "instruction_text": facts["instruction_text"],
        "actions_executed": list(facts["actions_executed"]),
        "buy_now_available": True,
        "buy_now_executed": False,
        "product": {
            "asin": product["asin"],
            "title": product["title"],
            "selected_options": dict(
                mapping(product["selected_options"], "selected options")
            ),
            "quantity": quantity,
            "unit_price": format(unit_price, "f"),
            "order_total": format(unit_price * quantity, "f"),
        },
        "experiment_context": dict(
            mapping(experiment_context.get("commerce_context"), "commerce context")
        ),
    }


def make_context_fact(
    mandate: Any,
    order: Any,
    request: Any,
    api: Mapping[str, object],
) -> Any:
    SourceType = api["SourceType"]
    state = {
        "mandate": {"mandate_id": mandate.mandate_id},
        "final_order": {"order_id": order.order_id},
        "request": {
            "request_id": request.request_id,
            "agent_id": request.agent_id,
            "amount": request.amount,
            "payee": request.payee,
            "currency": request.currency,
        },
    }
    sources = {
        "mandate.mandate_id": SourceType.USER_CONFIRMED,
        "final_order.order_id": SourceType.USER_CONFIRMED,
        "request.request_id": SourceType.PROTOCOL_VERIFIED,
        "request.agent_id": SourceType.USER_CONFIRMED,
        "request.amount": SourceType.USER_CONFIRMED,
        "request.payee": SourceType.USER_CONFIRMED,
        "request.currency": SourceType.USER_CONFIRMED,
    }
    evaluate_context_policy = api["evaluate_context_policy"]
    return evaluate_context_policy(
        state,
        trusted_sources=sources,
        required_source_paths=api["PAYMENT_REQUIRED_SOURCE_PATHS"],
        current_action=api["PAYMENT_CONTEXT_ACTION"],
        policy_version=api["POLICY_VERSION"],
    ).fact


def strip_ref(value: object, prefix: str) -> str:
    require(
        isinstance(value, str) and value.startswith(prefix),
        f"trace ref missing prefix {prefix}",
    )
    return str(value)[len(prefix) :]


def correlation(
    cid: str,
    source_path: str,
    source_value: object,
    target_path: str,
    target_value: object,
) -> dict[str, object]:
    return {
        "correlation_id": cid,
        "source_path": source_path,
        "source_value": source_value,
        "target_path": target_path,
        "target_value": target_value,
        "equal": source_value == target_value,
    }


def integration_phase(args: argparse.Namespace) -> int:
    bridge = mapping(json.loads(sys.stdin.read()), "replay bridge")
    facts = mapping(bridge.get("facts"), "replay facts")
    first_run = mapping(bridge.get("first_run"), "replay first run")
    api = product_imports()

    context_path = (REPOSITORY_ROOT / args.experiment_context).resolve()
    output_path = (REPOSITORY_ROOT / args.output).resolve()
    experiment_context = mapping(
        json.loads(context_path.read_text(encoding="utf-8")),
        "experiment context",
    )
    candidate = build_candidate(facts, experiment_context, api)
    adapt = api["adapt_webshop_purchase_candidate"]
    adaptation = adapt(candidate)
    require(
        adaptation.ready
        and adaptation.order is not None
        and adaptation.payment_request is not None,
        f"Commerce Adapter not ready: {adaptation.missing_fields}",
    )
    order = adaptation.order
    authority = mapping(experiment_context["authority"], "authority")
    runtime_identity = mapping(
        experiment_context["runtime_identity"], "runtime_identity"
    )
    offline_execution = mapping(
        experiment_context["offline_execution"], "offline_execution"
    )
    agent_id = str(authority["expected_agent_id"])
    bound_request = replace(adaptation.payment_request, agent_id=agent_id)

    IntentMandate = api["IntentMandate"]
    mandate = IntentMandate(
        mandate_id=str(authority["mandate_id"]),
        user_id=str(authority["user_id"]),
        max_amount=Decimal(str(authority["max_amount"])),
        allowed_merchants=frozenset({order.merchant}),
        allowed_categories=frozenset({bound_request.category}),
        expires_at=iso_datetime(authority["expires_at"], "authority.expires_at"),
        max_count=int(authority["max_count"]),
        expected_agent_id=agent_id,
        currency=str(authority["currency"]),
        authority_version=str(authority["authority_version"]),
    )
    AgentIdentity = api["AgentIdentity"]
    identity = AgentIdentity(
        agent_id=agent_id,
        provider=str(runtime_identity["provider"]),
        executor_instance_id=str(runtime_identity["executor_instance_id"]),
        status="active",
        credential_ref=str(runtime_identity["credential_ref"]),
    )
    PaymentExecutionRecord = api["PaymentExecutionRecord"]
    PaymentStatus = api["PaymentStatus"]
    payment_candidate = PaymentExecutionRecord(
        payment_id=f"same-journey-payment-{bound_request.request_id}",
        request_id=bound_request.request_id,
        order_id=order.order_id,
        status=PaymentStatus.PENDING,
        amount=bound_request.amount,
        currency=bound_request.currency,
        occurred_at=bound_request.occurred_at + timedelta(seconds=1),
        provider_ref=str(runtime_identity["provider"]),
        idempotency_key=f"same-journey:{bound_request.request_id}",
        authority_ref=mandate.mandate_id,
        agent_ref=agent_id,
        transaction_object_ref=bound_request.request_id,
        payee=order.payee,
    )
    policy_fact = make_context_fact(mandate, order, bound_request, api)
    GovernedPaymentAction = api["GovernedPaymentAction"]
    GovernedActionType = api["GovernedActionType"]
    SideEffectClass = api["SideEffectClass"]
    ActionReversibility = api["ActionReversibility"]
    governed_action = GovernedPaymentAction(
        action_id=f"same-journey-action-{bound_request.request_id}",
        action_type=GovernedActionType.EXECUTE_PAYMENT,
        subject_ref=mandate.user_id,
        agent_ref=agent_id,
        executor_ref=str(runtime_identity["executor_instance_id"]),
        authority_ref=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order_ref=order.order_id,
        order_version=order.order_version,
        request_ref=bound_request.request_id,
        payment_ref=payment_candidate.payment_id,
        source_refs=(
            "source:same-journey-webshop-runtime",
            "source:same-journey-explicit-authority",
        ),
        side_effect_class=SideEffectClass.PAYMENT_EXECUTION,
        reversibility=ActionReversibility.COMPENSATABLE_NOT_REVERSIBLE,
        occurred_at=bound_request.occurred_at + timedelta(milliseconds=500),
    )
    create_confirmation_record = api["create_confirmation_record"]
    confirmation = create_confirmation_record(
        confirmation_id=f"same-journey-confirmation-{bound_request.request_id}",
        authority_id=mandate.mandate_id,
        authority_version=mandate.authority_version,
        order=order,
        confirmed_at=bound_request.occurred_at - timedelta(minutes=1),
        expires_at=bound_request.occurred_at + timedelta(minutes=30),
    )
    callback_calls: list[str] = []

    def offline_checkout_seam() -> str:
        callback_calls.append("offline_checkout_seam")
        return str(offline_execution["callback_result_ref"])

    gate_webshop_buy_now = api["gate_webshop_buy_now"]
    gate = gate_webshop_buy_now(
        adaptation=adaptation,
        mandate=mandate,
        declared_agent_id=agent_id,
        execution_candidate=payment_candidate,
        agent_identity=identity,
        current_provider_ref=str(runtime_identity["provider"]),
        current_executor_instance_ref=str(runtime_identity["executor_instance_id"]),
        current_credential_ref=str(runtime_identity["credential_ref"]),
        context_policy_fact=policy_fact,
        checkout_callback=offline_checkout_seam,
        confirmation_record=confirmation,
        authorized_adaptation=adaptation,
        governed_action=governed_action,
    )
    require(
        getattr(gate.decision, "value", str(gate.decision)) == "ALLOW",
        f"Runtime Gate blocked: {gate.reason_codes}",
    )
    require(gate.bound_request is not None, "Runtime Gate bound request missing")
    require(
        gate.callback_count == 1 and callback_calls == ["offline_checkout_seam"],
        "offline callback seam count mismatch",
    )
    require(
        gate.callback_result_ref == offline_execution["callback_result_ref"],
        "offline callback seam ref mismatch",
    )

    payment = replace(
        payment_candidate,
        status=PaymentStatus.SUCCEEDED,
        receipt_ref="offline-same-journey-receipt",
    )
    FulfillmentRecord = api["FulfillmentRecord"]
    FulfillmentStatus = api["FulfillmentStatus"]
    fulfillment = FulfillmentRecord(
        fulfillment_id=f"same-journey-fulfillment-{order.order_id}",
        order_id=order.order_id,
        status=FulfillmentStatus.SUCCEEDED,
        occurred_at=payment.occurred_at + timedelta(minutes=3),
        evidence_ref="offline-same-journey-fulfillment-evidence",
    )
    assess = api["assess_webshop_payment_fulfilment"]
    sidecar = assess(
        gate_outcome=gate,
        adaptation=adaptation,
        mandate=mandate,
        payment=payment,
        fulfillment=fulfillment,
    )
    require(
        sidecar.ready and sidecar.authoritative_trace is not None,
        f"Payment Sidecar not ready: {sidecar.reason_codes}",
    )
    trace_obj = sidecar.authoritative_trace
    validate_trace = api["validate_product_authoritative_trace"]
    trace_validation = validate_trace(trace_obj)
    TraceValidationStatus = api["TraceValidationStatus"]
    require(
        trace_validation.status is TraceValidationStatus.VALID,
        f"authoritative trace invalid: {trace_validation.reason_codes}",
    )
    consume = api["consume_authoritative_trace"]
    consumed = consume(trace_obj)
    TraceConsumerStatus = api["TraceConsumerStatus"]
    require(
        consumed.status is TraceConsumerStatus.AVAILABLE
        and consumed.read_model is not None,
        f"authoritative trace consumer unavailable: {consumed.reason_codes}",
    )
    to_primitive = api["trace_read_model_to_primitive"]
    trace_primitive = to_primitive(consumed.read_model)
    project_origins = api["project_authoritative_trace_origins"]
    origin_to_primitive = api["action_origin_records_to_primitive"]
    origin_records = origin_to_primitive(project_origins(trace_primitive))
    origin_types = sorted({str(item["action_origin"]) for item in origin_records})
    require(
        EXPECTED_ORIGINS.issubset(set(origin_types)),
        f"Action Origin coverage incomplete: {origin_types}",
    )

    by_role = {event["entity_role"]: event for event in trace_primitive["events"]}
    trace_order_id = strip_ref(
        by_role["CURRENT_ORDER_SNAPSHOT"]["entity_ref"], "Order:"
    )
    trace_request_id = strip_ref(
        by_role["CURRENT_REQUEST"]["entity_ref"], "TransactionRequest:"
    )
    trace_payment_id = strip_ref(
        by_role["PAYMENT_EXECUTION_OUTCOME"]["entity_ref"],
        "PaymentExecutionRecord:",
    )
    require(trace_order_id == order.order_id, "trace order ref differs from same journey")
    require(
        trace_request_id == bound_request.request_id,
        "trace request ref differs from same journey",
    )
    require(
        trace_payment_id == payment.payment_id,
        "trace payment ref differs from same journey",
    )

    replay_product = mapping(facts["product"], "replay product")
    replay_selected_options = dict(
        mapping(replay_product["selected_options"], "replay selected options")
    )
    commerce_selected_options = dict(adaptation.selected_options)
    product_source = {
        "asin": str(replay_product["asin"]).upper(),
        "selected_options": replay_selected_options,
        "order_total": format(
            Decimal(str(replay_product["unit_price"]))
            * int(replay_product["quantity"]),
            "f",
        ),
    }
    product_target = {
        "asin": order.items[0].item_id.upper(),
        "selected_options": commerce_selected_options,
        "order_total": format(order.total_amount, "f"),
    }
    request_pair = {
        "request_id": bound_request.request_id,
        "order_ref": bound_request.order_ref,
    }
    runtime_pair = {
        "request_id": gate.bound_request.request_id,
        "order_ref": gate.bound_request.order_ref,
    }
    execution_source = {
        "request_id": bound_request.request_id,
        "order_id": order.order_id,
        "fulfillment_order_id": order.order_id,
    }
    execution_target = {
        "request_id": payment.request_id,
        "order_id": payment.order_id,
        "fulfillment_order_id": fulfillment.order_id,
    }
    continuity_source = {
        "order_id": order.order_id,
        "request_id": bound_request.request_id,
        "payment_id": payment.payment_id,
        "action_origin_types": sorted(EXPECTED_ORIGINS),
    }
    continuity_target = {
        "order_id": trace_order_id,
        "request_id": trace_request_id,
        "payment_id": trace_payment_id,
        "action_origin_types": origin_types,
    }
    action_source = {
        "instruction_text": facts["instruction_text"],
        "actions_executed": list(facts["actions_executed"]),
    }
    action_target = {
        "instruction_text": candidate["instruction_text"],
        "actions_executed": candidate["actions_executed"],
    }
    accepted_trace_sha = str(bridge["accepted_trace_sha256"])
    replay_trace_sha = str(bridge["replay_trace_sha256"])

    correlations = [
        correlation(
            "C01_REPLAY_IDENTITY",
            "accepted_behavior.runs[0].normalized_trace_sha256",
            accepted_trace_sha,
            "replay.normalized_trace_sha256",
            replay_trace_sha,
        ),
        correlation(
            "C02_SESSION_TO_CANDIDATE",
            "replay.session_id",
            facts["session_id"],
            "candidate.session_id",
            candidate["session_id"],
        ),
        correlation(
            "C03_ACTIONS_TO_CANDIDATE",
            "replay.instruction_and_actions",
            action_source,
            "candidate.instruction_and_actions",
            action_target,
        ),
        correlation(
            "C04_PRODUCT_TO_ORDER",
            "replay.product",
            product_source,
            "commerce.order.item",
            product_target,
        ),
        correlation(
            "C05_ORDER_TO_REQUEST",
            "commerce.order_id",
            order.order_id,
            "commerce.request.order_ref",
            adaptation.payment_request.order_ref,
        ),
        correlation(
            "C06_REQUEST_TO_RUNTIME",
            "commerce.request",
            request_pair,
            "runtime_gate.bound_request",
            runtime_pair,
        ),
        correlation(
            "C07_ORDER_REQUEST_TO_EXECUTION",
            "commerce.order_request",
            execution_source,
            "execution.payment_fulfillment_refs",
            execution_target,
        ),
        correlation(
            "C08_TRACE_ORIGIN_CONTINUITY",
            "execution.same_journey_refs_and_origins",
            continuity_source,
            "trace.same_journey_refs_and_origins",
            continuity_target,
        ),
    ]
    require(
        all(item["equal"] is True for item in correlations),
        "one or more same-journey correlations failed",
    )

    first_score = mapping(first_run["score"], "first replay score")
    replay_product_payload = dict(replay_product)
    result = {
        "schema": SCHEMA,
        "accepted_behavior": {
            "fixture_sha256": bridge["accepted_fixture_sha256"],
            "normalized_trace_sha256": accepted_trace_sha,
        },
        "replay": {
            "goal_index": int(bridge["goal_index"]),
            "seed": int(bridge["seed"]),
            "repeat": int(bridge["repeat"]),
            "repeat_identical": bool(bridge["repeat_identical"]),
            "normalized_trace_sha256": replay_trace_sha,
            "matches_accepted": replay_trace_sha == accepted_trace_sha,
            "buy_now_executed": False,
            "purchase_count": int(first_run["purchase_count"]),
            "session_id": facts["session_id"],
            "instruction_text": facts["instruction_text"],
            "actions_executed": list(facts["actions_executed"]),
            "product": replay_product_payload,
            "score": dict(first_score),
        },
        "candidate": candidate,
        "commerce": {
            "adaptation_ready": adaptation.ready,
            "user_intent_text": adaptation.user_intent_text,
            "order_item_id": order.items[0].item_id,
            "order_id": order.order_id,
            "request_id": adaptation.payment_request.request_id,
            "request_order_ref": adaptation.payment_request.order_ref,
        },
        "runtime_gate": {
            "decision": getattr(gate.decision, "value", str(gate.decision)),
            "bound_request_id": gate.bound_request.request_id,
            "bound_order_ref": gate.bound_request.order_ref,
            "callback_count": gate.callback_count,
            "callback_result_ref": gate.callback_result_ref,
            "real_webshop_buy_now_executed": False,
        },
        "execution": {
            "request_id": payment.request_id,
            "order_id": payment.order_id,
            "fulfillment_order_id": fulfillment.order_id,
            "payment_status": payment.status.value,
            "fulfillment_status": fulfillment.status.value,
            "sidecar_ready": sidecar.ready,
            "real_payment_executed": False,
            "real_fulfillment_executed": False,
        },
        "trace": {
            "validation_status": trace_validation.status.value,
            "action_origin_types": origin_types,
            "order_id": trace_order_id,
            "request_id": trace_request_id,
            "payment_request_id": payment.request_id,
            "payment_order_id": payment.order_id,
        },
        "correlations": correlations,
        "guardrails": {
            "external_network_calls": 0,
            "real_webshop_buy_now_count": 0,
            "real_payment_execution_count": 0,
            "real_fulfillment_execution_count": 0,
            "instruction_promoted_to_authorization": False,
            "experiment_context_promoted_to_webshop_fact": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "correlation_passed": sum(
                    1 for item in correlations if item["equal"]
                ),
                "correlation_total": len(correlations),
                "replay_trace_sha256": replay_trace_sha,
                "runtime_decision": result["runtime_gate"]["decision"],
                "trace_validation_status": result["trace"]["validation_status"],
                "action_origin_types": origin_types,
                "real_side_effects": 0,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.integration_json_stdin:
        return integration_phase(args)
    return replay_phase(args)


if __name__ == "__main__":
    raise SystemExit(main())
