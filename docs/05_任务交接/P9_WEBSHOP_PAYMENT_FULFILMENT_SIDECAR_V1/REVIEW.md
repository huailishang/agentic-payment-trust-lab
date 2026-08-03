# Evaluator Review

Task ID: `P9-WEBSHOP-PAYMENT-FULFILMENT-SIDECAR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Evaluator verdict: `REJECTED`

```yaml
review_state: REJECTED
current_role: Evaluator
commit_performed: false
push_performed: false
history_rewrite_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

执行交接包结构完整，workflow validator 在复核前返回 `OK`。评估者独立重跑得到：

```text
Sidecar 专项测试        21/21 PASS
Recovery/Conflict/Lifecycle 28/28 PASS
全量 unittest           358/358 PASS
正式入口                13/13 PASS
```

但是独立组合反例 `RV-EV-06` 稳定复现两个阻断问题：

1. Gate 中已经放行的 `bound_request` 与 Adapter 中的 `payment_request` 来自不同交易请求时，Sidecar 仍返回 `ready=true`；
2. 初始支付为 `UNKNOWN`，且 `known_attempts` 中已有同一业务请求的成功支付，但没有提供 query observation 时，Sidecar 返回 `duplicate_payment_blocked=false`。

因此 AC-02、AC-06 不通过，原任务不能 PASS。

## 2. 阻断发现

### F-01 — Gate 与 Adapter 的 TransactionRequest 可被交叉拼接

等级：`BLOCKING`  
影响：AC-02、VP-02、VP-07

独立反例构造：

```text
Gate bound_request:
  request_id = webshop-request-6c6a78eddffdb552c2af66ef
  amount     = 877.80

Adapter payment_request:
  request_id = cross-composed-request
  amount     = 878.80
```

实际结果：

```text
ready = true
effective_payment_status = UNKNOWN
task_status = UNKNOWN
未出现 adapter/gate request mismatch reason code
```

证据：

- `evidence/RV-EV-06.stdout.log`
- `evidence/RV-EV-06.stderr.log`
- `evidence/RV-EV-05_counterexamples.py`

原因定位：当前 `_prerequisite_reasons(...)` 只检查 `adaptation.payment_request` 是否存在；进入主流程后，生命周期和恢复逻辑使用 `gate_outcome.bound_request`，没有验证它是否确实由当前 Adapter 的 `payment_request` 投影而来。

这会允许不同商品候选、不同会话或不同金额的 Adapter 与一个已放行 Gate 结果交叉组合。虽然当前反例没有产生任务成功，但它破坏了合同要求的不可变绑定链：

```text
IntentMandate
→ Order
→ TransactionRequest
→ PaymentExecutionRecord
→ FulfillmentRecord
```

要求修复：在产生 effective payment 或 lifecycle 之前，验证：

```python
gate_outcome.bound_request
== replace(adaptation.payment_request, agent_id=gate_outcome.bound_request.agent_id)
```

或实现语义等价的完整字段核验。除 Gate 注入的 `agent_id` 外，交易请求其他字段必须一致；不一致必须 fail closed。

### F-02 — known attempts 的重复付款风险依赖 query 才会暴露

等级：`BLOCKING`  
影响：AC-06、VP-05、VP-06

独立反例构造：

```text
initial payment status = UNKNOWN
known attempt status   = SUCCEEDED
query observation      = None
```

实际结果：

```text
query_recovery_present = false
duplicate_payment_blocked = false
retry_allowed = false
未输出 duplicate:payment_blocked
```

证据：

- `evidence/RV-EV-06.stdout.log`
- `evidence/RV-EV-06.stderr.log`

当前实现只有在 `query_observation is not None` 时调用 `assess_payment_recovery(...)`，所以独立传入的 `known_attempts` 被完全忽略。

合同 AC-06 明确要求至少覆盖：

```text
UNKNOWN/PENDING + 另一未决尝试 → blocked
另一尝试已 SUCCEEDED          → blocked
```

该要求没有限定必须同时存在 query observation。即使当前 `retry_allowed` 已经是 false，`duplicate_payment_blocked=false` 仍会向 M5 和后续购买轨迹 UI 隐藏已有成功/未决尝试这一关键风险事实。

