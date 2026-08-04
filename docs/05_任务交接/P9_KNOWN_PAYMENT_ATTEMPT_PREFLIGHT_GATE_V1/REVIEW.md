# Evaluator Review

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Contract baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Actual clean start HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Task verdict: `REJECTED`  
Project impact verdict: `REGRESSED`

```yaml
review_state: REJECTED
project_impact_verdict: REGRESSED
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

冻结 T10 target 上的主要目标已实现：

```text
T10：ALLOW / callback 1
→ DENY / callback 0

重复或禁止副作用：1/12 → 0/12
callback 次数匹配：11/12 → 12/12
```

但独立反例证明，新预检会先校验全部历史记录的 `payment_id/status`，再筛选是否属于当前 request。结果是：

```text
当前 request = r1
历史记录 request = other
历史记录 payment_id 缺失
→ preflight = INDETERMINATE
→ Runtime Gate 阻断当前合法支付
→ callback = 0
```

这直接违反合同：

- AC-02：不同 `request_id` 的 attempt 不得阻断当前合法支付；
- AC-04：非重复任务必须保持原行为；
- Rollback condition：缺字段或恶意付款记录不得阻断合法支付。

因此不能用固定 T10 的改善覆盖新增的错误拒绝。当前实现属于“目标案例改善，但受影响范围内出现新回归”。

## 2. 独立反例

### 2.1 Fact 层

构造 exact `PaymentExecutionRecord`：

```text
request_id = other
payment_id = ""
status = SUCCEEDED
```

它与当前 `request_id=r1` 无关，合理结果应为 `CLEAR`。实际结果：

```text
status = INDETERMINATE
reason = known_payment_attempt_ref_missing
```

证据：`RV-EV-01`。

### 2.2 Runtime Gate 层

同一反例进入 `gate_webshop_buy_now` 后：

```text
decision = INDETERMINATE
callback_count = 0
calls = []
reason = preflight:known_payment_attempt_ref_missing
```

即无关记录阻断了当前合法 checkout。证据：`RV-EV-07`。

根因位于 `derive_known_payment_attempt_preflight`：当前实现对全部 exact records 先校验 `status/request_id/payment_id`，之后才计算 `same_request`。正确边界应是：

```text
先验证 request_id 是否可用于归属判断
→ request_id 明确不同：忽略该记录，不读取或校验其余字段
→ request_id 相同：再校验 payment_id/status/binding
→ request_id 自身缺失或非法：INDETERMINATE
```

## 3. 正向结果

独立复跑确认以下事实成立：

- frozen target 和 runner SHA-256 与 Phase A 记录一致；
- AFTER repeat=3 摘要完全一致；
- T10 为 `DENY / callback 0 / BLOCKED`；
- 重复或禁止副作用率 `0/12`；
- callback 次数匹配率 `12/12`；
- unsafe allow、false refusal、漏确认和禁止状态写入在冻结 target 内均为 0；
- 63 个本任务专项通过；
- 68 个相关 Payment Binding、Sidecar、Recovery、Status Conflict 回归通过；
- 全量 `445/445` 通过；
- 正式入口 `13/13` 通过；
- 允许范围、target/runner freeze、单一 P2 verifier 调用点和无外部副作用审计通过。

这些结果说明 H-06 的主方向没有被证伪，失败属于实现过滤顺序缺陷，而不是“副作用前预检”方案本身无效。

## 4. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 | 通过 | frozen fact、primitive serialization、exact tuple/member 类型边界和不可变测试通过；`RV-EV-03`、`RV-EV-08` |
| AC-02 | **不通过** | 无关但 `payment_id` 缺失的 exact record 返回 `INDETERMINATE`，违反“不同 request 不得阻断”；`RV-EV-01`、`RV-EV-07` |
| AC-03 | 通过 | bound SUCCEEDED attempt 在 callback 前 DENY；同 request 绑定无效/缺证据时 callback=0；`RV-EV-02`、`RV-EV-03` |
| AC-04 | **不通过** | 固定 11-task 投影相同，但合同要求的无关 attempt 反例发生合法支付误阻断；`RV-EV-07` |
| AC-05 | 通过 | 同 target/runner，T10 与项目目标指标达到阈值，repeat=3 一致；`RV-EV-02` |
| AC-06 | 通过 | target/runner freeze 一致，tamper 回归通过；`RV-EV-02`、`RV-EV-03`、`RV-EV-08` |
| AC-07 | 通过 | 专项 63/63、相关 68/68、全量 445/445、正式入口 13/13；`RV-EV-03`—`RV-EV-06` |
| AC-08 | 通过 | REPORT、EV triplets、diff、状态、哈希和偏差披露完整；合同 baseline 与实际开工 HEAD 不一致已显式记录 |

## 5. 独立证据

| Evidence | 内容 | 结果 |
|---|---|---|
| `RV-EV-01` | Fact 层无关 malformed attempt 反例 | FAIL，复现误阻断 |
| `RV-EV-02` | frozen target repeat=3、T10 和项目指标 | PASS |
| `RV-EV-03` | 本任务专项 | 63/63 PASS |
| `RV-EV-04` | Payment Binding、Sidecar、Recovery、Status Conflict | 68/68 PASS |
| `RV-EV-05` | 全量 unittest | 445/445 PASS |
| `RV-EV-06` | 正式入口 | 13/13 PASS |
| `RV-EV-07` | Runtime Gate 层无关 malformed attempt 反例 | FAIL，`INDETERMINATE / callback 0` |
| `RV-EV-08` | 范围、freeze、P2 调用点、无外部副作用审计 | PASS；同时确认合同 baseline 与实际开工 HEAD 不一致 |

## 6. 项目影响裁决

```text
Task verdict: REJECTED
Project impact verdict: REGRESSED
```

理由：冻结 target 内的 B-07 指标改善是真实的，但合同明确把“缺字段或恶意付款记录阻断合法支付”列为 rollback condition。独立反例已经触发该条件，因此当前实现不能进入项目基线。

这不是 H-06 被证伪，而是实现把“记录完整性校验”放在了“是否属于当前 request”的筛选之前。B-07 仍是当前瓶颈，B-03 排序不变，项目瓶颈地图暂不更新。

## 7. 过程偏差

合同 baseline 为 `8acaa9e...`，实际干净开工 HEAD 为 `71a3acb...`。执行者保留了两者并以实际开工快照完成 Phase A/Phase B，target 和 runner freeze 未被污染，因此该偏差不是本次驳回主因。

后续修复包必须以 `71a3acb...` 加当前父任务未提交快照作为继承边界，不再沿用旧 baseline 字段。

## 8. 后续动作

已冻结修复任务：

```text
Task ID: P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-UNRELATED-MALFORMED-REPAIR-V1
Task kind: repair
Parent task: P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1
Failed AC: AC-02、AC-04
Inherited bottleneck: B-07
Inherited hypothesis: H-06
Next state: CONTRACT_FROZEN / Executor
```

修复只调整 `known_payment_attempt.py` 的筛选顺序，并增加 Fact 与 Runtime Gate 两层回归；不得修改 target fixture、runner、Sidecar、Recovery 或项目指标定义。
