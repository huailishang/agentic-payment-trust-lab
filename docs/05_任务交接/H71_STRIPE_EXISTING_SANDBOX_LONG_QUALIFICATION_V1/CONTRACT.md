# H71：既有Stripe匿名环境长资格测量包

Task ID: H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H71_STRIPE_EXISTING_SANDBOX_LONG_QUALIFICATION_V1/VALIDATION_PLAN.yaml
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-12-r115
Active bottleneck: B-21
Hypothesis: H-71
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

项目目标为授权→绑定→执行→恢复→可消费审计。A–D本地关闭、E受控本地闭合、F当前。H69创建一次成功、Account三次403；监听、Checkout写入及付款未知。H68R本地修复已经签收，不重复扩例；H67人工延期。B-21最前置难点是匿名受限key的必要读取/监听权限与同环境证据关联。

Human本轮要求较长执行包、同包多步骤、最后统一复核且质量不降。未执行的H70窄包因此由本包显式替代，原件完整保留，不追认为失败或已执行。本包将资料核验、真实只读资格、固定CLI监听、本地浏览器能力和既有安全/回归合并；前置满足就按冻结规则继续，不逐步回Human复核。

Metric baseline: 匿名创建已证实，Account403；必要资源读取/测试监听UNKNOWN，合格外部支付旅程0。
Expected project impact: 缩小入口不确定性；只声称读取/监听与本地浏览器资格，不声称Checkout创建/前端付款/真实商户身份成立。
Expected material cost: 120主动分钟/4小时墙钟内的一轮；最多2实现版本/3L2/1L3，公开资料24 HTTP/8MiB，至多一个约11.93MB固定CLI ZIP。预算为上限，不为用满时间追加步骤或Case。
Rollback condition: 任何权限/来源/隔离/身份/预算限制保留证据并停止后续现场阶段；只关闭本任务进程，不删除外部环境，不换平台。

## Single objective / 唯一目标与最难点

判定H69已创建的同一匿名凭据上下文能否完成本仓后续旅程所需的三个资源读取、固定CLI测试监听，以及现有浏览器的隔离本地交互。以一份统一证据包区分READ_AND_LISTEN_READY、INPUT_LIMIT或AUTH_EXPIRED。唯一主要变化是入口资格测量链，产品全部只读。

最难点先处理：GET /v1/account被拒并不等于其它接口被拒；反之，三个空列表与监听READY也不构成真实账户身份保证。允许用封存provision响应的account/key关系→同一key指纹→真实读取/监听串联“同凭据上下文”，必须标PROVISION_CREDENTIAL_CONTEXT_ONLY；不得伪装成独立Account对象核验。Checkout写入权限、真实Stripe前端自动化和支付仍NOT_MEASURED。

## Authorization / 原授权余量的显式分配

依据H68 AUTHORIZATION.json中Human原话「同意按 H68 授权范围执行」（2026-11-12T00:52:09Z），Evaluator显式分配未消费的指定下载/本地服务/现有浏览器/必要只读API余量。当前用户只授权较长任务粒度，不被扩写成新增付款许可或延长授权。AUTHORIZATION.json固定原授权与本次收窄分配。

原截止仍为2026-11-13T00:59:06Z，即北京时间2026-11-13 08:59:06；本包现场窗口为开始后4小时与该截止的较早者。到期即不再进行运行API/下载/监听/浏览器，离线整理可如实报告AUTH_EXPIRED。不得把研究小预算解释为运行授权重置。

H68与H69累计实际消耗先复算：H68没有运行API/下载/付款，H69已有现场GET1、Executor GET1、Evaluator GET1及一次创建；该创建机会已消费，任何POST challenge/provision均禁止。对余额有新消费、开放未知尝试或无法对账即停止现场阶段。本包业务API只允许三个既有白名单GET，不使用余下会话/付款额度。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: true
authorization_install: true
authorization_local_service: true
authorization_browser_test_only: true
authorization_test_payments: false

## Execution steps / 七步连续执行，最后统一复核

### 1. 开工核对与一次准备

核CURRENT、冻结文件/BASELINE及H68/H69账本；原生Windows x64、已有Python/项目依赖、私有材料与端口资格。所有保护输入只读。H69原私有材料原位读取；本包使用另一个仓库外H71_PRIVATE_DIR，不改旧SNAPSHOT/CREDENTIALS。执行者先准备本包RUN、最小HTTPS客户端、取证与进程关闭，再跑便宜离线自检；运行失败不得重建环境或调用CLI登录。

### 2. 官方依据与四维权限矩阵

