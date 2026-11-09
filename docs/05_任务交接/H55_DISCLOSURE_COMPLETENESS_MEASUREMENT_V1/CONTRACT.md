# H55 披露完整性与授权约束的有界测量

Task ID: H55_DISCLOSURE_COMPLETENESS_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H55_DISCLOSURE_COMPLETENESS_MEASUREMENT_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r91
Active bottleneck: B-17
Hypothesis: H-55

最终目标是高风险支付授权、执行、恢复、审计可独立复核。A–D关闭，E仅本地受控，F当前。H54R已PASS/STOP已披露根条件修复，父H54仍拒收；但独立V07表明：同一已签JWT，去掉根cnf披露后SDK仍VALID、已披露视图不含cnf、消费者VERIFIED。没有付款/订单；不是SDK漏洞，是“已验签披露集合”和“完整授权语义”之间的消费合同缺口。该前置安全不确定性优先于同事务接线、HTTP、Provider（支付服务方），也优先于根typ/空checkout/旧版本三个WATCH。支付宝/比赛延期保持。

## Single objective / 唯一测量目标

只测固定同签名呈现对是否导致消费者对已知授权条件不可见，并与无害可选披露对比较。用真实已签原始材料、固定SDK及已接受H54R消费者的不可变快照，串行完成6份呈现各repeat2的12观察、3种最小机制比较和一个下一合同结论。不改产品/消费者/SDK，不建新闸门，不把测量改写成已修复/完整协议符合性或可付款。

准备已知V07、V02及父正常对照的大部分行为，不宣称本轮从全unknown测到known。D04由固定代码预测为VERIFIED，但尚未在H55运行消费者；其余观察的独立重复、同一issuer JWT及选择性披露责任仍须正式交付。before为已有诊断/代码依据，after仅可复算测量与机制判断，非能力改善率。

## Terms and fixed inputs / 概念与固定输入

- Signed commitment（已签承诺）：issuer JWT中的字节和摘要承诺；删除披露段不会重新签署它。
- Verified disclosed view（已验签披露视图）：SDK成功验签后还原出的已提供字段，不保证含所有被承诺字段。不能把“返回对象无cnf”等同“发行者没有承诺cnf”。
- Authorization completeness（授权条件完整性）：消费者是否具有作出授权结论所必需的条件证据；隐私字段可省略不等于安全条件可省略。这里只测差异，不预设全披露为普适协议规则。

FIXED_CASES.json固定6个合成呈现、请求/session原字节、公钥、时钟和预期现有实现行为。两对issuer JWT逐字节一致，差别仅一条披露，SHA/SDK及完整视图可独立复算；所有密钥只含公开部分，原合成私钥不需要也不读取。

| Case | 输入和已知Ground truth（来源真值） | 现有消费者预期/SDK |
|---|---|---|
| D01_CNF_REVEALED | 已提供根cnf披露 | DENY / VALID |
| D02_CNF_REDACTED | 同一签名，删除cnf披露；完整对照证明承诺过cnf | VERIFIED / VALID，视图不含cnf |
| D03_OPTIONAL_REVEALED | 已提供无害optional_note | VERIFIED / VALID |
| D04_OPTIONAL_REDACTED | 同一签名，删除无害optional_note | VERIFIED（准备预测）/ VALID |
| D05_NORMAL_CONTROL | 原合法标准checkout | VERIFIED / VALID |
| D06_BAD_SIGNATURE | D02签名位被改 | DENY / REJECTED |

这些是现有行为的测量预期，不是把D02定义为可安全授权。D01/D02与D03/D04的签名不变事实比重新签一个不同样本更能定位披露接缝。SDK保留摘要前后的代码依据见固定sd_jwt/verifier.py；AP2 agent_authorization.md说明Agent选择披露以兼顾隐私与授权，以及unresolved_constraint处理，都是本地已固定来源，不新增网上研究。

## Allowed scope / 允许范围

Executor只能写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json、MECHANISM_COMPARISON.json和evidence/。所有脚本、FIXED_CASES、consumer_snapshot.py、来源/许可/BASELINE、旧任务和src/tests只读。禁止实现新验证器、改SDK/快照、插入字段/重签token、搬动旧证据或偷偷接付款/HTTP。

PROBES.py是固定只读测量器，运行已有消费者快照；REFERENCE.py独立验证SDK、披露名称和同一已签JWT；CHECK.py核对原始观察/重复一致/账本及比较结构。snapshot逐字节复制已接受H54R，SOURCE_COPY记录来源hash，非新候选。RUNTIME仅日志scratch变更为.task_envs/H55/runs，Python/SDK/密码库和19个JCS公开源完全复用，不安装、不下载。真正签名仍由既有库验证，不以检查器预期冒充验签。

## Required mechanism comparison / 必须比较的三种机制

MECHANISM_COMPARISON.json含mechanisms列表，id固定NO_CHANGE、ALL_RELEVANT_DIGESTS_RESOLVED、EXPLICIT_SIGNED_PROFILE；每项填classification=ABSORB/REFERENCE_ONLY/REJECT/DEFER，evidence、privacy_tradeoff、compatibility、risk、estimated_cost、unknowns非空。

1. **不改变消费者**：说明现有已披露视图为何不能证明缺省授权条件不存在；不能把固定正例通过当安全闭环。
2. **相关安全容器的摘要全部解析**：只研究其判定依据、相关对象范围、合法可选字段/decoy（诱饵摘要）与兼容代价，不实现。不能靠猜摘要的字段名；“拒全部未披露字段”可能牺牲隐私/兼容，必须明确适用配置和代价。
3. **显式、被签名绑定的消费配置/发行方责任**：分析是否引入自定义声明/可信来源/额外协议义务，能否保持标准输入；不发明未授权机构背书或真正PKI。

