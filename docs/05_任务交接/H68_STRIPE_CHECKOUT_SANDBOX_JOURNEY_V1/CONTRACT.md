# H68：Stripe 外部沙箱长结账链验证

Task ID: H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: bounded external test-state writes, no real funds
Contract state: CONTRACT_FROZEN
Freeze readiness: AUTHORIZED_2026-11-12T00:52:09Z / EXECUTOR_BOUNDED_RUNTIME
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-11-r111
Active bottleneck: B-21
Hypothesis: H-68
Metric baseline: 本仓Stripe外部托管结账及恢复的已核代表旅程0条；这不是已有产品失败率。A–D本地关闭、E受控本地闭合、F当前；H67由Human延期且未执行。制包时原订单/恢复/生命周期/治理模块61项针对性基线测试通过，未执行Stripe。
Estimated affected scope: 一个隔离测试商户、一个数字资源、四个功能旅程；外部Stripe结账/付款/事件/查询和本仓订单/交付共同关联。
Expected project impact: 将Stripe方向从文档资格提升为可独立查询的外部结账、恢复和交付证据。原生Stripe幂等/安全机制不记成本仓新增控制效果。
Rollback condition: 资格、自动化、来源或权限受限即停；不改为纯付款API并仍声称托管结账通过，不换平台，不削弱本仓控制。新增模块可撤回，旧源码和H任务不变；沙箱测试记录不伪装可逆删除。
Expected material cost: 估计8主动小时、24小时墙钟内的一轮执行；最多两次实现尝试、两次L2、一次独立L3；一次匿名环境创建，四个结账会话、至多三笔USD1.00沙箱付款，真实资金0。预算细分以SPEC.json为准，失败和重试都计入。

Human于2026-11-12T00:52:09Z明确回复「同意按 H68 授权范围执行」，仅授权AUTHORIZATION_REQUEST.md所列单轮具体范围。Evaluator已将原话及时间记于AUTHORIZATION.json并冻结；真实资金、正式资料、提交/推送与扩大预算仍禁止。本包不要求Human重新选择平台或预先开户。

这是F阶段首次Stripe外部结账实证候选，不是新增战略阶段，也不是已接入独立第三方商城。商户业务订单及交付由本仓控制，Stripe托管结账和测试付款状态在外部服务；真实商户、真实身份、真实资金、生产安全及商业采用均未测。

## Single objective / 唯一目标

在不更改现有控制语义的条件下，将一个Stripe Checkout（托管结账）Adapter（适配器）接到本仓实际付款回调闸门，证明授权/订单、外部会话/付款、可信状态及交付/恢复形成可判定链；用四个功能旅程区分成立、输入受限或失败。

唯一主要变化是这个外部执行接缝。薄商户页、测试环境与取证脚本均为同一变化所需实现，不建设通用商城、钱包、通用运行时、审计播放器或第二套恢复规则。

## Preconditions and authorization / 前提与授权

1. 已获得本包精确受限授权，并由Evaluator记录原话、更新AUTHORIZATION.json与CURRENT、重新冻结INPUTS摘要；Executor必须在CHECK.py integrity通过后才能执行。若冻结摘要或权限与当前不符则停止。
2. 默认尝试官方匿名临时沙箱，不读已有账户/浏览器配置、不使用Git邮箱或姓名。候选联系标识为明确的合成测试地址 `h68-checkout-lab@example.invalid`，仅用作临时沙箱资格探针，不表示真实身份，不认领账户、不接收邮件。其被服务端接受仍UNKNOWN；若需要真实可收信邮箱或验证，立即INPUT_LIMIT，不编造身份或自动换邮箱。
3. 匿名路径只允许一个创建尝试；challenge/provision按官方流程执行，不绕过反滥用验证。失败的浏览器注册/登录回退必须停止，不跟随认领、正式登录或地区资格变更。
4. 用户无需预先手动点击结账；由已有受支持浏览器工具操作官方测试页面。Stripe官方明确前端存在防自动化措施；任何登录、验证码、反自动化挑战或真实支付资料要求均作为资格停止条件，不能绕过，也不承诺自动化必定可用。
5. 默认仅下载官方CLI v1.55.10的Windows x86_64发行包并核SHA-256，解压到仓库外隔离工具目录；不全局安装，不修改现有CLI配置，不启用自动更新或agent setup，不安装额外浏览器/框架/Stripe SDK。宿主不匹配或现有浏览器能力不足即INPUT_LIMIT。
6. 仅Python标准库、已有项目依赖、已有浏览器工具及指定CLI；Python/API版本及来源见SOURCE_LOCK.json。沙箱密钥、webhook签名秘密及原始证据保存在仓库外专用私有目录，用独立CLI配置和浏览器上下文。

