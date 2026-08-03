# Executor Report

Task ID: `P9-PROJECT-IMPACT-BASELINE-MEASUREMENT-INTEGRITY-REPAIR-V1`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Executor status: SUBMITTED_FOR_REVIEW

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-03-r3
active_bottleneck_id: B-01
hypothesis_id: H-01
parent_task_id: P9-PROJECT-IMPACT-BASELINE-V1
parent_task_verdict: REJECTED
project_impact_verdict: NOT_APPLICABLE
state_preserved: EXECUTING
current_role_preserved: Executor
commit_performed: false
push_performed: false
network_call_performed: false
api_call_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 执行结论

本轮只修复项目级基线的测量完整性，不修改支付产品行为。

父任务报告的以下结论作废：

```text
GESR = 5 / 12
重复或禁止副作用率 = 0 / 12
证据阶段完整率 = 5 / 12
```

作废原因：

1. T10 已有同一请求的成功付款，但 fixture 把 `expected_callback_count=1` 写成正确答案，掩盖了实际执行的一次重复 callback；
2. runner 自己构造的 ReplayEvent 被错误归类为产品实际产出的 Authoritative Trace。

修正后的可信测量：

```text
GESR = 0 / 12 = 0.000000
产品观测权威轨迹完整率 = 0 / 12 = 0.000000
证据阶段完整率 = 0 / 12 = 0.000000
重复或禁止副作用率 = 1 / 12 = 0.083333
回调次数匹配率 = 11 / 12 = 0.916667
```

该结果没有被改成更乐观的数值。T10 的实际 callback 仍为 1，稳定能力缺口为：

```text
duplicate_payment_callback_executed
```

## Workspace snapshot / 工作区快照

| 项目 | 结果 |
|---|---|
| HEAD | `8acaa9e4319240d258f14d8a23b1f15cc71d09b6` |
| Parent verdict | `REJECTED / NOT_APPLICABLE` |
| Fixture version | `1.1.0` |
| Result schema | `agentic-payment-project-impact-baseline-result/v1.1` |
| 修正前报告值 | 5/12，已标记 `INVALID_MEASUREMENT` |
| 修正后 GESR | 0/12，`0.000000` |
| 产品观测权威轨迹 | 0/12 |
| 评测器合成 Replay | T01、T09、T10、T11、T12 为 VALID，仅作诊断 |
| 重复或禁止副作用 | 1/12，T10 |
| 回调次数匹配 | 11/12 |
| 四态决策—理由一致 | 12/12 |
| 绑定完整 | 5/5 |
| 来源血缘完整 | 2/2 |
| 三次归一化摘要 | 完全一致 |
| 测量完整性专项 | 15/15 PASS |
| 相关能力回归 | 104/104 PASS |
| 全量测试 | 428/428 PASS |
| 正式入口 | 13/13 PASS |
| `src/` 产品代码 | 45 个 Python 文件与开工快照哈希完全一致 |
| Parent REPORT | SHA-256 保持不变 |
| Parent result JSON | SHA-256 保持不变 |
| 根目录重复结果文件 | 已删除；仅保留任务 `evidence/corrected_project_impact_baseline.json` |

## 2. T10 重复副作用测量修正

### 修正前

```text
已有同一 request 的 SUCCEEDED payment
+ expected_callback_count = 1
+ actual_callback_count = 1
→ 被错误判为 callback 匹配
```

### 修正后

T10 保持原业务目标、已有成功付款输入、最终状态和限制，只修正副作用期望：

```text
expected_callback_count = 0
side_effect_guardrail.max_callback_count = 0
callback_gap_code = duplicate_payment_callback_executed
```

实际运行结果：

```text
actual_callback_count = 1
actual_callback_observations = 1
duplicate_payment_blocked = true
retry_allowed = false
forbidden_side_effects = [duplicate_payment_callback_executed]
matched = false
```

这说明当前流程是在 Runtime Gate 已执行 callback 后，Sidecar 才识别重复付款。该产品缺口被如实保留，本轮未修改 Runtime Gate 或 Sidecar。

