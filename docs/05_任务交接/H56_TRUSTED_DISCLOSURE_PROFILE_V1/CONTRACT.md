# H56 授权位置必须查齐的有界消费规则

Task ID: H56_TRUSTED_DISCLOSURE_PROFILE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H56_TRUSTED_DISCLOSURE_PROFILE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r92
Active bottleneck: B-17
Hypothesis: H-56
Metric baseline: H55固定L2/L3各6/6、12观察一致；独立准备同一旧消费者在根cnf和结账载荷cnf两位置均有“完整时DENY、隐藏后VERIFIED”的真实签名反例（2/2误消费）；14目标配置样本中旧实现5符合、9不符合，后者含新定义的配置/兼容规则，不全是旧合同缺陷。
Estimated affected scope: 一个任务内标准授权消费者、两个已测安全条件隐藏位置；原39回归+14配置场景=53。实际用户/损失率/客户价值unknown。
Expected project impact: 把这两个位置的隐藏条件从误VERIFIED降为DENY，同时维持指定可选区隐私与合法标准事实；只证明任务内有界消费配置，不升级完整协议/生产身份/付款。
Rollback condition: 隐藏安全条件仍误放行、为配置误拒指定隐私正例、原护栏回归、需改SDK/商家/核心或超边界则不接受新配置，保留旧成果和失败并STOP/SWITCH。

项目最终证明高风险支付授权、执行、恢复、审计可靠。A–D已关闭、E仅本地、F当前。H55已完成披露差异测量并STOP重复样本；H54R只接受已披露根条件修复，父H54仍拒收。B-17最前缺口是“验签后返回的数据是否足够完整”，先补这一条规则，优于重复测量、接HTTP/支付或Provider（支付服务方）。支付宝/比赛延期不变。

## Principal change / 唯一主要变更

仅在新任务consumer.py加一条**受信任配置控制的披露完整性门槛**：官方签名/时效验证通过后，授权相关位置里的每个摘要承诺都必须被实际披露并解析；明确划出的可选资料区可以保留隐藏内容。未拿齐条件就DENY，不把缺省当不存在。H56不改SDK、原商家、支付/数据库/HTTP或全协议，也不增加“签一个材料齐全标签”后盲信它的机制。

## Selected mechanism / 机制选择与代价

H55的EXPLICIT_SIGNED_PROFILE=ABSORB仅可支持“需要明确可信消费配置”的方向，尚不能证明必须新加一个被签名声明。Evaluator将其收窄为已有请求外信任根+固定规则、签名已承诺结构的解析，不引入新签名协议：

| 机制 | 裁决与范围 |
|---|---|
| 保持旧消费者 | REJECT用于后续执行；两位置藏条件仍VERIFIED |
| 所有位置都强制全披露 | REJECT作为普适规则；会破坏指定可选隐私区，也不能宣称符合所有SD-JWT隐私语义 |
| 外部可信固定配置+授权位置摘要闭合 | ABSORB任务内单变量实验；可用现成官方SDK/JWS/摘要解析，无新库 |
| 新的被签名profile声明/发行清单/多issuer治理 | REFERENCE_ONLY；增加协议义务，当前不是最小必要机制 |

明确兼容代价：旧根optional_note未提供披露时，本配置拒绝（P06）；只有明确可见、被签名绑定的根optional_data对象允许隐藏子资料（P08）。不是声称能从摘要猜字段名，也不是声称新optional_data为AP2/UCP官方标准。该命名和含义只属于任务内发行/消费约定；现实发行方是否采用、如何迁移仍unknown。

## Frozen trust and format contract / 冻结信任与格式

