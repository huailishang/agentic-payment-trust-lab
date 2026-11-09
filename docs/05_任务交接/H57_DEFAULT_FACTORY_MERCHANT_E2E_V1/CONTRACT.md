# H57 把现有控制接回商城正常入口，检验完整交易流程

Task ID: H57_DEFAULT_FACTORY_MERCHANT_E2E_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H57_DEFAULT_FACTORY_MERCHANT_E2E_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r93
Active bottleneck: B-17
Hypothesis: H-57
Metric baseline: H51独立C07原生默认服务工厂为创建201/完成409、0付款0订单；H53R的dependencies.py与该基线逐字节一致，仍未传execution_control。H51成功路径靠测试dependency_overrides替换工厂；H53R授权消费仅方法级已接受。默认入口不替换工厂的完整受控交易尚未验证。
Estimated affected scope: 一个固定官方商城样例的本地已接受分支，6个业务旅程、每完整波次<=28进程内HTTP请求；实际商户/用户/交易量/收益unknown。
Expected project impact: 原生默认工厂从无法完成受控交易到可由明确应用配置完成一次交易/重放/查询，越权和不确定状态不多付；证明接线增量，不声称真实部署、标准CheckoutMandate或生产付款。
Rollback condition: 必须绕过原生工厂/签名/业务，需改其他商家实现，出现误放行/重复付款/数据无法从HTTP取得、恢复靠盲重试或超权限预算则不接受并停止，保留旧成果及精确接缝。

最终目标是外部交易链中的授权、执行、恢复、审计确实连起来。A–D已有本地代表能力、E仅本地验证，F当前。Human质疑主线后，Evaluator复查实际接入证据：H54–H56已收窄为独立授权验证器，H56自定义可选区尚无目标商家需求证据，不能继续当商城必经前置。H56未执行，保留为安全支线，不裁决PASS/REJECTED、不改其冻结合同；以后如要启用需据真实消费者重新评估并正式重冻结。

本轮回到B-17实际商家接缝：H51已证明测试替换工厂可以接入旧控制，H53R已证明新的授权消费方法；现在建设**正常应用配置→原生服务工厂→已接受控制→原生结账业务**，比重复授权字段实验更直接推进商城接入。支付宝/比赛延期保持，不增加真实网络或资金授权。

## Single objective / 唯一目标

让固定商家通过自己的正常HTTP入口和服务工厂使用已有控制，串行跑完创建、确认/授权、完成、重放、查询及失败后的状态查询，不使用FastAPI dependency_overrides替换工厂。唯一主要变更是应用与原生依赖工厂的显式接线；既有确认/授权/支付占用/订单/恢复实现全部保留。

这里的“商城”是UCP官方样例commit 99724a32da48bd0f4962c83e25f17c8345ce055e的已接受本地分支（H53R 37文件），不是上游零修改或真实线上商户。API保持2026-04-08；授权沿用H53R已接受的本地研究信封和独立确认，不把它改名成标准ap2.checkout_mandate。H54/H56的新协议/配置不导入，不以补齐全部协议为由重开安全支线。

## Allowed scope / 允许范围

唯一既有实现改动：merchant/dependencies.py的get_checkout_service函数体，原参数、原请求级Products/Transactions会话依赖及其他顶层语义节点必须不变。它通过request.app.state取得明确配置的execution_control，传给原CheckoutService；无配置保持原服务fail-closed（拒绝执行）。不能缓存/共享请求级会话或替换原生类。

唯一新增商家实现：merchant/guarded_app.py，提供create_app(execution_control=None)这个明确的应用装配入口。使用原server.app及其原生路由/错误处理/签名/数据库生命周期；可包裹原app.router.lifespan_context，在原生DB初始化后幂等初始化控制并安装/清理app.state.execution_control。原config.lifespan必须运行，不得重新写一套FastAPI路由、改config源函数或替换安全依赖。应用配置来自可信进程，不从HTTP正文/header得到控制对象、信任根或支付端口。

测试实现只允许HTTP_RUNTIME.py、RUN_JOURNEY.py；可写REPORT.md、RESULT.json、ATTEMPT_LEDGER.json及evidence/。其余36商家文件、原授权/确认/支付/恢复、SDK、src/tests、所有旧任务和本包冻结夹具/计划/合同/BASELINE只读。旧H51_HTTP_RUNTIME仅是参考（它含测试工厂替换，不能作为本轮执行路径）。新代码不能写入/清空dependency_overrides来掩盖替换；每个运行应用必须assert其为空。

可复用references/H51_METHOD_FIXTURES的独立耐久假PSP、商品请求和快照函数，以及references/H53R_FIXTURES的真实合成签名/公钥/原授权信封。不得调用这些参考文件的旧主程序/Env以冒充本轮旅程。合成商品/库存、profile/DNS离线夹具、时钟、明确故障hook和假PSP允许；不能patch CheckoutService、ExecutionControl、_process_payment、verify_signature、common_headers、业务路由或默认服务工厂。观察来自真实HTTP/SQLite/独立PSP账本，不能靠passed=true。