要求修复：无 query 时也必须通过既有 idempotency 能力识别同一业务请求的成功或未决尝试，只输出离线阻断事实，不创建支付、不执行重试。

## 3. 独立复核证据

| 证据 | 内容 | 结果 |
|---|---|---|
| `RV-EV-01` | Sidecar 专项测试 | 21/21 PASS |
| `RV-EV-02` | recovery/conflict/lifecycle 关联测试 | 28/28 PASS |
| `RV-EV-03` | 全量 unittest | 358/358 PASS |
| `RV-EV-04` | `run_experiment.py` | 13/13 PASS |
| `RV-EV-05` | 首次反例脚本 | 测试模块导入失败，不作为功能证据 |
| `RV-EV-06` | 修正后的组合反例 | 退出码 1，稳定复现 F-01、F-02 |
| `RV-EV-07` | HEAD、哈希、workflow validator | HEAD 与基线一致，validator OK |

`RV-EV-05` 仅记录评估脚本自身的导入失败；功能裁决只使用修正后成功运行的 `RV-EV-06`。

## 4. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 gate prerequisite and explicit facts | 通过 | `RV-EV-01` 中 gate/显式输入矩阵通过 |
| AC-02 binding and immutable composition | **不通过** | `RV-EV-06`：Adapter request 与 Gate request 不一致仍 `ready=true` |
| AC-03 payment status and original query | 通过 | `RV-EV-01`、`RV-EV-02` |
| AC-04 query and async convergence | 通过 | `RV-EV-01`、`RV-EV-02` |
| AC-05 fulfilment and task lifecycle | 通过 | `RV-EV-01`、`RV-EV-02` |
| AC-06 duplicate payment protection | **不通过** | `RV-EV-06`：无 query 时已成功 known attempt 未被标记 blocked |
| AC-07 evidence and serialization | 通过 | `RV-EV-01` primitive-only 序列化测试通过 |
| AC-08 dependency and side-effect boundary | 通过 | `RV-EV-01` 静态/动态副作用测试；`RV-EV-07` 哈希与 validator |
| AC-09 tests and regressions | 通过 | `RV-EV-01`—`RV-EV-04` |
| AC-10 roadmap and handoff | 通过（仅结构与事实状态） | 报告、CURRENT 和 validator 结构有效；不改变技术拒绝结论 |

## 5. VP 裁决

| VP | 裁决 | 依据 |
|---|---|---|
| VP-01 gate prerequisite matrix | 通过 | `RV-EV-01` |
| VP-02 success/failure fulfilment matrix | **不通过** | 常规矩阵通过，但跨 Adapter/Gate 绑定未验证，见 `RV-EV-06` |
| VP-03 query recovery matrix | 通过 | `RV-EV-01`、`RV-EV-02` |
| VP-04 query/async conflict matrix | 通过 | `RV-EV-01`、`RV-EV-02` |
| VP-05 duplicate-payment matrix | **不通过** | known-attempt-only 路径漏检，见 `RV-EV-06` |
| VP-06 evidence and serialization | **不通过** | 输出未暴露 known successful attempt 的 duplicate block 事实 |
| VP-07 static/dynamic side-effect audit | 通过 | `RV-EV-01`、`RV-EV-07` |
| VP-08 targeted sidecar tests | 通过 | 21/21，但覆盖不充分 |
| VP-09 full regression/formal entrypoint | 通过 | 358/358；13/13 |
| VP-10 scope/hash/workflow | 通过 | `RV-EV-07` |

## 6. 最终结论

```text
REJECTED
```

拒绝原因不是现有主路径回归失败，而是合同要求的组合绑定与重复付款阻断存在可复现漏检。

## 7. 后续动作

已创建并冻结最小修复任务：

```text
Task ID:
P9-WEBSHOP-PAYMENT-FULFILMENT-SIDECAR-BINDING-DUPLICATE-REPAIR-V1

Contract:
docs/05_任务交接/P9_WEBSHOP_PAYMENT_FULFILMENT_SIDECAR_BINDING_DUPLICATE_REPAIR_V1/CONTRACT.md

State:
CONTRACT_FROZEN / Executor
```

修复包只处理 F-01、F-02，并继承现有 Sidecar 实现；不得开始 P9-C2，不得修改共享 payment recovery/conflict/lifecycle 规则。
