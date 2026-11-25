"""Freeze H90 inputs while preserving the exact accepted H89 snapshot."""
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PARENT = TASK.with_name('H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1')
MAP = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
ARCHIVE = 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261125_r148.md'
FLUXA = 'docs/reference/05_产业与机构资料/fluxa/FluxA_AgentCard_授权到支付凭证_参考评估_20261125.md'
MUTABLE = ['src/agentic_payment_experiment/adapters/stripe_checkout.py',
           'src/agentic_payment_experiment/stripe_checkout_lab.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    before = load(PARENT / 'INPUTS.json')
    accepted = load(PARENT / 'evidence/evaluator/ACCEPTANCE.json')
    comparison = load(PARENT / 'evidence/evaluator/POSTCHECK.json')
    assert sha(ROOT / ARCHIVE) == accepted['map_sha256'] == before['files'][MAP]
    assert comparison['identical_stdout'] == 6 and comparison['whole_mandate_accepted'] == 0
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == before['head'] == accepted['head']
    for name, digest in accepted['submission'].items():
        assert sha(ROOT / name) == digest, name
    assert sha(PARENT / 'evidence/evaluator/CURRENT.pre_acceptance.md') == accepted['pre_acceptance_router_sha256']
    protected = {}
    mutable = {}
    for name, digest in before['files'].items():
        source = ARCHIVE if name == MAP else name
        assert sha(ROOT / source) == digest, source
        (mutable if source in MUTABLE else protected)[source] = digest
    assert sorted(mutable) == sorted(MUTABLE)
    for directory in (PARENT, TASK):
        for path in directory.rglob('*'):
            if path.is_file() and path != TASK / 'INPUTS.json' and '__pycache__' not in path.parts:
                protected[path.relative_to(ROOT).as_posix()] = sha(path)
    protected[MAP] = sha(ROOT / MAP)
    protected[FLUXA] = sha(ROOT / FLUXA)
    payload = {'task_id': TASK.name, 'head': head, 'map_revision': '2026-11-25-r149',
               'source_files': before['source_files'], 'mutable': mutable,
               'files': dict(sorted(protected.items())),
               'governance_alias': {MAP + '@2026-11-25-r148': ARCHIVE}}
    manifest = TASK / 'INPUTS.json'
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'protected': len(protected), 'mutable': len(mutable), 'sha256': sha(manifest)}))


if __name__ == '__main__':
    main()
