# H53R 完整两跳与终结支付链形状修复

Task ID: H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r87
Active bottleneck: B-17
Hypothesis: H-53R
Parent task: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
Failed criterion: AC-02

项目目标是高风险支付授权、绑定、执行、恢复与审计可独立复核。A–D阶段关闭，E仅本地受控代表性验证，F当前。B-17仍第一瓶颈，H53固定L2/L3虽各9/9、原28观察一致，但独立S04–S06违反完整两跳与受众/nonce（一次性标识）合同，故最终REJECTED/NOT_APPLICABLE。

零容忍边界不是锁本身，而是消费者把尚可继续委托的链当最终付款授权。修复一个新模块优于重测HTTP/迁移协议/接新Provider（支付服务方）；既有金额/投影/完整快照及一次执行收益保留，但父样机未接受。H51/H52 STOP与支付宝/比赛延期不变，原H53 L2=1/2、56/280case和拒收事实不重置。

## Measured failure / 已测失败

父任务evidence/review_20261031/INDEPENDENT_OBSERVATIONS.json和RV-INDEPENDENT-01原始三件套固定三条负向材料：

- S04：用户签PaymentMandate并授代理，代理签无cnf的OpenPaymentMandate，类型顺序反转；SDK可返回两个有效载荷，当前消费者按vct重组后付款1/订单1。
- S05：合法OpenPaymentMandate根+PaymentMandate末载荷，但末载荷含下一受托者cnf，typ=kb+sd-jwt+kb（中间型）；aud错误仍付款1/订单1。
- S06：同一中间型末跳，nonce错误仍付款1/订单1。

SDK支持验证可继续委托链本身，不意味着该链已获准作为H53最终支付输入；只有终结型分支执行预期aud/nonce检查。当前新模块只看SDK list长度和递归收集vct，漏掉根/末顺序及终结状态。不是SDK漏洞或真实资金事故。

S01合法对照、S02无可信配置拒绝、S03claim提交前故障回滚均已测正确。继承的原28固定场景通过。新修复模块尚未改变，SOURCE_COPY中37份商家代码仍为父任务提交快照，不把复制完成或旧L3通过算修复成绩。

## Single objective / 唯一目标

仅在任务副本ap2_authorization.py收窄最终支付消费者接受的完整两跳形状：**第一跳为受信OpenPaymentMandate，第二跳为已终结PaymentMandate；中间型末跳、反向/缺失/重复或额外不支持形状必须在claim写入前拒绝。** 保留官方SDK签名/披露/委托绑定和严格时钟/受众/nonce检查，不自行替代密码学验证。

校验要证明是完整两跳及按顺序的有效载荷，不能仅按类型在任意嵌套字典中凑出两份事实。终结型支付末跳不得携带继续委托的cnf，不能把kb+sd-jwt+kb当完成的kb+sd-jwt。可使用固定SDK解析元数据和验证后的有序载荷，原始解析值只作形状拒绝条件，不可代替官方验签结果。

不允许只匹配攻击case名、拒绝特定错误字符串/fixture key或关闭所有合法付款；S01和原28正常/生命周期场景必须保持。所有H53原金额/币种/收款方/原文投影/完整当前快照/确认/持久占用/同键响应/恢复语义继承。只支持明确本地2026-04-08普通compact JWS和AP2 v0.2.0支付两跳切片，不升级为完整UCP/AP2、JCS、真实身份或部署结论。

## Allowed scope and frozen sources

只允许修改merchant/services/ap2_authorization.py，填写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json与evidence/。其余36份商家文件，包括checkout_service和execution_control，一律只读；付款端口、数据库schema、确认/占用/恢复、SDK、src/tests及H37/H47–H53原任务只读。不能回写父H53以消除拒收。

SOURCE_COPY记录37份继承商家文件和夹具/检查器来源。FIXTURES及完整样本原样继承；原28测试只变更修复临时目录及更低预算值，案例/预期/调用语义不变。sources/evaluator/INDEPENDENT_CASES.py逐字复制原独立生成器，TAIL_CASES仅调其run_case、记新任务账本并要求所有六例满足原合同。冻结脚本/计划/合同/BASELINE只读，不得修改断言或SDK让负例变绿。

运行环境仍H47 Windows Python3.12及已有H37纯Python模块，AP2固定b4587ac1d055888a73b4b21750973cffba961793，cryptography46.0.7/pydantic2.13.4/jwcrypto1.5.6/sd-jwt0.10.4/ucp-sdk0.4.6/PyYAML6.0.3。临时目录只.task_envs/H53R/runs。四角色私钥仅内存，公开合成材料可留证；真实密钥与个人信息不读取。

