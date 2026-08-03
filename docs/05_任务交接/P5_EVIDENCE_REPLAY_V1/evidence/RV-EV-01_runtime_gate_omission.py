"""Independent P5 counterexample: replay accepts P1-only ALLOW beside invalid P4."""

from __future__ import annotations

import inspect
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from agentic_payment_experiment.payment_execution import PAYMENT_CONTEXT_ACTION, PAYMENT_REQUIRED_SOURCE_PATHS
from agentic_payment_experiment.runner import _build_replay_case
from agentic_payment_experiment.trusted_execution import evaluate_context_policy


def main() -> None:
    signature = str(inspect.signature(_build_replay_case))
    source = inspect.getsource(_build_replay_case)
    fact = evaluate_context_policy(
        {}, required_source_paths=PAYMENT_REQUIRED_SOURCE_PATHS, current_action=PAYMENT_CONTEXT_ACTION
    ).fact
    print(f"replay_builder_signature={signature}")
    print(f"p4_status={fact.status.value}")
    print(f"p4_missing={','.join(fact.missing_source_paths)}")
    print(f"builder_consumes_payment_gate={'execute_with_payment_binding_gate' in source}")
    print(f"builder_consumes_context_fact={'context_policy_fact' in source}")
    assert fact.status.value == "MISSING_EVIDENCE"
    assert "context_policy_fact" not in signature
    assert "execute_with_payment_binding_gate" not in source
    assert "context_policy_fact" not in source


if __name__ == "__main__":
    main()