给一个next_decision：BOUNDED_PROFILE_CONTRACT_REQUIRED或MEASUREMENT_LIMITATION_STOP，附why_not_execution及remaining_exact_input，必须指出下一合同所需的最小输入/信任前提；结论不以新增实现收尾，不泛化成全面AP2迁移。若没有证据支持最小机制，明确STOP及精确缺项，不能自动修H54R2。

## Acceptance criteria / 验收标准

### AC-01 — 固定原文、来源及只读边界

Given6份真实签名呈现和原样快照；When VP-01/02/06；Must observe两对issuer JWT相同、各只移除一条披露、完整SDK根证实对应名称，签名/原文/hash及旧文件保护一致；Must not observe重签伪对照、修改快照/SDK/既有成果或新增依赖；Evidence=FIXED_CASES/SOURCE_COPY/REFERENCE及EV。Mandatory: yes。

### AC-02 — 12次真实可复算观察

Given6份呈现各repeat2；When VP-03/04；Must observe12实际快照响应及SDK结果、原始输入/输出齐全、重复相同，D01/D02安全条件视图差异与D03/D04无害披露对照独立复算；Must not observe手填消费者响应、把准备预测算本轮实测、用D02 VERIFIED宣称可安全付款；Evidence=原始token/公钥/SDK/逐例响应/12记录。Mandatory: yes。

### AC-03 — 单一下一合同结论

Given测量与本地固定协议/代码；When VP-05及人工内容复核；Must observe3机制的来源/隐私/兼容/风险/成本/unknown比较、一个有界结论及精确下一输入，不只罗列愿望；Must not observe实现新闸门、跳过消费配置责任或因为同属支付就引入钱包/链/新Provider；Evidence=MECHANISM_COMPARISON、REPORT及原始观察。Mandatory: yes。

### AC-04 — 预算与证据交付

Given120主动分钟/2L2/72消费者测量调用；When完整6项；Must observe预留/失败/原始三件套保留、完整L2后整包提交，所有能力扩大标记false；Must not observe覆盖历史、越预算、网络/安装/付款或自授PASS；Evidence=账本/REPORT/RESULT/L2及独立L3。Mandatory: yes。

## Validation plan / 验证计划与预算

VP-01保护/环境；02签名/原文对照；03实际12测量；04观察复算与重复一致；05机制/结果/预算；06再次保护。6项命令已固定于VALIDATION_PLAN。无产品变化，不机械重跑此前25项回归或旧冻结计划；保护摘要确保原实现未动。

Executor<=120主动分钟、2正式L2、72快照调用（6个完整12波次）；Evaluator另<=48。所有快照调用只经PROBES.py --role executor，先向evidence/executor/ATTEMPTS.jsonl追加12预留，生成/导入/运行失败仍计数；每批新目录，原始输入先落盘、输出/失败保留，LATEST只是指针，不覆盖旧材料。max_parallelism=1，无代理；没有不记账临时快照探查。

正式L2前ATTEMPT_LEDGER预记formal_l2_attempts/active_work_minutes/consumer_calls_reserved（等于测量预留之和）；正式目录evidence/l2_executor_01或_02，旧失败不删。network_calls/asgi_requests/model_calls/provider_calls/packages_installed/payment_calls/orders_created/git_write_operations全部0。

RESULT schema=h55-result/v1、task_id本任务、classification=DISCLOSED_VIEW_NOT_AUTHORITY_COMPLETENESS_PROOF、new_policy_implemented=false、execution_ready=false、customer_demand=UNKNOWN、remaining_gaps非空。只有正式观察符合后才能填测量结论，未完成就保留真实失败；不得为了机械检查编成功。REPORT真实生成、逐AC/全部EV/失败成本/准备与本轮区分、PCAC影响、下一结论，完整L2通过后SUBMITTED_FOR_REVIEW。CURRENT仍EXECUTING/Executor，Evaluator接受未变快照后一次独立L3，不自授PASS。

## Stop conditions / 停止条件

需改输入/快照/SDK/冻结命令/AC/依赖、预算或权限即停回Evaluator。保护漂移、秘密落盘、预算耗尽或无新信息重复也停。签名/材料构造不符合固定对照不能“修原文变绿”，保留真实失败。测量不等于能力建设授权。

本轮通过只接受固定呈现/SDK/消费者的可复算差异和机制比较；如果形成有依据最小规则，由Evaluator另冻bounded profile（有界消费配置）合同后才CONTINUE能力实验；如果不能区分合法隐私和授权完整性，STOP并指出缺发行方声明/协议规则/可判据输入。两种结果都禁止直接接执行/付款。H54R切片STOP、父H54拒收不反写，真实身份/确认、完整协议/PSP/部署/客户仍unknown。

## Exclusions and authorization / 排除与授权

零外网/DNS/监听/HTTP/ASGI/模型/Provider/钱包/测试网/真实或沙箱付款/真实密钥读取/安装/对外联系/Git写操作。无区块链或通用运行时；本包不是商家协议升级、生产部署或上线许可。

## External requirement impact

已检查PCAC开发指标映射。profile=PCAC-AGENTPAY；PCAC-07/09=CORE，before=已披露约束修复接受但授权完整性缺可判据消费配置，after_target=只测量/建模，不升级实现成熟度；PCAC-12/20=CORE/EVIDENCE_ONLY，Test=12原始观察/6计划/机制比较/L2/L3，Evidence=同签名呈现对和SDK视图；PCAC-08仅合成平台来源，10/18撤销应急不变。残余隐私/未知摘要/发行方责任、现实身份/完整协议/执行/PSP仍未验证。无合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
