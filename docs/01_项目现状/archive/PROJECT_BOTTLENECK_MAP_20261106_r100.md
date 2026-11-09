# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-11-06-r100
Last reviewed: 2026-11-06
Map owner: Evaluator / Human Task Owner
Status: ACTIVE
> 当前新任务统一使用 `evaluator-executor-workflow/v2.2`，按“瓶颈—假设—同基线实验—保留或回滚”闭环推进。

2026-11-06 r100：**H61 PASS / NOT_APPLICABLE / STOP材料测量；H62_APPROVED_ORDER_RECOVERY_SEAM_V1 / capability_experiment / SINGLE / CONTRACT_FROZEN / Executor。A–D本地代表、E仅本地、F当前。H61正式L2/L3各6/6，57签收文件、2625保护文件、24原始流保持，三库19表逐值相同；Executor提取2/4、L2 1/2、保守11分钟，Evaluator1/2。B-17缩到批准消费与原生订单事务协议缺失。下一仅新副本四产品文件：共享订单逻辑、交易库唯一收据、批准锁→原生事务锁与全部撤销入口；恢复零付款、16恢复/24批准/6原生旅程/25AP2，360主动分钟/2L2，Evaluator独立一套另16case上限。新消费者尚未实现、无新成绩。通过STOP该切片，失败/跨范围回query-only，不自动SDK/第二商城/通知平台。已有共享适配/校验与跨算法第二消费者不重测；架构职责混放及README漂移登记、不抢主线。真实身份/PSP/标准互通/商户/客户unknown，H56未执行、支付宝/比赛延期、四外部/Git旗false。** 以下r99及更早为历史。

2026-11-04 r99：**H60R PASS / NOT_APPLICABLE / STOP批准登记器；H61_APPROVAL_CONSUMER_RECOVERY_SEAM_MEASUREMENT_V1 / one_off / measurement-only / CONTRACT_FROZEN / Executor / SINGLE**。地图r99，A–D本地代表、E仅本地、F当前，B-17从来源隔离转批准实际消费者未知。正式L2/L3各7/7、24例跨WSL/Windows稳定观察和来源视图一致；109签收文件/2414保护文件及28原始流hash保持，三个独立构造器检查通过。父H60拒收不回写，H60R新24例/1门禁/11分钟，继承后103/160、3/4、41/150；Evaluator26+24+3=53/60。批准仍LOCAL_OPERATOR_ASSUMED、execution_enabled=false，M06付款1/订单0。下一H61只读十文件/三库，不调用候选/商城/付款，比较query-only、旧complete与订单侧恢复，交十主题/三机制/八未来设计和唯一候选或STOP，不重复H58缺失盘点/再问H59、不直接补单。新120主动分钟/2L2/4提取器调用，Evaluator另2；提取器未实现、无新成绩。真实身份/PSP/标准互通/商户/客户unknown、H56未执行、支付宝/比赛延期、四授权false。入口H61/EXECUTOR_START.md。以下r98及更早为历史。

2026-11-04 r98：**H60未签收交付 REJECTED / INCONCLUSIVE；CONTINUE H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1 / repair / CONTRACT_FROZEN / Executor / SINGLE**。地图r98，A–D本地代表、E仅本地、F当前，B-17仍优先。独立复核原307提交文件不变、原两库hash保持，父五项只读检查通过；纯夹具不调用候选即复现C12关闭连接后的WAL摘要漂移，C17串行子进程同tick容差可在新包重冻结。但两独立子进程确认：账本为交易/假PSP来源硬链接时，构造器不拒绝且在来源副本建approvals/approval_events表，AC-01失败；无正式L3，旧修复版7/7自重放不能冒充签收。新包只许修新副本构造函数的文件身份隔离，其他产品AST不变；Evaluator已冻结合法夹具和原20+4别名=24例/七VP，候选原样、修复未实施。父Executor79case/30分钟与两次修复版门禁全计费；新<=72case/120主动分钟/2门禁，累计<=151/160case、150分钟、4门禁（新增修复配额，非旧额度重置）。父自重放20+本轮独立6占Evaluator26/60，新余34。通过STOP登记器再评实际消费者；需扩范围/预算则停。原M06付款1/订单0，执行关闭/身份LOCAL_OPERATOR_ASSUMED，真实身份/PSP/标准互通/商户/客户unknown；H56未执行，支付宝/比赛延期，四旗false。入口H60R/EXECUTOR_START.md。以下r97及更早为历史。

2026-11-02 r97：**Human已选择人工批准的对账处置入口；H59执行前决策已解决；H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1 / capability_experiment / SINGLE / CONTRACT_FROZEN / Executor**。A–D本地代表、E仅本地、F当前，B-17第一可执行瓶颈收窄为原M06持久证据上的明确操作员批准登记能力ABSENT。只新建一个标准库APPROVAL_INBOX模块，正常批准/CLI读取、错绑与越权拒绝、过期/变源/策略失效、撤销不复活、重启与两连接竞争，固定20例/七VP；240主动分钟/2L2/160case，Evaluator另60。批准绑定交易/付款/来源摘要/角色策略，只有新批准库可写，原交易/PSP只读；真实人身份仅LOCAL_OPERATOR_ASSUMED，execution_enabled始终false，不补单退款/解锁原claim。新明确批准有独立时限，不挪用旧付款确认或强制建设生产凭证体系。来源/夹具和判别器就绪须检查，候选实现尚不存在、20例未跑、无L2成绩。比回H56更接近商家处置责任，比直接自动补单更少副作用；若通过STOP此登记器，另评实际消费，不继续堆字段。H58 PASS/STOP、H57R PASS/STOP和父H57拒收保持；H56未执行、真实身份/PSP/标准互通/商户/客户unknown、支付宝/比赛延期、四旗false。Human选择记录H59/DECISION.md，入口H60/EXECUTOR_START.md。以下r96及更早为历史。

2026-11-02 r96：**H58 PASS / NOT_APPLICABLE / STOP固定材料重复测量；H59_LOCAL_REMEDIATION_DISPOSITION_DECISION_V1 / evaluator_design / DRAFT_CONTRACT / Evaluator / NOT_DISPATCHED**。A–D本地代表、E仅本地、F当前。H58正式L2/L3各6/6，38接受文件不变、24原始流hash/长度一致，M01/M06与两库17表两角色双遍逐值相同，六损坏自测拒绝。Executor4/8读取、1/2L2、保守13分钟闭合区间；Evaluator2/4。零HTTP/支付/恢复/订单写入/网络/Git。B-17从持久材料未知缩到“已有支付引用/绑定快照/确认摘要，但付款无订单的批准主体、结束状态及执行权限未定义”。接受MISSING_DURABLE_INPUT的固定边界，不接受必须存全部旧token/私钥/生产信任根的架构推断，不把真实PSP/客户未知作为所有本地研究的阻塞。原order成员实际省略，非显式null，复核已澄清、不影响orders=0。停止重复对同一资料加读取/字段；已向Human询问人工批准对账处置（建议）、明确条件自动补单、或保留查询切换方向。未答复不推定批准，H59精确缺该业务策略；无执行AC/预算/验证计划派发，不建第二份泛化测量。领域词汇见CONTEXT。H57R PASS/STOP及父H57拒收保持，H56未执行支线，真实身份/PSP/标准互通/商户/客户unknown，支付宝/比赛延期，四授权false。以下r95及更早为历史。

2026-11-02 r95：**H57R PASS / NOT_APPLICABLE / STOP本工厂接线及证据修复；下一H58_MERCHANT_PAID_ORDER_GAP_MEASUREMENT_V1 / one_off / measurement-only / CONTRACT_FROZEN / Executor**。A–D本地代表、E仅本地、F当前。正式签收后L3为7/7，与L2六旅程一致，125接受文件不变、50正式原始流长度/hash一致；25AP2及12负向自测通过。M01恰1付款1单，M02–M05零付款订单；M06真实首商城退出后GET200/新键409、原recover查询SUCCEEDED、不重扣，订单仍0。独立Windows内核句柄观察确认真实工作PID先存活后退出，不只启动器返回。38商家只读，历史57+新42=99/160，L2 1/2，保守收费150/240；Evaluator一次预签收流程误跑18加正式18=36/80，失败路由写入未改文件、原证据保留，正式签收后完整重跑已纠正。父H57拒收结论不改。B-17接线断口代表性关闭，第一业务缺口转为“已付款无订单”的补救责任/持久输入充分性未知。H58只读固定M01/M06及M06持久库，分清持久数据、实验交接和缺失事实，比较保留查询/未来补单/补偿，形成一个下一决策，不调用HTTP/付款/恢复、不实现补单退款。比回H56非标准支线更贴近已观察业务断点；真实Provider/商户/客户仍未知、支付宝/比赛延期。120主动分钟/2L2/8只读波次，Evaluator另4；四授权false，入口H58/EXECUTOR_START.md。以下r94及更早为历史。

2026-11-01 r94：**H57未签收交付REJECTED / INCONCLUSIVE；CONTINUE H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1 / repair / CONTRACT_FROZEN / Executor**。A–D本地代表成果、E仅本地、F当前保持。B-17正常商城接线已出现候选：原工厂体注入控制、原生装配以及六例18HTTP材料经Evaluator只读语义复算，1680保护/52冻结/36商家原源保持；这不是独立HTTP复跑或正式L2/L3。旧预留25对象被字面量换行串成一行且h57-2重复24次，后32条（14失败+18完整）虽规范却不在合同账本路径；materials确实JSONDecodeError，RESULT/预算账本及L2均缺。更关键：恢复脚本在首商城父进程还活着时同步开第二进程，只关lifespan，旧判别器只查不同PID，未覆盖AC-04首进程真正退出；不是已发现商城多付。新包只修两验证脚本的证据忠实性，38商家候选全冻结，历史raw/hash/57成本只读继承；监督者先wait首worker退出后才开恢复worker，重新完整六例/L2再独立L3。原160请求已57、余103，L2已0/2，Evaluator仍0/80；旧主动用时unknown，按执行会话墙钟上界保守收120分钟，新<=90且不越总240。比放宽日志或回H56更直接闭合当前商城链，完成后STOP此接线、按实际业务选下一步。H56未执行支线，真实身份/标准互通/商户/PSP/客户unknown，支付宝/比赛延期，四旗false。入口H57R/EXECUTOR_START.md，下方r93及更早为历史。

2026-10-31 r93：**主线重新锚定实际商城接线；H57_DEFAULT_FACTORY_MERCHANT_E2E_V1 / capability_experiment / CONTRACT_FROZEN / Executor / SINGLE**。Human质疑最近任务偏向细节，Evaluator复查H47/H49/H51/H53R实际证据：商城样例已在本地运行，H51成功HTTP靠测试dependency_overrides，原生默认get_checkout_service仍未传控制；其独立C07为201/409、0付款订单，且H53R默认工厂源与其逐字节相同，H53R授权仅方法级接受。H56的非标准可选区尚无该商家使用需求，不应默认抢占接入；H56未执行，冻结文件保留为安全支线，本轮不运行、不声称完成/失败或Human暂停，未来启用需重新评估/正式重冻结。B-17第一可执行缺口回到“正常应用配置→原生工厂→既有控制→商城业务”整链。H57只改新副本工厂函数体+新增guarded_app装配，原生路由/签名/生命周期/其余36文件保留，不许测试替换工厂。6旅程覆盖完成/重放/查询、改单、缺确认、假授权、未配控制、订单失败后真正新进程查询/不重扣；240分钟/2L2/160进程内HTTP请求，Evaluator另80。37商家/42来源复制和环境/判别器准备就绪，尚无新装配实现或HTTP成绩。保留2026-04-08及H53R本地授权信封，不冒充标准CheckoutMandate/真实部署，付款为独立假PSP，恢复为查询不自动补单。通过后STOP此接线，按实际商城断点选后续，不自动回字段修补。A–D本地成果、E本地边界、F当前，真实身份/标准互通/PSP/客户unknown；四旗false、支付宝/比赛延期不变。入口H57/EXECUTOR_START.md；r92及更早为历史优先级判断。

2026-10-31 r92：**H55 PASS / NOT_APPLICABLE / STOP重复披露测量；H56_TRUSTED_DISCLOSURE_PROFILE_V1 / capability_experiment / CONTRACT_FROZEN / Executor / SINGLE**。H55固定L2/L3各6/6、12观察逐字节一致，121接受文件未变，截至POST32原始流hash/长度一致。D01/D02同签名移除cnf后DENY→VERIFIED，D03/D04无害可选字段删减仍VERIFIED；这是问题实证，不是可执行授权。Executor24/72、L2 1/2、自报18分钟；Evaluator12正式+14新包旧对照=26/48，零支付/订单/网络。比较支持需要可信消费配置，不证明必须新签一个声明。Evaluator已收窄：请求外固定配置绑定已有平台kid/版本，授权默认区的已签摘要必须解析齐，只有签名认证可见的根optional_data对象内部可保留隐藏资料且不得参与授权/业务事实。该可选区为任务内非标准约定，旧根optional_note隐藏/授权区decoy摘要拒绝是明确兼容代价。准备14真实签名旧对照在根/有效载荷两位置都误放行隐藏cnf，9目标不符含新配置规则、不全是旧漏洞；新candidate原样H54R未实现。冻结原39+14=53、10计划、240分钟/2L2/424case，Evaluator另159；只改新consumer.py，不改SDK/商家/核心或付款。B-17从测量推进有界完整性门槛建设；成功后STOP该配置，另评未知语义/发行责任/执行接缝，不能自动HTTP/付款。H54R已接受范围、父H54拒收保持，真实身份/确认/完整协议/PSP/部署/客户unknown；API/Git四旗false，支付宝/比赛延期。入口H56/EXECUTOR_START.md，以下r91及更早为历史。

2026-10-31 r91：**H54R PASS / NOT_APPLICABLE / STOP已披露根条件修复；H55_DISCLOSURE_COMPLETENESS_MEASUREMENT_V1 / one_off / measurement-only / CONTRACT_FROZEN / Executor / SINGLE**。固定L2/L3各9/9、39稳定摘要一致，251接受文件未变，截至POST48原始流hash/长度一致，25AP2回归保持；U02/U03已DENY。仅consume函数体和一个官方完整根verify导入改变，原facade严格时钟保持。六条泛化保持（普通未知/披露/嵌套同名字段允许，空/null根cnf及坏签名拒绝），但额外诊断V07删除cnf披露后SDK仍VALID、视图无cnf、消费者VERIFIED；“已验签披露视图”不等于“发行者承诺的全部授权条件”。H54R只按已冻U02/U03合同接受，不倒加新失败AC，也不接受整体非委托证明或接付款。Evaluator46/117，Executor78/312、L2 1/2、自报24分钟，零付款/订单/网络；父H54仍拒收、旧H53R PASS/STOP保持。B-17最前移到披露完整性消费合同，该安全前置缺口优于同事务接线和三个旧协议WATCH。H55只读六份真实签名呈现各repeat2=12、三机制比较、6项验证，120分钟/2L2/72快照调用，Evaluator另48；原样快照，不改消费者/SDK/商家。准备仅核对6个SDK材料与两对相同已签JWT，未调用H55消费者，D04行为仅预测。完整测量后再冻最小配置/发行责任或STOP，不自动能力修补/HTTP/支付。API/Git四旗false，真实身份/确认/完整协议/PSP/部署/客户unknown，支付宝/比赛延期不变。入口H55/EXECUTOR_START.md；以下r90及更早为历史。

