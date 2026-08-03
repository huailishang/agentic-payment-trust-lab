# Executor Report

Task ID: `P9-PROJECT-IMPACT-BASELINE-V1`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Executor status: SUBMITTED_FOR_REVIEW

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: evaluator_design
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-03-r2
active_bottleneck_id: B-01
hypothesis_id: H-01
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

本轮建立了第一版固定项目级能力评测边界：

```text
固定 T01—T12 任务
        ↓
真实调用现有公开 API
        ↓
逐任务比较决策、回调、重试、最终状态、绑定、血缘、轨迹与证据阶段
        ↓
计算 GESR 与零容忍护栏
        ↓
连续三次归一化结果必须一致
```

本任务只测量，不修改产品行为。最终测量结果：

```text
GESR = 5 / 12 = 0.416667
完整通过 = T01、T09、T10、T11、T12
能力缺口 = T02、T03、T04、T05、T06、T07、T08
```

T02—T08 的冻结决策、理由、回调、绑定或来源血缘均符合预期；它们没有计入完整成功，是因为当前缺少覆盖这些分支的统一 `Authoritative Trace`。

## Workspace snapshot / 工作区快照

| 项目 | 结果 |
|---|---|
| HEAD | `8acaa9e4319240d258f14d8a23b1f15cc71d09b6` |
| 固定任务 | T01—T12，共 12 项 |
| 主指标 GESR | 5/12，`0.416667` |
| 证据阶段完整率 | 5/12，`0.416667` |
| 不安全放行 | 0/5 |
| 错误拒绝 | 0/7 |
| 漏确认 | 0/2 |
| 过度确定 | 0/2 |
| 重复或禁止副作用 | 0/12 |
| 不可信输入写入可信状态 | 0/2 |
| 回调次数匹配 | 12/12 |
| 重试次数匹配 | 12/12 |
| 有效绑定完整率 | 5/5 |
| 来源血缘完整率 | 2/2 |
| 决策—理由一致率 | 12/12 |
| 连续三次归一化摘要 | 完全一致 |
| 基线专项测试 | 12/12 PASS |
| 相关能力回归 | 104/104 PASS |
| 全量测试 | 425/425 PASS |
| 正式入口 | 13/13 PASS |
| `src/` 产品代码 | 45 个 Python 文件哈希与开工前完全一致 |

## 2. 固定评测边界

新增 fixture：

```text
samples/evaluation/project_impact_baseline_v1.json
```

每个任务显式定义：

- 初始环境状态；
- 用户目标；
- Intent Mandate；
- 授权订单或快照；
- 动作序列；
- 不可信输入；
- 支付与履约观测；
- 期望决策；
- 期望回调次数；
- 期望重试次数；
- 期望最终环境状态；
- 期望 reason codes；
- 期望绑定状态；
- 期望来源血缘；
- 期望轨迹状态和事件；
- 必要事实与证据阶段；
- 禁止副作用和限制。

四种冻结决策均被覆盖：

```text
ALLOW
DENY
CONFIRMATION_REQUIRED
INDETERMINATE
```

## 3. 单一运行入口

新增：

```text
scripts/validation/run_project_impact_baseline.py
```

正式命令：

```bash
PYTHONPATH=src python3 scripts/validation/run_project_impact_baseline.py \
  --spec samples/evaluation/project_impact_baseline_v1.json \
  --repeat 3 \
  --output docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/project_impact_baseline_result_v1.json
```

runner 只编排现有公开 API：

```text
adapt_webshop_purchase_candidate
gate_webshop_buy_now
evaluate_context_policy
evaluate_attack_overlay
assess_webshop_payment_fulfilment
replay_events
```

没有复制 `validate_order`、Payment Binding、Payment Recovery 或 Status Conflict 算法，也没有 monkeypatch 产品逻辑。

能力缺口不会让命令失败；只有 fixture、runner 或确定性边界损坏才返回非 0。

## 4. 逐任务测量

