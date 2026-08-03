# Executor Report

Task ID: `P9-GOVERNED-PAYMENT-ACTION-CONTRACT-V1`  
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
network_call_performed: false
api_call_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 执行结果

本轮完成 P9-C2-A 的单一治理动作类型：`EXECUTE_PAYMENT`。

```text
Agent / WebShop 准备执行支付
        ↓
GovernedPaymentAction
        ↓
verify_governed_payment_action（纯校验）
        ↓
GovernedActionBindingFact
        ↓
VALID 才继续既有 P2 → P3 → P4 → injected callback
```

动作契约只记录并验证“准备执行什么动作”，不执行支付、回调、网络、文件、进程或环境操作。

## 2. 公共动作契约

新增以下公开类型：

```python
class GovernedActionType(str, Enum):
    EXECUTE_PAYMENT = "execute_payment"

class SideEffectClass(str, Enum):
    PAYMENT_EXECUTION = "PAYMENT_EXECUTION"

class ActionReversibility(str, Enum):
    COMPENSATABLE_NOT_REVERSIBLE = "COMPENSATABLE_NOT_REVERSIBLE"

@dataclass(frozen=True)
class GovernedPaymentAction:
    action_id: str
    action_type: GovernedActionType
    subject_ref: str
    agent_ref: str
    executor_ref: str
    authority_ref: str
    authority_version: str
    order_ref: str
    order_version: str
    request_ref: str
    payment_ref: str
    source_refs: tuple[str, ...]
    side_effect_class: SideEffectClass
    reversibility: ActionReversibility
    occurred_at: datetime

    def to_dict(self) -> dict[str, object]: ...
```

V1 只支持 `EXECUTE_PAYMENT`。动作对象不包含自然语言指令、函数、任意工具参数或可变字典。

## 3. 验证事实与 API

```python
@dataclass(frozen=True)
class GovernedActionBindingFact:
    status: VerificationStatus
    action_id: str | None
    reason_codes: tuple[str, ...]
    checked_action_type: str | None
    checked_order_ref: str | None
    checked_request_ref: str | None
    checked_payment_ref: str | None

    def to_dict(self) -> dict[str, object]: ...


def verify_governed_payment_action(
    action,
    *,
    mandate,
    order,
    request,
    execution,
    agent_identity,
    current_executor_instance_ref,
    context_policy_fact,
) -> GovernedActionBindingFact: ...
```

验证器只分类证据：

| 验证状态 | 含义 | WebShop Gate 映射 |
|---|---|---|
| `VALID` | 动作合同与全部显式引用一致 | 继续现有 P2—P4 |
| `MISSING_EVIDENCE` | 必要字段或外部证据缺失 | `INDETERMINATE`，callback=0 |
| `INVALID` | 类型不可信、引用冲突或边界违规 | `DENY`，callback=0 |

字符串不会被静默转换为可信枚举。例如普通字符串 `execute_payment` 不是 `GovernedActionType.EXECUTE_PAYMENT`，结果为 `INVALID`。

## 4. 绑定规则

### 4.1 动作语义

```text
action_type       = EXECUTE_PAYMENT
side_effect_class = PAYMENT_EXECUTION
reversibility     = COMPENSATABLE_NOT_REVERSIBLE
source_refs       = 至少一个非空显式引用
```

### 4.2 主体与授权

```text
subject_ref       == mandate.user_id
authority_ref     == mandate.mandate_id
authority_version == mandate.authority_version
```

### 4.3 订单、请求与支付

```text
order_ref     == order.order_id
order_version == order.order_version
request_ref   == request.request_id
payment_ref   == execution.payment_id

execution.request_id == request.request_id
execution.order_id   == order.order_id
```

动作校验只验证引用连续性；金额、币种、收款方等完整 P2 规则仍由原有支付执行门禁负责。

### 4.4 Agent、Executor 与 Context Action

```text
action.agent_ref == request.agent_id
                 == mandate.expected_agent_id
                 == agent_identity.agent_id

action.executor_ref == current_executor_instance_ref
                    == agent_identity.executor_instance_id

action.action_type.value == context_policy_fact.current_action
```

