# Executor Report

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-REPAIR-V1`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-V1`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Executor status: SUBMITTED_FOR_REVIEW

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
parent_verdict: REJECTED
project_impact_verdict: NOT_APPLICABLE
state_preserved: EXECUTING
current_role_preserved: Executor
commit_performed: false
push_performed: false
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

本轮只修复父设计中的阻断矛盾，没有实现产品轨迹、没有修改 runner，也没有声明 B-03 已改善。

修复后的路线为：

```text
设计合同修复
→ 阶段 A：独立 measurement-adapter maintenance
→ 产品仍不产出 trace，重新冻结可信 0/12 BEFORE 和新 runner hash
→ Evaluator 接受阶段 A
→ 阶段 B：同一新 runner，只让 T10 产品 outcome 产出 trace
```

因此，旧设计中“同时修改测量工具和 T10 产品变量”的不可归因问题已经关闭。

## 2. 父 REVIEW F-01—F-05 closure

| Finding | 父任务问题 | 本轮 closure | 结果 |
|---|---|---|---|
| F-01 | 新 envelope 与旧 runner 不兼容，却直接冻结 T10 capability | 新增 `MEASUREMENT_ADAPTER.md`；阶段 A 先适配 runner 并重新冻结 0/12；父 `NEXT_SLICE.md` 改为条件冻结 | CLOSED |
| F-02 | T10 当前候选 Payment 与历史成功 Payment 没有角色 | 增加 `CURRENT_PAYMENT_CANDIDATE`、`HISTORICAL_SUCCEEDED_PAYMENT`；一致性按 `(entity_type, entity_role)` | CLOSED |
| F-03 | 无原生 ID 对象无稳定 ref；RESULT 存在循环 hash | 冻结 canonical projection；RESULT ref 排除 `authoritative_trace`；完成确定性结构化证明 | CLOSED |
| F-04 | T05/T06 只记录中间 ALLOW，无法解释最终 DENY / INDETERMINATE | 增加 `ACTION_BINDING_DECISION_RECORDED`，直接读取 `GovernedActionBindingFact.status` | CLOSED |
| F-05 | T02—T04 缺少双订单快照；T04 错写 `OrderDifference` | 增加授权/当前订单角色；T04 改用 `ValidationResult.evidence` 和 binding evidence | CLOSED |

验证证据：`EV-03`、`EV-04`、`EV-06`—`EV-09`。

## 3. 修改前后设计差异

### Before

```text
新 ProductAuthoritativeTrace envelope
+ 旧 runner 只读 authoritative_trace_events
+ T10 直接 capability freeze
+ 全链单 payment_ref / 单 order_ref
+ RESULT ref 未解决自引用
```

### After

```text
阶段 A：runner / validator measurement adapter
+ 产品仍无 trace
+ 0/12 BEFORE 重新冻结

阶段 B：同一 accepted runner
+ 单一 T10 product trace variable
+ 业务投影不变

一致性：按 entity_type + entity_role
稳定 ref：native ID 或 versioned canonical projection hash
RESULT：outcome projection excluding authoritative_trace
```

## 4. 两阶段图

```text
旧 runner hash a7d71...
        ↓ 仅作为阶段 A 输入
measurement-adapter maintenance
        ↓
新 envelope reader + strict validator
        ↓
产品 outcome 仍不产出 authoritative_trace
        ↓
重新测量 0/12 VALID
        ↓
Evaluator 接受 runner / target / BEFORE / non-trace hashes
        ↓
条件解锁 T10 capability experiment
        ↓
同一 accepted runner：NOT_AVAILABLE → VALID
```

阶段 A 与阶段 B 不得合并。

## 5. 修正后的最小 schema

正式设计：`docs/03_架构设计/产品权威轨迹最小合同_v1.md`。

新增或明确：

- `entity_type`、`entity_role`、`entity_ref`；
- closed relation；
- profile-specific required events；
- stable technical refs；
- final decision 必须有直接结构化决策事件；
- `INVALID / INDETERMINATE / NOT_AVAILABLE` 不得由 evaluator replay 补成 `VALID`。

关闭角色至少包括：

