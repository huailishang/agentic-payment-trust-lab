# H71R：失败传输取证与最终矩阵消费修复长包

Task ID: H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H71R_RELIABLE_TRANSFER_EVIDENCE_REPAIR_V1/VALIDATION_PLAN.yaml
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-12-r116
Active bottleneck: B-21
Hypothesis: H-71R
Dispatch mode: SINGLE

## Strategic basis / 战略依据

目标为可独立复核的支付信任链，A–D本地关闭、E受控本地闭合、F当前。H71原生Windows L3八项通过、安全9/9、回归74/74，但原合同第2/第7验收项不通过：最终矩阵仍把三个已成功GET写未测；来源只引用HTML导航；来源/下载整段read异常会丢失部分字节，下载还覆盖已获HTTP状态。整包REJECTED，三GET200完整空列表事实保留，不判支付或平台失败。

两个离线反例分别复现来源与下载的共同断点，最小机制明确：有界逐块落盘、保留状态、区分已观察/完整/未知字节，并将最终实际证据消费到矩阵。先修此取证链优于换通道重复下载：当前采集器会继续掩盖失败及成本；也优于H67或扩旧本地Case，后两者不修外部证据可靠性。不额外研究框架或数据集。

Metric baseline: 三个GET实证保留；最终矩阵未消费；两个23字节/HTTP200后超时反例产生0字节、下载status=null。
Expected project impact: 修复证据质量；本包不评价支付能力增量，impact=NOT_APPLICABLE。
Expected material cost: 120主动分钟/3小时墙钟、2任务脚本版本/3L2/1L3；只读已有约1MiB文档和已封存原文，新增网络/下载/安装/API/浏览器/服务/付款0。
Rollback condition: 原H71全部材料只读；若历史无法恢复就保持UNKNOWN，不补写旧事实，不重新现场采样。

## Single objective / 唯一目标

在一个统一离线包中修复H71证据生成与消费链：输出不改历史的纠正投影、真实最终权限矩阵及可独立故障注入的有界传输采集原语；共同主变化是“失败也能被准确记账和消费”，不新增接入或支付功能。

Failed AC: H71原合同第2项（最终矩阵/引用）、第7项（失败取证/字节）；精确原标识见EVIDENCE_GOLD.parent_failed_ac和原REVIEW。继承B-21入口资格方向；H71/H68候选代码及全部旧证据属于继承工作区，保持只读，不追认H71通过。

## Execution steps / 六步连续执行，统一验收

1. 核冻结保护、H71 REVIEW/L2/L3/接受快照与离线反例；复用原三GET原文和已有两份官方文档。原私有材料原位只读，不使用凭据，不询问Human重复提供key。
2. 生成EVIDENCE_CORRECTION.json：保留三GET200/空/完整分页及其摘要；两个失败源码读取的HTTP200已观察、完整归档0，但实际接收总字节UNKNOWN；下载HTTP状态/失败阶段/接收总字节UNKNOWN，完整归档0。分别说明“归档0”与“收到0”的差别，不能从反例23字节倒填历史。
3. 生成CORRECTED_MATRIX.json，四维实测/文档/未知分开，三个读取成功确实被消费；引用原两份官方文档内能支持论断的正文片段，不能再用导航标签。泛用key/CLI说明不等于rkcs_test_特定权限保证。保留Checkout写入、监听、Stripe前端和独立账户身份未测。
4. 实现本包RUN.py的纯离线采集原语capture_attempt，按SCHEMA_GUIDE接口接收注入的opener/时钟/流，逐块落盘；读/写失败都保留已获得的HTTP状态、已观察字节及不确定性。只能调用注入的opener，不自行建立网络或启动子进程；公共API不改。
5. 在同包内跑冻结独立故障驱动，核成功、空正文、建连失败、部分读取超时、错误状态、重定向、字节上限/跨尝试剩余预算和关闭；原安全9/Windows74回归保持。预算内只修新包实现/派生文件，保存物质失败与版本；不逐步交Human复核。
6. 完整L2通过后统一提交REPORT、修复产物及原始证据；Evaluator只执行一次完整独立L3，并逐AC审阅引用上下文、历史UNKNOWN与字节边界。没有任何网络重放、下载或运行授权延期。

## Acceptance criteria

### AC-01 — 原件、成果与修复范围保持

H71原REPORT/RESULT/矩阵/来源/账本/L2/L3/接受快照及旧产品/测试保持；保留三GET真实成功，不把修复结果回写历史。只在本包新增实现、纠正投影、矩阵、证据；所有原始敏感材料不公开。

### AC-02 — 历史纠正与保守预算

