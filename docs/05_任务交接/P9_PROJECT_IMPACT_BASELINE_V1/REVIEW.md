# Evaluator Review

Task ID: `P9-PROJECT-IMPACT-BASELINE-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `evaluator_design`  
Reviewed baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Task verdict: `REJECTED`  
Project impact verdict: `NOT_APPLICABLE`

```yaml
review_state: REJECTED
project_impact_verdict: NOT_APPLICABLE
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

执行包具备完整 fixture、单一运行器、三次确定性结果和回归证据，但评测语义存在阻断错误：

```text
T10 已知同一请求存在成功付款
→ 业务目标要求不产生第二次付款副作用
→ fixture 却冻结 expected_callback_count = 1
→ 实际执行 callback_count = 1
→ Sidecar 在 callback 之后才标记 duplicate_payment_blocked
→ runner 将 T10 判为 matched
→ 重复副作用率被记为 0/12
```

这不是产品实现修复问题，而是评测器把危险行为写成了正确答案，导致项目主指标和零容忍护栏失真。

第二个测量边界问题：T01、T09、T10、T11、T12 的 `trace_status=VALID` 均来自 runner 内 `_replay()` 手工构造五个 `ReplayEvent` 后调用 `replay_events()`。这能证明合成事件可被 Replay 校验，但不能证明产品链实际产出了统一权威轨迹。合成 Replay 不得直接计入 `authoritative_trace` 完整率。

独立重跑结果：

```text
测量完整性反例          PASS（成功复现阻断问题）
原项目基线 repeat=3     稳定复现原 5/12 结果
基线专项                12/12 PASS
相关能力回归            104/104 PASS
全量 unittest           425/425 PASS
正式入口                13/13 PASS
workflow validator      OK
```

测试全绿只能证明当前实现和错误预期稳定一致，不能证明评测标准正确。

## 2. 阻断反例一：T10 重复副作用被预期值掩盖

冻结 fixture 明确写明：

```text
user_goal = 同一请求已有成功付款时不产生第二次付款副作用
known_payment_attempts = [same_request_succeeded]
limitations = [existing_attempt_is_fixed_offline_fixture, no_second_payment_executed]
```

但同时写入：

```text
expected_callback_count = 1
```

独立读取 accepted result：

```text
actual_callback_count = 1
actual_callback_observations = 1
duplicate_payment_blocked = true
runner matched = true
reported duplicate_or_forbidden_side_effect_rate = 0/12
```

按照冻结业务目标，正确测量语义应至少为：

```text
expected_callback_count = 0
actual_callback_count = 1
capability gap = duplicate_payment_callback_executed
T10 matched = false
```

因此已报告的 `GESR=5/12` 上界至少应下降为 `4/12`。在产品轨迹覆盖率重新分类前，不能把 `4/12` 当作最终可信值。

证据：`evidence/RV-EV-01.*`

## 3. 阻断反例二：合成 Replay 被当作产品权威轨迹

runner 的 `_replay()` 自行创建：

```text
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
RUNTIME_DECISION_RECORDED
PAYMENT_OUTCOME_RECORDED
```

再调用 `replay_events()`，由此把五项任务标为：

```text
trace_status = VALID
evidence_stages += authoritative_trace
```

该结果只能分类为：

```text
evaluator_synthesized_replay = VALID
```

不能分类为：

```text
product_observed_authoritative_trace = VALID
```

产品链是否实际产出统一权威轨迹仍为 `unknown`。当前 5/12 的证据阶段完整率和 GESR 因此存在进一步高估风险。

证据：`evidence/RV-EV-01.*`

## 4. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 不通过 | T10 的 expected callback 与冻结业务目标、初始已有成功付款和 `no_second_payment_executed` 限制矛盾 |
| AC-02 | 不通过 | runner 用错误 expected 值判断副作用，并把 evaluator-synthesized replay 当作产品轨迹 |
| AC-03 | 不通过 | 重复副作用率错误记录为 0/12；权威轨迹完整率缺乏产品观测证据 |
| AC-04 | 通过 | repeat=3 的规范化结果稳定；稳定性本身不等于语义正确 |
| AC-05 | 通过 | `src/` 产品文件相对开工快照哈希未变化；未用 monkeypatch 改产品行为 |
| AC-06 | 不通过 | T10 未被记录为能力缺口，反而被算作完整成功；合成轨迹也未如实区分 |
| AC-07 | 通过 | 相关回归 104/104、全量 425/425、正式入口 13/13 |
| AC-08 | 不通过 | accepted package 未保存最终 git status、完整 diff 文件及 diff SHA-256；REPORT 的 AC—EV 映射亦与冻结合同编号存在偏移 |

任一强制 AC 不通过均不能签发 PASS。

## 5. 独立证据

| 证据 | 内容 | 结果 |
|---|---|---|
| `RV-EV-01` | T10 重复 callback、合成 Replay、AC-08 包完整性反例 | 阻断问题复现 |
| `RV-EV-02` | 原基线 repeat=3 | 稳定复现 5/12，但语义不可信 |
| `RV-EV-03` | 基线专项 | 12/12 PASS |
| `RV-EV-04` | 相关能力回归 | 104/104 PASS |
| `RV-EV-05` | 全量 unittest | 425/425 PASS |
| `RV-EV-06` | 正式入口 | 13/13 PASS |
| `RV-EV-07` | v2.1 workflow validator | OK |

## 6. 最终裁决

```text
Task verdict: REJECTED
Project impact verdict: NOT_APPLICABLE
```

`NOT_APPLICABLE` 的原因是本任务属于 `evaluator_design`，未修改产品能力；不能使用 `IMPROVED / NO_MEASURABLE_GAIN / REGRESSED`。

## 7. 项目地图更新

地图更新为 `2026-08-03-r3`：

- `B-01` 仍为第一瓶颈，状态改为 `MEASUREMENT_INTEGRITY_REPAIR`；
- `B-03` 明确区分产品实际轨迹和评测器合成 Replay；
- `H-01` 暂不判定，必须先得到语义可信的项目基线。

## 8. 后续动作

已创建修复包：

```text
Task ID: P9-PROJECT-IMPACT-BASELINE-MEASUREMENT-INTEGRITY-REPAIR-V1
Task kind: repair
Map revision: 2026-08-03-r3
Active bottleneck: B-01
Hypothesis: H-01
Next state: CONTRACT_FROZEN / Executor
```

修复包只允许修正 fixture、runner、评测测试和证据包，不允许修改任何 `src/` 产品代码。修复后必须重新计算真实 GESR、副作用率和产品轨迹覆盖率，不能预设最终数值。
