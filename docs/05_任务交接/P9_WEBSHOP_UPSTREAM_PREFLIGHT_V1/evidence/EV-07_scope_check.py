from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


BASELINE = "8acaa9e4319240d258f14d8a23b1f15cc71d09b6"
EXPECTED_ORIGIN = "https://github.com/princeton-nlp/WebShop.git"
EXPECTED_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
CHECKOUT = Path("local_sources/third_party/webshop")
TASK_ROOT = Path("docs/05_任务交接/P9_WEBSHOP_UPSTREAM_PREFLIGHT_V1")
CHECKER = Path("scripts/validation/webshop/check_webshop_upstream.py")
TEST = Path("tests/test_webshop_upstream_contract.py")
REFERENCE = Path("docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md")
REPORT = TASK_ROOT / "REPORT.md"
MANIFEST = TASK_ROOT / "evidence/webshop_upstream_manifest.json"
REQUIRED_TASK_FILES = (
    CHECKER,
    TEST,
    REPORT,
    MANIFEST,
    TASK_ROOT / "evidence/EV-01_acquisition.py",
    TASK_ROOT / "evidence/EV-04_toolchain_inventory.py",
    TASK_ROOT / "evidence/EV-07_scope_check.py",
)
UPSTREAM_HASHES = {
    "README.md": "79b7a90a1413a52deb53142b5bbd81ecf40f61743bd4601c2835e91375898ec0",
    "LICENSE.md": "8872dbf8660b00890b5e07ce1ea1f7a44fa7ae4e1857da56caba172b51dab3cb",
    "setup.sh": "0df1dbe7673b94e161b2d9064037af35f7fee3eb1d8131c63b21dd3385323912",
    "requirements.txt": "b4e83b7e9c670c724215fcb79e43f52f591de354a8f70870ba4553c88de26d2d",
    "web_agent_site/envs/__init__.py": "7cdf100d019fd715d605ff0cd0f0d3d4285d7f7b2dbe4e4634e9a1266ab5e854",
    "web_agent_site/envs/web_agent_text_env.py": "f4efee238c2a69ad76ff5372716a16051c67ea0351c7006491834822ea9afda3",
    "web_agent_site/engine/engine.py": "9b86ffc82951124f5c4a7eb8103de14100dbee11ba8869951ed6fb8feaeef804",
}
FORBIDDEN_IMPORT_ROOTS = {
    "web_agent_site",
    "gym",
    "flask",
    "torch",
    "spacy",
    "pyserini",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status_paths() -> list[str]:
    result = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    paths: list[str] = []
    records = result.stdout.decode("utf-8", errors="replace").split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        path = record[3:] if len(record) >= 4 else record
        paths.append(path)
        if record[:2].strip().startswith(("R", "C")) and index < len(records):
            index += 1
    return paths


def allowed_task_path(path_text: str) -> bool:
    path = Path(path_text)
    return (
        path == CHECKER
        or path == TEST
        or path == REFERENCE
        or path == Path("CURRENT.md")
        or path == Path(".gitignore")
        or path == TASK_ROOT
        or TASK_ROOT in path.parents
    )


def whitespace_findings(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            findings.append(f"{path}:{number}: trailing whitespace")
    if text and not text.endswith("\n"):
        findings.append(f"{path}: missing final newline")
    return findings


def forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings: list[str] = []
    for node in ast.walk(tree):
        roots: list[str] = []
        if isinstance(node, ast.Import):
            roots = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots = [node.module.split(".", 1)[0]]
        for root in roots:
            if root in FORBIDDEN_IMPORT_ROOTS:
                findings.append(f"{path}:{getattr(node, 'lineno', '?')}: forbidden upstream runtime import {root}")
    return findings


def main() -> int:
    failures: list[str] = []
    head = run("git", "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    print(f"BASELINE={BASELINE}")
    print(f"HEAD_BASELINE_UNCHANGED={head == BASELINE}")
    if head != BASELINE:
        failures.append("main repository HEAD changed")

    missing = [str(path) for path in REQUIRED_TASK_FILES if not path.is_file()]
    print(f"MISSING_TASK_FILES={missing}")
    failures.extend(f"missing task file: {path}" for path in missing)

    origin = run("git", "-C", str(CHECKOUT), "remote", "get-url", "origin")
    checkout_head = run("git", "-C", str(CHECKOUT), "rev-parse", "HEAD")
    symbolic = run("git", "-C", str(CHECKOUT), "symbolic-ref", "-q", "HEAD")
    checkout_status = run("git", "-C", str(CHECKOUT), "status", "--porcelain")
    ignored = run("git", "check-ignore", "-q", str(CHECKOUT))
    tracked_local = run("git", "ls-files", "local_sources")
    print(f"CHECKOUT_ORIGIN={origin.stdout.strip()}")
    print(f"CHECKOUT_HEAD={checkout_head.stdout.strip()}")
    print(f"CHECKOUT_DETACHED={symbolic.returncode != 0}")
    print(f"CHECKOUT_CLEAN={checkout_status.returncode == 0 and not checkout_status.stdout.strip()}")
    print(f"CHECKOUT_IGNORED={ignored.returncode == 0}")
    print(f"TRACKED_LOCAL_SOURCES={tracked_local.stdout.splitlines()}")
    if origin.stdout.strip() != EXPECTED_ORIGIN:
        failures.append("checkout origin mismatch")
    if checkout_head.stdout.strip() != EXPECTED_COMMIT:
        failures.append("checkout commit mismatch")
    if symbolic.returncode == 0:
        failures.append("checkout is not detached")
    if checkout_status.returncode != 0 or checkout_status.stdout.strip():
        failures.append("checkout contains local modifications")
    if ignored.returncode != 0:
        failures.append("checkout is not ignored by main repository")
    if tracked_local.stdout.strip():
        failures.append("third-party local_sources content is tracked")

    paths = status_paths()
    task_related = [
        path
        for path in paths
        if "webshop" in path.lower()
        or path.startswith(TASK_ROOT.as_posix())
        or path in {CHECKER.as_posix(), TEST.as_posix(), REFERENCE.as_posix(), "CURRENT.md"}
    ]
    unexpected = [path for path in task_related if not allowed_task_path(path)]
    escaped_local = [path for path in paths if path.startswith("local_sources/")]
    product_paths = [path for path in task_related if path.startswith("src/agentic_payment_experiment/")]
    print(f"TASK_RELATED_STATUS_PATHS={task_related}")
    print(f"UNEXPECTED_TASK_PATHS={unexpected}")
    print(f"ESCAPED_LOCAL_SOURCES_PATHS={escaped_local}")
    print(f"P9_PRODUCT_PATHS={product_paths}")
    failures.extend(f"unexpected task path: {path}" for path in unexpected)
    failures.extend(f"ignored source escaped into main status: {path}" for path in escaped_local)
    failures.extend(f"product path changed by P9: {path}" for path in product_paths)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
    print(f"MANIFEST_OVERALL_PASS={manifest.get('overall_pass')}")
    print(f"MANIFEST_ORIGIN={manifest.get('actual_origin')}")
    print(f"MANIFEST_COMMIT={manifest.get('actual_commit')}")
    if manifest.get("overall_pass") is not True:
        failures.append("upstream manifest did not pass")
    if manifest.get("actual_origin") != EXPECTED_ORIGIN:
        failures.append("manifest origin mismatch")
    if manifest.get("actual_commit") != EXPECTED_COMMIT:
        failures.append("manifest commit mismatch")
    for relative, expected_hash in UPSTREAM_HASHES.items():
        actual_hash = manifest.get("required_files", {}).get(relative, {}).get("sha256")
        matches = actual_hash == expected_hash and (CHECKOUT / relative).is_file() and sha256(CHECKOUT / relative) == expected_hash
        print(f"UPSTREAM_HASH {relative} expected={expected_hash} manifest={actual_hash} matches={matches}")
        if not matches:
            failures.append(f"upstream hash mismatch: {relative}")

    authored_files = [CHECKER, TEST, REPORT]
    authored_files.extend(
        path
        for path in TASK_ROOT.rglob("*")
        if path.is_file()
        and path.name != "CONTRACT.md"
        and path.suffix in {".py", ".md", ".json"}
    )
    whitespace: list[str] = []
    for path in sorted(set(authored_files)):
        whitespace.extend(whitespace_findings(path))
    print(f"TASK_WHITESPACE_FINDINGS={len(whitespace)}")
    for finding in whitespace:
        print(f"  {finding}")
    failures.extend(whitespace)

    imports: list[str] = []
    for path in (CHECKER, TEST, TASK_ROOT / "evidence/EV-01_acquisition.py", TASK_ROOT / "evidence/EV-04_toolchain_inventory.py"):
        if path.is_file():
            imports.extend(forbidden_imports(path))
    print(f"FORBIDDEN_UPSTREAM_RUNTIME_IMPORTS={imports}")
    failures.extend(imports)

    print("TASK_FILE_SHA256=")
    for path in sorted(set(authored_files)):
        print(f"  {sha256(path)}  {path.as_posix()}")

    global_check = run("git", "diff", "--check")
    print(f"GLOBAL_GIT_DIFF_CHECK_EXIT={global_check.returncode}")
    if global_check.returncode != 0:
        print("GLOBAL_FINDINGS_CLASSIFICATION=inherited/out-of-scope unless listed in TASK_RELATED_STATUS_PATHS")
        for line in (global_check.stdout + global_check.stderr).splitlines()[:20]:
            print(f"  {line}")

    ai_bridge_exists = Path(".ai-bridge").exists()
    print(f"AI_BRIDGE_EXISTS={ai_bridge_exists}")
    if ai_bridge_exists:
        failures.append("unexpected .ai-bridge directory exists")

    print(f"P9_SCOPE_RESULT={'PASS' if not failures else 'FAIL'}")
    if failures:
        print("FAILURES=")
        for failure in failures:
            print(f"  {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
