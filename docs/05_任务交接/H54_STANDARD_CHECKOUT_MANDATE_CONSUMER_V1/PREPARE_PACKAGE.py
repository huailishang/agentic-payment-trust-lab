"""Evaluator preparation: materialize connector-fetched UTF-8 bodies, no network."""
import hashlib
import json
from pathlib import Path
import shutil

TASK = Path(__file__).resolve().parent
def sha(raw): return hashlib.sha256(raw).hexdigest()
def main():
    draft = TASK / 'DRAFT_BEFORE_FREEZE_20261031.md'
    if not draft.exists(): shutil.copyfile(TASK / 'CONTRACT.md', draft)
    bundle = json.loads((TASK / 'SOURCE_BUNDLE.json').read_text(encoding='utf-8'))
    rows = []
    for row in bundle['files']:
        raw = row['content'].encode('utf-8')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert blob == row['blob_sha'], row['path']
        path = TASK / 'sources' / row['dest']
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists(): assert path.read_bytes() == raw
        else: path.write_bytes(raw)
        rows.append({k:v for k,v in row.items() if k != 'content'} | {
            'sha256':sha(raw), 'bytes':len(raw), 'license':'Apache-2.0',
            'classification':'ABSORB',
            'url':f"https://github.com/{row['repo']}/blob/{row['ref']}/{row['path']}"})
    manifest = {'schema':'h54-source-manifest/v1', 'retrieval_date':'2026-10-31',
        'transport':'public GitHub connector, fixed commit; no install', 'files':rows}
    (TASK / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'sources':len(rows),'git_blob_checks':'PASS','installs':0,'candidate_implemented':False}))
if __name__ == '__main__': main()