2026-10-31 r90：**H54最终REJECTED / INCONCLUSIVE，仅AC-04失败；H54R_NONDELEGATING_CHECKOUT_ROOT_REPAIR_V1 / repair / CONTRACT_FROZEN / Executor / SINGLE**。父固定L2/L3各8/8、36稳定观察一致、401接受文件复跑不变，截至POST核对60原始流，25AP2回归保持；但独立10例中U02明文外层cnf、U03合法披露的外层cnf均SDK完整根含cnf而facade提取载荷不含，消费者仍VERIFIED并返回完整checkout/hash。无付款/订单/网络，非SDK漏洞。H54仅查提取对象丢根约束，违反已冻非委托分支，不可接受可信改善。Evaluator46/144，Executor144/288、2/2 L2（首次失败留存）、自报35分钟。新副本仅consumer.py修复完整已验签根与有效载荷的非委托条件，不改SDK/商家/核心/JCS/原36；原H54拒收不回写，H53R PASS/STOP保持。冻结原36+U01/U02/U03=39场景、9计划、120主动分钟/2L2/312case，Evaluator另117。准备只确认父反例可判别，副本仍有缺陷、修复未开始。根typ/空checkout/旧签名版本三个额外诊断保持WATCH，不后加AC/捆绑全面协议；优先修合同内已知缺陷，再比较同事务接线，暂不包HTTP或支付。完整协议/现实主体/确认/PSP/部署/客户unknown，API/Git四旗false，支付宝/比赛延期不变。入口H54R/EXECUTOR_START.md；以下r89及更早为历史。

2026-10-31 r89：**H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1 / capability_experiment / CONTRACT_FROZEN / Executor / SINGLE**。按Human要求制定下一执行包，B-17仍第一瓶颈；H53R PASS/STOP和父H53 REJECTED保持。缺项已技术收敛为2026-08-25 UCP/AP2可信平台单CheckoutMandate、商家完整JCS签名与当前结账事实验证：新建一个consumer.py，标准ap2.checkout_mandate，请求外预置平台/商家keys，不改旧商家/SDK/核心。旧SDK compact checkout_jwt不能承载额外ap2成员，本配置明确拒绝、不静默丢失；非ap2未知字段全部保留。不把验证置于旧claim外假称付款接通，输出VERIFIED事实，支付/订单/HTTP/同事务接线另决策。准备公开只读源研究固定19个Apache-2.0文件，SHA256/Git blob一致，无安装；6对作者gold、10条RFC数字、Node跨语言/7非法域及官方单凭据/商家签名准备可跑，25项回归通过。36仅材料形状就绪，无候选实现/消费者成绩/L2/PASS。冻结5AC/8计划，360主动分钟/2L2/288case，Evaluator另144，失败与预留保留。通过且无独立反例才有界IMPROVED并STOP此验证切片，再比较同事务执行接缝；若需全面迁移/新权限则STOP/SWITCH。全协议、真实身份/确认、PSP/部署/客户仍unknown；执行期外网/安装/模型/Provider/付款/对外联系/Git零，四旗false，支付宝/比赛延期不变。入口H54/EXECUTOR_START.md，以下r88及更早按历史理解。

2026-10-31 r88：**H53R PASS / NOT_APPLICABLE / STOP本地授权消费与终结链修复**。冻结L2/L3各9/9、原28+独立6共34稳定观察一致，116接受文件复跑未变、36正式原始流长度/hash一致；76+8回归保持。父S04类型反转/S05中间型末跳错aud/S06错nonce均403、零占用/授权记录/付款/订单。额外七条形状检查均符合合同：合法终结别名可付款，三跳/截断/附加KB/伪头/嵌套根末类型拒绝。首次三跳测试构造误用SDK接口已保留失败和完整7case预留，纠正测试脚本后仅续六例，未改SDK/候选。Evaluator预留47/102，完成41个不同case；Executor68/272、L2 1/2，50分钟自报。仅目标函数语义改变、其他36商家文件不变；父H53仍REJECTED。B-17本地消费者断口收窄，整体未关闭：标准CheckoutMandate/完整JCS/可信流程与现实主体/Provider仍缺证据。下一H54_STANDARD_CHECKOUT_MANDATE_CONSUMER_V1为Evaluator-owned DRAFT_CONTRACT / NOT_DISPATCHED，精确缺一条完整标准输入/责任、JCS实现与独立向量、最小消费范围；不重复泛化测量、不自动协议迁移或新HTTP，不等付费客户。H53R冻结r87不反写，API/Git四旗false、支付宝/比赛延期不变；以下r87及更早为历史。

2026-10-31 r87（历史冻结）：**H53最终REJECTED / NOT_APPLICABLE，仅AC-02失败；H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1 / repair / CONTRACT_FROZEN / Executor / SINGLE**。父冻结L2/L3各9/9、28稳定观察一致、139接受文件复跑未变、36原始流长度/hash一致；独立六例中正常/缺配置/回滚通过，但S04颠倒两跳类型、S05中间型末跳错误aud、S06中间型末跳错误nonce各实际模拟付款1/订单1。新模块只看SDK返回长度和递归vct，没有要求完整Open→终结Payment；SDK可验证尚可委托链不等于本消费者可执行，非官方漏洞或真实资金事故。B-17未关闭，第一修复点收窄到最终链形状与上下文，优先于重开锁/HTTP或接新服务方。仅在新副本ap2_authorization.py修复，其他36商家文件/旧H53/src/tests/SDK只读；保留原28+独立6=34场景、9项计划，2主动小时/2L2/272case，Evaluator另102。父L2 1/2、56/280不重置；本轮Evaluator34/112。H53R仍是有缺陷副本，修复未开始；准备只确认判别器恰拒父S04–S06。H51/H52 STOP、完整JCS/协议/真实身份/Provider后置、支付宝/比赛延期及四旗false不变。入口H53R/EXECUTOR_START.md，以下r86及更早为历史。

2026-10-31 r86（历史冻结）：**H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1 / one_off / CONTRACT_FROZEN / Executor / SINGLE**。Human要求继续完善，Evaluator已补齐完整H51已接受checkout样本、既有SDK真实签验与输入判据、合成信任模型及原子接线范围；原草案归档。选择保留原始完整字节的普通JWS本地切片，保持商家2026-04-08，不宣称JCS或完整UCP/AP2，不作全面协议升级。准备3例旧API测量均签验有效/局部ALLOW，其中已签金额/币种与checkout冲突；76+8回归保持，36复制商家文件未改。没有候选实现、28例成绩或正式L2。唯一新增控制是在claim的同一BEGIN IMMEDIATE内结合已验签原文/投影/确认/完整DB快照；只许副本两文件指定位置和一个新授权模块，其他34商家文件/产品/旧任务只读。冻结28方法场景、9项计划、6主动小时/2L2/280case，Evaluator另112；整包后统一L3。B-17仍第一瓶颈，待真实执行证据才判断缩小；H51/H52 STOP、Stripe/Medusa后置、支付宝/比赛延期、外部/Git四旗false保持。入口H53/EXECUTOR_START.md。下方r85及更早为历史。

2026-10-31 r85（历史裁决）：**H52 PASS / NOT_APPLICABLE / STOP同类就绪测量**。完整L2/L3各8/8，12稳定观察一致、76+8回归通过；90接受文件复跑未变、32原始流长度/hash一致。Executor预留48/144材料case、正式L2 1/3；Evaluator新生成12/72，产品/商家零修改、零网络/ASGI/Provider/模型/付款/安装/对外联系/Git写操作。分类MERCHANT_CONTRACT_CHANGE_REQUIRED；Q04改投影金额仍局部ALLOW，Q06改币种却被归一为根USD并ALLOW、两者血缘false；Q07/09/10验签失败仍可单独得到业务ALLOW，暴露组合消费断口，不是错误付款实证。B-17缩小未关闭，下一应先收窄商家授权消费合同，不能直接把版本迁移/JCS/可信确认/执行/审计多项义务打包实施。H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1 / evaluator_design / DRAFT_CONTRACT / Evaluator / NOT_DISPATCHED，精确缺完整checkout/凭据格式与版本边界、现成JCS/独立向量、研究信任来源和唯一写入口范围。允许合成研究，不等付费客户；实际AC/命令未就绪不伪造计划或派实现。H51 STOP、Stripe/Medusa后置、支付宝/比赛延期及四旗false不变。H52冻结r84和Executor材料不反写；以下r84及更早均为历史。

2026-10-30 r84（历史冻结）：**H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1 / one_off / CONTRACT_FROZEN / Executor / SINGLE**。Human要求长串行包、整包统一评估；既有草案归档，不以“等付费客户”阻塞公开受控研究。固定3份官方原文/许可/摘要，花店2026-04-08对参考2026-08-25差异不静默升级。现有H47 Windows环境只读复用旧H37纯Python依赖、零安装；准备官方8例及76相关回归已过（首次路径失败保留），单一参考API接线smoke仅属准备。Executor串行完成来源/版本→四合成角色→12真实签名材料/血缘case→12接入义务表→一个最小未来边界→完整8项L2，再统一L3。6主动小时/3次L2/144材料case，Evaluator<=72；产品/商家/旧任务只读，无HTTP/ASGI/Provider/模型/付款/安装/对外联系/Git。B-17仍第一瓶颈，本轮只测就绪，不建设新闸门；发现缺口只记录。Stripe/Medusa、支付宝/比赛后置，四旗false。H51 PASS/STOP不改，没有Executor12例或新端到端通过，入口H52/EXECUTOR_START.md。下方旧草案/派发为历史。

2026-10-29 r83：**H51 PASS / NOT_APPLICABLE / STOP本HTTP切片**。冻结L2/L3各8/8；23方法与8 HTTP稳定摘要一致；111接受文件复跑不变、32正式原始流长度/hash一致。Evaluator实际19请求，C01正常/重放均200且总1付款1单，C02–07均拒绝且零付款/订单；C08首笔200/跟随409、1付款1单、两独立请求会话/连接、心跳约0.016秒。36实现只读，只有任务夹具服务工厂接线；默认工厂仍409，合成确认/离线公钥/假PSP不升级真实主体、部署、跨系统撤销、Provider或客户成熟度。B-17从入口未知缩到具体消费者的信任来源与执行责任未定；整体不关闭。停止继续加锁/路由/签发样机。下一H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1 / evaluator_design / DRAFT_CONTRACT / Evaluator / NOT_DISPATCHED，精确缺一个目标流程、获准样例、确认签发与商家部署/执行责任；商业交付另需问题负责人/预算意愿，研究消费者亦可。输入就绪后最多2主动小时只读就绪判断，不伪造AC或执行授权；没有具体消费者证据则保持本实现分支STOP。支付宝/比赛延期，外部/API/对外联系/Git权限不增加。H51冻结r82关联不反写，下方旧派发均为历史。

2026-10-20 r82：**H50R2 PASS / NOT_APPLICABLE / STOP本地方法锁修复；下一H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1 / one_off / CONTRACT_FROZEN / Executor**。独立L3原样7/7，2+15+4+2共23摘要与L2一致，96接受文件复跑后未变、28条正式流hash一致。真正claim使用timeout=0并在写锁获取点分类409；S01同订单/S02不同订单共争写锁均约1.72ms心跳、首笔完成/跟随409/总1付款1单。补充无关写者先占锁→零占用零付款拒绝→锁释放后同键重试恰1付款/1单成立。只有一个控制文件改变，旧H50/H50R拒收不反写；不自动H50R3。B-17移到HTTP入口/服务工厂/合成确认的接线：默认工厂不注入control是已知源码事实，真实HTTP结果未测。新包冻结36实现，仅HTTP夹具依赖注入与8场景，保持原生路由/验签/请求级会话及无注入对照，原23回归保持，共8项计划。4小时/2次L2、仅进程内ASGI、Executor请求总<=160；无socket/监听/外网/Provider/真实身份/客户/安装/Git。准备校验器不是HTTP结果。通过后STOP此切片再比较真实授权/Provider/需求，若需改原生实现则回商家合同。支付宝/比赛延期，四旗false，入口H51/EXECUTOR_START.md。

2026-10-20 r81（历史）：H50R REJECTED / NOT_APPLICABLE，仅AC-03空预查后的claim锁获取失败，转H50R2单文件90分钟/2次L2修复；原四例已有净收益。详见H50R最终REVIEW；本段不提供当前执行授权。

2026-10-20 r80（历史）：H50 REJECTED / NOT_APPLICABLE，AC-02/03失败，转H50R两文件/3小时/2次L2修复；独立反例为B写在途锁等待及原生成功分支无模拟付款。原H50两次L2用满，父任务保留，原型未接受。详见H50最终REVIEW；本段不再提供当前执行授权。

2026-10-20 r79：**H50 / one_off / CONTRACT_FROZEN / Executor / SINGLE**。H49最终PASS不变。Evaluator已收敛本地方法级样机的原生付款观察接口、同库合成授权先后及独立测试条件，准备35文件商家副本/许可，冻结15保护场景与2原生对照及5项计划。原生准备对照已复跑：正常库存5→4、改数量后5→3，均一次原模拟付款/一单；原生付款方法不传金额/快照，金额绑定before=NOT_OBSERVABLE，不作已知拒绝率提升。独立模拟账本保留所有charge调用；检查器自测拒5种过度结论+5种观测破坏。控制实现尚不存在，15保护场景未执行，没有H50 L2/L3或任务PASS。执行者只可在副本指定结算方法/新增执行控制中实现持久占用，保持原生业务；两连接竞争、事务A/B、真实退出进程/稳定引用查询均已列冻结验收。方法级结果不等于HTTP/生产/身份/跨系统撤销/Provider/客户。本包6小时/2次正式L2，网络/ASGI/模型/Provider/对外联系/Git全部零。B-17仍第一瓶颈，从设计就绪进入本地执行能力验证；支付宝/比赛继续延期。入口H50/EXECUTOR_START.md，下方草案/未派发均为历史。

2026-10-19 r78：**H49 PASS / NOT_APPLICABLE / STOP 本轮设计方向**。正式 L2/L3 均3/3，接受52文件复跑后未变，12条原始流长度/哈希核对一致；11入口/3机制/14未来设计完成只读核查。工程结论 SERVICE_CONTRACT_CHANGE_REQUIRED：付款前独立提交执行占用/冻结快照/稳定查询引用，付款后另提交订单；撤销与claim需要明确定义的共享先后。14项均未执行，服务端、产品和生产成熟度不升级，客户需求/预算UNKNOWN。B-17 的工程责任已收敛，但执行能力未建；当前剩余是原生付款接口不传金额/收款人/快照、本地授权假设及独立并发/恢复判定接线未冻结。下一候选 H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1 / DRAFT_CONTRACT / Evaluator / NOT_DISPATCHED；只考虑固定商家本地副本和合成付款，精确缺项在候选合同，禁止把草案当执行授权。不再追加同类泛化研究；接口/判定就绪才冻结，若等同另写商家则停止候选。支付宝/比赛延期及四项false授权不变。H49冻结关联仍r77，以下旧安排按日期理解。

