# Executor Report

Task ID: `P9-GOVERNED-PAYMENT-ACTION-OBJECT-TYPE-BOUNDARY-REPAIR-V1`  
Parent: `P9-GOVERNED-PAYMENT-ACTION-CONTRACT-V1`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

```yaml
executor_state: READY_FOR_REVIEW
current_role: Evaluator
review_requested: true
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

## 1. 小修结果

本轮只修复 `GovernedPaymentAction` 的最外层对象类型边界。

```text
action is None
→ 保持原有 MISSING_EVIDENCE / governed_action_missing

type(action) is GovernedPaymentAction
→ 继续原有字段级校验

其他任何对象
→ INVALID / governed_action_invalid_type
→ WebShop DENY
→ callback=0
→ 不读取对象属性
→ 不抛异常
```

生产代码只修改：

```text
src/agentic_payment_experiment/trusted_execution/governed_action.py
```

`webshop_runtime_gate.py` 未修改，说明现有 Gate 已能正确消费 verifier 返回的 `INVALID`。

## 2. 修复前评估者反例

EV-01 原始输出：

```text
PURE_LOOKALIKE
status= VALID
reasons= ('governed_action_binding_valid',)

PURE_DICT
exception= AttributeError
message= 'dict' object has no attribute 'action_type'

GATE_LOOKALIKE
decision= ALLOW
callback_count= 1
calls= 1

GATE_DICT
exception= AttributeError
message= 'dict' object has no attribute 'action_type'
```

问题本质：旧实现先调用 `_checked_values(action)`，再判断对象边界，因此 duck-typed 对象被信任，字典则在属性访问时异常。

## 3. 修复实现

严格边界位于 `_checked_values(...)` 和所有 `action.<field>` 访问之前：

```python
if action is None:
    return MISSING_EVIDENCE(governed_action_missing)

if type(action) is not GovernedPaymentAction:
    return GovernedActionBindingFact(
        status=VerificationStatus.INVALID,
        action_id=None,
        reason_codes=("governed_action_invalid_type",),
        checked_action_type=None,
        checked_order_ref=None,
        checked_request_ref=None,
        checked_payment_ref=None,
    )

checked = _checked_values(action)
# 原字段级校验继续
```

使用精确 `type(...) is ...`，不接受：

- `SimpleNamespace` 可变仿冒对象；
- 序列化字典；
- list；
- string；
- `GovernedPaymentAction` 子类；
- 属性访问会抛错的 proxy。

## 4. 修复后反例

EV-02 原始输出：

```text
PURE_LOOKALIKE
status= INVALID
action_id= None
reasons= ('governed_action_invalid_type',)
checked= (None, None, None, None)
exception=NONE

PURE_DICT
status= INVALID
action_id= None
reasons= ('governed_action_invalid_type',)
checked= (None, None, None, None)
exception=NONE

GATE_LOOKALIKE
decision= DENY
checkout_executed= False
callback_count= 0
calls= 0
runtime_gate_record= None
fact_status= INVALID
reasons= ('action:governed_action_invalid_type',)
exception=NONE

GATE_DICT
decision= DENY
checkout_executed= False
callback_count= 0
calls= 0
runtime_gate_record= None
fact_status= INVALID
reasons= ('action:governed_action_invalid_type',)
exception=NONE
```

## 5. 矩阵扩展

原 16 项保持不变，新增：

```text
mutable_lookalike_action_object
serialized_dict_action_object
```

两项结果：

```text
verification = INVALID
gate = DENY
callback = 0
reason = governed_action_invalid_type
```

EV-05：

```text
total=18
matched=18
failed=0
```

EV-09 逐项比较父任务 EV-01，确认原 16 个 case 的完整输出对象完全一致，primitive-only 序列化样例也完全一致。

## 6. 回归结果

```text
Governed Action：13/13 PASS
WebShop Runtime Gate：31/31 PASS
动作矩阵：18/18 matched
P2 + P4：27/27 PASS
全量测试：396/396 PASS
正式入口：13/13 PASS
```

保留行为：

- 精确 `GovernedPaymentAction` 仍为 `VALID`；
- `None` 仍为 `MISSING_EVIDENCE / governed_action_missing`；
- 字段级 missing / invalid / mismatch reason 未改变；
- P1—P4 决策未改变；
- 有效路径仍只执行一次 callback；
- 序列化格式未改变。

## Workspace Snapshot / 工作区快照

| 项目 | 结果 |
|---|---|
| HEAD | 8acaa9e4319240d258f14d8a23b1f15cc71d09b6 |
| Governed Action | 13/13 PASS |
| Runtime Gate | 31/31 PASS |
| 动作矩阵 | 18/18 matched |
| P2/P4 | 27/27 PASS |
| 全量 | 396/396 PASS |
| 正式入口 | 13/13 PASS |
| 网络、WebShop、Buy Now、支付副作用 | 未执行 |
| commit、push、history rewrite | 未执行 |

## 7. 改动文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/trusted_execution/governed_action.py` | `115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e` |
| `tests/trusted_execution/test_governed_action.py` | `67bfd682ae9fc5e1bf31b4431004f486577067cbf3d521c03691e7ca6f159cb9` |
| `tests/test_webshop_runtime_gate.py` | `6f35dc764e4596921fd11ad5d1fe9d636bee53a53dec7c0b4568d03c1db762ac` |
| `samples/external/webshop/governed_payment_action_matrix_v1.json` | `fe79911c986166f260e04650370a487e808c182f1b9e9e84804bb5a390c16b40` |
| `scripts/validation/webshop/run_governed_payment_action_matrix.py` | `a30ecba6a5e4ed2f2562efb158db1515446db673ee6b4399e388a4c36ca10e2b` |