1. **请求外配置**：trust.disclosure_profile必须为dict，id=h56-nondelegating-checkout-complete-v1、protocol_version=2026-08-25、platform_kid必须等于本次已验证平台JWT头kid并命中已有请求外platform_profile.keys。配置与原trust.protocol_version一致；只认固定id，不接受请求内声明、任意“豁免路径”或未知配置。原公钥/算法/确认责任不变，不构成真实身份或生产密钥治理。
2. **先验签再解释**：继续对同一精确token/同一外部公钥执行官方单凭据、严格时效和完整已披露根验证。只有这些成功后，才可使用被该签名认证的原JWT载荷、披露数组和摘要图检查完整性；原始解析不能代替验签。SHA-256为唯一支持的披露哈希，根_sd_alg缺省或sha-256可用，其他形态unsupported_profile。
3. **摘要图而非字段黑名单**：支持固定SDK原生对象_sd摘要数组、数组元素{"...": digest}及它们解析后对象里的嵌套摘要。每个授权相关摘要必须精确匹配本次实际提供的原始披露串的SHA-256，再按标准对象/数组位置解析和继续检查；不能对未提供的摘要猜字段名，不能仅在SDK已抹掉_sd的返回对象中找缺字段。非法/不支持结构拒绝，不跳过。原严格JSON/Unicode/有限数/重复键及SDK披露校验保持。
4. **默认授权相关**：根、delegate_payload及其所有嵌套字段（包括未来未知字段）默认要求摘要闭合。可见或正确解析的cnf仍由原根/条目非委托检查拒绝，不能因为“已经披露”就授权。未知未解析摘要和security decoy（授权位置的诱饵摘要）一律拒绝；这是保守配置代价，不声称知道诱饵里是哪条限制。
5. **唯一可选区**：根路径optional_data必须是已认证且可见的对象；本配置明确不从它提取授权、金额、有效期、商家/用户身份、委托、版本或执行事实。仅其内部未知/未提供披露可以保留；容器本身若藏在尚未解析的根摘要中，仍拒绝（P13）。名字相似、根以外同名字段、请求声明的豁免区都不能得到此例外。可选区不是权限来源，任何资料不能从这里提升为授权事实。
6. **原对象保持**：标准ap2.checkout_mandate、真实签名vct/iat/exp、完整商家JCS/checkout_hash/当前session、协议协商信任配置、无KB/多跳、失败不返回授权事实全部继承H54R/H54有界合同。不新增钱包/支付授权，不修改业务投影或原始token。三个既有协议WATCH（root typ/空checkout/旧签名版本）不在本包偷加全面schema要求；本profile的版本绑定是消费规则配置，不是完整协议互通认证。

完整披露的未知字段可以保留，不代表本配置理解或执行了任意新授权条件；本实验只证明隐藏已知条件的误消费被堵住和指定结构的披露完整性。未来消费者若依赖未知条件作授权，必须另冻其解释责任，不能据本配置直接付款。

## Allowed scope / 允许范围与来源

Executor仅可修改本任务consumer.py，填写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json及evidence/。所有旧任务/父拒收和接受证据、SDK/商家/src/tests、来源、夹具、检查器、合同、计划、BASELINE只读。当前consumer.py逐字节复制已接受H54R，尚未实现完整性规则；sources/H54R_consumer.py为不可变同基线对照。

SOURCE_COPY记录30份复制。RUNTIME仅scratch变.task_envs/H56/runs；FIXTURES.context只加请求外固定profile（kid按每次预置签发key绑定），原36及根3输入签名/攻击/预期语义保持，未把字段写到请求。新增14真实签名材料由PROFILE_CASES构造，官方SDK可同时验证部分/完整呈现及已知条件差异。准备对照14次计入H55 Evaluator预算（12+14=26/48），没有调用H56可变候选，没有新规则成绩；BASELINE_OBSERVATIONS原始数据在evidence及冻结sources各保留一份。

仅允许原JSON/摘要/编码/正则/typing/copy/rfc8785/jwcrypto/AP2/pydantic导入；无文件/进程/网络I/O、动态导入或读fixture/预期/case ID。保留接口consume(request_json,session_json,trust,now)，成功仍VERIFIED并完整返回原结账/签名/摘要/kid/版本，失败无checkout/checkout_jwt/checkout_hash。配置/完整性不支持用unsupported_profile或原类型化DENY，不新增付款ALLOW。

环境复用H47 Windows Python3.12、H37纯Python模块、AP2 b4587ac1d055888a73b4b21750973cffba961793、cryptography46.0.7/pydantic2.13.4/jwcrypto1.5.6/sd-jwt0.10.4/ucp-sdk0.4.6/PyYAML6.0.3及固定rfc8785 0.1.4/Node24.12.0独立JCS判据。没有新下载、安装、真实密钥或发行方联系；合成私钥仅内存。

## Acceptance criteria / 验收标准

### AC-01 — 单模块与来源保护

Given固定HEAD/环境/任务副本/可信配置；When VP-01/02/10；Must observe只consumer.py实现变化，冻结/来源/既有成果hash不变，无安装；Must not observe改SDK/商家/核心/旧任务、请求自信任或测试硬编码；Evidence=SOURCE_COPY/BASELINE/EV及源码复核。Mandatory: yes。

### AC-02 — 授权完整性与配置绑定

Given P01–P14实际签名/披露/公钥/SDK部分和完整结果；When VP-06/07；Must observe隐藏根cnf和隐藏载荷cnf均DENY，P09/10/11缺配置/请求自声明/错误kid拒绝，P12嵌套未知条件/P13容器本身隐藏/P14授权诱饵摘要拒绝；Must not observe仅信SDK返回对象、只按cnf名匹配或把未知摘要当无条件；Evidence=14原始材料、完整/部分SDK结果、同一issuer JWT与独立L3。Mandatory: yes。

### AC-03 — 合法数据、隐私与原39保持

