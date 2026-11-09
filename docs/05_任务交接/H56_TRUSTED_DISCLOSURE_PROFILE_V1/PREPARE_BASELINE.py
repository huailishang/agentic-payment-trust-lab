"""Evaluator-only unchanged comparator, charged to H55 independent review."""
import copy
import importlib.util
import json
from pathlib import Path
from RUNTIME import TASK
from PROFILE_CASES import CASES,make,sdk,assert_row,b64
def main():
    review=TASK.parent/'H55_DISCLOSURE_COMPLETENESS_MEASUREMENT_V1/evidence/review_20261031'
    charge=review/'H56_BASELINE_LEDGER.json'; assert not charge.exists()
    charge.write_text(json.dumps({'cases':CASES,'charged':14,'frozen_l3_calls':12,'combined':26,'limit':48})+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('h56_unchanged_comparator',TASK/'sources/H54R_consumer.py')
    old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    rows=[]
    for name in CASES:
        m=make(name)
        row={k:copy.deepcopy(m[k]) for k in ('case','expected','trust','now','token','fully_disclosed_token','omitted_disclosures','signed_root','public_keys')}
        row.update(request_b64=b64(m['request_raw']),session_b64=b64(m['session_raw']),sdk=sdk(m))
        row['response']=old.consume(m['request_raw'],m['session_raw'],m['trust'],m['now'])
        try: assert_row(row); row['meets_target_profile']=True
        except AssertionError: row['meets_target_profile']=False
        rows.append(row)
    out=TASK/'evidence/preparation/BASELINE_OBSERVATIONS.json'; assert not out.exists(); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'rows':rows,'candidate_called':False,'comparator_calls':14},ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'comparator_calls':14,'target_profile_failures':[r['case'] for r in rows if not r['meets_target_profile']],
        'candidate_called':False,'new_profile_implemented':False}))
if __name__=='__main__': main()