## Acceptance criteria

### AC-01 — 单文件修复与来源保护

Given父任务提交快照、环境和当前工作区；When VP-01/02；Must observe HEAD/保护/冻结摘要及其余36商家实现原样、零安装、唯一本地模块变化；Must not observe旧任务或公共验证机制变化、权限/范围扩张；Evidence=SOURCE_COPY/BASELINE/原始EV。Mandatory: yes。

### AC-02 — 完整链与最终支付上下文

Given原S04–S06真实签名材料家族；When VP-04/05；Must observe三个负例均类型化拒绝，attempt/authorization/payment/order全0，库存不变；SDK仍能验证其可继续委托链/反向载荷，但消费者明确拒绝其作为最终支付授权；Must not observe只检查返回长度/递归vct、自带root、忽略终结型、放宽aud/nonce或关闭官方校验；Evidence=重新签发的六例原始token/公钥/SDK结果/方法/DB/假PSP及独立源码复核。Mandatory: yes。

### AC-03 — 原28与合法对照/回滚保持

Given继承控制与固定研究信任模型；When VP-03/04/05；Must observe原T01–T28全部保持，S01一次付款一单、S02缺可信配置拒绝、S03提交前故障两表回滚且零付款订单；原并发两连接、同键响应和订单失败恢复仍正确；Must not observe付款端口隐藏重复、共享连接假并发、扩大恢复范围或把对象重构当真实新进程覆盖；Evidence=28+6方法材料/DB/假PSP与现有断言。Mandatory: yes。

### AC-04 — 回归、预算与真实交付

Given2主动小时/2次正式L2/272case；When完整VP-01..09；Must observe76相关回归/H37八例保持，所有原始EV与失败/重试留存，父反例保持可判别、九项能力声明false、完整L2后整包提交；Must not observe覆盖父证据、伪造修复前后收益或任务PASS/产品升级；Evidence=REPORT/RESULT/账本/L2及独立L3。Mandatory: yes。

## Validation plan and budgets

VP-01保护/环境；VP-02单文件范围；VP-03原28方法；VP-04独立六例；VP-05两类观察及SDK独立复算；VP-06原76相关回归；VP-07旧H37八例；VP-08完整材料；VP-09检查器自测。修复前判别器已确认父六例中恰S04/S05/S06不满足合同，旧缺陷未被准备工作修好。

Executor最多120主动分钟、2次正式L2、272保留case（8个完整34例波次），Evaluator另最多102case。原28与独立6分别先预留本批case、失败也计数，同一账本求和；新正式L2目录不能复用，旧观察覆盖前按hash归档。串行max_parallelism=1/代理0，无自动H53R2。

REPORT执行后真实生成，逐AC、前后比较、所有EV原始三件套、失败/成本/局限；只有完整L2通过后SUBMITTED_FOR_REVIEW。RESULT schema=h53r-result/v1、classification=LOCAL_TERMINAL_CHAIN_REPAIR_OBSERVED、customer_demand=UNKNOWN、remaining_gaps非空，九项原过度声明标记全false。Executor账本formal_l2_attempts<=2、active_work_minutes<=120、artifact_cases_run<=272且等于各批cases_reserved之和；network_calls/asgi_requests/model_calls/provider_calls/real_payment_calls/packages_installed全0。Evaluator另账本，不改父/Executor账本。

CURRENT仅CONTRACT_FROZEN→EXECUTING/Executor及execution_phase更新，任务/地图/权限/next_artifact=REPORT不变。不得自行PASS或给其他聊天发消息。整包后一次集中L3，非逐case等待签字。

## Stop conditions and exclusions

零外网/监听/DNS/HTTP/ASGI/模型/Provider/真实或沙箱付款/安装/对外联系/Git写操作。若需要改第二个实现文件、SDK/核心/锁/数据库/冻结断言或授权预算，立即停止报精确原因；不能以修复为由扩大协议义务。保护漂移、秘密落盘、预算耗尽、同一失败无新机制也停止回Evaluator。通过后STOP这个本地切片，再按真实输入和授权比较协议/HTTP/身份/Provider方向。

## External requirement impact

已核对PCAC开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=H53原28通过但终结链反例失败，未被接受；after_target=单文件修复后本地合同可接受，产品/生产身份成熟度不升级；Test=VP-01..09；Evidence=原始签名/SDK/DB/假PSP/L2/L3；残余=真实主体/确认来源、完整JCS/协议、跨系统撤销、Provider/部署/客户未知。无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
