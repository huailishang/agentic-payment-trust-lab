# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-11-25-r153
Last reviewed: 2026-11-25
Map owner: Evaluator / Human Task Owner
Status: ACTIVE

H91全生命周期测量已独立PASS/NOT_APPLICABLE/CONTINUE：L2/L3各6/6、八AC、六族13行、124回归、499保护及62接受项保持。两入口读后窗口与原生关联缺口确认，但不推定旧准入违规；恢复未见共同安全失败。B-27进入H92一个持久执行控制能力包，将停止/准入排序、未知不重放、恢复及原生视图合并验收。产品实现尚未执行；E/F与外部授权边界保持。

## Project outcome / 项目结果

在本地、可重置的边界内，证明用户授权、Agent动作、订单/支付绑定、执行前治理、异常恢复和审计形成可回放、可解释、可独立复核的信任链。错误放行、漏确认、重扣/重单、低可信来源覆盖确认、错绑、无前置治理的副作用是零容忍风险。

不扩张为通用Agent Runtime（智能体运行时），不以真实资金或生产支付接入为当前目标。客户需求、付费价值与工程能力分别记账。

## Global capability roadmap / 全局能力路线

| 阶段 | 状态 | 声明边界 |
| --- | --- | --- |
| A 评测与治理底座 | 本地阶段关闭 | 固定基线、守护线与独立复核已有代表证据 |
| B 授权、绑定、来源、执行前治理 | 局部撤回/停用切片关闭，H91整类测量签收，H92共同控制能力冻结 | 停止先于准入要阻断；准入先于停止须保留在途事实和未决，不能承诺物理取消；H92统一排序/不重放/原生视图，未预报结果 |
| C 支付生命周期、恢复、补救证据连续性 | 本地阶段关闭 | 代表性恢复/补救链；H62增加单个商城订单恢复切片 |
| D 责任归因与可消费审计链 | 本地阶段关闭 | Consumer/Read Model/Player（消费器/读取模型/播放器）已有代表覆盖 |
| E 主体真实性、凭证与签署指令 | 本地来源、消费归因、时点资格和单入口取证责任代表切片完成 | H85 L2/L3 各4/4，入口按次取得挑战证明，明确拒绝后身份降为BOUND；实际采用、生产可信时钟、撤销/轮换及组织/用户/硬件强认证仍待证据 |
| F 外部协议、SDK与消费者适用性 | 受控代表切片阶段关闭；未来真实接入条件仍受证据/授权约束 | 原4会话/3付款/3收款、通知/恢复及H72R2独立12/12保持；预算例外归档后修复PASS/STOP，旧拒收不追认，真实主体/生产PSP/独立采用未闭合 |

## End-to-end capability chain / 端到端能力链

用户授权 → 可信来源/主体事实 → 动作与交易绑定 → 副作用前治理 → 支付/订单执行 → 异常处置 → 权威证据 → 可消费审计。

H62使单个本地异常类型从“付款成功而订单缺失，只能查询”前移为“新批准→原生订单事务→唯一收据→重放同结果”；仍不代表真实商户订单、用户身份或履约完成。

## Measurement basis / 测量基础

- measured（H91独立终验）：L2/L3各6/6，八AC、六族13行、124/124零跳过、499冻结/62接受项保持，六份原始JSON语义一致。独立复算O5/O6/O7窗口覆盖A/B，原生gate八首观察无停止字段，关联来自测试。R1–R5十查询/二十新入口DENY，UNKNOWN/PENDING安全未决，迟到成功/已付恢复保持；R4为ledger CANCELLED与合成FAILED/BLOCKED不同投影。PASS/NOT_APPLICABLE/CONTINUE，无产品改善；停止整类重复测量。见 [H91复核](../05_任务交接/H91_SHUTDOWN_INFLIGHT_ORDERING_MEASUREMENT_V1/REVIEW_SCENARIO.md)。
- source-inspected / frozen design（H92制包）：现有事务可用于原子写停止和唯一准入，三个新Interface及控制表尚不存在，制包baseline已确认缺失、无产品运行。冻结一个表/两个产品文件的持久控制机制；O5/O6目标DENY/0，O7已准入在途仍ALLOW但原生可追溯且不得虚报全部取消。两入口丢返回及仅准入崩溃后不重放、旧库/坏事实/恢复/124回归统一2实现/2L2/1L3。仅设计，不计成绩。

- source-inspected / limited L1（r152制包）：十个原生符号与七表已定位；门禁记录在回调返回后形成，停止读取与执行分离；recover_original委托assess_payment_recovery，候选重试不直接执行支付。只有普通读取不能建立持久准入承诺。纯观察器正控制与8坏投影通过；O1正常创建与R1 UNKNOWN/两次重开查询/停止后两入口拒绝的抽样在第二次L1通过。第一次因任务辅助函数调用错误失败，原始三件套/修正前脚本保持；产品未改。该抽样不是13行完整矩阵、正式L2或独立L3。
- frozen design（H91 Amendment02）：六族统一覆盖，8顺序+5恢复共13行，H90/H88守护和原124回归，公共六VP/八AC；冻结后当前脚本最多一次修正、2L2/1独立L3。产品只读、附加权限全false。下一能力须依据共同原因与场景承诺，禁止按每行继续派补丁。

- governance correction（r151）：本次无新产品运行或能力增益。r150未先确定执行准入和关停承诺就把读取后窗口排为首个独立包，粒度偏细；用户要求场景级规划后撤回旧派发。H91原始合同/检查器/锁及preflight保持，正式矩阵未运行。先盘点未执行、准入/发送交界、在途未知、已成功、重启/重放及状态不可信的共同验收合同，再冻结整类测量/能力包。不能把所有行写成已缺能力或要求生产采用先行。

- measured（H90 终验）：L2 两轮 5/6、6/6，唯一独立 L3 6/6，七 AC、124 原回归零跳过、384 保护及接受后58不可变项保持。两侧8行同输入，停止表示0→1，A/B/C同事件DENY、回调及create/GET/click增量全0，D正常。H88、旧库、已付恢复和不可读/坏锚拒绝保持。PASS/IMPROVED/SWITCH。仅提交先于读取保证；整表丢失重开、读取后交错、真实控制与渠道失效未测。见 [H90复核](../05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/REVIEW.md)。
- source-inspected / unknown（H91制包）：两个stored入口读取停止事实后另行读取操作并调用原动作，付款另有GET到click间隔。尚无该窗口的实际交错成绩。冻结只测量、8行、同一H89合成图和两个本地SQLite句柄；调度只置于现有方法返回边界，不改产品判断。测量不能把H90排除的顺序写成既有合同违规。

- measured（H89 终验）：L2/L3 各 6/6，七 AC、124 原回归零跳过、325 保护及 24 接受文件保持。12 行独立复算，两个单次事件各只阻断目标，正常控制全保持，整份事件受理为零。共同断点为原生账本缺整份接收、两个门禁只消费按操作绑定的单次事实。PASS/NOT_APPLICABLE/CONTINUE。见 [H89 复核](../05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/REVIEW.md)。
- measured / estimated（H90 制包）：固定 H89 四位置正对照、角色/时间/快照、执行及防错条件，候选仅两产品文件。目标是停止表示 0→1，受理后同键三状态 DENY 与零副作用，D 和历史守护保持。最多两版/两次 L2/一次 L3，当前只有旧基线，无 H90 运行成绩。

- measured（2026-11-25 H88 独立终验）：L2/L3 各4/4、六 AC 通过，268 保护/25 接受项保持，124/124 回归零跳过。正常 create/GET/click=1/1/1；创建前和已建未付时登记合法撤回，重开后两个入口 CONFIRMATION_REQUIRED、增量0/0/0。补充同库两操作事件复用拒绝，四类损坏事实×两入口均 fail closed，原图保持、临时库清理通过。PASS/IMPROVED/SWITCH，停止 B-25 同类扩例。仅本地受信任调用方的单次确认及提交先于读取保证，不外推真实用户/整份委托/竞态。见 [H88 复核](../05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/REVIEW.md)。

- source-inspected / unknown（H89 制包）：IntentMandate 定义含 mandate_id/user_id/authority_version，无撤销状态；当前账本仅有 operation_id 绑定的 confirmation_withdrawals，两个 stored 入口消费该单次事实。整份委托的原生接收面和跨操作效果尚未系统实测。H89 冻结同库三个同委托动作加一个其它委托对照，以两个独立库比较无撤回/单次撤回并清点整份接收能力；不将缺接收入口写成已撤销后误付款。此项是待测假设，不是新能力成绩。

- measured（H87 独立终验）：三轮正式 L2 为 2/4、3/4、4/4，负责人续行记录保持。唯一 L3 4/4、六 AC 通过、124 项原回归零跳过、56 项接受文件与 198 项冻结输入保持。正向创建 ALLOW/1，直接 REVOKED 拒绝前置副作用，原图写接口拒绝该更新。重开后仍为未撤回的 CONFIRMED，旧图付款 ALLOW/GET1/点击1。两个 stored 动作均读同一原图边界，付款路径独立实测。未观察到已受理撤回后付款。PASS/NOT_APPLICABLE/CONTINUE。见 [H87 复核](../05_任务交接/H87_AUTHORIZATION_WITHDRAWAL_PROPAGATION_MEASUREMENT_V1/REVIEW.md)。

- measured / estimated（H88 制包）：原生 Python 枚举原 124 项，使用原合成时间和临时旧库确认两条正常入口为 ALLOW，创建/GET/模拟点击各 1。无撤回入口，原图登记拒绝 REVOKED，作为前后对照的基线。H88 的唯一主要变化是本地持久化撤回事实及既有门禁消费。两个产品文件，最多 2 版实现、2 次 L2、1 次 L3，无额外权限。尚无 H88 产品实现或正式门禁成绩。见 [H88 基线](../05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/BASELINE.json) 与 [合同](../05_任务交接/H88_STORED_CONFIRMATION_WITHDRAWAL_V1/CONTRACT.md)。

- estimated / source-inspected（2026-11-24 H87制包）：HEAD已由负责人同步到df4073d，H85/H86历史HEAD不追改。现有ConfirmationStatus含REVOKED，直接入口检查确认状态，StripeLabLedger保存不可变原授权图，stored入口重新载入该图。组合行为、撤回更新的可接收性与副作用次数尚未实测。H87冻结输入锁、四VP和六AC，以原模拟客户端与临时SQLite量出直接/持久化/重启差异。124项原测试仅枚举、未执行，正式L2/L3=0。

- measured（2026-11-24 H86终验）：正式离线L2/L3各2/2、113项输入零漂移、12个AST直接调用位置及动态kwargs可定位。Runner是离线场景；Stripe已验收受控TEST交易而当次Agent凭据Fact消费未定位；WebShop有H85本地实验来源。实际消费者完整采用链仍UNKNOWN。STOP同仓视图扫描与本地扩例，下一进入条件是实际消费者入口、责任方和可复核脱敏逐次记录。见 [H86复核](../05_任务交接/H86_ACTUAL_CONSUMER_EVIDENCE_QUALIFICATION_V1/REVIEW.md)。

- measured（2026-11-24 H85 独立终验）：L2/L3 各4/4，六项 AC 通过，原86项零跳过。136接受、6候选及11/210/284冻结保护项零漂移。公开原件78/80项独立复算签名、nonce动作摘要、业务快照、UID/socket、拒绝及清理。两轮分别2/3探针，约6.2935/10.9753秒取得明确拒绝。默认BOUND，入口自行取证VERIFIED，拒绝后BOUND，均ALLOW/1。历史P9业务快照与当前身份资格的实验关联有明确边界，生产采用UNKNOWN。见 [H85终验](../05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/REVIEW.md)。

- measured（2026-11-24 H84 独立终验）：正式 L2/L3 各 4/4、五项 AC 通过。118 提交、9 冻结、232 保护项零漂移，双方各 83 公开证据摘要一致。独立使用新根、新 nonce、同一锁定 SPIRE 资产，两轮均为 UID1001 初始发放和签名有效，登记各删一次，第二探针得到明确拒绝且旧证书仍在有效期。删除到拒绝观测约 5.242/5.206 秒。驱动供给本次 Fact 或省略旧 Fact，WebShop 分别为 VERIFIED / ALLOW / 1 和 BOUND / ALLOW / 1。原 86 项通过、零跳过，清理通过，产品改动和外部支付为零。结论覆盖受控来源与实验驱动关联。见 [H84 终验](../05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/REVIEW.md)。

