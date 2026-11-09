# H57R 修好商城验证记录，并真正退出首进程再恢复

Task ID: H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H57R_EVIDENCE_AND_PROCESS_EXIT_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 为什么现在做

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-01-r94
Active bottleneck: B-17
Hypothesis: H-57（继承，非新能力假设）
Measurement status: measured（历史材料/代码断点）；unknown（完整独立交易验收）

A–D本地代表成果保持，E仅本地，F当前。H57正常工厂接线及六例18请求材料已有进展，但AC-04/05不通过：25条旧预留被字面量换行拼成一行且ID重复，另32条规范新日志不在冻结Checker指定路径；恢复脚本只关首应用、不退出首OS进程。H57拒收/INCONCLUSIVE，无L2/L3。比回H56细节支线或延期真实Provider，这个小修复更直接闭合已接通商城的可复算验收。

## Single objective / 唯一目标

在完全不改商城业务候选的前提下，修复本地验证证据的忠实性：保留历史失败和成本，重新得到完整六旅程、合格请求预留及首OS进程已退出后才恢复的证明，完整L2后一次交独立L3。不是新商城功能、自动补单、生产支付或协议升级。

## Allowed scope / 只允许改什么

商家38文件（H57原37+guarded_app）全部冻结，只读；复制的是未验收H57候选，不预先接受其业务结果。原生默认工厂、路由、签名、确认/授权/占用/支付/恢复均不得改。RUNTIME、references、CASE_SPEC、CHECK、合同/计划/来源/BASELINE冻结。

仅可改本新包 `HTTP_RUNTIME.py` 与 `RUN_JOURNEY.py`：前者只修规范请求账本/预先预算检查，后者只修证据落盘与M06进程安排。不得重写M01–M05业务、改单/确认/授权语义、签发对象或原生验签；M06的相同交易/故障hook/原恢复方法保持。可以写REPORT、RESULT、ATTEMPT_LEDGER和evidence。旧H57全部只读，不改损坏日志/旧合同/旧Checker/旧报告，不从旧材料生成伪造的新请求预留。

运行边界继承H57：H47固定Python3.12/30包、H37两个固定库及固定AP2源；ASGITransport进程内HTTP，无端口/真实DNS/外网/Provider/安装；真实原生RFC9421签名及合成离线公开profile。私钥仅内存。临时DB仅.task_envs/H57/runs；默认工厂无dependency_overrides，控制来自可信进程配置。授权来自实际创建HTTP响应，不DB补字段。原生2026-04-08/H53R研究信封不冒充标准CheckoutMandate。四授权false。

## 历史证据与预算不可洗白

references/LEGACY_HTTP_ATTEMPTS.raw是旧原始文件逐字节复制：SHA-256 e0950438ff219c16ee539de623405951b6efb21c837bf2e244b679f2a8f9208f；只读解释25个对象，不改其wire ID，明确不合格。H57_LATER_HTTP_ATTEMPTS.jsonl复制32条（14失败+18完整），SHA-256 1a9d75bfa983daeacd34587728ec6050b83add1a7a0755021d5a53f231fb2984。旧57全部计入成本，不作为本包合格交易成绩。

原Executor160上限不重置：继承57，本包所有新预留合计最多103；每完整波次仍<=28。正式L2继承已用0，本包及父合计最多2，不覆盖失败门禁目录。Evaluator父已用HTTP0，本包另最多80。任何失败/进程退出、L1、独立诊断都计新预留；停止足够后重复测试。

旧主动分钟精确值unknown，不编精确值。已观察任务执行会话从2026-11-01T01:48:17.019Z到最后执行者响应02:48:30.990224Z，整个窗口向上收61分钟；历史仍保守收取120分钟，不宣称精确主动用时，见EXECUTION_WINDOW.json。后续等待/评估者准备不算执行者主动工时。新主动工作最多90分钟，累计收费120+新用时<=240；新用时由开始/结束工作区间记录。若另有更早/未计执行活动或无法守住上界，立即停回Evaluator。新包不增加权限。

