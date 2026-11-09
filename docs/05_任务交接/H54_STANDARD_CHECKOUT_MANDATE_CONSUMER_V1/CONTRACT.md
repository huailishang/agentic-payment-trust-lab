# H54 标准结账授权的最小可信消费者

Task ID: H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r89
Active bottleneck: B-17
Hypothesis: H-54
Metric baseline: 标准消费入口ABSENT；H53R是已接受的本地支付两跳消费者，不接本包标准请求。准备仅证明单CheckoutMandate签发/官方SDK验签与独立JCS材料可运行，尚无H54消费者或正负例成绩，禁止填造before拒绝率。
Estimated affected scope: 仅1个离线标准结账授权验证入口，36个固定合成场景；真实流量/事故率/客户收益unknown。
Expected project impact: 若独立L3通过，标准凭据→完整商家签名→当前结账事实从ABSENT变成BOUNDED_EXECUTABLE_CONSUMER；不把付款或生产接入记为改善。
Rollback condition: 误验签、错误放行、字段丢失、保护漂移、回归失败或无法在单模块内实现则不接纳候选，保留失败证据并STOP；原H53R等接受成果不改。

最终目标是高风险支付授权、绑定、执行、恢复、审计能独立复核。全局A–D关闭，E仅本地代表性闭环，F当前。H53R已PASS并STOP本地消费/终结链修复，父H53仍REJECTED。B-17最前剩余断口是自定义研究信封不能证明标准CheckoutMandate可忠实消费。给同一信封继续加HTTP/锁样本收益低；先接新Provider（支付服务方）又同时引入凭证、网络和资金责任。支付宝/比赛继续Human延期，商业需求未知不阻止本轮离线技术检验。

本轮只建设**标准授权材料的商家侧验证消费者**，不建设付款执行入口。完成后还要由Evaluator比较“标准事实与已接受执行控制同事务绑定”的下一切片是否值得冻结，之后才是获授权的HTTP/部署/现实主体/Provider；不自动顺序派发。

## Frozen mechanism / 冻结机制及来源

准备依据是H52已固定的2026-08-25 UCP/AP2扩展（其SOURCE_MANIFEST及原文受BASELINE保护）、AP2 v0.2.0 commit b4587ac1d055888a73b4b21750973cffba961793和Google官方教程相同单凭据路径。固定**Trusted Platform Provider（可信平台签发方）**分支：商家签完整checkout，平台在独立确定性合成确认后签CheckoutMandate，商家信任请求外配置的平台签名。请求标准位置是ap2.checkout_mandate，支付凭据另在payment.instruments[*].credential.token，本包仅保留后者为不读取、不验证、不使用的opaque（不透明）数据。

比较与分类：

| 机制 | 分类 | 采用范围与取舍 |
|---|---|---|
| 原H53R自定义支付信封保持不动 | REFERENCE_ONLY | 保留执行/恢复能力作后续接缝参考；不能改名CheckoutMandate或冒充本包before负例 |
| 固定AP2官方单CheckoutMandate + UCP detached JWS（分离载荷签名） | ABSORB | 复用真正SDK签名/披露/时效验证及官方字段；只写一个任务模块消费，不复制整个商家 |
| Trail of Bits rfc8785 0.1.4，commit f7e05bfc4ccaee27d9e18f8ef1c27cbe03cb3638 | ABSORB | Apache-2.0、无运行依赖，原样任务内固定；完整序列化机制，不是sort_keys替身；不pip安装，不回抽核心 |
| RFC8785与作者参考仓32a48195b9b20fe67b1795e39e4509f14d860b45的6对向量/Node实现 | ABSORB | 独立固定gold（预期字节）与不同语言引擎；作者Python实现不再复制，避免与候选相关的唯一判据 |
| 教程排序JSON、项目NFC规范化、钱包/多跳/全面协议迁移 | REJECT / REFERENCE_ONLY | 不能替代JCS；后几项增加信任/接口义务，本轮不进入实现 |

19份公开源已由GitHub connector（连接器）按commit读取，逐字节Git blob SHA及SHA256核验，许可/版权和URL保留于SOURCE_BUNDLE、SOURCE_MANIFEST、sources/；准备读取公开资料不等于执行期外部API授权。两份Python模块仅使用math/re/typing/io，Node参考仅字符串序列化，无网络/进程/文件副作用；已检查原文后才做准备运行。两套完整Apache许可正文/版权声明随源保留。

