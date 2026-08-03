from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path.cwd()
CHECKOUT = REPO / "local_sources" / "third_party" / "webshop"
EXPECTED_ORIGIN = "https://github.com/princeton-nlp/WebShop.git"
EXPECTED_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"


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
    symbolic = run("git", "-C", str(CHECKOUT), "symbolic-ref", "-q", "HEAD")
    checkout_status = run("git", "-C", str(CHECKOUT), "status", "--porcelain")
    ignored = run("git", "check-ignore", "-v", str(CHECKOUT.relative_to(REPO)))
    tracked_local_sources = run("git", "ls-files", "local_sources")
    main_status = run("git", "status", "--porcelain", "--untracked-files=all")

    escaped_local_sources = [
        line
        for line in str(main_status["stdout"]).splitlines()
        if "local_sources/" in line.replace("\\", "/")
    ]
    payload = {
        "schema": "webshop-upstream-acquisition/v1",
        "checkout_path": str(CHECKOUT),
        "checkout_exists": CHECKOUT.is_dir(),
        "git_directory_exists": (CHECKOUT / ".git").exists(),
        "origin": origin,
        "origin_is_official": origin["exit_code"] == 0 and origin["stdout"] == EXPECTED_ORIGIN,
        "head": head,
        "head_is_pinned": head["exit_code"] == 0 and head["stdout"] == EXPECTED_COMMIT,
        "detached_head": symbolic["exit_code"] != 0 and head["exit_code"] == 0,
        "checkout_clean": checkout_status["exit_code"] == 0 and not checkout_status["stdout"],
        "ignored_by_main_repo": ignored["exit_code"] == 0,
        "ignore_evidence": ignored,
        "tracked_local_sources": tracked_local_sources["stdout"].splitlines(),
        "escaped_local_sources_status": escaped_local_sources,
        "dependency_install_performed": False,
        "setup_script_executed": False,
        "external_dataset_or_model_download_performed": False,
        "service_started": False,
        "webshop_imported": False,
        "payment_or_testnet_action": False,
    }
    passed = all(
        (
            payload["checkout_exists"],
            payload["git_directory_exists"],
            payload["origin_is_official"],
            payload["head_is_pinned"],
            payload["detached_head"],
            payload["checkout_clean"],
            payload["ignored_by_main_repo"],
            not payload["tracked_local_sources"],
            not payload["escaped_local_sources_status"],
        )
    )
    payload["result"] = "PASS" if passed else "FAIL"
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