## 进程和日志合同

全部六例仍按CASE_SPEC顺序：M01正常完成/同键重放/查结账及订单（1付款1单库存4）；M02批准后改单409；M03缺确认403；M04传输签名有效但授权篡改403；M05无配置409；后四者全0副作用/库存5。M06同样付款后before_order_commit故障500、订单0库存5；第二进程GET200、新键完成409、总付款1，原recover方法QUERY/SUCCEEDED、query1。除原合同明确允许的故障hook/profile/DNS/假PSP，不patch类/方法/路由/服务工厂。

M06必须有三个不同PID：不承载M06商城应用的监督进程、首商城worker、恢复worker。监督进程等待首worker实际退出（wait/同步subprocess返回并收集退出码）之后，才启动恢复worker。首进程可正常结束，无需模拟kill断电；不是崩溃原子性保证。仅关闭lifespan或新建对象、父进程活着承载首次商城都不合格。交接仅合成token/公开信任上下文/稳定DB路径，无私钥；两个worker使用同transactions/PSP数据库，第二可生成新内存HTTP签名key。

每次运行新建evidence/<role>/run_NNNN；失败原始输入/输出/退出码不覆盖。沿用h57-journey-observations/v1及逐case原始HTTP/正文/签名/DB/假PSP格式，LATEST只指向成功完整六例。M06另存：M06_first.stdout.log、stderr.log；M06_second.stdout.log、stderr.log；M06_processes.json。

processes格式：supervisor_pid、transactions_db、psp_db、events按[first started, first exited, second started, second exited]，每项phase/event/pid/monotonic_ns；exited另exit_code=0。四时间为同一监督进程实际事件的严格递增monotonic_ns，不能用worker时间或事后推算。artifacts.first/second含对应stdout_sha256/stderr_sha256/exit_code。case.worker_pids=[first,second]；4请求PID依次[first,first,second,second]，状态[201,500,200,409]。监督进程在首worker退出后记录exited再生成second started，源码复核加独立执行验证此事实，不能只手填布尔字段。

新预留使用本包evidence/<role>/HTTP_ATTEMPTS.jsonl这个唯一规范路径，每请求之前append一条合法JSON加真实换行，唯一request_id/case/run/phase/worker_pid，flush+fsync后才调用HTTP。新ID不得碰撞历史任何ID；失败仍保留计费，绝不事后重编号。预留前校验总57+新Executor<160或Evaluator<80，超限不发请求。监督/worker顺序执行，不能并发写或覆盖日志。phase严格为method+空格+path，和真实记录一一对应；本包不重用旧AFTER_L1路径。

## Acceptance criteria

### AC-01 — 商城候选及历史证据完整保留
Given冻结38商家及父包；When VP-01/02/07；Must observe所有hash保持、只两验证脚本被改、57历史预留全计费、原始损坏与失败保留；Must not observe改业务/旧日志/SDK或通过测试替换工厂；Evidence=BASELINE/SOURCE_COPY/历史副本/代码审查。Mandatory: yes。

### AC-02 — 六条原生业务结果保持
Given继承CASE_SPEC和实际HTTP；When VP-03/04；Must observe旧CHECK.validate所有原断言和完整六例成立、签发内容等于实际HTTP创建响应、订单/库存/付款/授权绑定一致；Must not observe伪造观察/放宽验签或DB补客户缺字段；Evidence=新原始请求、签名、数据库、假PSP及独立L3。Mandatory: yes。

### AC-03 — 首进程真正退出后恢复
Given M06首worker付款后订单故障；When VP-03/04及源码审查；Must observe三不同PID、监督者wait首worker退出后才启动恢复者、完整原始进程流及时间顺序、相同持久状态不多付；Must not observe父进程保活当首商城、只关应用、用方法QUERY冒充HTTP恢复或自动补单；Evidence=上述processes/原始流/源码/独立重跑。Mandatory: yes。

