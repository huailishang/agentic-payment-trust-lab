from __future__ import annotations

import argparse
from pathlib import Path

from .runner import print_summary, run_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic payment protocol-neutral experiments")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run-scenarios",
        help="run the current fixed offline agentic-payment scenario set and generate JSON/HTML reports",
    )
    run_parser.add_argument("--scenarios-dir", type=Path, default=None)
    run_parser.add_argument("--artifacts-dir", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run-scenarios":
        card = run_scenarios(
            scenarios_dir=args.scenarios_dir,
            artifacts_dir=args.artifacts_dir,
        )
        print_summary(card)
        return 0 if card["summary"]["failed"] == 0 else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
