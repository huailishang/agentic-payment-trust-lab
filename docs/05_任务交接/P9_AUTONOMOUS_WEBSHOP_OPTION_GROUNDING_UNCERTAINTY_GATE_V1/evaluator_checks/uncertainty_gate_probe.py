from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.webshop_agent_behavior import (  # noqa: E402
    AgentPolicyInput,
    choose_webshop_action,
)


def decide(instruction: str, clickables: list[str], previous: list[str] | None = None):
    prior = previous or ["search[synthetic uncertainty query]", "click[aaaaaaaaaa]"]
    return choose_webshop_action(
        AgentPolicyInput(
            instruction_text=instruction,
            observation="synthetic evaluator uncertainty-gate state",
            available_actions={"clickables": clickables, "has_search_bar": False},
            step_index=len(prior),
            previous_actions=prior,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()

    results: list[dict[str, object]] = []

    def record(case_id: str, expected_action: str | None, expected_stop: bool, actual) -> None:
        passed = actual.action == expected_action and actual.stop is expected_stop
        results.append(
            {
                "case_id": case_id,
                "expected_action": expected_action,
                "expected_stop": expected_stop,
                "actual": asdict(actual),
                "passed": passed,
            }
        )

    # Positive control: exact lexical grounding must remain allowed.
    record(
        "UG-01-exact-unique-lexical",
        "click[burgundy]",
        False,
        decide(
            "please find a burgundy scarf",
            ["buy now", "maroon", "burgundy"],
        ),
    )

    # Positive control: one uniquely grounded visible variant may still be selected.
    record(
        "UG-02-unique-partial-extension",
        "click[turquoise blue]",
        False,
        decide(
            "I need a turquoise bath towel",
            ["buy now", "gray", "turquoise blue"],
        ),
    )

    # Ambiguous partial grounding: both visible options share the same requested root.
    record(
        "UG-03-ambiguous-shared-root",
        None,
        True,
        decide(
            "find an olive blanket",
            ["buy now", "olive green", "olive brown"],
        ),
    )

    # Missing specific modifier: visible values only satisfy the generic tail.
    record(
        "UG-04-missing-specific-modifier",
        None,
        True,
        decide(
            "smoky violet candle",
            ["buy now", "deep violet", "light violet"],
        ),
    )

    # Another independent ambiguity seed, with no exact visible value.
    record(
        "UG-05-ambiguous-style-modifier",
        None,
        True,
        decide(
            "silver tumbler",
            ["buy now", "matte silver", "polished silver"],
        ),
    )

    passed = sum(1 for item in results if item["passed"])
    payload = {
        "schema": "webshop-option-grounding-uncertainty-gate-probe/v1",
        "case_count": len(results),
        "passed_count": passed,
        "failed_count": len(results) - passed,
        "all_passed": passed == len(results),
        "cases": results,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if args.require_all and not payload["all_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
