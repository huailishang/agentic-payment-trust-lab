# H72R — 离线复核门禁闭合修复

Task ID: H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/VALIDATION_PLAN.yaml
Authorization: 本地可逆修复和验证；全部新增外部动作、安装、Git提交/推送为0。沿用项目Evaluator派发离线修复的职责，不恢复H72现场额度。

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-15-r121
Active bottleneck: B-21
Inherited hypothesis: H-72
Parent verdict: H72 REJECTED / INCONCLUSIVE / CONTINUE，见其REVIEW及完整L3 14/15。

目标仍是可独立复核支付信任链；A–D本地关闭、E受控本地代表闭合、F当前。外部四功能事实已有独立证据，整包未签收。第一断点是原生查询本地化误报、路由测试依赖调用上下文及读取计量报零。这个repair（修复）只闭合复核能力，不加业务Case、不提升真实性或生产成熟度；复用本次13GET优于重付或更换平台。

## Single objective / 单一目标

在不变的H72支付、数据库、通知和独立回查原件上，建立一个跨系统语言及合法角色上下文均可复核、又能拒绝结构/权限/预算损坏的本地门禁。单一主要变化是任务局部复核逻辑与其真实入口验证；不改支付业务或原任务结论。

## Dependency and branches / 依赖及分支

1. 先核本包BASELINE/原件、原生Windows agent环境和授权时间；发现内容漂移先停止，不把治理迁移误写成原支付证据变化。
2. 本包实现CHECK.py、NEGATIVE_TESTS.py及必要小辅助模块。可从原H72复用小函数/测试语义到本包，旧代码/报告/证据只读；不重写公共工作流或架构。
3. 完成结构查询、显式角色隔离用例、账本计量；普通路径/参数/采集问题在窗口内自主修补。原始查询必须逐次留存，正常流程不跟随重解析节点，不使用仅供副本的检查代替真实节点验证。
4. 运行必要守护与离线对象/签名/恢复联结，最后统一公共L2；成功后提交REPORT。Evaluator接受快照后独立L3，只读本地原件，不访问Stripe。

修复成功转入统一复核；普通失败在1个主要实现方案、2次L2和时间内继续；原始内容异常、产品反例、需改变范围/预算或需要外部请求即停止并报告，不扩大任务。

## Acceptance criteria / 逐项验收

### AC-01 — 原件、治理迁移和范围

本包BASELINE锁定全部H72权威原件、产品及旧测试、公共工具和HEAD。H72原保护清单1843项继续核；其中地图与REMOTE是本次Evaluator治理更新，必须分别验证本包当前新摘要和原r120地图/REMOTE原字节归档，不跳过或覆写旧BASELINE。真实支付/私有证据只读且不漂移；CURRENT仅流转本包，所有外部权限false。Mandatory: yes。

### AC-02 — 原生查询结构验证

真实Windows fsutil查询原节点，保存完整stdout/stderr及摘要，独立严格解析标签、声明数据长度和连续十六进制数据；与既有原始记录对比实质字节。英文/中文说明文字可不同但历史文件原字节摘要不可变；相同结构两个版本均通过。改变标签、长度、载荷、截断或无法唯一解析时必须拒绝，不能只比较文本摘要、只认标签、忽略多余/缺失数据或跟随节点。Mandatory: yes。

### AC-03 — 角色无关的真实拒绝自测

保留H72原16项自测的保护/范围/旧FAIL/角色/权限/预算/收据语义，以任务局部副本调用本包实际检查入口。明确构造合法Executor/EXECUTING、Evaluator/READY_FOR_REVIEW及非法组合，不从真实CURRENT盲替换字符串。在两个合法调用者上下文下都完整通过同语义16项；原test_02/test_06必须证明实际输入不同且按预期接受/拒绝。副本检查有明确NON_ADMITTING标识，不能替代真实节点检查；真实根路由和历史文件不被变异。Mandatory: yes。

### AC-04 — 账本计量及声明

从H72不变RESOURCE_LEDGER复算现场35、执行者5、评估者13、可控总53；13次独立读取不可报0。读取历史原前缀/序号、失败及角色归属可核；超额、负数、重复/断序在副本拒绝。合成USD3、浏览器66、4会话/3提交及2/3进程保持，不增加资源消费。D01明确为交付记账/收据失败恢复，传输中断重传未测；CLI/浏览器未知子请求不冒充全网络精确计数。Mandatory: yes。