保护文件：

| 文件 | 状态 |
|---|---|
| `webshop_runtime_gate.py` | 未修改，SHA `53cf9058...c1dd2` |
| package exports | 未修改 |
| `models.py` | 未修改 |
| `validator.py` | 未修改 |
| `order_validation.py` | 未修改 |
| `payment_execution.py` | 未修改 |
| `context_policy.py` | 未修改 |

## 8. AC 映射

| AC | 结果 | 证据 |
|---|---|---|
| AC-01 strict boundary | `None`、精确类型、其他对象三路分离；精确类型判断早于属性访问 | EV-02、EV-03、EV-09 |
| AC-02 stable fact / no exception | 非法外层对象统一返回全空 checked refs 和稳定 reason，无异常 | EV-02、EV-03 |
| AC-03 WebShop fail closed | 非法对象统一 DENY、callback=0、runtime record=null | EV-02、EV-04、EV-05 |
| AC-04 evaluator counterexamples | SimpleNamespace、dict、list、string、subclass、proxy 均覆盖 | EV-01、EV-02、EV-03、EV-04 |
| AC-05 matrix | 原 16 项保留，新增 2 项，18/18 matched | EV-05、EV-09 |
| AC-06 preserve prior behavior | 原 16 项完整输出与序列化逐项一致，P1—P4 回归通过 | EV-03 至 EV-09 |
| AC-07 scope / regression | 13、31、18、27、396、13/13 全通过；禁止动作未执行 | EV-03 至 EV-10 |

## 9. Evidence

### EV-01 — 修复前反例

- `evidence/EV-01.meta.json`
- `evidence/EV-01.stdout.log`
- `evidence/EV-01.stderr.log`

### EV-02 — 修复后反例

- `evidence/EV-02.meta.json`
- `evidence/EV-02.stdout.log`
- `evidence/EV-02.stderr.log`

### EV-03 — Governed Action 专项

命令：`python3 -m unittest tests.trusted_execution.test_governed_action -v`  
结果：13/13 PASS。

### EV-04 — Runtime Gate 专项

命令：`python3 -m unittest tests.test_webshop_runtime_gate -v`  
结果：31/31 PASS。

### EV-05 — 动作矩阵

命令：`PYTHONPATH=src python3 scripts/validation/webshop/run_governed_payment_action_matrix.py`  
结果：18/18 matched。

### EV-06 — P2/P4 关联回归

命令：`python3 -m unittest tests.trusted_execution.test_payment_binding tests.trusted_execution.test_context_policy -v`  
结果：27/27 PASS。

### EV-07 — 全量回归

命令：`PYTHONPATH=src python3 -m unittest discover -s tests -v`  
结果：396/396 PASS。

### EV-08 — 正式入口

命令：`python3 run_experiment.py`  
结果：13/13 PASS。

### EV-09 — 范围与父矩阵一致性审计

结果：严格边界、保护文件、父 16 项逐项一致和禁止动作审计全部通过。

### EV-10 — 工作流验证

最终工作流 validator，无 `BLOCKING` finding。

## 10. 偏差与限制

- 修复前证据脚本第一次运行仅因未加入仓库根目录而发生 `ModuleNotFoundError`，未执行反例；随后覆盖为 EV-01 的真实修复前输出。
- 测试开发过程中，矩阵测试在规范尚未增加两项时出现一次预期的 `18 != 16`；补齐矩阵后正式 EV-03 为 13/13 PASS。
- 未修改 Runtime Gate 或公共动作字段。
- 未新增动作类型、Source Lineage、Taint Propagation、提示注入或 UI。
- 未运行 WebShop、Buy Now、支付、网络、API、依赖安装或环境创建。
- 未执行 commit、push 或 history rewrite。
