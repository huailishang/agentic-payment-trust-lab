from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.paybench_challenges import (
    evaluate_paybench_attempts,
    load_paybench_attempts,
    load_paybench_challenges,
    write_paybench_report,
)
from agentic_payment_experiment.paybench_current_system import (
    run_current_rules_on_paybench,
    write_current_rules_paybench_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="运行固定 PayBench 10 题外部挑战评测。"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--attempts",
        type=Path,
        help="评测外部 Agent/Runtime 的 attempts JSON。",
    )
    mode.add_argument(
        "--current-rules",
        action="store_true",
        help="直接用本项目当前协议中立规则运行可表达的挑战，并报告覆盖缺口。",
    )
    parser.add_argument(
        "--challenges",
        type=Path,
        default=ROOT / "samples" / "external" / "paybench" / "phase1_selected_10.json",
        help="固定 PayBench 挑战集，默认使用项目内置的 10 题快照。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="报告输出路径；不指定时按运行模式写入 artifacts/。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    challenge_set = load_paybench_challenges(args.challenges)

    if args.current_rules:
        result = run_current_rules_on_paybench(challenge_set)
        output_path = args.output or ROOT / "artifacts" / "paybench_current_rules_report.json"
        write_current_rules_paybench_report(challenge_set, result, output_path)
        print(
            "PayBench current rules: "
            f"total={result.total} "
            f"supported={result.supported} "
            f"unsupported={result.unsupported}"
        )
        print(
            "Supported score: "
            f"supported_passed={result.supported_passed} "
            f"supported_failed={result.supported_failed}"
        )
        print(f"Report: {output_path.resolve()}")
        return 0 if result.supported_failed == 0 else 1

    if args.attempts is None:
        raise ValueError("--attempts is required unless --current-rules is used")
    attempts = load_paybench_attempts(args.attempts)
    batch = evaluate_paybench_attempts(challenge_set, attempts)
    output_path = args.output or ROOT / "artifacts" / "paybench_external_report.json"
    write_paybench_report(challenge_set, batch, output_path)

    print(
        "PayBench: "
        f"total={batch.total} "
        f"passed={batch.passed} "
        f"failed={batch.failed}"
    )
    print(
        "External risks: "
        f"unsafe_proceed={batch.unsafe_proceed} "
        f"refused_when_safe={batch.refused_when_safe} "
        f"forbidden_side_effect={batch.forbidden_side_effect}"
    )
    print(f"Report: {output_path.resolve()}")
    return 0 if batch.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
