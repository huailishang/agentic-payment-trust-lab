# H52 UCP/AP2授权至执行接入就绪测量（长串行执行包）

Task ID: H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-30-r84
Active bottleneck: B-17
Hypothesis: H-52

项目目标是授权、绑定、受控执行、恢复与审计可复核。A–D阶段关闭、E仅本地代表性闭环、F当前。H51固定HTTP接线已PASS并STOP，不能再以本包重做同类路由或锁测量。B-17最前缺口是UCP标准授权、已验签材料、中立业务判断与商家执行责任是否接成同一可信输入链。

Human于2026-10-30要求：“好的，你按照这个思路去整理一下，制定下一个执行包。可以制定长的执行包，然后统一评估”。本包据此串行走完全部测量和交付后一次复核；不逐阶段等待签字，不把“长包”解释为扩大生产/网络权限或先实现三阶段。旧2小时草案归档DRAFT_BEFORE_FREEZE_20261030.md，原评估保留；本合同为当前唯一执行授权。

Measurement status: 本地方法/HTTP及H37签验已measured；标准授权到执行组合unknown。
Metric baseline: H51 L3 8/8、23方法保持；H37代表性8例已接受。新12签名材料探针与12义务表未由Executor执行，不能声称0→12能力增益。
Expected project impact: 收敛一个最小后续实现边界或明确商家合同变化/停止理由，不直接升级产品能力。
Expected material cost: medium（中等估计），复用现有H47 Windows环境及旧H37纯Python依赖，无安装/模型/API成本。
强备选：继续锁/路由样本边际收益低；Stripe/Medusa引入服务方或商城新变量，当前授权/执行接缝未定，不抢占本包。支付宝与比赛继续延期。
本包不是capability_experiment（能力实验）；Task PASS不自动等于项目IMPROVED。

## Single objective / 唯一目标

用固定官方资料、现有SDK/产品API的真实离线签名材料测量，判断“标准UCP/AP2授权可怎样复用现有控制进入实际商家执行点”，最终仅给一个有源码和运行证据的下一边界或STOP。严格区分验签有效、投影来自已验签内容、业务规则通过、用户同意和商家已执行；这些概念不能互相替代。

串行完成：
1. 审计3份已固定官方来源、AP2 v0.2.0固定源及现有UCP花店profile/schema/入口；形成版本兼容表。
2. 明确四个受控角色及合成确认事件的可信假设，说明谁可签发、谁验证、哪些事实来源不由模型控制。
3. 实现PROBES.py，按CASE_SPEC.json运行12个真实签名材料探针，保留原始公开材料和实际API结果。
4. 对照12项接入义务，把已测、源码可见、缺口、不可观察分开；指出最前断点及未来商家改动最小位置。
5. 给出一个下一接入边界和未来验收设计；完整8项L2后一次交Evaluator。
普通不支持、缺字段、发现现有函数只负责局部验证，均是应记录的测量结果，继续做完其余材料；只有硬停止条件触发才提前停止。

## Fixed sources, environment and trust assumptions

- SOURCE_MANIFEST.json固定3份公开文档的原文、文本、URL、许可、摘要；Executor全离线，不重新下载main或自行扩大调研。
- 花店固定H51 merchant/routes/discovery_profile.json：UCP 2026-04-08，未广告AP2扩展；参考规范与教程为2026-08-25。不能静默升级schema/SDK或把字段存在当能力已实现。
- AP2源码固定local_sources/third_party/ap2-v0.2.0、commit b4587ac1d055888a73b4b21750973cffba961793；原许可Apache-2.0；只能调用既有真实API，不重写签验算法。
- 现有运行命令使用.task_envs/H47/.venv/Scripts/python.exe。RUNTIME.py仅追加旧jwcrypto=1.5.6/sd-jwt=0.10.4纯Python模块，编译依赖仍H47：cryptography=46.0.7/pydantic=2.13.4；ucp-sdk=0.4.6。新组合仅用于本包，不能倒写H37原环境或验收。
- RUNTIME.py已准备验证imports及旧H37 8例、76相关测试。准备过程首次focused因tests路径缺失失败，修正ROOT导入后76/76；保留PREP-FOCUSED-01/02。单一API接线smoke已通过，仅说明参考API可用，不是Executor12例或端到端能力通过。
- 四角色各独立内存EC P-256 key，kid=h52-角色名，公开key可落证据，私钥不可落盘；全部合成主体。预置信任trusted_user，不能相信请求自带root来证明用户同意。
- 正常probe：商家真实JWS签署固定ASCII/整数checkout；官方SDK签发OpenPaymentMandate root及PaymentMandate terminal，checkout_hash绑定完整compact checkout_jwt，trusted_user→delegate_agent两跳。此窄签名夹具不是完整UCP checkout/JCS实现，不得声称JCS合规。
- experiment_context只能填写冻结的合成试验上下文；真实身份、服务方、客户、端到端执行均未测，不自动补齐缺失事实。
- SDK日志仅重定向.task_envs/H52/runs，不能改官方验证函数或source；不能导出私钥、真实个人/支付数据。原始token为本任务合成材料，不是生产凭证。

