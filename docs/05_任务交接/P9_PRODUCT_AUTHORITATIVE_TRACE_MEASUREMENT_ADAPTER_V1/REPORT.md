# Executor Report

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MEASUREMENT-ADAPTER-V1`  
Executor status: SUBMITTED_FOR_REVIEW  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `maintenance`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Implementation commit: `NONE`

```yaml
state_preserved: EXECUTING
current_role_preserved: Executor
task_verdict_candidate: PASS
project_impact_verdict_candidate: NOT_APPLICABLE
final_verdict_owner: Evaluator
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
commit_performed: false
push_performed: false
history_rewrite_performed: false
network_call_performed: false
api_call_performed: false
data_download_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
workflow_validator: OK
```

## 1. 执行结论

本任务新增了纯测量层 `authoritative_trace.py`，把此前只存在于设计与 evidence 中的产品权威轨迹合同，固化为包内可执行、不可变、失败关闭的 measurement adapter；同时把项目基线 runner 从旧的 `authoritative_trace_events` 诊断路径切换为只读取：

```text
outcome.authoritative_trace
```

当前产品代码没有生产该 envelope，因此测量结果仍然诚实保持：

```text
baseline product trace = 0/12
baseline GESR          = 0/12
target product trace   = 0/12
target GESR            = 0/12
```

这轮关闭的是“测量口径不可信”问题，不是产品能力问题。没有新增 trace producer，没有修改支付判断、callback、履约、恢复或状态冲突逻辑。

执行过程中人工复核发现并修复了一个测试原先未覆盖的深度不可变缺口：`frozen=True` 不能阻止调用者传入的 `list` 被外部继续修改。现已在公共 dataclass 边界统一复制为 tuple，并新增对应回归测试。

## Workspace snapshot / 工作区快照

### 初始快照

初始范围审计见 `EV-04`：

```text
HEAD = b4eff597ebffe79c575522b91642f82b26ad5247
src tracked diff = []
src untracked = [authoritative_trace.py]
scripts diff = [run_project_impact_baseline.py]
tests diff = [test_project_impact_baseline.py]
tests untracked = [test_authoritative_trace.py]
producer hits = []
```

`EV-04` 的唯一失败项是用文件 mtime 判断“父文档是否在合同冻结后变化”。父 REVIEW 属于工作区继承的已接受产物，mtime 晚于当前合同并不代表本任务修改，因此该检查产生误报。失败证据被保留。

### 最终快照

修正后的不可变哈希与范围审计见 `EV-05`：

```text
checks_total  = 58
checks_passed = 58
checks_failed = 0
HEAD unchanged
producer_hits = []
git diff --check = PASS
RESULT = PASS
```

工作区同时继承了多个上一阶段尚未提交的设计、REVIEW 和 evidence 文件。本任务没有清理、覆盖或提交这些继承产物；`EV-05` 对六个关键父设计/报告文件使用固定 SHA-256，而不再使用不可靠的 mtime。

## Changed files / 改动文件

本任务实现范围内的文件：

| 文件 | 变化 | 作用 |
|---|---|---|
| `src/agentic_payment_experiment/authoritative_trace.py` | 新增 | 纯 trace contract、冻结 registry、canonicalization、引用重算、严格 validator、mapping adapter |
| `scripts/validation/run_project_impact_baseline.py` | 修改 | 只读取显式 `outcome.authoritative_trace`；旧事件属性不再计入产品轨迹 |
| `tests/test_authoritative_trace.py` | 新增 | 合同、哈希、T10/T12、正负例、深度不可变测试 |
| `tests/test_project_impact_baseline.py` | 修改 | runner 边界、旧属性隔离、0/12 与测量完整性回归 |
| `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/REPORT.md` | 新增 | 本执行报告 |
| `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/` | 新增/刷新 | repeat=3 原始 JSON、测试、范围审计、工作流验证证据 |

未修改产品行为文件：

```text
webshop_runtime_gate.py
webshop_payment_sidecar.py
attack_overlay.py
models.py
payment_recovery.py
payment_status_conflict.py
trusted_execution/
```

没有新增任何 `authoritative_trace = ...` 产品生产路径。

## 2. 合同实现

### 2.1 纯不可变合同

模块提供：

```text
TraceSourceBinding
TraceBindingAssertion
TraceRelation
ProductTraceEvent
ProductAuthoritativeTrace
TraceValidationResult
TraceValidationStatus
```

实现约束：

- dataclass 使用 `frozen=True`；
- projection 递归冻结为 `FrozenDict + tuple`；
- 公共有序集合即使传入 list，也在 `__post_init__` 中复制为 tuple；
- reason code、event、relation、binding 类型失败关闭；
- validator 不读取原始产品对象、不访问文档/evidence、不补造缺失事实。

### 2.2 冻结 registry

运行时内嵌 accepted contract，不依赖任务文档或 evidence 文件。`EV-02` 与 `EV-05` 独立重算结果：

| Registry | SHA-256 |
|---|---|
| Formula registry | `2d8f06ba7c5ca9e35c4957412c0b92da5171c95e135e0bb14b5a61d1bf3309fd` |
| Projection registry | `45aeaa0abb46fbf66573be1ee417bafb41c99802061bc5b3cb63549313c049b4` |
| T01—T12 profiles | `6b53b88d5413ae9dd6d536089a22efe3f32563b950f61604c79f136c03d720c2` |
| Full runtime contract | `4062944a6b3dfa5ca8042bc4f6a0ed429a75f00b8875c71c844e7eb0eb304f0e` |

模块文件 SHA-256：

```text
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a
```

### 2.3 Canonicalization 与引用重算

实现并测试：

```text
canonical primitive conversion
canonical JSON bytes
PROJECTION_HASH_IDENTITY_V1 source_object_ref
NATIVE_TEMPLATE source_object_ref
TraceSourceBinding binding_ref
entity_ref template rendering
relation target ref rendering
```

支持的 primitive closed set：`None / bool / int / str / Decimal / Enum / datetime / tuple / Mapping[str, ...]`。float、NaN、Infinity 和未知对象均拒绝。

九个 projection-hash identity 向量、T10 全部 binding digest、T12 conflict/sidecar digest 均从 accepted 固定 JSON 独立重算通过。

## 3. Validator status matrix

证据：`EV-02`。

| 输入情况 | 预期状态 | 实际状态 |
|---|---|---|
| T10 完整固定 envelope | `VALID` | `VALID` |
| 正确 source binding | `VALID` | `VALID` |
| 缺事件 | `INDETERMINATE` | `INDETERMINATE` |
| 多事件或乱序 | `INVALID` | `INVALID` |
| 缺 projection 字段 | `INDETERMINATE` | `INDETERMINATE` |
| 多 projection 字段 | `INVALID` | `INVALID` |
| 未知 projection schema | `INDETERMINATE` | `INDETERMINATE` |
| native/hash source identity 不匹配 | `INVALID` | `INVALID` |
| binding digest 不匹配 | `INVALID` | `INVALID` |
| event binding 缺失或无法解析 | `INDETERMINATE` | `INDETERMINATE` |
| 重复或未引用 binding | `INVALID` | `INVALID` |
| entity ref / relation target / assertion 篡改 | `INVALID` | `INVALID` |
| 未知 profile | `INDETERMINATE` | `INDETERMINATE` |
| 错误 source | `INVALID` | `INVALID` |
| sidecar projection 伪造 decision | `INVALID` | `INVALID` |
| result projection 嵌套 authoritative trace | `INVALID` | `INVALID` |
| list 传入公共有序字段 | 自动复制为 tuple | tuple 且与外部 list 解耦 |

## Impact comparison / 影响对比

Measurement evidence: `EV-01`、`EV-02`、`EV-03`、`EV-05`。  
Before: 旧 runner SHA-256 为 `a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4`，会读取旧式诊断事件路径；旧基线 product trace 与 GESR 均为 `0/12`。  
After: 新 runner SHA-256 为 `cbeafe9a3badcc5a69e7972420a5c90bb815f84bdd0d5bcde3d05f739c072100`，只承认通过严格 validator 的显式产品 envelope；当前 product trace 与 GESR 仍为 `0/12`。  
Delta: 产品能力指标 `0`；测量边界由“可能混入 evaluator replay/旧事件”收敛为“只认产品显式 envelope + 冻结 registry + 严格 validator”。  
Guardrail result: non-trace business projection hash 与全部支付守护指标保持不变；专项 42 项和全量 477 项通过。  
Scope caveat: 本任务禁止新增 producer，因此不能、也不应把产品轨迹从 `0/12` 提升到非零；产品能力改善需后续独立 capability experiment。

### 4.1 Baseline repeat=3

原始 JSON：`evidence/EV-01-baseline.json`  
输出 SHA-256：`9c4964f51ff4e5ca0e8ec0f1e2d0012a7e1ad6e75787875504c93d62c57d6eab`  
Normalized SHA-256（三次一致）：

```text
4dfc7743909374689ec7b437b3a1b774d4d2e1155e287f3f8dc23430498b7044
```

结果：

```text
product trace = 0/12
GESR          = 0/12
gap_task_ids  = T01—T12
```

### 4.2 Target repeat=3

原始 JSON：`evidence/EV-01-target.json`  
输出 SHA-256：`ac3ec88433718bbd097f2738cd2330267107431ce18c9c7b2a45964f9971b488`  
Normalized SHA-256（三次一致）：

```text
c802bacfcd9154bdca7e36a5e9a8a2cdcfdc24158c0af96baf755aafa738a770
```

结果：

```text
product trace = 0/12
GESR          = 0/12
```

### 4.3 Non-trace business projection

计算脚本：`evidence/EV-01-run-measurement.py`  
可读投影：`evidence/EV-01-non-trace-business-projection.json`  
Canonical projection SHA-256：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

与合同冻结值完全相同。说明新 measurement adapter 没有改变 T01—T12 的支付决策、callback、重试、业务状态、reason code、binding、lineage 或限制项。

### 4.4 Guardrails

| 指标 | 结果 |
|---|---:|
| callback count match | `12/12` |
| duplicate/forbidden side effect | `0/12` |
| unsafe allow | `0/5` |
| missed confirmation | `0/2` |
| overconfident decision | `0/2` |
| forbidden state write | `0/2` |
| binding completeness | `5/5` |
| source lineage completeness | `2/2` |
| retry count match | `12/12` |
| decision-reason consistency | `11/12` |

## 5. 测试证据

### 5.1 专项测试

证据三件套：`EV-02.meta.json / EV-02.stdout.log / EV-02.stderr.log`

```text
python3 -m unittest \
  tests.test_authoritative_trace \
  tests.test_project_impact_baseline -v

