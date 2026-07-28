from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from .adapters import adapt_ap2_snapshot
from .html_report import write_html_report
from .interactive_lab import build_interactive_catalog
from .lab_overview import build_lab_overview
from .learning_variants import build_s09_learning_variants
from .lifecycle import assess_lifecycle
from .payment_recovery import assess_payment_recovery
from .remediation import assess_remediation
from .presentation_zh import (
    DECISION_PRESENTATION_ZH,
    attach_scenario_presentation,
    missing_builtin_reason_mappings,
)
from .result_card import build_result_card, scenario_result_record, write_result_card
from .scenario_loader import Scenario, load_scenarios
from .validator import validate_request


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_scenarios(
    *,
    scenarios_dir: Path | None = None,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    root = project_root()
    scenario_path = scenarios_dir or root / "samples" / "scenarios"
    output_path = artifacts_dir or root / "artifacts"

    records: list[dict[str, Any]] = []
    for scenario in load_scenarios(scenario_path):
        mandate, request, protocol_trace = _runtime_input(scenario)
        result = validate_request(
            mandate,
            request,
            seen_request_ids=scenario.seen_request_ids,
            authorized_order=scenario.authorized_order,
            final_order=scenario.final_order,
        )
        lifecycle_result = None
        if scenario.payment_execution is not None and scenario.fulfillment is not None:
            if scenario.final_order is None:
                raise ValueError(
                    f"{scenario.source_path} lifecycle scenario requires a final_order"
                )
            lifecycle_result = assess_lifecycle(
                request,
                scenario.final_order,
                scenario.payment_execution,
                scenario.fulfillment,
            )
            if scenario.refund is not None or scenario.dispute is not None:
                lifecycle_result = assess_remediation(
                    scenario.final_order,
                    scenario.payment_execution,
                    lifecycle_result,
                    refund=scenario.refund,
                    dispute=scenario.dispute,
                )

        payment_recovery_result = None
        if (
            scenario.payment_recovery_initial is not None
            and scenario.payment_status_observation is not None
        ):
            payment_recovery_result = assess_payment_recovery(
                scenario.payment_recovery_initial,
                scenario.payment_status_observation,
                known_attempts=scenario.known_payment_attempts,
            )

        runtime_input = {
            "mandate": _json_ready(asdict(mandate)),
            "request": _json_ready(asdict(request)),
            "seen_request_ids": sorted(scenario.seen_request_ids),
        }
        if scenario.authorized_order is not None and scenario.final_order is not None:
            runtime_input["authorized_order"] = _json_ready(asdict(scenario.authorized_order))
            runtime_input["final_order"] = _json_ready(asdict(scenario.final_order))
        if scenario.payment_execution is not None:
            runtime_input["payment_execution"] = _json_ready(asdict(scenario.payment_execution))
        if scenario.fulfillment is not None:
            runtime_input["fulfillment"] = _json_ready(asdict(scenario.fulfillment))
        if scenario.refund is not None:
            runtime_input["refund"] = _json_ready(asdict(scenario.refund))
        if scenario.dispute is not None:
            runtime_input["dispute"] = _json_ready(asdict(scenario.dispute))
        if scenario.payment_recovery_initial is not None:
            runtime_input["payment_execution"] = _json_ready(
                asdict(scenario.payment_recovery_initial)
            )
        if scenario.payment_status_observation is not None:
            runtime_input["payment_status_observation"] = _json_ready(
                asdict(scenario.payment_status_observation)
            )
        if scenario.known_payment_attempts:
            runtime_input["known_payment_attempts"] = [
                _json_ready(asdict(item)) for item in scenario.known_payment_attempts
            ]
        record = scenario_result_record(
            scenario,
            result,
            runtime_input=runtime_input,
            protocol_trace=protocol_trace,
            lifecycle_result=lifecycle_result,
            payment_recovery_result=payment_recovery_result,
        )
        attach_scenario_presentation(record)
        if (
            scenario.sample_id == "S09"
            and scenario.authorized_order is not None
            and scenario.final_order is not None
        ):
            record["learning_variants"] = build_s09_learning_variants(
                scenario,
                mandate,
                request,
                scenario.authorized_order,
                scenario.final_order,
                record["protocol"],
            )
        records.append(record)

    missing_mappings = missing_builtin_reason_mappings(records)
    if missing_mappings:
        raise ValueError(f"missing Chinese reason mappings: {', '.join(sorted(missing_mappings))}")

    card = build_result_card(records)
    card["presentation_catalog"] = {"decisions": DECISION_PRESENTATION_ZH}
    card["interactive"] = build_interactive_catalog(scenarios_dir=scenario_path)
    card["lab_overview"] = build_lab_overview(card, root=root)
    json_path = output_path / "scenario_result_card.json"
    html_path = output_path / "scenario_report.html"
    card["artifacts"] = {
        "result_card": str(json_path),
        "html_report": str(html_path),
    }
    write_result_card(card, json_path)
    write_html_report(card, html_path)
    return card


def print_summary(card: dict[str, Any]) -> None:
    for scenario in card["scenarios"]:
        marker = "PASS" if scenario["status"] == "passed" else "FAIL"
        protocol = scenario.get("protocol", {}).get("name", "NEUTRAL")
        lifecycle = scenario.get("lifecycle")
        payment_recovery = scenario.get("payment_recovery")
        task_suffix = ""
        if lifecycle:
            task_suffix = (
                f" payment={lifecycle['payment_status']}"
                f" fulfillment={lifecycle['fulfillment_status']}"
            )
            if lifecycle.get("refund_status") is not None:
                task_suffix += f" refund={lifecycle['refund_status']}"
            if lifecycle.get("dispute_status") is not None:
                task_suffix += f" dispute={lifecycle['dispute_status']}"
            task_suffix += (
                f" remediation={lifecycle['remediation']['status']}"
                f" task={lifecycle['task_status']}"
            )
        if payment_recovery:
            task_suffix += (
                f" initial_payment={payment_recovery['initial_status']}"
                f" observed_payment={payment_recovery['observed_status']}"
                f" recovery={payment_recovery['recovery_status']}"
                f" retry_allowed={str(payment_recovery['retry_allowed']).lower()}"
            )
        print(
            f"{scenario['sample_id']} {marker} "
            f"protocol={protocol} "
            f"expected={scenario['expected']['decision']} "
            f"actual={scenario['actual']['decision']}"
            f"{task_suffix}"
        )

    summary = card["summary"]
    print(
        "\nSummary: "
        f"total={summary['total']} "
        f"passed={summary['passed']} "
        f"failed={summary['failed']}"
    )
    overview = card.get("lab_overview")
    if overview:
        print(f"\n实验模块总览：{overview['status_label_zh']}")
        for module in overview["modules"]:
            print(
                f"  {module['name_zh']}: {module['status']} "
                f"passed={module['passed']} failed={module['failed']} "
                f"gaps={module['gap_count']}"
            )

    print("Artifacts:")
    print(f"  {card['artifacts']['result_card']}")
    print(f"  {card['artifacts']['html_report']}")


def _runtime_input(
    scenario: Scenario,
) -> tuple[Any, Any, dict[str, Any] | None]:
    protocol_demo = scenario.raw.get("protocol_demo")
    if not protocol_demo:
        return scenario.mandate, scenario.request, None

    protocol_name = str(protocol_demo.get("protocol", "")).upper()
    if protocol_name != "AP2":
        raise ValueError(
            f"{scenario.source_path} uses unsupported protocol_demo: {protocol_name}"
        )

    snapshot = protocol_demo.get("snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError(f"{scenario.source_path} protocol_demo.snapshot must be an object")

    adapted = adapt_ap2_snapshot(snapshot)
    if not adapted.ready or adapted.mandate is None or adapted.request is None:
        raise ValueError(
            f"{scenario.source_path} AP2 snapshot cannot be adapted: "
            f"{', '.join(adapted.missing_fields)}"
        )

    trace = {
        "name": "AP2",
        "version": adapted.protocol_version,
        "status": "teaching_snapshot",
        "purpose": (
            "把用户授权边界和最终支付请求表达成可传递、可验证的对象，"
            "再交给本地规则引擎判断。"
        ),
        "what_it_does_not_do": (
            "当前快照不执行真实支付，也不验证SD-JWT、签名、委托链或收据。"
        ),
        "without_protocol": (
            "没有统一协议时，Agent、商户和支付方需要各自约定字段，"
            "金额、商户、有效期和授权范围容易出现口径不一致。"
        ),
        "raw_input": snapshot,
        "neutral_output": {
            "mandate": _json_ready(asdict(adapted.mandate)),
            "request": _json_ready(asdict(adapted.request)),
        },
        "field_mapping": list(protocol_demo.get("field_mapping", [])),
        "unverified_gaps": list(adapted.unmapped_fields),
        "source": "google-agentic-commerce/AP2 v0.2.0 teaching snapshot",
    }
    return adapted.mandate, adapted.request, trace


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_json_ready(item) for item in value]
        return sorted(items) if isinstance(value, (set, frozenset)) else items
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
