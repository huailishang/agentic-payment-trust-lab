# H87 用户撤回确认到持久化付款入口的传播测量

Task ID: H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1
Task kind: evaluator_design
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-24-r146
Active bottleneck: B-25
Hypothesis: H-87-AUTHORIZATION-WITHDRAWAL-PROPAGATION
Metric baseline: H85本地身份取证切片及H86仓内资格已签收，用户在保存授权之后撤回确认的传播链未系统测量
Estimated affected scope: 一个既有Stripe本地模拟消费者的直接入口、持久化入口及重启载入
Expected project impact: 明确已有撤回状态在副作用前可达的边界，给下一单一能力包提供共同断点或停止依据
Rollback condition: 证据漂移、模拟边界失守或需要修改产品才能继续时停止并保留原件

项目最终验证本地可重置的授权、绑定、执行、恢复和审计信任链。A–D本地代表阶段关闭，E中B-24本地来源/消费者资格切片已关闭，实际采用、可信时钟保持UNKNOWN。F外部受控代表切片已关闭。H86的“实际消费者材料不足”仅约束实际采用声明，不能阻塞本项目范围内的其它授权安全测量。

B-25优先于B-24实际采用，是因为用户撤回授权直接关系零容忍的执行前治理，现有ConfirmationStatus.REVOKED和Stripe存储入口提供明确、无新外部权限的测量位置。优先于延期B-20工具幂等以及新PSP，因为它们分别有既有延期和新的外部依赖。已关闭的B-22原快照保真继续保持，本轮考察原快照保存之后的新控制意愿传播，只有系统性共同断点才允许后续建设。

本轮冻结的是measurement-only，不预设撤回API存在，不预设产品有误付款。静态已知为确认枚举含REVOKED、原确认非活跃时有校验逻辑、StripeLabLedger保存不可变原始上下文；组合运行及撤回路径可达性待实测。

## Single objective

在同一合成订单、原确认和有效期内，测量当前确认撤回状态经直接上下文与持久化原上下文进入既有付款门禁的可达性。分清“接受撤回后仍执行”“撤回输入被拒绝或根本无入口”和“旧快照仍可按原规则使用”。只在已有公开接口提交输入，不伪造权威撤回事件或直接改数据库。确认撤回对象是单次订单ConfirmationRecord，不能推断用户整个Mandate的撤销能力。

## Acceptance criteria

| AC | 必须交付的观察与证据 |
| --- | --- |
| AC-01 | 冻结HEAD、src/tests/scripts及H85/H86签收材料摘要保持，既有工作区差异单列，任务外文件不改。 |
| AC-02 | 未撤回的同业务正对照正常；当前上下文含原生REVOKED确认的直接入口，记录真实决策、原因、provider创建/读取及模拟浏览器回调计数。任何已被门禁判无效却执行回调为零容忍反例。 |
| AC-03 | 先正常保存原上下文和原会话，再通过现有record_authority尝试同确认撤回状态。保存该输入是否被接受、确切异常、前后图摘要、关闭重开后的原图。无合法撤回入口时记录NOT_REPRESENTABLE，不能把拒绝写入当成已撤回。 |
| AC-04 | 仅对已有来源明确的状态比较重启后的authorize_stored_browser_payment。记录原批准和本次状态的关系、真实provider GET及模拟回调；同一订单摘要/授权/确认引用须保持。不使用SQL更新、猴补门禁或新造撤回服务。 |
| AC-05 | 原取消操作、过期确认、已付款恢复/补救、授权保真等既有测试以及H85原86项全部通过、零跳过。取消会话、确认撤回、身份撤销三者语义分别说明。 |
| AC-06 | 完整L2、独立L3三件套、原始观察、输入锁、源码定位及逐AC裁决，结论明确已有控制、共同缺口或NOT_JUDGEABLE；资格测量不计产品改善。 |

## Execution package

S0先核冻结输入和接口，直接检查门禁、ConfirmationRecord及存储接口中的撤回接收位置，写入报告源码依据。若找不到专用撤回入口，继续测现有record_authority，失败亦是可判定观察。

S1固定原测试工厂、虚拟NOW、FakeStripe、唯一合成订单。在不同隔离状态中做正对照、当前REVOKED直接输入、正常持久化、同原图撤回尝试和重启载入。固定付款前有效期，不引入真实时间漂移。这里不会把拒绝更新伪装成已被接受的用户动作。

