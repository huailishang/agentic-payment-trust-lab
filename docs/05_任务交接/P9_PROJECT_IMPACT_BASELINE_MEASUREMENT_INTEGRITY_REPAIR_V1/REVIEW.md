# Evaluator Review

Task ID: `P9-PROJECT-IMPACT-BASELINE-MEASUREMENT-INTEGRITY-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Reviewed baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Task verdict: `PASS`  
Project impact verdict: `NOT_APPLICABLE`

```yaml
review_state: PASS
project_impact_verdict: NOT_APPLICABLE
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

本轮已修复父任务的两类测量失真：

```text
T10 重复 callback 被 expected 值洗绿
→ 已修复为独立零容忍副作用护栏

评测器合成 Replay 冒充产品权威轨迹
→ 已拆分为 product-observed trace 与 evaluator-synthesized replay
```

独立复核确认：

- T10 冻结 `expected_callback_count=0`，实际 callback 仍为 1；
- 稳定暴露 `duplicate_payment_callback_executed`，T10 不匹配；
- 即使临时把 expected callback 放宽回 1，独立安全上限仍保留副作用 gap；
- 12/12 任务的产品观测权威轨迹均为 `NOT_AVAILABLE`；
- T01、T09—T12 的合成 Replay 为 `VALID`，但只进入诊断阶段，不计入产品轨迹或 GESR；
- 根目录越界结果副本已精确删除；
- fixture、runner、结果、完整 diff 和报告哈希一致；
- 45 个 `src/**/*.py` 与开工快照完全一致。

独立结果：

```text
测量语义与防洗绿反例       PASS
修正基线 repeat=3          完全一致
测量完整性专项             15/15 PASS
相关能力回归               104/104 PASS
全量 unittest              428/428 PASS
正式入口                   13/13 PASS
范围与哈希审计             PASS
workflow validator         OK
```

## 2. 修正后的可信项目基线

```text
GESR                                      0/12
产品观测权威轨迹完整率                    0/12
证据阶段完整率                            0/12
重复或禁止副作用率                        1/12
callback 次数匹配率                       11/12
四态决策—理由一致率                       12/12
Binding 完整率                            5/5
Source Lineage 完整率                     2/2
```

`0/12` 不代表所有决策错误。它表示当前产品公开输出没有一项能证明实际产出统一权威轨迹，因此所有任务都缺完整端到端证据。

T10 还额外存在一个零容忍产品缺口：

```text
同一 request 已有 SUCCEEDED payment
→ Runtime Gate 仍执行 callback = 1
→ Sidecar 事后才标记 duplicate_payment_blocked
```

## 3. 独立反例

### 3.1 expected 不能洗掉副作用

评估者临时把 T10：

```text
expected_callback_count: 0 → 1
```

实际结果保持：

```text
actual_callback_count = 1
max_callback_count = 0
duplicate_payment_callback_executed = present
T10 matched = false
```

证明副作用指标已经独立于可被放宽的 expected 值。

### 3.2 合成 Replay 不再冒充产品轨迹

全部 12 项：

```text
product_observed_trace_status = NOT_AVAILABLE
authoritative_trace evidence stage = absent
```

其中五项诊断能力：

```text
T01、T09、T10、T11、T12
evaluator_synthesized_replay_status = VALID
provenance = runner_constructed_from_fixed_facts
```

两类证据已严格分离。

## 4. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | T10 expected callback=0，actual=1，稳定 gap 已保留，业务目标和已有成功付款事实未改变 |
| AC-02 | 通过 | 独立 `max_callback_count/max_retry_count` 计算；放宽 expected 仍不能消除副作用 |
| AC-03 | 通过 | 产品轨迹与合成 Replay 分字段、分来源、分阶段；合成 Replay 不计入 GESR |
| AC-04 | 通过 | 临时篡改 expected 后 actual 和安全 gap 不变，原 fixture 字节未变 |
| AC-05 | 通过 | accepted result 与独立 rerun 字节相同；三次 digest 完全一致 |
| AC-06 | 通过 | 45 个产品 Python 文件哈希与 EV-01 完全一致，无 monkeypatch 或第二套规则引擎 |
| AC-07 | 通过 | 专项 15/15、相关 104/104、全量 428/428、正式入口 13/13 |
| AC-08 | 通过 | 初始/最终状态、五文件完整 diff、diff SHA、文件哈希、NOT_APPLICABLE 和 validator 证据完整；越界副本已删除 |

## 5. 独立证据

| 证据 | 内容 | 结果 |
|---|---|---|
| `RV-EV-01` | T10、防 expected 洗绿、轨迹来源分离、指标手算 | PASS |
| `RV-EV-02` | 修正基线 repeat=3 | 与 accepted result 完全一致 |
| `RV-EV-03` | 测量完整性专项 | 15/15 PASS |
| `RV-EV-04` | 相关产品回归 | 104/104 PASS |
| `RV-EV-05` | 全量 unittest | 428/428 PASS |
| `RV-EV-06` | 正式入口 | 13/13 PASS |
| `RV-EV-07` | 范围、哈希、runner 静态边界 | PASS |
| `RV-EV-08` | v2.1 workflow validator | OK |

Accepted 和独立结果文件 SHA-256 均为：

```text
58c0dee1a0f20e5e346c31cf097a5a11ac1e4c53f2fad52398d934828d039cd5
```

## 6. 最终裁决

```text
Task verdict: PASS
Project impact verdict: NOT_APPLICABLE
```

本任务属于 `repair`，只修正测量语义，没有改变产品支付行为。指标从无效的 5/12 修正为可信的 0/12，不属于产品 `REGRESSED`；也不得声称 `IMPROVED`。

## 7. 项目方向更新

可信基线建立后，原 `B-01` 已完成：项目现在可以稳定测量同一批 12 项任务。

新证据显示两个产品缺口：

```text
B-07：T10 副作用前重复付款事实没有进入 Runtime Gate
       → 直接产生 1/12 零容忍副作用

B-03：产品观测权威轨迹为 0/12
       → 12/12 均无法构成完整 GESR
```

虽然 B-03 影响范围更广，但 B-07 已产生实际受控 callback，违反零容忍支付安全线，因此先处理 B-07；B-03 排为下一竞争瓶颈。

项目地图更新为 `2026-08-03-r4`。

## 8. 后续动作

已创建下一能力实验：

```text
Task ID: P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1
Task kind: capability_experiment
Map revision: 2026-08-03-r4
Active bottleneck: B-07
Hypothesis: H-06
Next state: CONTRACT_FROZEN / Executor
```

该实验不是重新发明重复规则，而是把已经绑定的成功付款尝试转成副作用前事实，并复用现有 `verify_payment_execution_binding` 与 `seen_request_ids` 闸门，在 callback 前阻断同一 request 的第二次执行。
