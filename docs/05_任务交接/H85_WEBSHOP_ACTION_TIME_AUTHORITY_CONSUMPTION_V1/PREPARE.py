"""Evaluator-only offline readiness checks and H85 input sealing."""
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import CHECK as C


def expect_rejection(call, expected):
    try:
        call()
    except (ValueError, FileNotFoundError, FileExistsError) as error:
        C.need(expected in str(error), f"unexpected stop: {error}")
        return
    raise ValueError(f"precondition was not enforced: {expected}")


def verify_plan():
    location = importlib.util.spec_from_file_location("h85_validation_runner", C.RUNNER)
    module = importlib.util.module_from_spec(location)
    sys.path.insert(0, str(C.RUNNER.parent))
    sys.modules[location.name] = module
    location.loader.exec_module(module)
    for role in C.ROUTES:
        task_id, checks = module.load_plan(C.ROOT, C.TASK / "VALIDATION_PLAN.yaml", mode=role)
        C.need(task_id == C.TASK.name and len(checks) == 4, "plan shape mismatch")
        C.need(all(check.mandatory and check.expected_exit_code == 0 for check in checks), "plan weakening")
        expected_acs = {f"AC-{n:02}" for n in range(1, 7)}
        C.need({ac for check in checks for ac in check.acs} == expected_acs, "AC mapping mismatch")
        C.need(checks[-1].command[-2:] == ("--role", role), "role-specific command mismatch")


def verify_stops():
    authorize = {
        "task_id": C.TASK.name, "state": "EXECUTING", "current_role": "Executor",
        **dict.fromkeys(C.LOCAL_FLAGS, True),
    }
    expect_rejection(lambda: C.authorize("evaluator", authorize), "role is not active")
    excess = authorize | {"authorization_api_call": True}
    expect_rejection(lambda: C.authorize("executor", excess), "authorization scope drift")
    with patch.dict(C.os.environ, {"H85_FORMAL_ATTEMPT": ""}):
        expect_rejection(C.context, "formal gate reservation required")
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        dispatch = {"attempt": "executor-1", "role": "executor"}
        with patch.object(C, "existing_host") as host, patch.object(C, "invoke_candidate") as run:
            expect_rejection(lambda: C.live("executor", folder, dispatch), "VP-01.json")
            for i, check in enumerate(C.PREREQUISITES, 1):
                C.write_new(folder / f"{check}.json", {"dispatch": dispatch, "check": check})
                C.write_new(folder / f"EV-{i:02}.meta.json", {"exit_code": 1 if i == 3 else 0})
            expect_rejection(lambda: C.live("executor", folder, dispatch), "VP-03 did not pass")
            host.assert_not_called()
            run.assert_not_called()
        with patch.object(C, "existing_host"), patch.object(C, "invoke_candidate") as run:
            (folder / "EV-03.meta.json").write_text('{"exit_code": 0}', encoding="utf-8")
            marker = folder / "executor_LIVE.json"
            C.write_new(marker, dispatch)
            with patch.object(C, "role_live_marker", return_value=marker):
                expect_rejection(lambda: C.live("executor", folder, dispatch), "executor_LIVE.json")
            run.assert_not_called()


def seal():
    prepare = C.TASK / "evidence" / "PREPARATION.json"
    preflight = C.read(prepare)
    C.need(preflight["service_launches"] == preflight["formal_gates"] == 0, "invalid preparation scope")
    C.need(preflight["regressions"] == {"passed": 86, "skipped": 0}, "preparation regression mismatch")
    baseline = C.read(C.EVIDENCE / "BASELINE_PROBE.json")
    C.need(C.sha(C.ROOT / C.CALLER) == baseline["caller_sha256"], "baseline caller drift")
    C.need(C.sha(C.ROOT / baseline["source"]) == baseline["source_sha256"], "P9 input drift")
    C.need(C.sha(C.ROOT / baseline["context"]) == baseline["context_sha256"], "P9 context drift")
    frozen = [C.TASK / name for name in (
        "AUTHORIZATION.json", "BINARY_MEMBER_LOCK.json", "CHECK.py", "CONTRACT.md",
        "EXECUTOR_START.md", "PREPARE.py", "VALIDATION_PLAN.yaml",
        "evidence/BASELINE_PROBE.py", "evidence/BASELINE_PROBE.json",
        "evidence/CURRENT.draft.md", "evidence/PREPARATION.json",
    )]
    map_dir = C.ROOT / "docs/01_项目现状"
    history = [
        map_dir / "PROJECT_BOTTLENECK_MAP.md",
        map_dir / "archive/PROJECT_BOTTLENECK_MAP_20261124_r142.md",
        map_dir / "archive/PROJECT_BOTTLENECK_MAP_20261124_r141.md",
        C.ROOT / baseline["source"],
        C.ROOT / baseline["context"],
        C.RUNNER,
        C.RUNNER.with_name("capture_evidence.py"),
        C.RUNNER.with_name("validate_workflow.py"),
    ]
    for name in (
        "H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1",
        "H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1",
    ):
        history.extend(path for path in (C.TASK.parent / name).rglob("*")
                       if path.is_file() and "__pycache__" not in path.parts)
    for task, name in (
        ("H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1", "WORKLOAD.py"),
        ("H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1", "ASSET_LOCK.json"),
    ):
        history.append(C.TASK.parent / task / name)
    head = C.git("rev-parse", "HEAD").decode().strip()
    C.need(head in (C.TASK / "CONTRACT.md").read_text(encoding="utf-8"), "contract baseline drift")
    C.write_new(C.TASK / "FREEZE.json", {
        "task_id": C.TASK.name,
        "head": head,
        "frozen": {path.relative_to(C.ROOT).as_posix(): C.sha(path) for path in frozen},
        "protected_product": {name: C.sha(C.ROOT / name) for name in sorted(C.product_files())},
        "protected_evidence": {
            Path(C.os.path.relpath(path, C.ROOT)).as_posix(): C.sha(path) for path in sorted(set(history))
        },
    })


def main():
    if sys.argv[1:] == ["seal"]:
        seal()
        return
    C.need(sys.argv[1:] == ["preflight"], "choose preflight or seal")
    verify_plan()
    verify_stops()
    C.existing_host()
    C.write_new(C.EVIDENCE / "PREPARATION.json", {
        "task_id": C.TASK.name,
        "plan_roles_verified": list(C.ROUTES),
        "guard_checks": ["wrong_role", "excess_authority", "missing_reservation",
                         "missing_prerequisite", "failed_prerequisite", "duplicate_live"],
        "cached_archive_sha256_verified": True,
        "regressions": C.regressions(),
        "formal_gates": 0,
        "service_launches": 0,
        "temporary_credentials_issued": 0,
    })
    print(json.dumps(C.read(C.EVIDENCE / "PREPARATION.json")))


if __name__ == "__main__":
    main()
