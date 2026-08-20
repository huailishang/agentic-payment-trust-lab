# Executor Report

Task ID: `P9-WEBSHOP-RUNTIME-GATE-REASON-EVIDENCE-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Executor status: `READY_FOR_REVIEW`

```yaml
executor_state: READY_FOR_REVIEW
current_role: Evaluator
review_requested: true
commit_performed: false
push_performed: false
history_rewrite_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_fulfilment_executed: false
```

## 1. 执行结论

本轮只修复共享 Runtime Gate 的原因证据，不改变决策或 callback 行为。

修复前两个评估者反例均为：

```text
final decision = INDETERMINATE
callback_count = 0
reason_codes = p2 match + p3 match + p4:context_policy_valid
```

修复后：

```text
current_action = refund_payment
→ INDETERMINATE
→ callback_count = 0
→ p4:current_action_mismatch

source coverage amount digest = 999.00
current request amount = 877.80
→ INDETERMINATE
→ callback_count = 0
→ p4:source_coverage_value_mismatch
```

WebShop wrapper 未修改；它继续直接消费 `RuntimeGateRecord.reason_codes`。

## Workspace Snapshot / 工作区快照

| 项目 | 结果 | 证据 |
|---|---|---|
| 主仓 HEAD | 与基线一致 | EV-07 |
| 共享原因矩阵 | 15 个分支均有明确原因 | EV-02 |
| WebShop 两个反例 | 决策、callback 不变，原因已补齐 | EV-01 |
| 完整测试 | 337/337 PASS | EV-05 |
| 正式入口 | 13/13 PASS | EV-06 |
| ContextPolicy 构造规则 | 哈希保持不变 | EV-07 |
| WebShop wrapper | 哈希保持不变 | EV-07 |
| P9-B1 adapter / fixture / helper | 哈希保持不变 | EV-07 |
| commit / push | 未执行 | EV-07 |

## 2. 实现方式

`PaymentExecutionGateOutcome` 新增：

```python
gate_reason_codes: tuple[str, ...] = ()
```

共享 `execute_with_payment_binding_gate` 在每个分支产生稳定的阶段原因；`observe_payment_execution_gate` 将这些 gate reasons 与原 P2/P3/P4 fact reasons 合并进不可变 `RuntimeGateRecord.reason_codes`。

新增的主要 gate reasons：

```text
p1:upstream_prepayment_non_allow
p2:binding_missing
p2:binding_invalid
p3:identity_missing
p3:identity_invalid
p3:assurance_insufficient
p4:context_missing
p4:context_invalid
p4:unauthorized_state_change
p4:policy_version_mismatch
p4:current_action_mismatch
p4:required_source_paths_mismatch
p4:covered_source_paths_mismatch
p4:missing_source_paths
p4:source_coverage_value_mismatch
runtime:allow
```

P4 的 expected coverage 仍由共享 `payment_execution.py` 内已有 `_expected_payment_source_coverage` 产生。WebShop 层没有新增金额、摘要、来源或授权比较逻辑。

## 3. 两个反例前后对比

机器可读证据：

```text
evidence/EV-01.reason_counterexamples.json
```

### 3.1 current_action 不匹配

修复前：

```text
INDETERMINATE
callback_count = 0
causal_diagnostic_codes = []
reason_codes only contain p4:context_policy_valid
```

修复后：

```text
INDETERMINATE
callback_count = 0
checkout_executed = false
p4:current_action_mismatch
```

### 3.2 source coverage value digest 不匹配

修复前：

```text
INDETERMINATE
callback_count = 0
causal_diagnostic_codes = []
reason_codes only contain p4:context_policy_valid
```

修复后：

```text
INDETERMINATE
callback_count = 0
checkout_executed = false
p4:source_coverage_value_mismatch
```

两个场景均满足：

```text
WebShopBuyNowGateOutcome.reason_codes
== RuntimeGateRecord.reason_codes
```

证据：EV-01。

## 4. 共享 Runtime Gate 原因矩阵

机器可读证据：

```text
evidence/EV-02.shared_reason_matrix.json
```

| 分支 | 最终决策 | callback | 明确原因 |
|---|---|---:|---|
| upstream prepayment non-ALLOW | 保留上游决策 | 0 | `p1:upstream_prepayment_non_allow` |
| P2 binding missing | `INDETERMINATE` | 0 | `p2:binding_missing` |
| P2 binding invalid | `DENY` | 0 | `p2:binding_invalid` |
| P3 identity missing | `INDETERMINATE` | 0 | `p3:identity_missing` |
| P3 identity invalid | `DENY` | 0 | `p3:identity_invalid` |
| P3 assurance insufficient | `INDETERMINATE` | 0 | `p3:assurance_insufficient` |
| P4 context missing | `INDETERMINATE` | 0 | `p4:context_missing` |
| P4 context invalid | `DENY` | 0 | `p4:context_invalid` |
| P4 policy version mismatch | `INDETERMINATE` | 0 | `p4:policy_version_mismatch` |
| P4 current action mismatch | `INDETERMINATE` | 0 | `p4:current_action_mismatch` |
| P4 required paths mismatch | `INDETERMINATE` | 0 | `p4:required_source_paths_mismatch` |
| P4 covered paths mismatch | `INDETERMINATE` | 0 | `p4:covered_source_paths_mismatch` |
| P4 missing source paths | `INDETERMINATE` | 0 | `p4:missing_source_paths` |
| P4 source coverage mismatch | `INDETERMINATE` | 0 | `p4:source_coverage_value_mismatch` |
| all checks pass | `ALLOW` | 1 | `runtime:allow` |

矩阵结果：

```text
case_count = 15
all_non_allow_have_causal_reason = true
```

证据：EV-02。

## 5. 决策与 callback 语义保持

本轮没有改变以下行为：

- `ALLOW`：callback 恰好 1 次；
- P1/P2/P3/P4 非 `ALLOW`：callback 0 次；
- P2/P3 invalid 仍保持原 `DENY / INDETERMINATE` 映射；
- P4 wrong action 和 digest mismatch 仍为 `INDETERMINATE`；
- callback 异常仍只尝试一次、不重试、不声称 checkout success。

证据：EV-01、EV-02、EV-03、EV-04、EV-05。

## 6. 测试结果

| 验证 | 结果 | 证据 |
|---|---|---|
| 两个评估者反例 | PASS | EV-01 |
| 共享原因矩阵 | 15/15 PASS | EV-02 |
| `tests.trusted_execution.test_payment_binding` | 17/17 PASS | EV-03 |
| `tests.test_webshop_runtime_gate` | 14/14 PASS | EV-04 |
| 完整 unittest | 337/337 PASS | EV-05 |
| `python3 run_experiment.py` | 13/13 PASS | EV-06 |
| 范围、哈希和副作用审计 | PASS | EV-07 |

完整测试由修复前 336 增至 337，新增项为共享 Runtime Gate 全分支原因矩阵测试。

## 7. 改动文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/payment_execution.py` | `25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71` |
| `tests/trusted_execution/test_payment_binding.py` | `2f18ca0f41ddb94174bad779738a6cddc5711e7dee7a21c1ecfe21e32ae7ea69` |
| `tests/test_webshop_runtime_gate.py` | `0b370c909209970981671d983cafb024f0c601646b74e3e105a8ac8e2794d4a4` |
| `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md` | `e7b51baa54c90f27b3cb2917c5841e4e934df3aa268f8b38e05597ef421c511a` |
| `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` | `00e2bea16afd8afa7030599aa3b29309c6f2800fd896d7a122e760a0acbf79b9` |

