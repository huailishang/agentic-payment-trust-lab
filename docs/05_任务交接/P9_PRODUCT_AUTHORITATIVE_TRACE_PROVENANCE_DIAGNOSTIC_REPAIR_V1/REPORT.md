# Executor Report

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROVENANCE-DIAGNOSTIC-REPAIR-V1`  
Task kind: `repair`  
Workflow: `evaluator-executor-workflow/v2.1`  
Executor status: SUBMITTED_FOR_REVIEW  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Implementation commit: `NONE`

```yaml
state_preserved: EXECUTING
current_role_preserved: Executor
task_verdict_candidate: PASS
project_impact_verdict_candidate: NOT_APPLICABLE
final_verdict_owner: Evaluator
active_bottleneck_id: B-03
hypothesis_id: H-03
commit_performed: false
push_performed: false
network_call_performed: false
api_call_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
workflow_validator: OK
```

## Workspace snapshot / 工作区快照

```text
HEAD = b4eff597ebffe79c575522b91642f82b26ad5247
branch = main
state = EXECUTING
current_role = Executor
runner old hash = cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100
runner new hash = 70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3
product src hashes = inherited accepted values
samples = unchanged
commit/push/network/side effects = none
```

## Impact comparison / 影响对比

Measurement evidence: `EV-03`、`EV-04`、`EV-05`。  
Before: T10 `trace_provenance_separated=false`，`measurement_integrity_gaps=[trace_provenance_not_separated]`；Product Trace `1/12`，target GESR `1/12`。  
After: T10 `trace_provenance_separated=true`，`measurement_integrity_gaps=[]`；Product Trace `1/12`，target GESR `1/12`。  
Delta: 只修正 3 个 T10 measurement-only 字段；产品覆盖增量 `0`，GESR 增量 `0`。  
Guardrail result: non-trace SHA、决策、callback、retry、状态、原因、副作用、产品轨迹和其他 11 项均不变。  
Scope caveat: 本任务仅修测量诊断可信度，不新增产品 trace producer，因此项目影响为 `NOT_APPLICABLE`。

## 1. 修复结论

本轮只修复 runner 的 `trace_provenance_separated` 诊断。

旧逻辑错误地要求：

```text
产品轨迹必须不存在
```

因此 T10 同时存在以下两个明确不同的来源时仍被误报：

```text
product source = webshop_gate_outcome
evaluator replay provenance = runner_constructed_from_fixed_facts
```

新逻辑改为关闭判断：

```text
产品轨迹状态、产品来源、authoritative_trace stage 必须互相一致
Replay 状态、Replay provenance 必须互相一致
Replay 存在时 provenance 必须是固定 runner 来源
两者同时存在时来源必须明确且不同
未知状态、空白来源、缺失来源、同源或状态矛盾均失败
```

结果：

```text
T10 trace_provenance_separated: false → true
T10 measurement_integrity_gaps:
  [trace_provenance_not_separated] → []