有效动作不能修复或覆盖无效 P3/P4 事实。

### 4.5 时间与标识

```text
request.occurred_at <= action.occurred_at <= execution.occurred_at
```

`action_id` 必须非空，并且不能与 order、request 或 payment 标识碰撞。

## 5. WebShop Runtime Gate 消费行为

新增可选 keyword-only 参数：

```python
def gate_webshop_buy_now(
    ...,
    authorized_adaptation=None,
    governed_action=None,
) -> WebShopBuyNowGateOutcome: ...
```

输出新增结构化字段：

```python
WebShopBuyNowGateOutcome.governed_action_fact
```

执行顺序：

```text
P1 / 订单快照连续性
        ↓ ALLOW
Governed Payment Action 验证（仅在 supplied 时）
        ↓ VALID
P2 支付执行绑定
        ↓
P3 Agent / Executor 身份
        ↓
P4 Context Policy
        ↓
唯一 injected callback
```

当 `governed_action=None` 时，旧调用、原有决策与 callback 次数保持不变，`governed_action_fact=None`。

当提供动作时：

| 动作事实 | Gate 决策 | Runtime record | callback |
|---|---|---|---:|
| VALID | 继续 P2—P4 | 由既有门禁生成 | 最终 ALLOW 时 1 |
| MISSING_EVIDENCE | INDETERMINATE | null | 0 |
| INVALID | DENY | null | 0 |

动作阻断原因使用稳定命名空间 `action:<reason_code>`。无效动作不会被其他参数重新构造或替换。

## 6. P1—P4 保留验证

带有效动作合同的回归结果：

| 既有门禁 | 注入反例 | 结果 |
|---|---|---|
| P1 | mandate 超预算 | 既有 `DENY`，callback=0 |
| P2 | execution amount 不一致 | action `VALID`，P2 `DENY`，callback=0 |
| P3 | provider 不一致 | action `VALID`，P3 `DENY`，callback=0 |
| P4 | source coverage value 不一致 | action `VALID`，P4 `INDETERMINATE`，callback=0 |
| 全部有效 | 无异常 | `ALLOW`，callback=1 |

动作合同是新增治理边界，不替代 P1—P4。

## 7. Primitive-only 序列化示例

EV-01 固定样例：

```json
{
  "action": {
    "action_id": "webshop-action-1",
    "action_type": "execute_payment",
    "agent_ref": "webshop-agent-1",
    "authority_ref": "experiment-context-mandate-ref-v1",
    "authority_version": "experiment-authority-v1",
    "executor_ref": "offline-webshop-executor",
    "occurred_at": "2026-08-02T05:00:00.500000+00:00",
    "order_ref": "webshop-order-9eccab2b0154fca4af27f322",
    "order_version": "webshop-v1",
    "payment_ref": "webshop-payment-candidate-1",
    "request_ref": "webshop-request-6c6a78eddffdb552c2af66ef",
    "reversibility": "COMPENSATABLE_NOT_REVERSIBLE",
    "side_effect_class": "PAYMENT_EXECUTION",
    "source_refs": [
      "source:webshop-checkout-snapshot",
      "source:user-confirmation"
    ],
    "subject_ref": "webshop-user-1"
  },
  "verification": {
    "action_id": "webshop-action-1",
    "checked_action_type": "execute_payment",
    "checked_order_ref": "webshop-order-9eccab2b0154fca4af27f322",
    "checked_payment_ref": "webshop-payment-candidate-1",
    "checked_request_ref": "webshop-request-6c6a78eddffdb552c2af66ef",
    "reason_codes": ["governed_action_binding_valid"],
    "status": "VALID"
  }
}
```

输出只含 null、字符串、数字、布尔、列表和字典；datetime 使用 ISO-8601，enum 使用稳定 value，tuple 序列化为 list。

## 8. 动作矩阵

规范与执行器：

```text
samples/external/webshop/governed_payment_action_matrix_v1.json
scripts/validation/webshop/run_governed_payment_action_matrix.py
```

EV-01 结果：

```text
total=16
matched=16
failed=0
```

