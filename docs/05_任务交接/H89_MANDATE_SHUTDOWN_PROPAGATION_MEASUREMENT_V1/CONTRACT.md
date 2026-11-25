# H89 整份委托停止的跨操作传播测量（统一长执行包）

Task ID: H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1
Task kind: evaluator_design
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-25-r148
Active bottleneck: B-26
Hypothesis: H-89-MANDATE-SHUTDOWN-PROPAGATION
Metric baseline: H88 L2/L3 各4/4，单次确认撤回表示0→1、两入口阻断；124项回归保持。整份委托接收和跨操作传播只有源码线索，系统证据 UNKNOWN。
Estimated affected scope: 单一既有 Stripe 本地消费者、一个 SQLite 库、同一用户同一 mandate_id/version 的三个业务位置和另一个 mandate 对照。
Expected project impact: 得到可复核的停止对象/接收/传播边界及共同断点，足以负责地选择最小后续机制或停止；本包不声明产品能力改善。
Rollback condition: 产品/历史漂移、模拟边界失守、已受理控制与实际副作用矛盾、发现未冻结的接收候选、清理失败或需要新增权限时立即停止，保留原始证据。

项目目标仍是本地可重置的授权、绑定、执行、恢复和审计信任链。A/C/D 本地阶段关闭，B 的既有批准/绑定和 B-25 单次撤回代表切片关闭。E 真实用户/组织/硬件认证、生产时钟和实际采用未闭合；F 受控代表切片关闭，后续接入受权限约束。

B-26 是更高层授权生命周期边界，不重开 H88 同对象扩例。它直接关联 PCAC-10/22，且可以无新外部成本测量；B-24 实际采用仍缺消费者材料、B-20 人工延期。在途竞态需要另定动作开始及不可逆时点，先测停止对象和作用域的信息价值更高。暂停本地能力声明去测这一未知，比凭静态线索直接建模块更有依据。不触发新外部研究、数据集获取或第二套设计交接。

## Single objective

在同一账本中，系统测量整份用户委托停止是否存在合法原生接收面，并测清已有单次撤回对同委托不同确认、不同业务状态和后登记动作的实际作用域。一个假设为当前单次事件不足以代表整份委托停止；唯一主要工作是构造并记录跨操作测量。只有实测共同断点才支持后续能力建设。

## Frozen measurement semantics

- 委托键用于测量关联：`user_id + mandate_id + authority_version`。A/B/C 完全相同；D 是同一用户的另一 mandate，避免用用户不同掩盖作用域错误。每个订单、请求、付款、确认、操作及会话标识独立且可回查。
- 合成委托 max_count=3，A/B/C 分别 sequence_count=1/2/3，正常金额/时效/绑定满足原合同。只验证已有逐请求规则，不声称已经实现累计次数/金额预算。
- A：已存原批准，尚未创建会话；B：已创建并绑定原会话，尚未付款；C：在控制事件位置之后才登记并保存的同委托新动作；D：其它委托的隔离对照。固定四个业务位置是回答作用域问题的最小集合，不增加其它消费者、UI或攻击族。
- 三个独立临时库分支：无撤回、只撤回 A 的确认、只撤回 B 的确认。后两个事件只通过 H88 的真实公开接收接口提交，重开库再运行真实 stored 动作。它们是合法单次事件，不冒称整份委托撤销。
- 公开接收清点限定 IntentMandate、StripeLabLedger 及两个既有 stored 消费入口。枚举字段、公开方法及具体源码行，并人工回查确认接口参数和事件键；不得仅凭方法名断言全仓不存在。若发现可用但未冻结的整份接收候选，停止交 Evaluator，不猜参数、不伪造事实、不静默换测量方法。
- 没有合法整份入口时，记录 `NOT_REPRESENTABLE_IN_FROZEN_NATIVE_SURFACE`，整份事件 `accepted=false / NOT_SUBMITTED_NO_NATIVE_RECEIVER`。此时 ALLOW 是原有效批准下的正常行为，不构成“已撤销后误付款”。不通过 SQL 改状态、补丁、动态属性、伪造服务或主动过期来制造整份撤销。
- 原图始终历史保真：只读 SQL 可用于原始 payload/digest 取证；写入只用现有公开接口。固定 NOW 和事件先后序，不声明生产时钟、真实用户认证或竞态中断。

## Acceptance criteria

