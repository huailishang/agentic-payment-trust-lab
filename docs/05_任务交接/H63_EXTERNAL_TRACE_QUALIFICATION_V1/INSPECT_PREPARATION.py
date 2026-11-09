"""Preparation shape inspection only; no product/benchmark outcome scoring."""
import collections
import json
from pathlib import Path

task = Path(__file__).resolve().parent
summary = []
for path in sorted((task / 'references').glob('TRACE_*.jsonl')):
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    types = collections.Counter(row.get('type') for row in rows)
    shapes = {}
    for row in rows:
        shapes.setdefault(row.get('type'), sorted(row))
    summary.append({'file': path.name, 'lines': len(rows), 'types': dict(types), 'shapes': shapes})
print(json.dumps(summary, ensure_ascii=False, indent=2))