| case | verification | gate | callback | 主要原因 |
|---|---|---|---:|---|
| valid_execute_payment | VALID | ALLOW | 1 | governed_action_binding_valid |
| missing_action_id | MISSING_EVIDENCE | INDETERMINATE | 0 | action_id_missing |
| unsupported_action_type_or_invalid_type | INVALID | DENY | 0 | action_type_invalid |
| subject_mismatch | INVALID | DENY | 0 | subject_ref_mismatch |
| authority_mismatch | INVALID | DENY | 0 | authority_ref_mismatch |
| authority_version_mismatch | INVALID | DENY | 0 | authority_version_mismatch |
| order_ref_mismatch | INVALID | DENY | 0 | order_ref_mismatch |
| order_version_mismatch | INVALID | DENY | 0 | order_version_mismatch |
| request_ref_mismatch | INVALID | DENY | 0 | request_ref_mismatch |
| payment_ref_mismatch | INVALID | DENY | 0 | payment_ref_mismatch |
| agent_mismatch | INVALID | DENY | 0 | agent_ref_*_mismatch |
| executor_mismatch | INVALID | DENY | 0 | executor_ref_*_mismatch |
| context_action_mismatch | INVALID | DENY | 0 | context_action_mismatch |
| action_before_request | INVALID | DENY | 0 | action_before_request |
| action_after_execution | INVALID | DENY | 0 | action_after_execution |
| identifier_collision | INVALID | DENY | 0 | action_id_order_ref_collision |

每项均输出 expected/actual status、expected/actual gate decision、callback count、reason codes、action/order/request/payment refs，以及 `no_real_buy_now=true`、`no_real_payment=true`。

## Workspace Snapshot / 工作区快照

| 项目 | 结果 |
|---|---|
| HEAD | `8acaa9e4319240d258f14d8a23b1f15cc71d09b6` |
| 动作矩阵 | 16/16 matched |
| Governed Action 专项 | 12/12 PASS |
| Runtime Gate 专项 | 30/30 PASS |
| P2/P4 关联测试 | 27/27 PASS |
| 全量测试 | 394/394 PASS |
| 正式入口 | 13/13 PASS |
| WebShop / Buy Now | 未运行 |
| 网络 / API / 依赖安装 / 环境创建 | 未执行 |
| 支付 / 查询 / 履约 / 退款 / 争议副作用 | 未执行 |
| commit / push / history rewrite | 未执行 |

仓库中存在此前任务继承的未提交改动。本轮没有清理、暂存、提交或重写这些改动。

