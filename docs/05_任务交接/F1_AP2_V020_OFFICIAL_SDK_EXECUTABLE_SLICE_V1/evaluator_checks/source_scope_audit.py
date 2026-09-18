from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = "0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef"
AP2_PIN = "b4587ac1d055888a73b4b21750973cffba961793"

ALLOWED_PRODUCT = {
    "src/agentic_payment_experiment/adapters/__init__.py",
    "src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py",
    "tests/test_ap2_protocol_boundary.py",
    "src/agentic_payment_experiment/adapters/ap2_sdk_bridge.py",
    "tests/test_ap2_sdk_bridge.py",
}

FROZEN_HASHES = {
    "src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py": "fae40678a356ecad4bd0cf5998476071499ab2c180c846f32ca75f3fb479d9ae",
    "tests/test_ap2_protocol_boundary.py": "084439ff194656ec149d2c1bfcbecb8ca6ef5f16ec8b0df7c6f41a24ca65aed7",
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

def run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def changed_product_paths() -> list[str]:
    out = run("git", "status", "--porcelain", "--untracked-files=all")
    result = []
    for line in out.splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if path.startswith("src/") or path.startswith("tests/"):
            result.append(path)
    return sorted(result)

def main() -> None:
    assert run("git", "rev-parse", "HEAD") == BASELINE
    changed = changed_product_paths()
    unexpected = [p for p in changed if p not in ALLOWED_PRODUCT]
    assert not unexpected, f"unexpected product changes: {unexpected}"
    for rel, expected in FROZEN_HASHES.items():
        actual = sha256(ROOT / rel)
        assert actual == expected, f"hash mismatch {rel}: {actual}"
    ap2 = ROOT / "local_sources/third_party/ap2-v0.2.0"
    assert run("git", "rev-parse", "HEAD", cwd=ap2) == AP2_PIN
    assert run("git", "status", "--porcelain", cwd=ap2) == ""
    print({
        "result": "PASS",
        "baseline_head": BASELINE,
        "official_ap2_pin": AP2_PIN,
        "frozen_hashes": len(FROZEN_HASHES),
        "observed_product_changes": changed,
    })

if __name__ == "__main__":
    main()