2026-10-18 r77：**H48 PASS / NOT_APPLICABLE；结束客户端方向，CONTINUE B-17 → H49_MERCHANT_ENFORCEMENT_FEASIBILITY_V1 / one_off / CONTRACT_FROZEN / Executor**。独立 L3 5/5，18条摘要与L2一致，接受41文件核对不变，12种非法输入和5种错误投影拒绝，9+42回归通过。任务内桥接成立；G01模拟处理1次/库存4，G02–G06零处理，L01检查后改动及L02直接调用仍完成2件/库存3。准备已测过部分方向，产品核心无改动，不宣称服务端改善。第一瓶颈从付款前输入桥接进一步缩小为商家执行前写协调、可信确认及付款/提交恢复责任。H49 串行完成11入口审计、3机制比较、最小边界设计、14个未来验收设计、一个商业问题与统一L2；本包只读不实现，14项不是已执行测试。一次完成后必须选择有依据样机、商家合同改变或停止，不反复派泛化调研。10月18日复核ServiceNow官方发布：其签名权限/运行时授权/撤销/审计有重叠，AI Passport预计Q4；尚无本项目交易绑定运行证据，REFERENCE_ONLY，商业竞争权重提高但不替代B-17。支付宝、比赛继续Human延期，真实需求/预算UNKNOWN，外部运行/模型/Provider/对外联系与Git授权不变。下方r76及更早为历史。

2026-10-15 r76 H47 独立复核：**PASS / NOT_APPLICABLE；结束通用适用性测量，CONTINUE B-17 的 H48 受限确认接缝探针**。正式 L2/L3 均 5/5，18 条摘要一致，九种破坏拒绝、42+18 回归通过；接受的 120 个文件在 L3 后核对未变。固定完整商家原生已具签名、幂等与查询，C02 合法变更后完成只揭示与独立用户确认的集成缺口，不是官方漏洞。CORE_SEMANTIC_GAP 仅指到完整支付合同的缺口，不证明核心必须改；内部付款前 Order 不必等同完成后商家最终订单。B-17 缩小为“可信输入的付款前快照投影及真正执行边界”。H48 / one_off / CONTRACT_FROZEN / Executor：仅任务内纯投影，复用已有确认，正常必须完成、变更/缺证据必须拦，并保留检查后穿插更新和客户端旁路反例；不是生产适配或完整支付闸门。准备 Oracle 已测正常 ALLOW/一次处理、变更需重确认/零处理、检查后更新仍可完成两件；这不是执行者结果或新产品能力。三团队需求/预算仍 UNKNOWN，继续堆名单无益；不对外联系。支付宝、金密杯、支付马拉松继续延期，四项授权 false。旧 r75 以下为历史冻结/检查点。

2026-10-15 r75 冻结下一长程串行测量包：**CONTINUE B-17 / H47 / CONTRACT_FROZEN / one_off / Executor**。官方 UCP Python 商家固定 commit `99724a32...`、49 个原文和 30 包任务隔离环境；Evaluator 离线完整应用准备检查得到缺签名 401、正文篡改 400、创建 201、完成及同键重复 200/200，最终 1 个订单、模拟支付处理 1 次、库存 5→4；另测固定确认数量 1 后合法更新到 2 可行。就绪从 source-only 缩小到部分 measured，但正式九路径与完整产品适用性仍未测；原生已有幂等，不能预设我们有增量。按 Human 要求串行完成来源审计、九路径各重复两次、17 项字段/控制入口映射、三个公开团队的工作流/既有控制/问题假设、单一下一步结论及完整 L2，整包后一次 L3。产品核心不改、完整产品控制对照 NOT_MEASURED，不做新适配器或伪造字段。H46 PASS/STOP 不变；支付宝 B-06、金密杯及支付马拉松后置，外网/模型/Provider/对外联系零，Git 四旗保持 false。依据见 H47/EVALUATOR_ASSESSMENT.md；下方 r74 及更早“无新派发”为历史。

2026-10-11 r74 Human 优先级调整：**SWITCH TO B-17 / MEASUREMENT_FIRST / NOT_DISPATCHED**。下一第一瓶颈改为“外部商城交易链接入就绪与适用性未知”，从已筛选 UCP 商家样例与交易团队入手，技术先测忠实映射、执行接缝和可复算结果，商业并行核验具体工作流、问题、负责人及预算；不能用演示通过替代客户或 Provider 证据。支付宝 B-06 与金密杯按 Human 决策暂缓，已有成果保留、缺口不关闭；金密杯与安全主线有关，但当前机会成本高于补外部交易/客户证据，不作参赛投入。H46 PASS/STOP 和冻结合同不变，下一执行任务 NONE，API/Git 授权不变。方向依据见 `docs/02_未来规划/新商城接入与交易团队商业筛选_20261011.md`；下方 r73 及更早“第一瓶颈”是历史判断，以本次现行路线/登记表为准。

2026-10-11 r73 H46 统一复核：**PASS / NOT_APPLICABLE / STOP H46**。正式 L2/L3 均 5/5 PASS，八条状态相同，候选包六种破坏被拒绝，20+42 相关回归通过，60 个接受文件未变。结论仅为固定 AgentDojo 源片段/合成状态/脚本动作可复算及固定产品入口 SEMANTIC_GAP，不是模型攻击、完整闸门对照、Provider 或实际第三方成绩。准备时已有四状态与缺绑定探针证据，本次主要增加独立复算和候选材料核查，不能把全部结果写成未知变已知。B-16 本片段 STOP，整体 WATCH；不派银行 Adapter、不自动启动 H44/H45、不重开 A–E。B-06 重新明确为战略第一缺口，但仍受 fixture 合同与 Human 支付宝后置安排约束：当前无新的执行任务。冻结合同保持 r72 不变，CURRENT 标 H46 PASS。下文旧“当前”“未执行”按其日期理解，以下现行路线/登记表/第一瓶颈优先。

2026-10-11 r72 串行包派发：Human 要求执行包可稍长、整包后一次评估。冻结 H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1 / one_off / Executor，将固定来源、四状态源片段测量、产品适用性诊断、单一结论与候选复核材料串行完成；完整 L2 后统一 L3，不逐阶段等待 Evaluator。准备检查确认现有 Python/pydantic 可运行所选源片段；银行工具缺商业订单/币种/确认等输入，本包不伪造字段，不自动扩成完整 gate 对照。有效 SEMANTIC_GAP 是测量结果，继续归档；只有保护/权限/预算等硬停止才 BLOCKED。当前 B-16 第一测量瓶颈不变，B-06 支付宝继续 Human 后置；H44 模型对照/H45 正式第三方结果仍 DRAFT。准备检查不是 H46 PASS，尚无执行者 L2。下文带日期的旧派发为历史。

2026-10-11 r71 H42 独立复核：**PASS / NOT_APPLICABLE / STOP H42**，冻结 L2/L3 均 3/3 PASS，15+42 相关回归通过，八条测量记录一致。固定授权污染分支为 INDETERMINATE/p1:order_id_mismatch/callback0，两次一致；按错选候选重建确认则 ALLOW/callback1，仅作诊断。一个合成标题污染族的 unknown 已变 measured，不是产品改善或外部泛化，B-16 不关闭。当前可执行优先缺口转为 B-16 的外部任务来源、可信授权、真实模拟工具状态及判定器有效性；下一产物 H44/P0_READINESS.md 为 Evaluator-owned DRAFT，不派执行、不运行模型。B-06 仍缺有效 Provider Payment-Proof/绑定，按 Human 安排支付宝后置；H38 PARTIAL/LIVE_BLOCKED，H41/H43 STOP。相比追加同类 H42 输入，外部就绪测量信息收益更高；相比 H45 完整打包，必须先有已验收外部结果。API/Git 授权全 false。下文带日期的旧决策均为历史。

2026-09-30 r70 角色分离与下一派发：Human 要求恢复独立 Evaluator/Executor，H43 历史同会话实现/复核的限制保留。B-06 支付宝实证仍为战略高优先缺口，但暂无新的安全 fixture 路线；当前可执行第一测量瓶颈切 B-16。Evaluator 固定指令、价格、动作列表，仅改变网页商品标题，已实测 Agent 从商品 2 转为商品 1；同旅程源码按选中订单生成确认，故不能直接用于固定用户确认的攻击评估。冻结 H42 one_off/measurement-only：合成目录桥接真实确定性策略与现有 gate，良性/污染 × 固定确认/重建确认诊断 × repeat2，共 8 次纯内存测量；未授权 callback 结果仍 unknown。不改产品，不接模型或真实 WebShop，不调用支付宝。执行者实现测量脚本并交 L2，我仅冻结检查器和做后续 L3。下面 r69 及更早为历史。

2026-09-30 r69 H43 复核：冻结 L2/L3 均 4/4 PASS，合成已签名通用网关错误的本地安全分类 `0/1→1/1`；旧方法响应与负向护栏保持。H43 仅 `PASS / IMPROVED_LOCAL` 并 STOP，不补证 H41 原响应、不证明真实 Provider、Payment-Proof 或四维绑定。B-06 仍第一瓶颈，但本地错误解析不再值得继续堆 Case；H39 已测过 fixture 路线，H43 未改变其合同阻塞；无新增官方可执行路径时，不重复同类调研，先切 B-16/X1 Agent-facing 攻击接缝测量。H38 `PARTIAL / LIVE_BLOCKED`，API 授权继续 false。下面 r68 是派发时判断。

2026-09-30 r68 下一执行决策：B-06 仍为第一瓶颈，不因 H41 失败而直接切比赛或横向攻击。新只读官方来源复核发现官方 SDK 同时处理接口专属响应与通用 `error_response` 的签名原文；本地适配器仅接受前者。Evaluator 用临时合成 RSA 正对照独立复现：合法签名通用网关错误当前 `0/1` 可识别；这**不能证明** H41 原 HTTP 200 就是该格式（原始响应未保留），却是直接影响后续 Provider 错误证据的可复现本地断点。冻结 H43 为 `SINGLE / capability_experiment / OFFLINE_ONLY`：仅在 Alipay adapter 中安全识别签名通用错误，目标 `0/1→1/1`，同时无效、篡改、重复键、双外壳与旧方法响应全部守住；API/密钥/造单/付款预算零。H42/B-16 草案降为备选；H43 通过后再比较安全 fixture 路线，不自动授权 H38 live。由于官方沙箱收银参考路径仍有 HTTP、占位买家签名及重试，不能靠“看过网页”直接执行它。下文 r67 为历史检查点。

2026-09-30 r67 密钥来源补证：Human 的同一沙箱应用控制台截图现完整显示“支付宝公钥”；Evaluator 将其五行可见文本与本地文件逐段视觉比对一致，记录为 `CONSOLE_SCREENSHOT_VISUAL_MATCH`，非控制台复制文本的机器级哈希比对。“没有支付宝公钥”或“完全没有来源证据”均不再成立；先前 B-06 叙述中的公钥来源疑点已明显缩小。战略瓶颈仍是 B-06 的有效 Payment-Proof / Provider 结果 / 绑定闭环：H41 原响应未留存，`INVALID_RESPONSE` 不能倒查，一次预算已耗尽；H39 的安全 fixture 获取路线仍未闭合，不能仅因公钥匹配就重试或造单。下一可执行候选 H42/B-16 仍仅为设计草案；若找到不越过 H39 安全边界的 fixture 路线，应重新比较其项目价值。下文 r66 为前一检查点。

2026-09-29 r66 当前裁决：A–D 已完成，E 本地代表性闭环，F 仍是战略瓶颈 B-06。H41 唯一一次合成 Sandbox 请求得到 HTTP 200，但探针分类 `UNVERIFIED_RESPONSE / INVALID_RESPONSE`，预算已消耗；无法由脱敏证据分辨缺签名、验签失败或结构错误，不构成 Provider 签名、有效 Payment-Proof、支付或绑定证据。H38 继续 `PARTIAL / LIVE_BLOCKED`，H41 `STOP` 且不得重试。B-06 仍最重要，但目前缺可验证公钥来源及安全有效 fixture/新增授权，暂无可执行的下一 live slice。下一可执行候选改为 B-16/X1 的 Evaluator-owned measurement-only 接缝设计：先确认真实不可信 Agent observation 是否进入 action 和 governed gate；现有 Attack Overlay `6/6` 为预声明字段覆盖，不等于 Agent-facing 对抗验证。H42 仅 `DRAFT_CONTRACT`，不派执行、不改产品、不增加外部调用。下文 r65 及更早“P1 可调用 / B-16 等 H38 live 后再开”等叙述均为历史检查点，不代表现行授权。

## Project outcome / 项目结果

### 可观察的项目结果

在本地、离线、可重置的实验边界内，证明智能体代表用户完成购物与支付任务时：

```text
用户授权
→ Agent / 外部环境产生动作和事实
→ 订单、支付请求、身份、来源和状态持续绑定
→ 每个副作用前经过统一治理闸门
→ 正常任务正确完成
→ 越权、冲突、缺证据任务被阻断或要求确认
→ 支付、履约、恢复和最终状态可回放、可解释、可独立复核
```

### 主要用户与业务价值

- 给开发者提供一个协议中立的智能体支付可信实验室；
- 用可运行环境说明“为什么允许、为什么阻断、为什么需要确认”；
- 用外部任务和固定评测避免“自己出题、自己判卷”；
- 为后续接入 WebShop、x402、UCP / ACP、银行沙箱提供可复用的治理和评测底座。

### 风险容忍度与禁止失败

以下失败采用零容忍守护线：

```text
错误放行产生受控 callback 或支付副作用
漏掉必须的人工确认
重复下单、重复付款或 UNKNOWN 状态下盲目重试
低可信网页、LLM 或工具事实静默覆盖用户确认事实
动作、订单、请求、支付、Agent、Executor 或授权错绑
没有前置治理证据的副作用
```

### 当前评测边界

包含：

- 本地 Python 确定性规则与回归；
- S01—S13、M5、PayBench、AP2、Attack Overlay；
- P1—P6 Trust Control Plane；
- x402 离线一致性；
- WebShop 上游预检、small smoke、Commerce Adapter、Buy Now Gate、Payment / Fulfilment Sidecar；
- 已验收的 Governed Action、Fact Lineage、Payment Lifecycle / Recovery、Remediation / Closure、Authoritative Trace Consumer / Player；
- B-15 Actor Authenticity（主体真实性）已在本地离线边界形成代表性闭环；H-30 已把 PayBench Data Minimization（数据最小化）从 `8/10` 补到 `10/10` 可执行；H-31/H-32 已关闭 B-03 T05/T06 Trace 与 T10 baseline drift。B-06仍缺支付宝第二Provider实际证据、Human后置；H47/H48/H49设计、H50R2方法修复及H51离线HTTP接线已分别验收并停止对应切片，真实消费者/确认来源/部署责任仍未知。