```text
AUTHORIZED_ORDER_SNAPSHOT
CURRENT_ORDER_SNAPSHOT
CURRENT_PAYMENT_CANDIDATE
HISTORICAL_SUCCEEDED_PAYMENT
RUNTIME_GATE_OBSERVATION
ACTION_BINDING_FACT
FINAL_OUTCOME
```

## 6. Stable-ref 规则和证明

```text
native-ref:
<type>:<native-id>[:<version>]

no-native-id:
<type>:sha256(canonical-json({
  projection_schema,
  primitive value
}))
```

固定转换：UTF-8、key 字典序、primitive-only、Enum→value、tuple→array、对象原生 datetime→ISO-8601；禁止当前时间、随机值、内存地址和文件路径。

指定投影：

- `RuntimeGateRecord`：`to_dict()`；
- `GovernedActionBindingFact`：`to_dict()`；
- `KnownPaymentAttemptPreflightFact`：`to_dict()`；
- `ValidationResult`：固定 primitive projection；
- outcome：固定 projection，排除 `authoritative_trace`。

RESULT 循环关闭：

```text
RESULT source ref
= hash(outcome projection excluding authoritative_trace)
```

结构化样例和重复计算证明：`EV-06-stable-ref-examples.json`、`EV-08-stable-ref-proof.json`。

## 7. T10 双 Payment 关系

```text
CURRENT_PAYMENT_CANDIDATE
ref = project-baseline-payment-1
= GovernedPaymentAction.payment_ref
= execution_candidate.payment_id

HISTORICAL_SUCCEEDED_PAYMENT
ref = project-baseline-payment-existing-success
status = SUCCEEDED
ref ∈ KnownPaymentAttemptPreflightFact.related_attempt_refs
```

两个 Payment ref 允许不同；validator 只核对现有 fact 的 refs，不重新执行 payment binding。

结构化样例：`EV-06-t10-dual-payment.json`。实际 ID 静态依据：`EV-09`。

## 8. T05/T06 最终决策修正

```text
T05:
PREPAYMENT_DECISION_RECORDED = ALLOW
ACTION_BINDING_DECISION_RECORDED = INVALID → DENY

T06:
PREPAYMENT_DECISION_RECORDED = ALLOW
ACTION_BINDING_DECISION_RECORDED = MISSING_EVIDENCE → INDETERMINATE
```

来源仅为现有 `GovernedActionBindingFact`；轨迹层不反推、不重跑 binding。

## 9. T02—T04 双订单快照修正

三项均冻结：

```text
ORDER_RECORDED [AUTHORIZED_ORDER_SNAPSHOT]
ORDER_RECORDED [CURRENT_ORDER_SNAPSHOT]
```

T04 删除不存在的 `OrderDifference` source object，改为：

- authorized/current Order；
- `ValidationResult`；
- `ValidationResult.evidence`；
- confirmation/order binding evidence。

## 10. T01—T12 覆盖结果

正式映射：`docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`。  
结构化结果：`EV-06-coverage-repaired.json`。  
SHA-256：`2f7ee5dc446efbe4c0b55f1cc0e705c3aa939606309154cb7e38babf1f70821d`。

校验结果：

```text
T01—T12 = 恰好 12 项
重复 = 0
遗漏 = 0
每项有真实入口 / outcome / source objects / roles
每项有最终 decision source
每项有事件顺序 / insertion point / ref strategy
当前 product trace = 0/12 VALID
new_business_rule_required = false
```

## 11. Measurement adapter 前置任务

设计文件：`MEASUREMENT_ADAPTER.md`。

Task kind 选择 `maintenance`，因为后续会修改纯 trace 数据合同、validator、runner 和测试，但不修改产品行为、不声明项目改善。

阶段 A 必须证明：

- exact `outcome.authoritative_trace` reader；
- absent → `NOT_AVAILABLE`；
- evaluator replay 不回退；
- invalid profile / role / ref / relation fail closed；
- 产品 producer 仍为 0；
- 同一 12 项重新测量仍为 0/12；
- 其他项目指标和业务投影不变；
- accepted runner / target / BEFORE / non-trace hashes 被独立冻结。

## 12. 条件 T10 slice

父文件 `P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md` 已改为：

```text
State = CONDITIONAL_NOT_FROZEN
prerequisite = measurement adapter accepted
runner hash = TBD_AFTER_ADAPTER_ACCEPTANCE
before hash = TBD_AFTER_ADAPTER_ACCEPTANCE
```

