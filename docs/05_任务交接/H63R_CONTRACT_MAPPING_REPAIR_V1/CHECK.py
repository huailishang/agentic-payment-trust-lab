"""Bounded mapping-repair guardrails; final meaning requires independent L3 review."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = TASK.parent / 'H63_EXTERNAL_TRACE_QUALIFICATION_V1'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def source():
    base = read(TASK / 'BASELINE.json')
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == base['head']
    for name, digest in base['protected'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in base['frozen'].items():
        assert sha(TASK / name) == digest, name
    known = set(base['protected']) | {'CURRENT.md'}
    prefix = TASK.relative_to(ROOT).as_posix() + '/'
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).split(b'\0')
    assert all(n.decode('utf-8') in known or n.decode('utf-8').startswith(prefix) for n in names if n)
    allowed = set(base['frozen']) | {'BASELINE.json', 'MAP.py', 'MAPPING.json', 'ATTEMPT_LEDGER.json', 'REPORT.md', 'REVIEW.md'}
    for path in TASK.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            name = path.relative_to(TASK).as_posix()
            assert name in allowed or name.startswith('evidence/'), name
    print(json.dumps({'protected': len(base['protected']), 'frozen': len(base['frozen'])}))

def validate(data):
    spec = read(TASK / 'SPEC.json')
    old = read(OLD / 'MEASUREMENT.json')
    assert data['task_id'] == TASK.name
    assert [s['sample_id'] for s in data['samples']] == [s['sample_id'] for s in old['samples']]
    for sample, original in zip(data['samples'], old['samples']):
        assert set(sample['contracts']) == set(spec['contracts'])
        for key, rule in spec['contracts'].items():
            item = sample['contracts'][key]
            assert item['contract_name'] == rule['name'] and item['contract_ref'] == rule['ref']
            assert item['input_status'] in {'PARTIAL', 'MISSING'}, 'previews lack complete authoritative contract inputs'
            assert set(rule['missing']) <= set(item['missing_inputs'])
            assert len(item['reason'].strip()) >= 30
            assert isinstance(item['fact_keys'], list)
            assert set(item['fact_keys']) <= set(original['facts'])
            assert all(original['facts'][f]['status'] != 'ABSENT' for f in item['fact_keys'])
            if key == 'P3':
                assert item['input_status'] == 'MISSING' and item['fact_keys'] == [], 'transaction ids do not establish executor identity'
    decision = data['decision']
    assert decision['candidate_classification'] == 'REFERENCE_ONLY'
    assert decision['evidence_level'] == 'TRANSCRIPT_ONLY'
    assert set(spec['limits']) <= set(decision['limits'])
    assert decision['view_decision'] in {'BOUNDED_READONLY_COMPARISON_CANDIDATE', 'STOP_PREVIEW_VIEW'}
    if decision['view_decision'] == 'STOP_PREVIEW_VIEW':
        assert decision['question'] is None
    else:
        assert isinstance(decision['question'], str) and len(decision['question'].strip()) >= 30
    assert len(decision['reason'].strip()) >= 30
    ledger = read(TASK / 'ATTEMPT_LEDGER.json')
    assert ledger['task_id'] == TASK.name
    assert 0 < ledger['active_minutes'] <= 60 and 0 < ledger['mapping_versions'] <= 2
    assert 0 <= ledger['formal_l2_attempts'] <= 2
    for key in ['network_calls', 'model_calls', 'payment_calls', 'installation_calls', 'product_calls']:
        assert type(ledger[key]) is int and ledger[key] == 0

def mapping():
    validate(read(TASK / 'MAPPING.json'))
    print(json.dumps({'mappings': 30, 'independent_semantic_review_required': True}))

def selftest():
    data = read(TASK / 'MAPPING.json')
    validate(data)
    for variant in range(4):
        bad = copy.deepcopy(data)
        items = bad['samples'][0]['contracts']
        if variant == 0:
            items['P4']['contract_ref'] = items['P2']['contract_ref']
        elif variant == 1:
            items['P1']['input_status'] = 'OBSERVABLE'
        elif variant == 2:
            items['P3']['input_status'] = 'PARTIAL'
            items['P3']['fact_keys'] = ['checkout_snapshot']
        else:
            items['P5']['missing_inputs'] = []
        try:
            validate(bad)
        except AssertionError:
            continue
        raise AssertionError('original semantic error accepted')
    print(json.dumps({'semantic_regression_mutations_rejected': 4}))

if __name__ == '__main__':
    {'source': source, 'mapping': mapping, 'selftest': selftest}[sys.argv[1]]()