明确不包含：

- 真实资金、真实信用卡或生产支付网络；
- 生产商户、生产凭证、主网资产；
- 完整 Agent PKI 或生产身份认证；
- 未授权的外部 API、测试网、钱包和网络调用；
- 对生产安全、监管合规或业务合法性的证明。

## Global capability roadmap / 全局能力路线

评估者以后先从这 6 个大阶段定位项目，再看具体 `B-* / H-*`。任务编号不是路线，能力阶段才是路线。

```text
A. 评测与治理底座                  [已完成]
→ B. 授权、绑定、来源、执行前治理   [已完成]
→ C. 支付生命周期、恢复、补救证据链 [已完成]
→ D. 责任归因与可消费审计链         [已完成]
→ E. 主体真实性 / 凭证 / 签署指令   [本地代表性闭环已完成]
→ F. 外部真实协议 / SDK / 网络接入   [CURRENT：B-17 / H61只读测量已验收并STOP；H62批准后订单侧恢复实验；H56未执行，支付宝/比赛延期]

横切补强：B-05 Data Minimization（数据最小化）【本地阶段关闭】
B-03 Product Authoritative Trace（产品权威轨迹）【固定 12 项覆盖已闭合】
纵向缺口：F/B-06 的支付宝有效 fixture、Provider Payment-Proof 与绑定实证【PARTIAL / LIVE_BLOCKED / Human 后置】。H42【PASS / STOP，仅单一合成输入测量】；B-16/H46 外部离线证据链【PASS / STOP，本源片段已结束，B-16 整体 WATCH】。H43【PASS / STOP】，H41 单次请求【STOP】，旧放行记录均为历史。
横向安全轨：固定负例 → Agent-facing attacks → 外部可判定任务 → Adaptive Model Red Team → Cross-Provider Adversarial Eval【当前无新派发；H46 未完成完整闸门/模型对照，模型/API 预算零】
```

历史检查点（r61，原判断不提供当前执行授权）：2026-09-22 r61 决策依据见 `docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/EVALUATOR_DECISION.md`。当前第一瓶颈仍为 B-06：缺第二 Provider 的实际证据；H41 先分离传输/响应签名问题与交易 fixture 问题。P1 错误响应验签成立只关闭该窄层；无签名、网络不确定或意外成功则 STOP 并按证据选择路线，不追加请求。AP2 扩展与横向攻击继续 WATCH；不把 H41 包装成 H38 通过。

| 阶段 | 要解决的核心问题 | 当前代表能力 / 证据 | 状态 |
|---|---|---|---|
| A 评测与治理底座 | 怎么知道一次修改真的让项目变好，而不是测试数量变多 | 12 项项目基线、GESR、零副作用守护线、Evaluator / Executor、L2/L3 独立复核 | `CLOSED` |
| B 授权、绑定、来源、执行前治理 | Agent 能不能在明确授权、正确对象、可信来源下安全触发副作用 | P1 Delegated Authority、P2 Payment Binding、P3 BOUND Identity、P4 Context Policy、Governed Action、Fact Lineage、重复付款保护 | `CLOSED` |
| C 生命周期、恢复、补救证据链 | 支付后 UNKNOWN、履约失败、退款、争议、原交易错绑时能不能安全恢复并留下连续证据 | Payment Lifecycle / Recovery、Finality、Remediation / Closure、Product Authoritative Trace `10/12`，B-12/B-13 阶段关闭 | `CLOSED` |
| D 责任归因与可消费审计链 | 事后能不能回答“谁做的、依据什么、发生了什么”，并让 UI / 审计消费者稳定读取 | Action Origin、Same-Journey Responsibility、Consumer、Read Model、Player；H-23 五分支消费 `5/5` | `CLOSED` |
| E 主体真实性 / 凭证 / 签署指令 | ID 对得上之后，能否证明执行者真的持有对应凭证/密钥，授权/指令真的由对应主体签署 | B-15A 已由 ACP/HMAC + AP2/ES256 两个消费者闭合；B-15B 已由 bounded X.509-SVID + proof-of-possession + challenge binding 形成首个受控 `BOUND→VERIFIED` 路径 | `CLOSED_WITH_LOCAL_BOUNDARY` |
| F 外部真实协议 / 网络接入 | 本地机制在真实 SDK、Sandbox、Provider 下是否仍成立 | AP2 v0.2.0 已完成 compatibility → boundary → official SDK → official two-hop crypto/delegation；H-38 转支付宝 Agent Pay Sandbox，验证第一条 provider-observed payment-proof evidence | `ACTIVE` |

### 已完成的能力，不再默认继续扩

- 项目级同基线评测与独立复核；
- Delegated Authority（委托授权）、Confirmation Binding（确认绑定）；
- Order / Request / Payment 连续 Binding（绑定）；
- Agent / Executor `DECLARED / BOUND` 身份保证边界；
- Context / Tool Integrity（上下文 / 工具完整性）与来源策略；
- Idempotency / Replay（幂等 / 重放防护）、UNKNOWN 查询恢复、支付最终性 / 状态冲突；
- Governed Action（受治理动作）与 Fact Lineage（事实血缘）；
- Same-Journey Responsibility（同旅程责任链）；
- Payment Lifecycle / Recovery（支付生命周期 / 恢复）；
- Refund / Dispute / Closure（退款 / 争议 / 结束状态）证据连续性；
- Product Authoritative Trace（产品权威轨迹）的代表性覆盖；
- Consumer / Read Model / Player（消费器 / 读取模型 / 播放器）只读审计消费链。

### 当前与后续能力

阶段 E 已在本地、离线边界形成代表性闭环：

```text
B-15A Signed Instruction Verification（签署指令验证）【STAGE CLOSED】
  → ACP/HMAC + AP2/ES256 两个独立消费者复用同一通用验证事实

B-15B Credential / Possession Verification（凭证 / 持有证明验证）【LOCAL STAGE CLOSED】
  → credential_ref-only 仍为 BOUND
  → bounded X.509-SVID + subject binding + proof-of-possession + freshness/replay 可产生受控 VERIFIED
  → H-29R 已关闭 signed challenge metadata relabel replay
```

阶段 E 的剩余真实 Provider、生产 credential/key、live SPIRE / PKI / OIDC / DID / VC 统一归入 B-06 / 阶段 F，只有出现明确外部环境与授权后再进入；不为了增加 Provider 数量继续扩本地 synthetic verifier。

H-30 已把 B-05 Data Minimization（数据最小化）的本地字段名级代表性缺口关闭：PayBench current rules 从 `8/10 executable` 提升为 `10/10 executable + 10/10 PASS`，非 D1 八题保持不变。完整 Privacy Governance、真实 PII 与监管合规仍明确不在当前能力声明内。

### 第一瓶颈选择公式 / 决策顺序

```text
项目最终目标与零容忍风险
→ 哪个大阶段还没有代表性闭环
→ 该缺口影响范围 / 风险严重度
→ measured / estimated / unknown 的证据强度
→ 是否有重复共同失败，而不是单一 Case
→ 修复成本、复杂度、外部授权依赖
→ 与 WATCH / DEFERRED 备选项比较 expected project value（预期项目价值）
→ 选第一瓶颈
```

历史 H31 派发依据（已由 H31/H32 关闭，不代表当前优先级）：

- B-05 已由 H-30 `PASS / IMPROVED` 达成本地阶段关闭，不继续扩完整隐私治理；
- B-04 Fresh Unseen Agent 行为已有真实长尾基线，但项目已明确不沿逐 Case 意图/规格优化继续主线，保持 `WATCH（观察）`；
- B-06 真实 SDK / testnet / network 依赖额外授权与环境，保持 `DEFERRED（延期）`；
- B-03 是当前唯一明确且无需外部授权即可闭合的固定项目缺口：T05/T06 的 decision、binding 与 callback 已正确，共同只缺 action-binding rejection 的产品权威轨迹，Product Trace=`10/12`、GESR=`9/12`。
- 下一包严格只补证据连续性，不修改 T05/T06 业务决策，也不把独立的 T10 lifecycle/duplicate semantic gap 混进来。

## End-to-end capability chain / 端到端能力链

```text
用户任务 / 授权
→ 外部协议、Agent 或 WebShop 环境
→ Commerce / Protocol Adapter
→ Governed Action + Explicit Facts
→ Authority / Order / Request / Payment / Identity Binding
→ Source Registry / Fact Lineage
→ Context Policy + Runtime Authorization Gate
→ ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE
→ Controlled Action Seam
→ Payment / Query / Fulfilment / Recovery
→ Authoritative Trace / Replay
→ M5 + 外部任务 + 项目级影响评测
```

## Measurement basis / 测量基础

### 已固定或已独立复核的组件基线

| 边界 | 当前事实 | 性质 | 证据入口 |
|---|---:|---|---|
| S01—S13 正式入口 | 13/13 PASS | measured | `python run_experiment.py` 与历次独立复核证据 |
| Governed Payment Action 类型边界 | 18/18 动作矩阵，13/13 专项，31/31 Runtime Gate | measured | `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_OBJECT_TYPE_BOUNDARY_REPAIR_V1/REVIEW.md` |
| 全量 unittest | 703/703 PASS | measured | `P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1/REVIEW.md` |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 10/10 可执行且 10/10 PASS | measured | `P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1/REVIEW.md` |
| x402 离线一致性 | 第一轮已完成 | measured but bounded | P8-A 任务合同、报告与复核 |
| 多步骤自主购物项目级指标 | 12 项固定任务；GESR 9/12；重复/禁止副作用 0/12；callback 匹配 12/12；产品权威轨迹 10/12；三次结果一致 | measured | `P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/REVIEW.md` |

### 主要指标

`Governed End-to-End Task Success Rate`：

```text
同时满足以下条件的固定端到端任务数
────────────────────────────
固定端到端任务总数
```

单个任务必须同时满足：

1. 最终环境状态正确；
2. 四态决策正确；
3. callback / 副作用次数正确；
4. 必要确认没有遗漏；
5. 动作、授权、订单、请求、支付、身份和来源证据连续；
6. 轨迹与 reason codes 能解释最终结果。

### 守护指标

| 指标 | 目标线 |
|---|---:|
| 错误放行率 | 0 |
| 漏人工确认率 | 0 |
| 重复副作用率 | 0 |
| 禁止状态写入率 | 0 |
| 来源链完整率 | 100%（在纳入 lineage 的任务内） |
| 权威轨迹完整率 | 100%（在纳入 trace 的任务内） |
| 决策—原因一致率 | 100% |
| 既有正式入口 | 不低于 13/13 |
| 既有全量回归 | 不允许出现新增失败 |

### 测量命令或证据路径

当前组件回归可复用：