## 3. 独立零容忍副作用护栏

旧算法使用：

```text
actual_callback_count > expected_callback_count
```

这允许通过放宽 expected 掩盖实际副作用。

新算法使用独立业务安全上限：

```text
actual_callback_count > side_effect_guardrail.max_callback_count
actual_retry_count > side_effect_guardrail.max_retry_count
```

超过上限会生成稳定 gap code，并直接计入 `duplicate_or_forbidden_side_effect_rate`。

专项测试临时把 T10 的 expected callback 改回 1，结果仍为：

```text
actual callback = 1
安全上限 = 0
duplicate_payment_callback_executed 仍存在
重复或禁止副作用率仍为 1 / 12
T10 仍不匹配
```

原 fixture 字节和 SHA-256 保持不变。

## 4. 产品轨迹与评测器合成 Replay 分离

runner 现在分别输出：

```text
product_observed_trace_status
product_observed_trace_events
product_observed_trace_source

 evaluator_synthesized_replay_status
 evaluator_synthesized_replay_events
 evaluator_synthesized_replay_provenance
```

产品权威轨迹只允许来自现有产品公开返回对象实际暴露的精确 `authoritative_trace_events`。

当前公开输出没有该字段，因此：

```text
T01—T12 product_observed_trace_status = NOT_AVAILABLE
产品观测权威轨迹完整率 = 0 / 12
```

T01、T09、T10、T11、T12 的固定事实仍可构造 ReplayEvent 并通过 `replay_events`：

```text
evaluator_synthesized_replay_status = VALID
evaluator_synthesized_replay_provenance = runner_constructed_from_fixed_facts
```

但它们只增加 `evaluator_synthesized_replay` 诊断阶段，不增加 `authoritative_trace` 阶段，也不计入 GESR。

## 5. 修正后的指标

| 指标 | Count | Denominator | Rate |
|---|---:|---:|---:|
| Governed End-to-End Task Success Rate | 0 | 12 | 0.000000 |
| Product-observed Authoritative Trace Completeness | 0 | 12 | 0.000000 |
| Evidence Stage Completeness | 0 | 12 | 0.000000 |
| Duplicate / Forbidden Side Effect Rate | 1 | 12 | 0.083333 |
| Callback Count Match Rate | 11 | 12 | 0.916667 |
| Unsafe Allow Rate | 0 | 5 | 0.000000 |
| False Refusal Rate | 0 | 7 | 0.000000 |
| Missed Confirmation Rate | 0 | 2 | 0.000000 |
| Overconfident Decision Rate | 0 | 2 | 0.000000 |
| Forbidden State Write Rate | 0 | 2 | 0.000000 |
| Retry Count Match Rate | 12 | 12 | 1.000000 |
| Binding Completeness Rate | 5 | 5 | 1.000000 |
| Source Lineage Completeness Rate | 2 | 2 | 1.000000 |
| Decision—Reason Consistency Rate | 12 | 12 | 1.000000 |

`0/12` 不表示全部规则错误。它表示 GESR 要求的完整产品权威轨迹目前为 0/12，因此没有任务能满足所有端到端成功条件。

## 6. 确定性与哈希

三次归一化 SHA-256：

```text
d9f1424eb8f7f4e4b8ba071173af1ac81038eb68fe7955945e40e0fee2ec277a
d9f1424eb8f7f4e4b8ba071173af1ac81038eb68fe7955945e40e0fee2ec277a
d9f1424eb8f7f4e4b8ba071173af1ac81038eb68fe7955945e40e0fee2ec277a
```

