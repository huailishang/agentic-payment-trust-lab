# H87 Executor report

Task ID: H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Executor status: SUBMITTED_FOR_REVIEW

## Workspace snapshot

冻结 INPUTS.json SHA-256 c8340416625e05879767fe5558eac235acd821075431c58969084719faaad67e；HEAD与198项输入核对通过，源集合不变。三轮VP-01均PASS，第三轮VP-03及VP-04结束再次核验通过。原有CURRENT、地图r146、历史未跟踪交接文件及准备材料为执行前已有差异；未修改地图或历史包。使用现有原生Windows Conda agent Python 3.12.13，未安装依赖。

## Changed files

仅CURRENT本任务路由、本任务REPORT及evidence：三轮独立原始L2、连续ATTEMPT_LEDGER.jsonl、局部runtime/Python312/site-packages/tests/__init__.py、OWNER_AUTHORIZATION_20261124.md、REPORT.blocked-attempt-2.md。原冻结合同、计划、检查器、产品和原测试不改；无SQL更新、无门禁猴补。第二轮原阻塞报告逐字节封存。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/L2-GATE.json
- Validation plan: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- 第一次L2：2/4；VP-03/04因第三方tests包遮蔽本仓命名空间而失败。原证据evidence/l2-attempt-1/。
- 第二次L2：3/4；隔离导入后VP-03实测PASS，VP-04冷启动子进程因未继承src导入路径失败。原证据evidence/l2-attempt-2/。
- 第三次L2：负责人2026-11-24T14:23:20Z明确授权继续，不受原预算限制。原两次FAIL不覆盖、累计次数不重置。只补进程树PYTHONPATH=仓库src，保留局部tests隔离；实际子进程预检确认两模块来自仓库，原计划4/4 PASS，mandatory failures=0。原冻结输入及所有外部权限不变。独立L3待评估者。

## EV-01

- AC: AC-01, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-01.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-01.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-01.stderr.log
- Result: PASS

## EV-02

- AC: AC-02, AC-03, AC-04, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-02.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-02.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-02.stderr.log
- Result: PASS

## EV-03

- AC: AC-02, AC-03, AC-04, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-03.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-03.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-03.stderr.log
- Result: PASS

## EV-04

- AC: AC-01, AC-05, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-04.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-04.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-04.stderr.log
- Result: PASS

## Measurement observations

固定合成原订单和虚拟NOW 2026-11-12T01:00:00+00:00，operation-h68 / mandate-h68 v1 / confirm-h68 / order-h68 / request-h68 / payment-h68。FakeStripe与list模拟回调，未调用StripeTestAPI或外部支付。第二、第三轮行为观察一致。

| 对照 | 结果 | provider create / GET / 本次模拟点击 |
|---|---|---|
| 原确认正常会话创建 | ALLOW，创建回调1 | 1 / 0 / 0 |
| 直接输入原生REVOKED | CONFIRMATION_REQUIRED，p1:upstream_prepayment_non_allow | 1→1 / 0→0 / 0 |
| 同确认REVOKED经record_authority | 拒绝 authority_original_gate_not_allowed，未接受撤回 | 1 / 0 / 0 |
| 重开ledger后原图付款 | 原状态CONFIRMED，ALLOW，runtime:allow | 1→1 / 0→1 / 1 |

原图与重载图SHA256均为757874b383ad59f7f88428f8bed4e8970609eba02d91de02c2cd5e3a4a082c0a。分类 NOT_REPRESENTABLE_VIA_RECORD_AUTHORITY；whole_mandate_revocation NOT_JUDGEABLE。VP-03通过且临时SQLite清理断言通过。未观察到已被门禁拒绝却执行、或合法撤回已接受后仍执行的反例；旧图ALLOW不等于撤回后的违规付款。

## Source anchors

- adapters/stripe_checkout.py:226–260：直接入口第236行计算决策，239/257为受门禁控制的provider GET与回调。
- stripe_checkout_lab.py:182–237：record_authority冻结原图，203–204要求原门禁ALLOW，228–229保护不可变原事实；此接口无法表达REVOKED作为当前控制事件。
- stripe_checkout_lab.py:239–266：load_authority恢复原图并验证摘要；adapters/stripe_checkout.py:280–299：stored入口加载原图并检查SESSION_OPEN后调用原直接入口。
- tests/test_stripe_authority_context.py:91–106：冷启动子进程继承env；第三轮显式传递src导入路径后原测试通过。

## AC observations (Executor only)

| AC | 执行者观察 |
|---|---|
| AC-01 | 198项锁与HEAD保持，VP-01通过；原有差异不纳入本任务。 |
| AC-02 | 正常创建ALLOW，直接REVOKED要求重新确认，provider/回调增量0。 |
| AC-03 | 原接口拒绝REVOKED，图摘要保持；该接口NOT_REPRESENTABLE。 |
| AC-04 | 原图CONFIRMED，旧图模拟付款ALLOW/GET1/点击1，无已接受撤回；逐次引用见EV-03。 |
| AC-05 | 124/124原回归通过，0跳过；EV-04十组原测试42/6/6/6/18/8/7/16/6/9均OK。 |
| AC-06 | 三轮L2原始证据及账本完整；最终L2 PASS，独立L3未运行，待Evaluator复查。 |

## Impact comparison

Measurement evidence: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/l2-attempt-3/EV-03.stdout.log（行为JSON）；EV-04.stdout.log和stderr.log（124项原回归）。
Before: B-25确认撤回在保存后传播UNKNOWN。
After: 直接REVOKED门禁有效；现有record_authority拒绝该输入；持久化路径只加载不可变原确认，未定位合法撤回登记/传播能力。
Delta: 单一既有持久化接口的表示缺口，不是已接受撤回后的实际误付款，不是整份Mandate撤销、身份凭据撤销或会话取消。
Guardrail result: 124项原回归全部通过，198项冻结原件保持，清理检查通过。
Scope caveat: 受控合成本地测量，未改产品；无真实支付、网络或生产采用。Impact NOT_APPLICABLE，最终裁决由Evaluator。建议后续独立撤回状态与原批准不可变保真结合，但本包未授权建设。

## Deviations and unresolved items

前两轮环境失败原因及已消耗执行额度保留，原阻塞报告见evidence/REPORT.blocked-attempt-2.md。负责人明确授权继续，见evidence/OWNER_AUTHORIZATION_20261124.md。第三轮仅在已有原生agent子进程设置PATH（agent及Library/bin、Git cmd）、PATHEXT=.COM;.EXE;.BAT;.CMD、PYTHONUSERBASE=本任务evidence/runtime、H87_PROJECT_TESTS=仓库tests、PYTHONPATH=仓库src、PYTHONDONTWRITEBYTECODE=1。不修改系统环境、共享依赖、源代码、原测试、计划或冻结断言。原生子进程和preflight确认原项目src/tests及124项枚举，第三轮正式执行全部通过。

ATTEMPT_LEDGER：三轮runner墙钟分别6.047、10.579、13.797秒，累计30.423秒，不含准备/工具开销；实际主动分钟UNKNOWN。原预算2次，负责人追加授权后正式L2累计3次，历史失败保持，L3=0/1。无安装、服务、WSL测试、外部API、凭据、浏览器、实际付款、Git提交或推送。执行者提交供Evaluator独立L3与最终裁决，不代替评估者accept。
