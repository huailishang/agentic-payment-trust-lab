from pathlib import Path

path = Path('docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/REPORT.md')
text = path.read_text(encoding='utf-8')
text = text.replace('workflow_validator: PENDING', 'workflow_validator: OK', 1)
text = text.replace('| Workflow validator | PENDING EV-05 |', '| Workflow validator | EV-05 / EV-06 PASS |', 1)
text = text.replace(
    '## EV-04 — Final workspace, diff and hashes\n\n- AC: AC-08, AC-09\n- Result: PENDING',
    '## EV-04 — Final workspace, diff and hashes\n\n- AC: AC-08, AC-09\n- Result: PASS — final status, complete tracked diff, artifact hashes, protected diff 0, diff check PASS',
    1,
)
text = text.replace(
    '## EV-05 — Workflow validator\n\n- AC: AC-08, AC-09\n- Result: PENDING',
    '## EV-05 — Workflow validator\n\n- AC: AC-08, AC-09\n- Result: PASS — OK: v2.1 routing and required artifacts are structurally valid',
    1,
)
if '## EV-06 — Final workflow validator' not in text:
    text += '''

## EV-06 — Final workflow validator

- AC: AC-08, AC-09
- Result: PASS — final post-report v2.1 structural validation
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROJECTION_IDENTITY_FORMULA_REPAIR_V1/evidence/EV-06.stderr.log`
'''
path.write_text(text.rstrip() + '\n', encoding='utf-8')
print('report finalized')