未创建 T10 capability `CONTRACT.md`，也未将其路由为 `CONTRACT_FROZEN`。

## Impact comparison / 影响对比

Measurement evidence: `EV-06`、`EV-07`、`EV-08`、`EV-10`。

本任务为 `repair`，不是 capability experiment。

Before：

```text
父设计不可直接执行
runner 与 envelope 不兼容
T10、T02—T06 引用/决策模型存在矛盾
```

After：

```text
设计阻断 F-01—F-05 已形成关闭方案
阶段 A / B 可独立归因
产品行为与产品轨迹指标均未变化
```

Delta：

```text
design executability: blocked → repair candidate ready for independent review
product-observed trace: 0/12 → 0/12
GESR: 0/12 → 0/12
```

Guardrail result:

- 256 个受保护产品、测试、runner 和 fixture 文件哈希全部不变；
- HEAD 不变；
- 未创建 T10 capability contract；
- 未执行产品运行、网络或支付副作用；
- 项目影响保持 `NOT_APPLICABLE`。

Scope caveat：只有未来 T10 capability experiment 在 accepted Stage A runner 下证明 `NOT_AVAILABLE → VALID`，才能裁决项目 `IMPROVED`。

## Project impact verdict / 项目影响说明

```text
Impact verdict: NOT_APPLICABLE
```

原因：本任务只修设计和后续实验边界，没有修改产品能力、runner、测试或测量结果。

## 13. Workspace / 范围审计

| 项目 | 结果 |
|---|---|
| Baseline HEAD | `71a3acbbd9622b68a8064381b9034e07c1f4d700` |
| Final HEAD | `71a3acbbd9622b68a8064381b9034e07c1f4d700` |
| 受保护范围 | `src/`、`tests/`、`scripts/`、`samples/` |
| 初始受保护文件 | 256 |
| 最终受保护文件 | 256 |
| added / removed / changed | `0 / 0 / 0` |
| 产品运行或副作用 | 未执行 |

初始 manifest：`EV-05`。最终比较：`EV-10`。

工作区包含前序任务继承的未提交产品改动；本任务没有清理、回退或改变这些文件。

## Changed files / 改动文件

本任务只修改或新增允许范围：

| 文件 | 用途 |
|---|---|
| `CURRENT.md` | `CONTRACT_FROZEN → EXECUTING`，角色仍为 Executor |
| `docs/03_架构设计/产品权威轨迹最小合同_v1.md` | 修正 schema、role、stable-ref、taxonomy 和两阶段边界 |
| `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md` | 重建 T01—T12 映射 |
| 父任务 `NEXT_SLICE.md` | 改为条件冻结 |
| `MEASUREMENT_ADAPTER.md` | 冻结阶段 A 设计 |
| repair `REPORT.md` | 本报告 |
| repair `evidence/EV-*` 和结构化 JSON | 原始审计、验证、范围和流程证据 |

完整 diff、状态与文件哈希见 `EV-11`。

## AC mapping / 验收映射

| AC | 执行结果 | 证据 |
|---|---|---|
| AC-01 | measurement adapter 与产品 capability 已拆分；阶段 A 保持产品 0/12 | `MEASUREMENT_ADAPTER.md`；`EV-07` |
| AC-02 | T10 runner/before hash 改为 adapter acceptance 后冻结；旧 runner 仅是阶段 A 输入 | 父 `NEXT_SLICE.md`；`EV-07`、`EV-09` |
| AC-03 | 增加关闭 entity roles；一致性改为 `(entity_type, entity_role)` | 设计文档；`EV-06`、`EV-07` |
| AC-04 | T10 当前候选 / 历史成功 Payment 角色与关系已冻结 | 设计、覆盖、结构化样例；`EV-06`、`EV-09` |
| AC-05 | native/no-ID stable refs、canonical JSON、RESULT 排除 trace 已冻结并证明确定性 | `EV-06`、`EV-08` |
| AC-06 | taxonomy 增加 `ACTION_BINDING_DECISION_RECORDED`；T05/T06 最终决策来源正确 | 设计、覆盖；`EV-06`、`EV-07` |
| AC-07 | T02—T04 双订单快照；T04 source mapping 已修正 | 覆盖；`EV-06`、`EV-07` |
| AC-08 | T01—T12 恰好 12 项，角色、决策、顺序、插入点、ref strategy 齐全；仍为 0/12 | `EV-06-coverage-repaired.json`；`EV-07` |
| AC-09 | 父 NEXT_SLICE 为 `CONDITIONAL_NOT_FROZEN`，TBD hashes，未创建 capability contract | 父 `NEXT_SLICE.md`；`EV-07` |
| AC-10 | closure、差异、两阶段图、结构化样例、范围、diff、限制、授权和 validator 均记录 | `EV-01`—`EV-12` |