准确区分已知原状态、完整归档字节与UNKNOWN接收量；原来源两次HTTP200保留，下载状态不得凭空补200或认定无响应。已有源码两次read各上限2MiB+1，已成功来源字节已知；下载read上限64MiB+1且无部分落盘，必须以保守未知范围记账，不证明已超额，也不把0归档当0配额消费。若无法证明原64MiB下载额度仍有余额，guaranteed_remaining_download_bytes=0，不能自动授权重试。

### AC-03 — 可消费的最终矩阵与有效引用

四维覆盖，checkout_required_endpoints含三份实际200、空且完整的原文摘要观察；不再标这些GET未测或能否读取未知。account_read仍H69的403，test_listener仍未测，same_environment_binding仅原provision同凭据上下文。至少两条对正文论断有效的来源注释，分别来自原key与listen文档；逐字片段与摘要可回指，导航片段/通用文档推断特定key权限不得通过。

### AC-04 — 有界采集与失败证据

HTTP状态取得后不被正文异常清空；每个返回成功块先落盘/计数，异常后已观察块仍可复算；body_bytes_total只在EOF证明完整时为整数，否则null。body_bytes_observed、bytes_charged、归档摘要与文件真实字节明确区分，最后失败read的保守预留计入bytes_charged，不把未观察字节冒充精确0。单read大小不超过剩余预算，达到上限但未证EOF则LIMIT，不为探测EOF多读一字节。完成、异常与LIMIT均关闭本任务流，记录失败阶段和异常类型，不回显消息中的秘密。

### AC-05 — 独立反例、守护与统一交接

冻结CHECK_PROBES全部通过，不能修改/伪造驱动结果；原安全9/Windows74回归保持。完整L2/独立L3与逐AC审阅仍必要，判别器通过不替代来源和传输语义。两个实现版本/三次L2内允许任务内修复，产品/旧测试/公共runner不能动。

### AC-06 — 真实预算与零外部动作

120主动分钟/3小时墙钟，implementation≤2、L2≤3、L3≤1；追加BEGIN/END，失败照计。新增网络/下载/API/浏览器/服务/环境/会话/付款/安装/提交/推送均0。本包是离线修复，不恢复或延长原H68截止；修复通过后仍须Evaluator单独判断下载保守余额与后续所需授权。

## Allowed scope / 允许范围

Executor仅新增本包RUN.py、EVIDENCE_CORRECTION.json、CORRECTED_MATRIX.json、RESULT.json、REPORT.md、ATTEMPT_LEDGER.jsonl、evidence/、versions/；CURRENT只作本任务执行/交接字段变化。原文只读，所有冻结合同/金标/驱动/检查器/计划/基线不可改，不刷新BASELINE。

## Exclusions / 排除

不修产品、旧H71文件、全局配置、CLI接入或浏览器桥接；不复制旧未验证HOME覆盖和硬编码工具不可用实现。只设计离线采集原语，不安装/运行Stripe CLI、不换网络通道、不重试任何真实GET或下载、不新建环境/会话/付款，不改变原授权或架构角色。不能用修复掩盖历史UNKNOWN。

## Validation plan / 验证计划

VP-01保护/冻结/范围；VP-02纠正投影与矩阵；VP-03独立故障驱动；VP-04原九安全；VP-05原74回归；VP-06预算/零外部声明。公共runner完整运行executor/evaluator计划；独立驱动仅临时合成流，不调用网络。Evaluator审新RUN实际实现、引用支持关系与历史诚实性。

## Authorization / 权限

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

安装、服务、浏览器与测试付款均false。本包既有文件读取、派生文件、隔离临时故障注入与离线测试已在本任务范围内，无缺失Human事实或权限。

## Stop conditions / 停止条件

任何新网络/凭据使用、原输入漂移、需要改产品/旧证据/冻结AC、超过预算或无法保留失败原文就停止返回Evaluator。普通新包脚本/引用/报告修复在预算内自主完成。若历史事实不可恢复，正确保留UNKNOWN并解释限制，不反复现场取样。

## Project impact and continuation / 影响与后续

impact=NOT_APPLICABLE。修复通过只恢复入口测量的证据可信性；不认领新外部资格或支付成绩。后续运行必须另冻较长包并核原截止、剩余请求/字节；无法证明正余额则先解决该精确资源/授权缺口，不自动换平台或索要真实资料。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/12/15/20；CORE/ADAPTER/EVIDENCE_ONLY的单取证链修复；before=失败信息丢失/矩阵漏消费，after仅对应Test/Evidence；不提升支付/强认证/密钥治理/签名信任源或合规成熟度。
