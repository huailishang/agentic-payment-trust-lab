# 第一纵向切片：Delegated Authority v1

> 日期：2026-07-29
> 状态：已实现并通过 P1 Gate
> 目标：把 Agent Trust Control Plane 的第一条 P0 能力真正接入现有代码，而不是继续增加 S14 / D1。

## 1. 这次只解决一个问题

> **用户确认过的授权和交易对象一旦发生关键版本变化，旧确认不能被静默复用。**

最小链路：

```text
Delegated Authority
    ↓ authority_version
Authorized Order
    ↓ order version / critical fields
Payment Request
    ↓
判断旧确认是否仍然有效
    ↓
ALLOW / CONFIRMATION_REQUIRED / DENY
    ↓
Replay Evidence 解释原因
```

这次不解决完整 Agent 身份认证、签名、PKI、真实用户交互或真实支付。

结合 2026-07-29 的外部信源复核，本切片还明确承担一个架构职责：**先提供未来 Runtime Authorization Gate 所需的 Authority / Confirmation 输入，但本轮不提前实现通用 Gate。**

```text
P1 本轮输出
authority_ref
+ authority_version
+ confirmation_policy
+ confirmation_binding_fact
        ↓
未来和 P2 / P3 / P4 输入汇合
        ↓
Runtime Authorization Gate
```

外部参考见 [Agent 身份与运行时授权开源项目参考](../reference/Agent身份与运行时授权开源项目参考_20260729.md)。

## 2. 为什么复用 S08 / S09

### S08 已经有

```text
max_amount = 550
confirmation_above = 500
request.amount = 520
=> CONFIRMATION_REQUIRED
```

它验证“授权范围内，但自主执行权限不足”。

### S09 已经有

```text
用户确认 order v1 = 480
最终 order v2 = 490
490 仍低于 confirmation_above = 500
=> 仍需重新确认
```

它已经隐含了最关键原则：

> **用户确认的是具体交易对象，不只是一个金额阈值。**

所以第一条纵向切片不新增场景编号，只把 S08/S09 背后的规则从“案例规则”升级成明确的 Delegated Authority / Confirmation Validity 能力。

## 3. 最小代码变化

### 3.1 `IntentMandate` 增加最小授权版本语义

建议增加：

```python
authority_version: str = "v1"
```

暂时不把 `IntentMandate` 重命名成 `DelegatedAuthority`，避免大范围机械重构。

本轮只确认：

```text
mandate_id
+ authority_version
= 当前被确认的授权版本
```

### 3.2 Order 显式记录它绑定的授权版本

当前已经有：

```python
mandate_ref
order_version
```

建议最小增加：

```python
authority_version_ref: str | None = None
```

含义：

> 这个订单是在用户哪个授权版本下形成 / 确认的。

### 3.3 新增“确认有效性”确定性事实

建议放在 `trusted_execution` 中，名字保持事实型，不直接返回支付业务决定：

```python
verify_confirmation_binding(
    *,
    expected_authority_id: str,
    expected_authority_version: str,
    authorized_order: Order,
    final_order: Order,
) -> VerificationResult
```

它只回答：

```text
授权引用是否一致
授权版本是否一致
授权订单与最终订单关键绑定是否仍然成立
证据是否缺失
```

它不直接返回：

```text
ALLOW
DENY
CONFIRMATION_REQUIRED
```

支付域继续决定业务动作。

## 4. 支付域规则

第一版只冻结以下规则。

### R1. 授权版本不一致

```text
authorized_order.authority_version_ref
    !=
mandate.authority_version

=> 旧确认失效
=> CONFIRMATION_REQUIRED
```

不是直接 `DENY`，因为这可能只是用户更新了授权，需要重新确认交易对象。

### R2. 最终订单关键字段变化

沿用当前 S09 语义，至少包括：

```text
amount
merchant
payee
items
currency
```

如果最终订单和已确认订单发生关键变化：

```text
=> 旧确认失效
=> CONFIRMATION_REQUIRED
```

即使最终金额仍低于 `confirmation_above`，也不能静默继续。

### R3. 非关键表现变化不能误杀

规范化后语义等价的表示变化，不应导致确认失效。

继续复用现有 Canonicalization / Binding 能力。

### R4. 授权引用错误仍是结构问题

例如：

```text
authorized_order.mandate_ref != mandate.mandate_id
```

继续按现有结构校验处理，不把所有异常都改成“重新确认”。

## 5. Replay Evidence 最小输出

本轮不新增完整事件存储，只先把现有 `EvidenceRef` 变得能解释这条链。

建议至少新增 / 固化：

```text
authority_ref
authority_version
authorized_order_authority_version_ref
final_order_version
confirmation_binding_status
confirmation_binding_reason
confirmation_invalidated_by
```

例如 S09：

```text
authority_ref = mandate-shoes-009
authority_version = v1
authorized_order_authority_version_ref = v1
final_order_version = v2
confirmation_binding_status = INVALID
confirmation_invalidated_by = order_total_changed, order_item_unit_amount_changed
```

这样 UI 未来可以直接解释：

> 用户确认的是订单 v1；最终订单变成 v2，关键金额发生变化，因此旧确认失效，需要重新确认。

而不是只展示：

> S09 FAIL / M5 PASS。

## 6. 测试先行