```text
python run_experiment.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

项目级端到端基线已冻结为 12 项固定任务和 `run_project_impact_baseline.py`，可用于同 target 的 capability experiment（能力实验）前后比较。B-11—B-15 与 B-05 已分别完成责任链、生命周期 / 恢复、补救 / 结束状态、Consumer / Player、本地主体真实性和字段名级数据最小化的代表性闭环。H31/H32 后固定基线 GESR / evidence / Product Trace 均为 `12/12`、gap=0、repeat=3；此前 `10/12` / `9/12` 是 H31 前的历史快照，不再代表当前本地缺口。本次 H46 只复跑相关 62 项测试，没有重新测量整个项目基线。

### 已知盲区

- 当前测试数量增长不能直接等价为项目能力增长；
- H-14 当前 `5` 个 synthetic/metamorphic probe（合成 / 变形探针）只覆盖**已经暴露出来的规格失败机制**，不是 option-grounding（规格匹配）能力全集；即使达到 `5/5`，也只能证明当前假设在冻结代表样本上成立，不能声称“规格问题已经测全”；
- 规格能力仍存在未系统发现的组合空间，例如同义表达、大小写/空格/标点变化、单位与数字格式、多个干扰选项、多个规格组、缺失规格、歧义候选、页面顺序变化、部分匹配与冲突请求；这些未知细节不能靠人工逐条穷举，而要用 property/metamorphic testing（性质 / 变形测试）系统发现；
- 已揭晓 Blind Holdout 只能作为回归证据；任何新的“泛化成立”结论都必须来自下一轮产品修改前冻结的 fresh unseen evidence（新鲜未见证据）；
- WebShop 已形成多个离线切片，但还没有冻结统一的多步骤 Agent 任务集；
- 当前没有生产网络、真实支付、真实身份和真实 LLM 行为；
- PayBench D1 字段名级数据最小化已由 H-30 覆盖，但真实 PII、retention、日志脱敏、跨 Provider 传播、监管分类与 DLP 仍未覆盖；
- 当前多数结果是组件或局部纵向切片结果，不是统一项目指标；
- 冻结 runner 的 `trace_provenance_separated` 诊断只在“产品轨迹不存在”时返回真；T10 同时存在产品轨迹与评估器 Replay 后产生误报。原始来源字段已明确分离，下一包先修复该测量诊断，再扩展第二个产品轨迹场景。

## Bottleneck register / 瓶颈登记表

| ID | 阶段 | 可观察失败 | 估计影响范围 | 证据 | 信心 | 状态 |
|---|---|---|---:|---|---|---|
| B-01 | 项目级评测 / V3 环境 | 固定 12 项任务、统一 runner、独立副作用护栏和轨迹来源分类已建立；H-32 已将 T10 主 fixture 对齐到此前独立验收的 preflight 安全语义 | 固定 12 项当前全部匹配；GESR / evidence completeness / Product Trace 均 12/12 | H-32 Evaluator REVIEW：L3 `6/6 PASS`、708/708；T10 保持 `DENY/callback0/BLOCKED`，仅修 5 个 stale expected 字段；repeat=3/3 | high | RESOLVED / BASELINE_RECONCILED |
| B-02 | Fact Lineage | 组件级来源传播已通过，但尚未测量它在固定端到端任务中减少了多少来源丢失、错误放行或证据缺口 | 所有包含派生事实的外部环境任务；具体比例 unknown | P9 Fact Lineage REVIEW：16/16 矩阵、12/12 专项、Overlay 投影不变 | medium | WATCH / IMPLEMENTED_UNMEASURED |
| B-03 | Authoritative Trace | H-31 已补齐 T05/T06 action-binding rejection trace，固定 T01-T12 均有 `VALID` 产品权威轨迹；T05/T06 决策/binding/callback 原样保持 | 固定 12 项 Product Trace `12/12`；当前无剩余 trace coverage gap | H-31 Evaluator REVIEW：L3 `8/8 PASS`、708/708、PayBench 10/10、S01-S13 13/13；Product Trace `10/12→12/12`、GESR `9/12→11/12` | high | RESOLVED / FIXED_12_TASK_TRACE_COVERAGE |
| B-08 | Trace Consumer / UI Read Model | 通用只读 Consumer 与 Trace Player 已贯通：T01/T02/T07/T10 四类代表轨迹均可由同一 Read Model 进入同一只读 UI，事件、relation、source binding 可机械回指 | 当前 4 个已验证结构族；UI-ready 4/4 | P9 Authoritative Trace Player REVIEW：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready 0/4→4/4 且旧轨迹/UI/Consumer hash 不变 | high | RESOLVED / TRACE_PLAYER_READY |
| B-09 | WebShop Journey 多事实源合同 | WebShop runtime、experiment context、Commerce Adaptation、payment authoritative trace 四类证据已能在一个 deterministic Journey Read Model 中分层保存并机械关联；错绑 fail closed | 第一轮 1 条固定 WebShop smoke/T01 正常购买路径，Journey source-classified 1/1 | P9 Journey Fact Source Read Model REVIEW：27/27 专项、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；17 条 correlation 全 true，来源边界不变 | high | RESOLVED / SOURCE_CLASSIFIED_JOURNEY_READY |
| B-10 | WebShop Journey UI composition | 固定脚本 Journey 已能按来源安全进入一个 deterministic Player；accepted-input schema/source-classification 两个反例已全部 fail closed | 第一轮固定脚本 Journey UI-ready 1/1 | Journey Player 父任务合法路径 1/1；accepted-input repair L2/L3 4/4、Player 27/27、两个反例 4 个入口组合全拒绝 | high | RESOLVED / SAFE_JOURNEY_PLAYER_READY |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 已形成真实多步骤 autonomous behavior、H-12 `5/5` 开发/回归证据、Blind Holdout `3/8` 泛化边界、H-14 通用修复与 Systematic Discovery `19/24`；已证明 Agent 可产生真实行为，也证明意图/规格存在难穷举长尾 | 当前价值已从“继续提高购物理解准确率”转为向信任链提供真实 Agent 行为与已知限制；H-15 `2/5` probe 保留为回归资产，不再阻塞主线 | H-14 `PASS / IMPROVED`；Systematic Discovery `PASS / NOT_APPLICABLE`、L3 `4/4 PASS`、48 observations all reproducible、safety hits 0；H-15 在 Executor 开始前 superseded | high | WATCH / BEHAVIOR_BASELINE_ESTABLISHED |
| B-11 | Action Origin / Responsibility Trace | H-13 已完成 Action Origin `0/5→5/5`；H-17 修正跨 policy 版本基线后，同一 autonomous journey 的 Agent→Order/Request→Runtime→offline Payment/Fulfillment→Trace 连续关联 `8/8`，五类 origin 可投影 | 代表性 happy-path responsibility chain 已闭合；不再继续扩 Action Origin 字段 | H-17 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `8/8 PASS`、same-journey `8/8`、657/657 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-12 | Same-Journey Payment Lifecycle / Recovery Continuity | H-20 已将 H-18 三个同类证据链断点统一闭合：semantic `4/4` 保持，continuity `1/4→4/4`，四条 Trace 均 VALID 且 Action Origin 可投影 | L5-L7 支付执行、状态、恢复、冲突与履约的代表性同旅程证据连续性已闭合 | H-20 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`、Product Trace `9/12→10/12`、GESR `8/12→9/12`、658/658 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-13 | Same-Journey Remediation / Closure Continuity | H-21 定位 5/5 共同补救证据断点；H-22 以一个通用 extension 将 remediation evidence `0/5→5/5`、continuity `0/5→5/5`；H-22R 又使 public runtime fingerprint 与 live validator contract 完全一致，R05 全程保持 `INVALID` | 支付后退款/争议/原交易绑定/Closure 的代表性同旅程证据生产与合同身份已闭合，不再继续扩 R01-R05 或补救产品字段 | H-22R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；effective projection/profile/runtime hash 全部与 live contract 一致；H-22 复验 SHA-256 完全相同；662/662、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-14 | Remediation Accountability / Closure Consumption | H-23 已对冻结 5 个补救分支完成现有 Product Trace → Consumer → Read Model → Action Origin → Player 系统测量；Consumer/Player/continuity 均 `5/5`，R05 `INVALID` 原样可见且无虚假 payment relation | 代表性退款/争议/原交易错绑证据已经可被现有通用只读消费链稳定消费，无需新增 Consumer/Player 特判 | H-23 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `7/7 PASS`，first breakpoint=`NONE:5`，51/51 专项、662/662 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-15 | Actor Authenticity / Credential / Signed Instruction Verification | B-15A 已由 ACP/HMAC + AP2/ES256 形成跨协议/跨算法两个 Signed Instruction 消费者；B-15B 已由 bounded X.509-SVID + subject binding + proof-of-possession + freshness/replay 形成首个受控 `BOUND→VERIFIED` 路径，H-29R 关闭 metadata relabel replay | 当前本地、离线真实性边界已具代表性闭环；真实 Provider / 生产凭证 / live identity 迁入 B-06 | H-29R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；relabel counterexample fail closed；H-29 `7/7` 保持；30/30 focused、699/699 full unittest、项目 guardrails 不退化 | high | RESOLVED / LOCAL_REPRESENTATIVE_CLOSURE |
| B-05 | 数据最小化 | H-30 已建立协议中立 `DataDisclosureFact`，机械比较 required / allowed / requested；D1 Trap 阻断非必要字段但保持购买可执行，Lookalike 必要字段正常 | PayBench 字段名级隐私挑战 `8/10→10/10` 可执行；完整 Privacy Governance 仍不在当前范围 | H-30 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，L3 `8/8 PASS`；PayBench `10/10 PASS`，703/703，全项目守护线不退化 | high | RESOLVED / LOCAL_STAGE_CLOSED |
| B-16 | 横向攻击验证 / Agent-facing 安全测量 | H42 单合成标题族已测；H46 固定银行源片段/脚本状态可复算，但固定完整产品入口语义不匹配，无共同产品失败 | 本源片段适用性/候选材料已核查；完整控制对照、同订单字段篡改和真实模型仍未测；下一轮信息收益不足 | H42 REVIEW；H46 REVIEW、L2/L3 5/5、六种候选包负例与接受快照 | high（本片段事实）；unknown（完整外部有效性） | WATCH / H46_SOURCE_SLICE_STOPPED |
| B-06 | 真实身份与外部协议 | AP2 官方两跳验证已闭合；H43 本地通用错误分类已改善；支付宝有效 Payment-Proof/绑定证据仍缺 | H39 安全 fixture 路线需独立合同；H41 已停止，未取得可信 Provider 结果；Human 暂缓支付宝 | H38 PARTIAL/LIVE_BLOCKED，H43 PASS/STOP；2026-10-11 Human 优先级调整，不关闭缺口 | high | DEFERRED / EXECUTION_BLOCKED / HUMAN_DEFERRED |
| B-17 | F / 商城业务补救链 | M06付款1/订单0；批准已登记、订单侧逻辑存在但缺安全消费协议 | 单次批准→原生订单/库存/收据提交、撤销先后与崩溃恢复未实现 | H61 L2/L3各6/6、57文件与19表独立核对；H62实现实验冻结 | measured（断口）；unknown（新消费者/现实采用） | ACTIVE / APPROVED_ORDER_RECOVERY_SEAM |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-17

当前第一瓶颈仍B-17。r100接受H61只读结果并STOP同一材料盘点：旧complete因claim拒绝，订单事务没有批准消费收据，两库读写没有串行协议。下一H62用一个显式本地消费者复用原生订单事务，订单/库存/收据同提交，恢复零付款，批准与全部撤销入口同锁序。与保持查询比较，只有本包能对已观察订单0产生可测增量；比第二商城/通用SDK/全量平台接线更少范围和授权依赖。已有共享适配器/校验器与跨算法第二消费者，不据架构焦虑重做；确认辅助函数职责混放及README漂移未形成运行安全反例，登记为非主线。本包仍本地合成，成功后STOP切片再按真实消费者需求重排，不自动扩通知/售后平台。

H55继续STOP重复测量，H56未执行且不再是当前派发。H57选择已接受本地2026-04-08/H53R闭合输入流，不把未接受的新标准消费者接付款，也不要求先建自定义完整性profile。只把正常工厂接回原有控制、真实走原生HTTP/DB/假PSP，6业务旅程分别验证能完成、能拦、重放不多付、失败可查不重扣。其收益直接可由默认工厂0→1完整正常交易衡量，高于再扩非标准字段；标准互通/任意授权语义/真实来源仍unknown。若原HTTP拿不到必要输入或需改业务，则按实际断点停止，不悄悄DB补字段或全面迁移。四旗false，支付宝/比赛延期保持。

历史检查点（r57）：2026-09-21 核对 CURRENT、H39 REVIEW 与实际 probe，R1–R3 已 PASS，R4 仍未实现；四个继承 H38 文件 hash 仍与 H39 BASELINE 一致。冻结 H40 bounded repair，仅补在线入口的当前任务/显式授权检查及 fake-transport 验证，不运行网络、读取真实密钥或创建交易。H40 验收后必须处理 Route A 的精确 transport、proof 来源、内存交接和绑定字段限制，才能冻结上游执行合同。Human 目前无需补信息；不是重复索要密钥。AP2/VI/横向攻击不抢占本前置缺陷；支付宝阶段验收后按既定顺序进入 VI measurement。

历史检查点（r56）：H-38 adapter 16 项与 evaluator 14 项离线测试通过，主场景 13/13 和项目基线通过；全量 749 项中 738 passed、10 skipped、1 Windows WebShop 路径断言失败。已取得用户授权的沙箱密钥并完成本地配对/签验，仍无 live Provider 证据。第一断点细化为交易 fixture 获取路径、Agent Pay 可用性及 proof/四维绑定语义。冻结 H-39 measurement-only，先确定官方路径、最小输入和合同差异；不新增产品、不创建交易、不调用验付。AP2 typed semantics / Receipt 与 B-16 继续 WATCH。READY 路径交 Evaluator 冻结上游操作后恢复 H-38；缺字段或不支持则 STOP/SWITCH，不降低验收。

### 当前判断

最近验收H61 PASS/NOT_APPLICABLE/STOP：正式L3六项，独立提取1/2；L2/L3十源文件、三库19表相同，57签收文件/2625保护文件及24原始流保持。H60R和父H60原结论保留。H62四产品文件实验已冻结，尚未实现或运行。

H-32 已由 Evaluator 独立 L3 复核通过：

```text
Task verdict: PASS
Project impact: NOT_APPLICABLE
L3: 6/6 PASS
full unittest: 708/708
PayBench: 10/10 PASS
S01-S13: 13/13 PASS
matched: 12/12
GESR: 12/12
evidence completeness: 12/12
Product Trace: 12/12
gap: []
```

T10 产品行为没有被修改，仍是 `DENY / callback0 / preflight BLOCKED / trace VALID`。H-32 只把主项目 baseline 的 5 个旧 expected 字段对齐到此前已经独立验收的 B-07 target，因此 `GESR 11/12→12/12` 属于 corrected measurement，不是新增产品能力。

F0R 已由 Evaluator 独立 L3 复核通过，并由 F1 继续向 official SDK/types 前移。

F1 最新正式结果：

```text
Task verdict: PASS
Project impact: IMPROVED
Continuation: CONTINUE
L3: 9/9 PASS
Official SDK cases: 9/9 PASS
F1 focused: 10/10 PASS
H-34 boundary: 10/10 PASS
existing AP2: 17/17 PASS
project baseline: 12/12 repeat=3
full unittest: 731 OK (10 expected SDK skips)
protected Core: 11/11 unchanged
```

H-35 证明官方 AP2 v0.2.0 generated model objects 可以通过极薄 SDK Bridge 复用 H-34 gate 并进入现有 Canonical Facts，不需要 AP2-specific Core branch，也不需要让产品模块直接依赖 `pydantic/ap2`。

H-37 已由 Evaluator 独立 L3 `8/8 PASS`，因此 B-06 的 official two-hop runtime 断点已清除：AP2 pinned SDK/crypto 在本地隔离环境中已有正向与七类负向运行证据。B-06 仍未关闭，但第一断点已前移到 **第二个真实外部 Sandbox/Provider 能否在不使用真实资金的前提下产生 provider-observed request / payment-proof verification / callback-state evidence，并进入现有 Trust / Trace 边界**。继续补 AP2 Checkout/Payment typed semantics 或 Receipt 保持 WATCH，不作为当前第一优先。

### 当前主线

```text
A-D【STAGE CLOSED】
        ↓
E. Actor Authenticity【LOCAL REPRESENTATIVE CLOSURE】
        ↓
LOCAL REPRESENTATIVE BASELINE【12/12 CLOSED】
        ↓
F. External Protocol / SDK / Provider【CURRENT】
        ↓
F0 AP2 v0.2.0 Compatibility Measurement【PASS】
        ↓
F0R Bounded AP2 Adapter Protocol Boundary Gate【PASS / IMPROVED】
        ↓
F1 AP2 Official SDK Executable Slice【PASS / IMPROVED】
        ↓
H-36 Official Crypto/Delegation Boundary Measurement【PASS / DEPENDENCY_BLOCKED】
        ↓
H-37 Two-hop Official Verification Slice【PASS / IMPROVED】
        ↓
H-38 / F2 Alipay Agent Pay Sandbox First External Slice【PARTIAL / LIVE_BLOCKED / HUMAN_DEFERRED】
        ↓
B-17 External Commerce Enforcement【H57R接线、H58/H61测量及H60R登记已接受；H62批准后订单恢复CURRENT】
        ↓
H52 UCP/AP2 Readiness【PASS / NOT_APPLICABLE / STOP；12观察一致、L3 8/8、商家消费合同变化必要】
        ↓
H53 Merchant Authorization Consumer Contract【REJECTED / AC-02；固定28保持，独立终结链反例失败】
        ↓
H53R Terminal Chain Shape Repair【PASS / NOT_APPLICABLE / STOP本地消费切片；34固定+7形状通过】
        ↓
H54 Standard CheckoutMandate Consumer【REJECTED / INCONCLUSIVE；固定36通过，外层cnf两反例误VERIFIED】
  ↓
H54R Nondelegating Checkout Root Repair【PASS / NOT_APPLICABLE / STOP已披露根条件修复；39固定+6泛化保持，V07另记】
  ↓
H55 Disclosure Completeness Measurement【PASS / NOT_APPLICABLE / STOP重复测量；12观察一致，三机制范围收窄】
  ↓
H56 Trusted Disclosure Profile【冻结文件保留/未执行/安全支线；非当前派发，需真实商家需求后重评/重冻结】
  ↓
H57 Default Factory Merchant E2E【REJECTED / INCONCLUSIVE；历史不回写】
  ↓
H57R Evidence / Process Exit Repair【PASS / NOT_APPLICABLE / STOP；正式L3 7/7、六原生旅程、进程内核观察】
  ↓
H58 Paid Order Gap Measurement【PASS / NOT_APPLICABLE / STOP；L3 6/6、两库17表双遍一致、零业务执行】
  ↓
H59 Local Remediation Disposition Decision【RESOLVED_BEFORE_EXECUTION；Human选择人工批准入口，无实验PASS】
  ↓
H60 Local Operator Reconciliation Approval【REJECTED / INCONCLUSIVE；文件别名可写来源】
→ H60R Source/Ledger Isolation【PASS / STOP；本地批准登记切片接受，非订单恢复】
→ H61 Approval Consumer Seam【PASS / STOP，只读接缝证据已验收】
→ H62 Approved Order Recovery【CONTRACT_FROZEN / Executor；共享订单事务+唯一收据，未实现】
交易团队问题与需求仍未知；支付宝与比赛【HUMAN_DEFERRED】
```

