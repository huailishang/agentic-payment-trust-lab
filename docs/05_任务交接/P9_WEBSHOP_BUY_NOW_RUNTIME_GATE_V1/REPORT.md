# Executor Report

Task ID: `P9-WEBSHOP-BUY-NOW-RUNTIME-GATE-V1`  
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

P9-B2 的实现和客观验证已完成：

```text
P9-B1 WebShopCommerceAdaptation
+ 显式 IntentMandate
+ 显式 declared Agent ID
+ 显式 PaymentExecutionRecord candidate
+ 显式 AgentIdentity / provider / executor references
+ 显式 ContextPolicyFact
+ 可选 ConfirmationRecord / seen request IDs
+ 本地注入 checkout callback
        ↓
P1 validate_request
        ↓ 仅 ALLOW
P2 / P3 / P4 observe_payment_execution_gate
        ↓ 仅最终 ALLOW
本地 callback 恰好一次
```

本轮只新增薄编排层，没有复制或修改 P1—P4 规则。结果满足：

- 明确许可且 P1—P4 全部有效：`ALLOW`，本地回调 1 次；
- 限制性授权：`DENY`，回调 0 次；
- 确认失效：`CONFIRMATION_REQUIRED`，回调 0 次；
- 确认证据缺失：`INDETERMINATE`，回调 0 次；
- P2/P3/P4 任一缺失或失配：失败关闭，回调 0 次；
- callback 抛异常：只尝试 1 次，不重试，不声称结账成功，最终为 `INDETERMINATE`。

工作流预验证没有 `BLOCKING`；格式性 advisory 已原地补齐。当前候选包进入 `READY_FOR_REVIEW`，P9-C、P9-D、P9-E 均未开始。

## Workspace Snapshot / 工作区快照

| 项目 | 结果 | 证据 |
|---|---|---|
| 主仓 HEAD | `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`，与基线一致 | EV-07 |
| 本轮新增生产文件 | `webshop_runtime_gate.py` | EV-07 |
| P9-B1 adapter / fixture / helper | 三个 SHA-256 与上一任务一致 | EV-07 |
| `models.py` / `validator.py` | diff 为空 | EV-07 |
| 继承的未提交规则文件 | `payment_execution.py`、`context_policy.py` 状态保持，未由本任务编辑 | EV-07 |
| WebShop / 网络 / 环境 / Buy Now | 均未执行 | EV-07 |
| commit / push | 均未执行 | EV-07 |

## 2. 新增公共 API

```python
@dataclass(frozen=True)
class WebShopBuyNowGateOutcome:
    decision: Decision
    checkout_executed: bool
    callback_count: int
    callback_result_ref: str | None
    bound_request: TransactionRequest | None
    prepayment_result: ValidationResult | None
    runtime_gate_record: RuntimeGateRecord | None
    reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]


def gate_webshop_buy_now(
    adaptation,
    mandate,
    declared_agent_id,
    execution_candidate,
    agent_identity,
    current_provider_ref,
    current_executor_instance_ref,
    context_policy_fact,
    checkout_callback,
    *,
    current_credential_ref=None,
    confirmation_record=None,
    seen_request_ids=(),
) -> WebShopBuyNowGateOutcome:
    ...
```

公共导出位置：

```text
agentic_payment_experiment.WebShopBuyNowGateOutcome
agentic_payment_experiment.gate_webshop_buy_now
```

生产代码：

```text
src/agentic_payment_experiment/webshop_runtime_gate.py
```

## 3. 显式输入来源

