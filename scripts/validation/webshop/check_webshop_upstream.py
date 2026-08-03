from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXPECTED_ORIGIN = "https://github.com/princeton-nlp/WebShop.git"
EXPECTED_COMMIT = "64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd"
REQUIRED_FILES = (
    "README.md",
    "LICENSE.md",
    "setup.sh",
    "requirements.txt",
    "web_agent_site/envs/__init__.py",
    "web_agent_site/envs/web_agent_text_env.py",
    "web_agent_site/engine/engine.py",
)


@dataclass(frozen=True)
class ContractCheck:
    name: str
    path: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class GitCommandResult:
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WebShopUpstreamReport:
    schema: str
    generated_at_utc: str
    checkout_path: str
    expected_origin: str
    actual_origin: str | None
    expected_commit: str
    actual_commit: str | None
    detached_head: bool
    branch_context: tuple[str, ...]
    tag_context: tuple[str, ...]
    license: str | None
    required_files: dict[str, dict[str, Any]]
    contracts: tuple[ContractCheck, ...]
    acquisition_statements: dict[str, bool]
    overall_pass: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["contracts"] = [asdict(item) for item in self.contracts]
        return payload


class SourceContractError(ValueError):
    """Raised when a source file cannot be inspected safely."""


def _run_git(checkout: Path, *args: str) -> GitCommandResult:
    result = subprocess.run(
        ("git", "-C", str(checkout), *args),
        text=True,
        capture_output=True,
        check=False,
    )
    return GitCommandResult(
        exit_code=result.returncode,
        stdout=result.stdout.strip(),
        stderr=result.stderr.strip(),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceContractError(f"cannot read UTF-8 source: {path}: {exc}") from exc


def _parse_python(path: Path) -> tuple[str, ast.Module]:
    source = _read_text(path)
    try:
        return source, ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise SourceContractError(f"cannot parse Python source: {path}: {exc}") from exc


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _find_method(class_node: ast.ClassDef | None, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    if class_node is None:
        return None
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _source_for_node(source: str, node: ast.AST | None) -> str:
    if node is None:
        return ""
    segment = ast.get_source_segment(source, node)
    return segment or ""


def _compact(source: str) -> str:
    return re.sub(r"\s+", "", source).replace('"', "'")


def _registered_text_environment(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        if function_name != "register":
            continue
        keywords = {
            keyword.arg: keyword.value
            for keyword in node.keywords
            if keyword.arg is not None
        }
        identifier = keywords.get("id")
        entry_point = keywords.get("entry_point")
        if (
            isinstance(identifier, ast.Constant)
            and identifier.value == "WebAgentTextEnv-v0"
            and isinstance(entry_point, ast.Constant)
            and entry_point.value == "web_agent_site.envs:WebAgentTextEnv"
        ):
            return True
    return False


def _end_button_value(tree: ast.Module) -> str | None:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: Iterable[ast.expr]
            value: ast.expr | None
            if isinstance(node, ast.Assign):
                targets = node.targets
                value = node.value
            else:
                targets = (node.target,)
                value = node.value
            if any(isinstance(target, ast.Name) and target.id == "END_BUTTON" for target in targets):
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    return value.value
                return None
    return None


def _append_check(
    checks: list[ContractCheck],
    name: str,
    path: Path,
    passed: bool,
    success_detail: str,
    failure_detail: str,
) -> None:
    checks.append(
        ContractCheck(
            name=name,
            path=path.as_posix(),
            passed=passed,
            detail=success_detail if passed else failure_detail,
        )
    )


def inspect_checkout(
    checkout: Path,
    *,
    expected_origin: str = EXPECTED_ORIGIN,
    expected_commit: str = EXPECTED_COMMIT,
) -> WebShopUpstreamReport:
    checkout = checkout.resolve()
    checks: list[ContractCheck] = []

    checkout_exists = checkout.is_dir()
    _append_check(
        checks,
        "checkout_directory",
        checkout,
        checkout_exists,
        "checkout directory exists",
        f"missing checkout directory: {checkout}",
    )

    git_directory = checkout / ".git"
    git_exists = git_directory.exists()
    _append_check(
        checks,
        "git_checkout",
        git_directory,
        git_exists,
        "Git metadata exists",
        f"missing Git metadata: {git_directory}",
    )

    origin_result = _run_git(checkout, "remote", "get-url", "origin") if git_exists else GitCommandResult(1, "", "missing .git")
    actual_origin = origin_result.stdout if origin_result.exit_code == 0 else None
    origin_ok = actual_origin == expected_origin
    _append_check(
        checks,
        "official_origin",
        git_directory / "config",
        origin_ok,
        f"origin matches {expected_origin}",
        f"origin mismatch in {git_directory / 'config'}: expected {expected_origin!r}, actual {actual_origin!r}",
    )

    head_result = _run_git(checkout, "rev-parse", "HEAD") if git_exists else GitCommandResult(1, "", "missing .git")
    actual_commit = head_result.stdout if head_result.exit_code == 0 else None
    commit_ok = actual_commit == expected_commit
    _append_check(
        checks,
        "pinned_commit",
        git_directory / "HEAD",
        commit_ok,
        f"HEAD matches pinned commit {expected_commit}",
        f"commit mismatch at {git_directory / 'HEAD'}: expected {expected_commit}, actual {actual_commit}",
    )

    symbolic_result = _run_git(checkout, "symbolic-ref", "-q", "HEAD") if git_exists else GitCommandResult(1, "", "missing .git")
    detached_head = symbolic_result.exit_code != 0 and actual_commit is not None
    _append_check(
        checks,
        "detached_head",
        git_directory / "HEAD",
        detached_head,
        "checkout is detached from moving branches",
        f"checkout is not detached at {git_directory / 'HEAD'}",
    )

    status_result = _run_git(checkout, "status", "--porcelain") if actual_commit else GitCommandResult(1, "", "missing HEAD")
    clean_worktree = status_result.exit_code == 0 and not status_result.stdout
    _append_check(
        checks,
        "clean_worktree",
        checkout,
        clean_worktree,
        "upstream checkout has no local source modifications",
        f"upstream checkout contains local modifications: {checkout}: {status_result.stdout}",
    )

    branch_result = _run_git(checkout, "branch", "-r", "--contains", "HEAD") if actual_commit else GitCommandResult(1, "", "missing HEAD")
    tag_result = _run_git(checkout, "tag", "--points-at", "HEAD") if actual_commit else GitCommandResult(1, "", "missing HEAD")
    branch_context = tuple(line.strip() for line in branch_result.stdout.splitlines() if line.strip())
    tag_context = tuple(line.strip() for line in tag_result.stdout.splitlines() if line.strip())

    required_file_manifest: dict[str, dict[str, Any]] = {}
    for relative in REQUIRED_FILES:
        path = checkout / relative
        exists = path.is_file()
        required_file_manifest[relative] = {
            "exists": exists,
            "sha256": _sha256(path) if exists else None,
        }
        _append_check(
            checks,
            f"required_file:{relative}",
            path,
            exists,
            "required upstream file exists",
            f"missing required upstream file: {path}",
        )

    license_path = checkout / "LICENSE.md"
    license_name: str | None = None
    if license_path.is_file():
        license_text = _read_text(license_path)
        if "MIT License" in license_text and "Permission is hereby granted" in license_text:
            license_name = "MIT"
    _append_check(
        checks,
        "mit_license",
        license_path,
        license_name == "MIT",
        "MIT license text identified",
        f"MIT license markers missing or changed: {license_path}",
    )

    init_path = checkout / "web_agent_site/envs/__init__.py"
    text_env_path = checkout / "web_agent_site/envs/web_agent_text_env.py"
    engine_path = checkout / "web_agent_site/engine/engine.py"
    readme_path = checkout / "README.md"
    setup_path = checkout / "setup.sh"

    init_tree: ast.Module | None = None
    text_env_source = ""
    text_env_tree: ast.Module | None = None
    engine_tree: ast.Module | None = None
    try:
        if init_path.is_file():
            _, init_tree = _parse_python(init_path)
        if text_env_path.is_file():
            text_env_source, text_env_tree = _parse_python(text_env_path)
        if engine_path.is_file():
            _, engine_tree = _parse_python(engine_path)
    except SourceContractError as exc:
        checks.append(
            ContractCheck(
                name="source_parse",
                path=str(checkout),
                passed=False,
                detail=str(exc),
            )
        )

    registration_ok = init_tree is not None and _registered_text_environment(init_tree)
    _append_check(
        checks,
        "text_environment_registration",
        init_path,
        registration_ok,
        "WebAgentTextEnv-v0 registration targets WebAgentTextEnv",
        f"missing WebAgentTextEnv-v0 registration contract: {init_path}",
    )

    text_env_class = _find_class(text_env_tree, "WebAgentTextEnv") if text_env_tree is not None else None
    _append_check(
        checks,
        "web_agent_text_env_class",
        text_env_path,
        text_env_class is not None,
        "WebAgentTextEnv class exists",
        f"missing class WebAgentTextEnv: {text_env_path}",
    )

    step_method = _find_method(text_env_class, "step")
    reset_method = _find_method(text_env_class, "reset")
    _append_check(
        checks,
        "web_agent_text_env_step",
        text_env_path,
        step_method is not None,
        "WebAgentTextEnv.step(action) exists",
        f"missing WebAgentTextEnv.step(action): {text_env_path}",
    )
    _append_check(
        checks,
        "web_agent_text_env_reset",
        text_env_path,
        reset_method is not None,
        "WebAgentTextEnv.reset(...) exists",
        f"missing WebAgentTextEnv.reset(...): {text_env_path}",
    )

    step_source = _source_for_node(text_env_source, step_method)
    action_grammar_ok = "search[keywords]" in step_source and "click[value]" in step_source
    _append_check(
        checks,
        "action_grammar",
        text_env_path,
        action_grammar_ok,
        "step contract documents search[...] and click[...] grammar",
        f"missing search[...] or click[...] action grammar: {text_env_path}",
    )

    end_button = _end_button_value(engine_tree) if engine_tree is not None else None
    _append_check(
        checks,
        "end_button",
        engine_path,
        end_button == "Buy Now",
        "END_BUTTON resolves to Buy Now",
        f"END_BUTTON must resolve to 'Buy Now' in {engine_path}; actual={end_button!r}",
    )

    sim_server_class = _find_class(text_env_tree, "SimServer") if text_env_tree is not None else None
    receive_method = _find_method(sim_server_class, "receive")
    done_method = _find_method(sim_server_class, "done")
    receive_compact = _compact(_source_for_node(text_env_source, receive_method))
    done_compact = _compact(_source_for_node(text_env_source, done_method))

    receive_route_ok = all(
        marker in receive_compact
        for marker in (
            "clickable_name==END_BUTTON.lower()",
            "self.done(",
            "status['done']=True",
        )
    )
    _append_check(
        checks,
        "buy_now_routes_to_done",
        text_env_path,
        receive_method is not None and receive_route_ok,
        "SimServer.receive routes Buy Now to done() and marks terminal status",
        f"missing Buy Now -> done() terminal route in SimServer.receive: {text_env_path}",
    )

    done_contract_ok = all(
        marker in done_compact
        for marker in (
            "session['actions']['purchase']+=1",
            "get_reward(",
            "['done']=True",
            "['reward']=reward",
        )
    )
    _append_check(
        checks,
        "done_records_purchase_reward_terminal_state",
        text_env_path,
        done_method is not None and done_contract_ok,
        "SimServer.done records purchase, calculates reward and sets terminal state",
        f"missing purchase/reward/terminal-state contract in SimServer.done: {text_env_path}",
    )

    readme_text = _read_text(readme_path) if readme_path.is_file() else ""
    setup_text = _read_text(setup_path) if setup_path.is_file() else ""
    small_setup_ok = (
        "-d small" in readme_text
        and "1000" in readme_text
        and "small" in setup_text
        and "1000" in setup_text
    )
    _append_check(
        checks,
        "small_1000_product_path",
        readme_path,
        small_setup_ok,
        "small setup path and 1000-product subset are documented",
        f"missing small/1000-product setup documentation in {readme_path} or {setup_path}",
    )

    overall_pass = all(item.passed for item in checks)
    return WebShopUpstreamReport(
        schema="webshop-upstream-preflight/v1",
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        checkout_path=str(checkout),
        expected_origin=expected_origin,
        actual_origin=actual_origin,
        expected_commit=expected_commit,
        actual_commit=actual_commit,
        detached_head=detached_head,
        branch_context=branch_context,
        tag_context=tag_context,
        license=license_name,
        required_files=required_file_manifest,
        contracts=tuple(checks),
        acquisition_statements={
            "dependency_installed": False,
            "dataset_downloaded": False,
            "model_downloaded": False,
            "service_started": False,
            "webshop_imported": False,
            "browser_started": False,
            "payment_or_testnet_action": False,
        },
        overall_pass=overall_pass,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a pinned WebShop checkout by Git and source inspection only.",
    )
    parser.add_argument("checkout", type=Path, help="Path to the WebShop Git checkout")
    parser.add_argument("--expected-origin", default=EXPECTED_ORIGIN)
    parser.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    parser.add_argument("--manifest-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = inspect_checkout(
        args.checkout,
        expected_origin=args.expected_origin,
        expected_commit=args.expected_commit,
    )
    payload = report.to_dict()
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    print(serialized)
    if args.manifest_out is not None:
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(serialized + "\n", encoding="utf-8")
    return 0 if report.overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
