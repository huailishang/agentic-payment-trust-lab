from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVID = Path(__file__).resolve().parent
MANIFEST_PATH = EVID / "TASK-START-src-manifest.json"
EXPECTED = {
    "src/agentic_payment_experiment/authoritative_trace_consumer.py": "6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5",
    "tests/test_authoritative_trace_consumer.py": "dfa4a7717020819c96fdc0c21a8c7e68a9aee043a4fb02932b4d8252026100fc",
    "src/agentic_payment_experiment/html_report.py": "b93aeb6f18b59bac195e624b7acf10c20e6ed46338796735a3bfc1017f93164a",
    "src/agentic_payment_experiment/interactive_lab.py": "cb083a9fee9c21e5d87e49f097b1ce33d0546c1b0fb79bb59f7b5b7da6308150",
    "src/agentic_payment_experiment/interactive_server.py": "d0be3aa65cca715845d3c41e38a75cb251764e2287cf49c3eb5efef1019b718f",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in sorted((ROOT / "src").rglob("*.py"))
    }
    for rel, expected in EXPECTED.items():
        actual = sha(ROOT / rel)
        assert actual == expected, (rel, expected, actual)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_sha = sha(MANIFEST_PATH)
    print(f"observed_task_start_head={head}")
    print(f"task_start_src_count={len(manifest)}")
    print(f"task_start_src_manifest_file={MANIFEST_PATH.name}")
    print(f"task_start_src_manifest_file_sha256={manifest_sha}")
    for rel in EXPECTED:
        print(f"frozen_hash {rel}={sha(ROOT / rel)}")
    print("RESULT=PASS")


if __name__ == "__main__":
    main()
