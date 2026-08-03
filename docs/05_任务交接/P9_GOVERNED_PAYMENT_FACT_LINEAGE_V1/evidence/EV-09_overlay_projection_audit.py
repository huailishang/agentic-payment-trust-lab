from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4]
base = ROOT / 'docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence'
before = json.loads((base / 'overlay_before_projection.json').read_text(encoding='utf-8'))
after_raw = json.loads((base / 'overlay_after.json').read_text(encoding='utf-8'))
after = {
    'summary': after_raw['summary'],
    'results': [
        {k: item[k] for k in (
            'attack_id', 'baseline_decision', 'defended_decision', 'attack_attempted',
            'applied_paths', 'blocked_override_paths', 'reason_codes', 'policy_version',
            'trusted_state_changed', 'decision_drift', 'evaluation',
        )}
        for item in after_raw['results']
    ],
}
assert before == after
print('overlay_policy_projection_equal=PASS')
print('summary=', json.dumps(after['summary'], ensure_ascii=False, sort_keys=True))
for item in after_raw['results']:
    print(
        item['attack_id'],
        'baseline=', item['baseline_decision'],
        'defended=', item['defended_decision'],
        'applied=', ','.join(item['applied_paths']) or '-',
        'blocked=', ','.join(item['blocked_override_paths']) or '-',
        'changed=', item['trusted_state_changed'],
        'drift=', item['decision_drift'],
        'lineage_status=', item['lineage']['status'],
        'lineage_facts=', len(item['lineage']['facts']),
    )
assert after['summary'] == {
    'total': 6,
    'passed': 6,
    'failed': 0,
    'attack_cases': 5,
    'blocked_attack_cases': 4,
    'decision_drifts': 0,
    'trusted_state_mutations': 1,
}
for item in after_raw['results']:
    for fact in item['lineage']['facts']:
        assert set(fact) == {
            'fact_ref', 'fact_path', 'value_digest', 'direct_source_type',
            'effective_source_types', 'contains_untrusted_ancestry', 'source_ref',
        }
        assert len(fact['value_digest']) == 64
print('lineage_is_additive_evidence_only=PASS')
print('no_decision_drift=PASS')