- measured / estimated（2026-11-24 H85 制包）：用已签收的 P9 离线输入重跑同旅程集成原入口，基线 BOUND / ALLOW / 1，原 8 项关联、trace VALID，来源服务调用为零。冻结包验证入口自身获取来源状态与时点并绑原生受治理动作，守住原准入。最多两版实现、两次 L2 和一次 L3，双方各最多一次现场。负责人明确制包不需另外授权，本包沿用上一轮列明的隔离范围，H84 额度不续用。见 [H85 冻结合约](../05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/CONTRACT.md)。

- measured（2026-11-24 H83 独立终验）：L2/L3 各 3/3，五项 AC 通过，原六套 86 项通过、零跳过，26 项提交、14 项冻结、28 项保护摘要各零漂移。同单原入口 BOUND/ALLOW/1，受控当次 VERIFIED/ALLOW/1，独立过去 301 秒和未来 1 秒对照均 BOUND/ALLOW/1，基础身份撤销 DECLARED/DENY/0。回调均模拟。项目增益限于本地身份晋级资格，真实状态和时钟为 UNKNOWN。见 [H83 终验](../05_任务交接/H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1/REVIEW.md)。

- measured / estimated（2026-11-23 H83 制包）：H78 公开证明 7 个输入摘要复核一致，历史观察时点验签 VALID。WebShop 未改入口的同单基线为 BOUND / ALLOW / 1 模拟回调，原六组 86 项通过、零跳过。以固定的受控动作时点测同次证据能否晋级而历史证据不能。冻结仅一个产品文件，最多 2 次实现、2 次 L2 和 1 次独立 L3。评估者预检独立列账，尚无实现或正式门禁成绩。

- measured（2026-11-23 H82 独立终验）：L2/L3 各 5/5，15 项原件锁、27 份提交文件及 45 项接受快照零漂移。五组原回归 44/44、0 skip。S0 环境受阻为保留历史。唯一 L3 使用既有 Windows Conda `agent`，runner 墙钟 4.071 秒。合成 Fact 同输入保持 VERIFIED，调用方撤销标志为 INVALID/DECLARED，凭据引用失配、freshness=false、跨 Agent 均为 VALID/BOUND。仓内 Runner、WebShop、Stripe 静态可定位调用未向 P3 供给凭据验证 Fact。产品改动、真实发行、API、支付为 0。实时保证仍为 NOT_JUDGEABLE。见 H82/REVIEW.md 及本地原始 L2/L3。

- measured（2026-11-19 H81独立终验）：正式Executor L2五项5/5、Evaluator唯一L3五项5/5，原2548保护及修正后2647接受文件独立零漂移；封存stdout先空后写仅一SHA元数据修正，旧2645清单原字节保存/独立核实，未改原始L2或产品。H79同源同输入M01 VERIFIED→VERIFIED、M02错误VERIFIED→BOUND（1→0）；33消费者观测/10密码学负例、原28/18/6及130/16/协议4正21负/8回归独立通过。H80两失败L2不追认；H81 1正式实现登记/1L2/1L3，非正式修复成本另记；历史observed回放不是当前身份认证/实际付款。详见H81/REVIEW.md、evidence/evaluator_review_20261119/POSTCHECK.json。B-23本地代表消费切片关闭，B-24仅候选，未冻结H82。

- measured/estimated（H81制包）：H80R冻结/2517保护/唯一可变测试初始字节保持，无实现登记/L2/L3；新增一份BLOCKED_PRE_IMPLEMENTATION原生入口受限报告已封入30文件快照。当前Evaluator工具实际为Windows pwsh/Win32NT，但不外推其他会话工具能力。Human指示将小修并入瓶颈包，H81同输入前后对照只用H79原已证M01/M02、修复后沿用原33项消费观测与全部原回归，不加产品机制或无关Case。新额度最多2实现/2L2/1独立L3，父H80 2/2/0保持，H80R0/0/0停用；成本低/主动分钟UNKNOWN，尚未运行产品或行为对照。

- measured（H80再次复核）：两轮L2各3/4，第二轮原28/18通过、新增6中1失败，后续130/16/4正21负/8门禁未执行；正式L3=0。独立只读核2430保护、8组三件套、当前产品/测试字节保持；错误测试实际INVALID/DECLARED+identity_credential_ref_mismatch，同步identity/current引用的隔离输入为VALID/BOUND+credential_possession_ref_mismatch。原生Windows子进程导入对照成功；历史Bash/WSL祖先边界UNKNOWN，旧报告结构校验exit2格式缺项保留。REJECTED/INCONCLUSIVE/CONTINUE，不签收产品改善。H80R冻结仅一测试关键字、继承产品摘要、首测试前原生导入环境与全部原回归；最多1实现/2L2（第二次仅同代码导入启动错误）/1独立L3，无新外部权限，未执行。

- measured（H78完整独立签收）：L2/L3各6/6，2116正式保护及2229接受项零漂移；双方真实预检257,815,664字节、5.124/5.085源时钟秒并清理。唯一新根/nonce事件真实完成管理list/create/show、UID1001唯一SVID/目录0700密钥0600-owner1001及持有签名、UID1002同接口PermissionDenied/0身份。原验证器VALID/四true、独立EC/URI/签名及十负例0 VALID；原16/4正21负/8门禁/130通过。匹配同步3次、非匹配1、签名1，Server1/Agent1不重启；85来源公开索引、原始清理和额外只读回查通过，残余进程/私有目录/公开私钥0。Windows L3编排100.598409秒，实际主动分钟/系统网络字节UNKNOWN，下载/安装/付款/外部API/Git0。PASS/IMPROVED/STOP同源扩例，项目SWITCH后续只读测量。
- measured（B-23/H79）：首次L2与唯一离线L3各4/4，2361保护/2395接受项无漂移，原始结果除phase外一致。H78公开证明原observed时点VALID，M01同上下文VERIFIED，M02把mandate/request/payment/identity换为自洽h79-other-agent后仍VERIFIED，P2/P4有效且credential_ref相同；确认错误身份保证归因，无真实付款证据。首反例后M03–M06未执行。源码独立回查定位：验证器已验规范签名上下文，事实未传三元值、消费者未核。task PASS/NOT_APPLICABLE，产品未变。L3编排8.716619秒，实际主动分钟/系统网络字节UNKNOWN；发行/WSL/服务/新凭据/网络/API/真实付款/Git0。H80冻结最小离线修复，尚未实现。

- measured（H77R3签收与H78冻结）：H77R3唯一独立L3 5/5、4正/21负、原16/130、2085接受保持，解析修复PASS/NOT_APPLICABLE，来源完整性仍UNKNOWN。H78独立核63候选/2114保护及8组原始输出；独立8门禁测试和300秒允许/301秒与错绑拒绝对照通过，没有实际预检/发行。候选修正跨时钟误比较、会抢占清理的外层1250秒超时及无成功索引时的失败清理核查；原发行器/资产/原断言不改。
- measured/estimated（H78新授权）：Human在完整范围确认后答复“批准”，原话与前置问题见AUTHORIZATION.json及activation快照。冻结最多2L2、每角色1真实无服务预检、1Evaluator L3/1发行/Server1+Agent1；Executor发行0。仅本机回环及专属socket，无下载/安装/外部API/付款/Git，实际主动分钟/总网络字节未知保留UNKNOWN。完整来源代表切片仍待实际证据，授权不等于能力成绩。

- measured（H77R2再次复核）：提交1938文件与六组L2原始证据一致，接受1939输入。独立实际资产预检5.347秒、257,815,664字节严格核对并清理；随后Server/Agent各启动1，管理根先于Agent，管理列表成功，entry create退出0且唯一results.status.code=0。采集器one_entry不支持results[0].entry，在entry show前报entry object schema；UID取证/叶/持有签名0。原16保护/130回归通过，49运行公开文件摘要正确、1939接受零漂移；失败原清理及额外只读WSL回查残余进程/发行tmpfs/两次预检目录/公开私钥0。唯一L3三过三失败，REJECTED/NOT_APPLICABLE/CONTINUE；本次实际来源完整结论仍UNKNOWN。
- estimated（H77R3离线修复）：以实际完整脱敏创建响应/父列表冻结输入，只改新副本one_entry；实际外层+旧三形态、21项外层/内层拒绝矩阵、原16/130及历史保持统一验收。最多2实现/2离线L2/1离线L3，发行/服务/凭据生成/WSL/下载/安装/API/付款/Git0；无总体时间自设上限，不把纯解析通过当来源闭合或自动新授权。

- measured（H77R再次独立复核）：L2 6/6、1812输入接受后L3 VP-01/04/06通过、VP-02/03/05失败。Windows路径修复生效；已核官方archive SHA及70,187,551字节，进入提取器后因Server179,378,008>157,286,400阈值失败。Agent78,437,656；完整11成员均已只读核对，目标路径/唯一性/普通文件正确，两个成员SHA固定，总binary257,815,664字节。原130、接受零漂移与失败分支独立清理通过，SPIRE服务/新证书/签名0。正式L3=1、发行尝试预算=1、服务启动=0分列；额外只读目录WSL调用1、无提取/执行。最终REJECTED/NOT_APPLICABLE/CONTINUE。
- estimated（H77R2冻结）：将任意阈值改为同一锁定archive的精确两成员profile，且同一生产提取器先过真实无服务预检。最多2版实现/2L2/2次Executor预检，Evaluator1预检/1L3/1发行；无新下载/安装/API/付款及总体时限，原完整来源/十负例/130/独立清理要求保持。先解决固定输入资格，避免只用tiny fixture再触发现场前置错误；本轮未执行新包。

- measured（H77独立评审）：提交L2 6/6、15项任务自检，1693接受文件；独立L3 VP-01/04/06通过、VP-02/03/05失败，原130回归通过。CHECK使用str(relative_path)传Windows反斜杠，被RUN的POSIX严格入口拒绝；发生在DISPATCH与wsl.exe之前，实际SPIRE/私钥/支付0。POSTCHECK复现原异常并验证同路径.as_posix()可通过原保护，无新运行；接受1693零漂移。H77 REJECTED/INCONCLUSIVE/CONTINUE，原正式L3=1/实际运行0分别保留。
- estimated（H77R冻结）：只修新复制检查器一处调用参数，接收方/发行实现/产品不变，新增实际argv表达式到入口的离线联调；最多2离线L2，Executor实际0，Evaluator1正式L3/1真实运行，无新下载/安装/API/付款、无总体时间上限。修复本身不声明产品改善，来源是否闭合仍待独立实际证据。

- measured（本轮Evaluator只读审查）：H76公共20文件摘要一致，1502原保护项/冻结不变，103份输入另封；独立密码学/原十负例及原130回归通过。旧路由结构门禁exit=1。历史WSL3轮、成功1轮，原补充文档首次+1修复边界偏差保留，负责人原话未给数字上限。原Docker正式L2/L3=0；独立新鲜来源仍UNKNOWN。审查见H76/REVIEW与H77/evidence/preparation。
- estimated（H77冻结）：同目标、同固定SPIRE/Ubuntu/UID/直接EC根；Executor新发行0，最多2版脚本/2离线L2，Evaluator1正式L3/1实际新根新nonce运行，无新下载/安装/API/付款；不设总工作时长上限，防挂单命令180秒/单运行20分钟。全部AC通过才计受控实际来源切片改善；本轮只制包，不计新发行或能力成绩。

- measured（H75续行设计）：固定SPIRE1.16.0官方资产摘要、Python3.12.13镜像单平台digest及三个签名依赖wheel；4文件主体75,225,023字节，含image声明压缩层合计120,646,653字节仅为首次下载估计，实际尚未下载。形成H76八AC/六VP/十消费反例与统一L2/独立L3；运行授权待补。负责人取消后续制包自设时间限制，旧25分钟窗口与超出记录不追改，续行实际主动UNKNOWN。