## Deviations and unresolved items / 偏差与未解决项

1. `EV-02` 首次检索使用当前环境未安装的 `rg`，返回 `command not found`；未修改任何产品文件，后续 `EV-03` 使用 `grep` 完成同一审计。
2. 一次通过 shell heredoc 写设计文档时，Markdown 反引号被外层 shell 解释，造成该文档临时缺失代码块内容；随后使用受控文件写入接口完整覆盖，最终 SHA 和内容已重新验证。产品、测试、runner、fixture 未受影响。
3. `EV-07` 的捕获命令 stderr 出现反引号相关 shell 提示，但内部 Python 校验实际完整执行，stdout 中全部 22 项布尔检查为 true，exit code 为 0。
4. `EV-11` 首次 diff 封装因 shell 循环变量被外层命令层吞掉而返回 `Could not access ''`；原始失败保存为 `EV-11-initial.*`，随后使用固定 Python diff 脚本重新生成，最终 `EV-11` exit code 为 0。
5. 当前产品轨迹仍为 `0/12 VALID`，这是本修复任务必须保持的真实基线，不是通过文档修复产生的能力提升。
6. 未执行产品测试或正式入口，因为本任务禁止修改产品、测试、runner 和 fixture；只做静态只读审计和设计验证。
7. 未执行 commit、push、network、API、download、依赖安装、环境创建、WebShop runtime、Buy Now、支付或订单副作用。
8. 按 v2.1，Executor 提交后 `CURRENT.md` 保持 `EXECUTING / Executor`；只有 Evaluator 可接受并切换到 `READY_FOR_REVIEW / Evaluator`。

## Evidence index

## EV-01 — Initial route and workspace snapshot

- AC: AC-10
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-01.stderr.log`

## EV-02 — Initial search attempt

- AC: deviation
- Result: FAILED — `rg` unavailable; no file change
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-02.stderr.log`

## EV-03 — Source inventory with grep

- AC: AC-01—AC-08
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-03.stderr.log`

## EV-04 — Product object and old-runner audit

- AC: AC-01—AC-07
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-04.stderr.log`

## EV-05 — Initial protected manifest

- AC: AC-10
- Result: PASS — 256 protected files
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-05.stderr.log`
- Artifact: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/immutable_manifest.json`

## EV-06 — Repaired coverage and structured examples

- AC: AC-03—AC-08
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-06.stderr.log`
- Artifacts: `EV-06-coverage-repaired.json`、`EV-06-stable-ref-examples.json`、`EV-06-t10-dual-payment.json`

## EV-07 — Static contract validation

- AC: AC-01—AC-09
- Result: PASS — all 22 checks true
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-07.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-07.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-07.stderr.log`

## EV-08 — Stable-ref determinism proof

- AC: AC-05
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-08.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-08.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-08.stderr.log`
- Artifact: `EV-08-stable-ref-proof.json`

## EV-09 — Concise actual-object audit

- AC: AC-01, AC-02, AC-04, AC-06, AC-07
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-09.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-09.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-09.stderr.log`

## EV-10 — Final protected-surface audit

- AC: AC-10
- Result: PASS — 256/256 unchanged; HEAD unchanged
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-10.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-10.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-10.stderr.log`
- Artifact: `EV-10-final-scope-audit.json`

## EV-11 — Final changed files, hashes and diff

- AC: AC-10
- Result: PASS
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-11.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-11.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-11.stderr.log`

## EV-12 — Final workflow validator

- AC: AC-10
- Result: `OK: v2.1 routing and required artifacts are structurally valid`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-12.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-12.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_REPAIR_V1/evidence/EV-12.stderr.log`