| Artifact | Before SHA-256 | After SHA-256 |
|---|---|---|
| Fixture | `809aee0f720e050dab80d0c9a2f41ebb514ad94419e78f67f8476bfab78d1d9e` | `4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5` |
| Runner | `a1bd1f565e7a26c09a07280d66f38040c28227fede3ec77463cb7b4b73ca9089` | `05c8bd7baa29a37b08eb6bc8867c96f6505d7b54d109e5221da8977eab1cdaf3` |
| Tests | `947d6b224c18bd2b75c8f4c3945bdf18b93b6fa61df26026910d3a8a5ea13749` | `ee8c336408d1ff69a6ae016daa4e4a1163885a5f65d58e91215d9dffced8d8b8` |
| Baseline document | `7860b89577634992856e2a5777cb403783bd4b4bda4d636c5457ac9481ac969a` | `98c61359c604c4df8f0c3235a68fec0e2779e68bd86b9a05640316b4184d5f75` |
| Corrected result | N/A | `58c0dee1a0f20e5e346c31cf097a5a11ac1e4c53f2fad52398d934828d039cd5` |

完整实现范围 diff：

```text
Path:
docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-07_implementation_allowed_scope.diff

Bytes: 136820
SHA-256: 5454acc257ab951aa131c6ca2b6e3f51e24e94f46c194c07725191b01f362a1e
```

## Impact comparison / 影响对比

Measurement evidence: `EV-02`、`EV-03`、`EV-07`

Before: 父任务报告 GESR 5/12、副作用 0/12，但评估者证明 T10 expected 掩盖重复 callback，且 evaluator 合成 Replay 被冒充为产品轨迹；该结果状态为 `INVALID_MEASUREMENT`。

After: 使用独立副作用安全上限和显式轨迹来源后，可信 GESR 为 0/12、产品权威轨迹 0/12、重复或禁止副作用 1/12；T10 稳定暴露 `duplicate_payment_callback_executed`。

Delta: `invalid 5/12 → corrected 0/12`；重复或禁止副作用 `invalid 0/12 → corrected 1/12`。这是测量诚实性修复，不是产品能力退化或提升。

Guardrail result: 测量完整性专项 15/15、相关能力 104/104、全量 428/428、正式入口 13/13；45 个 `src/` 文件哈希不变。

Scope caveat: 本任务类型是 `repair`，只修 fixture、runner、测试、基线文档与治理证据；未修复 T10 产品重复 callback，也未实现产品 Authoritative Trace。

## 7. Project impact verdict / 项目影响说明

```text
Impact verdict: NOT_APPLICABLE
```

原因：本轮没有改变产品代码或支付行为。测量值降低是旧测量被纠正后的事实，不应被裁决为 `REGRESSED`；同样不得声称 `IMPROVED`。

## Changed files / 改动文件

| 文件 | 用途 |
|---|---|
| `samples/evaluation/project_impact_baseline_v1.json` | T10 零 callback、独立副作用护栏、轨迹来源双通道、fixture 1.1.0 |
| `scripts/validation/run_project_impact_baseline.py` | 独立副作用计算、产品轨迹与 evaluator Replay 分离、可信指标重算 |
| `tests/test_project_impact_baseline.py` | 15 项测量完整性、防期望洗绿、防轨迹洗白测试 |
| `docs/04_验证体系/项目级能力评测基线_v1.md` | 标记旧 5/12 无效并记录修正后的可信基线 |
| `CURRENT.md` | 仅切换为本任务 `EXECUTING / Executor` |
| `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/REPORT.md` | 本执行报告 |
| `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/` | EV triplets、结果 JSON、完整 diff 与范围审计 |

未修改任何 `src/` 产品文件。父任务已接受的 REPORT 和结果 JSON 哈希保持不变。评估者预接受时发现的仓库根目录重复结果文件已精确删除，正式结果仅保留在本任务 `evidence/` 目录。

## 8. AC 映射