- measured（H74R签收）：44提交文件、3修复源码/测试、24冻结与2969保护输入保持，L3 6/6，独立10组、16单测、原19/9/74通过。补充T+1/T+2/T+10重试保留首次digest/payload，过期拒绝，外来同名PaymentStatus/Decision拒绝；原H74拒收不追认。
- measured（H74主线收尾）：父Executor保守25.019200+修复7.882246=32.901446；父Evaluator19.284441+修复制包9.693477+修复复核9.983433=38.961351；合计71.862797/150分钟保守整窗，actual active UNKNOWN，原20.825250账本与补录均保持。
- estimated（H75设计）：新Evaluator资格准备25分钟/最多6次公开网页工具调用；只读本地已有资料、官方公开材料和命令存在性，不安装/下载/启动服务/签发凭据/付款。真实SPIRE签发、进程证明与轮换尚未验证，实际运行环境和权限需明确后另冻。
- measured（H75设计收尾）：Docker客户端/Compose存在但本地Linux engine连接失败，实际签发未运行；公开网页工具5次。准备保守整窗超自设25分钟，停止新核验并标BUDGET_EXCEEDED_NOT_ACCEPTED，精确整窗/超出数与actual UNKNOWN见H75/evidence/preparation/CLOSE.json；草案未签收，旧预算不追改，H74R签收保持。

- measured（H74独立拒收）：147任务文件、4源码/测试、20冻结与2687保护项保持；L3 8/8，原19/9/74通过，独立九组7通过/2失败。原GateContext在T与T+1秒重存失败；外来同名PaymentStatus转成原生类型，闭集/原图保真不成立。只有正常本地路径增量证据，整体INCONCLUSIVE。
- measured（H74费用审阅）：原Executor20.825250分钟未覆盖收尾，SUBMISSION原声明至少晚于END0.916958秒，报告/提交mtime支持后续收尾；实际主动UNKNOWN，不判超105。Evaluator19.284441分钟，唯一L3；建议追加到06:24Z的25.019200分钟保守Executor上界，旧账本不回写。
- estimated（H74R冻结）：只修上述两问题并追加成本，45执行/15评估、1实现/1L2/1L3，累计105/45/150含父包与制包；原计数保留，旧13及19/9/74、独立冻结反例必须通过。尚未实现，外部0。

- measured（H73独立验收）：48提交/50冻结/100接受文件、2549保护输入与两私有源摘要保持；L3 6/6，521引用与三session/intent/charge/resource精确关联通过，12边界96项语义逐项支持。三独立点击/操作行共同缺原事实引用，非仅工厂代码重复；其它私有来源未知，原领域时间UNKNOWN。
- measured（H73成本）：Executor21.395618、Evaluator19.325080，合计40.720698/150分钟保守整窗；1L2/1L3，制包28.562003分钟单列，实际主动UNKNOWN。原H72/H72R拒收/H72R2最终签收不改判，外部0。
- estimated（H74冻结）：同一新合成三单元/固定原src基线，单主要变化为不可变GateContext存储+既有adapter消费；105执行/45评估、总150分钟、2实现/2L2/1L3，原安全9/业务74及Stripe三个模块回归。只有未来实测才计本地增量，未执行能力或产品测试，不继承旧权限。

- measured（H73制包静态核对）：N01恢复保留原标识并重新调用当前时间工厂；点击收据记录ALLOW/回调数，ledger记录交易标识。08:54:39Z负责人续行授权存在，必须纳入合法续授解释。这些已知机制本身不算新漏洞或共同断点；完整原授权是否在已存材料中可回查仍unknown。
- estimated（H73新包）：150分钟保守角色窗，Executor≤105/Evaluator≤45、2L2/1L3、一版方法；固定四例/三个边界及两个白名单私有材料，网络/安装/服务/浏览器/付款/模型服务0。制包成本另列，不继承已关闭H72预算或权限。只测量，未来能力包须由共同证据断点支持。

- measured（已测）：H62 REVIEW、L2/L3各8/8；独立16恢复/24批准/6商城旅程/25AP2。同类新M06付款1/订单0/库存5→付款仍1/订单1/库存4，恢复新增付款0；原2638保护文件及3来源库保持。
- measured（已测）：H63准备核对H62目录1154文件和原2638保护文件；CartTrace源固定revision `86cab5e539e161e0915d78d8abdd9023f09b411e`，按路径规则取得6份JSONL预览，未按结果挑选。
- measured（已测）：六预览只有session/message记录。**预览缺独立后端状态表是已知边界，不作为待重新发现的假设**；整个数据集的支付/订单/事件表充分性不由预览推断。
- measured（已测）：H63独立L3结构4/4，但AC-03合同语义错位，REJECTED（拒收）；原件保留。H63R已独立L3 3/3、30映射语义审阅和4个原错误变异通过，PASS（通过）/NOT_APPLICABLE（修复不评价能力增量）/STOP（停止该视图）。30映射为8项部分输入、22项缺失、0项完整可观察，不是产品通过/失败率。
- measured（已测）：S01/S02/S03/S06仅有P1/P2零散输入，S04/S05对应输入缺失；六例均无完整P3执行身份、P4来源/上下文策略、P5治理回放输入。S03/S06调用关系可读，但重复同一六例的新增信息收益低。
- measured（已测，仅准备）：H64固定数据revision及GitHub回放实现commit `61f05faadc64badedd0ca727778ea5c9cd384702`，校验14份静态代码/文档的Git blob归属，取得完整数据索引和校验和；未查看新episode、未安装解码器或运行回放。代码存在缺call id按顺序回退及域名替换，已知边界不充作下一轮发现。
- estimated（估计）：H64 180主动分钟/2L2、6个固定规则新样本、20GET/256MiB，唯一隔离PyArrow解码依赖约28.6MB；不安装上游，不调用产品/模型/支付。准备获取与执行预算分开，实际见H64 PREPARATION/READINESS。
- measured（已测）：H64选定6新例、4 Parquet及11/12 world材料，18 GET/88,710,515字节、两次同envpack失败，1次解码安装；独立L3结构4/4、8纯函数例通过，但AC-02/03语义不通过，REJECTED/INCONCLUSIVE。第4例关联值32/32/34混拼；第6例协议total=4425、currency=usd、checkout可见而被统一payment=None丢弃。
- measured（已测）：缺失envpack属于INPUT_LIMIT（输入获取受限），不是源文件不存在；5例world对完整。原始付款观察、单位/授权绑定、实际后端状态必须逐维清点，不能由通用空输入推断全部源不可用。
- estimated（估计）：H64R仅复用原六例与现有材料，90主动分钟/2L2/至多12次sample读取，网络/安装/产品/回放/模型/付款0。先修离线关联/金额清点比重试下载更有直接信息收益。
- measured（已测，仅开工准备）：评估者核对H64R原3816保护/7冻结文件；3812保护及7冻结一致，另4文档共10行各去除两个行尾ASCII空格，原Git blob字节均匹配旧摘要。已保留原BASELINE/合同/路由/地图及差异文件原字节，显式迁移至HEAD 211151e；CHECK/计划和测量范围/预算不变。未读取样本、未执行正式L2/L3，不增加产品能力成绩。
- unknown（未知）：本仓控制效果、独立未见样本泛化及新来源可用性；真实商户/PSP/客户价值。不能由六预览缺本仓内部对象推断整个数据集不可用。
- measured（已测）：H64R独立L3 4/4、四损坏变异及原八用例通过；独立读六源核对全部提交引用与12文件/14个L2文件摘要。5调用为4完整/1部分，6响应金额及4请求额度观察、4用户金额确认；call-32/34分开、call-68的4425/usd保留。修复PASS/NOT_APPLICABLE，六例NOT_JUDGEABLE不等于产品失败。
- estimated（估计）：H65 75主动分钟/12源读取/1版/2L2；只测现有单位与确认桥，无新GET/安装/回放/模型/产品/付款。wallet有Consent/checkout/amount结构线索，但每例实际绑定及单位是否可证明仍unknown。
- measured（已测）：H65独立L3四VP与四原变异通过，接受快照12文件/14个L2文件保持；独立源审阅发现四条用户消息的arguments.consent有amount/currency/checkout_id/given=true，分别seq40/79/31/64。第4例tools[8]直接定义allowance.max_amount的最小货币单位。原分析的缺失清点不成立，AC-02/03/04不通过而拒收，不能据此停止当前来源视图。
- estimated（估计）：H65R 45主动分钟/8源读取/1版/2L2，网络/安装/模型/产品/回放/付款0；只修已定位漏读，完整链仍须逐字段独立验证。轨迹直接记录确认不等于真实用户身份或清算。
- measured（已测）：H65R独立L3 4/4、六损坏通过，独立枚举确认1/1/0/1/0/1，57引用和12提交/14个L2摘要保持；第4例同例checkout/5818 USD/最小单位→call-34 ACP 201→同调用令牌返回可回指，call-32无wire。AC-01/02/03通过，AC-04因失败读取缺遥测且sample_reads改为不同样本数不通过，整包REJECTED（拒收）/NOT_APPLICABLE（不评产品增量）。不能声称已证明超预算，也不能把声明6当实际累计次数。
- measured（已测，静态参考）：IronClaw固定提交b0b999d96781516ee05e6ba961d6f3ead900da96可定位审批服务、宿主和凭据注入入口；此前仅局部阅读，未验证金融消费者或运行效果。旧金融Issue、签名计划及抽查未合并PR不替代主分支接线证明。
- estimated（估计）：H66 90分钟墙钟/20次来源请求/单目标2次/正文归档8MiB/并发1/1版/2L2；失败照计、事前预留，不安装或执行上游/模型服务/产品/钱包/付款。具体金融入口及可独立判定边界仍unknown。
- measured（已测）：H66独立L3 4/4、七损坏通过；9固定文件blob向官方复核、11引用复算，10顶层/14个L2/15来源/4辅助快照保持。15请求=11成功+4失败、归档304999字节、请求/L2账本763.844秒、1L2；报告收尾约22分钟内。通用宿主/审批/凭据接线可参考，但金融消费者NOT_FOUND_IN_VIEW，PASS/NOT_APPLICABLE/SWITCH，停止本IronClaw接入视图，不作全仓不存在结论。
- measured（已测，仅准备）：ACP官方Issue #295提出必填幂等键在MCP变可选；评估者固定官方HEAD 7fdd78df677a94dce04c770644b0fbbb1401272b，核5原文blob/许可并提取必要JSON/文本投影。REST规范限定所有POST，OpenRPC meta.required仅含api_version，工具绑定涵盖4变更/1读取；机器描述仍unreleased（未发布），尚未执行H67正式成对测量，不证明服务端重复扣款。
- estimated（估计）：H67 45分钟墙钟/2分析尝试/2L2，固定10元数据探针+5示例观察；标准库、网络/安装/上游服务/产品/模型服务/钱包/付款0。只测绑定契约，不扩成完整RPC验证器。
- estimated（估计）：H63测量120主动分钟/2L2、中低维护成本，运行时/模型/支付/安装0。准备匿名公开读取10文件/727832字节；公开网页研究另计，不写成零网络。
- measured（已核人工决定）：2026-11-11 Human明确H67先不执行，优先外部沙箱/测试网络，授权先搜索一轮；H67仍无REPORT/RESULT，不发起L2/L3，不因延期得出技术成败。六类攻击与新增攻击扩展不派发，已有本地回归保留。
- measured（已核公开资料/发布源码）：Stripe官方文档列匿名沙箱、邮箱及七天临时凭据；已发布CLI v1.55.10的sandbox.go包含匿名创建和邮箱处理。固定主分支f3ea38a25b2836cd127125331b6569e94833928f可定位challenge/provision接线，Apache-2.0；Windows发行包元数据11,929,882字节，未下载/执行。PayPal订单查询/幂等与x402测试网文档作为备选，不等于本机运行可用。
- estimated（估计）：Stripe单沙箱/单资源、正常及响应丢失恢复两情形可作为首轮；一次创建、60分钟/20API/至多两笔合成USD1.00付款、真实资金0仅为待冻结预算。邮箱、创建/密钥/安装/API权限及真实可观察性仍缺，不恢复支付宝或测试网延期权限。研究见docs/02_未来规划/外部沙箱与测试网络首轮筛选_20261111.md。
- measured（已核设计决定）：Human在比较后选Stripe并要求长执行包、低手工门槛；原60分钟小切片仅为历史估计，由H68待批预算明确替代，不能当作已执行成本。真实任务范围是本仓订单/交付加外部Stripe托管结账，不是独立外部商城。
- measured（仅制包基线）：既有订单/恢复/生命周期/治理/上下文61项针对性测试通过；证据checker的2合成对照/15损坏反例通过。均未产生Stripe运行成绩。官方前端有防自动化限制，匿名邮箱接受、事件监听权限与无人值守结账仍UNKNOWN。
- estimated（H68待授权）：单主要变化为Stripe适配接缝；480主动分钟/24小时、2实现尝试/2L2/1L3，一次匿名创建、4会话/至多3笔合成USD1.00付款。可控服务端API120次，现场80、Executor/Evaluator各20只读；浏览器80操作、下载3请求/64MiB。合成联系标识可尝试资格；需真实邮箱/登录/验证码即受限，不绕过。仅制包，全部运行权限仍false。
- measured（H68执行及受阻复核）：后续仓库授权记录为GRANTED；Executor约112主动分钟、1实现/1L2、两个Chrome探针失败，外部创建/API/会话/付款0，四旅程NOT_EXECUTED。六份L2原始输出摘要独立相符；独立完整性/预算/结构/判别器自测通过，但原生Windows74项回归有6项数据库清理ERROR，过期确认放行/原会话恢复错绑/付款通知错绑均复现。首个57文件快照保持，未接受正式L3。
- measured（仅本地浏览器资格）：Evaluator用现有mcp__Playwright隔离上下文完成自写data页打开/点击/读取并关闭，共5操作、Stripe0；不能外推Stripe服务资格，也不反推Executor当时工具可见性。H68R冻结独立对照保留合法路径，并补充未来确认/错误request关联反例；9测试含子例8失败，作为红基线，不是L2。
- estimated（H68R本地修复）：90主动分钟/4小时、2实现/2L2/1L3，四候选文件；网络/安装/浏览器/付款/提交/推送0。修复后再冻结Stripe环境资格测量，不直接重启H68付款额度。
- measured（H68R独立签收）：44文件接受快照、三份L2摘要及1331保护输入复核；仅两产品文件修改、原测试未削弱。独立Windows L3三项PASS、安全9/9、指定74/74；额外到期微秒/逐项关联错绑/已知付款后的外来通知/事务回滚与句柄关闭四检查通过。1实现/1L2/1L3，外部0；PASS/NOT_APPLICABLE，停止同类本地修复扩例。
- measured（H69制包来源）：重新读官方v1.55.10匿名创建与sandbox客户端源码、CLI/监听文档，定位创建失败会进入登录后备路径；新包只采用公开challenge/provision语义并在失败时停止。未执行源码/CLI或创建沙箱。离线checker两失败对照/八损坏反例通过，不计运行资格。
- estimated（H69入口资格）：45主动分钟/2小时且不越过原H68 2026-11-13T00:59:06Z截止；一次原授权匿名流程、challenge/provision各1 POST无重试、本账户现场GET2/双方独立各2、下载3 HTTP/64MiB、监听/回调各1且60秒。0会话/0支付/0浏览器，不重置共享配额；服务接受合成联系标识和监听权限仍UNKNOWN。
- measured（H69独立签收）：1395保护输入、50接受文件及六份L2元数据摘要保持；原生Windows L3三项PASS。challenge/provision各一次200，创建凭据/账户及挑战解绑定；初始/Executor/Evaluator各一次同账户GET均403，三份原文错误类型/消息相同。1实现/2L2/1L3，下载/监听/会话/付款/浏览器0；PASS/NOT_APPLICABLE/STOP。创建机会已消费，不能重建；403只证明Account读取受限，不外推Checkout/监听或整个沙箱不可用。
- estimated（H70权限适用性）：35主动分钟/60墙钟、1版/2L2/1L3、官方公开来源12 HTTP/4MiB/单URL2/并发1；仅复用H69材料及官方固定源码/文档，形成四维权限矩阵与最小证明建议。Stripe运行API/凭据请求/安装/浏览器/会话/付款0。是否需要Account读取和是否有更合适同环境证明仍UNKNOWN；不延长原H68运行授权。
- measured（任务粒度决定与制包核验）：Human要求较长、可多步骤的执行包，先解决最难点，最终统一复核且不降质量。Evaluator确认H70无RUN/REPORT/RESULT/账本，原包及r114/路由原字节保留，未出成败结论。重新核官方key/CLI/监听文档与v1.55.10源码；Context7不可用后用官方网页，未下载CLI或调用Stripe运行API。泛用key文档不能替代rkcs_test_的特定权限实测。
- estimated（H71长资格测量）：120主动分钟/4小时墙钟且不越原2026-11-13T00:59:06Z；2任务脚本版本/3L2/1L3，24公开HTTP/8MiB，现场/Executor/Evaluator各三个固定GET一次，固定ZIP3 HTTP/64MiB，listen/接收器各1且60秒、本地浏览器8操作。七步前置满足自动继续，最后一次统一签收；零创建/会话/付款/产品改动。同凭据上下文不升级为独立账户真实性；Checkout写入与托管前端仍待后续。
- measured（H71独立拒收）：1491保护输入/15冻结输入/64接受文件保持，原生Windows L3八项、安全9/9、回归74/74通过。现场三个固定GET各200且完整空列表，来源四请求两成功归档/两HTTP200后超时，一次ZIP尝试状态/接收量未知；1实现/1L2/1L3，监听/浏览器/会话/付款0。最终矩阵仍写GET未测，三处引用仅导航；离线23字节/HTTP200后超时分别复现来源记0、下载记0并清空状态。AC-02/07不通过，REJECTED/NOT_APPLICABLE/CONTINUE，不能据此证明历史超预算。
- unknown（历史失败传输）：两次源码与一次ZIP完整归档为0，但实际接收字节未保留；下载异常阶段/是否已获HTTP状态也无法恢复。请求次数已知、字节额度不应按0消费计算，原64MiB下载额度的正余额不能保证；不因还有请求次数就自动重试。
- estimated（H71R离线修复）：120主动分钟/3小时墙钟、2任务脚本版本/3L2/1L3，六步连续修复历史纠正投影、最终矩阵、有界逐块采集与独立故障驱动，保留9安全/Windows74。原文/旧产品只读，新增网络/下载/API/安装/浏览器/服务/会话/付款/提交推送0，不延长原H68运行授权。
- measured（H71R独立拒收）：1596保护输入/11冻结输入保持，矩阵三GET与正文引用/历史UNKNOWN修好，12份自定义原始日志摘要相符。原生Windows独立六项、11传输/9安全/74回归通过；但归档后rb读取PermissionError无元数据返回，另有既有目标误归摘要风险。第1预算预留仅说明，第2/3轮由自建run_l2写非标准Gate/元数据，不构成合法公共L2。原合同第4/5项不通过，REJECTED/NOT_APPLICABLE/CONTINUE。
- measured（接受顺序纠正）：Evaluator曾在结构拒绝后捕获67文件快照并继续独立复现，顺序错误；SNAPSHOT_CLASSIFICATION明确它仅为候选审计保全，不是合法接受。原报告格式修正前字节另存，原自建门禁未转写；独立L3输出仅作诊断，不替代缺失L2。
- estimated（H71R2）：120主动分钟/3小时、2实现/3公共L2/1独立L3；复用正确矩阵/纠正投影，只修输出独占归属和全生命周期失败保真，以原11+新9生命周期探针、9安全/Windows74及公共结构门禁统一验收。新增网络/API/下载/安装/浏览器/服务/环境/会话/付款0；旧运行授权2026-11-13T00:59:06Z已过期，历史下载正余额仍未证。

