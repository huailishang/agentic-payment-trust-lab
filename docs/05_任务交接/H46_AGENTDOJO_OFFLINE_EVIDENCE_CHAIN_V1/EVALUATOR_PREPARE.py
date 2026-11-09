"""Evaluator-only preparation: read pinned public sources; never run upstream."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
COMMIT = "a75aba7631d3ca5fb7ab938965c97ead2f9ff84b"
FILES = {
    "LICENSE": "LICENSE",
    "banking_client.py": "src/agentdojo/default_suites/v1/tools/banking_client.py",
    "user_tasks.py": "src/agentdojo/default_suites/v1/banking/user_tasks.py",
    "injection_tasks.py": "src/agentdojo/default_suites/v1/banking/injection_tasks.py",
    "task_suite.py": "src/agentdojo/default_suites/v1/banking/task_suite.py",
    "banking_init.py": "src/agentdojo/default_suites/v1/banking/__init__.py",
    "pyproject.toml": "pyproject.toml",
}


def main():
    folder = TASK / "sources"
    folder.mkdir(exist_ok=True)
    entries = []
    for name, path in FILES.items():
        url = f"https://raw.githubusercontent.com/ethz-spylab/agentdojo/{COMMIT}/{path}"
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read(300000)
        assert content and len(content) < 300000
        (folder / name).write_bytes(content)
        entries.append({"path": f"sources/{name}", "upstream_path": path,
                        "url": url, "sha256": hashlib.sha256(content).hexdigest(),
                        "bytes": len(content)})
    lock = {"schema": "h46-source-lock/v1", "commit": COMMIT, "release": "v0.1.35",
            "suite": "v1/banking", "license": "MIT", "files": entries,
            "runtime_boundary": "AST_SOURCE_SLICE_NOT_FULL_AGENTDOJO_RUNTIME"}
    (TASK / "SOURCE_LOCK.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_count": len(entries), "commit": COMMIT}))


if __name__ == "__main__":
    main()
