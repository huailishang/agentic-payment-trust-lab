# H54R 完整已验签根的非委托条件修复

Task ID: H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r90
Active bottleneck: B-17
Hypothesis: H-54R
Parent task: H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1
Failed criterion: AC-04

最终目标为高风险支付授权、绑定、执行、恢复及审计可靠可复核。A–D已关闭，E仅本地受控，F当前。H54虽固定L2/L3各8/8、36稳定观察一致，却被两个外层cnf反例证伪，最终REJECTED / INCONCLUSIVE。B-17第一瓶颈收窄到标准授权消费者遗漏完整根约束；优先于把未接受事实接入claim（执行占用）、扩HTTP或接Provider（支付服务方）。H53R已接受/STOP、本地执行能力及父H53拒收不变；支付宝/比赛继续Human延期。

## Measured failure / 已测失败及唯一目标

父REVIEW、evidence/review_20261031/HOLDOUT_OBSERVATIONS及原始RV-HOLDOUT-01固定两例：

- U02：平台有效签名的SD-JWT最外层cnf.jwk，官方verify_root结果确含cnf，MandateClient.verify(...).mandate_payload只保留delegate_payload中的CheckoutMandate、不含外层cnf；消费者返回VERIFIED及完整checkout/hash。
- U03：同一外层cnf经合法披露/已签摘要承诺，官方SDK还原根含cnf，而提取后对象不含；仍VERIFIED。

父consumer.py第149行只保存提取载荷，第160行只查这个对象的cnf；“提取结果无cnf”不代表完整根不可继续委托。SDK支持该凭据形态，不是SDK漏洞；本消费者明确不支持委托，故违反父合同第4条和AC-04。没有付款或订单事故。

**唯一修复：在本任务副本consumer.py内，保留官方验签后完整SD-JWT根和结账有效载荷两个层次的安全条件，只有二者都无继续委托cnf时才能VERIFIED。** 包括明文和经官方披露还原的外层条件。使用同一精确token和同一请求外平台根的官方完整验证结果（现成ap2.sdk.sdjwt.sd_jwt.verify可用）或等价已验证SDK对象；不得仅靠未验证payload/任意披露字符串/递归关键词匹配作为可信根，也不得改SDK或自写密码学替代。

继续保留MandateClient单凭据验证的严格时钟、实际签名vct/iat/exp、checkout_hash、完整商家JCS签名、当前完整session、无KB/多跳、请求外keys、格式/重复键/数值/Unicode及失败无授权事实规则。普通合法字段/任意新kid/币种/Unicode不应误拒绝，不要求过滤所有未知根字段。不能把所有凭据拒绝，或只对测试key/case名硬编码。

## Allowed scope / 允许范围与冻结材料

仅可修改本任务consumer.py，填写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json和evidence/。父H54提交/拒收证据、所有旧任务、src/tests、SDK、商家、冻结合同/计划/检查器/来源/BASELINE全部只读。新副本当前逐字节保留父有缺陷consumer.py；SHA与来源在SOURCE_COPY，尚未修复。

复用父H54的36场景和完整JCS/19公开源，不改案例、预期或调用语义。RUNTIME只改临时日志目录为.task_envs/H54R/runs；FROZEN_TESTS只降低Evaluator预算；CHECK仅换任务/地图/结果/账本元数据。父独立生成器逐字节复制sources/evaluator/H54_HOLDOUT.py，ROOT_CASES只调用U01新kid/新条款合法对照及U02/U03，共3例；不执行该来源脚本main中其余诊断。其他三条WATCH不是本修复AC，不扩完整协议义务。

接口原样consume(request_json: bytes,session_json: bytes,trust: dict,now: int)->dict；只输出原字段VERIFIED或无授权事实DENY，不改输入，不产生付款ALLOW/付款/订单。允许导入仍JSON/摘要/编码/正则/typing/copy、固定rfc8785、jwcrypto、AP2和pydantic，无文件/进程/网络I/O或动态导入。不能修改冻结检查器绕过验证。

同一H47 Windows Python3.12、已有H37纯Python模块，固定AP2 commit b4587ac1d055888a73b4b21750973cffba961793，cryptography46.0.7/pydantic2.13.4/jwcrypto1.5.6/sd-jwt0.10.4/ucp-sdk0.4.6/PyYAML6.0.3；任务内原样rfc8785 0.1.4及Node24.12.0独立判据。无新下载、安装、钱包/真实根/真实确认；合成私钥仅内存，公开材料可留证。父H54已消耗2/2 L2、144/288case及Evaluator46/144保持，不回写、不重置。

## Acceptance criteria / 验收标准

### AC-01 — 单模块修复与来源保护

Given父提交/新副本/固定环境与HEAD；When VP-01/02/09；Must observe冻结与保护摘要一致，只修改本任务consumer.py及指定交付，来源许可/hash/旧实现不变；Must not observe修改SDK/商家/产品/旧任务/判据或权限；Evidence=SOURCE_COPY/BASELINE/原始EV及独立源码复核。Mandatory: yes。

### AC-02 — 外层完整根条件不得丢失

Given U02/U03真实平台签名及已验证完整根含cnf、提取条目不含cnf；When VP-05/06；Must observe两例DENY且不返回checkout/checkout_jwt/checkout_hash，完整官方根/有效条目/原始材料均可复算；Must not observe只检查facade提取对象、猜测明文披露或关闭官方校验；Evidence=ROOT_CASES各输入/输出/SDK完整根与有效载荷、独立L3/源码。Mandatory: yes。

