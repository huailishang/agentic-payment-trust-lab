from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BASELINE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RegressionComparison:
    matches: bool
    differences: tuple[str, ...]


def build_regression_snapshot(card: dict[str, Any]) -> dict[str, Any]:
    scenarios: dict[str, Any] = {}
    for record in card["scenarios"]:
        sample_id = str(record["sample_id"])
        scenarios[sample_id] = {
            "status": record["status"],
            "expected": {
                "decision": record["expected"]["decision"],
                "reason_codes": list(record["expected"]["reason_codes"]),
                "evidence_codes": list(record["expected"]["evidence_codes"]),
                "forbidden_effects": list(record["expected"].get("forbidden_effects", [])),
            },
            "actual": {
                "decision": record["actual"]["decision"],
                "reason_codes": list(record["actual"]["reason_codes"]),
                "evidence_codes": [item["code"] for item in record["actual"]["evidence"]],
                "order_differences": record["actual"].get("order_differences", []),
            },
            "evaluation": _json_ready(record["evaluation"]),
            "observed_effects": list(record.get("observed_effects", [])),
            "lifecycle": _lifecycle_snapshot(record.get("lifecycle")),
            "payment_recovery": _payment_recovery_snapshot(record.get("payment_recovery")),
        }

    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "sample_set": card["sample_set"],
        "evaluation_summary": _json_ready(card["evaluation_summary"]),
        "scenarios": scenarios,
    }


def load_regression_baseline(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported regression baseline schema: {data.get('schema_version')!r}"
        )
    return data


def write_regression_baseline(snapshot: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_regression_report(
    comparison: RegressionComparison,
    *,
    baseline_path: Path,
    scenario_count: int,
    path: Path,
) -> None:
    report = {
        "status": "PASS" if comparison.matches else "FAIL",
        "baseline": str(baseline_path),
        "scenario_count": scenario_count,
        "differences": list(comparison.differences),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare_regression_snapshots(
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> RegressionComparison:
    differences: list[str] = []
    _compare_values(expected, actual, path="", differences=differences)
    return RegressionComparison(
        matches=not differences,
        differences=tuple(differences),
    )


def _lifecycle_snapshot(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "payment_status": value["payment_status"],
        "fulfillment_status": value["fulfillment_status"],
        "refund_status": value.get("refund_status"),
        "dispute_status": value.get("dispute_status"),
        "remediation": {
            "status": value["remediation"]["status"],
            "next_action": value["remediation"]["next_action"],
        },
        "task_status": value["task_status"],
        "reason_codes": list(value["reason_codes"]),
        "evidence_codes": [item["code"] for item in value["evidence"]],
    }


def _payment_recovery_snapshot(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "initial_status": value["initial_status"],
        "observed_status": value["observed_status"],
        "effective_status": value["effective_status"],
        "recovery_status": value["recovery_status"],
        "retry_allowed": value["retry_allowed"],
        "next_action": value["next_action"],
        "reason_codes": list(value["reason_codes"]),
        "evidence_codes": [item["code"] for item in value["evidence"]],
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _compare_values(
    expected: Any,
    actual: Any,
    *,
    path: str,
    differences: list[str],
) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            child_path = f"{path}.{key}" if path else str(key)
            if key not in expected:
                differences.append(f"{child_path}: unexpected={actual[key]!r}")
            elif key not in actual:
                differences.append(f"{child_path}: missing expected={expected[key]!r}")
            else:
                _compare_values(
                    expected[key],
                    actual[key],
                    path=child_path,
                    differences=differences,
                )
        return

    if isinstance(expected, list) and isinstance(actual, list):
        if expected != actual:
            differences.append(f"{path}: expected={expected!r} actual={actual!r}")
        return

    if expected != actual:
        differences.append(f"{path}: expected={expected!r} actual={actual!r}")