- measured（H72独立复核）：接受前1843保护/12冻结/29引用及L2 15份三件套一致；317任务文件、4产品/测试文件和2380既有私有文件复核后无漂移。原安全9/回归74/取证11/生命周期9与新增URL6独立通过；实际拒绝自测14/16，两个用例依赖调用者原路由。
- measured（H72外部事实）：独立13GET确认同一测试环境4会话/3付款意图/3收款，全部原对象测试模式、usd/100最小单位、订单/操作/运行/资源关联；N01付款交付、C01未付取消、R01原付款UNKNOWN后重启查询恢复、D01交付记账失败恢复。3原始通知独立HMAC复算及9篡改/错误秘密/过期反例拒绝。D01先收到119字节再注入记账失败，传输中断重传未测，不追加该新AC。
- measured（H72最终拒收）：公共L3 14/15，VP-02报special_node_live_query_drift；独立证明原生标签2684354589、20字节载荷及数据摘要相同，英文/中文说明文字摘要不同。另预算摘要固定evaluator_reads_spent=0，实际账本13。AC-01/02/10/11不通过，REJECTED/INCONCLUSIVE/CONTINUE；原完整合格目标0/4未签收，四功能事实独立列账，不追认原Gate。
- measured（H72成本）：可控现场35/执行者只读5/评估者只读13=53/120，浏览器66/80，会话4/4，3次各USD1合成付款；真实资金0。1传输/2HTTP/11,929,882字节；追加授权监听/商户启动2/3，执行者主动时间上界约103分钟，评估另累计。CLI/浏览器不可全观测子请求仍UNKNOWN。
- estimated（H72R离线修复）：60主动分钟/3小时墙钟、2新包L2/1新包L3，累计主线480分钟且不越原2026-11-16T04:08:37Z；只修本地化结构核验、角色无关隔离用例及账本计量。原H72的唯一L3已用尽，新包不重跑付款/原L3，不覆写旧合同、报告、收据或失败证据。

- measured（H72R复核，原件保持）：公共L2/L3均11/11，但独立错误字典断言在ParserCases正常返回，单命令test_count 9→99仍被隔离入口接受；AC-02/03不通过，最终REJECTED/NOT_APPLICABLE/CONTINUE。原生结构/角色构造/53与13计量修复正面证据保留。
- measured（H72R2负责人执行及独立复核）：负责人直接授权及追加离线窗口已登记，不冒充Evaluator事前冻结。接受前2232保护/2393私有/69父快照及109任务文件不变；两轮L2各12/12、24三件套，合同格式修订未改变代码/计划。独立L3 12/12，原12解析+2框架完整性、两角色各17、原11/9/9/74/6通过。
- measured（H72R2反例闭合）：Evaluator另建程序确认标准fail继承、错误字典及直接fail抛AssertionError；完整收据正对照通过，单命令9→99、缺null计数字段、null改0、顶层99均拒绝。旧H72/H72R代码/报告/收据/Gate保持，新增API/支付/服务/浏览器/安装0，不再做同类工程修复。
- measured/unknown（H72R2预算）：首BEGIN 12:39:00Z至首END 13:15:08Z，墙钟36.133333分钟；原账主动时间UNKNOWN、charge=30，不能把30称为已证明的保守上界。追加授权有效，全Executor段墙钟上界48.947316、续接12.813982；169.035为不含全部Evaluator成本的部分账面数。无证据证明实际超30/480，也无证据证明原首窗≤30；AC-07待负责人补证或明确例外，HUMAN_REQUIRED/NOT_APPLICABLE/HUMAN_REQUIRED。

- measured（H72R2负责人裁定收尾）：Human明确选择首段36.133333分钟保守入账、实际UNKNOWN和原记录保留、补列评估成本；OWNER_DECISION.md保存原话与来源。COST_RECONCILIATION.json校正已知Executor上界175.169316分钟，另列评估窗口/未知范围；主线保守包络将除已终态负责人等待段外的其余墙钟计入，记录时461.316193/480，不冒充实际主动精确总数。109原接受文件保持，新增最终REVIEW_OWNER_DECISION.md签PASS/NOT_APPLICABLE/STOP，原REVIEW及授权/账本/Gate不回写。

## Bottleneck register / 瓶颈登记表

