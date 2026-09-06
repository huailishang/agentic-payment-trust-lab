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


def decide(instruction: str, clickables: list[str], previous: list[str]):
    return choose_webshop_action(
        AgentPolicyInput(
            instruction_text=instruction,
            observation="synthetic evaluator option state",
            available_actions={"clickables": clickables, "has_search_bar": False},
            step_index=len(previous),
            previous_actions=previous,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()

    base_prev = ["search[synthetic query]", "click[aaaaaaaaaa]"]
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

    record(
        "OG-01-simple-exact-text-option",
        "click[teal]",
        False,
        decide(
            "please find a teal bath towel",
            ["buy now", "teal", "teal blue"],
            base_prev,
        ),
    )

    record(
        "OG-02-do-not-overwrite-completed-requested-option",
        None,
        True,
        decide(
            "buy a cashew snack with hazelnut flavor",
            ["buy now", "hazelnut", "original cashew", "sea salt"],
            base_prev + ["click[hazelnut]"],
        ),
    )

    record(
        "OG-03-dimension-format-normalization",
        "click[72x44x38cm]",
        False,
        decide(
            "storage cube size 72 x 44 x 38 cm",
            ["buy now", "72x44x38cm", "80x50x40cm"],
            base_prev,
        ),
    )

    record(
        "OG-04-cardinality-word-to-visible-label",
        "click[1pcs]",
        False,
        decide(
            "show one serum roller for scalp care",
            ["buy now", "1pcs", "2pcs"],
            base_prev,
        ),
    )

    first = decide(
        "deodorant with cedar scent in a 2.4 ounce size",
        ["buy now", "floral", "cedar scent", "2.5 ounce (pack of 1)", "2.4 ounce (pack of 1)"],
        base_prev,
    )
    if first.action == "click[cedar scent]" and not first.stop:
        second = decide(
            "deodorant with cedar scent in a 2.4 ounce size",
            ["buy now", "floral", "cedar scent", "2.5 ounce (pack of 1)", "2.4 ounce (pack of 1)"],
            base_prev + [first.action],
        )
    else:
        second = first
    record(
        "OG-05-multiple-independent-option-groups",
        "click[2.4 ounce (pack of 1)]",
        False,
        second,
    )

    passed = sum(1 for item in results if item["passed"])
    payload = {
        "schema": "webshop-option-grounding-probe/v1",
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