运行环境仍H47 Windows Python3.12的30个固定包及H37 jwcrypto1.5.6/sd-jwt0.10.4/AP2固定源码；零下载/安装。临时DB仅.task_envs/H57/runs。假PSP只是记录本地charge/query的独立SQLite账本；私钥仅内存，不落盘。真实请求签名仍由原生RFC9421验签执行，require_signatures=true，profile/DNS仅在原生查询位置提供离线公开材料，不是真实身份。

## Journey contract / 六条实际商城旅程

全部正常动作走httpx.ASGITransport的原生HTTP，不监听端口。每案例独立应用/数据库；每个应用生命周期只装配一次配置。所有case第一个HTTP为POST /checkout-sessions→201，原文/响应保存；签发确认/本地授权依据必须是这次HTTP实际返回的结账内容，**不得读DB补缺字段后重新构造一个客户拿不到的授权对象**。观察者可以读DB核对结果。如果HTTP原文与既有授权合同确实不兼容，停止报具体缺口，不改验签或商家业务凑通过。

| Case | 运行与必需结果 |
|---|---|
| M01_NORMAL_REPLAY_QUERY | 应用显式配置后：创建→独立确认/真实合成授权→HTTP完成200→同键同正文重放200→GET checkout及GET /orders/{id}均200；完成/重放响应相同并指向同一订单；独立账本1charge、1订单、库存5→4 |
| M02_CHANGED_AFTER_CONFIRM | 批准1件后用原HTTP PUT合法改2件，再带旧确认/授权完成→409；0付款/订单，库存5 |
| M03_MISSING_CONFIRMATION | HTTP签名/已签授权有效但缺h50_confirmation_ref→403；0付款/订单。不是伪造用户未同意的生产事实 |
| M04_INVALID_AUTHORIZATION | HTTP传输签名有效，但h53授权被篡改→403/H53_AUTHORIZATION_DENIED；0付款/订单 |
| M05_UNCONFIGURED_APP | create_app未配控制；默认工厂创建正常、完成→409/H50_EXECUTION_DENIED；0付款/订单；不能夹具偷偷注入 |
| M06_ORDER_FAILURE_RESTART_QUERY | 已模拟charge后在原before_order_commit hook注入一次订单失败，HTTP500原始响应保留，订单0/库存5/耐久占用与授权记录各1；真正退出该应用进程，用同DB/假PSP账本和公开信任配置启动新进程，GET checkout 200，新键重试complete 409，charge总仍1；原control.recover方法诊断QUERY/payment_state=SUCCEEDED且独立query1次，不自动重扣或补订单 |

M06两进程PID必须不同，不把重建Python对象当进程重启。第二进程请求签名可用新内存key及离线profile，但原支付授权只复用已保存的合成token和公开根；禁止落盘私钥。控制与原生业务始终用同一transactions.db。前台同步子进程允许，不得开启后台服务/真实监听。恢复诊断是原方法调用，HTTP只证明查询和重试被拦，不宣称已有HTTP恢复接口或自动完成订单。

## Evidence format / 原始交付格式

RUN_JOURNEY.py --role executor/evaluator须每次创建evidence/<role>/run_NNNN，写每case独立JSON及observations.json，最后更新LATEST.json={run:...}。允许--case CASE_ID做L1子集，但完整正式门禁必须全6。每个实际HTTP前向HTTP_ATTEMPTS.jsonl追加唯一request_id/case/run/phase/worker_pid预留；失败/进程退出仍计数，不覆盖旧输入/输出。全波次请求<=28，Executor累计<=160，Evaluator另<=80。

observations schema=h57-journey-observations/v1、boundary=NATIVE_DEFAULT_FACTORY_LOCAL_ASGI_WITH_FAKE_PSP、require_signatures=true、asgi_requests=本波实际请求数、cases按CASE_SPEC顺序。各case必须含：case、app_configured、default_factory_used=true、dependency_overrides_empty=true、calls、worker_pids、state（orders/inventory/checkouts/attempts/payment_calls）、psp_calls、authorization_records；有批准则confirmation={ref,snapshot}、authorization_public_keys。M06另psp_queries/recovery及阶段/同一存储标识，保存退出/重启的原始stdout/stderr/退出码。

calls每项含method/path/request_id/worker_pid/headers/request_body/wire_body_utf8/response_status/response_body，所有请求按真实原生签名，Content-Digest/Signature-Input/Signature证据保留；500可保留原始文本，不能丢弃或改成模拟JSON。完整原始HTTP体/公钥可含合成token，无真实付款/个人信息。确认/实际付款快照、令牌/checkout hash、PSP稳定引用及订单ID需能逐项对上；Evaluator会独立核对真实工厂、签名、生命周期和来源，不仅看布尔字段。

## Acceptance criteria

### AC-01 — 正常工厂实际接线及来源保护

Given固定37文件/配置入口；When VP-01/02/07和源码复核；Must observe36原样、只原工厂体+新装配模块改变，请求级依赖参数不变、原生生命周期/路由/签名保留、无dependency_overrides或绕过类；Must not observe新路由/SDK/业务补丁或测试工厂替换；Evidence=SOURCE_COPY/BASELINE/工厂/子进程与实际请求。Mandatory: yes。

