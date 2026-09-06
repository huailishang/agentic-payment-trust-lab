from __future__ import annotations

import json

from agentic_payment_experiment.webshop_agent_behavior import _instruction_option


def main() -> int:
    instruction = "I need black loafers"
    orders = [
        ["black1901", "black2003"],
        ["black2003", "black1901"],
    ]
    results = []
    for clickables in orders:
        results.append(
            {
                "clickables": clickables,
                "selected": _instruction_option(clickables, instruction, ()),
            }
        )

    order_invariant = results[0]["selected"] == results[1]["selected"]
    payload = {
        "schema": "webshop-policy-tiebreak-counterexample/v1",
        "instruction": instruction,
        "results": results,
        "order_invariant": order_invariant,
        "interpretation": (
            "Equivalent visible coded black variants change selection when UI order changes; "
            "instruction alone does not distinguish them."
        ),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if order_invariant is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
