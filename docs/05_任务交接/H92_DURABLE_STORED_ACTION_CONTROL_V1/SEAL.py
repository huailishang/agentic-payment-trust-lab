"""Freeze the accepted H91 baseline and the H92 two-file capability scope."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H91_SHUTDOWN_INFLIGHT_ORDERING_MEASUREMENT_V1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = TASK / 'INPUTS.json'
    assert not destination.exists(), 'do not overwrite a frozen lock'
    prior = json.loads((PARENT / 'SCENARIO_INPUTS.json').read_text(encoding='utf-8'))
    accepted = json.loads((PARENT / 'evidence/scenario/evaluator/ACCEPTANCE.json').read_text(encoding='utf-8'))
    post = json.loads((PARENT / 'evidence/scenario/evaluator/POSTCHECK.json').read_text(encoding='utf-8'))
    assert post['result'] == 'PASS' and post['accepted_immutable_count'] == 62
    mutable = {name: sha(ROOT / name) for name in prior['inherited_product_diff']}
    assert len(mutable) == 2
    current_map = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
    archived_map = 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261125_r152.md'
    files = {}
    for name, digest in (prior['files'] | accepted['immutable_files']).items():
        mapped = archived_map if name == current_map else name
        assert sha(ROOT / mapped) == digest, mapped
        if name not in mutable:
            files[mapped] = digest
    for path in PARENT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            files[path.relative_to(ROOT).as_posix()] = sha(path)
    for path in TASK.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            files[path.relative_to(ROOT).as_posix()] = sha(path)
    files[current_map] = sha(ROOT / current_map)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == prior['head']
    manifest = {'task_id': TASK.name, 'head': head, 'map_revision': '2026-11-25-r153',
                'active_bottleneck_id': 'B-27', 'source_files': prior['source_files'],
                'files': dict(sorted(files.items())), 'mutable': mutable,
                'historical_map_alias': {current_map: archived_map},
                'formal_executor_l2': 0, 'formal_evaluator_l3': 0}
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {'at': datetime.now(timezone.utc).isoformat(), 'frozen_manifest_sha256': sha(destination),
              'protected': len(files), 'mutable': mutable, 'head': head, 'map_revision': '2026-11-25-r153',
              'product_implementation': 'NOT_STARTED', 'l2': 0, 'l3': 0,
              'baseline': 'three native methods absent; H91 accepted matrix is unchanged baseline',
              'active_minutes': 'UNKNOWN', 'external_cost': 0, 'result': 'PASS'}
    prep = TASK / 'evidence/preparation'
    prep.mkdir(parents=True, exist_ok=True)
    (prep / 'FREEZE.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