| ID | 范围 | 当前证据与缺口 | 状态 |
| --- | --- | --- | --- |
| B-01/03/07/08/09/10/11/12/13/14 | 评测、重扣、轨迹、责任与消费 | 继承r100代表性结果，无新反例不重开 | LOCAL_STAGE_CLOSED |
| B-05 | 数据最小化 | 字段名级本地闭合；真实PII/完整隐私治理未证实 | LOCAL_STAGE_CLOSED |
| B-15 | 主体真实性来源 | H78已独立签收受控实际新根/登记/UID/SVID/持有/拒绝/清理代表闭环；停止同源发行。组织/用户/硬件身份及生命周期不外推 | STAGE_CLOSED_CONTROLLED_ACTUAL_SOURCE_SLICE |
| B-02/04 | 血缘收益与Agent行为长尾 | 无新共同失败 | WATCH |
| B-16 | 横向外部攻击 | H46源片段停止，不重测既知完整入口语义缺口 | WATCH / SOURCE_SLICE_STOPPED |
| B-06 | 真实身份/外部支付服务方 | 支付宝有效Payment-Proof及绑定仍缺；Human后置，权限不恢复 | DEFERRED / HUMAN_DEFERRED |
| B-17 | 商城批准与业务恢复 | H62本地代表性已付无单改善；真实采用/履约未知 | LOCAL_SLICE_CLOSED / REAL_ADOPTION_UNKNOWN |
| B-18 | 独立外部轨迹可判定性 | 4源确认与1额度/令牌链已核；整包预算不签收，独立产品控制效果未测；当前六例静态修补停止，非整个数据集无效 | WATCH / CURRENT_STATIC_VIEW_STOPPED |
| B-19 | 外部具体金融执行消费者资格 | H66资格研究通过，通用机制可参考，固定有界视图未定位金融消费者；不继续追通用运行时，不否定全上游 | WATCH / IRONCLAW_VIEW_STOPPED |
| B-20 | 协议到工具绑定的幂等契约保真 | 原线索保留；Human决定先不执行H67，成对测量、服务器行为及资金影响均未测 | WATCH / HUMAN_DEFERRED_NOT_EXECUTED |
| B-21 | 外部可执行测试环境与治理/恢复接缝 | 受控四功能事实、H72R2独立技术门禁及明确预算例外闭合；修复PASS/STOP，旧拒收不改判；真实生产接入/独立采用仍未知 | STAGE_CLOSED_CONTROLLED_REPRESENTATIVE_SLICE |
| B-22 | 外部操作的授权/确认事实连续性 | H74R原反例/成本闭合，正常本地stored路径代表切片关闭；legacy未强制迁移，历史外部交易未补造快照，真实外部采用未知 | LOCAL_STORED_REPRESENTATIVE_SLICE_CLOSED |
| B-23 | 已验证凭据事实的消费上下文 | H79独立反例后H80被拒收，H81完整L2/L3各5/5、2647接受文件零漂移，M02错误晋级1→0、M01保持、33观测/10负例/必要回归均通过；历史身份事实不可外推为当前认证 | LOCAL_REPRESENTATIVE_SLICE_CLOSED / H81_PASS_IMPROVED_STOP |
| B-24 | 已验证事实的使用时点有效性/撤销与轮换连续性 | H85本地受治理入口责任切片签收，实际采用、生产时钟和权威状态责任待证 | LOCAL_CONSUMER_SLICE_CLOSED / ACTUAL_CONSUMER_EVIDENCE_REQUIRED |
| B-25 | 已保存批准之后的用户确认撤回传播 | H88 独立签收本地受信任单次撤回、两 stored 入口、重开库及必要守护；停止同类扩例 | LOCAL_REPRESENTATIVE_SLICE_CLOSED / H88_PASS_IMPROVED_STOP |
| B-26 | 整份用户委托停止的跨操作传播 | H90 独立6/6、七AC签收三同键状态、D隔离和历史守护；限停止先提交后读取 | LOCAL_REPRESENTATIVE_SLICE_CLOSED / H90_PASS_IMPROVED_STOP |
| B-27 | 授权撤回与停用的生命周期处置闭环 | H91整类测量签收；共同缺口是持久准入顺序及原生控制关联，已有恢复安全保持，H92一个机制消费整表 | ACTIVE / CONTRACT_FROZEN_DURABLE_ACTION_CONTROL |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-27

B-15、B-21/B-22、B-23、B-24、B-25与B-26本地代表切片保持关闭。当前第一问题是现有局部通过尚不能回答“用户停用后，未开始、在途、已成功、重启恢复的各笔交易最终如何处理”。先把受理、禁止新准入、在途结果和处置责任区分，避免将源码上的读后窗口直接定性成漏洞。该场景横跨B/C/D，已有能力应复用，但停止与恢复的组合不能靠单模块PASS推定。相比旧凭证缺独立消费点、B-24缺实际采用材料及B-20人工延期，场景合同和本地组合证据有更直接价值。真实渠道取消和恶意存储回滚仍受独立前提约束。

H86仅测仓内采用资格。项目目标在本地可重置边界，实际生产采用不是全部后续能力测量的前置条件。H87不重复身份发行/时点扩例，测量另一控制事件——原批准保存之后的新确认撤回。旧原图保真与新撤回信号的接收责任各自独立记录。

## Active hypothesis / 当前假设

Hypothesis ID: H-92-DURABLE-STORED-ACTION-CONTROL
Hypothesis status: CONTRACT_FROZEN / CAPABILITY_EXPERIMENT

同一SQLite事务序列原子判定停止与唯一动作准入，准入先提交后才进入原门禁/替身动作，可使O5/O6新规则下可靠拒绝，已准入的O7保留在途；持久事实同时防止ADMITTED/UNKNOWN重放，并支撑原生恢复及只读生命周期视图。普通read_clear不能改名充当新能力。原身份/绑定/策略/确认门禁保持，先准入不等于最终允许付款。

H92单一主变化为一个本地持久执行控制事实Module，不另建Runtime/状态机；只改账本与Stripe adapter两个产品文件，新增单控制表。接受/准入全局sequence、终结/未知和恢复关联、只读视图在同包建设，S0–S7前置自动继续，统一L2/L3。旧库停止保留并标历史顺序缺失，不伪造过去；真实取消、外部凭证/主体、恶意存储回滚继续受条件约束。

## Candidate experiments / 候选与比较

| 方向 | 分类与动作 |
| --- | --- |
| 实际SPIRE来源的独立新鲜复验 | STOP_H78_SOURCE_SLICE：已独立签收，停止同源发行/扩例，组织/用户/生命周期不外推 |
| 已验证事实的消费上下文保真 | CLOSED_B23_H81：L2/L3各5/5签收；错误归因1→0，停止同类扩例，不重跑历史拒收/来源 |
| 保存后单次确认撤回传播 | STOP：H88 已独立签收本地代表切片，不继续扩字段、UI 或同类案例 |
| 整份委托停止的跨操作传播 | STOP：H90本地提交先于读取切片独立签收，不继续同类扩例 |
| 旧支付凭证使用时有效性 | WATCH / REFERENCE_ONLY：先有真实可回查的停止事实，再选定一个合成或获授权的凭证消费点进行同凭证前后对照。FluxA 材料作为机制与证据参考 |
| 读取与副作用间的在途竞态 | H91场景内候选诊断，不再独立FIRST；先决定原生业务准入和关停承诺，再判读后继续是否需修 |
| 授权停用的生命周期处置闭环 | FIRST / H92：H91整表证据已足够停止重复测量，建设持久准入/停止排序及原生生命周期证据，已有恢复守护复用 |
| 整表丢失/备份回滚后停止事实连续性 | WATCH：H90只验现存事实及当前句柄查询不可用，未验重开后的完整性；先明确存储威胁模型，不宣称抗回滚 |
| 历史身份事实的使用时点和来源状态连续性 | H83/H84/H85本地代表切片签收，H86仓内资格已测。STOP本地扩例，实际采用链待材料 |
| 原上下文stored切片 | STOP：H74R闭合本地代表性断点，不再扩字段/Case，外部legacy采用不升级 |
| 真实主体/发行者/强认证/凭据治理 | DEFER_EXECUTION：重要且未证实，真实来源与消费者/权限条件尚不足；H73不替代此能力 |
| CartTrace固定六预览 | REFERENCE_ONLY（只参考）；来源资格测量完成，STOP_PREVIEW_VIEW，不升级ABSORB（吸收）或导入产品；不外推整个源 |
| CartTrace完整表/world/静态回放实现 | REFERENCE_ONLY（只参考）；保留4确认/1额度令牌链，当前六例静态视图停止；不因预算拒收而重复重跑，不启动完整回放栈 |
| IronClaw执行权限与凭据接缝 | REFERENCE_ONLY（只参考）；H66研究通过但有界视图未找到金融消费者，停止当前接入研究，通用机制不当作资金安全证明 |
| ACP REST→MCP幂等键要求 | REFERENCE_ONLY（只参考）；H67人工延期、未执行，不修上游/产品、不声称真实重扣 |
| Stripe匿名隔离沙箱＋Checkout | 受控功能事实与H72R2技术修复独立验证，预算例外已登记；阶段关闭/STOP同类工程及付款 |
| PayPal Sandbox | 备选；订单/收款回查及幂等有官方依据，开发者和买卖测试账户未核，不登录/创建 |
| x402 Base Sepolia | 备选；公共测试结算有官方依据，但钱包/签名/领币/交易仍需单独权限，不默认采用链 |
| UCP samples #277履约引用/报价 | WATCH（观察）；公开复现线索未独立运行，不凭此重开H62或宣布授权漏洞 |
| APort Vault | REFERENCE_ONLY（只参考）；文件访问需申请且分享账号信息，不申请/下载 |
| Gordon AgentCommerceBench | REFERENCE_ONLY（只参考）；受限且含生产来源，不申请、不接链/服务 |
| ModelScope ACEBench线索 | REFERENCE_ONLY（只参考）；工具能力资料不足替代授权/支付状态证据，不展开 |
| E本地再扩、通知平台、第二商城、H56 | 不派发；缺新消费者需求或反例；H56仍未执行，无新成败结论 |

## Reassessment triggers / 继续、停止与切换

- CONTINUE_H92：原生持久排序、O5/O6前置拒绝、O7在途不假取消、UNKNOWN不重放、恢复/原生视图及全部守护统一通过；只有仍有重要共同断点且净收益值得才续包，否则STOP/SWITCH。
- STOP_H92：停止后新准入、无可信准入副作用、重复/UNKNOWN重放、旧图/已付漂移、未知伪报完成、必要回归/清理失败、超预算/范围/权限立即保全交Evaluator。不能以重新定义read_clear回避能力要求。
- STOP/SWITCH_H91：场景整表在当前边界内有代表证据、未知安全停留和责任明确后停止扩例；无共同收益或需真实渠道/新权限时重排。已付不可逆动作不因停用被改写成取消。
- STOP_ZERO_TOLERANCE：停止先于读取仍放行、错绑定受理、读状态未知仍放行、历史漂移或守护失败立即保全交Evaluator；读取后窗口是待测边界，记录后只完成冻结守护，不自行修产品。
- STOP_H90：受理后副作用、错绑定受理、不可读放行、历史漂移、对照或清理失败、突破预算或新权限需求，立即保全并交 Evaluator。
- INPUT_LIMIT（输入受限）：下载/解码/预算不足与数据本身无证据区分；保留失败和限额记录，后续授权/资源取舍再评估，不无限重试。
- STOP（停止）：H77–H79正式L3及H78同源发行不重跑；H80拒收/H80R被替代保持，H81一次正式L2与唯一L3通过后STOP同类扩例。H84 的双角色一次现场均已完成，STOP 同一驱动扩例。B-24 若证据仅涵盖历史 observed 时点或无法确定使用时点与权威状态，保留 NOT_JUDGEABLE 并停止扩大安全效果声明。
- SWITCH（切换）：首选实际不可用且另一个候选有更明确权限及可判定证据时重新比较，不能自动注册其它平台或启用钱包；新的零容忍反例仍可触发优先级重评。
- H72旧许可不继承。H75超限/UNKNOWN、H76三轮偏差、H77正式L3=1/WSL0、H77R正式L3=1/发行尝试1/服务0保持。H77R2正式L3=1/发行尝试1/Server1+Agent1/UID与签名0、双方各1预检分列。H77R3所有WSL/服务/发行权限false，不续用父额度；历史费用UNKNOWN保持，无总体时间自设上限。