### AC-03 — 合法标准流程与原护栏保持

Given原36案例、JCS固定gold及U01新kid/EUR/Unicode合法控制；When VP-03/04/05/06；Must observe原36全部符合父合同、U01 VERIFIED且完整事实/签名/摘要保持；Must not observe全部拒绝、未知字段丢失、来源/时间/JCS/hash/完整session/降级/类型默认值护栏退化；Evidence=原36+根3=39场景及独立SDK/JWS/Node复算。Mandatory: yes。

### AC-04 — 回归、成本与完整交付

Given120主动分钟/2L2/312case；When全部9项；Must observe25项AP2回归保持，原检查器4种破坏及父两反例可判别，失败/预留/原始三件套留存，完整L2后一次整包提交；Must not observe自授PASS、覆盖父失败、越预算或升级付款/HTTP/生产声明；Evidence=REPORT/RESULT/账本/L2及独立L3。Mandatory: yes。

## Validation plan / 验证计划与预算

VP-01保护/环境；02候选范围；03原完整JCS判据；04原36；05根条件3；06原始材料、完整根与总账本；07原25回归；08原4种破坏/父反例判别；09再次保护。VALIDATION_PLAN已固定9项命令及Evaluator命令。准备H54R-PREP-01只验证旧合法控制和父反例可判别，**未调用新候选，未修复、没有H54R场景成绩或L2**。

Executor<=120主动分钟/2正式L2，原36包装器上限288case，根3包装器上限24case，总<=312；Evaluator原36上限108、根3上限9，总<=117。每轮完整39。FROZEN_TESTS.py --role executor [--case CASE_ID]和ROOT_CASES.py --role executor是全部候选调用入口；先追加对应ATTEMPTS.jsonl / ROOT_ATTEMPTS.jsonl预留，导入/生成/断言失败仍计数。每批新目录，原始输入先落盘、输出/失败保留，不覆盖；LATEST仅指针。max_parallelism=1、代理0。无账本额外调用候选禁止。

正式L2前更新ATTEMPT_LEDGER，目录只用evidence/l2_executor_01和_02。artifact_cases_reserved须等于executor两份预留之和，formal_l2_attempts等于保留L2目录数，active_work_minutes<=120。network_calls/asgi_requests/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations/payment_calls/orders_created全部0。中央Runner写9项stdout/stderr/meta及L2-GATE；首轮失败有具体合同内机制可用第二轮，禁止无限续跑。

REPORT执行后生成，含Task ID/Task kind/Baseline HEAD、逐AC、失败/成本/边界、全部EV、external_requirement_impact及SUBMITTED_FOR_REVIEW。RESULT schema=h54r-result/v1、task_id本任务、classification=LOCAL_NONDELEGATING_CHECKOUT_REPAIR_OBSERVED、before=PARENT_REJECTED_OUTER_CNF_ACCEPTED、after=BOUNDED_NONDELEGATING_CONSUMER，仅实测通过后可填；customer_demand=UNKNOWN、remaining_gaps非空列表；production_ready/full_ucp_conformance/real_actor_authentication/psp_verified/payment_execution_integrated/http_integrated/cross_system_revocation/customer_value_proven全部false。修复是repair，项目影响裁决不冒充能力实验提升率。

CURRENT只可改EXECUTING/Executor与execution_phase，固定任务/地图/权限和next_artifact=REPORT不变。完整L2通过后提交，仍EXECUTING/Executor；Evaluator接受未变快照后才READY_FOR_REVIEW及独立L3。无空REPORT/REVIEW占位，不自行PASS、不自动H54R2/H55。

## Stop conditions / 停止条件

如果需改第二实现文件、SDK/商家/核心/接口、冻结判据/依赖/假设/AC/预算或网络/付款权限，立即停止交Evaluator，不能借修复扩完整schema/协议。保护漂移、秘密落盘、预算耗尽或同一失败无新机制也停止，保留完整材料。

通过原36+根3且独立无合同反例、回归和来源保持才可接受，并STOP本验证切片；之后另比较同事务标准事实到执行接缝。若仍误放行继续拒收，不包HTTP或支付；范围必须全面迁移时STOP/SWITCH。三个父诊断（中间型根typ/空结账/旧签名版本）仅WATCH，若未来需要更严格协议配置需另冻合同，不能本轮静默扩张。

## Exclusions and authorization / 排除与授权

零网络/DNS/监听/HTTP/ASGI/模型/Provider/钱包/测试网/真实或沙箱付款/安装/真实密钥/对外联系/Git写操作。无通用运行时/区块链/新商家。H53R已接受成果、父H54拒收和所有历史账本不变。

## External requirement impact

已复核PCAC开发指标映射。profile=PCAC-AGENTPAY；PCAC-07/09=CORE，before=父标准非委托合同有反例、未接受，after_target=仅该切片修复可接受；PCAC-12/20=CORE/EVIDENCE_ONLY，Test=VP-01..09及完整根/有效载荷/原始材料/L2/L3；PCAC-08=CORE/ADAPTER，仅合成签发来源，不升级真人身份/同意；PCAC-10/18撤销/应急不变。剩余完整协议/现实来源/PSP/同事务执行/部署/客户unknown。无监管合规或生产安全结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