## Journey contract / 四个功能旅程

所有旅程为同一合成USD1.00/数量1的数字资源；固定内容及摘要在首次付款前封存。各业务操作有独立mandate/order/request/idempotency身份，重试不得换业务操作或金额。金额只表示测试账面值。

| ID | 可观察过程 | 必须结果 |
| --- | --- | --- |
| N01 | 订单与批准→本仓闸门→真实托管结账→测试付款→事件及查询→交付 | 1会话、1成功付款/收款、1次成功交付，客户端实收内容摘要相符 |
| C01 | 同样创建结账会话，买家在付款前取消并由我方expire会话 | 1会话、0成功付款/收款、0交付；查询确认未付且会话expired。允许平台生成未付/取消的PaymentIntent，不能把付款对象存在当已收款 |
| R01 | 外部付款后，丢弃我方返回路径并暂缓我方事件消费；产品先记录UNKNOWN，再查询原会话/付款恢复 | 仍为原1会话/1成功付款、无新付款提交；持久关联跨一次我方进程重启保持，最终1次交付 |
| D01 | 外部付款已确认，我方首次交付故意失败，再恢复交付；重复消费同一已验证事件 | 仍1会话/1成功付款；先交付失败，后唯一成功收据和正确内容；重复事件不再付款或重复交付 |

R01只在我方受控回调/事件队列制造丢失和暂缓，不攻击Stripe或修改其支付响应；审计采集器已经取得的真实结果不得提前灌入产品输入。D01明确模拟交付失败，不能谎称Stripe导致该故障。取消与恢复是功能验证，不是重启六类攻击扩展。

官方组件参考使用相同原始对象与版本：分别记录Stripe原生幂等、付款与通知行为，以及本仓绑定/恢复的消费结果。不存在未经治理的对照付款。首轮 `security_control_increment=NOT_MEASURED`，不将原生机制或简单前后数量差当成本仓新增防攻击效果。

## Interface and implementation seam / 接口与实现接缝

- 复用 `models.py` 的IntentMandate、Order、TransactionRequest、PaymentExecutionRecord、PaymentStatusObservation和FulfillmentRecord；金额采用Decimal/整数最小单位，禁止浮点换算。
- 本仓实际闸门是 `payment_execution.execute_with_payment_binding_gate` / `observe_payment_execution_gate`，不是只分类已有事实的 `verify_governed_payment_action`。保存真实回调执行点记录，callback_result_ref只返回本地引用或会话ID，不返回结账URL或密钥。
- 批准的订单/金额/币种/商户上下文/资源摘要必须在创建会话前核对；浏览器点击付款前重新查询会话并再次核对。非ALLOW或证据不足时不得创建会话、交给浏览器或点击付款。
- 初次本地payment_id在创建会话前确定；服务方原始引用在会话创建后绑定为唯一cs_test会话。付款对象/收款对象在外部产生后关联，不把未知的payment_intent补造出来。恢复以持久的业务操作→会话关联为入口。
- 调用已有 `validator.validate_request` 产生付款前判断、`payment_recovery.assess_payment_recovery` 消费原付款查询，再调用生命周期判断，不改其规则。P3身份provider与Stripe收款商户上下文分别处理，不能互相冒充。若已有结果自带simulation_only等限制，保留原限制并另附来源说明，不篡改为生产证明。
- 只做一个SKU和一个薄商户页，复用本仓业务对象；不引入商品检索、库存系统或新的商城运行时。交付状态持久保存，恢复与重复事件不得仅依赖内存集合。
- 不修改既有authoritative_trace封闭注册表或伪装WebShop profile。任务证据包序列化既有事实与外部引用，明确新Stripe证据尚未获得通用Consumer/Player适配证明；不重开D阶段。

## External calls and data boundary / 外部调用与数据边界

外部可控服务端请求白名单：

