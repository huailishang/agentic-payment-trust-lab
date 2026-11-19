# H69：Stripe匿名环境与测试通知入口资格测量

Task ID: H69_STRIPE_ANONYMOUS_SANDBOX_QUALIFICATION_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H69_STRIPE_ANONYMOUS_SANDBOX_QUALIFICATION_V1/VALIDATION_PLAN.yaml
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-12-r113
Active bottleneck: B-21
Hypothesis: H-69
Dispatch mode: SINGLE

## Strategic basis / 战略依据

H68R已独立L3 3/3、安全9/9及Windows74/74通过，修复四类本地缺陷；不再追加同类本地Case。B-21外部合格旅程仍0。现有浏览器仅证明隔离自写页可交互，匿名沙箱/测试账户/事件监听尚未知。本包只测这三个最先未知的入口，比重复平台研究、直接付款或重开H67更有信息价值。

Metric baseline: 未创建Stripe匿名环境，未建立测试监听，无本账户外部查询证据。
Expected project impact: 得到可复查的入口资格或精确输入限制；不认领外部支付/交付能力增量。
Rollback condition: 所有运行进程仅本任务所有、结束后停止；外部匿名环境不可谎称已删除。失败/超限/登录要求即停，不重复创建、不换平台。

## Objective / 唯一目标与边界

判定明确合成联系标识能否获得一个官方匿名测试环境、能否查询该环境自己的账户，以及固定官方CLI能否建立test-mode监听。结果只允许ELIGIBLE、INPUT_LIMIT或UNKNOWN_PROVISION_RESULT。INPUT_LIMIT可作为真实测量结果，但不得写成环境可用；超时创建结果未知不得写成未创建。

不创建Checkout会话、不支付、不发测试事件、不证明前端接受自动化、不声称真实webhook已收到。成功也只结束本入口测量，再由Evaluator制定后续托管结账旅程。

## Authorization / 既有授权的显式分配

授权依据是H68 AUTHORIZATION.json记录的Human原话「同意按 H68 授权范围执行」，时间2026-11-12T00:52:09Z。H68原账本匿名创建/下载/API/付款均0。本包由Evaluator显式分配其中未使用的匿名环境、指定CLI、回调服务及本账户只读余量，范围比原批准更小；不是从H68R继承权限，更不是新增一次匿名创建机会。

原H68第一次工作开始于2026-11-12T00:59:06Z，因此原24小时截止仍为2026-11-13T00:59:06Z；H69不得延长。H69开始前须复核原账本摘要与零消耗事实；若其它任务已经消费匿名创建机会，本包停止交Evaluator。后续所有任务共用同一次创建，不自动补建过期环境。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: true

仅允许本合同的API、隔离下载和本地服务。浏览器、正式登录、真实邮箱/姓名/卡、认领、生产、钱包、支付、退款/转账、提交推送一律禁止。当前复核只制包、不执行外部动作。

## Mechanism and sources / 机制与来源

固定Stripe CLI v1.55.10、服务端API版本2026-10-28.endive。来源见SOURCE_LOCK.json和H68原来源锁；本轮已重新读官方固定版本sandbox.go及CLI文档。

官方CLI匿名创建在失败时可能进入登录，因此不运行sandboxes create。仅在任务RUN.py里用Python标准库复现官方pkg/sandbox/sandbox.go的公开challenge/provision过程：POST challenge发送合成email；只接受SHA-256算法，按官方salt和十进制number求挑战解；POST provision提交原challenge/salt/signature/number/email，不加真实姓名。计算上限100,000,000次且30秒，先到即停；不是规避挑战。不执行服务端返回的代码，不跟随登录/浏览器后备路径。

只允许POST `https://ai.stripe.com/keys/challenge`一次和`/keys/provision`一次；联系标识固定`h68-checkout-lab@example.invalid`。HTTP重定向禁止、每请求30秒、响应2MiB；任一失败不重试创建，provision超时按UNKNOWN处理。合成地址被服务接受仍未知；需真实收信/验证码即停。

创建成功后只用响应里的rkcs_test_凭据，GET `https://api.stripe.com/v1/account`核对响应account_id。账户对象没有通用livemode字段，不编造；依据隔离匿名响应、测试凭据前缀和监听模式分别记账。不得读本机既有CLI配置或浏览器资料。

只有账户查询通过后才下载固定Windows x86_64 ZIP。一次下载逻辑、总HTTP至多3次/64MiB，重定向仅GitHub官方release资产；核SHA-256后仓库外解压。宿主不是原生Windows x86_64或发行包不符即停，不找其它版本/宿主。无全局安装、无SDK/浏览器/框架安装。

CLI只运行离线version/help及listen，使用仓库外新配置/独立project-name，关闭自动更新。移除继承的Stripe账户/凭据选择变量后，仅向子进程环境注入本次测试key，禁止出现在命令行、公开日志或工具输出。listen限定checkout.session.completed、checkout.session.expired、payment_intent.succeeded，转发127.0.0.1:8768/stripe/webhook；禁止--live、--latest、--skip-verify、trigger、登录/认领、创建公网webhook。