## Active hypothesis / 当前假设

Hypothesis ID: H-62
Hypothesis status: CONTRACT_FROZEN / SINGLE / EXECUTOR；显式批准消费、共享原生订单事务与唯一交易收据，可使同源M06订单0→1且恢复额外付款0，撤销先后/崩溃/重放/并发不产生第二订单或扣库。成功阈值：16恢复、24批准、6原生旅程与25AP2全通过且保护不变；无增益/拒绝或重复副作用即不接入、回query-only，360主动分钟/2L2耗尽或需范围外改动则STOP，预算不重置。

历史已验证H-57命题：明确应用配置和原生get_checkout_service装配已有ExecutionControl，即可在不替换默认工厂/路由/业务的前提下，通过现有商城HTTP创建、完成、重放和查询，同时保留确认/授权拒绝与失败后不重扣。一个接线主要变更，只工厂体+新guarded_app；6旅程/7计划、240分钟/2L2/160请求，Evaluator另80。before为相同默认工厂201/409/0付款，after须实际HTTP/DB/独立假PSP证明，非字段测试数。标准授权消费者/现实部署不在主张内，成功后按业务断点重新选择，不自动回安全支线。

H46 已回答：固定源片段、合成账户/授权与脚本动作能够形成可复算的三类判定及候选材料，固定完整入口存在 SEMANTIC_GAP；未测完整闸门/模型对照，没有共同产品失败。冻结前已有部分 oracle 实测，本次主要增加正式交付与独立核查。STOP 该片段，H44 模型草案与 H45 正式结果包仍 DRAFT；不自动派后续任务。下文 H43 等为历史。

历史 H43 假设：仅让 Alipay adapter 严格验签并分类通用 `error_response`，从本地合成基线 `0/1` 到 `1/1`，同时确保其绝不成为有效支付。H41 原响应格式仍 unknown；下文 H35–H38 前提与候选表为历史决策记录，不提供新的 live 授权。

### 已验证前提

H-35/F1 已证明：AP2 v0.2.0 官方 generated model objects 可以通过极薄 SDK Bridge 进入 H-34 protocol-boundary gate，再进入现有 Canonical Facts；不需要 AP2-specific Core branch。

H-36 已独立 L3 `5/5 PASS`，把 B-06 的下一假设收敛为 H-37：

```text
root SD-JWT
→ root key provider + issuer signature + disclosure
→ verified root cnf.jwk
→ terminal KB-SD-JWT holder signature
→ previous-token binding
→ expected aud / nonce
→ STOP before Checkout/Payment semantics and Receipt
```

H-37 已独立 L3 `8/8 PASS`，official AP2 two-hop crypto/delegation slice 从 `ABSENT → BOUNDED_EXECUTABLE_SLICE`。当前继续 AP2 本地扩展的边际收益低于切换第二个真实外部 Sandbox。Human 已于 2026-09-19 明确要求把支付宝任务布置好交给 Executor，Evaluator 将授权严格限定为 Sandbox network/API、sandbox-only credential 与模拟交易，继续禁止生产环境、真实 PII/资金和新增依赖。

## Candidate experiments / 候选实验与设计任务

r100唯一执行包H62_APPROVED_ORDER_RECOVERY_SEAM_V1，capability_experiment/SINGLE/CONTRACT_FROZEN/Executor，假设H-62；四产品文件、360主动分钟/2L2/16恢复场景+24批准回归+6原生旅程+25AP2。恢复零付款；只有隔离本地合成副本可写，无新消费者成绩。旧H61材料测量停止。下表为历史候选。

| 优先级 | 方向 | 当前状态 | 触发条件 | 当前动作 |
|---:|---|---|---|---|
| 1 | H-36 / AP2 official cryptographic-delegation boundary measurement | PASS / CLOSED | 独立 L3 `5/5 PASS`；classification=`DEPENDENCY_BLOCKED` | 已完成：两跳 slice、最小依赖、crypto/semantics/receipt 分层和 ES256 复用边界均已定位 |
| 2 | H-37 bounded official crypto/delegation capability slice | PASS / CLOSED | Evaluator 独立 L3 `8/8 PASS` | 已完成：root SD-JWT + terminal KB-SD-JWT official verification，C01-C08 `8/8 PASS`，不再机械扩 AP2 本地 Case |
| 3 | H-38 / F2 Alipay Agent Pay Sandbox first external slice | CONTRACT_FROZEN / EXECUTOR | Human 已授权仅 Sandbox network/API + sandbox-only credential + simulated transaction；禁止生产环境/真实资金；本机缺 fixture/secret 时必须 BLOCKED，不得编造 | 第一条 live slice 只验证 sandbox Payment-Proof → `alipay.aipay.agent.payment.verify` → provider response signature → minimal external verification fact；L3 审计持久证据，不重复 live 支付验证 |
| 4 | additional AP2 boundary evidence | WATCH | H-36 发现新的共同断点且无需扩大协议层即可独立证实 | 只针对共同断点开包，不回滚 H-34/H-35 |
| 5 | F3/F4 Identity Provider + 极小额线上证据 | DEFERRED | Sandbox 稳定且 Human 明确资金授权 | 再进入真实 credential / production-like payment |


## Reassessment triggers / 重新排序触发器

只有发生以下情况才更新或重排地图：

- B-01 的项目级任务集和主指标已经可重复测量；
- 当前 Fact Lineage 独立复核发现新的高影响错误放行；
- 两到三轮相同假设没有可测收益；
- 失败从来源传播转移到轨迹、Agent 行为或环境状态；
- 项目目标、外部授权或测试环境发生变化；
- PayBench、WebShop、x402 或其他外部评测提供新的实测结果。

不得因为“某个模块容易实现”就把它升为第一瓶颈。

## Revision log / 修订记录