- GET官方GitHub v1.55.10发行包/校验资料，重定向只允许已核官方release资产域；完整临时签名下载URL不写报告。
- POST `https://ai.stripe.com/keys/challenge`、`/keys/provision`，仅一次资格创建流程。
- `https://api.stripe.com`：GET `/v1/account`；POST `/v1/checkout/sessions`；GET `/v1/checkout/sessions`、`/v1/checkout/sessions/{id}`及`/{id}/line_items`；POST取消会话的`/{id}/expire`；GET `/v1/payment_intents`、`/v1/payment_intents/{id}`、`/v1/charges`、`/v1/charges/{id}`和`/v1/events/{id}`。只查询本隔离环境/本run的已知对象或有界清点。禁止直接POST payment_intents/confirm替代托管结账。
- 官方CLI本地事件监听所需test-mode握手/流连接；只接收checkout.session.completed、checkout.session.expired、payment_intent.succeeded，转发到 `http://127.0.0.1:8768/stripe/webhook`。不得加--live、--skip-verify或创建公网webhook。
- 浏览器主导航限Stripe创建接口实际返回、经校验的 `https://checkout.stripe.com` 官方托管会话URL和本地 `http://127.0.0.1:8768`；官方页面子资源按当前浏览器工具处理，不能把任意跳转当许可，出现非Stripe支付/登录目的页停止。

服务端API固定版本为 `2026-10-28.endive`；如服务不支持，不换版本凑通过。事件版本以原始通知记录并核兼容，不使用--latest静默漂移。

测试卡和账单数据仅用官方合成测试值，运行时载入，不使用真实卡、真实姓名、真实地址、用户钱包或已有浏览器cookie。原始创建输出、结账URL、密钥、签名秘密、client_secret、原始通知与完整HTTP响应不进入仓库或公开工具输出。仓库内RESULT只保留去敏引用与摘要；私有原始材料供独立复核，不因脱敏丢弃。

## Acceptance criteria

### AC-01 — 资格、来源与隔离

来源/版本/发行包摘要真实，只有一个隔离测试商户；实际所有会话/付款/收款均livemode=false。匿名创建及浏览器资格有成功或失败证据；仅说明可创建未付会话不算完整旅程通过。配置/凭据隔离，禁止读取已有正式配置。Mandatory: yes。

### AC-02 — 实际执行前治理与交易绑定

每次创建会话、交给浏览器及付款点击前均可回指本仓批准和实际闸门；金额100最小单位、usd、商户上下文、订单版本与资源一致。局部不允许/错绑守护例证明实际回调数0；运行事件按时间有序，不能事后补造ALLOW。L3还须审阅调用接线，不能只验RESULT中的布尔值。Mandatory: yes。

### AC-03 — 正常与取消链

N01和C01按表取得实际托管页面过程、独立会话查询与付款/收款对象；N01交付正确，C01未付且未交付。不得以本地SUCCESS、成功页或checkout.session.completed单一事件代替paid/intent/charge状态核验。Mandatory: yes。

### AC-04 — 未知付款恢复及无第二笔

R01保存初始UNKNOWN、一次本地重启和后续原会话查询；调用已有恢复逻辑，恢复不重新提交付款、不新建会话。所有原始清点列表has_more=false，限定隔离账户、运行时间窗口、业务操作集合；不能仅凭查询同一对象或余额断言没有第二笔。Mandatory: yes。

### AC-05 — 交付失败恢复及去重

D01先失败后成功，N01/R01/D01各只有一次成功交付和一个对应内容摘要；C01没有交付。重复同一已验证事件与交付恢复复用原付款；支付、订单、交付、任务完成分别记账。Mandatory: yes。

### AC-06 — 真实通知与状态可信性

至少N01及D01有本次实际付款产生的CLI转发通知；保留原始字节、Stripe-Signature和接收时间，在配置的测试签名秘密下验证。篡改、错秘密和过期时间负例拒收；历史L3按原接收时间复核，不伪装为新鲜通知。独立再查实际会话/付款/收款；配置秘密验签不代表真实主体或独立签名信任源。Mandatory: yes。

### AC-07 — 可复算的分层证据

四例的批准、闸门、业务订单、外部会话/付款/收款、通知/查询、交付/恢复能逐引用关联；公开摘要与私有原始材料摘要一致，审计可复算。Evaluator用单独只读额度重新查询，不仅信Executor归档；无法取得独立材料即不可PASS。Mandatory: yes。

### AC-08 — 有界执行与数据安全

所有可控API调用、失败/重试、浏览器操作、CLI/服务起止、下载和L2均事前预留、追加记录；预算口径不能从累计次数改成不同对象数。秘密不落公开记录；清理仅停止本任务进程，不删除外部记录或扩大权限。Mandatory: yes。

### AC-09 — 历史保持、回归及贡献边界

