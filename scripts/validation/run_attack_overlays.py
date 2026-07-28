from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.attack_overlay import (
    load_attack_overlay_suite,
    run_attack_overlay_suite,
    write_attack_overlay_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="运行 Attack Overlay v1：验证不可信网页/工具文本不能直接改写可信支付输入。"
    )
    parser.add_argument(
        "--suite",
        type=Path,
        default=ROOT / "samples" / "attacks" / "attack_overlay_v1.json",
        help="Attack Overlay 场景集。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "attack_overlay_v1_report.json",
        help="报告输出路径。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    suite = load_attack_overlay_suite(args.suite)
    batch = run_attack_overlay_suite(
        suite,
        scenarios_dir=ROOT / "samples" / "scenarios",
    )
    write_attack_overlay_report(suite, batch, args.output)

    print(
        "Attack Overlay v1: "
        f"total={batch.total} passed={batch.passed} failed={batch.failed} "
        f"attack_cases={batch.attack_cases} blocked={batch.blocked_attack_cases} "
        f"decision_drifts={batch.decision_drifts} "
        f"trusted_state_mutations={batch.trusted_state_mutations}"
    )
    for result in batch.results:
        print(
            f"  {result.attack_id}: {result.evaluation.status} "
            f"decision={result.defended_decision.value} "
            f"blocked={','.join(result.blocked_override_paths) or '-'}"
        )
    print(f"Report: {args.output.resolve()}")
    return 0 if batch.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