| 输入 | 来源 | 本轮处理 |
|---|---|---|
| `WebShopCommerceAdaptation` | P9-B1 已通过的离线适配结果 | 只读取；不修改嵌套 Order / TransactionRequest |
| `IntentMandate` | 调用方显式提供 | 传给现有 `validate_request` |
| declared Agent ID | 调用方显式提供 | 使用 `dataclasses.replace` 写入复制后的 request |
| `PaymentExecutionRecord` candidate | 调用方显式提供 | 传给现有 P2 gate |
| `AgentIdentity` | 调用方显式提供 | 传给现有 P3 gate |
| provider / executor / credential refs | 调用方显式提供 | 传给现有 P3 gate |
| `ContextPolicyFact` | 调用方显式提供 | 传给现有 P4 gate |
| `ConfirmationRecord` | 调用方可选显式提供 | 传给现有 P1 confirmation binding |
| seen request IDs | 调用方可选显式提供 | 传给现有重复请求检查 |
| checkout callback | 调用方注入的本地测试 seam | 仅最终 `ALLOW` 时尝试调用 |

没有从以下内容推导授权、身份或执行事实：

```text
instruction_text
product title
WebShop reward
page content
Buy Now 可见状态
```

P9-B1 的原始 adaptation 保持不变；原 request 的 `agent_id` 仍为 `None`，新 outcome 中的复制 request 才具有 `webshop-agent-1`。

## 4. 决策与回调示例

机器可读结果：

```text
evidence/EV-01.decision_examples.json
```

| 场景 | P1 | 最终决策 | callback_count | callback_result_ref |
|---|---|---|---:|---|
| 显式许可，P1—P4 全部匹配 | `ALLOW` | `ALLOW` | 1 | `simulated-webshop-checkout` |
| max 30 USD 且仅允许 clothing | `DENY` | `DENY` | 0 | `null` |
| confirmation 已过期 | `CONFIRMATION_REQUIRED` | `CONFIRMATION_REQUIRED` | 0 | `null` |
| confirmation 缺失 | `INDETERMINATE` | `INDETERMINATE` | 0 | `null` |
| callback 抛 `RuntimeError` | `ALLOW` | `INDETERMINATE` | 1 次尝试 | `null` |

限制性授权案例证明：当前 `877.80 USD` 的 `home_furniture` console table 不会因为 WebShop 到达 Buy Now 就被默认接受。

正常 ALLOW 的 RuntimeGateRecord：

```text
binding_status: VALID
identity_status: VALID
context_policy_status: VALID
callback_count: 1
final_decision: ALLOW
```

固定 limitations：

```text
offline_interception_only
no_webshop_runtime_execution
no_real_buy_now_execution
no_real_payment_or_fulfilment
instruction_is_not_authorization_mandate
checkout_callback_is_injected_test_seam
```

证据：EV-01。

## 5. P1 预支付验证

闸门先创建复制后的 request，再调用：

```python
validate_request(
    mandate,
    bound_request,
    seen_request_ids=seen_request_ids,
    authorized_order=adaptation.order,
    final_order=adaptation.order,
    confirmation_record=confirmation_record,
)
```

覆盖的失败关闭条件：

- 金额超过 mandate；
- currency 不一致；
- merchant 不在授权范围；
- category 不在授权范围；
- mandate 已过期；
- sequence count 超限；
- duplicate request ID；
- confirmation 缺失；
- confirmation 过期或失效；
- declared Agent ID 缺失或不匹配。

只要 P1 不是 `ALLOW`，不会调用 P2/P3/P4 runtime callback gate，并保留原决策。

证据：EV-01、EV-04。

## 6. P2 / P3 / P4 组合矩阵

机器可读矩阵：

```text
evidence/EV-02.runtime_mismatch_matrix.json
```

共 14 个失配场景，全部：

```text
callback_count = 0
checkout_executed = false
```

### P2 连续绑定

| 场景 | 最终决策 |
|---|---|
| execution request ref 指向其他 request | `DENY` |
| transaction object ref 指向其他 request | `DENY` |
| execution order ref 指向其他 order | `DENY` |
| authority ref 不一致 | `DENY` |
| Agent ref 不一致 | `DENY` |
| payee 不一致 | `DENY` |
| amount 不一致 | `DENY` |
| currency 不一致 | `DENY` |