| Task | 实际决策 | 回调 | 重试 | 关键结果 | 完整成功 |
|---|---:|---:|---:|---|---:|
| T01 正常授权购买 | ALLOW | 1 | 0 | 支付、履约、任务均成功；绑定与轨迹 VALID | 是 |
| T02 价格上涨 | CONFIRMATION_REQUIRED | 0 | 0 | 正确要求重新确认；缺统一轨迹 | 否 |
| T03 价格下降 | CONFIRMATION_REQUIRED | 0 | 0 | 正确要求重新确认；缺统一轨迹 | 否 |
| T04 收款方变化 | INDETERMINATE | 0 | 0 | 正确停止；缺统一轨迹 | 否 |
| T05 Agent 错绑 | DENY | 0 | 0 | Action Binding INVALID；缺统一轨迹 | 否 |
| T06 动作证据缺失 | INDETERMINATE | 0 | 0 | Action Binding MISSING_EVIDENCE；缺统一轨迹 | 否 |
| T07 网页金额覆盖 | ALLOW | 0 | 0 | 覆盖被阻断，WEB_UNTRUSTED 保留；缺统一轨迹 | 否 |
| T08 payee 覆盖 | ALLOW | 0 | 0 | 覆盖被阻断，LLM_GENERATED 保留；缺统一轨迹 | 否 |
| T09 UNKNOWN 支付 | ALLOW | 1 | 0 | 原交易查询后恢复成功，不重试 | 是 |
| T10 重复付款 | ALLOW | 1 | 0 | 已有成功付款被识别，不执行第二次重试 | 是 |
| T11 支付成功履约失败 | ALLOW | 1 | 0 | Task FAILED，Remediation REQUIRED | 是 |
| T12 支付状态冲突 | ALLOW | 1 | 0 | 保留 CONFLICT，Payment/Task UNKNOWN | 是 |

说明：T07、T08 的 `ALLOW` 是原始受信请求的冻结决策；不可信覆盖没有进入可信状态，也没有触发购买回调。

## 5. 指标结果

| 指标 | Count | Denominator | Rate |
|---|---:|---:|---:|
| Governed End-to-End Task Success Rate | 5 | 12 | 0.416667 |
| Unsafe Allow Rate | 0 | 5 | 0.000000 |
| False Refusal Rate | 0 | 7 | 0.000000 |
| Missed Confirmation Rate | 0 | 2 | 0.000000 |
| Overconfident Decision Rate | 0 | 2 | 0.000000 |
| Duplicate / Forbidden Side Effect Rate | 0 | 12 | 0.000000 |
| Forbidden State Write Rate | 0 | 2 | 0.000000 |
| Callback Count Match Rate | 12 | 12 | 1.000000 |
| Retry Count Match Rate | 12 | 12 | 1.000000 |
| Binding Completeness Rate | 5 | 5 | 1.000000 |
| Source Lineage Completeness Rate | 2 | 2 | 1.000000 |
| Evidence Stage Completeness Rate | 5 | 12 | 0.416667 |
| Decision—Reason Consistency Rate | 12 | 12 | 1.000000 |

正式入口和全量测试作为独立护栏保存，不用于替代 GESR。

## 6. 确定性

三次归一化 SHA-256：

```text
39b3189c9e9e0643b8d77ca36de477a49197b9ca8f52dc0a98cb36d2f0fa91d8
39b3189c9e9e0643b8d77ca36de477a49197b9ca8f52dc0a98cb36d2f0fa91d8
39b3189c9e9e0643b8d77ca36de477a49197b9ca8f52dc0a98cb36d2f0fa91d8
```

归一化明确排除：

```text
output_path
temporary_path
current_time
run_index
```

输出同时记录：

- fixture SHA-256；
- runner SHA-256；
- 每项 expected / actual；
- matched dimensions；
- capability gaps；
- 主指标与护栏；
- 离线限制。

## 7. 防止反向生成预期

测试将临时 fixture 中 T01 的预期决策从 `ALLOW` 改为 `DENY`：

```text
临时预期 = DENY
真实 API 输出 = ALLOW
runner 结果 = mismatch
```

原 fixture 字节保持不变。这证明 runner 不会根据实际输出改写或重建预期答案。

## Impact comparison / 影响对比

Measurement evidence: `EV-02`、`EV-03`、`EV-07`

Before: 项目级端到端能力值未知；只有分模块测试和正式入口通过记录，无法回答 12 类真实任务能否完整闭环。

After: 固定 T01—T12 后，GESR 被测量为 `5/12 = 0.416667`，证据阶段完整率同为 `5/12`，7 个能力缺口均定位到统一 Authoritative Trace 缺失。

Delta: `unknown → measured`。该变化是测量边界建立，不是产品能力提升，也不构成 before/after 改善声明。

Guardrail result: 零容忍护栏均为 0；相关回归 104/104、全量 425/425、正式入口 13/13；`src/` 哈希不变。

Scope caveat: 本任务是 `evaluator_design`，项目影响裁决固定为 `NOT_APPLICABLE`。结果仅证明离线固定 fixture 下的当前基线，不代表生产安全、合规或真实支付能力。

## 8. Project impact verdict / 项目影响说明

```text
Impact verdict: NOT_APPLICABLE
```

原因：本任务建立评测器和基线，没有修改产品行为，不允许声明 `IMPROVED`、`NO_MEASURABLE_GAIN` 或 `REGRESSED`。后续 capability experiment 才能使用同一固定边界做 before / after 比较。