T10 measurement_diagnostics_matched: false → true
```

产品能力和业务结果没有变化：

```text
T10 product trace = VALID
Product Trace = 1/12
Target GESR = 1/12
T10 matched = true
T10 capability_gaps = []
non-trace projection SHA-256 unchanged
```

因此本任务候选裁决为：

```text
Task verdict candidate: PASS
Project impact candidate: NOT_APPLICABLE
```

该 repair 提升测量可信度，但没有新增产品能力覆盖或 GESR。

## 2. Exact changed files

本任务实际修改或新增：

| 文件 | 变化 | 作用 |
|---|---|---|
| `CURRENT.md` | 修改 | 仅 `CONTRACT_FROZEN → EXECUTING` |
| `scripts/validation/run_project_impact_baseline.py` | 修改 | 新增纯 provenance 关闭函数并替换旧误报公式 |
| `tests/test_project_impact_baseline.py` | 修改 | 增加正反真值矩阵，并更新 T10 正确诊断断言 |
| 本任务 `REPORT.md` | 新增 | 执行报告 |
| 本任务 `evidence/EV-*` | 新增 | 测试、repeat=3、字段 diff、冻结审计、工作流证据 |

本任务未修改：

```text
src/agentic_payment_experiment/
samples/
authoritative_trace.py
T10 trace producer / builder / validator
授权、绑定、重复付款、支付、恢复或状态业务规则
PROJECT_BOTTLENECK_MAP.md
```

工作区中其他未提交 P9 文件均为继承的已接受产物，本任务未清理、重置、覆盖或回退。

## 3. Defect before / after truth table

### 3.1 正例

| 场景 | Product | Replay | Stage | 结果 |
|---|---|---|---|---|
| 两者都不存在 | `NOT_AVAILABLE / None` | `NOT_AVAILABLE / None` | 无 authoritative trace | `true` |
| 仅产品轨迹 | `VALID / explicit_product_outcome` | `NOT_AVAILABLE / None` | 有 authoritative trace | `true` |
| 仅 evaluator replay | `NOT_AVAILABLE / None` | `VALID / runner_constructed_from_fixed_facts` | 无 authoritative trace | `true` |
| 两者明确不同 | `VALID / webshop_gate_outcome` | `VALID / runner_constructed_from_fixed_facts` | 有 authoritative trace | `true` |

### 3.2 负例

以下 12 个固定场景全部为 `false`：

```text
product source missing
product authoritative stage missing
product NOT_AVAILABLE but source present
replay provenance missing
replay NOT_AVAILABLE but provenance present
product source equals replay provenance
unknown product status
unknown replay status
blank product source
blank replay provenance
unexpected replay provenance
product NOT_AVAILABLE but authoritative stage present
```

`_compare(...)` 仍会为非法组合生成：

```text
measurement_integrity_gaps = [trace_provenance_not_separated]
```

证据：`EV-01`、`EV-05`。

## 4. Runner hash

| 项目 | SHA-256 |
|---|---|
| Old accepted runner | `cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100` |
| New repaired runner | `70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3` |

Runner hash 变化仅来自本任务 provenance 诊断修复。

## 5. Repeat=3 measurement

### 5.1 Baseline

原始 JSON：`evidence/EV-03-after-baseline.json`

```text
output SHA-256 = 992653a63194c391ae30f7c48bf02c34ed50cfe0b87c12914851f8572f95e26a
normalized SHA-256 = f1aa119f14e88b7a15bdcc40760391692d6ba5c9a5d795f093d0bda0d8dfb5bc
repeat count = 3
all identical = true
Product Trace = 1/12
GESR = 0/12
```

### 5.2 T10 target

原始 JSON：`evidence/EV-04-after-target.json`

```text
output SHA-256 = 4d447be2ed752455dab1c29e0da838c515fecebf379c573b6991ae216522f95b
normalized SHA-256 = 5593a59562b42378dd95f78c4a95bc906884b515cad6acac6f20e4c81b4c8421
repeat count = 3
all identical = true
Product Trace = 1/12
GESR = 1/12
matched_tasks = 1
T10 matched = true
T10 capability_gaps = []
```

## 6. Measurement-only before / after diff

结构化证据：

```text
evidence/EV-05-measurement-only-diff.json
SHA-256 = 9d44ba6d8e877a0ab8d4db6f05e2dc264587373bf424dfe0d64d0b1f6c89f824
```

Baseline 和 target 各自精确只有 7 个差异：

```text
runner_sha256
repeatability.normalized_sha256[0]
repeatability.normalized_sha256[1]
repeatability.normalized_sha256[2]
T10 measurement_diagnostics.trace_provenance_separated
T10 measurement_diagnostics_matched
T10 measurement_integrity_gaps
```

其中真正的测量内容变化只有：

```text
trace_provenance_separated: false → true
measurement_diagnostics_matched: false → true
measurement_integrity_gaps: [trace_provenance_not_separated] → []
```

其余变化由 runner hash 变化直接导致。

## 7. Business and product invariance

Non-trace canonical projection SHA-256：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

与修复前完全一致。

以下保持不变：

```text
T10 decision = DENY
callback count = 0
callback observations = 0
retry count = 0
known payment preflight = BLOCKED
duplicate_payment_blocked = true
retry_allowed = false
trusted_state_changed = false
binding_status = VALID
reason codes unchanged
forbidden_side_effects = []
T10 product trace = exact VALID 12 events / 11 bindings
其他 11 项仍无产品轨迹
```

## 8. Freeze audit

| 冻结项 | SHA-256 / 结果 |
|---|---|
| Measurement module | `07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a` |
| WebShop runtime gate | `d148c1aaa5a77b4f551bf1f045180c4127e4d45731884fa611af421e24c5b3ec` |
| T10 trace builder | `e6864905f4b67ef3024b7f7118b547c27c586127c60d537a3f5bab5a48f1e2c9` |
| Baseline fixture | `4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5` |
| Target fixture | `f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee` |
| Formula registry | `2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd` |
| Projection registry | `45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4` |
| Profiles | `6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2` |
| Runtime contract | `4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e` |

全部保持接受值。

## 9. Tests

### Focused

证据：`EV-01`。

```text
python3 -m unittest tests.test_project_impact_baseline -v