JCS按RFC8785保留Unicode而不NFC归一化，UTF-16属性排序、数组顺序、ECMAScript数字/转义；采用库的安全整数限制abs(integer)<=2**53-1、有限IEEE754浮点、合法Unicode、字符串键、无重复成员。该整数限制比RFC可表示数字域保守，超域明确拒绝，不宣称全域协议符合性。6对作者向量+10条RFC Appendix B字面预期+Node跨语言Unicode/数字对照+7非法域检查已在准备通过；不是H54候选测试成绩。

## Representation and trust / 对象与信任边界

冻结兼容配置名：H54_UCP_20260825_AP2_V02_PLATFORM_ES256_SINGLE。不是完整2026-08-25商家迁移或全AP2认证。

1. **原生对象**：AP2 CheckoutMandate直接有效载荷必须实际签有vct=mandate.checkout.1、checkout_jwt、checkout_hash、iat、exp；不能用generated model（生成模型）默认值补出未签vct，不能递归找同名嵌套字段。SDK有效单凭据验签须用请求外JWK和current_time=now、clock_skew_seconds=0。原始解析只用于严格格式拒绝，可信事实只能来自官方验证结果。
2. **完整原文**：checkout_jwt为商家compact JWS（紧凑签名串），payload为完整checkout去掉整个ap2后的JCS字节；checkout_hash=base64url(SHA256(checkout_jwt ASCII))。验签覆盖protected header（受保护头）与payload，不能只验解码后小投影。保留所有未知业务字段、ucp命名空间字段与数组顺序；JWS载荷必须等于独立完整JCS，不能用typed Checkout模型过滤后验签。
3. **ap2可重构边界**：旧SDK CheckoutMandate只承载checkout_jwt/hash，而固定UCP原文要求完整checkout含merchant_authorization。采用官方教程的compact重构路径：从compact的header/signature恢复ap2.merchant_authorization，并与可信当前session该签名核对；**本配置只支持ap2={merchant_authorization}**。遇额外ap2成员必须unsupported_profile，不准静默丢弃或声称完整扩展兼容。非ap2未知字段一律完整保留。
4. **平台分支**：只接受单个平台签发SD-JWT，无继续委托cnf、无附加KB JWT、无~~多跳；这些是明确未支持分支，拒绝，不关闭SDK校验以绕过。平台与商家仅ES256/P-256、公钥来自外部预置profile顶层keys[]，kid须明确命中。不得信任请求携带jwk/jku/x5u/x5c、平台自声明、consent=true或错误算法；无可信配置拒绝。不是钱包holder（持有者）认证、PKI、现实身份、生产密钥治理或跨系统撤销。
5. **协商和状态**：ap2_required=True及protocol_version=2026-08-25由请求外商家session/trust配置固定。消费方法不实现发现网络或完整协商引擎；已锁定后缺ap2.checkout_mandate拒绝，客户端删能力/称无需AP2不得降级；其他配置unsupported_profile。完整当前session（去ap2）必须与已签完整payload的JCS一致，包含id/币种/金额/商品/未知字段；不能只核对hash或使用陈旧投影。当前session必须有merchant_authorization，额外ap2拒绝。
6. **明确责任**：平台夹具只在独立合成receipt批准且绑定checkout_hash后签发，未批准不出凭据；商家信任平台签名意味着用户同意，而非再从请求造一份确认。合成receipt不代表真人确认。支付授权由PSP验证，本包不产生PaymentMandate、不付款、不下单，也不声称仅CheckoutMandate可支付。

## Allowed scope / 允许改动范围

Executor仅新建一个实现文件consumer.py，填写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json和evidence/。所有合同、计划、夹具、gold、检查器、公开源、BASELINE及旧任务、src/tests、SDK、商家实现只读。只允许import JSON/摘要/编码/正则/typing/copy、固定rfc8785、jwcrypto、AP2、pydantic；无文件/进程/网络I/O或动态导入。候选不得读取case ID/预期/夹具、按固定签名/公钥值硬编码；必须使用真实官方验证。

唯一接口：consume(request_json: bytes, session_json: bytes, trust: dict, now: int) -> dict，同步、纯验证，不修改输入。JSON与各JWT/SD-JWT disclosure（披露）中相关JSON均须拒绝重复成员、非法Unicode和非有限数；不能让普通json.loads覆盖重复键后补验。请求与session的原字节摘要用于证据，不作为跨系统签名算法。

