"""Evaluator preparation: anonymous bounded metadata/source acquisition, no upstream execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

TASK = Path(__file__).resolve().parent
REFS = TASK / 'references'
REFS.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
LEDGER = TASK / 'PREPARATION.json'
state = json.loads(LEDGER.read_text(encoding='utf-8')) if LEDGER.exists() else {'purpose': 'evaluator preparation only', 'requests': [], 'max_gets': 40, 'max_total_bytes': 12000000}
def get(url, name, cap=2500000):
    assert len(state['requests']) < state['max_gets']
    target = REFS / name
    assert not target.exists()
    row = {'url': url, 'file': name, 'status': 'RESERVED'}
    state['requests'].append(row)
    LEDGER.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    try:
        with urlopen(Request(url, headers={'User-Agent': 'agentic-payment-trust-lab-source-preparation'}), timeout=25) as response:
            body = response.read(cap + 1)
            row.update(status_code=response.status, bytes=len(body))
            assert len(body) <= cap
            assert sum(r.get('bytes', 0) for r in state['requests']) <= state['max_total_bytes']
        target.write_bytes(body)
        row.update(status='FETCHED', sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        row.update(status='FAILED', error=str(exc))
    LEDGER.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(row))

if __name__ == '__main__':
    if sys.argv[1] == 'metadata':
        state['environment'] = {'python': sys.version, 'available_modules': {name: importlib.util.find_spec(name) is not None for name in ['pyarrow', 'pandas', 'datasets', 'duckdb', 'yaml']}}
        get('https://api.github.com/repos/generalmachines/cartTrace-100k/commits/main', 'GITHUB_COMMIT.json')
        get('https://huggingface.co/api/datasets/generalmachines/CartTrace-100k/revision/86cab5e539e161e0915d78d8abdd9023f09b411e', 'HF_METADATA.json')
    elif sys.argv[1] == 'fetch':
        get(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'environment':
        print(json.dumps({'python': sys.executable, 'available_modules': {name: importlib.util.find_spec(name) is not None for name in ['pyarrow', 'pandas', 'datasets', 'duckdb', 'yaml']}}))
    elif sys.argv[1] == 'code':
        commit = json.loads((REFS / 'GITHUB_COMMIT.json').read_text(encoding='utf-8'))['sha']
        names = ['README.md', 'LICENSE', 'NOTICE', 'pyproject.toml', 'src/carttrace/repro/dataset.py', 'src/carttrace/repro/replay.py', 'src/carttrace/repro/worlds.py', 'src/carttrace/collect/payment.py', 'src/carttrace/sandbox/core/handlers/payments.py', 'tests/test_repro.py']
        for name in names:
            get('https://raw.githubusercontent.com/generalmachines/cartTrace-100k/' + commit + '/' + name, 'CODE_' + name.replace('/', '__'))
    elif sys.argv[1] == 'final_sources':
        commit = json.loads((REFS / 'GITHUB_COMMIT.json').read_text(encoding='utf-8'))['sha']
        for name in ['src/carttrace/sandbox/core/state.py', 'src/carttrace/sandbox/core/event.py', 'src/carttrace/sandbox/core/psp.py', 'src/carttrace/agents/wallet.py']:
            get('https://raw.githubusercontent.com/generalmachines/cartTrace-100k/' + commit + '/' + name, 'CODE_' + name.replace('/', '__'))
        for name in ['checksums.sha256', 'SCHEMA.md', 'README.md', 'NOTICE']:
            get('https://huggingface.co/datasets/generalmachines/CartTrace-100k/resolve/86cab5e539e161e0915d78d8abdd9023f09b411e/' + name, 'DATA_' + name.replace('.', '_'))
