# Evaluator Review

Task ID: `P9-GOVERNED-PAYMENT-ACTION-CONTRACT-V1`  
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

执行者完成了动作字段、引用、时间和 P1—P4 接线，名义回归也全部通过：

```text
动作矩阵                    16/16 PASS
Governed Action 专项        12/12 PASS
Runtime Gate 专项           30/30 PASS
P2/P4 关联测试              27/27 PASS
全量测试                    394/394 PASS
正式入口                    13/13 PASS
workflow validator          OK
```

但是，独立评估发现动作对象的最外层类型边界没有被验证。

因此系统当前不能证明：

> 只有真正的、不可变的 `GovernedPaymentAction` 才能继续进入受控回调。

本轮打回。

## 2. 阻断缺陷

### F-01 — 普通可变对象可伪装成合法动作契约并触发 callback

评估者把合法动作的字段复制到普通可变对象：

```python
SimpleNamespace(**valid_action.__dict__)
```

该对象：

- 不是 `GovernedPaymentAction`；
- 不是 frozen dataclass；
- 校验后仍可以修改；
- 仅仅因为字段名和值相同，就被验证器判定为 `VALID`。

独立结果：

```text
mutable verifier status = VALID
mutable gate decision   = ALLOW
callback_count          = 1
callback observations   = 1
mutable after verify    = true
```

这意味着当前实现实际上是：

```text
任何“长得像动作单”的对象
→ 都可能被当成正式动作契约
→ 进入 P2—P4
→ 最终触发 callback
```

这与任务核心目标“不可变动作对象”相冲突。

### F-02 — 字典输入没有失败关闭，而是直接抛异常

评估者把合法动作序列化为字典后传入验证器和 Runtime Gate。

独立结果：

```text
AttributeError:
'dict' object has no attribute 'action_type'
```

验证器没有返回：

```text
VerificationStatus.INVALID
+ stable reason code
```

Runtime Gate 也没有返回：

```text
DENY
+ callback_count = 0
```

而是直接异常退出。

这违反了“错误类型必须失败关闭”的要求。

## 3. 根因

`verify_governed_payment_action(...)` 一进入函数就执行：

```python
checked = _checked_values(action)
```

之后直接访问：

```python
action.action_id
action.action_type
action.subject_ref
...
```

但没有先执行严格的动作对象类型检查，例如：

```python
type(action) is GovernedPaymentAction
```

因此出现两个方向的问题：

```text
有同名属性的可变对象 → 被 duck typing 放行
没有属性的 dict       → AttributeError
```

## 4. 独立证据

### RV-EV-01 — 动作对象类型边界反例

路径：

```text
docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/
evidence/RV-EV-01_action_object_type_boundary.py
```

原始结果：

```text
mutable_verifier_status       = VALID
mutable_gate_decision         = ALLOW
mutable_gate_callback_count   = 1
mutable_was_mutated_after_verification = true

dict_verifier_exception      = AttributeError
dict_gate_exception          = AttributeError
```

### 其他独立重跑

| 证据 | 内容 | 结果 |
|---|---|---|
| `RV-EV-02` | 现有 16 项动作矩阵 | 16/16 PASS |
| `RV-EV-03` | Governed Action 专项 | 12/12 PASS |
| `RV-EV-04` | Runtime Gate 专项 | 30/30 PASS |
| `RV-EV-05` | P2/P4 关联测试 | 27/27 PASS |
| `RV-EV-06` | 全量 unittest | 394/394 PASS |
| `RV-EV-07` | 正式入口 | 13/13 PASS |

结论是：现有测试均通过，但测试集遗漏了真正决定“不可变动作契约”是否成立的外层对象类型边界。

## 5. AC 裁决

| AC | 裁决 | 原因 |
|---|---|---|
| AC-01 immutable and primitive-only action contract | 不通过 | 验证器接受普通可变 `SimpleNamespace` 为 VALID，无法保证进入门禁的是不可变动作契约 |
| AC-02 mandatory evidence and exact action semantics | 不通过 | 非动作对象类型没有稳定 INVALID；dict 直接抛异常 |
| AC-03 authority and subject binding | 通过 | 字段级独立反例符合预期 |
| AC-04 order, request and payment binding | 通过 | 动作引用与 execution chain 已绑定，P2 继续保留 |
| AC-05 Agent, executor and context-action binding | 通过 | 字段链和 P3/P4 关联符合合同 |
| AC-06 temporal and identity boundaries | 通过 | 时间前后界及标识碰撞符合合同 |
| AC-07 WebShop Runtime Gate consumer | 不通过 | 可变伪动作被判 VALID 并触发一次 callback；dict 导致异常而不是 DENY |
| AC-08 valid action does not replace P1—P4 | 通过 | 对真正 `GovernedPaymentAction` 的 P1—P4 回归符合预期 |
| AC-09 machine-readable action matrix | 通过但覆盖不足 | 已满足合同列出的 16 项，但没有覆盖外层动作对象类型；修复包必须补入固定回归 |
| AC-10 side-effect, scope and regressions | 通过名义回归 | 394/394 与 13/13 通过，但不能抵消 AC-01、AC-02、AC-07 的阻断缺陷 |

## 6. 最终结论

```text
REJECTED
```

不是整体设计方向错误，也不需要重做支付动作契约。

需要修复的是一个非常集中的信任边界：

```text
只有严格的 GovernedPaymentAction 实例
才允许进入字段校验

其他任何 supplied 对象
→ INVALID
→ stable reason code
→ WebShop DENY
→ callback = 0
→ 不抛异常
```

## 7. 修复路由

已冻结修复任务：

```text
P9-GOVERNED-PAYMENT-ACTION-OBJECT-TYPE-BOUNDARY-REPAIR-V1
```

修复包只处理 F-01 和 F-02，不增加新动作类型，不进入 Source Lineage、提示注入、UI 或真实支付。
