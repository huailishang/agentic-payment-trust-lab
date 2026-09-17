from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

EXPECTED = {
    "src/agentic_payment_experiment/authoritative_trace.py": "f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492",
    "src/agentic_payment_experiment/webshop_trace_assembler.py": "c98c3a1477ebf64a5696707c0d637da60d8563ef174b06a100c9d9b7bebc1656",
    "src/agentic_payment_experiment/trusted_execution/governed_action.py": "115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e",
    "src/agentic_payment_experiment/payment_execution.py": "d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49",
    "src/agentic_payment_experiment/validator.py": "9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb",
    "scripts/validation/run_project_impact_baseline.py": "70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3",
    "samples/evaluation/project_impact_baseline_v1.json": "e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0",
    "src/agentic_payment_experiment/data_disclosure.py": "42fb3ffff4bbb034f9d1fe3840f58931b9281fa4f691b5303eb7ff0775da3d26",
    "src/agentic_payment_experiment/paybench_current_system.py": "319cdf82d849393b8adcaeabf73d79f4f7fb772fab2784439fc2c4877fbaccc1",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing protected file: {relative}")
            continue
        actual = digest(path)
        if actual != expected:
            failures.append(f"protected hash drift: {relative}: {actual}")

    toolkit = ROOT / "src/agentic_payment_experiment/webshop_action_binding_trace_toolkit.py"
    if not toolkit.is_file():
        failures.append("missing action-binding rejection trace toolkit")
    else:
        text = toolkit.read_text(encoding="utf-8")
        forbidden = (
            "scenario_id",
            "task_id",
            "governed_action_agent_mismatch",
            "governed_action_missing_id",
        )
        for token in forbidden:
            if token in text:
                failures.append(f"evaluator identity leaked into toolkit: {token}")

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1
    print("PASS: protected hashes unchanged and rejection trace toolkit is independent of evaluator task/scenario identity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
