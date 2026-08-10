from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
MANIFEST = EVID / "TASK-START-src-manifest.json"
EXPECTED = {
    "samples/external/webshop/pre_buy_now_candidate_v1.json": "6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5",
    "src/agentic_payment_experiment/adapters/webshop.py": "035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4",
    "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    "src/agentic_payment_experiment/authoritative_trace_player.py": "9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    current = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
    }
    for rel, expected in EXPECTED.items():
        actual = sha(ROOT / rel)
        assert actual == expected, (rel, expected, actual)
    MANIFEST.write_text(
        json.dumps(current, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"observed_task_start_head={head}")
    print(f"task_start_src_count={len(current)}")
    print(f"task_start_src_manifest_sha256={sha(MANIFEST)}")
    for rel in EXPECTED:
        print(f"frozen_hash {rel}={sha(ROOT / rel)}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()
