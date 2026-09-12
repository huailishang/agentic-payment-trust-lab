from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/authoritative_trace.py": "f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492",
    ROOT / "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    ROOT / "src/agentic_payment_experiment/authoritative_trace_player.py": "9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541",
    ROOT / "src/agentic_payment_experiment/action_origin.py": "b43cf1338e7397107aae83a1fca78752b55cd15c900f0160d64a6983707fcada",
    ROOT / "src/agentic_payment_experiment/webshop_remediation_trace.py": "961f6042bc48afc160b3373bd2b439da30127f32de44fa3937cc00d1dc3460ad",
    ROOT / "scripts/validation/webshop/run_same_journey_remediation_trace_closure.py": "a90f0923ee6fdbb1c9b8d0cee76390f04d2786a8350bd8c09fafa7e62061d1fc",
    ROOT / "tests/test_authoritative_trace_consumer.py": "dfa4a7717020819c96fdc0c21a8c7e68a9aee043a4fb02932b4d8252026100fc",
    ROOT / "tests/test_authoritative_trace_player.py": "3101671e80139988c1b755a5f975c92f8f75f570498613ee223154111ffcf991",
    ROOT / "docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_TRACE_EVIDENCE_CLOSURE_V1/evidence/H22_REMEDIATION_TRACE_RESULT.json": "ba1d4e562bef9ae975c81049b0c24399513cf62f6f8d1c7bb6ece4f2b4e09891",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for path, expected in PROTECTED.items():
        if not path.is_file():
            raise AssertionError(f"protected file missing: {path}")
        if sha256(path) != expected:
            raise AssertionError(f"protected file changed: {path}")
    print("PASS: H-22 product and existing Consumer/Player/Action-Origin stack remain byte-frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
