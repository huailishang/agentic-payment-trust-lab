"""Evaluator setup: source copies and fixture/runtime preparation, no new gate."""
import hashlib
import json
from pathlib import Path
import shutil
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT=TASK.parent/'H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1'
PROFILE='h56-nondelegating-checkout-complete-v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(text,old,new): assert old in text,old; return text.replace(old,new)
def main():
    assert not (TASK/'SOURCE_COPY.json').exists()
    names=['consumer.py','RUNTIME.py','FIXTURES.py','FROZEN_TESTS.py','ROOT_CASES.py',
        'JCS_CHECK.py','NODE_ORACLE.js','SOURCE_BUNDLE.json','SOURCE_MANIFEST.json']
    names += [p.relative_to(PARENT).as_posix() for p in (PARENT/'sources').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    rows={}
    for name in names:
        src=PARENT/name; dst=TASK/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        if name=='RUNTIME.py': dst.write_text(replace(dst.read_text(encoding='utf-8'),'.task_envs/H54R/runs','.task_envs/H56/runs'),encoding='utf-8')
        if name=='FIXTURES.py':
            t=dst.read_text(encoding='utf-8')
            t=replace(t,"return {'ap2_required':True,'protocol_version':VERSION,'platform_id':'h54-synthetic-platform',",
                "return {'disclosure_profile':{'id':'"+PROFILE+"','protocol_version':VERSION,'platform_kid':registry['platform'].get('kid')},\n        'ap2_required':True,'protocol_version':VERSION,'platform_id':'h54-synthetic-platform',")
            dst.write_text(t,encoding='utf-8')
        rows[name]={'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'copy_sha256':sha(dst),
            'scaffold_changes':name in {'RUNTIME.py','FIXTURES.py'}}
    # Immutable old consumer is the actual same-baseline comparator.
    src=PARENT/'consumer.py'; dst=TASK/'sources/H54R_consumer.py'; shutil.copyfile(src,dst)
    rows['sources/H54R_consumer.py']={'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),
        'copy_sha256':sha(dst),'scaffold_changes':False}
    (TASK/'SOURCE_COPY.json').write_text(json.dumps({'files':rows,'profile_id':PROFILE,'candidate_implemented':False,
        'scaffold_changes':'scratch directory and trusted fixture profile only; original36/root3 case semantics unchanged'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'copies':len(rows),'candidate_implemented':False,'candidate_equals_accepted_parent':True}))
if __name__=='__main__': main()
