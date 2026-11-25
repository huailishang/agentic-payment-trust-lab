"""Evaluator-owned immutable submission and evidence audit; no product writes."""
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OUT = TASK / 'evidence' / 'evaluator'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(stage):
    OUT.mkdir(parents=True, exist_ok=True)
    submitted = json.loads((TASK / 'SUBMISSION.json').read_text(encoding='utf-8'))
    files = submitted['files']
    checked = {}
    for name, digest in files.items():
        if stage != 'accept' and name == 'CURRENT.md':
            continue
        assert sha(ROOT / name) == digest, name
        checked[name] = digest
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == submitted['head']
    raw = []
    for attempt in ('attempt-1', 'attempt-2'):
        for meta_path in sorted((TASK / 'evidence' / attempt).glob('EV-*.meta.json')):
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            for stream in ('stdout', 'stderr'):
                path = meta_path.parent / meta[stream + '_path']
                assert path.stat().st_size == meta[stream + '_bytes'], path
                assert sha(path) == meta[stream + '_sha256'], path
            raw.append(meta_path.relative_to(ROOT).as_posix())
    record = {'stage': stage, 'at': datetime.now(timezone.utc).isoformat(),
              'head': head, 'files': checked, 'raw_triplets_checked': raw,
              'result': 'PASS', 'active_minutes': 'UNKNOWN'}
    if stage == 'accept':
        (OUT / 'CURRENT.submitted.md').write_bytes((ROOT / 'CURRENT.md').read_bytes())
        old = (TASK / 'evidence' / 'attempt-1-frozen' / 'CHECK.py').read_text(encoding='utf-8')
        new = (TASK / 'CHECK.py').read_text(encoding='utf-8')
        (OUT / 'CHECK.authorized.diff').write_text(''.join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True), fromfile='attempt-1/CHECK.py',
            tofile='attempt-2/CHECK.py')), encoding='utf-8')
    else:
        gate = json.loads((OUT / 'l3' / 'L3-GATE.json').read_text(encoding='utf-8'))
        assert gate['result'] == 'PASS' and gate['checks_total'] == 6
        comparisons = {}
        for i in range(1, 7):
            left = TASK / 'evidence' / 'attempt-2' / f'EV-{i:02}.stdout.log'
            right = OUT / 'l3' / f'RV-EV-{i:02}.stdout.log'
            comparisons[f'VP-{i:02}'] = left.read_bytes() == right.read_bytes()
        assert all(comparisons.values()), comparisons
        record['l2_l3_stdout_byte_equal'] = comparisons
        record['l3_child_seconds'] = sum(json.loads(p.read_text(encoding='utf-8')) and
            (datetime.fromisoformat(json.loads(p.read_text(encoding='utf-8'))['finished_at_utc']) -
             datetime.fromisoformat(json.loads(p.read_text(encoding='utf-8'))['started_at_utc'])).total_seconds()
            for p in (OUT / 'l3').glob('RV-EV-*.meta.json'))
    (OUT / ('ACCEPTANCE.json' if stage == 'accept' else 'POSTCHECK.json')).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'stage': stage, 'checked': len(checked), 'triplets': len(raw), 'result': 'PASS'}))


if __name__ == '__main__':
    audit(sys.argv[1])