### AC-02 — 正常完成、重放与查询

Given M01的真实HTTP数据及独立批准；When VP-03/04；Must observe默认工厂下完成与重放200/200、查询checkout及同一order200、1charge/1order/库存4、实际付款快照/确认/完整已签checkout与创建HTTP响应一致；Must not observe读取DB补客户缺字段、手填响应/多扣；Evidence=完整HTTP、签名/SDK独立复算、DB/假PSP。Mandatory: yes。

### AC-03 — 改单、缺确认、假授权、缺配置保住边界

Given M02–M05；When VP-03/04；Must observe原生更新成功后旧批准409、缺确认403、篡改授权403、缺配置409，全0付款/订单/占用/授权记录，库存5；Must not observe篡改传输签名冒充授权拒绝或默认工厂暗中配置；Evidence=逐请求与实际数据库/账本/源码。Mandatory: yes。

### AC-04 — 商城失败后状态可查且不重复付款

Given M06付款后订单提交失败及真实新进程；When VP-03/04；Must observe500原始失败留存、稳定引用、GET200/新键完成409、总1charge/0order/库存5、旧恢复诊断QUERY/SUCCEEDED与query账本；Must not observe盲重扣/自动补单或把方法诊断冒充HTTP恢复/完整结算；Evidence=两PID/进程原始流/HTTP/同DB/独立PSP。Mandatory: yes。

### AC-05 — 回归、成本及诚实整包交付

Given240分钟/2L2/160请求；When完整7项；Must observe25相关AP2回归、6计数破坏自测、原始输入/失败/请求预留保留，完整L2后一次提交；Must not observe真实资金/外部商户/标准AP2接通或生产能力虚报；Evidence=REPORT/RESULT/账本/L2/L3与源码复核。Mandatory: yes。

## Validation plan and budget

VP-01保护/环境；02工厂范围；03六条真实HTTP旅程；04原始HTTP/授权/DB/假PSP/预算；05固定25AP2回归；06计数判别器自测；07复查保护。7命令已冻结，RUN_JOURNEY/HTTP_RUNTIME和装配实现由Executor新增，尚不存在，不把准备复制/旧H51基线当本轮成功。

Executor<=240主动分钟、2正式L2、ASGI预留<=160，每完整波次<=28；Evaluator另<=80。只有前述本地ASGI/同步子进程/假PSP调用允许，外部网络仍0。正式前ATTEMPT_LEDGER预记formal_l2_attempts（等于l2_executor_01/_02目录数）、active_work_minutes、asgi_requests_reserved（等于HTTP_ATTEMPTS预留行数）；network_calls/model_calls/provider_calls/real_payment_calls/packages_installed/git_write_operations全0。ASGI与假charge/query按实记，不能再写全0。

REPORT执行后真实生成，含Task ID/Task kind/Baseline HEAD、逐AC/所有EV/Impact comparison、真实请求与模拟charge/query总数、失败/成本、工厂与旧测试替换区别、已有/新证据、PCAC及残余。RESULT schema=h57-result/v1、task_id本任务、classification=DEFAULT_FACTORY_MERCHANT_E2E_OBSERVED仅完成后可填、customer_demand=UNKNOWN、remaining_gaps非空；production_ready/real_identity_verified/provider_verified/standard_checkout_mandate_integrated/h56_profile_integrated/automatic_order_recovery/customer_value_proven全false。

完整L2通过才SUBMITTED_FOR_REVIEW，CURRENT仍EXECUTING/Executor；Evaluator接受未变快照后统一独立L3。H56不在本包运行，也不宣称已完成/失败；当前由Evaluator转向主线，不是重置其预算。无自动H57R或H58。

## Stop conditions and exclusions

需改第二个既有商家函数/其余源文件、SDK、既有确认/授权/支付/数据库/恢复、协议版本或冻结AC/计划/预算/权限立即停回Evaluator。若HTTP返回内容不足以满足原授权合同，记录准确字段/责任缺口，不读DB补造、改验签放行或顺手迁移协议。保护漂移、秘密落盘、预算耗尽/无新机制重复同样停止，保留证据。

通过后STOP本地正常入口接线，按真实业务旅程证据再选下一缺口；不能为了更多字段再默认转回H56。失败则只围绕商城真实断点修复或STOP/SWITCH。没有外网/DNS真实调用/监听/uvicorn、生产或沙箱支付、真实密钥/PII、模型、下载/安装、外部联络、Git写操作、钱包/测试网/区块链或通用Agent运行时。

## External requirement impact

已核对PCAC开发指标映射。profile=PCAC-AGENTPAY；PCAC-07/09=CORE，before=方法/测试工厂已有本地证据，after_target=默认工厂实际HTTP旅程接线；PCAC-08=CORE/ADAPTER，只有合成独立确认/签名来源，真人身份/同意不升级；PCAC-12/20=CORE/EVIDENCE_ONLY，Test=6旅程/7计划、Evidence=HTTP/DB/假PSP/工厂/L2/L3；PCAC-18=CORE/ADAPTER仅查询不重扣，不声称完整事故恢复；10跨系统撤销不变。无生产/监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