### P3 身份与执行者

| 场景 | 最终决策 |
|---|---|
| AgentIdentity / provider / executor 证据缺失 | `INDETERMINATE` |
| executor instance 不一致 | `DENY` |

### P4 上下文来源

| 场景 | 最终决策 |
|---|---|
| required source coverage 缺失 | `INDETERMINATE` |
| 检测到未授权 trusted state 变化 | `DENY` |
| current action 不是 `execute_payment` | `INDETERMINATE` |
| coverage digest 绑定到其他 amount | `INDETERMINATE` |

闸门直接调用现有 `observe_payment_execution_gate`，没有在 WebShop 层复制 P2/P3/P4 规则。

证据：EV-02。

## 7. Callback 异常边界

异常发生在 P1—P4 已经全部 `ALLOW`、实际尝试调用注入 seam 的时点。

处理结果：

```text
callback 实际尝试次数：1
自动重试次数：0
callback_result_ref：null
checkout_executed：false
最终 decision：INDETERMINATE
reason：checkout_callback_exception:RuntimeError
```

RuntimeGateRecord 保留“实际发生过一次 callback 尝试”的观测事实，但 outcome 不把该尝试解释为结账成功。

证据：EV-01、EV-04。

## 8. 依赖与副作用边界

生产模块导入：

```text
__future__
collections.abc
dataclasses
typing
adapters.webshop
models
payment_execution
trusted_execution
validator
```

未导入或调用：

```text
gym
web_agent_site
pyserini
Flask
Selenium / Playwright
requests / urllib / socket
subprocess / os / pathlib
文件读写
环境变量
UI
支付 provider / wallet / testnet
```

生产模块不包含：

```text
click[buy now]
SimServer.done()
```

动态测试封锁 `open`、socket、`urlopen`、`subprocess.run` 和 `os.getenv` 后，正常 ALLOW 仍只调用本地注入 callback 一次。

证据：EV-03、EV-07。

## 9. 测试与回归

| 验证 | 结果 | 证据 |
|---|---|---|
| 四态决策、回调计数和异常示例 | PASS | EV-01 |
| P2/P3/P4 失配矩阵 | 14/14 callback blocked | EV-02 |
| Python 编译、静态依赖和动态副作用审计 | PASS | EV-03 |
| runtime gate 专项测试 | 14/14 PASS | EV-04 |
| 主仓完整 unittest | 336/336 PASS | EV-05 |
| `python3 run_experiment.py` | 13/13 PASS | EV-06 |
| HEAD、范围、哈希和安全审计 | PASS | EV-07 |

## 10. 改动文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/webshop_runtime_gate.py` | `5aadec69b787825dc7909276d1ea6881f1620d911d4b7f83839bf3400f39e368` |
| `src/agentic_payment_experiment/__init__.py` | `f41704928b0dcd39d7666867bc69485fb8de40529ec7254c0a50cb5b4a19add3` |
| `tests/test_webshop_runtime_gate.py` | `a7fbfe1f340f3ac35934edd5fb71bb70b20969d763cc75166e688e29bfcddef8` |
| `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md` | `15c80abd6010b7aae6d82ccf153f2129b49a126a2140da1e8b784dbc18cb4523` |
| `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` | `36d6738a7c9ca2a68951ed136a3d80326935ad09ad4de6595e7b50ea7f1dc5c5` |

`src/agentic_payment_experiment/__init__.py` 在任务开始前已有继承改动，本任务只增加新 public API 的 import 和 `__all__` 两项导出。

## 11. 禁止范围核对

