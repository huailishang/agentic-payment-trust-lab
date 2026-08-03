from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


REPO = Path.cwd()
CHECKOUT = REPO / "local_sources" / "third_party" / "webshop"
EXPECTED_ORIGIN = "https://github.com/princeton-nlp/WebShop.git"
TOOLS = ("python", "python3", "python3.8", "java", "conda", "docker", "podman", "uv", "micromamba", "mamba", "pyenv")


def run(*args: str) -> dict[str, object]:
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    return {
        "argv": list(args),
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main() -> int:
    origin = run("git", "-C", str(CHECKOUT), "remote", "get-url", "origin")
    head = run("git", "-C", str(CHECKOUT), "rev-parse", "HEAD")
    ignored = run("git", "check-ignore", "-q", str(CHECKOUT.relative_to(REPO)))
    disk = shutil.disk_usage(REPO)
    payload = {
        "checkout_path": str(CHECKOUT),
        "checkout_exists": CHECKOUT.exists(),
        "git_directory_exists": (CHECKOUT / ".git").is_dir(),
        "origin": origin,
        "origin_is_official": origin["exit_code"] == 0 and origin["stdout"] == EXPECTED_ORIGIN,
        "head": head,
        "pinned_checkout_present": head["exit_code"] == 0 and str(head["stdout"]).startswith("64fa2a5"),
        "ignored_by_main_repo": ignored["exit_code"] == 0,
        "tools": {name: shutil.which(name) for name in TOOLS},
        "python3_version": run("python3", "--version"),
        "java_version": run("java", "-version"),
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
        "status": "BLOCKED_NETWORK_ACQUISITION",
        "dependency_install_performed": False,
        "dataset_download_performed": False,
        "service_started": False,
        "webshop_imported": False,
        "api_or_model_called": False,
        "payment_or_testnet_action": False,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
