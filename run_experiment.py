from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.interactive_server import create_interactive_server
from agentic_payment_experiment.regression_baseline import (
    build_regression_snapshot,
    compare_regression_snapshots,
    load_regression_baseline,
    write_regression_report,
)
from agentic_payment_experiment.runner import print_summary, run_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="运行当前固定智能体支付离线场景集，并生成JSON与HTML报告。"
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="运行成功后使用默认浏览器打开HTML报告或交互实验台。",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="启动仅绑定本机的交互实验服务，支持修改关键条件后由Python重新计算。",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="交互服务监听地址；默认仅本机127.0.0.1。",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="交互服务端口，默认8765。",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ROOT / "samples" / "regression" / "internal_baseline_v1.json",
        help="内部回归基线文件，默认使用 samples/regression/internal_baseline_v1.json。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    card = run_scenarios()
    print_summary(card)

    failed = int(card["summary"]["failed"])
    if failed:
        print("\n实验存在失败场景，请先检查结果卡，不自动打开页面。")
        return 1

    baseline = load_regression_baseline(args.baseline)
    current_snapshot = build_regression_snapshot(card)
    regression = compare_regression_snapshots(baseline, current_snapshot)
    regression_report_path = ROOT / "artifacts" / "internal_regression_report.json"
    write_regression_report(
        regression,
        baseline_path=args.baseline,
        scenario_count=len(card["scenarios"]),
        path=regression_report_path,
    )
    if not regression.matches:
        print(f"\n内部回归基线：FAIL（{args.baseline}）")
        for difference in regression.differences:
            print(f"  - {difference}")
        return 1
    print(f"\n内部回归基线：PASS（{args.baseline}）")

    report_path = Path(card["artifacts"]["html_report"]).resolve()
    print(f"\n验证通过。HTML报告：{report_path}")

    if args.serve:
        server = create_interactive_server(report_path, host=args.host, port=args.port)
        bound_host, bound_port = server.server_address[:2]
        url = f"http://{bound_host}:{bound_port}/"
        print(f"交互实验台：{url}")
        print("按 Ctrl+C 停止本地服务。")
        if args.open:
            opened = webbrowser.open(url)
            if not opened:
                print("未能自动打开浏览器，请手动打开上述交互实验台地址。")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n交互实验台已停止。")
        finally:
            server.server_close()
        return 0

    if args.open:
        opened = webbrowser.open(report_path.as_uri())
        if not opened:
            print("未能自动打开浏览器，请手动打开上述HTML文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