P9-B1 文件哈希保持不变：

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/adapters/webshop.py` | `035e6bb20d44b0a52be3f6adab2830c402e01f53839e917698343761c5481ec4` |
| `samples/external/webshop/pre_buy_now_candidate_v1.json` | `6e9d67c3b787cc2d9202bd22b30dec88bf9f920dfa3741bdeb364108a2a3c8e5` |
| `scripts/validation/webshop/export_webshop_commerce_fixture.py` | `aae4c6109586f20e6e78c35ba48b6c94dfee76e478134842731140f50a9382f0` |

另外确认：

```text
models.py diff 为空
validator.py diff 为空
主仓 HEAD = baseline HEAD
```

`payment_execution.py` 和 `trusted_execution/context_policy.py` 的未提交修改是本任务开始前已有的继承状态；本轮只调用其公开接口，没有编辑这些文件。

证据：EV-07。

## Deviations / 偏差

没有模型层、规则层或依赖偏差；现有 P1—P4 接口可以直接完成本任务。

Callback 异常采用合同允许的“确定性失败结果”分支：P1—P4 在调用前已给出 `ALLOW`，因此 callback 实际尝试一次；callback 抛错后 outcome 降级为 `INDETERMINATE`，`checkout_executed=false`，且不自动重试。`RuntimeGateRecord.callback_executed=true` 仅表示 callback 确实被调用，不表示结账成功。

## 12. 路线状态

```text
P9-A1  PASS
P9-A2  PASS
P9-B1  PASS
P9-B2  READY_FOR_REVIEW 候选
P9-C   未开始
P9-D   未开始
P9-E   已规划，基础能力完成后执行
```

P9-B2 仍是纯离线控制点。真实 WebShop runtime、真实 Buy Now、支付、履约和 UI 没有执行。

## 13. AC 映射

| AC | 状态 | 证据 |
|---|---|---|
| AC-01 explicit facts only | PASS | EV-01、EV-03、EV-04 |
| AC-02 P1 pre-payment validation | PASS | EV-01、EV-04 |
| AC-03 P2/P3/P4 runtime composition | PASS | EV-01、EV-02、EV-03 |
| AC-04 callback side-effect boundary | PASS | EV-01、EV-02、EV-04 |
| AC-05 realistic WebShop boundary examples | PASS | EV-01、EV-04 |
| AC-06 dependency and side-effect boundary | PASS | EV-03、EV-07 |
| AC-07 tests and regressions | PASS | EV-04、EV-05、EV-06 |
| AC-08 roadmap and handoff consistency | PASS，路线状态已更新，两轮交接前验证均无 `BLOCKING` | EV-07、EV-08、EV-09 |

## 14. VP 映射

| VP | 状态 | 证据 |
|---|---|---|
| VP-01 permissive mandate + fake callback | PASS | EV-01 |
| VP-02 restrictive fixture mandate | PASS | EV-01 |
| VP-03 confirmation and indeterminate matrix | PASS | EV-01 |
| VP-04 P2/P3/P4 mismatch matrix | PASS | EV-02 |
| VP-05 callback exception / no retry | PASS | EV-01、EV-04 |
| VP-06 static imports / side-effect audit | PASS | EV-03、EV-07 |
| VP-07 runtime-gate tests | PASS | EV-04 |
| VP-08 full regression / formal entrypoint | PASS | EV-05、EV-06 |
| VP-09 scope / hash / workflow | PASS，两轮交接前验证均无 `BLOCKING` | EV-07、EV-08、EV-09 |

## 15. 明确未发生事项

本轮没有：

- 运行 WebShop、`webshop38`、Flask、浏览器或后台服务；
- 执行真实或模拟环境中的 `click[buy now]`；
- 调用 `SimServer.done()`；
- 调用网络、API、LLM、钱包、测试网或真实支付；
- 创建真实订单、支付或履约副作用；
- 修改 P9-B1 adapter、fixture 或 export helper；
- 修改 `models.py`、`validator.py`、`payment_execution.py` 或 `trusted_execution/` 规则；
- 修改 UI 或开始 P9-E；
- 修改环境或安装依赖；
- commit、push 或 history rewrite。