INPUTS中的保护文件和全部历史任务不变，新增代码仅在允许文件；指定61项历史回归保持，新增接缝守护测试通过。before=0条已核Stripe旅程，after按实际合格条数记；官方保护、真实资金、身份、客户价值和合规不计为新增成绩。Mandatory: yes。

## Allowed scope / 允许范围

Executor仅允许新增：

- `src/agentic_payment_experiment/adapters/stripe_checkout.py`
- `src/agentic_payment_experiment/stripe_checkout_lab.py`
- `tests/test_stripe_checkout_adapter.py`、`tests/test_stripe_checkout_lab.py`
- `scripts/validation/stripe_checkout_lab.py`
- 本任务 `RUN.py`、`RESULT.json`、`REPORT.md`、`ATTEMPT_LEDGER.jsonl`、`derived/`、`versions/`、`evidence/`。必须保留失败与旧版本。
- CURRENT仅在正式冻结后改本任务EXECUTING/阶段字段；不能改权限、合同、CHECK、SPEC、SOURCE_LOCK、INPUTS或计划。

不改现有models、规则、闸门、恢复、trace注册表、pyproject、旧tests或上游。若现有接缝无法满足合同，停止交回Evaluator，不通过放宽规则解决。

## Exclusions / 明确排除

禁止修改既有models、支付闸门、恢复规则、trace注册表、pyproject或旧tests；不引入通用商城、钱包或新的跨项目框架。禁止生产/真实资金、真实个人资料、正式账户登录/认领、充值、退款、争议、转账、直接PaymentIntent确认代替托管结账、外部反自动化绕过与未授权提交推送。以上是已冻结原范围的显式归类，未放宽或扩大任何权限。

## Validation plan / 验证计划

正式L2/L3使用公共run_validation.py与本包VALIDATION_PLAN.yaml；所有现场付款在L2前按RUN阶段完成并保留原始材料，L2/L3不重跑付款。VP-04使用冻结的只读复核器独立查询，Executor/Evaluator额度分开。VP-03/05不调用外部服务。制包阶段仅运行CHECK package/selftest及61项历史基线，不冒充正式L2/L3。

L3除重跑门禁，还审查实际副作用接线、外部来源、故障注入位置、账户/时间/业务操作清点及原始通知，逐AC给出判定。严格路径保护只针对本包记录的新基线，不在新CURRENT下重跑旧H任务全工作区checker。

## Budget and stop conditions / 预算与停止条件

SPEC.json为机器可读上限：480主动分钟、24小时墙钟；实现2尝试、L2两次、L3一次；匿名创建1次、会话最多4、付款点击最多3、成功测试付款最多3笔/累计USD3.00；服务端可控业务API最多120次（现场80、Executor只读20、Evaluator只读20）；每个POST至多一个逻辑写入，同键重试最多1次且计预算，未知付款禁止新提交；浏览器操作80、下载3请求/64MiB。

CLI流连接及Stripe页面自主子资源不是“本方服务端API请求”，必须单独记录会话/时长/可观察请求数；无法完整观察时明确UNKNOWN，不宣称全网络次数精确或零网络。不得把浏览器未计流量混进API额度后临时改口径。

遇真实模式/非指定账户、非测试数据、无前置治理的副作用、第二笔同业务付款、秘密泄漏、来源造假、权限/验证码限制、预算不足或接口版本漂移立即停止；先保留失败，不通过扩大权限/换账号/换协议解决。资格不成立记INPUT_LIMIT/INCONCLUSIVE，不能把静态检查通过当替代成功。

## Authorization / 当前授权

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: true

精确批准范围见AUTHORIZATION_REQUEST.md与AUTHORIZATION.json，2026-11-12T00:52:09Z一次授权。开始运行前必须通过冻结摘要检查并记入追加账本；遇资格/浏览器限制严格停机。无需重新询问平台选择。

## Project impact and continuation / 项目收益与下一步

通过时可增加外部Stripe测试链适用性证据；安全控制增量仍单列NOT_MEASURED。若四例均闭合且无新共同断点，STOP该首轮，不继续堆同类Case。若出现重复共同断点，再冻结针对该断点的最小修复；若资格受限，保留失败后比较现成正式测试沙箱或其它候选，不能自动切换。独立商户、真实主体、生产支付、完整库存/退款/争议和商业采用均为后续独立条件，不自动续包。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/07/08/09/11/12/18/20；适用性=CORE/ADAPTER/EVIDENCE_ONLY的单接缝；before=无本包外部运行证据，after按实际Test/Evidence判定；不提升全部族成熟度。真实强认证、密钥治理、签名信任源、资金安全和合规unknown。