## Acceptance criteria

### AC-01 — 来源、环境与范围

Given上述固定来源、现有工作区与环境；When VP-01/02；Must observe保护摘要、HEAD、源码/纯Python依赖与环境版本一致，来源归因/许可证与2026-04-08对2026-08-25差异明确；Must not observe新依赖、旧任务/产品修改、静默升级、外部调用；Evidence=BASELINE、SOURCE_MANIFEST、SOURCE_AUDIT、COMPATIBILITY、原始EV。Mandatory: yes。

### AC-02 — 真实材料与独立可复算测量

Given四角色、固定时钟、12个冻结变更；When VP-03/04；Must observe每例公开注册key、完整chain/snapshot/验证参数、真实官方签验/边界适配/validator结果，checker从原始输入独立复算一致；Q01合法链可形成VALID/ALLOW局部事实，Q07可信root检查与自带root诊断分列；Must not observe假签名、硬编码状态、用参考函数代做Executor测量、把输入自带root当用户授权。Evidence=observations_l2.json及独立重跑。Mandatory: yes。

### AC-03 — 信任层级与投影血缘不混淆

Given Q02–Q12及当前API责任范围；When VP-03/04/05；Must observe篡改checkout、换签checkout但PM旧hash、投影金额/收款方/币种变化、无同意、过期、错误受众、带seen-id重放、缺上下文的完整真实结果及差异归因；未强制的义务明确GAP或NOT_OBSERVABLE，而不是补实现使其过；Must not observe把crypto VALID当业务允许、把ALLOW当真实同意/付款、把合成缺口升级为官方漏洞。Evidence=PROBES/raw observations/TRUST_BOUNDARY/12义务表。Mandatory: yes。

### AC-04 — 形成一个有证据的最小下一边界

Given固定商家和12项接入义务；When VP-02/05；Must observe每项有源码/规范行号锚点、责任方、当前状态和REUSE/BRIDGE/MERCHANT_CHANGE/DEFER动作；明确默认工厂、AP2能力协商、完整签名载荷/JCS、可信确认、金额/币种/收款方、执行占用/撤销先后、稳定服务方引用与审计回传；NEXT_BOUNDARY只选一个方向并列未来正负验收、实现边界/非目标及停止条件；Must not observe自动Stripe/Medusa/ADK迁移、另写授权服务、把未来测试算已执行、无共同缺口就扩核心。Evidence=READINESS_MATRIX/NEXT_BOUNDARY/RESULT。Mandatory: yes。

### AC-05 — 回归保持、预算与完整交付

Given6主动小时/3次正式L2/144材料case上限；When VP-05..08及完整L2；Must observe76相关测试与旧H37 8例保持、原始EV、各AC证据、失败/重试/花费、单一结果与残余风险诚实；Must not observeL2失败仍SUBMITTED、覆盖失败观察、隐藏准备失败、原生能力/身份/生产/服务方/客户成熟度升级。Evidence=正式L2/账本/检查器自测，Evaluator独立L3与源码审阅。Mandatory: yes。

## Allowed scope

只允许新建/修改本目录PROBES.py（测量驱动）、SOURCE_AUDIT.md、COMPATIBILITY.json、TRUST_BOUNDARY.md、READINESS_MATRIX.json、NEXT_BOUNDARY.md、RESULT.json、REPORT.md、ATTEMPT_LEDGER.json及evidence/。临时输出仅.task_envs/H52/runs。
CASE_SPEC、RUNTIME、REFERENCE、PACKET_CHECK、RUN_PROBES、CONTRACT、VALIDATION_PLAN、sources/、SOURCE_MANIFEST、入口、准备脚本/记录、历史草案/评估和BASELINE只读。所有src/tests、H37/H47–H51及旧task、源码和外部依赖只读。
CURRENT仅CONTRACT_FROZEN→EXECUTING/Executor及execution_phase更新；task/map/hypothesis/历史/权限/next_artifact=REPORT不变。不得给其他聊天发消息，不使用代理。
PROBES必须由RUN_PROBES.py启动；独立构造真实材料并调用既有API，不得调用REFERENCE.recompute代做测量。可使用SDK/JWK/JWS/既有产品类型和辅助序列化，不实现新业务拒绝规则、不改验签器。