- 成功status=VERIFIED，必须返回完整checkout（含恢复的ap2.merchant_authorization）、checkout_jwt、checkout_hash、mandate_sha256、request_sha256、session_sha256、platform_kid、merchant_kid、protocol_version。签名和原token字节不能规范化重签；不输出付款ALLOW。
- 失败status=DENY，code为mandate_required / agent_missing_key / mandate_invalid_signature / mandate_expired / mandate_scope_mismatch / merchant_authorization_invalid / merchant_authorization_missing / unsupported_profile / invalid_input之一；不返回checkout/checkout_jwt/checkout_hash等可误用的已授权事实。错误类别必须与失败原因相称，不能吞掉内部错误后伪称成功。
- 不支持形状可使用unsupported_profile；不是扩大协议定义。非法密码学输入不得抛未分类异常越过消费者边界。

现成Windows H47 Python3.12、H37已固定纯Python依赖；cryptography46.0.7/pydantic2.13.4/jwcrypto1.5.6/sd-jwt0.10.4/ucp-sdk0.4.6/PyYAML6.0.3。Node24.12.0仅独立oracle（判据），冻结本机二进制摘要；不是候选依赖。SDK合成日志只到.task_envs/H54/runs，签名私钥只存内存、不落盘；公开材料不含真实支付/个人数据。既有未提交改动全部保持，不提交或推送。

## Acceptance criteria / 验收标准

### AC-01 — 单模块与来源保护

Given固定HEAD/地图r89/环境/19源；When VP-01/02/08；Must observe冻结文件及继承保护摘要一致、只新增consumer.py与指定交付、零安装、依赖无漂移；Must not observe改SDK/商家/核心/旧任务/检查器或请求自信任；Evidence=BASELINE/SOURCE_MANIFEST/EV与源码复核。Mandatory: yes。

### AC-02 — 完整JCS机制及独立判据

Given固定作者gold及RFC字面向量；When VP-03；Must observe6对预期字节、10条数字、跨语言UTF-16/Unicode/数组/转义/数字一致，7非法域拒绝；候选实际使用该固定完整机制覆盖完整签名与快照，不能自写排序替代；Evidence=独立gold/Node原文与EV；Must not observe只用同一实现自签自验证明符合性。Mandatory: yes。

### AC-03 — 合法标准材料可忠实消费

Given C01正常/C02重排空白重序列化/C03含新增未知字段的真正平台SD-JWT与商家JWS；When VP-04/05；Must observe3/3 VERIFIED、官方SDK与独立商家验签一致、完整字段/字节/hash/kid/版本证据齐全；Must not observe过滤未知字段、NFC替换或以拒绝全部规避风险；Evidence=逐例原始request/session/token/公钥/响应、独立复算。Mandatory: yes。

### AC-04 — 标准授权负向边界

Given C04–C36共33例，覆盖时效/来源、锁定后缺凭据/回退、金额/币种/商品/id/未知字段、merchant JWS/JCS/hash、vct缺失/错误、继续委托/多跳/附加KB、重复JSON/头、非法数/Unicode、额外ap2、请求自带平台根、未确认不签发；When VP-04/05；Must observe33/33 DENY且不返回已授权事实、不修改可信输入；Must not observe只凭SDK能解析就放行，或默认补vct；Evidence=FIXTURES固定家族、真实签名材料、原始错误/响应与L3。Mandatory: yes。

### AC-05 — 回归、预算及可复核交付

Given完整8项计划和预算；When VP-05/06/07/08；Must observe25项AP2相关回归保持、检查器拒绝4种破坏、失败/预留/原始EV不覆盖、完整L2后一次整包提交；Evidence=账本/REPORT/RESULT/L2、后续独立L3；Must not observe任务自授PASS、付款/订单/HTTP/生产能力虚报或将准备36形状当消费者已通过。Mandatory: yes。

## Validation plan / 验证计划与预算

VP-01保护/环境；02候选范围；03独立JCS；04完整36消费者场景；05原始材料和预算复算；06固定25项AP2回归；07检查器自测；08复查保护。命令已固定在VALIDATION_PLAN.yaml，不运行旧任务冻结计划，避免治理历史变化被误当旧实现回归。