| AC | 原子交付要求 |
| --- | --- |
| AC-01 | HEAD、源/测试/脚本集合、所有输入锁及 H88 报告/L2/L3/终验保持；当前地图按 r148 校验，原 r147 只通过显式归档别名保护；无产品修改。 |
| AC-02 | 列出限定接收面的字段、公开方法、接口签名与关键源码行；逐项区分整份委托、单次确认、取消会话及身份撤销；没有入口与拒绝输入分开，不作全仓/真实系统不存在声明。 |
| AC-03 | 四业务位置的关联与独立性可复算，原生批准保存均成功；无撤回分支 A/C/D 创建 ALLOW/1，B 付款 ALLOW/GET1/click1；B 预先创建计数单列。 |
| AC-04 | 两个合法单次事件分支均有真实回查事实；重开库后只对应目标 CONFIRMATION_REQUIRED/副作用0，其它同委托和其它委托动作分别记录真实结果。C 在事件位置后登记，原图保持。 |
| AC-05 | 三分支各行包含用户/委托/版本/确认/操作/快照、原生门禁、回调、create/GET/click增量及事件受理状态；能定位两个不同业务状态共享的接收/消费断点，或给出反证/NOT_JUDGEABLE。缺整份受理事实绝不宣称撤销后错误放行。 |
| AC-06 | H88 两入口撤回/冲突与不可读守护保持，原十组124/124零跳过；所有临时库清理，产品/历史输入结束时零漂移。 |
| AC-07 | 一次统一报告给出逐AC、原始L2、每步账本、预算和机制约束表；表中明确后续停止键/信任来源/生效排序/旧图保全/失败拒绝/新动作覆盖/残余边界及CONTINUE/STOP/SWITCH条件。Evaluator 接受同一快照后独立L3与语义回查，测量不计产品增益。 |

## Execution package and dependencies

这是一个完整八步骤包，S0→S1→S2→S3→S4→S5→S6→S7，满足前置后自行继续；不逐步提交 Human、不为普通修正新建任务。产品建设不属于任何成功分支。

| 步骤 | 工作与必须留存证据 | 成功后 / 失败分支 |
| --- | --- | --- |
| S0 输入和环境 | 核 INPUTS、旧治理别名、HEAD、当前工作区差异；原生 Python 3.12 无优化、既有 Conda agent；登记开始与工具版本。 | 通过→S1；仅进程导入/PATH故障可就地恢复；锁漂移/需安装→停止。 |
| S1 接收责任清点 | 用冻结 inventory 列表和源码人工回查真实参数、事件键及两个入口消费；在报告说明四种控制对象区别。 | 缺整份入口仍是可测分支→S2；新未绑定候选→停止交Evaluator，不自行调用。 |
| S2 最难前置：跨操作资格 | 用 qualification 建立四独立上下文，核同委托键/计数/不同确认，证明 A 已存、B 原生创建并绑定、C 尚未登记。 | 可合法构造→S3；构造失败仅环境可修，业务契约不改、Case不换。 |
| S3 正常对照与两种单次事件 | measurement 在三套独立库运行同四业务位置，B 预创建与后续增量分开，分别保存 A/B 单次受理事实。 | 控制可解释→S4；错误绑定受理/目标撤回后回调→立即停止行为采集，保留清理与事实。 |
| S4 重开和未来动作 | 每分支重开库，再登记C；运行 A/C/D 创建、B付款，记录真实门禁和副作用，原图字节/确认保持。 | 完整→S5；清理失败或原图漂移→停止，不修产品。 |
| S5 共同断点与机制约束 | 逐行对照事件对象、受理边界与消费入口，报告候选最小机制的约束；比较整份接收缺口、单次隔离正确、无法判定三种解释，列出证据路径。 | 能判定或诚实NOT_JUDGEABLE均→S6；不得把建议写成已实现或自动建设。 |
| S6 守护与回归 | 冻结 guards：H88 两入口重开/幂等冲突/不可读拒绝；运行原124回归，结束再核锁和清理。 | 通过→S7；失败保留，不降测试数、不跳过、不更改原测试。 |
| S7 统一提交 | 公共 runner 一次跑六项强制门禁，保存每次原始三件套；报告含上述分析、成本与限制，写 SUBMISSION，结构验证后按原协议提交。 | L2 PASS→提交同一快照；可恢复环境/证据问题且预算剩余→本包一次修正与完整第二轮L2；否则BLOCKED交Evaluator。 |

