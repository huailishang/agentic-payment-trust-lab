"""Evaluator setup of a new repair copy; never edit the rejected submission."""
import hashlib
import json
from pathlib import Path
import shutil

TASK=Path(__file__).resolve().parent
PARENT=TASK.parent/'H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(text,old,new):
    assert old in text,old
    return text.replace(old,new)
def main():
    assert not (TASK/'SOURCE_COPY.json').exists()
    names=['consumer.py','RUNTIME.py','FIXTURES.py','FROZEN_TESTS.py','CHECK.py',
        'JCS_CHECK.py','NODE_ORACLE.js','SOURCE_BUNDLE.json','SOURCE_MANIFEST.json']
    names += [p.relative_to(PARENT).as_posix() for p in (PARENT/'sources').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    rows={}
    for name in names:
        src=PARENT/name; dst=TASK/name
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        if name in {'RUNTIME.py','FROZEN_TESTS.py','CHECK.py'}:
            t=dst.read_text(encoding='utf-8')
            if name=='RUNTIME.py': t=replace(t,'.task_envs/H54/runs','.task_envs/H54R/runs')
            if name=='FROZEN_TESTS.py': t=replace(t,"else 144","else 108")
            if name=='CHECK.py':
                for old,new in [("=='capability_experiment'","=='repair'"),('2026-10-31-r89','2026-10-31-r90'),
                    ("ledger['active_work_minutes']<=360","ledger['active_work_minutes']<=120"),
                    ("=='H-54'","=='H-54R'"),("else 144","else 108"),
                    ("'h54-result/v1'","'h54r-result/v1'"),
                    ("'BOUNDED_STANDARD_CHECKOUT_CONSUMER_OBSERVED'","'LOCAL_NONDELEGATING_CHECKOUT_REPAIR_OBSERVED'"),
                    ("result['before']=='ABSENT'","result['before']=='PARENT_REJECTED_OUTER_CNF_ACCEPTED'"),
                    ("result['after']=='BOUNDED_EXECUTABLE_CONSUMER'","result['after']=='BOUNDED_NONDELEGATING_CONSUMER'"),
                    ("assert ledger['artifact_cases_reserved']==executor_cases<=288",
                     "root_log=TASK/'evidence/executor/ROOT_ATTEMPTS.jsonl'\n    root_cases=sum(json.loads(l)['charged'] for l in root_log.read_text(encoding='utf-8').splitlines())\n    assert ledger['artifact_cases_reserved']==executor_cases+root_cases<=312")]:
                    t=replace(t,old,new)
            dst.write_text(t,encoding='utf-8')
        rows[name]={'source':src.relative_to(TASK.parents[2]).as_posix(),'source_sha256':sha(src),'copy_sha256':sha(dst),
            'scaffold_changes':name in {'RUNTIME.py','FROZEN_TESTS.py','CHECK.py'}}
    src=PARENT/'evidence/review_20261031/HOLDOUT.py'; dst=TASK/'sources/evaluator/H54_HOLDOUT.py'
    dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    rows['sources/evaluator/H54_HOLDOUT.py']={'source':src.relative_to(TASK.parents[2]).as_posix(),
        'source_sha256':sha(src),'copy_sha256':sha(dst),'scaffold_changes':False}
    (TASK/'SOURCE_COPY.json').write_text(json.dumps({'schema':'h54r-source-copy/v1','files':rows,
        'candidate_repaired':False,'changes':'runtime scratch; repair routing/result/budget metadata only; original36 semantics unchanged'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'copied_files':len(rows),'candidate_repaired':False,'candidate_sha256':sha(TASK/'consumer.py')}))
if __name__=='__main__': main()
