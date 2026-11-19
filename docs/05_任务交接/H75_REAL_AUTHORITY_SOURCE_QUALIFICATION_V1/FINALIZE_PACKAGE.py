"""Materialize locks/snapshots, without runtime or executable downloads."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
NEXT = P.parent / "H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1"
META = P / "evidence/continuation/20261116T091438Z/ASSET_METADATA.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive():
    dest = P / "references/before_owner_completion"
    dest.mkdir(parents=True, exist_ok=True)
    sources = {"CONTRACT.md": P / "CONTRACT.md", "CURRENT.md": ROOT / "CURRENT.md", "REMOTE_HANDOFF.md": ROOT / "REMOTE_HANDOFF.md", "PROJECT_BOTTLENECK_MAP_r127.md": ROOT / "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md", "QUALIFICATION.md": P / "QUALIFICATION.md", "RUNTIME_SCOPE_DRAFT.md": P / "RUNTIME_SCOPE_DRAFT.md"}
    for name, source in sources.items():
        if not (dest / name).exists():
            shutil.copyfile(source, dest / name)
    target = ROOT / "docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261116_r127.md"
    if not target.exists():
        shutil.copyfile(sources["PROJECT_BOTTLENECK_MAP_r127.md"], target)


def locks():
    meta = json.loads(META.read_text(encoding="utf-8"))
    release = next(a for a in meta["spire"]["assets"] if a["name"] == "spire-1.16.0-linux-amd64-musl.tar.gz")
    files = [{"filename": release["name"], "url": release["browser_download_url"], "size": release["size"], "sha256": release["digest"].removeprefix("sha256:"), "license": "Apache-2.0", "role": "issuer_agent_binaries"}]
    requirements = []
    for package in ("cryptography", "cffi", "pycparser"):
        item = meta[package]
        assert len(item["wheels"]) == 1
        wheel = item["wheels"][0]
        files.append({**wheel, "license": item["license_expression"], "role": "holder_signing_dependency", "package": package, "version": item["version"]})
        requirements.append(package + "==" + item["version"] + " --hash=sha256:" + wheel["sha256"])
    lock = {"schema": "h76-asset-lock/v1", "metadata_only": True, "platform": "linux/amd64", "observed_utc": meta["observed_utc"], "spire_version": "1.16.0", "spire_source_commit": meta["spire"]["source_commit"], "public_metadata_evidence": META.relative_to(ROOT).as_posix(), "public_metadata_sha256": sha(META), "files": files, "python_image": meta["python_image"], "image_reference": "docker.io/library/python@" + meta["python_image"]["linux_amd64_digest"], "file_body_bytes_first_attempt": sum(x["size"] for x in files), "estimated_image_layer_compressed_bytes": meta["python_image"]["compressed_layer_bytes"], "estimated_first_transfer_body_bytes": sum(x["size"] for x in files) + meta["python_image"]["compressed_layer_bytes"], "actual_runtime_download_bytes": "NOT_RUN", "docker_internal_wire_bytes": "UNKNOWN", "licenses": {"spire": "Apache-2.0, fixed source LICENSE archived", "python_image_recipe": "MIT; https://github.com/docker-library/python/blob/master/LICENSE", "python_runtime": "PSF-2.0 and bundled notices; verify image LICENSE", "base_os": "Debian mixed component licenses; no complete transitive audit or production claim", "wheels": "PyPI license_expression locked; inspect downloaded .dist-info/licenses before execution"}, "fixed_sources": meta["fixed_sources"], "metadata_failure_preservation": {"initial_attempt_metadata": (P / "evidence/continuation/ASSET_METADATA.json").relative_to(ROOT).as_posix(), "initial_recorded_body_bytes": 41738, "initial_omitted_size_limited_body_read_bytes": 2097153, "correction": "initial summary omitted rejected large body; actual read counted here, original retained", "second_attempt_recorded_body_bytes": meta["http_response_body_bytes"]}}
    write_json(NEXT / "ASSET_LOCK.json", lock)
    (NEXT / "requirements.lock").write_text("\n".join(requirements) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "file_bytes": lock["file_body_bytes_first_attempt"], "estimated_plus_image_bytes": lock["estimated_first_transfer_body_bytes"]}))


def freeze():
    import yaml
    plan = yaml.safe_load((NEXT / "VALIDATION_PLAN.yaml").read_text(encoding="utf-8"))
    assert plan["task_id"] == NEXT.name and len(plan["checks"]) == 6
    assert {a for check in plan["checks"] for a in check["ac"]} == {"AC-" + str(i).zfill(2) for i in range(1, 9)}
    assert all(check["mandatory"] and check["expected_exit_code"] == 0 for check in plan["checks"])
    for name in ("CHECK.py", "BOOTSTRAP.py"):
        ast.parse((NEXT / name).read_text(encoding="utf-8"))
    mutable = {"CURRENT.md", "REMOTE_HANDOFF.md", "docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md"}
    paths = subprocess.check_output(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    prefix = NEXT.relative_to(ROOT).as_posix() + "/"
    protected = {rel: sha(ROOT / rel) for rel in sorted(set(filter(None, paths))) if not rel.startswith(prefix) and rel not in mutable and (ROOT / rel).is_file()}
    for path in (P / "evidence").rglob("*"):
        if path.is_file():
            protected[path.relative_to(ROOT).as_posix()] = sha(path)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    write_json(NEXT / "BASELINE.json", {"head": head, "protected": protected, "mutable_governance": sorted(mutable), "pre_existing_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True), "runtime_status": "NOT_RUN"})
    names = ("CONTRACT.md", "RUNTIME_PROTOCOL.md", "REVIEW_PROCEDURE.md", "NEGATIVE_ORACLES.json", "VALIDATION_PLAN.yaml", "ASSET_LOCK.json", "requirements.lock", "CHECK.py", "BOOTSTRAP.py", "DESIGN_CHECK.py", "AUTHORIZATION_REQUEST.md", "BASELINE.json")
    write_json(NEXT / "FREEZE.json", {"schema": "h76-technical-content-freeze/v1", "authority": "PENDING; runtime prohibited", "contract_state": "DRAFT_CONTRACT", "files": {name: sha(NEXT / name) for name in names}})
    print(json.dumps({"syntax": "PASS", "plan": "6 checks / 8 AC mapped", "protected": len(protected), "technical_files": len(names), "runtime": "NOT_RUN"}))


if __name__ == "__main__":
    {"archive": archive, "locks": locks, "freeze": freeze}[sys.argv[1]]()