| AC | 执行结果 | 原始证据 |
|---|---|---|
| AC-01 | T10 expected callback=0，actual callback=1，稳定 gap `duplicate_payment_callback_executed`，业务目标和已有成功付款输入未改变 | EV-02、EV-03、EV-07 |
| AC-02 | 副作用率由独立 `max_callback_count/max_retry_count` 计算；修改 expected 不能消除实际违规 | EV-02、EV-03 |
| AC-03 | 产品观测轨迹与 evaluator 合成 Replay 分开输出、分开来源、分开阶段；合成 Replay 不计入 GESR | EV-02、EV-03、EV-07 |
| AC-04 | 临时篡改 T10 callback expected 和合成 Replay expected，actual 与独立 gap 不变；原 fixture 字节不变 | EV-03 |
| AC-05 | 修正后 12 项和指标连续三次归一化 SHA-256 完全一致 | EV-02、EV-07 |
| AC-06 | 45 个 `src/**/*.py` 与 EV-01 开工快照完全一致；父任务接受快照不变 | EV-01、EV-07 |
| AC-07 | 专项 15/15、相关 104/104、全量 428/428、正式入口 13/13 | EV-03 至 EV-06 |
| AC-08 | 初始/最终 status、完整实现范围 diff、diff SHA、文件哈希、before/after、NOT_APPLICABLE 和 workflow 证据齐全 | EV-01、EV-02、EV-07、EV-08 |

## Deviations and unresolved items / 偏差与未解决项

1. 第一次 EV-01 命令中的 shell 路径变量被桥接层展开为空，尝试写 `/evidence` 被拒绝；没有创建业务文件或修改路由，随后使用完整字面路径成功采集。
2. 一次模糊代码补丁发现 `state = _empty_state()` 有两个候选位置后主动终止，未写入；随后按函数边界精确修改。
3. 更新 Markdown 时桥接层把反引号解释为命令替换，导致基线文档第 10 节临时污染；fixture、runner、测试和 EV-02/EV-03 未受影响。随后从唯一第 10 节边界截断，使用 Base64 载荷恢复；恢复后 498 行、污染标记 0、结构检查通过。
4. 修正后的 GESR 为 0/12，不是执行失败。它如实反映产品权威轨迹 0/12；本 repair 不允许为了提高分数修改产品代码。
5. T10 当前仍在 Runtime Gate 执行 callback 后才由 Sidecar 识别重复付款。该产品缺口没有在本轮修复。
6. 未执行 commit、push、history rewrite、网络、API、依赖安装、环境创建、WebShop runtime、Buy Now、支付、退款或钱包副作用。
7. Evaluator 预接受检查发现仓库根目录存在一个与正式 evidence 结果字节完全相同、但不在合同允许范围内的重复文件 `corrected_project_impact_baseline.json`。本次小修只删除该根目录副本，保留 evidence 正式结果；随后覆盖 EV-07、完整 diff 和 EV-08，指标与产品文件均未变化。
8. 按 v2.1，Executor 提交报告后仍保持 `EXECUTING / Executor`，只有 Evaluator 可以接受交接并切换路由。

## 9. Evidence index

## EV-01 — Initial workspace and protected source snapshot

- AC: AC-06, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-01.stderr.log

## EV-02 — Corrected baseline repeat 3

- AC: AC-01, AC-02, AC-03, AC-05, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-02.stderr.log
- Result: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/corrected_project_impact_baseline.json

## EV-03 — Measurement-integrity targeted tests

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-07
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-03.stderr.log

## EV-04 — Focused product capability regressions

- AC: AC-06, AC-07
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-04.stderr.log

## EV-05 — Full unittest regression

- AC: AC-06, AC-07
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-05.stderr.log

## EV-06 — Formal 13-scenario entrypoint

- AC: AC-06, AC-07
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-06.stderr.log

## EV-07 — Scope, full diff, hash and semantic audit

- AC: AC-01, AC-03, AC-05, AC-06, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-07.stderr.log
- Diff: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-07_implementation_allowed_scope.diff

## EV-08 — Final v2.1 workflow validation

- AC: AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-08.stderr.log

EV-08 在本报告完成后执行。报告提交后不再修改 fixture、runner、测试、基线文档或 EV-01 至 EV-07；路由继续保持 `EXECUTING / Executor`，等待 Evaluator 独立复核。
