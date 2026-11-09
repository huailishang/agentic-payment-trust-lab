"""Evaluator prepares the accepted merchant and sources, no wiring implementation."""
import hashlib
import json
from pathlib import Path
import shutil
TASK=Path(__file__).resolve().parent
ROOT=TASK.parents[2]
PARENT=TASK.parent/'H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1'
HTTP=TASK.parent/'H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not (TASK/'SOURCE_COPY.json').exists()
    rows={}
    pairs=[(p,'merchant/'+p.relative_to(PARENT/'merchant').as_posix()) for p in (PARENT/'merchant').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    pairs += [(PARENT/'FIXTURES.py','references/H53R_FIXTURES.py'),
        (HTTP/'FROZEN_TESTS.py','references/H51_METHOD_FIXTURES.py'),
        (HTTP/'HTTP_RUNTIME.py','references/H51_HTTP_RUNTIME.py'),
        (HTTP/'HTTP_CHECKER.py','references/H51_HTTP_CHECKER.py'),
        (PARENT/'UPSTREAM_LICENSE','UPSTREAM_LICENSE')]
    for src,name in pairs:
        dst=TASK/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        rows[name]={'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'copy_sha256':sha(dst)}
    assert len([n for n in rows if n.startswith('merchant/')])==37
    assert sha(HTTP/'merchant/dependencies.py')==sha(PARENT/'merchant/dependencies.py')
    observations=json.loads((HTTP/'evidence/http_l3.json').read_text(encoding='utf-8'))
    baseline=next(c for c in observations['cases'] if c['case']=='C07_NO_CONTROL_INJECTION')
    assert [c['response_status'] for c in baseline['calls']]==[201,409]
    assert not baseline['state']['orders'] and not baseline['psp_calls']
    (TASK/'references/DEFAULT_FACTORY_BASELINE.json').write_text(json.dumps(baseline,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    (TASK/'SOURCE_COPY.json').write_text(json.dumps({'files':rows,'merchant_files':37,
        'official_commit':'99724a32da48bd0f4962c83e25f17c8345ce055e',
        'baseline':'H51 independent C07; default factory function identical to H53R',
        'wiring_implemented':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'merchant_files':37,'source_copies':len(rows),'default_factory_baseline':[201,409],
        'new_wiring_implemented':False,'new_http_requests':0}))
if __name__=='__main__': main()
