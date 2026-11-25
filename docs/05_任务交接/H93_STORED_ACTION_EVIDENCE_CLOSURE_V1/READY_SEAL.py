"""Freeze explicit pre-dispatch fixture-locator correction; never touch product."""
from pathlib import Path
import hashlib
import json

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    lock = TASK / 'INPUTS.json'
    old_sha = sha(lock)
    data = json.loads(lock.read_text(encoding='utf-8'))
    assert 'readiness_correction' not in data
    changed = [TASK / 'SUPPLEMENT.py', ROOT / 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md']
    for path in changed:
        data['files'][path.relative_to(ROOT).as_posix()] = sha(path)
    for path in (*(TASK / 'evidence/preparation/readiness_fix').iterdir(), Path(__file__)):
        data['files'][path.relative_to(ROOT).as_posix()] = sha(path)
    data['readiness_correction'] = {'reason': 'shared-mandate view includes B setup; filter genuine-denial positive control by target operation; align active map step labels',
        'prior_manifest_sha256': old_sha, 'product_or_AC_or_budget_or_plan_changes': False}
    lock.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    current = ROOT / 'CURRENT.md'
    text = current.read_text(encoding='utf-8')
    assert old_sha in text
    current.write_text(text.replace(old_sha, sha(lock)), encoding='utf-8')
    print(json.dumps({'protected': len(data['files']), 'lock': sha(lock), 'product_edits': 0}))


if __name__ == '__main__':
    main()