Ran 42 tests
OK
```

### 5.2 全量测试

证据三件套：`EV-03.meta.json / EV-03.stdout.log / EV-03.stderr.log`

```text
python3 -m unittest discover -s tests -p 'test_*.py'

Ran 477 tests
OK
```

进入本任务的冻结下限为 `451`；实际通过 `477`，未删除或放宽既有测试。

## 6. Product boundary 与静态审计

证据：`EV-05`。

```text
product implementation hashes unchanged from baseline
producer_hits = []
runner reads getattr(output, "authoritative_trace", None)
runner does not read legacy authoritative_trace_events
runtime module does not read docs/evidence/CURRENT
samples unchanged
HEAD unchanged
git diff --check = PASS
```

范围审计还验证了 accepted parent coverage、identity vectors、六个继承父设计/报告文件和四个 registry hash。

## 7. Deviations and unresolved items / 偏差与未解决项

1. 首次在当前会话直接执行专项命令时，`tests/test_authoritative_trace.py` 未将 `src` 加入 `sys.path`，导致测试模块 import 失败；17 个原有 runner 测试当时通过。已补齐与仓库其他测试一致的入口，最终 `EV-02` 为 `42/42 OK`。
2. 初始 `EV-04` 用 mtime 判断继承父文件是否被当前任务改动，因父 REVIEW 本来就晚于本合同而误报 1 项失败。失败证据保留；改为固定 SHA-256 后，`EV-05` 为 `58/58 PASS`。
3. 当前产品没有 `authoritative_trace` producer，所以 `0/12` 是可信缺口，不是本任务漏做。新增 producer 被合同明确排除。
4. 工作区包含上一阶段遗留的未提交文件和一个与本任务无关的 `docs/reference` 修改。本任务未清理、覆盖、提交或推送这些内容。
5. 未执行真实商城、Buy Now、支付、订单、网络、API、下载、安装依赖或创建环境。
6. 没有 commit、push 或 history rewrite；最终裁决与路由切换由 Evaluator 完成。

## 8. Authorization / limitations

`CURRENT.md` 中所有授权均为 `false`：

```text
commit / push / history rewrite
API / network / data download
dependency install / create environment
webshop runtime / buy now
payment or order side effect
```

执行只使用本地固定数据、离线 Python 和 Git 只读检查。`CURRENT.md` 保持：

```text
state: EXECUTING
current_role: Executor
```

## 9. Acceptance criteria mapping

| AC | Executor mapping | Evidence |
|---|---|---|
| AC-01 | 新增冻结、primitive-safe、深度不可变的 trace contract | EV-02、EV-03 |
| AC-02 | 内嵌 16 个 projection schema、T01—T12 profile 与 accepted registry hash | EV-02、EV-05 |
| AC-03 | 实现 canonical primitive/JSON、source ref、binding ref、entity/relation ref 重算 | EV-02 |
| AC-04 | 严格 validator 仅消费 envelope + frozen registry，返回 VALID/INVALID/INDETERMINATE | EV-02 |
| AC-05 | runner 只读取显式 `authoritative_trace`，旧属性不计入产品轨迹 | EV-01、EV-02、EV-05 |
| AC-06 | 正负例、T10/T12、篡改、缺失、深度不可变测试 | EV-02、EV-03 |
| AC-07 | baseline 与 target repeat=3，可信 product trace/GESR 均为 0/12 | EV-01 |
| AC-08 | non-trace hash与全部业务 guardrail 不变；全量 477 项通过 | EV-01、EV-03 |
| AC-09 | 产品实现文件不变且 zero producer | EV-05 |
| AC-10 | 报告、原始 JSON、哈希、测试、范围、失败证据和 workflow validator 齐备 | EV-01—EV-07 |

## 10. Evidence index

| Evidence | 内容 | Exit code |
|---|---|---:|
| `EV-01` | baseline/target repeat=3、输出哈希、normalized hash、non-trace projection、guardrails | 0 |
| `EV-02` | 42 项专项测试 | 0 |
| `EV-03` | 477 项全量测试 | 0 |
| `EV-04` | 初始范围审计；保留 mtime 误报失败 | 1 |
| `EV-05` | 修正后的 58 项范围、父文件哈希、zero-producer、registry、diff 审计 | 0 |
| `EV-06` | workflow validator 首次执行；报告缺少机器可解析 EV/AC 映射 | 2 |
| `EV-07` | 修正报告后的 evaluator-executor-workflow/v2.1 validator | 0 |

Executor 候选结论：

```text
Task verdict candidate: PASS
Project impact verdict candidate: NOT_APPLICABLE
```

原因：任务完成了测量基础设施维护并建立可信 `0/12 BEFORE`，但合同禁止产品能力变更，因此不把本轮声明为产品指标改善。最终裁决仅由 Evaluator 签发。

## EV-01 — Repeat-3 measurement

- AC: AC-02, AC-05, AC-07, AC-08, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-01.stderr.log`

## EV-02 — Focused contract tests

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-02.stderr.log`

## EV-03 — Full regression

- AC: AC-01, AC-06, AC-08, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-03.stderr.log`

## EV-04 — Initial scope audit failure

- AC: AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-04.stderr.log`

## EV-05 — Final scope and zero-producer audit

- AC: AC-02, AC-05, AC-09, AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-05.stderr.log`

## EV-06 — Initial workflow validator failure

- AC: AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-06.stderr.log`

## EV-07 — Final workflow validator

- AC: AC-10
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-07.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-07.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MEASUREMENT_ADAPTER_V1/evidence/EV-07.stderr.log`
