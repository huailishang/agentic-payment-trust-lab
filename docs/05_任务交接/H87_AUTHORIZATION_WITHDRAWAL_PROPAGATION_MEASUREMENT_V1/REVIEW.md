# H87 用户确认撤回传播测量独立复核

Task ID: H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad

## 全局位置

项目要证明本地用户授权、交易绑定、受治理执行、恢复与审计能形成可复核的闭环。A、C、D 和 B 的既有批准与绑定已有代表证据，B 回到保存后的确认撤回。E 已签收本地身份取证代表切片，B-24 实际采用仍等逐次材料。F 已闭合受控代表切片，进一步接入受授权约束。H87 只测 B-25，因为撤回传播与执行前用户控制直接相关，现有本地入口和对照可以独立核验。

## Pre-review checks

- 接受前工作流结构校验通过。评估者对三轮 L2 共 12 组三件套复算长度和摘要，先锁定 56 项提交文件及路由原件，再接受同一快照。复测后 56 项保持，198 项冻结输入和 HEAD 在 L3 内核对通过。见 `evidence/evaluator/ACCEPTANCE.json`。
- 两次环境失败保持原判，第三轮由负责人明确续行，覆盖范围仅 H87。同一 Windows Conda agent 环境使用原生 Python 子进程和进程内导入路径，评估者另建临时 SQLite，未安装依赖。
- 所有附加权限为 false。冻结检查未调用 Stripe API 客户端或真实浏览器，所有行为计数来自 FakeStripe 与列表回调。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/L3-GATE.json
- Validation plan: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE。评估者使用冻结命令重新生成原始证据。

## RV-EV-01

- AC: AC-01, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-01.stderr.log
- Result: PASS

## RV-EV-02

- AC: AC-02, AC-03, AC-04, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-02.stderr.log
- Result: PASS

## RV-EV-03

- AC: AC-02, AC-03, AC-04, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-03.stderr.log
- Result: PASS

## RV-EV-04

- AC: AC-01, AC-05, AC-06
- Meta: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/evidence/evaluator/l3/RV-EV-04.stderr.log
- Result: PASS

## Acceptance matrix

| AC | 裁决 | 独立依据 |
| --- | --- | --- |
| AC-01 | 通过 | RV-EV-01、RV-EV-04 核对 198 项输入及 HEAD，56 项接受文件复查一致。 |
| AC-02 | 通过 | RV-EV-03 原确认创建 ALLOW/1。直接输入原生 REVOKED 为 CONFIRMATION_REQUIRED，provider 创建、读取与模拟点击增量均 0。 |
| AC-03 | 通过 | RV-EV-02/03。原图入口以 `authority_original_gate_not_allowed` 拒绝新状态，原图和重载图 SHA 一致，记录为 NOT_REPRESENTABLE_VIA_RECORD_AUTHORITY。 |
| AC-04 | 通过 | RV-EV-03 重启后仍读取 CONFIRMED 原批准，既有付款 ALLOW，读取和点击各 1。原确认、订单、请求、付款与同一 SHA 绑定。撤回输入从未受理，旧图执行按有效原批准解释。 |
| AC-05 | 通过 | RV-EV-04 十组共 124 项通过，零跳过。会话取消属于支付会话状态，确认撤回作用于一份用户确认，凭据撤销属于身份来源。 |
| AC-06 | 通过 | 三轮 L2 的 2/4、3/4、4/4 以及唯一 L3 4/4 均保全，L2 最终和 L3 行为标准输出逐字节一致，临时库清理通过。 |

## Final verdict

PASS

六项验收通过。源码交叉核对显示两个既有持久化动作均调用 `load_authority` 后把原图交给原生门禁。H87 独立实测覆盖直接门禁、原图登记、会话创建正对照和已建会话的持久化付款。保存后另行登记当前撤回信号仍需建设。未观察到合法撤回已受理后仍执行的反例。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

本包建立了能力基线。产品字节保持，无能力增益声明。整份委托撤销、真实用户核验、并发竞态和真实支付保持待证。

## Iteration value and continuation decision

Continuation decision: CONTINUE

两个既有持久化动作共用原批准读边界，其中付款路径已有独立实测。原门禁本身已经理解原生撤回状态，因此只需验证可绑定、可保全的本地撤回登记是否能传到两个入口。B-24 实际采用需要消费者责任和脱敏逐次材料，B-20 仍为延期观察，继续 B-25 的风险收益更明确。三轮 Executor runner 累计 30.423 秒，主动时间 UNKNOWN。Evaluator 使用 1/1 次正式 L3。旧任务续行授权及次数保留在原账本。

## Next execution package

- Dispatch mode: SINGLE
- Next task ID: H88_STORED_CONFIRMATION_WITHDRAWAL_V1
- Next contract: `docs/05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/CONTRACT.md`
- Initial routing: CONTRACT_FROZEN / Executor
- 允许一次主机制实现与一次合同内修正、最多两次 L2 与一次独立 L3。以原快照不变、预付款阻断、同事件幂等、错绑隔离和 124 项回归统一验收。发现已受理撤回后的回调、快照漂移或需要新增外部授权即停止并交 Evaluator。