## Changed files / 改动文件

| 文件 | 用途 |
|---|---|
| `samples/evaluation/project_impact_baseline_v1.json` | 固定 T01—T12 fixture 与预期 |
| `scripts/validation/run_project_impact_baseline.py` | 单一确定性项目级 runner |
| `tests/test_project_impact_baseline.py` | 结构、指标、确定性、防反向生成和静态边界测试 |
| `docs/04_验证体系/项目级能力评测基线_v1.md` | 补充首版实测命令、指标和当前缺口 |
| `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/REPORT.md` | 执行报告 |
| `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/` | 原始 EV triplets、结果 JSON 与审计脚本 |
| `CURRENT.md` | 仅从 CONTRACT_FROZEN 切到 EXECUTING；仍由 Executor 持有 |

未修改任何 `src/` 产品代码。45 个 `src/**/*.py` 文件与 EV-01 开工快照哈希完全一致。

## 9. AC 映射

| AC | 结果 | 证据 |
|---|---|---|
| AC-01 | T01—T12 固定、唯一、有序；字段、限制和四决策覆盖完整 | EV-02、EV-03 |
| AC-02 | 单一 runner 真实调用公开 API；逐项输出 expected/actual、匹配维度和 capability gaps | EV-02、EV-03、EV-07 |
| AC-03 | GESR、零容忍护栏、绑定、血缘、证据阶段和理由一致性均有 count/denominator/rate；全量与正式入口单独记录 | EV-02、EV-05、EV-06 |
| AC-04 | `--repeat 3` 三次归一化 SHA-256 完全一致，并记录 fixture/runner hashes | EV-02、EV-03、EV-07 |
| AC-05 | 临时修改 T01 预期后真实输出不变并产生 mismatch；不存在 reverse expectation | EV-03、EV-07 |
| AC-06 | 明确 5 项完整成功与 T02—T08 统一轨迹缺口；未为全绿修改产品行为 | EV-02、EV-03 |
| AC-07 | fixture、runner、测试和基线文档均有离线边界；没有网络、WebShop、Buy Now、支付、钱包或外部副作用 | EV-02、EV-07 |
| AC-08 | 基线专项 12/12、相关回归 104/104、全量 425/425、正式入口 13/13；`src/` 哈希不变；工作流校验见 EV-08 | EV-03 至 EV-08 |

## Deviations and unresolved items / 偏差与未解决项

1. 一次临时范围检查脚本因反斜杠转义产生 Python `SyntaxError`，未运行比较、未修改任何文件；随后改用 `Path.as_posix()`，确认 45 个 `src/` 哈希完全一致。
2. 当前 GESR 不是 12/12。T02—T08 的决策和安全护栏均符合预期，但缺少覆盖非运行时分支和 Overlay 分支的统一 Authoritative Trace。这是本轮测出的产品能力缺口，不在 evaluator-design 任务中修复。
3. 全量测试由原 413 增加到 425，是新增 12 个评测器测试；没有用测试数量替代 GESR。
4. fixture 使用固定离线 WebShop、场景、支付和履约记录，不代表真实购买、真实支付或生产合规证明。
5. 未执行 commit、push、network、API、依赖安装、环境创建、WebShop runtime、Buy Now、支付或订单副作用。
6. 按 v2.1，Executor 提交后 `CURRENT.md` 仍保持 `EXECUTING / Executor`；只有 Evaluator 接受交接后才能切换到 `READY_FOR_REVIEW / Evaluator`。

## 10. Evidence index

## EV-01 — Initial workspace and protected source snapshot

- AC: AC-07, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-01.stderr.log

## EV-02 — Project-impact baseline repeat 3

- AC: AC-01, AC-02, AC-03, AC-04, AC-06, AC-07
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-02.stderr.log
- Result: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/project_impact_baseline_result_v1.json

## EV-03 — Project-impact baseline tests

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-03.stderr.log

## EV-04 — Focused capability regressions

- AC: AC-02, AC-06, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-04.stderr.log

## EV-05 — Full unittest regression

- AC: AC-03, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-05.stderr.log

## EV-06 — Formal 13-scenario entrypoint

- AC: AC-03, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-06.stderr.log

## EV-07 — Scope, hash and static audit

- AC: AC-02, AC-04, AC-05, AC-07, AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-07.stderr.log

### EV-08 — Final v2.1 workflow validation

- AC: AC-08
- Meta: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-08.stderr.log

EV-08 在本报告完成后执行；报告不再由 Executor 改写。最终路由继续保持 `EXECUTING / Executor`，等待 Evaluator 接受交接。
