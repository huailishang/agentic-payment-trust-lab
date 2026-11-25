"""Evaluator pre-dispatch metadata correction; preserve original freeze and failure."""
from pathlib import Path
import hashlib
import json

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    saved = TASK / 'evidence/preparation/format_fix'
    saved.mkdir(exist_ok=False)
    contract = TASK / 'CONTRACT.md'
    lock = TASK / 'INPUTS.json'
    current = ROOT / 'CURRENT.md'
    for path in (contract, lock, current):
        (saved / path.name).write_bytes(path.read_bytes())
    original_lock_sha = sha(lock)
    manifest = json.loads(lock.read_text(encoding='utf-8'))
    text = contract.read_text(encoding='utf-8')
    needle = '网络/API/模型/下载/安装/服务/浏览器/WSL/凭据/真实资金/Git提交推送和历史改写全部false。'
    assert text.count(needle) == 1
    contract.write_text(text.replace(needle, '## Authorization / 授权边界\n\n' + needle), encoding='utf-8')
    manifest['files'][contract.relative_to(ROOT).as_posix()] = sha(contract)
    for path in (*saved.iterdir(), Path(__file__)):
        manifest['files'][path.relative_to(ROOT).as_posix()] = sha(path)
    manifest['metadata_correction'] = {'reason': 'validator requires explicit Authorization section heading',
        'original_manifest_sha256': original_lock_sha, 'scope_AC_budget_commands_changed': False,
        'original_snapshot': saved.relative_to(ROOT).as_posix()}
    lock.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    text = current.read_text(encoding='utf-8')
    assert original_lock_sha in text
    current.write_text(text.replace(original_lock_sha, sha(lock)), encoding='utf-8')
    print(json.dumps({'fix': 'METADATA_ONLY', 'protected': len(manifest['files']), 'sha256': sha(lock)}))


if __name__ == '__main__':
    main()