| Revision | 日期 | 证据或原因 | 瓶颈变化 | 假设变化 |
|---|---|---|---|---|
| `2026-08-03-r1` | 2026-08-03 | 根据项目中控、整体修正计划、验证体系路线、ArbiterOS 吸收方案、P9 已复核任务和 v2.1 skill 初始化 | 首次建立；B-01 定为固定端到端评测边界缺失 | H-01 定为项目级基线设计 |
| `2026-08-03-r2` | 2026-08-03 | P9 Fact Lineage 独立复核 PASS：16/16 矩阵、12/12 专项、413/413 全量，Overlay 策略投影不变 | B-01 仍为第一瓶颈；B-02 更新为组件已实现、项目影响未测量 | H-01 不变，下一包建立统一项目基线 |
| `2026-08-03-r3` | 2026-08-03 | P9 Project Impact Baseline 独立复核 REJECTED：T10 的 expected callback=1 掩盖已有成功付款后的重复副作用；5 个 VALID trace 均为评测器合成 Replay | B-01 保持第一瓶颈并进入测量完整性修复；B-03 更新为产品轨迹覆盖率未测量 | H-01 暂不判定，先修复测量语义后重新建立可信基线 |
| `2026-08-03-r4` | 2026-08-03 | Measurement Integrity Repair 独立复核 PASS：可信基线 GESR 0/12、重复副作用 1/12、产品轨迹 0/12，三次一致 | B-01 完成；新增 B-07 并升为第一瓶颈，B-03 为竞争瓶颈 | H-01 已确认；激活 H-06 副作用前重复付款事实传递 |
| `2026-08-04-r5` | 2026-08-04 | Known Payment Attempt capability revalidation 独立复核 PASS / IMPROVED：T10 callback 1→0，重复副作用 1/12→0/12，其他 11 项不变，边界挑战无误阻断 | B-07 完成；B-03 从竞争瓶颈升为第一瓶颈 | H-06 SUPPORTED；激活 H-03 产品权威轨迹最小合同 |
| `2026-08-06-r6` | 2026-08-06 | T10 产品权威轨迹切片独立复核 PASS / IMPROVED：product trace 0/12→1/12，target GESR 0/12→1/12，12-event/11-binding VALID，非轨迹投影与安全守护线不变 | B-03 从影响 12/12 缩小到剩余 11/12，仍为第一瓶颈；同时登记 provenance 诊断误报 | H-03 SUPPORTED_BY_T10；先修测量诊断，再扩展第二个单任务 slice |
| `2026-08-06-r7` | 2026-08-06 | T01 正常购买轨迹切片独立复核 PASS / IMPROVED：product trace 1/12→2/12，baseline GESR 0/12→1/12，11-event/10-binding VALID，T10 与非轨迹投影均不退化 | B-03 缩小到剩余 10/12 产品轨迹缺口，仍为第一瓶颈；新增公共组装结构债务作为第三个切片前置维护 | H-03 同时被 T10 拒绝链和 T01 成功链支持；下一步先抽统一 Trace Assembler，再扩展第三个路径族 |
| `2026-08-06-r8` | 2026-08-06 | T09 UNKNOWN 支付恢复轨迹切片独立复核 PASS / IMPROVED：product trace 2/12→3/12，baseline GESR 1/12→2/12，11-event/10-binding VALID，20 项负例、T01/T10 完整轨迹和非轨迹投影均不退化 | B-03 缩小到剩余 9/12 产品轨迹缺口，仍为第一瓶颈；统一 Trace Assembler 已由第三个路径族验证 | H-03 获得支付恢复链支持；下一步选择真实状态冲突事实闭合的 T12 单任务切片 |
| `2026-08-06-r9` | 2026-08-06 | T12 执行前设计复核：T01/T09 builder 分别 597/595 行，T01/T09/T12 的 11 个事件中 9 个完全相同；旧 T12 合同会继续新增专属 builder，尚未执行 | B-03 测量值不变；新增 Sidecar builder 复制这一结构约束，先以场景族工具包方式扩展 | H-03 不变；T12 继续作为唯一新增覆盖，但实现改为统一 Sidecar Trace Toolkit + 声明式 Profile |
| `2026-08-06-r10` | 2026-08-06 | Sidecar Family Toolkit 独立复核 PASS / IMPROVED：T01/T09 迁移为 43/40 行兼容层，产品 sidecar 仅一个 Toolkit 调用，无 T12 专属 builder；Product Trace `3/12→4/12`、GESR `2/12→3/12`，512/512 全量通过 | B-03 缩小到剩余 8/12 产品轨迹缺口，仍为第一瓶颈；场景族工具化路线得到验证 | H-03 继续获支持；下一步一次覆盖结构完全相同的 T02/T03/T04 Prepayment 家族 |
| `2026-08-07-r11` | 2026-08-07 | Prepayment Family Toolkit completion 独立复核 PASS / IMPROVED：T02/T03/T04 用一个 Toolkit + 3 个固定 Profile，10/10 边界、152/152 focused、522/522 全量、repeat=3 通过；Product Trace `4/12→7/12`、GESR `3/12→6/12`，12 项 actual 与旧 trace hashes 全部不变 | B-03 缩小到剩余 5/12（T05/T06/T07/T08/T11）；同时发现剩余 fixture 有 4 个 stale event-name expectations，先统一修 measurement contract | H-03 获得 Prepayment family 支持；修尺子后优先进入 T07/T08 Attack Overlay family |
| `2026-08-07-r12` | 2026-08-07 | Attack Overlay Family Toolkit 独立复核 PASS / IMPROVED：10/10 existing、15/15 family、21/21 project-impact、538/538 全量、repeat=3；Product Trace `7/12→9/12`、GESR `6/12→8/12`；其他 10 项 actual、旧 7 条 trace hash 与 non-trace 全部不变 | B-03 降为 WATCH，仅剩 T05/T06/T11；新增 B-08 Trace Consumer / UI Read Model 并升为第一瓶颈，因为已有四种代表轨迹结构但下游 consumer=0/4 | H-03 获得 Attack Overlay family 支持；激活 H-07，先证明轨迹可被统一只读消费，再进入 P9-E UI |
| `2026-08-10-r13` | 2026-08-10 | Authoritative Trace Consumer 独立复核 PASS / IMPROVED：19/19 consumer、21/21 project-impact、557/557 全量、13/13 正式入口、repeat=3；Consumer-ready `0/4→4/4`，Product Trace `9/12`、GESR `8/12`、旧 src 与 accepted trace hashes 不变 | B-08 保持第一瓶颈，但失败位置从“缺统一 Consumer”下移到“UI 尚未消费稳定 Read Model”；B-03 继续 WATCH | H-07 SUPPORTED；激活 H-08，先做只读 Trace Read Model Player，再讨论完整 WebShop Journey UI |
| `2026-08-10-r14` | 2026-08-10 | Authoritative Trace Player 独立复核 PASS / IMPROVED：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready `0/4→4/4`，source-binding drill-down 与 hostile-string 边界通过，既有 Product Trace/GESR 不变 | B-08 完成；新增 B-09 WebShop Journey 多事实源合同并升为第一瓶颈，先解决商城事实、experiment context 与支付权威证据的来源分离 | H-08 SUPPORTED；激活 H-09，先做 UI-neutral source-classified Journey Read Model，再进入完整 Journey UI / 自主 Agent |
| `2026-08-10-r15` | 2026-08-10 | WebShop Journey Fact Source Read Model 独立复核 PASS / IMPROVED：27/27 Journey、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；Journey source-classified `0/1→1/1`，17 条跨源 correlation 全 true，错绑 fail closed，既有指标不变 | B-09 完成；新增 B-10 Journey UI composition 并升为第一瓶颈 | H-09 SUPPORTED；激活 H-10，只让 UI 消费 accepted Journey Read Model，之后再进入 B-04 自主 Agent |
| `2026-08-23-r16` | 2026-08-23 | WebShop Journey Player 独立复核 REJECTED / INCONCLUSIVE：合法代表路径可展示 1/1，但 `UNVERIFIED` source classification 与未知 schema 两个反例均正常渲染；AC-01/09 失败，相关回归与项目指标未退化 | B-10 保持第一瓶颈，失败位置收敛到 accepted-input guard；B-04 暂不提升 | H-10 尚未得到支持；先执行最小 accepted-input repair，复评通过后再切 B-04 |
| `2026-08-23-r17` | 2026-08-23 | Journey Player accepted-input repair 独立复核 PASS / NOT_APPLICABLE：L2/L3 4/4、Player 27/27、相关回归 67/67、正式入口 13/13；两个反例在 build/render 四个组合全部 fail closed，Product Trace/GESR/side-effect 守护线不变 | B-10 完成；B-04 提升为第一瓶颈，首轮范围固定为 WebShop small goal index 2 的自主 pre-Buy-Now 行为 | H-10 SUPPORTED；激活 H-11，先证明单任务真实环境行为正确且可评分，再扩多任务 |
| `2026-08-24-r18` | 2026-08-24 | Executor preflight 与 Evaluator 独立 runtime probe 一致：固定 shuffle 后 goal index 2=`B07S7HDC88` black loafers，index 10=`B099231V35` orange cargo pants，checkout HEAD=`64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`，两次 reset purchase count=0 | B-04 顺序与量级不变；仅纠正首轮 runtime selector 事实，原 r17 的 index 2 记录由本修订明确取代 | H-11 实质不变；首轮 selector 由 2 更正为 10，任务原地 Amendment A1 后继续 |
| `2026-09-02-r19` | 2026-09-02 | H-11 独立复核 `PASS / IMPROVED`：L3 `6/6 PASS`，goal 10 autonomous Journey/target+option `0/1→1/1`，零 Buy Now/支付副作用；随后 frozen multigoal checker 对 goals 0/2/7/9/10、repeat=2 复现 `3/5`，goal 2/7 均错选商品 | B-04 保持第一瓶颈，但失败位置从“无自主 Agent 行为”下移到“multi-goal product ranking / option matching 泛化不足” | H-11 `SUPPORTED(single-goal)`；激活 H-12，把同一五题 baseline `3/5→5/5`，禁止目标真值/goal-index 补丁 |
| `2026-09-05-r20` | 2026-09-05 | H-12 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`，冻结五目标 `3/5→5/5`，643/643 全量回归且零购买/支付副作用；额外等价 UI 顺序反例得到 `order_invariant=false`；同时发现 H-11 accepted-but-uncommitted policy 只保留 hash、未保留 exact source snapshot | B-04 保持第一瓶颈，但从“已知五题 generalization failure”下移为“unseen-task transfer / semantic robustness 未测量”；不再继续调五题 | H-12 `SUPPORTED_ON_FROZEN_SET`；下一步先做 Evaluator-only Blind Holdout Measurement；H-13 在盲测结论前不激活 |
| `2026-09-06-r21` | 2026-09-06 | Blind Holdout measurement Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `3/3 PASS`，L2=L3；8 个原未见任务 exact `3/8`、deterministic `8/8`、零 Buy Now/购买副作用；失败族 `REQUIRED_OPTION_MISMATCH=4`、`TARGET_PRODUCT_MISMATCH=1` | B-04 保持第一瓶颈，但从“unseen transfer 未测量”下移为“option-grounding generalization（规格匹配泛化）”；已揭晓 8 Case 降级为 regression set，不再作为无偏盲测集 | H-12 项目外推边界确认不足；激活 H-14，用不同值 synthetic/metamorphic probe `1/5→5/5` 验证通用规格匹配机制；H-13 继续后置 |
| `2026-09-06-r22` | 2026-09-06 | Human 明确要求防止把当前已知规格细节误当成“能力已测全”；Evaluator 补充能力不变量、系统性变形发现、新鲜未见迁移测量与失败族台账原则 | B-04 第一瓶颈不变；补充 H-14 后的测量收敛链，避免继续逐题补丁 | H-14 单一主要变化不变；`5/5` 只作为已知失败机制修复门，后续必须经过系统性变形发现 + fresh unseen evidence，再决定 CONTINUE / SWITCH / H-13 |
| `2026-09-06-r23` | 2026-09-06 | H-14 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `8/8 PASS`；frozen option-grounding probe `1/5→5/5`，H-12 real regression `5/5`，647/647 全量回归，Product Trace `9/12`、GESR `8/12`、零 Buy Now/外部副作用 | B-04 保持第一瓶颈，但“已知规格失败机制”已收敛；当前第一未知量转为系统性边界发现 + fresh unseen transfer | H-14 `SUPPORTED_ON_KNOWN_MECHANISMS`；下一步进入 Evaluator-owned Systematic Metamorphic Discovery，不直接继续改代码，也不进入 H-13 |
| `2026-09-06-r24` | 2026-09-06 | Systematic Discovery Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `4/4 PASS`；24 Case=`19 PASS / 5 FAIL`、48 observations 全可重复、safety hits 0；`AMBIGUOUS_OPTION_GUESSED=3` 跨 2 independent seeds；H-15 新 probe baseline `2/5` | B-04 保持第一瓶颈，但从“系统性边界未知”下移为“证据不足 / 候选不唯一时仍猜规格” | 激活 H-15 Option Grounding Uncertainty Gate；先修重复 uncertainty mechanism，再做 fresh unseen transfer |
| `2026-09-06-r25` | 2026-09-06 | 主线纠偏：确认 P9/WebShop 的目的不是穷举意图/规格准确率；B-04 已形成真实自主行为 + 泛化失败证据，H-15 在 Executor 开始前 superseded 并降为 WATCH；代码侧 GovernedPaymentAction / Runtime Gate / Authoritative Trace / Payment-Fulfillment 底座已存在，但 machine-readable Action Origin 仍为 0/5 | 新增并激活 B-11 Action Origin / Responsibility Trace；B-04 改为 WATCH / BEHAVIOR_BASELINE_ESTABLISHED | 冻结 H-13 read-only Action Origin minimal slice；Fresh unseen 不再是 H-13 强制前置门槛 |
| `2026-09-06-r26` | 2026-09-06 | H-13 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `8/8 PASS`；Action Origin `0/5→5/5`，657/657 全量回归；同时确认 autonomous behavior fixture 与 T01 payment trace 仍是独立证据，不能声称 same-journey responsibility chain | B-11 继续 ACTIVE，但瓶颈从“无机器可读 Action Origin”下移为“无同一 journey 连续责任关联” | H-13 `SUPPORTED`；激活 H-16 one-off Same-Journey Responsibility Correlation，先测现有组件能否自然串联，不预设产品修复 |
| `2026-09-06-r27` | 2026-09-06 | H-16 Executor L2 + Evaluator L3 均在 C01 复现 stale cross-policy trace baseline：历史 policy `af2a...` / trace `8c0a...`，当前 policy `6133...` / trace `b99e...`；最终商品/规格/价格与零副作用仍一致；Evaluator fresh current-policy replay 3/3 deterministic | B-11 继续 ACTIVE，但断点从“same-journey 未串通”进一步收敛为“baseline lifecycle 测量合同错误”，尚无证据表明下游产品链失败 | H-16 `REJECTED / INCONCLUSIVE / SWITCH`；激活 H-17，只修测量合同并直接重跑 C01..C08，不改任何产品/runner |
| `2026-09-06-r28` | 2026-09-06 | H-17 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `8/8 PASS`；baseline lifecycle 修正后现有 same-journey responsibility `C01..C08=8/8`、Action Origin 5/5、Trace VALID、657/657、真实副作用 0 | B-11 `RESOLVED / STAGE_CLOSED`；新增 B-12 Same-Journey Payment Lifecycle / Recovery Continuity 并升为第一瓶颈 | H-17 证明 H-16 主要是测量合同问题；激活 H-18 measurement-only 四分支测量，先测现有 Recovery/Finality/Lifecycle/Trace 组合，不预设产品修复 |
| `2026-09-10-r29` | 2026-09-10 | H-18 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `7/7 PASS`；同一 H-17 journey 四分支 semantic=`4/4`、continuity=`1/4`、J03 首断点=`AUTHORITATIVE_TRACE_AVAILABLE`、J02/J04 首断点=`ACTION_ORIGIN_PROJECTABLE`、657/657、真实副作用 0 | B-12 保持第一瓶颈，但从“生命周期组合未测量”下移为 Evidence / Accountability 连续性；先处理更上游的 J03 Trace 缺失 | H-18 完成测量并支持“现有生命周期语义正确但证据链不完整”；激活 H-19，只补失败履约声明式 Sidecar Trace Profile，目标 continuity `1/4→2/4`，不改 Toolkit / Action Origin |
| `2026-09-10-r30` | 2026-09-10 | 执行前重新评估任务粒度：H-18 的 J02/J03/J04 三个失败均属于 Lifecycle Evidence Registry Coverage；J03 缺通用 failed-fulfilment Profile，J02/J04 的既有 VALID Trace 扩展事件缺 Action Origin mapping | B-12 不变，但把三个同类证据链断点合并为一个中等大小的 registry closure，避免连续微修；Payment / Lifecycle / Trace Toolkit 继续冻结 | H-19 `SUPERSEDED_BEFORE_EXECUTION`；激活 H-20 Lifecycle Evidence Continuity Closure，统一目标 semantic `4/4` 保持、continuity `1/4→4/4` |
| `2026-09-11-r31` | 2026-09-11 | H-20 Evaluator REVIEW：Attempt 1 因 T11 旧基线期望 `6/7` 阻断，A1 仅修 regression expectation；Attempt 2 L2 `7/7`、Evaluator L3 `7/7 PASS`，semantic=`4/4`、continuity=`4/4`、Product Trace=`10/12`、GESR=`9/12`、658/658 全量、真实副作用 0 | B-12 `RESOLVED / STAGE_CLOSED`；新增 B-13 Same-Journey Remediation / Closure Continuity 并升为第一瓶颈；B-03 缩小为仅 T05/T06 WATCH | H-20 `SUPPORTED / STOP_THIS_DIRECTION`；激活 H-21 measurement-only，先测 full/partial refund、dispute 与原交易错绑在同一 journey 的 L8-L9 continuity，不预设产品修复 |
| `2026-09-12-r32` | 2026-09-12 | H-21 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `7/7 PASS`；5/5 semantics、5/5 original-transaction binding expectation、5/5 closure explicit、5/5 existing Product Trace VALID，但 remediation evidence in trace=`0/5`，共同 first breakpoint=`TRACE_REMEDIATION_EVIDENCE_PRESENT`；658/658、真实副作用 0 | B-13 保持第一瓶颈，但从“L8-L9 未测量”收敛为“post-payment remediation evidence registration 缺失”；不是退款/争议规则错误 | H-21 完成测量；激活 H-22，一个通用 remediation trace extension，把 Refund/Dispute + OriginalTransactionBindingFact + Closure outcome source-bound 接回同一 Product Authoritative Trace，不做逐 Case 修补 |
| `2026-09-12-r33` | 2026-09-12 | H-22 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`；remediation evidence `0/5→5/5`、continuity `0/5→5/5`、R05 保持 `INVALID`、662/662、真实副作用 0；Evaluator 独立 probe 发现 live projection hash=`71a4...3966`，但 public runtime hash 仍为 base `45ae...b4` | B-13 的核心补救证据链能力已闭合，但进入 Replay / Accountability 前仍有 contract identity / auditability 缺口；不再增加补救业务场景 | 激活 H-22R bounded repair：只修 historical base 与 effective runtime contract/hash 的分层和公开指纹一致性；修复后重新评估 B-13 是否 STAGE_CLOSED |
| `2026-09-12-r34` | 2026-09-12 | H-22R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；public effective projection/profile/runtime fingerprint 与 live validator contract 机械一致；historical base identity 保持；H-22 五分支复验 SHA-256 完全相同、662/662、真实副作用 0 | B-13 `RESOLVED / STAGE_CLOSED`；新增 B-14 Remediation Accountability / Closure Consumption 为第一瓶颈。Consumer 底座已有部分真实使用证据，但 5 个补救分支经 Consumer + Player 的完整消费仍未系统测量 | 激活 H-23 measurement-only：产品冻结，测现有 Consumer / Read Model / Action Origin / Player 对 5 个补救分支的完整性、确定性和 R05 负例保留；仅在共同断点出现后再考虑 capability package |
| `2026-09-12-r35` | 2026-09-12 | H-23 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `7/7 PASS`；冻结 5 个补救分支 Consumer/Player/continuity 全部 `5/5`、first breakpoint=`NONE:5`，R05 `INVALID` 原样可见，662/662、真实副作用 0 | B-14 `RESOLVED / STAGE_CLOSED`；不再开发 Consumer/Player。新增 B-15 Actor Authenticity / Signed Instruction Verification：P3 最高 BOUND，AP2/ACP 多个签名/身份边界明确 not_verified，但共同机制尚未系统测量 | 激活 H-24 cross-surface measurement-only：冻结产品，跨 P3 + AP2 HP/HNP + ACP 测 6 个真实性边界；只有出现重复共同 verifier gap 后才考虑最小通用真实性验证能力 |
| `2026-09-12-r36` | 2026-09-12 | H-24 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / CONTINUE`，L3 `7/7 PASS`；6/6 探针 deterministic，P3 三路径最高 `BOUND`，product `VERIFIED=0/6`；AP2 HP/HNP + ACP 三个独立入口重复出现 cryptographic signature `not_verified`，34/34 专项、662/662 全量、真实副作用 0 | B-15 继续 ACTIVE，但拆为 B-15A Signed Instruction【当前第一子瓶颈】与 B-15B Credential/Possession【后续】；不建设万能身份模块 | 激活 H-25 capability experiment：协议中立 SignedInstructionVerificationFact + HMAC-SHA256 verifier + ACP 2026-04-17 Merchant-Signature 首个消费者；AP2 SD-JWT、P3 VERIFIED、PKI/钱包/网络继续排除 |
| `2026-09-13-r37` | 2026-09-13 | H-25 Evaluator REVIEW：Task `PASS / IMPROVED / CONTINUE`，L3 `10/10 PASS`；ACP signed-webhook `0/6→6/6`、5/5 negative fail-closed、13/13 focused、675/675 full unittest，H-24 accepted hash 不变，真实网络/支付/生产凭据密钥 0 | B-15A 明显缩小：已获得 ACP 第一个真实 Signed Instruction consumer，但跨协议/跨算法复用尚未由第二消费者证明；B-15B 继续后置 | 激活 H-26 evaluator-design：先冻结 AP2 第二消费者的 pinned source、exact signed object、key relation 与正负验证样例；证据不足则不进入 AP2 verifier 编码并重排方向 |
| `2026-09-13-r38` | 2026-09-13 | H-26 evidence gate：官方 AP2 `v0.2.0` release / merchant-signed JWT / deterministic verification 提供稳定协议依据；冻结 evaluator-owned ES256/P-256 synthetic fixture、六案例正负矩阵；本机已有 `cryptography 41.0.7`，无需网络或安装 | B-15A 从“第二消费者证据是否存在”前移为“第二消费者能否真实复用同一 Fact”；完整 SD-JWT / Credential / AP2 conformance 继续排除 | 激活 H-27 capability experiment：generic ES256 compact-JWS verifier + AP2 merchant-authorization adapter；目标 AP2 `0/6→6/6`、real consumers `1→2`、H-25 accepted hash 不变 |
| `2026-09-13-r39` | 2026-09-13 | H-27 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，L3 `10/10 PASS`；AP2 ES256 `0/6→6/6`、real consumers `1→2`、5/5 negative fail-closed、17/17 focused、692/692 full unittest，H-25 accepted hash 不变，真实网络/支付/生产凭据密钥 0 | B-15A `RESOLVED / STAGE_CLOSED`：ACP/HMAC + AP2/ES256 已提供跨协议/跨算法第二消费者证据；第一子瓶颈切换为 B-15B Credential/Possession，P3 仍最高 `BOUND` | 激活 H-28 evaluator-design：冻结 credential validity、subject binding、proof-of-possession、freshness/replay 与 `BOUND→VERIFIED` promotion rule；证据不足则保持 `BOUND` |
| `2026-09-15-r40` | 2026-09-15 | H-28 evidence gate 完成：SPIFFE X.509-SVID / Trust Bundle / Workload API 与 RFC 9449 PoP 语义足以冻结四条件升级门；Evaluator 生成不含私钥的 synthetic X.509-SVID 正例与 wrong-trust/wrong-subject/no-proof/bad-proof/replay/stale 六类负例；本机 `cryptography 41.0.7` 可离线执行 | B-15B 保持第一瓶颈，但从“真实 verifier 语义未定义”前移为“有界 X.509-SVID credential/PoP 能否第一次合法产生 VERIFIED”；B-06 live identity/network 继续 DEFERRED | 激活 H-29 capability experiment：protocol-neutral CredentialPossessionVerificationFact + bounded X.509-SVID verifier + P3 promotion wiring；目标 product VERIFIED `0→1` 且 legacy credential_ref-only 保持 BOUND |
| `2026-09-15-r41` | 2026-09-15 | H-29 Executor L2 `8/8`、冻结七案例 `7/7`、698/698 与项目 guardrails 均通过，但 Evaluator 独立 `RV-EV-09` 复现 metadata relabel replay：旧 signed payload/signature 保持不变，仅重贴 fresh nonce/issued_at 即错误返回 `VALID / credential_possession_verified` | B-15B 保持第一瓶颈；H-29 `REJECTED / REGRESSED`，失败位置收敛到 signed challenge 与 freshness/replay 元数据未密码学绑定；不是 X.509-SVID 方向整体失败 | 激活 H-29R bounded repair：只增加 canonical signed challenge binding，冻结 P3 promotion / Payment policy / Signed Instruction；先关闭 false VERIFIED 再决定是否继续 B-15B |
| `2026-09-17-r42` | 2026-09-17 | H-29R Evaluator L3 `8/8 PASS`：六类 metadata relabel attack 全部 fail closed，父 H-29 `7/7` 与 `VERIFIED 0→1` 保持；30/30 focused、13/13 正式场景、699/699 全量、Product Trace 10/12、GESR 9/12。同期复跑 PayBench current rules=`8/10`，唯一 unsupported 为 D1 Trap/Lookalike | B-15 在本地离线边界达到代表性闭合并转 `RESOLVED`；真实 identity 归 B-06 `DEFERRED`。B-05 从 WATCH 升为第一瓶颈，因为 D1 两个独立外部挑战共同缺 data disclosure fact | 激活 H-30 capability experiment：一个最小协议中立 DataDisclosureFact + PayBench D1 首个消费者；目标 executable `8/10→10/10`，不扩完整隐私治理 |
| `2026-09-17-r43` | 2026-09-17 | H-30 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，修正 evaluator plan 的 `PYTHONPATH=src` 可复现性后 L3 `8/8 PASS`；PayBench `8/10→10/10` 可执行且 `10/10 PASS`，703/703 全量，守护线不退化。重新测量 T05/T06：decision/binding/callback 均正确，共同只缺产品权威轨迹 | B-05 `RESOLVED / LOCAL_STAGE_CLOSED`；B-03 从 WATCH 升为第一本地瓶颈，范围严格限定 T05/T06 action-binding rejection trace；B-04 WATCH，B-06 DEFERRED | 激活 H-31：复用现有 Trace Assembler / frozen profile contract，为 T05/T06 拒绝分支附加一个通用产品权威轨迹族；目标 Product Trace `10/12→12/12`、GESR `9/12→11/12`，不修改决策语义 |
| `2026-09-17-r44` | 2026-09-17 | H-31 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，独立 L3 `8/8 PASS`、708/708、PayBench 10/10、S01-S13 13/13；Product Trace `10/12→12/12`、GESR `9/12→11/12`，仅剩 T10。历史回查确认 B-07 已独立验收 T10 `DENY/callback0/BLOCKED`，而主 fixture 仍保留更早 `ALLOW + lifecycle` 期望；临时机械对齐 accepted target 后 GESR/evidence/Product Trace 均 `12/12`、gap=0、repeat=3 | B-03 `RESOLVED / FIXED_12_TASK_TRACE_COVERAGE`；B-01 因 T10 主 baseline expectation drift 重新激活为第一瓶颈；B-04 WATCH，B-06 DEFERRED | 激活 H-32 measurement repair：只允许主 fixture T10 五个 stale expected 字段与 accepted B-07 target 对齐，并同步直接依赖测试；零产品/runner 修改，Project impact 固定 `NOT_APPLICABLE` |
| `2026-09-17-r45` | 2026-09-17 | H-32 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，独立 L3 `6/6 PASS`、708/708、PayBench 10/10、S01-S13 13/13；protected product/runner/accepted target 不变，仅 T10 五个 stale expected 字段与 B-07 target 对齐；fresh repeat=3 得到 matched/GESR/evidence/Product Trace 全部 `12/12`、gap=0 | B-01 `RESOLVED / BASELINE_RECONCILED`；当前固定本地代表性项目基线无 active gap。B-02/B-04 保持 WATCH，B-06 保持 DEFERRED | H-32 `PASS / CLOSED`；不自动激活新本地假设，等待新项目级失败、新外部评测或真实环境授权再重排 |
| `2026-09-17-r46` | 2026-09-17 | Human 明确授权进入 F 阶段公开外部验证；公开资料复核确认 AP2 `v0.2.0` release=`b4587ac`，重点覆盖 Human Not Present，官方规范/SDK/source/schema 可作为独立外部合同来源 | B-06 从 DEFERRED 激活为第一瓶颈，但先做 `OFFICIAL_PROTOCOL_COMPATIBILITY_MEASUREMENT`，不直接接 SDK 依赖、Sandbox 或真实资金 | 激活 H-33 / F0：冻结 AP2 v0.2.0 只读 source，做 12 维兼容矩阵；`src/tests` 冻结，结果只允许导向 NO_PRODUCT_GAP / BOUNDED_ADAPTER_GAP / CORE_SEMANTIC_GAP / SOURCE_ENV_BLOCKED |
| `2026-09-18-r47` | 2026-09-18 | H-33/F0 Evaluator REVIEW：`PASS / NOT_APPLICABLE / CONTINUE`；独立 L3 `6/6 PASS`，AP2 focused `17/17`、项目 baseline `12/12 repeat=3`、708/708；12 维矩阵=`3 SUPPORTED / 6 PARTIAL / 3 UNSUPPORTED`，gap=`BOUNDED_ADAPTER_GAP` | B-06 保持第一瓶颈，但从“官方协议兼容性未知”下移为“AP2 Adapter 最上游 object identity / checkout hash / payment→checkout binding 未验证”；Core 无已证实语义缺口 | H-33 `SUPPORTED / CLOSED`；激活 H-34 / F0R capability experiment：一个 bounded AP2 protocol-boundary gate，B01-B07 `7/7` 为目标，Canonical Core / SDK / Receipt / cnf / Sandbox 全部冻结或后置 |
| `2026-09-18-r48` | 2026-09-18 | H-34/F0R Evaluator REVIEW：`PASS / IMPROVED / CONTINUE`；独立 L3 `7/7 PASS`，B01-B10 `10/10`、targeted `13/13`、AP2 `17/17`、项目 baseline `12/12 repeat=3`、721/721；11 个 protected Core hashes 不变 | B-06 保持第一瓶颈但继续前移：exact vct / checkout hash / payment→checkout verified binding 已关闭；当前首断点转为 official SDK/types / executable integration | H-34 `SUPPORTED / CLOSED`；F1 AP2 official SDK executable slice 进入 `READY_FOR_DESIGN`，需单独冻结依赖/SDK/网络权限，Sandbox/Provider/真实资金继续后置 |
| `2026-09-18-r49` | 2026-09-18 | F1 设计复核：本地已固定 AP2 `v0.2.0 / b4587ac1...`，generated model slice 只需 `pydantic`；当前系统 Python 实测 `pydantic MISSING`，不需要先引入 jwcrypto/sd-jwt/完整 AP2 安装 | B-06 首断点进一步收敛为“官方 generated types 是否可经极薄 SDK Bridge 复用 H-34 boundary gate”；环境依赖成为执行前置而非产品 Core 缺口 | 激活 H-35 / F1 `DRAFT_CONTRACT`：只允许 task-local `pydantic==2.12.5`，未获 Human 授权前禁止联网自动安装；产品 principal change 限定 SDK Bridge，Core 与 H-34 boundary 冻结 |
| `2026-09-18-r50` | 2026-09-18 | H-35/F1 Evaluator REVIEW：`PASS / IMPROVED / CONTINUE`；独立 L3 `9/9 PASS`，official SDK cases `9/9`、focused `10/10`、H-34 `10/10`、AP2 `17/17`、baseline `12/12 repeat=3`、731 tests OK（10 个 SDK tests 在系统环境按 optional dependency 设计 skip，并在隔离环境 `10/10 PASS`）；11 个 protected Core hashes 不变 | B-06 保持第一瓶颈但继续前移：official generated types → Bridge → H-34 → Canonical 已闭合；当前首断点转为 official cryptographic/delegation verification，Sandbox/Provider/真实资金继续后置 | H-35 `SUPPORTED / CLOSED`；下一方向 H-36 evaluator-design/measurement：先定位 official verifier/helper 第一可执行边界、最小 pinned dependencies 与现有 generic ES256 verifier 复用关系，再决定是否编码 |
| `2026-09-19-r51` | 2026-09-19 | Human 批准继续第 2/3 步：F1 commit `e693127` 已推送远程；Evaluator 基于 pinned AP2 v0.2.0 source 将下一断点拆为 `MandateClient.verify → sdjwt.chain.verify_chain` 的密码学/委托链验证、Checkout/Payment chain 约束语义、Receipt 独立验证路径，并冻结 H-36 measurement 包 | B-06 保持第一瓶颈；H-36 只测量 official verifier/helper、最小依赖与 generic ES256 复用边界，不修改产品、不安装依赖、不进入 Sandbox/Provider/真实资金 | H-36 `CONTRACT_FROZEN / EXECUTOR`；只有形成单一 next-slice decision 并通过 L2/L3 后才允许开 H-37；F2 继续 GATED |
| `2026-09-19-r52` | 2026-09-19 | H-36 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / HUMAN_REQUIRED`；独立 L3 `5/5 PASS`，10 surfaces、4 dependency rows、classification=`DEPENDENCY_BLOCKED`；generic ES256 仅 `REUSE_PRIMITIVE_ONLY`；project baseline 12/12、S01-S13 13/13、PayBench 10/10、AP2 minimal 2/2、Attack Overlay 6/6 | B-06 继续 ACTIVE，但首断点从“official crypto/delegation 边界未知”收敛为“已明确 root SD-JWT + terminal KB-SD-JWT 两跳 slice，缺 faithful pinned isolated runtime environment”；Receipt 与 Checkout/Payment semantics 独立后置 | H-37 暂不冻结：等待 Human 明确授权 task-local isolated environment 安装/对齐 `jwcrypto==1.5.6`、`sd-jwt==0.10.4`、`cryptography==46.0.5`，保留 `pydantic==2.12.5`；F2 继续 GATED |
| `2026-09-19-r53` | 2026-09-19 | Human 明确批准 H-37 任务级隔离环境安装四个 direct pins：`pydantic==2.12.5`、`jwcrypto==1.5.6`、`sd-jwt==0.10.4`、`cryptography==46.0.5`，并仅允许 resolver 必要传递依赖；Evaluator 冻结 H-37 capability contract 与 8-case 独立验证矩阵 | B-06 第一断点保持为 official two-hop runtime verification；依赖授权阻塞已解除，但能力尚未执行，不能提前写成已验证 | H-37 `CONTRACT_FROZEN / EXECUTOR`；唯一 principal change 为 thin AP2 official-verifier adapter，直接调用 pinned `MandateClient.verify`；系统 Python、Sandbox/provider/wallet、真实凭证/PII/资金、commit/push 继续禁止 |
| `2026-09-19-r54` | 2026-09-19 | H-37 Evaluator REVIEW：`PASS / IMPROVED / HUMAN_REQUIRED`；独立 L3 `8/8 PASS`，C01-C08 `8/8`、existing AP2+ES256 `25/25`、project baseline `12/12 repeat=3`、S01-S13 `13/13`、PayBench `10/10`、AP2 minimal `2/2`、Attack Overlay `6/6`、full unittest `733 OK / 10 skips` | B-06 official two-hop runtime 断点关闭；AP2 本地 official SDK+crypto 代表性链路已形成。第一断点前移到第二个真实外部 Sandbox/Provider 能否产生 provider-observed payment-proof / callback-state evidence，并进入 Trust / Trace；继续 AP2 typed semantics/Receipt 降为 WATCH | 下一方向 H-38/F2 Alipay Agent Pay Sandbox first external slice；官方资料确认 Sandbox 不使用真实资金，Machine Pay 链路包含 402、Payment-Proof、`alipay.aipay.agent.payment.verify` 与异步履约回执；执行前仍需 Human 新授权 sandbox network/API + sandbox-only credential/test account |
| `2026-09-19-r55` | 2026-09-19 | Human 授权 H-38 仅在支付宝 Agent Pay Sandbox / sandbox-only credential / 模拟交易 / 零真实资金边界执行；Evaluator 冻结 Sandbox first external slice，同时新增 `横向攻击验证轨.md` 与 B-16 cross-cutting adversarial track | B-06 从 `LIVE_SANDBOX_AUTH_REQUIRED` 前移为 `ALIPAY_SANDBOX_FIRST_SLICE`；B-16 作为 WATCH 横向轨，不抢占纵向 H-38 | H-38 `CONTRACT_FROZEN / EXECUTOR`；第一 slice 只做 `Payment-Proof → alipay.aipay.agent.payment.verify → provider response signature → minimal neutral fact`；若缺 Sandbox secret/fixture 则 BLOCKED，不得转生产、不安装新依赖 |
| `2026-09-24-r64` | 2026-09-24 | H-41 P0 最终 Evaluator REVIEW：中央结构校验 OK，正式 L3 `7/7 PASS`、mandatory failures=`0`；H41 28/28、H38 gate 12/12、Alipay adapter 16/16、observer 14/14、独立反例 7/7，保护 hash 全一致；R1/R2 关闭，复核期间真实网络与真实密钥读取均为 0 | B-06 仍是第一瓶颈；离线探针已可安全承担一次 signed-error 测量，但尚无 Provider 实证、有效 Payment-Proof、付款或四维绑定证据 | H-41 `P0 PASS / RELEASE_P1`；CURRENT 仅授权一次固定合成 Sandbox HTTPS 请求，任何结果均 STOP 并回交 Evaluator，不自动改变 H38 `PARTIAL / LIVE_BLOCKED` |
| `2026-09-27-r65` | 2026-09-27 | H-41 P1 前置检查因 HEAD drift 零调用停止；Evaluator 确认 `7831d23` 为已验收 H38–H41 快照固化，保护及受审 hash 不变，commit/security audit 通过；H38 gate 12/12、adapter 16/16、observer 14/14、独立反例 7/7。H41 27/28，唯一失败是已失效的 P0 实际状态断言 | B-06 不变；基线身份阻塞关闭，但 Provider 响应仍未测量 | 接受 a3 baseline reanchor，原一次 P1 授权继续有效且预算未消耗；不扩大请求或秘密边界 |
