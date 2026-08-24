from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from agentic_payment_experiment.webshop_journey_player import (
    WebShopJourneyPlayerInputError,
    build_webshop_journey_player_payload,
    render_webshop_journey_player,
)
from tests.test_webshop_journey_player import build_representative_journey


def require_rejection(label: str, journey: object) -> None:
    for operation in (
        build_webshop_journey_player_payload,
        render_webshop_journey_player,
    ):
        try:
            operation(journey)
        except WebShopJourneyPlayerInputError as exc:
            print(f"PASS {label} via {operation.__name__}: {exc}")
            continue
        raise AssertionError(
            f"{label} produced normal output via {operation.__name__}"
        )


def main() -> None:
    accepted = build_representative_journey()
    require_rejection(
        "unverified source classification",
        replace(accepted, source_classification_status="UNVERIFIED"),
    )
    require_rejection(
        "unknown schema version",
        replace(accepted, schema_version="webshop-journey-read-model/v999"),
    )


if __name__ == "__main__":
    main()
