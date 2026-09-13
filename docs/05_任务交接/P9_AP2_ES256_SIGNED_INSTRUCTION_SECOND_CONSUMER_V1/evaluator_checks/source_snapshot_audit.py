from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[4]

PROTECTED = {
    ROOT / "src/agentic_payment_experiment/adapters/ap2.py": "22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867",
    ROOT / "src/agentic_payment_experiment/adapters/acp_webhook.py": "cc723725eb3fd220482bbc21721843d77ba92e7b7a7c29431753e6c6e0e4ffac",
    ROOT / "scripts/validation/run_signed_instruction_verification_capability.py": "5be73da638cac0583857c012acaa00575ae27b008faf383225f72f8e9d03c543",
    ROOT / "docs/05_任务交接/P9_AP2_ES256_SIGNED_INSTRUCTION_SECOND_CONSUMER_V1/evaluator_fixtures/AP2_ES256_JWS_MATRIX.json": "17b10958e319d965fa081144824a4d54773b52a5b90314aafcc86252150ce605",
}

REQUIRED = (
    ROOT / "src/agentic_payment_experiment/trusted_execution/signed_instruction.py",
    ROOT / "src/agentic_payment_experiment/adapters/ap2_signed_instruction.py",
    ROOT / "scripts/validation/run_ap2_es256_signed_instruction_capability.py",
    ROOT / "tests/trusted_execution/test_signed_instruction_es256.py",
    ROOT / "tests/test_ap2_signed_instruction.py",
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
            raise AssertionError(f"required H-27 file missing: {path}")

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if dependencies != ["cryptography>=41"]:
        raise AssertionError(f"unexpected dependency set: {dependencies!r}")

    version = importlib.metadata.version("cryptography")
    major = int(version.split(".", 1)[0])
    if major < 41:
        raise AssertionError(f"cryptography too old: {version}")

    print("PASS: protected AP2/ACP/H-25 sources and frozen H-27 matrix are stable; only cryptography>=41 is declared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