## Historical preservation / 历史保护与新基线

r152原字节归档为 `archive/PROJECT_BOTTLENECK_MAP_20261125_r152.md`。H91在原r152完成唯一L3、62接受项保持、终态validator OK，CURRENT.final.md已保全。H92锁将原current-map引用映射到r152归档，当前r153另锁；H91原合同/报告/提交/正式证据不回写，不在新产品上追改原成绩。

r151原字节归档为 `archive/PROJECT_BOTTLENECK_MAP_20261125_r151.md`；重冻前路由保存于H91/evidence/scenario/preparation/CURRENT.before-refreeze.md。Amendment02采用独立SCENARIO_INPUTS/计划/检查器/报告路径，显式保护旧H91锁、合同、检查器、两次原生L1原件与修正前脚本。正式L2/L3额度尚未用，不改H88/H90裁决。

r150原字节归档为 `archive/PROJECT_BOTTLENECK_MAP_20261125_r150.md`。原H91仍0L2/0L3/矩阵未运行；CURRENT.before-scenario-replan.md保存原派发。r151是用户纠正粒度后的显式规划变更，无新能力或历史裁决变更。原H91冻结锁指向r150时只能作历史复现，不在r151下重跑并误报漂移。

r149原字节归档为 `archive/PROJECT_BOTTLENECK_MAP_20261125_r149.md`。H90先在原r149完成独立L3、58项提交保持与终态结构校验，CURRENT.final.md保存后才切r150。H91锁将历史地图键映射到r149原件，当前r150另锁；H90合同、报告、L2/L3、提交与原失败原件不回写。

r148 原字节归档为 `archive/PROJECT_BOTTLENECK_MAP_20261125_r148.md`，与 H89 接受记录的摘要一致。H89 终验及 L2/L3 保全。H90 输入锁将 H89 已签收的 r148 显式映射到归档，与当前 r149 分开保护。历史测量结论限当时的产品和地图。

r147 原字节保存于 `archive/PROJECT_BOTTLENECK_MAP_20261124_r147.md`，其摘要已由 H88 接受快照与 POSTCHECK 交叉核对。H88 在地图变更前已终验及结构校验，最终路由存于 H88/evidence/evaluator/CURRENT.final.md。H89 的 INPUTS 将旧当前地图键显式映射到 r147 归档，当前 r148 单独保护；不得在新治理路由下重跑旧严格地图断言并误判旧产品漂移。旧报告、L2/L3、接受快照及裁决不回写。

r145原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r145.md`，SHA-256 `86b5b38785124825b59457bdb9d94e1b5a0fc63e77f4f99f070bb37741bd1a9b`。H86终态路由保存在H87/evidence/preparation/CURRENT.before.md。H87以已同步HEAD df4073d建立新锁，不机械重跑旧HEAD冻结门禁。旧证据与结论按原字节保留。

r144 原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r144.md`，SHA-256 `78a51112f79f517d5c1de05fc8bccf45c896be35078b0f412fbff42526a74fd1`。H86最终结构校验通过后保存CURRENT.final.r144.md，再更新本治理修订。

r143 原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r143.md`，SHA-256 `c01e5ddfe9c9bc42b0d01ebdca0ff919fe331b72f10ec3a6af1adcada9df019f`。H85独立终态结构校验通过后保存CURRENT.final.md，再切换本修订。历史严格回查使用原地图字节。

r142 原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r142.md`，SHA-256 `bb21522d1e1691d7662b6020ea024882bb55dbbecaed66f746dec8c06bb1ec93`。H85 原草案路由按原字节保存在本任务证据目录。

r141 原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261124_r141.md`，SHA-256 `3eb29f37886f5a2348c1738f96d9689380c95f4849fb347c47a29e8fc879067b`。H84 接受前及 L3 后按原 r141 路径核对零漂移。H84 提交、接受、终态路由保存在本任务证据目录。历史严格回查使用 r141 原字节，r142 是签收后的路由修订。

r140 原字节保存于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261123_r140.md`，SHA-256 `d1f95e959617fd5da097def4c9a67745c732687a05dea29f6d8cbb9658c640eb`。H83 终态结构校验在 r140 通过。提交与终态路由均保存于 H83 证据目录。r141 是签收后的治理修订，H83 冻结检查仍以 r140 的原路径和原字节为基线。

r139 原字节归档 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261123_r139.md`，SHA-256 `87e94d07090d1e07e75f5d917fc95638406bf69bf7c2621c8c180fcfff1659a9`。H83 冻结前草案、旧路由和预检原始三件套保存在本地 H83/evidence/preparation。

r138 的 H82 冻结原字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261119_r138.md`，SHA-256 `ea59af109f7cb533cbbeec90b06200cd5a35b6ac71ab1fedb84d0424088678e9`。H82 原接受路由与独立终态路由保存在本地 H82/evidence。终态在 r138 原位时通过结构校验，之后才切换治理路由及地图 revision。H82 冻结回查应使用归档原件。

r137原字节归档为`docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261118_r137.md`，SHA-256=`6f9d4df1f35bf8abfa9f17f728e3e4e22ce3f380a6dde6ba42e8c54eeb166de7`。它和旧CURRENT/H81 2647接受项在治理更新前独立零漂移；r138是**H81 PASS之后**的新治理决策，勿在r138当前路由下机械重跑H81严格冻结checker并将预期地图变化误报为H81产品漂移。H81/REVIEW、正式L2/L3及原证据均不回写，B-24未冻结下一包。

r136原字节归档archive/PROJECT_BOTTLENECK_MAP_20261118_r136.md及H81/references/before_h81，旧CURRENT/REMOTE和四实现文件逐字快照。H80R全部30非运行时文件含冻结/准备输出/执行前阻塞报告以SUPERSEDED_SNAPSHOT保护，0实现/0L2/0L3；其小修与启动前置并入H81，不追认技术通过/失败。H81继承2517保护项及原H80/H79/H78历史，来源前后两模块用BEFORE_LOCK精确锁定；本次仅制包。

r135原字节归档archive/PROJECT_BOTTLENECK_MAP_20261117_r135.md及H80R/references/before_h80r，旧CURRENT/REMOTE和当前四实现文件也逐字快照。H80未提交的86非运行时任务文件（含两轮失败EV、报告、冻结和本次独立审计/REVIEW）统一摘要保全；原2430保护经明确治理别名继承，新产品/原支付fixture当前摘要锁定，不追改旧拒收。H80R只是新冻结包，无实现/L2/L3成绩。

r134原字节归档archive/PROJECT_BOTTLENECK_MAP_20261117_r134.md及H80/references/before_h80。H79 2395接受项在治理变化前全量复核不变，完整L2/L3、REVIEW、接受/路由修正/独立审计封存；H80允许改的两产品文件及一个fixture保留旧字节并明确别名，当前源码按新提交接受后保护，不把父路径原地保持与合法修复混淆。r135与REMOTE进入H80保护。父严格保护checker不在新路由机械重跑，父原始证据和结论不追改。

r133原字节保存于archive/PROJECT_BOTTLENECK_MAP_20261117_r133.md及H79/references。H78最终REVIEW、2229接受输入、完整L2/L3/实际源85公开索引及Evaluator额外时间/清理/费用原文均由H79 BASELINE保护；根地图/REMOTE治理变化通过明确旧字节别名保持，不在新路由机械重跑父严格checker并误报产品回归。原H78授权/失败历史不回写。

r132原字节保存于archive/PROJECT_BOTTLENECK_MAP_20261117_r132.md及H78/references。H77R3终态路由/旧REMOTE、H78候选合同/未授权记录/原候选清单已逐字封存；H78 PREPARATION_BASELINE保护2114旧输入，正式BASELINE用明确旧治理别名保留2085父接受项。原预授权就绪审查不是实际执行，不追改为来源能力成绩。

r131原字节归档archive及H77R3/references/before_repair；H77R2拒收路由、原REMOTE、完整1939接受输入及本次L3/失败/独立回查由新BASELINE保护。1939输入在治理变更前零漂移；本次地图/REMOTE改写后的旧字节通过明确别名保持，不在新路由机械重跑父checker或改写父FAIL。

r130原字节复制archive及H77R2/references/before_repair，H77R拒收路由、原REMOTE、全部提交/接受/L2/L3/失败产物/清理与只读目录均受新BASELINE保护。H77R结束后1812接受文件零漂移；新地图/REMOTE治理变更通过旧字节别名保留，旧严格门禁不在新路由机械重跑。

r129原字节复制archive及H77R/references/before_repair；H77拒收路由、原REMOTE、全H77提交/接受/L2/L3/拒收与POSTCHECK全部由修复BASELINE保护。H77结束后1693接受文件核对零漂移；后续地图/REMOTE治理变更通过旧字节别名保留，不在新路由下重跑旧严格checker并误报产品漂移。

r128、原CURRENT和REMOTE完整原字节及SHA见H77/references/before_h77与evidence/preparation/ASSESSMENT.json；r128另复制archive。H76原103份文件封存，唯一新增旧任务文件为本轮Evaluator REVIEW，不改原合同/资产锁/计划/产物。旧H76严格checker有原路由/地图依赖，新包不在新路由下机械重跑并将治理切换误作产品回归；H77 BASELINE通过历史路径别名保护旧治理字节。

r119原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261115_r119.md`及H72 references/before_activation/governance。H72原草案合同/计划/预算/授权/BASELINE等与原CURRENT/REMOTE共15快照已保留；新授权/自主空间是Human明确指令后的本任务冻结，不改历史成败。新基线仅重封显式治理/授权控制文件，旧测试、产品初始字节、旧H71R3及失败证据继续保护。

r118原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261114_r118.md`及H72 references/governance_before_merge。原CURRENT/REMOTE与H71R3合同/计划/BASELINE/修订/依据/再评估共9快照、原H71R3全部40个非缓存文件摘要见H72 SUPERSESSION/references。旧H71R3并包是Human显式制包决定，不是产品成绩；新BASELINE保护历史和旧测试，仅把三个Stripe接缝文件列为后续授权范围内可改并保留初始字节。当前DRAFT不授予外部动作。

r117原字节保存于`archive/PROJECT_BOTTLENECK_MAP_20261113_r117.md`和H71R3的`references/before_amendment_01/PROJECT_BOTTLENECK_MAP.md`。原H71R3合同/九项计划、旧CURRENT/REMOTE也在该references目录，摘要见`evidence/reassessment_20261114/ORIGINAL_SNAPSHOT.json`。r118是Evaluator明确的治理/合同可执行性修订，不追认执行成绩；本包新BASELINE重新封存当前治理、旧任务及公共脚本，历史checker不得在新路由下机械重跑并把预期路由差异当产品回归。

r116原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261112_r116.md`及H71R2 references，原路由/REMOTE与H71R拒收路由保存。H71R报告原件、接受前格式附录、候选快照分类、自建门禁及结构拒绝均保留；其终态结构验证仍检出原无效L2，作为拒收证据，不手工修成成功。H71R2以新基线保护这些历史材料，INPUT_SEAL复用正确矩阵/纠正投影。

r115原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261112_r115.md`及H71R references；旧路由/REMOTE和H71 REJECTED终态路由、原始L2/L3/64接受文件全部保留。EVIDENCE_GOLD只提取三GET与两份已有来源摘要，不包含key/原账户ID。H71R新基线保护旧任务及忽略证据；历史严格checker在原地图/路由/范围下复现，不把本次治理切换误报为产品回归。

