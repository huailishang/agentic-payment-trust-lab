from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "scripts/validation/webshop/run_same_journey_lifecycle_branches.py"
PROTECTED = {
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evidence/SAME_JOURNEY_RESULT.json": "9c611dfe121d970569ea41d1e1831d0f829da307c61a6839996846ca893545fc",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_SAME_JOURNEY_BASELINE_LIFECYCLE_REPAIR_V1/evaluator_fixtures/SAME_JOURNEY_EXPERIMENT_CONTEXT.json": "6a52d7cb77a1186209a88ab877560a352089b818e8c898977e1e0148dc94b3d1",
    ROOT / "src/agentic_payment_experiment/webshop_agent_behavior.py": "6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f",
    ROOT / "scripts/validation/webshop/run_same_journey_responsibility.py": "ad962ae567851a5929e17163dc227a84b636bd85589edbcf52f52a5afe25208e",
    ROOT / "src/agentic_payment_experiment/webshop_payment_sidecar.py": "e74939a0b1da9eba5e70f34ab8f745ac61e8ae2254c2ab823ee92c5299a210c8",
    ROOT / "src/agentic_payment_experiment/payment_recovery.py": "c8c2d7a71b4293105ea2365a7486f143b4ad2f8a9ea10d842bf00dae522107de",
    ROOT / "src/agentic_payment_experiment/payment_finality.py": "b517d00e28d6a018d03f333af2a638ec8b0f95532a819fcad64a415d4018c9a1",
    ROOT / "src/agentic_payment_experiment/payment_status_conflict.py": "75c87e9382f29b045caf987a4d6e92281395748189df505294a210bb1fbbbf4d",
    ROOT / "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    ROOT / "src/agentic_payment_experiment/remediation.py": "43a76921fe3058edee4b1778b73949a00dc76a44de08a36f8a3d4e8cdb8c15d3",
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "95ef06d6d396f9c912f321df907ed198908f629abf93c296ce0f9bf3d68439a6",
}
FORBIDDEN_IMPORT_ROOTS = {"requests", "httpx", "urllib", "socket", "selenium", "playwright"}
REQUIRED_SOURCE_TOKENS = {
    "assess_webshop_payment_fulfilment",
    "derive_payment_query_finality",
    "validate_product_authoritative_trace",
    "consume_authoritative_trace",
    "project_authoritative_trace_origins",
    "run_same_journey_responsibility",
}
FORBIDDEN_TOKENS = {
    "click[buy now]",
    "requests.",
    "httpx.",
    "socket.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path, expected in PROTECTED.items():
        require(path.is_file(), f"protected file missing: {path}")
        require(sha256(path) == expected, f"protected file changed: {path}")

    require(RUNNER.is_file(), f"measurement runner missing: {RUNNER}")
    text = RUNNER.read_text(encoding="utf-8")
    lower = text.lower()
    for token in REQUIRED_SOURCE_TOKENS:
        require(token.lower() in lower, f"required existing capability not consumed by runner: {token}")
    for token in FORBIDDEN_TOKENS:
        require(token.lower() not in lower, f"forbidden real-side-effect/network token in runner: {token}")

    tree = ast.parse(text, filename=str(RUNNER))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                require(alias.name.split(".", 1)[0] not in FORBIDDEN_IMPORT_ROOTS, f"forbidden network import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            require(root not in FORBIDDEN_IMPORT_ROOTS, f"forbidden network import: {node.module}")

    print("PASS: lifecycle branch measurement consumes existing payment-state/finality/recovery/trace/origin capabilities without modifying protected product code or enabling real side effects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
