import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OUT = TASK / 'evidence/evaluator'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    accepted = load(OUT / 'ACCEPTANCE.json')
    for name, expected in accepted['submission'].items():
        assert digest(ROOT / name) == expected, name
    seconds = 0
    from datetime import datetime
    for i in range(1, 7):
        for base, stem in ((TASK / 'evidence/attempt-1', f'EV-{i:02d}'),
                           (OUT / 'l3', f'RV-EV-{i:02d}')):
            m = load(base / (stem + '.meta.json'))
            assert m['exit_code'] == 0
            for stream in ('stdout', 'stderr'):
                path = base / m[stream + '_path']
                assert digest(path) == m[stream + '_sha256']
                assert path.stat().st_size == m[stream + '_bytes']
            if stem.startswith('RV-'):
                start = datetime.fromisoformat(m['started_at_utc'])
                end = datetime.fromisoformat(m['finished_at_utc'])
                seconds += (end - start).total_seconds()
        assert (TASK / f'evidence/attempt-1/EV-{i:02d}.stdout.log').read_bytes() == (
            OUT / f'l3/RV-EV-{i:02d}.stdout.log').read_bytes()
    result = load(OUT / 'l3/RV-EV-03.stdout.log')
    assert len(result['observations']) == 3
    baseline = result['observations'][0]['units']
    assert len({row['snapshot_sha256'] for row in baseline.values()}) == 4
    assert len({row['confirmation_id'] for row in baseline.values()}) == 4
    def key(r):
        return r['subject_ref'], r['mandate_id'], r['authority_version']
    assert key(baseline['A']) == key(baseline['B']) == key(baseline['C']) != key(baseline['D'])
    blocked = []
    for branch in result['observations']:
        assert branch['whole_mandate_event'] == {'status': 'NOT_SUBMITTED_NO_NATIVE_RECEIVER', 'accepted': False}
        assert branch['temporary_cleanup'] == 'PASS' and branch['original_snapshots_unchanged']
        for label, row in branch['units'].items():
            assert key(row) == key(baseline[label])
            assert row['snapshot_sha256'] == baseline[label]['snapshot_sha256']
            if row['gate_decision'] == 'CONFIRMATION_REQUIRED':
                assert row['effect_delta'] == [0, 0, 0] and row['callback_count'] == 0
                assert row['withdrawal_fact']['operation_id'] == row['operation_id']
                blocked.append([branch['mode'], label])
            else:
                assert row['gate_decision'] == 'ALLOW' and row['callback_count'] == 1
                assert row['effect_delta'] == ([0, 1, 1] if label == 'B' else [1, 0, 0])
                assert row['withdrawal_fact'] is None
            assert row['registered_after_event_position'] == (label == 'C')
    assert blocked == [['withdraw_A', 'A'], ['withdraw_B', 'B']]
    data = {'accepted_files': len(accepted['submission']), 'relations_and_count_rows': 12,
            'blocked': blocked, 'whole_mandate_accepted': 0, 'identical_stdout': 6,
            'triplets_verified': 12, 'l3_child_seconds': round(seconds, 6),
            'map_sha256': accepted['map_sha256'],
            'l3_gate_sha256': digest(OUT / 'l3/L3-GATE.json')}
    with (OUT / 'POSTCHECK.json').open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
    print(json.dumps(data))


if __name__ == '__main__':
    main()
