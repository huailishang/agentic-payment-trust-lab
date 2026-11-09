"""H42 frozen validation entry; existing runtime only."""
import os
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]

def main():
    runtime = os.environ.get("H42_TEST_PYTHON")
    if not runtime or not Path(runtime).is_file():
        raise SystemExit("H42_TEST_PYTHON must name an existing Python with cryptography")
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONUTF8="1")
    mode = sys.argv[1]
    if mode in {"baseline", "measurement"}:
        commands = [[runtime, str(PACKAGE / "EVALUATOR_CHECK.py"), mode]]
    elif mode == "regressions":
        commands = [[runtime, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-q"]
                    for pattern in ("test_webshop_agent_behavior.py", "test_webshop_runtime_gate.py")]
        commands += [["git", "diff", "--check"]]
    else:
        raise SystemExit("unknown mode")
    codes = [subprocess.run(command, cwd=ROOT, env=env, check=False).returncode for command in commands]
    return 0 if all(code == 0 for code in codes) else 1

if __name__ == "__main__":
    sys.exit(main())
