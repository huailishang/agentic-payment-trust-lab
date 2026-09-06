from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

AUTONOMOUS_FIXTURE = ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_PREBUY_BEHAVIOR_CAPTURE_V1/evidence/EV-AUTONOMOUS-BEHAVIOR.json"
TRACE_FIXTURE = ROOT / "docs/05_任务交接/P9_AUTHORITATIVE_TRACE_READ_MODEL_PLAYER_V1/evidence/EV-03-T01.payload.json"
EXPECTED_ORIGINS = {
    "USER_AUTHORITY",
    "AGENT_DECISION",
    "RUNTIME_DECISION",
    "EXTERNAL_FACT",
    "EXECUTION_RESULT",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()

    try:
        from agentic_payment_experiment.action_origin import (
            ActionOrigin,
            ActionOriginError,
            classify_trace_event_origin,
            project_authoritative_trace_origins,
            project_autonomous_behavior_origins,
            action_origin_records_to_primitive,
        )
    except Exception as exc:  # target module is intentionally absent at baseline
        payload = {
            "schema": "action-origin-evaluator-probe/v1",
            "all_passed": False,
            "passed_count": 0,
            "failed_count": 5,
            "error": f"action-origin module unavailable: {type(exc).__name__}: {exc}",
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(text, end="")
        return 1 if args.require_all else 0

    behavior = json.loads(AUTONOMOUS_FIXTURE.read_text(encoding="utf-8"))
    trace = json.loads(TRACE_FIXTURE.read_text(encoding="utf-8"))

    cases: list[dict[str, object]] = []

    origin_values = {item.value for item in ActionOrigin}
    cases.append(
        {
            "case_id": "AO-01-closed-origin-types",
            "passed": origin_values == EXPECTED_ORIGINS,
            "observed": sorted(origin_values),
            "expected": sorted(EXPECTED_ORIGINS),
        }
    )

    autonomous_records = tuple(project_autonomous_behavior_origins(behavior))
    run0_steps = behavior["runs"][0]["steps"]
    autonomous_primitive = action_origin_records_to_primitive(autonomous_records)
    autonomous_agent_records = [
        item for item in autonomous_primitive if item.get("action_origin") == "AGENT_DECISION"
    ]
    agent_actions = [item.get("action_or_event") for item in autonomous_agent_records]
    expected_actions = [item["chosen_action"] for item in run0_steps]
    cases.append(
        {
            "case_id": "AO-02-autonomous-agent-decisions",
            "passed": agent_actions == expected_actions
            and len(autonomous_agent_records) == len(run0_steps)
            and all(item.get("evidence_ref") for item in autonomous_agent_records),
            "observed_actions": agent_actions,
            "expected_actions": expected_actions,
        }
    )

    trace_records = tuple(project_authoritative_trace_origins(trace))
    trace_primitive = action_origin_records_to_primitive(trace_records)
    anchors = {
        item.get("action_or_event"): item.get("action_origin")
        for item in trace_primitive
    }
    expected_anchors = {
        "AUTHORITY_RECORDED": "USER_AUTHORITY",
        "ORDER_RECORDED:CURRENT_ORDER_SNAPSHOT": "EXTERNAL_FACT",
        "ACTION_RECORDED": "AGENT_DECISION",
        "RUNTIME_DECISION_RECORDED": "RUNTIME_DECISION",
        "PAYMENT_OUTCOME_RECORDED": "EXECUTION_RESULT",
    }
    cases.append(
        {
            "case_id": "AO-03-authoritative-trace-anchor-mapping",
            "passed": all(anchors.get(key) == value for key, value in expected_anchors.items()),
            "observed": {key: anchors.get(key) for key in expected_anchors},
            "expected": expected_anchors,
        }
    )

    trace_origins = {item.get("action_origin") for item in trace_primitive}
    cases.append(
        {
            "case_id": "AO-04-five-origin-coverage-and-evidence-ref",
            "passed": EXPECTED_ORIGINS.issubset(trace_origins)
            and all(item.get("evidence_ref") for item in trace_primitive),
            "observed_origins": sorted(x for x in trace_origins if isinstance(x, str)),
            "expected_origins": sorted(EXPECTED_ORIGINS),
        }
    )

    unknown_rejected = False
    try:
        classify_trace_event_origin(
            {
                "sequence_no": 999,
                "event_type": "UNKNOWN_EVENT",
                "entity_role": "UNKNOWN_ROLE",
                "entity_type": "Unknown",
                "entity_ref": "Unknown:1",
                "source_binding_ref": "unknown-binding",
            }
        )
    except ActionOriginError:
        unknown_rejected = True
    cases.append(
        {
            "case_id": "AO-05-unknown-origin-fails-closed",
            "passed": unknown_rejected,
            "observed": unknown_rejected,
            "expected": True,
        }
    )

    passed_count = sum(1 for item in cases if item["passed"])
    payload = {
        "schema": "action-origin-evaluator-probe/v1",
        "case_count": len(cases),
        "passed_count": passed_count,
        "failed_count": len(cases) - passed_count,
        "all_passed": passed_count == len(cases),
        "autonomous_fixture": str(AUTONOMOUS_FIXTURE.relative_to(ROOT)),
        "trace_fixture": str(TRACE_FIXTURE.relative_to(ROOT)),
        "cases": cases,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if args.require_all and not payload["all_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