Executor<=360主动分钟，最多2次正式L2，消费者case预留总<=288；Evaluator另<=144。候选所有调试/正式调用须经FROZEN_TESTS.py --role executor [--case CASE_ID]；自动在调用前向evidence/executor/ATTEMPTS.jsonl追加本批预留，失败/导入失败仍计数，单次完整36。每批新目录、输入先落盘、输出和断言失败都保留，不覆盖旧观察；LATEST只是指针。禁止绕过包装器额外无账本调用候选。序列化/回归/夹具准备不算消费者case，但主动耗时照计。max_parallelism=1，无代理/外部任务。

正式L2前在ATTEMPT_LEDGER.json预记formal_l2_attempts及累计active_work_minutes，分别写evidence/l2_executor_01、_02；不得删失败目录重置次数。中央Runner生成每项stdout/stderr/meta和L2-GATE；完整8/8通过才提交。若首轮失败且有合同内具体修复可用第二轮，不无限追加预算。

REPORT执行后生成，含Task ID/Task kind/Baseline HEAD、逐AC证据、Impact comparison（影响对比）、Preparation/Executor区分、成本/失败/边界、external_requirement_impact及SUBMITTED_FOR_REVIEW。RESULT schema=h54-result/v1、task_id=本任务；classification=BOUNDED_STANDARD_CHECKOUT_CONSUMER_OBSERVED仅完整场景通过后可写；before=ABSENT、after=BOUNDED_EXECUTABLE_CONSUMER（必须有实际证据），customer_demand=UNKNOWN、remaining_gaps为非空列表。必须把production_ready/full_ucp_conformance/real_actor_authentication/psp_verified/payment_execution_integrated/http_integrated/cross_system_revocation/customer_value_proven均标false。ATTEMPT_LEDGER至少记录formal_l2_attempts（等于保留的正式L2目录数）、active_work_minutes、artifact_cases_reserved（等于executor/ATTEMPTS.jsonl预留之和），以及network_calls/asgi_requests/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations/payment_calls/orders_created全部为0；Checker实际核对，不只报告自述。首轮失败时保留真实未完成RESULT，不得为门禁造成功值。

CURRENT只可CONTRACT_FROZEN→EXECUTING/Executor及execution_phase更新；任务/地图/权限与next_artifact=REPORT不变。提交时仍EXECUTING/Executor；Evaluator接受未变提交快照后才READY_FOR_REVIEW，再独立L3与保留的额外留出检查。REPORT/REVIEW不预建空文件，Executor不自行PASS或派H55。

## Stop conditions / 停止与继续条件

需要第二实现模块、商家/SDK/核心修改、付款/HTTP接线、下载/安装/网络/新权限、改变假设/AC/预算时立即停止，报最小精确原因交Evaluator；不得修改冻结向量让失败变绿。保护漂移、秘密落盘、预算耗尽、无新机制重复失败同样停止；失败材料完整保留。

固定正负例与独立留出均通过、无安全反例才可判任务PASS及有界标准消费IMPROVED，随后STOP本轮切片，Evaluator另评同事务执行接缝。若只是SDK可验签而完整条款/来源失败，REJECTED或INCONCLUSIVE，不加HTTP；若范围必须全面迁移则SWITCH/STOP。外部真实信任来源、现实主体/确认、完整协商/钱包/算法/扩展、PSP/部署/客户仍unknown。

## Exclusions and authorization / 明确排除与授权

执行期零外网/DNS/监听/HTTP/ASGI/模型/Provider/钱包/测试网/真实或沙箱付款/依赖安装/对外联系/Git写操作。不创建新商家或通用运行时，不接区块链。当前任务请求授权离线制定/派发及合同内实现，不授权运行历史支付宝任务。

## External requirement impact / 外部要求影响

已检查PCAC开发指标映射。profile=PCAC-AGENTPAY。

| PCAC | 适用性 | 本切片before→after_target | Test / Evidence / 残余 |
|---|---|---|---|
| 07 授权合同、09 完整性 | CORE | 标准消费M1→至多M4（需L3） | AC-03/04、签名/原始材料；完整支付授权不升级 |
| 08 支付意愿核验 | CORE / ADAPTER | 合成来源模型保持，生产成熟度不变 | C30/33、请求外平台根/合成receipt；真人意愿未证 |
| 12 证据链、20 上线前评估 | CORE / EVIDENCE_ONLY | 本切片M1→至多M4（需L3） | AC-01/05、EV/L2/L3；不构成上线批准 |
| 10 撤销、18 应急 | CORE / ADAPTER | 本轮不变 | 原接受控制只读，跨系统撤销/事故恢复未测 |

after_target不是已达成熟度，无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