建议继续 TDD。

### 第一组：授权版本

新增单元测试：

1. `authority_version_ref == authority_version` → 绑定可继续。
2. `authority_version_ref != authority_version` → 确认绑定失效。
3. `authority_version_ref missing` → `MISSING_EVIDENCE`，不能静默放行。

### 第二组：订单变化

复用 `tests/test_order_validation.py`：

1. 同一订单语义 → 不要求重新确认。
2. 金额变化 → `CONFIRMATION_REQUIRED`。
3. payee 变化 → `CONFIRMATION_REQUIRED` 或沿现有高风险规则处理。
4. item 变化 → `CONFIRMATION_REQUIRED`。
5. 纯序列化 / 表示差异 → 不误判。

### 第三组：S08 / S09 回归

必须保持：

```text
S08 -> CONFIRMATION_REQUIRED
S09 -> CONFIRMATION_REQUIRED
```

但证据要升级成能说明：

```text
S08 = autonomy / confirmation policy 边界
S09 = confirmed object binding 失效
```

### 第四组：全量回归

运行当前项目全量测试。

验收：

```text
0 新增失败
M5 关键指标不退化
现有 PayBench / AP2 / Attack 不因字段变化被破坏
```

## 7. 预计涉及文件

优先控制在：

```text
src/agentic_payment_experiment/models.py
src/agentic_payment_experiment/trusted_execution/execution_facts.py
src/agentic_payment_experiment/order_validation.py
src/agentic_payment_experiment/validator.py
samples/scenarios/S08_confirmation_required.json
samples/scenarios/S09_order_total_changed.json
tests/test_order_validation.py
tests/test_validator.py
```

如果可以避免，本轮不要碰：

```text
lab_overview.py
html_report.py
interactive UI 大结构
AP2 / ACP 大规模字段映射
payment_recovery.py
remediation.py
```

UI 只在现有字段消费确实报错时做最小兼容修复。

## 8. 验收标准

本切片只有满足以下条件才算完成：

```text
[ ] IntentMandate 有明确 authority_version
[ ] Order 能声明绑定哪个 authority version
[ ] Trusted Execution 能返回 confirmation binding 事实
[ ] 支付域仍拥有最终 ALLOW / CONFIRMATION_REQUIRED / DENY 决定权
[ ] S08 继续验证确认策略边界
[ ] S09 继续验证订单变化导致旧确认失效
[ ] 缺证据不能静默 ALLOW
[ ] Evidence 能解释“哪个授权版本 / 哪个对象变化导致重确认”
[ ] 专项测试通过
[ ] 全量回归通过
[ ] 不新增 S14
[ ] 不重构主 UI
```

## 9. 2026-07-30 实施状态

已实现并接入主链：

```text
ConfirmationRecord
    -> 保存 authority_id / authority_version / order_id / order_version
    -> 保存确认时关键交易内容的 canonical SHA-256 摘要
    -> 保存 confirmed_at / expires_at / status
当前订单
    -> 重新计算同一关键内容摘要
verify_confirmation_binding()
    -> VALID / INVALID / MISSING_EVIDENCE + reason + invalidated_by
execute_with_confirmation_gate()
    -> 仅 VALID 执行回调；INVALID -> CONFIRMATION_REQUIRED；缺证据 -> INDETERMINATE
```

`IntentMandate.authority_version`、`Order.authority_version_ref`、Scenario Loader、`validate_request()`、S09、交互实验、ACP 对照、结果卡和冻结回归基线均已接入。S08 仍只表达确认阈值，不与“已确认对象发生变化”混为一条规则。

验证结果：P1 核心、验证器与主结果专项 `32 passed, 4 subtests passed`；完整 `unittest` 为 `200 tests OK`；正式入口 S01—S13 `13/13 PASS`，M5 与内部冻结基线 PASS。订单版本标签单独变化不替代内容 Hash，也不会无条件误杀；商品展示顺序变化也不会产生假失效；授权版本变化、关键内容变化、确认过期或证据缺失会阻断静默执行。

P1 Gate 已满足；后续 P2 连续 Binding 到 Payment 也已完成，详见 [P1 授权绑定与执行前核验执行记录](../04_验证体系/P1授权绑定与执行前核验执行记录_20260730.md) 与 [P2 连续支付绑定执行记录](../04_验证体系/P2连续支付绑定执行记录_20260730.md)。

## 10. P1 完整验收后再决定什么

本切片通过后的判断：

1. `IntentMandate` 是否值得正式重命名 / 拆成 Delegated Authority。
2. `TransactionRequest` 是否需要拆出独立 Payment Request 对象。
3. Binding 是否进一步升级成完整 Intent → Authority → Order → Payment 链。
4. UI 是否开始从 M/S 导航改成“授权 / 身份 / 绑定 / 执行 / 恢复 / 审计”。
5. 第二条纵向切片应该是 Agent Identity，还是 Trust Source / Replay。

## 11. 当前执行顺序

```text
领域模型【已冻结】
    ↓
P1 TDD 实现【已完成】
    ↓
S08 / S09 专项验证【已完成】
    ↓
全量回归 + M5【已完成】
    ↓
P1 Gate【PASS】
    ↓
P2 连续 Binding 到 Payment【已完成】
    ↓
P3 Agent / Executor Identity【当前下一步】
```
