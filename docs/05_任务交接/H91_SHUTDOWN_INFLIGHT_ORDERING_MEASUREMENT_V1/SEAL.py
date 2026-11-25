"""Evaluator preparation: preserve historical map and accepted candidate bytes."""
from importlib import util
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H90_STORED_MANDATE_SHUTDOWN_V1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = TASK / 'INPUTS.json'
    assert not target.exists(), 'initial seal is one-shot; never overwrite a frozen manifest'
    old = json.loads((PARENT / 'INPUTS.json').read_text(encoding='utf-8'))
    accepted = json.loads((PARENT / 'evidence/evaluator/POSTCHECK.json').read_text(encoding='utf-8'))
    map_path = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
    old_map = 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261125_r149.md'
    files = {}
    for name, digest in (old['files'] | accepted['files']).items():
        if name == 'CURRENT.md':
            continue
        mapped = old_map if name == map_path else name
        assert sha(ROOT / mapped) == digest, mapped
        files[mapped] = digest
    for name in old['source_files']:
        files[name] = sha(ROOT / name)
    for path in PARENT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            files[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in ('CONTRACT.md', 'VALIDATION_PLAN.yaml', 'CHECK.py', 'EXECUTOR_START.md', 'SEAL.py'):
        path = TASK / name
        files[path.relative_to(ROOT).as_posix()] = sha(path)
    files[map_path] = sha(ROOT / map_path)
    pcac = 'docs/reference/05_产业与机构资料/pcac/智能体支付应用自律公约_开发指标映射_v1.md'
    files[pcac] = sha(ROOT / pcac)
    manifest = {'task_id': TASK.name, 'head': old['head'], 'map_revision': '2026-11-25-r150',
                'active_bottleneck_id': 'B-27', 'source_files': old['source_files'],
                'inherited_product_diff': sorted(old['mutable']), 'files': dict(sorted(files.items())),
                'historical_map_alias': {map_path: old_map},
                'formal_executor_l2': 0, 'formal_evaluator_l3': 0}
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    out = TASK / 'evidence/preparation'
    out.mkdir(parents=True, exist_ok=True)
    prep = {'at': datetime.now(timezone.utc).isoformat(), 'protected': len(files),
            'inputs_sha256': sha(target), 'historical_map_sha256': sha(ROOT / old_map),
            'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'preflight_observation': {'trace_controls': 2, 'rejected_corrupt_traces': 4,
                                      'fixed_rows': 8, 'product_actions': 0, 'result': 'PASS'},
            'preflight_capture': 'tool-returned text, not a raw stream capture',
            'executor_l2': 0, 'evaluator_l3': 0, 'measurement_matrix': 'NOT_RUN',
            'active_minutes': 'UNKNOWN', 'external_calls': 0, 'product_writes': 0}
    (out / 'PREPARATION.json').write_text(json.dumps(prep, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'protected': len(files), 'frozen_manifest_sha256': sha(target), 'result': 'PASS'}))


if __name__ == '__main__':
    main()