Ran 20 tests
OK
```

### Full regression

证据：`EV-02`。

```text
python3 -m unittest discover -s tests -p 'test_*.py'

Ran 489 tests
OK
```

合同下限为 486；本轮新增 3 个 provenance 测试后实际为 489。

## 10. Deviations and unresolved items / 偏差与未解决项

1. 本任务没有新增产品能力，Product Trace 和 target GESR 均保持 `1/12`，所以项目影响候选必须为 `NOT_APPLICABLE`。
2. Replay provenance 当前关闭合同只接受 `runner_constructed_from_fixed_facts`。其他非空来源不会被模糊接受。
3. 未执行 WebShop runtime、Buy Now、真实 callback、支付、钱包、订单、网络、LLM、API、下载、安装或环境创建。
4. 未 commit、push、reset 或 history rewrite。
5. 当前状态保持 `EXECUTING / Executor`，最终裁决由 Evaluator 独立签发。

## 11. Acceptance criteria mapping

| AC | Executor mapping | Evidence |
|---|---|---|
| AC-01 | 新增只读取五项 measurement 字段的纯关闭函数 | EV-01、EV-05 |
| AC-02 | replay-only 既有任务继续 separated=true、无 integrity gap | EV-01、EV-03、EV-05 |
| AC-03 | T10 product+replay 不同来源变为 separated=true、gap 清零 | EV-03、EV-04、EV-05 |
| AC-04 | product-only 固定对象为 true | EV-01、EV-05 |
| AC-05 | 12 个缺失、矛盾、空白、未知、同源场景均 false | EV-01、EV-05 |
| AC-06 | T10 Product Trace/GESR/matched/capability 均保持 | EV-04、EV-05 |
| AC-07 | non-trace SHA 与产品代码、fixture、轨迹结构不变 | EV-05 |
| AC-08 | module、product、fixtures、registry 全部冻结；记录 runner old/new hash | EV-05 |
| AC-09 | focused 20、full 489、baseline/target repeat=3 全通过 | EV-01—EV-05 |
| AC-10 | 报告、原始 JSON、truth table、字段 diff、哈希和工作流证据齐全 | EV-01—EV-06 |

## 12. Evidence index

| Evidence | 内容 | Exit code |
|---|---|---:|
| `EV-01` | 项目级 focused tests 与 provenance 正反矩阵 | 0 |
| `EV-02` | 489 项全量测试 | 0 |
| `EV-03` | baseline repeat=3 原始 JSON | 0 |
| `EV-04` | T10 target repeat=3 原始 JSON | 0 |
| `EV-05` | old/new 精确 diff、truth table、non-trace 与冻结审计 | 0 |
| `EV-06` | v2.1 workflow validator | 0 |

## EV-01 — Focused provenance tests

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-01.stderr.log`

## EV-02 — Full regression

- AC: AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-02.stderr.log`

## EV-03 — Baseline repeat=3

- AC: AC-02, AC-06, AC-07, AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-03.stderr.log`

## EV-04 — T10 target repeat=3

- AC: AC-03, AC-06, AC-07, AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-04.stderr.log`

## EV-05 — Repair and freeze audit

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-05.stderr.log`

## EV-06 — Workflow validator

- AC: AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_PROVENANCE_DIAGNOSTIC_REPAIR_V1/evidence/EV-06.stderr.log`
