"""Frozen offline caller-to-receiver integration check; never dispatches WSL."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import sys
import tempfile

import RUN
from CHECK import historical

P = Path(__file__).resolve().parent


def main():
    tree = ast.parse((P / "CHECK.py").read_text(encoding="utf-8"))
    live = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "live")
    calls = [n for n in ast.walk(live) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess" and n.func.attr == "run"]
    if len(calls) != 1 or not isinstance(calls[0].args[0], ast.List):
        raise ValueError("frozen caller expression changed")
    base = P / "runtime/seam_check"
    base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="owned_", dir=base) as tmp:
        root = Path(tmp).resolve()
        task = root / "task"
        run_id, nonce = "a" * 32, "b" * 32
        out = task / "evidence/evaluator_runs" / run_id
        out.mkdir(parents=True)
        expression = ast.Expression(body=calls[0].args[0])
        # Evaluate only the already-frozen argv expression, never a subprocess.
        argv = eval(compile(expression, "frozen-caller-argv", "eval"), {"__builtins__": {"str": str}, "sys": sys, "P": task, "ROOT": root, "out": out, "run_id": run_id, "nonce": nonce})
        supplied = argv[argv.index("--out") + 1]
        if supplied != out.relative_to(root).as_posix() or RUN.output_path(root, task, run_id, supplied) != out:
            raise ValueError("actual caller-to-receiver integration failed")
        negatives = ["../escape", str(out), "//outside/share", "C:/outside", supplied + "/..", supplied.replace("/", "\\")]
        for value in negatives:
            try:
                RUN.output_path(root, task, run_id, value)
            except ValueError:
                pass
            else:
                raise ValueError("strict output guard weakened")
        if any(out.iterdir()):
            raise ValueError("offline seam check wrote dispatch artifacts")
    print(json.dumps({"actual_frozen_caller_argv_checked": True, "receiver_unchanged": True, "positive": 1, "rejected_paths": len(negatives), "wsl_dispatches": 0, "live_runs": 0}))
    print(json.dumps(historical(), ensure_ascii=False))


if __name__ == "__main__":
    main()
