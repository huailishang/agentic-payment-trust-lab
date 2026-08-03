from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


CONDA_ROOT = Path("/mnt/d/SoftWare/Anaconda/install")
CONDA_EXE = CONDA_ROOT / "Scripts/conda.exe"
ENVS_ROOT = Path("/mnt/d/SoftWare/Anaconda/workspace/.conda/envs")
AGENT_PYTHON = ENVS_ROOT / "agent/python.exe"
MODULES = ("gym", "flask", "torch", "spacy", "pyserini")
WSL_TOOLS = ("python", "python3", "java", "docker", "podman", "uv", "micromamba", "mamba", "pyenv")


def run(*args: str) -> dict[str, object]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {
        "argv": list(args),
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    conda_env_list = run(str(CONDA_EXE), "env", "list") if CONDA_EXE.is_file() else {
        "argv": [str(CONDA_EXE), "env", "list"],
        "exit_code": 127,
        "stdout": "",
        "stderr": "conda.exe absent",
    }
    agent_probe_code = (
        "import importlib.util,json,sys;"
        f"names={list(MODULES)!r};"
        "print(sys.version);"
        "print(json.dumps({n:importlib.util.find_spec(n) is not None for n in names},sort_keys=True))"
    )
    agent_probe = run(str(AGENT_PYTHON), "-c", agent_probe_code) if AGENT_PYTHON.is_file() else {
        "argv": [str(AGENT_PYTHON), "-c", agent_probe_code],
        "exit_code": 127,
        "stdout": "",
        "stderr": "agent python absent",
    }

    environment_versions: list[dict[str, object]] = []
    python_paths = [CONDA_ROOT / "python.exe"]
    python_paths.extend(sorted(ENVS_ROOT.glob("*/python.exe")))
    python_3813_available = False
    for python_path in python_paths:
        result = run(str(python_path), "--version")
        version = str(result["stdout"] or result["stderr"])
        environment_versions.append(
            {
                "path": str(python_path),
                "exit_code": result["exit_code"],
                "version": version,
            }
        )
        if "Python 3.8.13" in version:
            python_3813_available = True

    disk = shutil.disk_usage(Path.cwd())
    payload = {
        "schema": "p9-webshop-toolchain-inventory/v1",
        "windows_conda_root": str(CONDA_ROOT),
        "conda_executable_exists": CONDA_EXE.is_file(),
        "conda_env_list": conda_env_list,
        "agent_environment_path": str(AGENT_PYTHON.parent),
        "agent_python_exists": AGENT_PYTHON.is_file(),
        "agent_probe": agent_probe,
        "environment_python_versions": environment_versions,
        "python_3_8_13_available": python_3813_available,
        "wsl_tools": {name: shutil.which(name) for name in WSL_TOOLS},
        "wsl_python3": run("python3", "--version"),
        "java": run("java", "-version"),
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
        "planned_p9_a2_environment": "webshop38",
        "p9_a1_environment_created_or_modified": False,
        "dependency_install_performed": False,
    }
    passed = (
        payload["conda_executable_exists"]
        and conda_env_list["exit_code"] == 0
        and payload["agent_python_exists"]
        and agent_probe["exit_code"] == 0
        and not python_3813_available
        and payload["planned_p9_a2_environment"] == "webshop38"
    )
    payload["result"] = "PASS" if passed else "FAIL"
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
