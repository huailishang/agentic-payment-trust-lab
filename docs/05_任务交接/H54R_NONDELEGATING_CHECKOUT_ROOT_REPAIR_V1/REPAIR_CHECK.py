"""Repair checker extends original36 checks without changing their semantics."""
import argparse
import json
from RUNTIME import TASK
import CHECK
from ROOT_CASES import CASES,inspect,selftest
def materials(role):
    CHECK.materials(role)
    base=TASK/'evidence'/role
    folder=base/json.loads((base/'ROOT_LATEST.json').read_text())['run']
    rows=json.loads((folder/'observations.json').read_text())['rows']
    assert [r['case'] for r in rows]==CASES
    for row in rows:
        assert row['check']=='PASS'; inspect(row)
        assert json.loads((folder/(row['case']+'.output.json')).read_text())==row
        raw=json.loads((folder/(row['case']+'.input.json')).read_text())
        assert all(row[k]==v for k,v in raw.items())
    root_log=[json.loads(l) for l in (base/'ROOT_ATTEMPTS.jsonl').read_text().splitlines()]
    assert all(r['cases']==CASES and r['charged']==3 for r in root_log)
    original=sum(json.loads(l)['charged'] for l in (base/'ATTEMPTS.jsonl').read_text().splitlines())
    roots=sum(r['charged'] for r in root_log)
    assert roots<=(24 if role=='executor' else 9)
    assert original+roots<=(312 if role=='executor' else 117)
    print(json.dumps({'original_cases':36,'root_cases':3,'combined_reserved':original+roots,'role':role}))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['materials','selftest']); ap.add_argument('--role',choices=['executor','evaluator']); a=ap.parse_args()
    if a.mode=='selftest':
        from FROZEN_TESTS import selftest as original
        original(); selftest()
    else: assert a.role; materials(a.role)
