"""One-shot evaluator freeze, preserving old contracts and preparation failures."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
PREP = TASK / 'evidence/scenario/preparation'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = TASK / 'SCENARIO_INPUTS.json'
    assert not destination.exists(), 'one-shot freeze; do not overwrite an existing lock'
    old = json.loads((TASK / 'INPUTS.json').read_text(encoding='utf-8'))
    current_map = 'docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md'
    old_map = 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261125_r150.md'
    files = {}
    for name, digest in old['files'].items():
        mapped = old_map if name == current_map else name
        assert sha(ROOT / mapped) == digest, mapped
        files[mapped] = digest
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    assert head == old['head']
    ledger = []
    for label in ('SCENARIO-PREFLIGHT', 'SCENARIO-NATIVE-SMOKE', 'SCENARIO-NATIVE-SMOKE-2'):
        path = PREP / (label + '.meta.json')
        meta = json.loads(path.read_text(encoding='utf-8'))
        for stream in ('stdout', 'stderr'):
            raw = PREP / meta[stream + '_path']
            assert raw.stat().st_size == meta[stream + '_bytes']
            assert sha(raw) == meta[stream + '_sha256']
        expected = 1 if label == 'SCENARIO-NATIVE-SMOKE' else 0
        assert meta['exit_code'] == expected
        seconds = (datetime.fromisoformat(meta['finished_at_utc']) - datetime.fromisoformat(meta['started_at_utc'])).total_seconds()
        ledger.append({'phase': 'PREPARATION_L1', 'label': label, 'exit_code': meta['exit_code'],
                       'meta': path.relative_to(ROOT).as_posix(), 'child_seconds': seconds,
                       'counts_as_formal_l2': False, 'counts_as_formal_l3': False,
                       'active_minutes': 'UNKNOWN', 'external_cost': 0})
    smoke = json.loads((PREP / 'SCENARIO-NATIVE-SMOKE-2.stdout.log').read_text(encoding='utf-8'))
    assert smoke['sampled_rows'] == ['O1', 'R1']
    assert smoke['recovery']['status_case'] == 'unknown'
    assert smoke['recovery']['recovery_observations'][0]['recovery_status'] == 'UNRESOLVED'
    with (PREP / 'PREPARATION_LEDGER.jsonl').open('x', encoding='utf-8') as out:
        for row in ledger:
            out.write(json.dumps(row, ensure_ascii=False) + '\n')
    for path in TASK.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        relative = path.relative_to(TASK).as_posix()
        if relative.startswith('evidence/scenario/') and not relative.startswith('evidence/scenario/preparation/'):
            continue
        files[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in ('CONTEXT.md', current_map,
                 'docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261125_r151.md',
                 'docs/reference/05_产业与机构资料/pcac/智能体支付应用自律公约_开发指标映射_v1.md'):
        files[name] = sha(ROOT / name)
    for name in ('run_validation.py', 'capture_evidence.py', 'validate_workflow.py'):
        relative = '../localagent-common/skills/evaluator-executor-workflow/scripts/' + name
        files[relative] = sha(ROOT / relative)
    manifest = {'task_id': TASK.name, 'amendment': '02', 'head': head,
                'map_revision': '2026-11-25-r152', 'active_bottleneck_id': 'B-27',
                'source_files': old['source_files'], 'inherited_product_diff': old['inherited_product_diff'],
                'files': dict(sorted(files.items())),
                'historical_map_alias': {current_map: old_map},
                'formal_executor_l2': 0, 'formal_evaluator_l3': 0,
                'preparation_sampled_rows': ['O1', 'R1'], 'complete_matrix': 'NOT_RUN'}
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = {'at': datetime.now(timezone.utc).isoformat(), 'frozen_manifest_sha256': sha(destination),
               'protected': len(files), 'head': head, 'preparation_child_seconds': sum(r['child_seconds'] for r in ledger),
               'preparation_failures_preserved': 1, 'active_minutes': 'UNKNOWN',
               'formal_l2': 0, 'formal_l3': 0, 'complete_matrix': 'NOT_RUN',
               'product_changes': 0, 'result': 'PASS'}
    (PREP / 'SCENARIO_FREEZE.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