### AC-05 — 原必要守护与正规门禁

同一原生Windows Conda agent及任务局部用户包实际通过原9安全/74回归/11取证/9生命周期，以及6个URL用例。旧断言/计划/公共runner不改。本包11项计划完整公共L2及独立L3均通过，原H72 L3继续FAIL；本包通过不是原H72改判。Mandatory: yes。

### AC-06 — 外部事实的离线复算

仅从已有本次Evaluator13份独立GET原文、数据库及3原始通知验证4/3/3对象、每例原订单/运行/操作/资源/金额/币种/测试模式、R01原付款恢复无重付、D01收据唯一与去重。3通知独立HMAC正例及篡改/错误秘密/过期反例拒绝；不信FINAL字符串代替源证据。报告分别记四功能事实成立、原整包未签收和本包修复状态；不得把真实强认证、签名信任源、生产清算或商户采用升级。Mandatory: yes。

### AC-07 — 预算、安全和完整交接

新包BEGIN/END、源码版本、所有失败/正式门禁三件套可核；原件/共享环境未污染，秘密不出仓库外私有目录。60主动分钟/3小时墙钟、1方案/2本包L2/1本包L3；不越2026-11-16T04:08:37Z，累计H72主线480主动分钟（原约103分钟及本次Evaluator时间均保留、不清零）。新增网络/API/下载/安装/服务/浏览器/支付/模型/Git写入全0；任一强制项无法复核不得提交为通过。Mandatory: yes。

## Allowed scope / 允许范围

- 本包新增/维护CHECK.py、NEGATIVE_TESTS.py、本地小辅助模块、runtime/、versions/、derived/、ATTEMPT_LEDGER.jsonl、RESULT.json、REPORT.md、evidence/。不得新增通用框架、第二套runner或公共Gate。
- CONTRACT、VALIDATION_PLAN、BASELINE、FROZEN_INPUTS、EXECUTOR_START、references冻结后只读；Evaluator拥有最终REVIEW与治理更新。
- 原H72与全部产品/旧测试/公共工具只读。本包runtime可建立进程级PYTHONUSERBASE/tests入口，根tests.__path__仍限定原仓tests；禁止共享依赖更改、启动钩子、断言/Path/subprocess猴子补丁或替换旧回归。
- 仓库外H72私有目录仅按已封存locator读取已有数据库/对象/通知；不打印key、秘密、原始结账URL或真实账号数据，不读取通用配置/凭据/cookie。

## Exclusions / 明确排除

不改变H72合同、15项计划、已接受报告、任何原始收据或失败Gate；不改支付代码、旧测试或运行既有四旅程脚本；不访问Stripe/其他网站、启动服务/浏览器/CLI监听或新增支付；不实现传输层故障业务、第二平台、通用运行时、凭据治理或新攻击族。

## Validation plan / 验证计划

固定11项精确命令见VALIDATION_PLAN.yaml；所有命令离线，Evaluator与Executor使用同一计划，不包含现场evaluator_command。实现CHECK的environment/preservation/native/negatives/accounting/offline-evidence/summary七个命令。summary在Gate生成前仅核事实/引用，不循环要求尚未生成Gate；提交后核完整公共Gate和元数据。

## Stop conditions / 停止条件

零容忍产品反例、既有源证据漂移、超预算/超截止、需新权限/新外部请求、修改AC/范围/旧断言/假设时停止交Evaluator。H72旧次数不续期；新包仅有本合同明确分配的本地验证额度，不得用改目录掩盖重复正式尝试。额度耗尽如实BLOCKED，保留原件，不伪造或覆盖Gate。

## External requirement impact / 外部要求影响

profile=PCAC-AGENTPAY；直接PCAC-12/20，兼顾PCAC-15；CORE/EVIDENCE_ONLY。对象仅复核门禁，before=未闭合、after=待证据，不改H72复合M0或宣称M4。Test为本11项及原守护；Evidence为新EV/RV-EV、原H72 L3/13GET/通知原件及本地结构反例。残余风险为真实身份/凭据/生产支付/商户采用及传输级交付未测；不作监管合规结论。