### AC-04 — 新规范账本及成本真实可复核
Given历史57/新预算103/原总160/原2L2；When VP-04/07；Must observe请求前耐久预留、全部新ID唯一和元数据匹配、失败计费、RESULT/ATTEMPT_LEDGER/REPORT齐全、主动分钟诚实；Must not observe清零旧成本、洗白历史wire ID、替换旧raw或省略失败。Mandatory: yes。

### AC-05 — 回归和诚实完整提交
Given完整7VP；When正式L2/L3；Must observe25AP2回归和原6计数+新6进程/账本负向自测、全部完整L2后一次提交，保留全部raw；Must not observe把旧L1/新准备当最终PASS、真实身份/PSP/生产/客户/标准互通虚报。Mandatory: yes。

## Validation plan

VP-01保护/环境；VP-02只读38商家/两验证脚本范围；VP-03原生六旅程；VP-04业务、日志、进程和交付；VP-05原25AP2；VP-06原6计数+新6负向判别器；VP-07保护复查。精确argv及role差异见冻结VALIDATION_PLAN.yaml，禁止执行者改Checker/计划。

ATTEMPT_LEDGER含inherited_asgi_reservations=57、new_asgi_requests_reserved=本包executor规范账本行数、asgi_requests_reserved=两者之和<=160；inherited_time_charge_minutes=120、active_work_minutes<=90、charged_minutes_total为两者之和<=240；inherited_formal_l2_attempts=0、formal_l2_attempts=本包l2_executor_*目录数<=2。network_calls/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations全0。REPORT另如实记每完整运行HTTP/模拟charge/query、所有失败/区间工时、来源/范围/每AC/所有EV、历史请求不合格及原进程缺口；不能声称历史主动分钟精确。

RESULT schema=h57r-result/v1、task_id本包、classification=NATIVE_FACTORY_EVIDENCE_REPAIRED（只完整成功后）、customer_demand=UNKNOWN、remaining_gaps非空；production_ready/real_identity_verified/provider_verified/standard_checkout_mandate_integrated/h56_profile_integrated/automatic_order_recovery/customer_value_proven均false。

执行先将CURRENT状态EXECUTING/Executor并准确phase，不能改其Global position内容。完整L2提交仍EXECUTING/Executor；Evaluator确认未变快照后READY_FOR_REVIEW再独立L3。通过后STOP本接线切片，再按商城实际下一缺口选任务；失败仅合同内预算修复，耗尽或需改商家/AC/权限即STOP回Evaluator。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY。已检查开发指标映射；PCAC-12/20 CORE证据由不合格L1变目标可复算L2/L3；PCAC-18 CORE/ADAPTER补“首进程退出后查询不多付”，仍非完整事故恢复；PCAC-07/09保持既有业务候选、不新增授权规则；08只合成根/独立确认，真实身份/同意不升级；10撤销不变。Test=六旅程/七VP/12负向判别器；Evidence=新HTTP/数据库/PSP/退出流/L2/L3；剩余真实商户/PSP/标准互通/客户未知，无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## Exclusions and forbidden side effects

不改38商家候选、旧H57、SDK、核心或现有验签/支付/确认/授权。禁止外部网络/真实DNS/监听、真实或沙箱支付、真实凭据/PII、模型、下载/安装、对外联系、Git提交/推送/改历史、钱包/测试网/区块链；H56不执行。

## Stop conditions

原始材料或保护hash漂移；新增请求/工作分钟/L2预算不足或耗尽；需要改商城业务、信任边界、Checker、合同、AC、计划或权限；无法实现真实首进程退出证据；出现误放行/多付/秘密落盘；发现未计执行成本，均停止并保留原始失败交回Evaluator，不继续扩张或清零重跑。
