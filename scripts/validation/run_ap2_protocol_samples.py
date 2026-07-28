from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_payment_experiment.adapters import adapt_ap2_flow_snapshot, evaluate_ap2_flow


DEFAULT_FIXTURES = (
    ROOT / "samples" / "protocol_snapshots" / "AP2_v020_HP_cards.json",
    ROOT / "samples" / "protocol_snapshots" / "AP2_v020_HNP_cards.json",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="离线运行 AP2 v0.2.0 的人在场 / 人不在场最小协议样例。"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "ap2_v020_flow_report.json",
        help="报告输出路径。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    results: list[dict[str, object]] = []

    for fixture_path in DEFAULT_FIXTURES:
        snapshot = json.loads(fixture_path.read_text(encoding="utf-8"))
        adapted = adapt_ap2_flow_snapshot(snapshot)
        validation = evaluate_ap2_flow(adapted)
        source = snapshot.get("_source", {})
        expected_decision = "ALLOW"
        status = "PASS" if adapted.ready and validation.decision.value == expected_decision else "FAIL"
        results.append(
            {
                "fixture": fixture_path.name,
                "flow_mode": adapted.flow_mode.value if adapted.flow_mode else None,
                "adapter_ready": adapted.ready,
                "decision": validation.decision.value,
                "expected_decision": expected_decision,
                "status": status,
                "issue_codes": [issue.code for issue in validation.issues],
                "flow_errors": list(adapted.flow_errors),
                "missing_fields": list(adapted.missing_fields),
                "unmapped_fields": list(adapted.unmapped_fields),
                "source_scenario": source.get("scenario"),
            }
        )

    passed = sum(item["status"] == "PASS" for item in results)
    report = {
        "benchmark": "AP2 v0.2.0 minimal flow integration",
        "status": "PASS" if passed == len(results) else "FAIL",
        "source": {
            "repository": "google-agentic-commerce/AP2",
            "release": "v0.2.0",
            "commit": "b4587ac",
            "license": "Apache-2.0",
        },
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
        },
        "limitations": {
            "offline_normalized_fixtures": True,
            "cryptographic_signatures_not_verified": True,
            "natural_language_intent_not_machine_verified": True,
            "not_ap2_conformance_test": True,
            "does_not_execute_real_payment": True,
        },
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "AP2 v0.2.0: "
        f"total={report['summary']['total']} "
        f"passed={report['summary']['passed']} "
        f"failed={report['summary']['failed']}"
    )
    for item in results:
        print(
            f"  {item['flow_mode']}: {item['status']} "
            f"decision={item['decision']}"
        )
    print(f"Report: {args.output.resolve()}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