## Deliverables and schemas

- COMPATIBILITY.json: schema=h52-compatibility/v1；merchant_ucp_version=2026-04-08；reference_ucp_version=2026-08-25；merchant_ap2_advertised=false；auto_upgrade_performed=false；另列SDK/schema差异和所需动作。
- observations: schema=h52-signed-artifact-observations/v1；具体字段/固定变更见CASE_SPEC和PACKET_CHECK。observed结构见REFERENCE；所有原始输入必须保留，不能只交passed=true。
- READINESS_MATRIX.json: schema=h52-readiness-matrix/v1，12唯一id；status=MEASURED_LOCAL/SOURCE_ONLY/GAP/NOT_OBSERVABLE，next_action=REUSE/BRIDGE/MERCHANT_CHANGE/DEFER；claim、责任owner、说明、references[{path,start,end,anchor}]及关联probe必填解释。结构checker不能替代Evaluator逐项判断真假。
- RESULT.json: schema=h52-readiness-result/v1；唯一classification=READY_FOR_BOUNDED_IMPLEMENTATION / MERCHANT_CONTRACT_CHANGE_REQUIRED / STOP_NO_JUSTIFIED_INTEGRATION；remaining_gaps非空、one_next_action单一，customer_demand=UNKNOWN，evidence_boundary为冻结值；PACKET_CHECK.FALSE_FLAGS九项全false。READY仅为下一任务就绪，不是接入已完成。
- SOURCE_AUDIT/TRUST_BOUNDARY/NEXT_BOUNDARY每份至少500字符，内容须覆盖本合同，不以长度充质量；REPORT按公共v2.2模板逐AC、Impact comparison、L2与全部EV原始三件套、局限/预算。
- ATTEMPT_LEDGER：formal_l2_attempts<=3、active_work_minutes<=360、artifact_cases_run<=144；网络/模型/Provider/ASGI/付款计数全0。RUN_PROBES先预留12case，失败同样计数，观察覆盖前归档。Evaluator独立账本<=72case，不改Executor账本。
- 每次实质probe运行必须保留不同输出或归档及账本，不静默丢弃失败。正式L2预算先计数，过关后才SUBMITTED_FOR_REVIEW；准备检查不计Executor正式L2。

## Validation plan and budget

8项固定计划：VP-01范围/环境；VP-02来源与义务表；VP-03十二真实材料探针；VP-04独立原始输入复算；VP-05材料/分类/账本；VP-06 76相关回归；VP-07旧H37八例；VP-08检查器自测。
主动6小时、最多3次正式L2、材料case总144（12次完整波次）、单次12case；串行、max_parallelism=1、代理0。Evaluator材料case上限72。完整交付后只做一次集中L3，普通问题在合同/预算内修复，不逐阶段等Human。没有自动下一实现授权。

## Exclusions and stop conditions

无商家/ASGI/外部socket/监听/HTTP/DNS/模型/真实或测试支付/Provider调用；无Stripe/Medusa/ADK部署；无安装、真实账号/密钥读取、真实个人信息、资金、Git提交/推送/改历史、对外联系。
保护漂移、环境或依赖不符、需要扩大源码/架构/AC/权限、秘密落盘、预算耗尽或同一失败无新机制即停止并报告精确原因。正常“不支持/缺证据”不应伪造通过，也不应把剩余材料半途丢弃；将结果分类并整包交Evaluator。
若测量发现需要改商家扩展、增加可信签发器或产品组合逻辑，只写最小边界，不在本包实施。H51 STOP保持，不重开旧方法锁方向。

## External requirement impact

已核对PCAC开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；requirement_ids=PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；maturity_before=现有本地证据；maturity_after_target=接入差距有独立测量，不升级产品/生产身份成熟度；Test=VP-01..08；Evidence=来源/原始签名材料/12义务表/独立复核；残余=真实主体、确定性用户确认来源、商家部署/旁路、跨系统撤销、Provider、客户未知。无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