复用H70的四维矩阵要求：account_read、checkout_required_endpoints、test_listener、same_environment_binding，区分OBSERVED/DOCUMENTED/UNKNOWN。核H69私有错误语义、本仓实际接口、固定v1.55.10源码与官方文档。来源保存原字节/URL/时间/摘要，引用逐字可回指。普通key文档不得被写成rkcs_test_的专门保证。

资料明确禁止当前key访问某接口则停止对应现场阶段；资料没有给出特定key权限时可以在原授权白名单内测量以下只读接口，但不能预先填PASS。矩阵完成后自动进入第3步，无需中间签收；研究达到预算即保留UNKNOWN，不扩新方向。

### 3. 同凭据上下文的三个实际只读探测

只用H69返回的rkcs_test_，API版本2026-10-28.endive，依次各一次GET：`/v1/checkout/sessions?limit=100`、`/v1/payment_intents?limit=100`、`/v1/charges?limit=100`。不再GET /v1/account。禁重定向，单请求30秒/2MiB；实际方法/固定URL/UTC起止/状态/响应字节及摘要私有保存，凭据在环境或内存、不进argv/公开输出。

三个响应均200、object=list、has_more=false、data=[]才继续。新环境本应没有业务对象，发现意外对象立即停止，不能过滤掉再说为空；任何401/403、超时、版本限制不重试、不换key。空列表仅证明读取被接受，不能证明创建Checkout、支付或独立账户真实性。

### 4. 固定CLI下载与隔离测试监听

只有第3步通过才下载H69同一v1.55.10 Windows x86_64 ZIP，至多3 HTTP/64MiB，实际字节SHA/大小须与SPEC相同，仓库外解压；不安装SDK、浏览器、全局配置或其它依赖。原生Windows与WSL路径明确分开，不能假设wslpath在原生Windows存在。

先离线version/help，显式独立config/project，清除继承的Stripe账户选择变量；禁止读取现有CLI登录资料，不改HOME或用户全局配置。仅向子进程环境注入本次key，禁argv key、交互stdin、自动登录/认领/插件安装、自动升级、--live/--latest/--skip-verify/trigger。若固定版本无法以独立配置做到这些则INPUT_LIMIT。

只开一个127.0.0.1:8768回调接收器和一个CLI listen，事件仅checkout.session.completed、checkout.session.expired、payment_intent.succeeded。每进程最多60秒，READY及本次whsec原文只留私有日志，稳定10秒后关闭；端口占用不杀他人进程。实际握手/流和辅助流量单列，不捏造全网请求数。没有实际付款事件，不能将READY写成webhook交付或验签链通过。

### 5. 现有浏览器的本地交互资格

前级均通过才用当前可见的受支持浏览器工具，在新隔离上下文打开本任务自写data页/127.0.0.1页、点击合成按钮、读状态并关闭。至多8工具操作、一次上下文；不启动新Chrome/CDP后备链，不安装框架，不读用户页/cookie。证据保存实际操作及预期状态关联，不能只填browser=true。没有访问Stripe托管页，因此其前端接受自动化仍UNKNOWN。

### 6. 同包回归、合同内修复与收尾

执行已有H68R九项冻结安全检查和原生Windows74项指定回归；不要运行其旧全范围integrity。只修本任务RUN/证据适配，原产品/原测试不得修改。两版实现与三次L2内可修复路径、脱敏、账本、进程关闭、报告等合同内缺陷后继续，不为每次局部修复发新任务。所有失败版本与物质尝试保留。

前级INPUT_LIMIT也要做能离线完成的安全回归、证据与关闭检查；后续现场步骤明确NOT_RUN。安全测试失败、产品需改或预算用尽，停止自修并报告BLOCKED，不削弱checker/AC。

### 7. 一次提交、一次独立复核

关闭本任务进程/主动区间，运行完整冻结L2计划，REPORT统一索引所有步骤、原始三件套、失败与成本。L2全通过才SUBMITTED_FOR_REVIEW；不逐步要求Human签收。Evaluator接受不可变快照后运行一次完整L3；其三个独立GET只占自己的额度，不重跑下载/监听/浏览器或任何创建。若运行授权到期无法完成必要独立回查，不认领READ_AND_LISTEN_READY。

## Acceptance criteria

### AC-01 — 范围、来源与余额

原H70/H69/H68R及产品、旧测试、忽略证据保持；冻结本包不变；所有官方来源字节、引用与获取时间可复核；原授权/截止及共享余额真实，不能重建环境。原H70为未执行替代，不造验收结论。

### AC-02 — 权限矩阵与上下文关联

四行矩阵准确区分实测/文档/未知；H69私有provision字节摘要、原账户引用与本次key指纹一致。Account403不外推其它接口；同key关联不升级为独立真实身份保证。资料未能回答可标UNKNOWN，但没有依据的成功项不能PASS。

### AC-03 — 真实读取与独立回查