## Changed files / 改动文件

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/trusted_execution/governed_action.py` | `a0950d80b86c48b3eb585315a0342e804e8a57384ca9b37c1ab55da103a5b047` |
| `src/agentic_payment_experiment/trusted_execution/__init__.py` | `62ebd2a8a9d06d57f3948461e306ad4603b5750104de052e15a3deed35d29551` |
| `src/agentic_payment_experiment/__init__.py` | `3d7c3cc93654d5353eaa6b7f9c371f890f79712cd1e158c2e430aeab628fadbe` |
| `src/agentic_payment_experiment/webshop_runtime_gate.py` | `53cf905867905ae73f2886c4612a6d19cc839420677afe4f0eb4f655c87c1dd2` |
| `tests/trusted_execution/test_governed_action.py` | `51242c0cbfe65691b3b3bbf548f5ff6237e344d35d5f0a4fd4ac208a0cdd28d0` |
| `tests/test_webshop_runtime_gate.py` | `4a6db0197c787e966e3e1425e3ec8095643a2c9a61cfd57bbe384d4c966bd577` |
| `samples/external/webshop/governed_payment_action_matrix_v1.json` | `db719ebdf33ff3f09be6d2fcefcd908c5f7a4ceefa5c9168944370f7bc4c5222` |
| `scripts/validation/webshop/run_governed_payment_action_matrix.py` | `93344a77edb3b05cc73b09700ac38aa34d4b08195af908509dae2609ac341e0e` |
| `REPORT.md` | 本报告 |
| `evidence/EV-*` | 原始证据三件套与范围审计脚本 |
| `CURRENT.md` | 仅用于原子交接 |

保护范围：

- `models.py`、`validator.py`、`order_validation.py` 的 git diff 为空；
- `payment_execution.py` SHA-256 保持 `25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71`；
- `context_policy.py` SHA-256 保持 `be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56`。

## 9. AC 映射

| AC | 结果 | 证据 |
|---|---|---|
| AC-01 immutable / primitive-only | action 与 fact 为 frozen dataclass；datetime/enum/tuple 稳定序列化；无可执行字段 | EV-01、EV-02、EV-07 |
| AC-02 mandatory semantics | 必填缺失→MISSING；字符串枚举/容器错误→INVALID；只支持 EXECUTE_PAYMENT | EV-01、EV-02、EV-07 |
| AC-03 authority / subject | subject、authority、authority-version 独立反例均 INVALID | EV-01、EV-02 |
| AC-04 order / request / payment | 四类 action refs 与 execution chain 独立校验；既有 P2 保留 | EV-01、EV-02、EV-03、EV-04 |
| AC-05 Agent / executor / context | action、request、mandate、identity、current executor 与 current_action 全链绑定 | EV-01、EV-02、EV-03、EV-04 |
| AC-06 time / identity | request≤action≤execution；前后越界与三类标识碰撞 INVALID | EV-01、EV-02 |
| AC-07 WebShop consumer | 可选 keyword-only；VALID 继续；MISSING→INDETERMINATE；INVALID→DENY；fact 被保留 | EV-01、EV-03、EV-07 |
| AC-08 preserve P1—P4 | 有效 action 下 P1/P2/P3/P4 仍分别阻断；全有效 callback=1 | EV-03、EV-04、EV-05 |
| AC-09 action matrix | 16 项 status/decision/callback/reasons/refs/limitations 完整且全匹配 | EV-01、EV-02 |
| AC-10 side effects / regressions | 静态审计通过；12、30、27、394、13/13 全通过；工作流无 BLOCKING | EV-02 至 EV-08 |

## Deviations / 偏差与未解决项

- 无产品范围偏差。
- 动作矩阵开发期首次试跑未传现有 P1 confirmation record，旧 P1 正确返回 `INDETERMINATE`；正式矩阵补齐固定确认记录后，EV-01 为 16/16。该过程未改变 P1 规则。
- 证据批量采集首次使用 shell 临时变量时，被本地桥接层展开为空；没有执行测试或产生有效证据。最终 EV-01 至 EV-07 使用完整路径采集，退出码均为 0。
- 报告首次通过 shell heredoc 写入时，Markdown 反引号被桥接 shell 误解析；该污染文件已通过受控文件写入接口完整覆盖。产品代码和正式证据未受影响。
- 未实现 Source Lineage、Taint Propagation、提示注入组合测试、UI 或其他动作类型。
- 未执行任何合同禁止动作。

## EV-01

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-09
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-01.stderr.log

机器可读动作矩阵与 primitive-only 序列化样例。结果：16/16 matched。

## EV-02

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-09, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-02.stderr.log

命令：`python3 -m unittest tests.trusted_execution.test_governed_action -v`。结果：12/12 PASS。

## EV-03

- AC: AC-07, AC-08, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-03.stderr.log

命令：`python3 -m unittest tests.test_webshop_runtime_gate -v`。结果：30/30 PASS。

## EV-04

- AC: AC-04, AC-05, AC-08, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-04.stderr.log

命令：`python3 -m unittest tests.trusted_execution.test_payment_binding tests.trusted_execution.test_context_policy -v`。结果：27/27 PASS。

## EV-05

- AC: AC-08, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-05.stderr.log

命令：`PYTHONPATH=src python3 -m unittest discover -s tests -v`。结果：394/394 PASS。

## EV-06

- AC: AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-06.stderr.log

命令：`python3 run_experiment.py`。结果：`total=13 passed=13 failed=0`。

## EV-07

- AC: AC-01, AC-02, AC-07, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-07.stderr.log

哈希、保护规则、静态 API、单动作类型、禁止依赖、零 callback 调用和未使用授权审计。结果：exit code 0。

## EV-08

- AC: AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_CONTRACT_V1/evidence/EV-08.stderr.log

最终工作流验证；要求无 `BLOCKING` finding。
