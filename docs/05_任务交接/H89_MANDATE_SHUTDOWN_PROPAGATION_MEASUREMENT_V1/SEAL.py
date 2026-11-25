"""Evaluator-only governance sealing and immutable input audit."""
from datetime import datetime, timezone
import hashlib
from importlib import util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
H88 = TASK.with_name('H88_STORED_CONFIRMATION_WITHDRAWAL_V1')
MAP = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
OLD_MAP = 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r147.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def postcheck_h88():
    accepted = read(H88 / 'evidence/evaluator/ACCEPTANCE.json')
    for name, digest in accepted['submission'].items():
        assert sha(ROOT / name) == digest, name
    identical = []
    for index in range(1, 5):
        name = f'EV-{index:02d}.stdout.log'
        assert (H88 / 'evidence/l2-attempt-1' / name).read_bytes() == (
            H88 / 'evidence/evaluator/l3' / ('RV-' + name)).read_bytes()
        identical.append(name)
    triplets = 0
    for meta_path in (H88 / 'evidence/evaluator').rglob('*.meta.json'):
        meta = read(meta_path)
        assert meta['exit_code'] == 0
        for stream in ('stdout', 'stderr'):
            path = meta_path.parent / meta[stream + '_path']
            assert sha(path) == meta[stream + '_sha256']
            assert len(path.read_bytes()) == meta[stream + '_bytes']
        triplets += 1
    assert triplets == 5
    result = {'accepted_files_unchanged': len(accepted['submission']),
              'l2_l3_identical_stdout': identical, 'independent_triplets_verified': triplets,
              'l3_gate_sha256': sha(H88 / 'evidence/evaluator/l3/L3-GATE.json'),
              'review_sha256': sha(H88 / 'REVIEW.md'),
              'original_map_sha256': sha(ROOT / OLD_MAP),
              'completed_at_utc': datetime.now(timezone.utc).isoformat()}
    assert result['original_map_sha256'] == accepted['map_sha256']
    write(H88 / 'evidence/evaluator/POSTCHECK.json', result)
    return result


def seal():
    old = read(H88 / 'FREEZE.json')
    protected = {}
    for name, digest in old['files'].items():
        target = OLD_MAP if name == MAP else name
        assert sha(ROOT / target) == digest, target
        protected[target] = digest
    accepted = read(H88 / 'evidence/evaluator/ACCEPTANCE.json')
    for name, digest in accepted['submission'].items():
        assert sha(ROOT / name) == digest, name
        protected[name] = digest
    spec = util.spec_from_file_location('h89_frozen_check', TASK / 'CHECK.py')
    check = util.module_from_spec(spec)
    spec.loader.exec_module(check)
    source_files = check.source_set()
    for name in source_files:
        protected[name] = sha(ROOT / name)
    for directory in (H88, TASK):
        for path in directory.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.name != 'INPUTS.json':
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    protected[MAP] = sha(ROOT / MAP)
    protected[OLD_MAP] = sha(ROOT / OLD_MAP)
    for name in ('SKILL.md', 'scripts/run_validation.py', 'scripts/capture_evidence.py',
                 'scripts/validate_workflow.py'):
        relative = '../localagent-common/skills/evaluator-executor-workflow/' + name
        protected[relative] = sha(ROOT / relative)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == old['head']
    write(TASK / 'INPUTS.json', {'head': head, 'source_files': source_files,
          'files': dict(sorted(protected.items())),
          'governance_alias': {MAP + '@2026-11-24-r147': OLD_MAP},
          'task_id': TASK.name, 'map_revision': '2026-11-25-r148',
          'note': 'H88 accepted product inherited read-only; CURRENT and future execution evidence are mutable.'})
    print(json.dumps({'protected_files': len(protected), 'manifest_sha256': sha(TASK / 'INPUTS.json')}))


if __name__ == '__main__':
    {'postcheck-h88': postcheck_h88, 'seal': seal}[sys.argv[1]]()