公共 runner 是顺序执行器，后续检查可能继续执行；每条检查自行核锁，全部动作均无外部权限。STOP 后不得启动第二次正式行为轮，不用后续守护测试改写已出现反例。Evaluator 一次统一独立 L3/逐 AC 验收，不按步骤分轮。

## Allowed scope

Executor 只写本任务 REPORT.md、SUBMISSION.json、evidence/attempt-* 与 append-only 账本，以及标准 CURRENT 执行/提交元数据。CHECK.py、INPUTS.json、CONTRACT.md、VALIDATION_PLAN.yaml、EXECUTOR_START.md、冻结脚本和准备证据只读。所有产品、原测试/脚本、历史报告/证据与地图只读。Evaluator 可写 REVIEW、独立证据及后续治理。不共享旧临时库。

## Exclusions

整份撤销实现、产品/测试修复、新API/UI、第二消费者、在途竞态、已付回滚/退款、累计预算治理、凭据生命周期、真实用户认证、生产时钟、服务/WSL/网络/浏览器/模型接口/真实或外部测试付款/下载/安装/凭据/Git提交推送及历史改写均排除。只用 FakeStripe 与列表回调，不实例化 StripeTestAPI，不读取真实凭据。不加载或执行上游项目。

## Validation plan

Validation plan file: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml

六项强制检查：qualification（含前后输入锁）、接收面、三分支完整测量、H88守护、124回归、最终保护。精确 argv/cwd/exit 见计划。L3 使用同冻结命令、新进程和新临时库，另人工核 AC-02/05/07 的因果解释、源码签名及机制约束，不以结构通过替代语义。治理更新后旧 H88 严格 preserve 不再针对当前地图重跑；本锁校验 r147 归档原字节，直接复用未改 H88 行为函数和原回归，不削弱产品守护。

## Authorization

来源为负责人要求“评估，并制定下一执行包”及“新的执行包要尽量包含比较长的步骤”，授权本地可逆制包/离线测量。全部额外权限为 false，H87 续行与旧现场额度不继承。本轮只冻结包并预检测量夹具，不代行 Executor 正式 L2，不声明 H89 已验收。

## Cost and stop conditions

- 固定1版冻结测量方法、4个业务位置、3个隔离分支；每次完整测量12行，不追加Case。每分支一个临时目录，清理必须成功。
- 最多2次正式Executor L2、1次Evaluator L3，第二次仅限同源码/同测量方法的环境或证据输出故障；脚本/AC/输入/权限需改即交Evaluator显式修订，不重置次数。普通进程环境与报告修正不逐步交Human。
- 成本估计中低，执行分析/证据整理及独立语义复核约90–180分钟，低置信、非强制总工作时限；不为做长而拖延。记录真实命令与角色起止，主动分钟无法精确计量写UNKNOWN。外部调用/费用0；不把本地工具耗时当人工时间。
- 立即停止：已受理目标单次撤回后副作用、错绑、原图漂移、状态不可读仍放行、夹具正对照不成立、产品锁变化、新未冻结整份接收候选、清理失败、需要外部权限或预算用完。保留已产生原始数据，不能修产品或自动追加下一包。
- 两不同业务状态共享可回查的整份接收缺口，正对照/隔离/守护成立→Evaluator可CONTINUE最小能力合同；本包仅报告。已有完整链、无共同断点或边际收益低→STOP/SWITCH。NOT_JUDGEABLE→指出精确缺的事实，不创造授权。零容忍反例→保全并重新排序，不能当缺入口的普通结果。

## external_requirement_impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-10, PCAC-12, PCAC-18, PCAC-20, PCAC-22]
  applicability: CORE
  maturity_before: M1
  maturity_after: M1
  maturity_scope: 整份委托停止传播的测量合同，不提升产品能力成熟度；H88单次切片M4保持
  test_evidence: [AC-02, AC-03, AC-04, AC-05, AC-06]
  trace_evidence: [VP-02, VP-03, VP-04, VP-05]
  residual_risk: [整份撤销能力待建或待证, 真实控制来源, 生产时钟, 在途竞态, 一键关闭界面, 外部传播, 实际支付]
```

只有上述CORE关联进入必要测量/回归；PCAC-18/20是既有恢复/评估守护，PCAC-22仅作用域问题，不新增同名模块或声称完整一键关闭。完整要求成熟度和合规结论均不由本包推断。
