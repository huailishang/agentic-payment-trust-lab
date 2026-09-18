from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef"

PROTECTED = {
    "src/agentic_payment_experiment/models.py": "d38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65",
    "src/agentic_payment_experiment/validator.py": "9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb",
    "src/agentic_payment_experiment/trusted_execution/payment_binding.py": "139cc77fa57689cd46e9b2716c5877b012d5366e520bab812d8ad121fdcf9e87",
    "src/agentic_payment_experiment/trusted_execution/signed_instruction.py": "6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2",
    "src/agentic_payment_experiment/trusted_execution/credential_possession.py": "ecea0b6d674d71b92de0cf148be2aff0b158cb11d5f62d5ac61a37d66b38650c",
    "src/agentic_payment_experiment/data_disclosure.py": "42fb3ffff4bbb034f9d1fe3840f58931b9281fa4f691b5303eb7ff0775da3d26",
    "src/agentic_payment_experiment/lifecycle.py": "8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92",
    "src/agentic_payment_experiment/authoritative_trace.py": "f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492",
    "src/agentic_payment_experiment/payment_execution.py": "d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49",
    "src/agentic_payment_experiment/adapters/ap2.py": "22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867",
    "src/agentic_payment_experiment/adapters/ap2_signed_instruction.py": "c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae",
}

ALLOWED_PRODUCT_CHANGES = {
    "src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py",
    "src/agentic_payment_experiment/adapters/__init__.py",
    "tests/test_ap2_protocol_boundary.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed_product_paths() -> set[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "src", "tests"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        raw = line[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.add(raw.replace("\\", "/"))
    return paths


def main() -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != BASELINE:
        raise SystemExit(f"baseline HEAD moved: expected={BASELINE} actual={head}")

    bad_hashes: list[str] = []
    for relative, expected in PROTECTED.items():
        path = ROOT / relative
        if not path.is_file():
            bad_hashes.append(f"{relative}:missing")
            continue
        actual = sha256(path)
        if actual != expected:
            bad_hashes.append(f"{relative}:{actual}")

    changed = changed_product_paths()
    unexpected = sorted(changed - ALLOWED_PRODUCT_CHANGES)
    required_new = {
        "src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py",
        "tests/test_ap2_protocol_boundary.py",
    }
    missing_new = sorted(path for path in required_new if not (ROOT / path).is_file())

    if bad_hashes or unexpected or missing_new:
        print(
            {
                "result": "FAIL",
                "protected_hash_failures": bad_hashes,
                "unexpected_product_changes": unexpected,
                "missing_required_files": missing_new,
                "observed_product_changes": sorted(changed),
            }
        )
        raise SystemExit(1)

    print(
        {
            "result": "PASS",
            "baseline_head": head,
            "protected_files": len(PROTECTED),
            "observed_product_changes": sorted(changed),
        }
    )


if __name__ == "__main__":
    main()