S2重启后进入原stored付款入口，观察旧图、provider GET和回调，输出可复算JSON。零容忍反例即结束行为测量，保留清理并报告，不补修产品。若仅观察到缺接收入口，交付边界证据并继续原守护回归。

S3统一运行124项必要原回归、核原件保持、整理源证据和成本。一次交齐L2和报告。评估者接受同一快照后运行唯一L3，在临时数据库中自己重复测量，并用源码与异常路径交叉验证。

## Allowed scope

只允许本任务evidence运行产物、REPORT.md和执行账本，及按标准提交阶段维护CURRENT。合同、CHECK.py、VALIDATION_PLAN.yaml、INPUTS.json和已有准备证据为冻结只读。评估者可写REVIEW和治理地图。所有产品、原测试、样本、历史证据只读。临时SQLite数据库仅在TemporaryDirectory中创建和清理。

## Exclusions

全部外部API、网络、浏览器、真实或外部测试付款、服务、WSL、临时凭据、下载、安装、Git提交推送及历史改写权限false。不调用StripeTestAPI，不读取真实凭据。只使用已存在FakeStripe及模拟浏览器list回调。不得修改付款准入规则或增加第二消费者。身份降级、确认撤回和订单取消各自按真实对象命名。

## Validation plan

Validation plan file: docs/05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml

四项强制检查顺序为输入冻结、边界源码定位、真实本地入口组合测量及原回归。CHECK.py为评估者冻结的测量器，只读取真实返回及计数，支持结果与假设不一致。公共runner会继续执行后续条目，故所有检查自行核输入锁；没有外部现场步骤。L3重新创建临时数据库独立运行相同命令，原始EV/RV-EV逐项复算。

## Authorization

负责人本轮要求复核并结合瓶颈制定新执行包，已有离线任务执行授权持续有效。本包仅本地离线合成输入与临时数据库，所有额外权限false。当前制包不产生正式门禁或行为测量成绩。

## Cost and stop conditions

两次正式Executor L2、一次Evaluator L3。第二次L2仅限环境/证据输出的可恢复问题，禁止换源码、调整观察结果或重定义撤回。原始失败保留。任一实现/断言需要改冻结检查器即回Evaluator显式修订，不能用新任务重置旧账。预计低到中本地成本，整理与独立复核约60–120分钟（estimated，非人工时间上限），无API/模型费用。实际主动时长UNKNOWN如实写入。临时文件总目录≤各角色每次一套，清理由上下文管理器负责。

共同断点成立且在两个既有边界可重现→CONTINUE，下一包由Evaluator冻结最小状态接收及副作用前传播。已有完整撤回链且守护通过→STOP该方向并重排。只有缺合法输入→记录缺对象/入口/责任，不能写修复或风险降低；是否建设需要下轮合同。超范围、源码漂移、零容忍反例或清理失败→STOP并交Evaluator。无网络失败重试或额度续期。

## external_requirement_impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-08, PCAC-09, PCAC-10, PCAC-12, PCAC-18, PCAC-20]
  applicability: CORE
  maturity_before: M1
  maturity_after: M1
  maturity_scope: 单次确认在保存后撤回的传播测量合同，能力成熟度待独立证据裁决
  test_evidence: [AC-02, AC-03, AC-04, AC-05]
  trace_evidence: [VP-02, VP-03, VP-04]
  residual_risk: [整份用户委托撤销, 真实用户身份, 外部传播, 并发撤回, 在途真实付款]
```

profile=PCAC-AGENTPAY。PCAC-10 CORE用户授权撤销是战略关联，当前仅测单订单确认撤回这一子对象，整体成熟度before/after保持UNKNOWN，待测量支持细分。PCAC-08 CORE/ADAPTER确认意愿及PCAC-09 CORE授权执行、PCAC-12 CORE证据链、PCAC-18 CORE/ADAPTER恢复、PCAC-20 CORE/EVIDENCE_ONLY评估均沿用现有成熟度。Test为AC-02至AC-05，Evidence为源码定位/JSON观察/EV-RV三件套。明确残余风险为整份委托撤销、用户身份、真实外部传播、并发撤回与真实在途付款尚未验证。无监管合规结论。