一个回调接收器仅监听127.0.0.1:8768；端口占用即停，不杀他人进程。监听READY后保留10秒、单进程总时长最多60秒，然后停止本次两个进程；日志及签名秘密只进私有目录。CLI握手/流及自带辅助流量按进程/时长/可观察请求单列，不捏造精确全网次数；本包不产生支付事件。

## Acceptance criteria

### AC-01 — 保持、来源与授权余量

新BASELINE保护H68/H68R原报告、L2/L3、合同/检查器、修复代码和历史输入；不改产品。原匿名机会未被消费，原截止和本包上限保持。下载真实字节SHA符合固定发行包；若前级受限未下载则明确NOT_RUN。

### AC-02 — 可判定的资格结果

挑战/创建/账户的实际请求方法、固定URL、开始/结束、状态或超时、私有原始响应摘要逐条关联。ELIGIBLE必须有成功provision、测试key、本账户查询相符；INPUT_LIMIT必须有具体失败阶段原文；UNKNOWN_PROVISION_RESULT保留写请求结果未知，不发第二次POST。未到阶段明确NOT_RUN，不补造账号、凭据或成功。

### AC-03 — 监听资格和边界

ELIGIBLE还须固定CLI校验、test-mode监听READY、原始私有日志含本次签名秘密、两个进程结束证据。前置受限可不运行监听，不能认领可用；创建了账户但监听失败须记INPUT_LIMIT并保留该账户，后续复用而不新建。不把READY写成实际事件/付款链通过。

### AC-04 — 独立回查、预算和最小化

公开RESULT只含状态/阶段/摘要/去敏账户引用，原始HTTP/密钥/claim URL/签名秘密在仓库外私有目录。L2/L3均不重跑创建、下载或监听；创建已确知时各用自己的GET额度查同一账户，无法独立查询不能认领ELIGIBLE。无账户可查的失败分支只复核原文与接线，不声称已证外部不存在环境。追加账本、失败照计、所有本任务进程关闭；0会话/0支付/0浏览器/0提交推送。

## Allowed scope / 允许范围

Executor只新增本包RUN.py、RESULT.json、REPORT.md、ATTEMPT_LEDGER.jsonl、evidence/、versions/。所有产品、H68/H68R任务、旧测试、冻结输入只读；不复制或修改上游CLI源码，不改权限或基线。CURRENT仅执行state/phase。私有目录用H69_PRIVATE_DIR，先校验位于仓库之外；本包既有CHECK/SPEC/SOURCE_LOCK/AUTHORIZATION/BASELINE/PREPARE/计划由Evaluator冻结。

## Exclusions / 排除

不做四旅程编排，不发Checkout/PaymentIntent/Charge/退款/支付API，不接商城、不扩新攻击、不换平台、不激活钱包，不安装依赖/代理/浏览器/全局配置。不得以反复curl或CLI登录后备逻辑绕过资格失败。不在L2/L3重复任何写入。

## Validation plan / 验证计划

公共runner按冻结计划：VP-01 integrity；VP-02 artifacts读取私有原文与公开摘要；VP-03 readback分别actor=executor/evaluator。失败测量可如实形成报告，但所有证据AC仍须满足，不能凭自报INPUT_LIMIT就跳过检查。Evaluator另审实际传输/挑战/进程/数据落盘接线及共享预算；runner通过不自动签收。

## Stop conditions and budget / 停止条件与预算

45主动分钟/2小时墙钟且不得越过原H68截止；准备实现1、L2两次、L3一次。匿名流程1，challenge POST1/provision POST1且无重试，现场account GET最多2，Executor/Evaluator独立GET各2；下载HTTP最多3/64MiB；监听与回调进程各1/60秒；单请求30秒。全部累计计入原H68总额，本包不重置余额。开始前逐项BEGIN预留、完成END；失败也保留。公开研究来源读取与运行API分开，不宣称本轮总网络0。

真实邮箱/身份/登录/验证码、非测试key/非本账户、来源/版本不符、异常写入/敏感信息公开、超时或预算不足即STOP并保留证据。一个阶段受限不在后续阶段继续尝试。不得为凑ELIGIBLE新增预算；外部结果未知时不重试POST。

## Project impact and continuation / 影响与后续

本包为one_off资格测量，impact=NOT_APPLICABLE。ELIGIBLE仅允许Evaluator考虑同一环境的后续托管链；INPUT_LIMIT/UNKNOWN则按具体限制STOP，可能需要Human事实时只问该缺口。H67不恢复，PayPal/x402不自动启用。后续真实主体、资金、商业采用和合规不升级。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/12/20；ADAPTER/EVIDENCE_ONLY；before=匿名环境/监听未证实，after只记本次入口资格Test与私有原文Evidence；不提升支付/强认证/密钥治理/签名信任源成熟度。