r114原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261112_r114.md`及H71 references。H70整个冻结包及准备证据保持，SUPERSESSION.json记录未执行替代、原路由/REMOTE/AGENTS摘要，不伪造H70失败或签收。H71新基线显式包含治理偏好变更与旧包保护；旧严格checker只在对应历史路由/地图/范围快照下复现。

r113原字节归档于`archive/PROJECT_BOTTLENECK_MAP_20261112_r113.md`及H69 `evidence/l3_review/governance/`；原路由/REMOTE、H69 PASS路由、最终工作流验证和摘要同目录保留。H69原合同/REPORT/RESULT/L2/L3不回写；H70基线保护历史材料及忽略证据。旧H69严格门禁只在原r113/原路由与范围快照复现，不把新治理差异误报为产品回归。

r112原字节及H68R PASS时CURRENT/旧REMOTE保存于 `docs/05_任务交接/H69_STRIPE_ANONYMOUS_SANDBOX_QUALIFICATION_V1/references/`，地图SHA-256=`edd2f84871efacaa383fc7adcb7c1282deb2423612241b1a087cdf9221383e0b`；原H68R完整L2/L3/REPORT/RESULT/冻结文件不回写。H69 BASELINE保护包括Git忽略证据在内的H68与H68R全部已有文件；旧严格门禁在原路由/地图快照复现，不把本次治理更替误判为产品回归。

r111原字节保存于 `docs/05_任务交接/H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/evidence/blocked_review/governance/PROJECT_BOTTLENECK_MAP_r111.md`，SHA-256=`50cfac216a960ee29608d3ffcd730d6487a26951c957bad5b07f2025784a3cb6`；旧CURRENT/REMOTE同目录保存。H68全部冻结输入和执行证据不回写。r112是新复核后的显式治理变更；H68R新基线保护旧H68与既有工作区，旧H68严格范围checker只在其原路由/范围快照下复现，不把新治理差异当业务回归。

r110原字节归档于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261111_r110.md`，SHA-256=`0a820307f92fef6c3f525ccd6acb8fedb26a4c463f41ff3c42ae316db5da95a3`；旧CURRENT/REMOTE_HANDOFF/就绪草案保存于H68 references，CURRENT原SHA-256=`c704b300cb0e64da9db9b97cd50d8072a05a9b14052491a41c6d7d09ac0ea4df`。本轮只制包，不追认现场授权或旧任务成绩。

r109原字节归档于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261110_r109.md`，SHA-256=`da842128dfa0d897891934dd736ac57382b64de194fdba36b669a1f5474ead1c`；原CURRENT保存于新草案references/PRIOR_CURRENT.md，SHA-256=`0052f76e7932d1342cd137004c985d5fd75eb2f324493909012102f48b553606`。r110是Human方向调整，不改H67原九份文件，不重跑旧基线或伪造H67验收。

r100原SHA-256=`ec6bb8f8895a6e8dfb9c284ba37c5fb5c530c6966f030378280f38bc19633328`。当前展示归档 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261106_r100.md` 在第5/6行各去除两个行尾空格，当前SHA-256=`7960dd28efa9a7ec50d98171ff33254e380fbc06151f970267d892063abd6109`；2026-11-09已从本地Git blob a32aad586492a7feaa7d4b881cee177e295115bb找回旧字节并匹配原摘要，完整原字节编码保存在H64R `evidence/governance_refreeze_20261109/DRIFT_AUDIT.json`。历史字节复现用该旧快照，不声称当前展示文件仍有原摘要。H62合同、报告、计划、判别器、INPUTS与全部证据不回写。

当前地图与CURRENT为H62签收后的显式治理变更。H63 BASELINE记录旧路径→归档路径及H62/其他工作区摘要。H62冻结checker要求原路径/工作区集合，不能在新增任务后的当前工作区直接重跑并把预期治理差异当产品回归；历史复现须在隔离原基线中进行。H63只核历史保持与新范围，不重跑H62业务。

H63R完成L3及终态结构校验后，r101逐字节归档为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261107_r101.md`，SHA-256=`24edf9d63cbbb1812816bc048893b668366faec6247bf5ef87c2e7b8c4b19935`。r102是验收后治理更新，不重写H63/H63R冻结BASELINE、合同、报告、数据或L2/L3；保护检查历史复现使用原地图与工作区快照。更新审计见H63R `evidence/GOVERNANCE_UPDATE_20261108.json`。

r102原字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r102.md`，SHA-256=`c0a1617e9b94ed1399886faa3e18344912d8be90a50ed43910d5d37f8ba4206a`；H64 BASELINE将r103作为新保护输入，并保护H63R/H63/历史工作区和原三库。旧CURRENT完整副本见H64 references/PRIOR_CURRENT.md；不在新路由下重跑历史全工作区checker。

H64完成独立L3与拒收结构检查后，r103归档为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r103.md`，SHA-256=`0fd46544e823738b164210264a21c2e220e24c4324f06b0e187c55c2a311ad9d`；r104为新修复治理基线。H64R保护完整H64提交/原证据/已获材料、原三库及既有解码器，不回写旧预算或重跑旧全工作区checker。

r104原字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r104.md`，SHA-256=`c22c10c5c6e89623d66cbfbfceef122b7aa3e1ba4c2ec3f7d0be3199420e2020`。r105仅修正执行基线和历史字节声明；B-18排序与H64R任务范围不变。旧CURRENT、合同、BASELINE及全部7冻结文件的字节另存H64R `evidence/governance_refreeze_20261109/ORIGINAL_SNAPSHOT.json`；不覆盖旧L2/L3或失败准备证据。

## Revision log / 修订记录

| 2026-11-25-r153 | H91独立PASS/NOT_APPLICABLE/CONTINUE，六VP/八AC、13行、124回归/499保护/62接受保持；停止重复测量。冻结H92一个持久控制机制共同处理准入/停用排序、不重放、恢复与原生视图，2实现/2L2/1L3；尚未实现或预报改善。 |

| 2026-11-25-r152 | Human要求制定新包；核定原生责任后H91 Amendment02冻结六族13行完整measurement包、六VP/八AC、124回归、2L2/1L3。制包观察器及O1/R1第二次原生L1通过，首脚本调用失败保留；产品0改、完整矩阵与正式Gate未运行，不计能力增益。 |

| 2026-11-25-r151 | Human要求按异常场景整体规划，撤回H91独立细节派发；显式Amendment01接管，Evaluator/DRAFT。B-27重定位为停用生命周期闭环，先核业务准入和组合证据再统一冻结；H88/H90及H91原0/0保持，不计能力增益。 |

| 2026-11-25-r150 | H90 PASS/IMPROVED/SWITCH，独立L3 6/6、七AC、124回归和384保护保持；B-26“提交先于读取”切片关闭。B-27升为只测量第一瓶颈，冻结H91八步顺序测量包，产品只读、无外部权限；未执行H91正式门禁。 |

| 2026-11-25-r149 | H89 PASS/NOT_APPLICABLE/CONTINUE，L2/L3 各6/6，独立复算12行，整份停止接收缺口成立。冻结 H90 八步骤本地能力包，FluxA 用作执行责任与证据参考，旧凭证及渠道验证维持候选。 |

| 2026-11-25-r148 | H88 PASS/IMPROVED/SWITCH，L2/L3 各4/4、124回归、268保护、25接受保持；B-25 本地代表切片关闭。归档 r147，冻结 H89 八步骤整份委托停止传播测量，B-26 第一瓶颈，无产品/外部新权限。 |

| 2026-11-24-r141 | H83 PASS / IMPROVED / STOP，L2/L3 各 3/3，五项 AC 和 86 项原回归通过。本地使用时点切片关闭，真实来源、状态和时钟仍未知。H84 进入证据资格草案。 |
| 2026-11-24-r142 | H84 PASS / NOT_APPLICABLE / CONTINUE，两角色各一次本地实际发放资格测量，独立 L3 完成。B-24 仍优先，H85 聚焦现有受治理的 WebShop 动作入口，草案等待独立现场授权。 |
| 2026-11-24-r143 | H85 冻结并交接 Executor，明确受限现场及一次性额度，机器检查器补齐。不计任何 H85 实现、正式门禁或现场结果。 |
| 2026-11-24-r144 | H85 PASS/IMPROVED/STOP，关闭本地单入口取证责任切片，H86只读测量现有实际消费者证据资格。 |
| 2026-11-24-r145 | H86 PASS/NOT_APPLICABLE/STOP。仓内113输入、12直接调用定位；实际采用链UNKNOWN。停止同源扩例，等实际消费者逐次材料再冻结核验。 |
| 2026-11-24-r146 | 纠正实际生产采用作为全局前置的过度限制。B-25保存后确认撤回传播提升为measurement-only首瓶颈，H87冻结交接。原B-24及H85/H86成绩与未知保持。 |
| 2026-11-24-r147 | H87 独立 PASS/NOT_APPLICABLE/CONTINUE，原图登记无法表示后续撤回。归档 r146，冻结 H88 单一能力包及基线，B-25 保持首位。 |
| 2026-11-23-r140 | H83 冻结一处本地 WebShop 使用时点资格。从 H78 公共材料独立复算 VALID，原入口 BOUND/ALLOW/1 模拟回调，86 旧回归通过。L2/L3 与产品结果待执行。付款策略及生产权威结论沿用此前边界。 |
| 2026-11-23-r139 | H82 独立 PASS / INCONCLUSIVE / STOP，L2/L3 各 5/5，原回归 44/44，45 项接受快照零漂移。本地接口确认，实时状态和生产上游仍未知。B-24 保持第一瓶颈，H83 草案待具体消费者与权威来源。r138 原字节归档。 |
| 2026-11-19-r138 | H81正式L2/L3各5/5，原2548保护和修正后2647提交独立零漂移，M02错误身份晋级1→0/M01保持，原33观测、10负例及全部必要回归通过；PASS/IMPROVED/STOP B-23本地代表消费切片。封存stdout先空后写SHA单项透明修正，旧清单字节保留；r137按原字节归档。下一B-24仅高优先只读测量候选，H82未冻结/未执行，真实use-time撤销轮换与强认证未知。 |
| 2026-11-18-r137 | 按Human要求将小修纳入B-23完整闭环包H81：入口/输入前置→同输入前后对照→完整原矩阵和必要回归→统一闭合证据/提交→接受后独立L3。H80R0/0/0及执行前阻塞报告原件保留并替换，不新增产品机制或外部权限，未执行/未预报改善。 |
| 2026-11-18-r136 | H80两轮L2各3/4、预算耗尽/无提交/无L3，独立核2430保护/8组EV及错误测试基础前提；拒收/整体改善未定，B-23未闭合。冻结H80R唯一测试输入/原生Windows完整门禁修复，产品当前摘要锁定、完整原回归/独立验收不减，历史WSL式启动未知不追认。 |
| 2026-11-17-r135 | H79测量独立签收PASS/NOT_APPLICABLE/CONTINUE，L2/L3各4/4、2395接受保持；跨Agent错误VERIFIED归因确认，M03–M06未执行。B-23转为明确修复，冻结H80三元上下文传递/精确核对的一个最小接缝修复，保留BOUND同策略、原密码学/授权守护及完整回归；无新物理权限。 |
| 2026-11-17-r134 | H78新鲜实际来源完整独立签收：L2/L3各6/6、2229接受保持、管理/UID/SVID/持有/十负例/原130/清理成立，PASS/IMPROVED，关闭B-15窄来源切片并停止同源发行。下一B-23为已验证事实消费上下文UNKNOWN，冻结H79六槽只读测量/首反例停止，未执行、不预报漏洞、不继承物理运行授权。 |

| 2026-11-17-r133 | H77R3解析修复独立签收、停止同类扩例；H78候选63文件/2114保护及独立门禁核查通过。Human明确批准新H78固定WSL/双方各1资产预检/Evaluator1发行与Server1+Agent1；冻结完整有界来源测量，原十负例/16/130/独立清理不减，尚无新发行成绩。r132/旧路由/旧候选与未授权记录保全。 |

| 2026-11-17-r132 | H77R2独立真实资产预检通过，Server/Agent实际启动、管理根/列表及创建成功，但results[0].entry封装解析失败，UID/持有0；L3三过三失败，原130/1939接受保持/独立清理通过，REJECTED/NOT_APPLICABLE/CONTINUE。冻结H77R3单纯函数实际响应离线修复，发行/服务/WSL0；不自动续给来源重演权限。 |

| 2026-11-17-r131 | H77R独立L3三过三失败，路径已恢复但官方Server179,378,008字节被150MiB阈值误拒；服务启动0，原130/1812接受保持及独立清理通过，REJECTED/NOT_APPLICABLE/CONTINUE。只读完整真实archive固定两成员大小/SHA后，冻结H77R2精确profile及同生产提取器真实资产预检；新包未执行，不升级B-15/E。 |