实际三个固定GET按顺序各一次、原始响应与账本逐次匹配；前置成功方可进入下载。READ_AND_LISTEN_READY还须Executor/Evaluator分别以同一凭据独立核三个列表仍200/空/完整。失败分支可如实签收输入受限的测量，不能因此认领成功。回查摘要、独立nonce与checker摘要绑定，同actor复跑只审原证据不再发请求。

### AC-04 — CLI与进程隔离

成功分支实际ZIP大小/SHA、离线版本/help、独立配置、test-mode READY/whsec私有原文及两个进程关闭证据完整；未运行则NOT_RUN。任何旧配置读取、密钥进argv、自动登录/升级、无法证明隔离或进程关闭均不通过。

### AC-05 — 本地浏览器与声明边界

成功分支本地实际点击/读取/关闭可复核；失败分支真实记录工具限制，不能以H68原失败或历史data页成功代替本次。Stripe托管前端、Checkout写权限、付款、真实事件/商户身份仍未测。

### AC-06 — 安全与质量守护

冻结九项安全检查及原生Windows74回归保持。预算内只修任务脚本，不改产品/旧测试；L2/L3不降低任何强制项。失败分支与成功分支均需保护输入和安全回归，客观不可复核项不能PASS。

### AC-07 — 统一完整证据与预算

逐尝试BEGIN/END、阶段依赖、失败/NOT_RUN、活跃时间、下载字节、工具操作和进程起止可复核；公私摘要相符，敏感值不公开。0匿名创建/0会话/0付款/0生产/0提交推送，L2与L3均只读重核，不重做现场步骤。

## Allowed scope / 允许范围

Executor仅新增本包RUN.py、REPORT.md、RESULT.json、PERMISSION_MATRIX.json、SOURCE_MANIFEST.json、ATTEMPT_LEDGER.jsonl、sources/、evidence/、versions/；CURRENT只改本任务state/phase/正常交接。产品/旧任务/冻结文件/地图/AGENTS全部只读。不得修改或刷新BASELINE/CHECK/SOURCE_CHECK/SPEC/AUTHORIZATION/SCHEMA_GUIDE/计划。

## Exclusions / 排除范围

不创建匿名环境、Checkout、PaymentIntent、Charge或付款；不重新查询Account，不发测试事件，不访问托管Checkout页，不执行原H68四旅程，不扩产品/商城/钱包/攻击集；不使用真实邮箱/资料/卡、登录/认领、生产key、公开webhook、代理绕过或任何真实资金。不修改公共workflow架构或新增审核角色。

## Validation plan / 验证计划

公共runner一次完整计划：VP-01 integrity；VP-02 sources；VP-03 artifacts；VP-04分actor独立readback；VP-05冻结九安全；VP-06冻结74回归；VP-07 budget；VP-08资格判别器的停止分支与伪成功反例。L2最多3次，L3一次；重复门禁复核已封存现场证据，不重复发起下载/监听/浏览器。Evaluator另审实际传输、接线、私有原文、阶段依赖与声明，不仅看结构字段。

本包实现版本/L2预算仅用于新增任务编排与离线验证，按Human本轮较长任务要求冻结；不增加H68产品实现次数或任何外部配额。产品保持只读。

## Budget and stop conditions / 预算与停止条件

SPEC是机器上限：120主动分钟/4小时墙钟且现场不越原截止；2实现版本/3L2/1L3；来源24 HTTP/8MiB/单URL2/并发1；现场三个GET各1，Executor/Evaluator各三个GET各1；下载3 HTTP/64MiB；CLI离线检查2、listen/接收器各1且60秒；本地浏览器8操作。共享H68原总额度先扣H68/H69真实已消费；余额不足即停，失败照计，无匿名创建和付款机会重置。

前级成功自动继续；只有真实身份/登录/验证码、非测试/非本次凭据、明确权限限制、来源/版本不符、异常对象/副作用、敏感信息泄漏、无法关闭进程、保护漂移、预算/截止或需改合同义务时停。普通任务内路径/报告/取证修复不触发中间Human复核。

## Project impact and continuation / 影响与后续

impact=NOT_APPLICABLE。READ_AND_LISTEN_READY只允许Evaluator考虑下一较长托管支付旅程包，不提升Checkout写入、前端自动化、付款或主体真实性成熟度；INPUT_LIMIT准确定位阶段，停止当前现场，不重复403或自动换平台。资料与现场测量统一复核后，才比较CONTINUE/STOP/SWITCH。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/12/15/20；CORE/ADAPTER/EVIDENCE_ONLY的单入口证据；before=必要资源/监听未知，after按实际Test/Evidence；不提升强认证、凭据治理、签名信任源或合规结论。