证据：EV-07。

## 8. 保护范围

以下文件哈希保持不变：

| 文件 | SHA-256 |
|---|---|
| `trusted_execution/context_policy.py` | `be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56` |
| `webshop_runtime_gate.py` | `5aadec69b787825dc7909276d1ea6881f1620d911d4b7f83839bf3400f39e368` |
| P9-B1 `adapters/webshop.py` | `035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4` |
| P9-B1 fixture | `6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5` |
| P9-B1 export helper | `aae4c6109586f20e6e78c35ba48b6c94dfee76e478134842731140f50a9382f0` |

另外：

```text
models.py diff = empty
validator.py diff = empty
HEAD = baseline HEAD
```

证据：EV-07。

## Deviations / 偏差

没有决策模型、ContextPolicy 构造、WebShop wrapper 或依赖偏差。

`RuntimeGateRecord.reason_codes` 仍保留原始 fact reasons，例如 `p4:context_policy_valid`，并额外加入当前 gate 调用的因果 reason。这样既保留“ContextPolicyFact 本身有效”的事实，也解释“该 fact 不适用于当前 execute_payment 调用”的原因。

## 9. AC 映射

| AC | 状态 | 证据 |
|---|---|---|
| AC-01 causal reason for every branch | PASS | EV-02、EV-03 |
| AC-02 two evaluator counterexamples | PASS | EV-01、EV-04 |
| AC-03 no duplicated WebShop policy logic | PASS | EV-01、EV-07 |
| AC-04 decision/callback semantics preserved | PASS | EV-01—EV-05 |
| AC-05 evidence/replay consumability | PASS | EV-01、EV-02 |
| AC-06 regressions | PASS | EV-03—EV-06 |
| AC-07 scope and handoff | PASS，workflow validator 无 `BLOCKING` | EV-07、EV-08 |

## 10. VP 映射

| VP | 状态 | 证据 |
|---|---|---|
| VP-01 shared gate branch reason matrix | PASS | EV-02 |
| VP-02 wrong-action counterexample | PASS | EV-01 |
| VP-03 digest-mismatch counterexample | PASS | EV-01 |
| VP-04 WebShop reason forwarding | PASS | EV-01、EV-04 |
| VP-05 callback/decision regression matrix | PASS | EV-02—EV-04 |
| VP-06 targeted tests | PASS | EV-03、EV-04 |
| VP-07 full regression/formal entrypoint | PASS | EV-05、EV-06 |
| VP-08 scope/hash/workflow | PASS，workflow validator 无 `BLOCKING` | EV-07、EV-08 |

## 11. 明确未发生事项

本轮没有：

- 运行 WebShop、`webshop38`、Flask、浏览器或后台服务；
- 执行 `click[buy now]` 或 `SimServer.done()`；
- 调用网络、API、LLM、钱包或测试网；
- 创建真实订单、支付或履约副作用；
- 修改 UI 或开始 P9-C、P9-D、P9-E；
- 修改 `models.py`、`validator.py`、`context_policy.py`；
- 修改 P9-B1 adapter、fixture、export helper；
- 修改 WebShop wrapper；
- 安装依赖或修改环境；
- commit、push 或 history rewrite。