| 2026-11-16-r130 | H77提交L2 6/6，1693输入接受后独立L3三过三失败；Windows调用方反斜杠违反POSIX入口，WSL/SPIRE实际0，原130回归/接受保持通过。REJECTED/INCONCLUSIVE/CONTINUE，原失败不重跑。H77R冻结单处.as_posix()调用方修复与实际argv离线联调，原源脚本不变；新包尚未执行，B-15不减记。 |

| 2026-11-16-r129 | 本轮Evaluator发现r128落后于WSL授权/三轮执行；独立20文件、1502保护项、密码学/十负例及130回归通过，原正式L2/L3=0、结构门禁失败。H76原合同REJECTED/INCONCLUSIVE，保留实际样本与次数偏差。冻结H77离线L2→接受→唯一Evaluator新根/nonce重演；未执行新包，不宣称E整体或来源独立证据已闭合。 |

| 2026-11-16-r128 | 负责人取消自设制包时间上限后H75设计完成，旧超限/UNKNOWN保留。H76实际SPIRE来源测量包技术内容齐备：固定4文件及Python镜像摘要、八AC/六VP/十负例/原回归/清理/独立L3，唯一待补运行授权。仅离线就绪/元数据核验，无实际发行或新产品能力成绩；r127原字节归档。 |

| 2026-11-16-r127 | H74R独立L3 6/6、10组/16测试/19/9/74及补充重试/类型对照通过，PASS/NOT_APPLICABLE/STOP，接受原件保持。主线保守累计71.862797/150分钟，原实际UNKNOWN与H74拒收保留；B-22仅本地stored代表切片关闭。Human继续后转H75 Evaluator来源资格设计，既有SVID消费者/SPIRE优先候选，25分钟/6次公开网页工具上限，无实际运行权限或能力成绩。r126/完成路由/REMOTE归档。 |

| 2026-11-16-r126 | H74独立L3 8/8但原事实幂等/同名枚举保真反例导致AC-02失败，收尾未入账导致AC-08失败，最终REJECTED/INCONCLUSIVE。原147/4/20及2687保护保持，独立9组7过2失败、原19/9/74过；Evaluator19.284441分钟。保留原20.825250账本，追加保守25.019200需另包记录。冻结H74R两功能问题及成本修复45+15分钟，累计105/45/150不变，外部0。r125/拒收路由/源码原字节保存。 |

| 2026-11-16-r125 | H73独立L3六项、521引用、12边界96字段及三共同审计断点通过；48提交/50冻结/100接受/2549保护保持，PASS/NOT_APPLICABLE。整窗Executor21.395618+Evaluator19.325080=40.720698分钟，旧制包另列。停止静态视图，冻结H74原上下文持久化/消费单一离线能力；三新合成单元、105+45分钟/2实现/2L2/1L3，原9/74及Stripe模块回归，外部0。r124/完成路由/原源码逐字节保存。 |

| 2026-11-15-r124 | Human要求Evaluator基于项目瓶颈制订下一包。B-21保持关闭，新增B-22未知授权事实连续性，冻结H73 measurement-only：四原旅程/三边界/两白名单私有源，150分钟独立新角色窗、2L2/1L3；先测共同断点再决定能力，不预判越权。原r123/路由/REMOTE逐字节保存，外部全false，无执行或产品增量。 |

r105原字节归档于 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261109_r105.md`，SHA-256=`48fd5abb2c59eb1f7e8c06dff166cdf993345376a8715adc44b51d948fd89c4a`。H64R原REPORT/测量/账本/接受快照及L2/L3不回写；公开展示副本与原件分别标记，发布不追认原始证据被修改。

| Revision | 证据与决策 |
| --- | --- |
| 2026-11-15-r123 | Human明确选择预算例外，首窗按36.133333分钟上界入账、实际UNKNOWN/原记录保留并补列评估成本。原109接受文件一致；不重跑L2/L3或支付，新增REVIEW_OWNER_DECISION最终PASS/NOT_APPLICABLE/STOP，原HUMAN_REQUIRED及H72/H72R拒收保持。B-21受控代表切片阶段关闭，无下一执行包，所有未来权限不延长。 |
| 2026-11-15-r122 | 补录H72R门禁11/11但独立反例拒收；负责人直接授权H72R2后两次L2及本次独立L3均12/12，原两项反例真实拒绝、技术修复闭合。首窗主动时间UNKNOWN、墙钟36.133333而称30保守上界，完整主线成本口径未证；H72R2 HUMAN_REQUIRED/NOT_APPLICABLE，AC-01～06通过、AC-07待补证或明确例外。停止同类工程，不认定实际超预算，不再派实现包；预算资料及原r121归档完备。 |
| 2026-11-15-r121 | H72 L2 15/15，独立L3 14/15，原9/74/11/9及URL6实际通过；13GET确认4/3/3测试对象及四功能事实，三通知独立HMAC/九反例通过。原生节点数据不变但文字本地化误报，额外拒绝自测14/16，读取摘要0与实际13错位；REJECTED/INCONCLUSIVE/CONTINUE。归档r120与旧路由，冻结H72R单个零外部动作的离线复核门禁修复，不重付、不覆盖原FAIL，D01明确为交付记账恢复。 |
| 2026-11-15-r120 | Human明确授权H72，要求不重复确认，并允许主线内步骤/线路调整和网络多次尝试。登记新原话/24小时许可，冻结CONTRACT/SPEC/AUTHORIZATION/AUTONOMY，切Executor；只读/下载最多4次，固定下载12HTTP/4传输/64MiB，2主要方案内普通修补不按每次编辑另扣。15项计划及资金/环境/安全标准不变，15份草案/治理快照保留；未运行正式Gate/外部交易，四旅程仍0/4。 |
| 2026-11-15-r119 | Human要求把本地收尾与外部长包写在一起。H71R3仍无REPORT/L2/L3，40文件保持，旧1804保护核对通过，9快照封存；H72准备合同/15项计划/范围/预算/原件基线，P0吸收原9/74/11/9，随后资格及四旅程，最终统一复核。待一次新外部授权，DRAFT/Evaluator；四旅程仍0/4，零新外部动作/正式Gate。 |
| 2026-11-14-r118 | H71R2原生Windows L3 5/7、两项缺依赖，继续REJECTED；后续agent具备两依赖但tests遮蔽。H71R3尚无REPORT/L2；独立1701保护输入仅REMOTE治理差异、13冻结输入全保持，原完整性命令退出1。定位旧路由/新增范围及旧预算核验不适配、PYTHONPATH被嵌套回归重设；DA-02任务局部用户包导入探针通过，0断言/0正式Gate。封存原合同/九项计划，显式修订01重冻十项；CONTINUE有界修复，不增加产品或外部成绩。 |
| 2026-11-13-r117 | H71R正确矩阵/历史纠正保留，独立Windows六项/11探针/9安全/74回归通过；但收尾摘要失败丢元数据、自建L2不合格，原第4/5项不通过，REJECTED/NOT_APPLICABLE/CONTINUE。候选67文件与分类澄清保留，冻结H71R2六步归档/公共门禁离线长包，0新外部动作；原运行授权已过期。 |
| 2026-11-12-r116 | H71 L3八项/9安全/Windows74通过，但AC-02最终矩阵/引用、AC-07失败字节与HTTP阶段不通过，REJECTED/NOT_APPLICABLE/CONTINUE。保留三GET200事实和64接受文件；冻结H71R较长离线取证修复，120主动分钟/3小时，零新网络/API/下载/付款；历史下载接收量未知，不保证剩余字节额度。 |
| 2026-11-12-r115 | Human要求较长多步骤执行包与统一复核；确认H70未执行并原样保留，冻结H71七步入口资格长包，120主动分钟/4小时且原截止不变，显式分配原H68最小余量，0创建/会话/付款/产品改动。保留9安全/74回归/独立回查与完整L2/L3；本轮只制包，无新运行成绩。 |
| 2026-11-12-r114 | H69独立L3 3/3、1395保护输入/50接受文件保持；创建一次成功，三次Account读取403，PASS/NOT_APPLICABLE/STOP。冻结H70只读权限/资格门槛适用性核验，0运行API/会话/付款；B-21未关闭，不将接口403外推整个沙箱不可用。r113原字节与旧路由保留。 |
| 2026-11-12-r113 | H68R独立L3 3/3、安全9/9、Windows74/74及四边界检查通过，PASS/NOT_APPLICABLE；停止同类本地扩例，冻结H69匿名账户/监听资格测量，仅分配原H68未使用授权余量和原截止，0会话/付款。本轮只制包，B-21仍待外部入口实证。 |
| 2026-11-12-r112 | H68受阻交付不具备L3资格，外部四旅程未测；独立复现四类本地缺陷及Windows六项错误，现成浏览器本地交互成功。保存r111/原路由、57文件快照及L2摘要审计，冻结H68R离线最小修复；B-21不减记、外部权限不继承。 |
| 2026-11-11-r111 | Human选Stripe并要求低手工的长执行包；形成H68四功能旅程、明确权限/预算及独立只读验证设计。当前DRAFT/待精确运行许可，无安装/创建/付款；61项历史基线及checker合成自测不计产品成绩。归档r110及原路由，H67保持延期。 |
| 2026-11-11-r110 | Human明确H67先不执行、优先外部沙箱/测试网络，六类攻击扩展不派发；一轮官方研究支持Stripe匿名隔离沙箱首选，B-21仅就绪设计，CURRENT为Evaluator草案，实际创建/安装/API/付款未授权。r109与原CURRENT原字节归档；无新增产品成绩。 |
| 2026-11-10-r109 | H66独立4VP/9官方blob/11引用/15请求预算通过，PASS但停止IronClaw接入视图；切换B-20/H67固定ACP幂等键绑定契约测量。r108原字节归档SHA-256=31fe04cc5a9f0905f71206415717673abbab46b958368882870441448e601686；无新产品成绩或实际重扣证明。 |
| 2026-11-10-r108 | H65R四VP/57源引用通过，四确认及一额度令牌链已核，但AC-04真实读取预算无法复核而拒收；停止同六例重跑，切换B-19/H66固定IronClaw消费者资格研究。r107原字节归档SHA-256=c99c442c39cd638e854f3dd34ff15953790b3ee70e4bbfcedfe4038dad942762；无新产品成绩。 |
| 2026-11-10-r107 | H65结构4/4但独立源审阅复现4条确认/1项单位漏读，AC-02/03/04不通过；拒收并冻结45分钟H65R最小修复。r106原字节归档SHA-256=4021661f48364b8c13127863872735a1285d9c56c5d5c2c1ba3adea671a6cb73；IronClaw保留参考，不以错误停止结论转向。 |
| 2026-11-09-r106 | H64R独立L3/六源审阅PASS，修复完成但六例仍不可判定；冻结H65单位/确认桥最后有界静态测量，缺环即停止此视图。r105归档；公开入口与安全控制文件统一推送，原始输入不公开。 |
| 2026-11-09-r105 | 评估者核清HEAD漂移和四文档10行尾空格差异，找回全部旧字节并保存审计；同一H64R显式迁移执行基线，CHECK/计划/预算/授权不变。r104逐字节归档；仅恢复可开工条件，无新测量或产品通过结论。 |
| 2026-11-08-r104 | H64独立L3结构4/4、语义AC-02/03不通过；原调用id混拼/已报告金额被丢弃，REJECTED/INCONCLUSIVE。冻结H64R离线最小修复，0网络/安装；下载限制保留，不能据此否定源或声称产品漏洞。归档r103。 |
| 2026-11-08-r103 | Human要求制定新包；固定完整表/world与代码来源、规则/选择/预算/依赖，H64 CONTRACT_FROZEN，尚未执行。B-18测量主线，不恢复真实支付权限；归档r102，原H63/H63R不改。 |
| 2026-11-08-r102 | H63R PASS，独立L3 3/3及30映射语义复核；原H63拒收保留；停止六预览资格研究。B-18独立控制效果证据仍缺，新来源未就绪，无下一执行包；E/F和支付权限不升级。归档r101。 |
| 2026-11-07-r101 | H62既有PASS/IMPROVED/STOP；归档r100，B-17本地切片关闭，B-18有界外部资料资格测量。非新产品成绩。 |
| 2026-11-06-r100及更早 | 完整原文见归档，不改历史合同/结论。 |