Given P05根未知字段完整/P07可选区完整/P08仅可选区内部隐藏，及原36+根3；When VP-03..07；Must observe三个配置正例VERIFIED、完整原结账/签名/摘要不丢，原39保持，JCS gold保持；P06旧根可选字段隐藏明确拒绝并记录兼容代价；Must not observe所有未披露字段一刀切，或悄悄放宽授权位置来保隐私；Evidence=53场景、独立JCS/SDK/JWS复算。Mandatory: yes。

### AC-04 — 回归、成本与真实交付

Given240主动分钟/2L2/424case；When全部10项；Must observe25项AP2回归、原/根检查器及旧对照9目标失败可判别，所有预留/失败/原始三件套保留，完整L2后整包提交；Must not observe任务自授PASS或夸大真实身份/标准/支付能力；Evidence=REPORT/RESULT/账本/L2及独立L3。Mandatory: yes。

## Validation plan / 验证计划与预算

VP-01保护/环境；02候选范围；03完整JCS；04原36；05根3；06配置14；07三类原始观察/SDK/预算；08固定25回归；09判别器自测；10复查保护。共53场景，10项已冻结。新候选未有场景成绩或L2，准备只确认旧对照和判别器。

Executor<=240主动分钟/2正式L2/424总case，分账原36<=288、根3<=24、配置14<=112；Evaluator另<=159（108+9+42）。所有候选调用只经FROZEN_TESTS.py --role executor [--case CASE_ID]、ROOT_CASES.py --role executor、PROFILE_CASES.py --role executor；各自先追加ATTEMPTS/ROOT_ATTEMPTS/PROFILE_ATTEMPTS.jsonl预留，导入/构造/断言失败仍计数。每批新目录/输入先落盘/输出失败留存，LATEST仅指针。max_parallelism=1，代理0，不存在不记账直接调用候选。

正式L2前ATTEMPT_LEDGER预记formal_l2_attempts（等于保留的l2_executor_01/_02目录数）、active_work_minutes、artifact_cases_reserved（等于三账本预留总和）；network_calls/asgi_requests/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations/payment_calls/orders_created全0。失败不得删目录/改断言清零；首轮失败仅合同内有具体修复时可用第二轮。

REPORT真实生成，含Task ID/Task kind/Baseline HEAD、逐AC、全部EV、Impact comparison（影响对比）、成本/失败、P06/P14兼容代价与非标准可选区义务、PCAC影响。RESULT schema=h56-result/v1、task_id本任务、classification=LOCAL_TRUSTED_DISCLOSURE_PROFILE_OBSERVED、profile_scope=TASK_LOCAL_NON_STANDARD_POLICY、customer_demand=UNKNOWN、remaining_gaps非空；production_ready/full_ucp_conformance/real_actor_authentication/psp_verified/payment_execution_integrated/http_integrated/cross_system_revocation/customer_value_proven全false。只有实际通过后才填能力结果；首轮未完成就保留真实失败，不造成功值。

完整L2通过才SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor，next_artifact=REPORT；Evaluator接受未变快照后一次集中L3及独立泛化，再裁决。原H55为24/72调用、L2 1/2，自报18分钟；H55 Evaluator26/48；旧账本不重置、不自动H57。

## Stop conditions / 停止与继续条件

需改第二实现、SDK/商家/核心、引入新声明/发行网络、任意豁免路径/新增配置字段、冻结AC/夹具/计划、依赖/预算/授权即停回Evaluator。保护漂移、秘密落盘、预算耗尽或同一失败无新机制也停，保留失败，不以研究为由跑外网。

两位置隐藏条件拒绝、指定隐私/原39保持且独立无合同反例，才可接受本地有界配置改善并STOP该配置切片；随后重新评估剩余协议语义/可信发行责任和同事务执行接缝，不能自动把VERIFIED接付款。若必须依赖任意发行方自声明、牺牲合同内隐私例外或全面迁移则STOP/SWITCH，不能把测试全绿当闭环。

## Exclusions and authorization / 排除与授权

零外网/DNS/监听/HTTP/ASGI/模型/Provider/钱包/测试网/真实或沙箱付款/真实密钥读取/安装/对外联系/Git写操作。无通用运行时/区块链/新商家。协议WATCH、真实身份/用户确认、PSP/生产密钥治理/跨系统撤销/部署/客户unknown保持。

## External requirement impact

已检查PCAC开发指标映射。profile=PCAC-AGENTPAY；PCAC-07/09=CORE，before=披露完整性已测但无门槛，after_target=仅任务内固定消费配置可实现/独立验证；PCAC-15=CORE/ADAPTER，指定可选资料区允许隐藏，P06/P14兼容代价必须披露，不声称现实隐私合规；PCAC-12/20=CORE/EVIDENCE_ONLY，Test=53场景/原始承诺与披露/10计划/L2/L3；PCAC-08仅合成平台来源，10/18撤销应急不变。无监管/生产结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
