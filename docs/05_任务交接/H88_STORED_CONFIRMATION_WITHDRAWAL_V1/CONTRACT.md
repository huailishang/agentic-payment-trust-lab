# H88 保存后的单次确认撤回

Task ID: H88_STORED_CONFIRMATION_WITHDRAWAL_V1
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-24-r147
Active bottleneck: B-25
Hypothesis: H-88-STORED-CONFIRMATION-WITHDRAWAL
Metric baseline: H87 L2/L3 各 4/4（最后一轮 L2），直接 REVOKED 阻止副作用，原图写接口拒绝撤回，重启后未撤回原批准仍 ALLOW/GET1/点击1。H88 制包基线固定同一合成输入及两个正常入口。
Estimated affected scope: 单一 Stripe 本地消费者、单次确认、两个既有持久化入口、一个 SQLite 账本。
Expected project impact: 可接受的本地撤回信号从 0 种表示到 1 种，两个既有持久化入口在读到该信号后都由原确认门禁阻止副作用。
Rollback condition: 受理后的回调、读取失败时放行、撤回错绑、历史快照漂移或任何新增外部权限需求均停止，保留原始证据交回 Evaluator。

项目要验证用户授权、绑定、执行、恢复及审计的本地闭环。A、C、D 已有代表证据，B 的既有批准与绑定保持闭合，B-25 进入能力实验。E 有本地身份取证代表证据，B-24 实际采用依赖消费者及逐次记录。F 已闭合受控代表切片，进一步接入受授权约束。B-25 直接影响用户控制，具有可对照的现有机制与低外部成本，优先于 B-24 的材料依赖和 B-20 的已延期幂等方向；停止本轮会留下已定位的生产前控制断点。H87 样本中的旧图付款有原批准，未发生撤回已经受理后的误付款。

## Single objective

同一不可变批准保存后，仓内受信任的本地用户控制调用方能登记一次绑定的撤回。数据库受理提交先于持久化门禁读取时，会话创建和模拟付款入口均返回原生 `CONFIRMATION_REQUIRED`，执行计数为 0。原批准、业务记录及无撤回路径保持。一个主要变化为独立持久化撤回及两个入口复用同一门禁投影。

## Frozen behavioral contract

- 仓内控制调用边界提供已核定的 `subject_ref`。H88 用固定合成用户控制调用方模拟此前置，ledger 校验其与原 `IntentMandate.user_id` 严格一致。业务 Agent、付款调用参数及未核定的用户载荷没有登记入口。输入字段本身只用于绑定，身份认证由真实调用方负责。
- `StripeLabLedger.record_confirmation_withdrawal(operation_id, *, expected_sha256, confirmation_id, subject_ref, event_id, received_at)` 仅在原业务操作及同一原快照可验证时受理。核对确认 ID、原图 digest、原业务绑定和原用户。时间须含时区且不早于原批准保存时点，也不能早于原确认时点。规范化为 UTC ISO 8601 保留。受理从本地提交起生效，时间字段仅供证据使用。
- 首次合法登记返回公开最小事实，`get_confirmation_withdrawal(operation_id, *, expected_sha256)` 返回同一事实，无记录时返回 `None`。事实字段为 `event_id`、`operation_id`、`snapshot_sha256`、`confirmation_id`、`subject_ref`、`received_at`、`source`，其中 `source=LOCAL_USER_CONTROL`。同事件及相同绑定/时间重复登记返回原事实，第二事件或同事件字段冲突拒绝。事件 ID 跨操作唯一。一笔事务完成校验与写入，失败保留原状态。
- 原不可变记录和 `load_authority` 的历史读取保真。两个 stored 入口共享同一有效确认投影，在已验原快照的业务上下文中消费持久化事实，复用原 REVOKED 门禁。门禁状态读取异常或已存事实绑定失配时 fail closed。撤回只影响新动作，既有已付款事实、取消和已付款恢复沿用原规则。已存在历史库以增量方式初始化新表。
- 验收顺序从撤回事务提交到下一次门禁状态读取，覆盖重开库。与动作已获准或回调已开始重叠的竞态、取消上游会话、支付中断、退款和生产时钟责任留给后续证据。

## Acceptance criteria

