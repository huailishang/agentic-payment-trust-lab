from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "docs/05_任务交接/P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1"

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/trusted_execution/signed_instruction.py": "6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2",
    ROOT / "src/agentic_payment_experiment/adapters/ap2_signed_instruction.py": "c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae",
    ROOT / "src/agentic_payment_experiment/adapters/acp_webhook.py": "cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac",
    ROOT / "pyproject.toml": "bc16c28fde7ba55e3de78c054efd2751bfcf6e033298ff0472fe3056023fbbd3",
    TASK / "evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json": "b0ffc3a5707e403febb545bb8a142767e101a2c3edf42eaad40396552f9fe910",
    TASK / "evaluator_fixtures/X509_SVID_POSSESSION_MATRIX.json": "9f72cc24c8557aee48f7b611ed71e3d253ad311c607e3260f713500140a8eda8",
}

REQUIRED = (
    ROOT / "src/agentic_payment_experiment/trusted_execution/credential_possession.py",
    ROOT / "src/agentic_payment_experiment/trusted_execution/execution_facts.py",
    ROOT / "src/agentic_payment_experiment/trusted_execution/__init__.py",
    ROOT / "src/agentic_payment_experiment/payment_execution.py",
    ROOT / "scripts/validation/run_p3_x509_svid_credential_possession_capability.py",
    ROOT / "tests/trusted_execution/test_credential_possession.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for path, expected in PROTECTED.items():
        if not path.is_file():
            raise AssertionError(f"protected file missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise AssertionError(f"protected file changed: {path}: {actual} != {expected}")

    for path in REQUIRED:
        if not path.is_file():
            raise AssertionError(f"required H-29 file missing: {path}")

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if dependencies != ["cryptography>=41"]:
        raise AssertionError(f"unexpected dependency set: {dependencies!r}")

    version = importlib.metadata.version("cryptography")
    if int(version.split(".", 1)[0]) < 41:
        raise AssertionError(f"cryptography too old: {version}")

    vector = json.loads((TASK / "evaluator_fixtures/X509_SVID_POSSESSION_VECTOR.json").read_text(encoding="utf-8"))
    serialized = json.dumps(vector, ensure_ascii=False).lower()
    forbidden = ("private_key", "private key-----", "begin ec private key", "begin private key")
    if any(token in serialized for token in forbidden):
        raise AssertionError("evaluator fixture appears to persist private-key material")

    print("PASS: H-29 frozen fixtures/protected Signed Instruction sources/dependency boundary are stable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
