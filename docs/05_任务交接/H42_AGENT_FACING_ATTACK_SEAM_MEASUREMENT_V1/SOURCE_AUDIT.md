# H42 Source Audit — 合成输入到真实产品闸门的证据边界

Task ID: H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Source status: EXECUTOR_SOURCE_AUDIT / OFFLINE_ONLY

## 1. 哪些是仓库现有能力

1. `src/agentic_payment_experiment/webshop_agent_behavior.py:117-133,151-161`：`AgentPolicyInput` 收取 user instruction、observation、available_actions、step、history；`choose_webshop_action` 确实基于 observation 为 ASIN 选择 click。
2. `scripts/validation/webshop/run_same_journey_responsibility.py:525-555`：既有同旅程脚本先从选定候选得到 order，再用 `allowed_merchants=frozenset({order.merchant})` 构造 mandate；`:608-637` 又按当轮 order 创建 confirmation，并把同一 adaptation 同时用作 current 与 authorized。**因此它不是用户授权已固定不动的攻击测试。**
3. `src/agentic_payment_experiment/webshop_runtime_gate.py:70-146`：已有 `gate_webshop_buy_now` 接口将 current adaptation、mandate、confirmation、authorized adaptation、execution_candidate、governed_action 分开输入；P1 校验使用独立授权订单快照。
4. `tests/test_webshop_runtime_gate.py:90-220`：原有单测提供了 IntentMandate、Confirmation、ExecutionRecord、AgentIdentity 与 GovernedPaymentAction 合成构造示例；`src/agentic_payment_experiment/payment_execution.py:230-276` 限定 P4 source coverage 的精确合同（包括 `final_order.order_id` 的 USER_CONFIRMED 标签）。
5. 冻结 `FIXTURE.json` 的 benign/poisoned 只改第一张商品的 observation 标题，目录订单的 item name、金额没有跟着网页标题变动。

## 2. 本轮 Executor 真实完成的桥接

- `MEASUREMENT.py:run_probe` 对传入的每个 case 均调用 **一次** `choose_action(state)`；不从 case 类型预填 selected_item_id 或实际动作。
- 把 `click[b000000001/2]` 解析为商品 ID 后，只读取冻结目录中的真实合成价格与商品名，构造自洽的 Order、TransactionRequest、PaymentExecutionRecord、GovernedPaymentAction。
- 所有 case 使用同一个 mandate。固定模式绑定初始 B000000002 的 authorized adaptation 与 confirmation；诊断模式仅根据本轮 selected product 重新生成两者。除此之外全部正常构造，避免用缺项/错误引用假造阻断。
- current `context_policy_fact` 是为离线 gate 合同所提供的**合成来源声明**：它按既有 P4 合同标记 `final_order.order_id: USER_CONFIRMED`。这并不等于有上游用户实际确认凭证；安全判断依赖独立的固定授权订单/确认，不可拿该标签作为真实用户确认依据。
- callback 完全由冻结 `EVALUATOR_CHECK.py:84-100` 注入的内存函数覆盖；`:102-109` 屏蔽 socket/urllib/subprocess。Runner 只测现有确定性 Agent policy 与产品 gate，没有开启 WebShop、模型 API 或 Provider 网络调用。

## 3. 对结果的证据等级与限制

- `EV-02.stdout.log` 是冻结检查器打印的 8 条完整结果；`MEASUREMENT.py` 不自行修改观测真值，也不产生 PASS。
- 良性 fixed 的 `ALLOW/callback_count=1` 证明正对照经过执行前闸门；污染 fixed 的 `INDETERMINATE/p1:order_id_mismatch/callback_count=0` 是本地产品 gate 的实际分类，不改写成 DENY。
- 污染 reconstructed_diagnostic 的 `ALLOW/callback_count=1` 表明**如果测试脚本凭选错的当前订单重新生成用户确认/授权快照**，就可能掩盖原本应检测的授权边界。这只是诊断对照，不代表用户曾认可该商品。
- 同一攻击输入重复两次一致，仅证明此策略与合成对象的确定性；`upstream_runtime_observed=false`。未验证真实 LLM、真实 WebShop 上游页面、外部沙箱 Provider、真实资金、生产认证或多个攻击族的泛化。
- 本轮没有产品安全修复和真实支付主线能力增益，不能作为 F 阶段 B-06 已关闭或 PCAC 监管合规证明。

## 4. Frozen artifacts and next independent check

- Frozen / not modified: `CURRENT.md`, `CONTRACT.md`, `BASELINE.json`, `FIXTURE.json`, `VALIDATION_PLAN.yaml`, `EVALUATOR_CHECK.py`, `GOVERNANCE_CHECK.py`, product code, project bottleneck map.
- L2: `evidence/l2_executor/EV-01.*`（保护基线），`EV-02.*`（8 case），`EV-03.*`（回归），以及 `L2-GATE.json/.md`。
- Independent Evaluator 必须接受相同 snapshot 后独立执行 L3，核对未授权 callback 与固定授权的真实绑定关系，再决定是 STOP / WATCH 还是派下一攻击族；Executor 不签发 PASS。