| AC | 必须交付的观察与证据 |
| --- | --- |
| AC-01 | HEAD、冻结文件、旧证据及 196 项继承保护输入均匹配。产品变更至多两指定文件。 |
| AC-02 | 同一 H87 输入的无撤回控制：创建 ALLOW/1，已持久化付款 ALLOW/GET1/点击1。原图登记 REVOKED 仍拒绝。 |
| AC-03 | 在独立临时库中分别在创建前、已创建未付时提交同一原确认的合法撤回。重开库后两个入口均 CONFIRMATION_REQUIRED，provider 创建、GET、模拟点击增量为 0。保留结构化门禁结果。 |
| AC-04 | 公开事实回查与提交一致，原图 payload 和 SHA 原字节不变。同事件幂等，两种冲突及错主体、错确认、错原图、错操作、无时区或早于原批准均拒绝。读取不到可信状态 fail closed。 |
| AC-05 | 历史无撤回数据库可就地打开并保留原图和合法行为。原十组 124 项测试全通过，零跳过，含取消、到期、已付款恢复及身份守护。 |
| AC-06 | 提交源差异与哈希、前后矩阵、一次统一报告及全部原始 L2。Evaluator 接受同一快照并重新建立临时库运行独立 L3，逐 AC 判决并汇报成本和清理。 |

## Execution package

1. S0 确认原生 Python 3.12 和冻结锁，读取 `BASELINE.json` 中现有行为及旧 schema，记录执行开始。导入预检仅允许调整本次进程环境，环境无法恢复即保留诊断。
2. S1 先实现最难的接收与保全：单一撤回事件、原图归属、冲突和重放、旧数据库初始化。确认账本接口对外呈现真实受理事实后，自动接入同一有效投影至两个 stored 方法。
3. S2 固定测量条件和业务原图，一次统一采集正常、撤回、负向与历史库对照。局部失败可在允许范围内修正，修正后重跑完整验证。若受理后任何副作用发生、绑定错位、快照变化或状态不可读仍放行，停止使用候选并交 Evaluator。
4. S3 运行公共 L2，保留每次门禁三件套及版本/墙钟账。最后一次提交 `REPORT.md`、逐 AC 对照与最小事实快照。Evaluator 独立验收，不逐步交 Human。

## Allowed scope

只允许两个产品文件 `src/agentic_payment_experiment/stripe_checkout_lab.py`、`src/agentic_payment_experiment/adapters/stripe_checkout.py`，本任务 `REPORT.md`、运行证据/账本及标准路由元数据。冻结测试、历史样本和所有既有代码之外的受保护输入只读。只在临时目录使用合成 SQLite 库，报告使用脱敏合成标识。

## Exclusions

产品 UI/API、第二消费者、整份 Mandate 撤销、真实用户认证、真实支付/网络、服务、浏览器、安装、WSL、凭据、下载、Git 提交推送与历史改写均不在本包。取消、已付款恢复、直接确认和协议行为仅作回归守护。

## Validation plan

Validation plan file: docs/05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/VALIDATION_PLAN.yaml

四项强制检查依次为输入锁与边界、固定行为/负向/旧库、既有回归、最终输入锁。H88 `CHECK.py` 每项行为均使用本地 FakeStripe 与临时 SQLite。原 H87 临时库和失败账本不复用。L3 在独立进程跑同一冻结检查，复核候选差异和原始矩阵。

## Authorization

基于负责人要求制定下一执行包和项目内已有的本地离线任务范围。外部/API/安装/服务/凭据/浏览器/支付/Git 类额外授权全部 false。H87 续行和任何历史外部额度均属于其原任务。

## Cost and stop conditions

最多初版与一次范围内修正、2 次 L2、1 次独立 L3。低至中本地成本，估计实现及复核约 75–150 分钟，估计仅供排序。使用现有环境，外部费用 0。执行者按实际记录墙钟和各轮计数，无法计量的主动分钟记 UNKNOWN。第二次 L2 只用于可恢复环境、证据或合同内修正。不可读状态放行、已受理撤回后副作用、原图变更或对照失真即 STOP。所有 AC 通过且两个入口均在副作用前阻断，可结束 B-25 的这个代表切片，后续仅在整份委托、在途竞态或真实控制来源有独立证据时重排。若原假设无净收益，SWITCH 或 STOP 并量明原因。

## external_requirement_impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-08, PCAC-09, PCAC-10, PCAC-12, PCAC-18, PCAC-20, PCAC-22]
  applicability: CORE
  maturity_before: M1
  maturity_after: M4
  maturity_scope: 单次确认的本地受控撤回切片，M4 为独立签收达标后的目标
  test_evidence: [AC-02, AC-03, AC-04, AC-05]
  trace_evidence: [VP-02, VP-03]
  residual_risk: [整份用户委托撤销, 真实身份与入口, 一键关闭界面, 在途竞态, 外部传播与真实付款]
```

PCAC-10 是核心主项，现阶段仍为 M1。PCAC-08/09/12/18/20 为现有控制回归，PCAC-22 的查询和一键关闭体验继续待证。各要求的整体成熟度沿用原判。
