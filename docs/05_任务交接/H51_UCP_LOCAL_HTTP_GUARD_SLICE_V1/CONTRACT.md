# H51 固定商家HTTP入口的受控交易切片

Task ID: H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-20-r82
Active bottleneck: B-17
Hypothesis: H-51

最终目标是授权、绑定、受控执行、恢复、审计可信；A–D完成、E本地代表性闭环、F当前。H50R2已独立接受本地方法级修复，停止继续堆锁测试。下一最前缺口是原生HTTP路由、签名检查、服务工厂、合成确认与已验收控制能否接成同一调用链。源码已知dependencies.get_checkout_service不传execution_control，不能预设直接启动即具受控付款；新增价值是测量真实路由上的接线和拒绝结果，不再研究泛化设计。

本包是one_off/measurement-only（只测量），不是产品能力建设。唯一主变量为任务夹具的FastAPI服务工厂依赖注入：同一固定商家副本，无注入对照应拒绝执行；注入合成ExecutionControl后，正常完成且非法输入零付款。原生路由、签名验证、请求模型、业务与控制源码全部只读。AP2已闭合首链；支付宝/比赛仍Human延期。商业问题/负责人/预算未知，但再扩团队名单不能替代这一已知技术接缝；本包不联系客户、不宣称需求成立。

## Single objective / 唯一目标

用实际固定FastAPI应用的进程内ASGI（应用服务器网关接口）HTTP请求，测出上述接线是否可行及在哪里失败。不得直接调用服务方法冒充HTTP结果；不得另写路由、验签器或简化商家。只在任务夹具使用app.dependency_overrides[dependencies.get_checkout_service]注入原生CheckoutService的既有execution_control参数，正确保留原生请求级产品/事务会话与履约服务。无注入对照清除该覆盖，不给原生默认工厂偷偷注入。

复用H47固定应用/签名/离线profile夹具思路和固定30包，复用H50R2独立模拟付款账本及快照函数。复制的36文件全部冻结。临时本地合成EC私钥只存内存；签名profile/DNS/HTTP返回均离线fixture（夹具），禁止真实网络。正常签名仍由原生verify_signature执行，require_signatures=true；不能覆盖common_headers、verify_signature、路由函数、_process_payment或ExecutionControl来造期望结果。

## Acceptance criteria

### AC-01 — 固定来源与范围

Given已接受H50R2副本和H47环境；When VP-01/07；Must observe36实现逐字相同、父任务/产品/冻结材料不变，仅HTTP_RUNTIME.py、HTTP_MEASURE.py和允许交付改变；Must not observe新依赖、源码/原生路由/签名/业务补丁、套壳API或隐藏真实网络；Evidence=BASELINE/INHERITED_COPY/源码与运行审阅。Mandatory: yes。

### AC-02 — HTTP正常完成及幂等

Given实际HTTP创建201、可信本地fixture签发一次确认；When C01经签名complete与同键同正文重放；Must observe200/200、独立账本总1charge、1订单、库存4、实际付款完整快照等于那次确认，回放相同订单；Must not observe仅服务方法直调、原生付款计数冒充金额绑定、重复付款或弱化签名；Evidence=逐HTTP请求/响应、DB状态、独立模拟账本。Mandatory: yes。

### AC-03 — HTTP拒绝保住边界

Given C02确认后经HTTP合法更新数量、C03缺确认、C04伪确认、C05无签名、C06签名后改正文、C07默认工厂无注入；When HTTP complete；Must observe冻结状态/错误码及零charge/零订单/库存5，无签名401、正文篡改400；C07应409/H50_EXECUTION_DENIED，不得悄悄以正常夹具覆盖它；Must not observe允许付款、数据库500或把HTTP签名当用户支付授权；Evidence=8场景原始HTTP流、数据库与账本。Mandatory: yes。

### AC-04 — 在途HTTP竞争及已接受方法回归

Given C08同checkout两HTTP请求/不同键，首笔模拟付款后订单尚未提交；When第二笔到达并释放首笔，记录事件循环heartbeat（心跳调度延迟）；Must observe首笔200、第二笔409、总1付款/1单/库存4、两独立请求标识与<2秒心跳；原2+15+4+2方法场景保持；Must not observe移钩子、强制串行/全局锁、重复付款或把共享测试服务实例当原生请求会话；Evidence=HTTP/会话/钩子/账本及VP-02..05。Mandatory: yes。

### AC-05 — 诚实测量与可复核结果

Given完整8场景、计划和预算；When VP-06..08及完整L2；Must observe正常和负向样本/独立账本齐备，RESULT单一分类、未支持则说明具体接缝，REPORT/DESIGN/账本/原始EV齐全；Must not observe生产/真实身份/跨系统撤销/Provider/客户/全局竞态闭合结论；Evidence=校验器、自测、原始流、Evaluator独立L3与源码审阅。Mandatory: yes。

## Allowed scope

只允许新建/修改本目录HTTP_RUNTIME.py（离线应用夹具）、HTTP_MEASURE.py（8场景测量），以及REPORT.md、DESIGN.md、RESULT.json、ATTEMPT_LEDGER.json、evidence/。临时DB仅.task_envs/H51/runs下。merchant/36文件、复制的FROZEN_TESTS/REPAIR_PROBES/CLAIM_RACE_PROBES、HTTP_CHECKER、EVALUATOR_CHECK、合同/计划/来源/许可/入口/基线/REVIEW全部冻结。其他项目/旧任务只读。

可在夹具初始化时创建合成商品、库存、确认与独立假PSP；可按冻结测试点安排竞争。成功动作必须从真实HTTP入口进入，不能把method-test（方法测试）结果替换到HTTP观察。恢复仍沿用本地服务证据，不新增HTTP恢复/签发端点。C02更新必须走HTTP；本地fixture签发确认不是生产认证接口。

CURRENT只可CONTRACT_FROZEN→EXECUTING/Executor及phase更新，关联/历史/授权/next_artifact=REPORT不变。无其他聊天消息或代理。

## Exclusions

没有对外HTTP/DNS/socket、监听端口/uvicorn、真实商家/支付/Provider/客户联系、下载安装、模型、Git动作；ASGI进程内请求不等于外部接入。禁止改签名/确认/授权义务、修改已接受控制或通过FastAPI覆盖安全依赖来通过。发现需改原生模型/路由/业务或新增包，停止并报告精确合同缺口，不自动实现适配器。

## Validation / Deliverables

冻结8项：VP-01基线；VP-02原生2；VP-03保护15；VP-04旧修复4；VP-05写锁2；VP-06真实HTTP8场景；VP-07材料与独立HTTP断言；VP-08检查器自测。运行公共run_validation，先廉价L1再完整L2，不手造原始输出。ARCHIVE_AND_RUN在覆盖观察前按hash归档。L2通过才能SUBMITTED_FOR_REVIEW；Evaluator接受快照后独立L3并审查夹具是否保留真实路由/验签/会话及账本。

HTTP输出遵循HTTP_CHECKER的h51-http-observations/v1；每场景calls为实际请求顺序记录，含method/path/request_body/headers/response_status/response_body；state来自实际DB；psp_calls来自独立SQLite账本；confirmation保留本次付款前签发的完整快照。C08保留两session/connection标识、钩子和heartbeat。禁止以passed=true替代原始数据。

RESULT schema=h51-result/v1，classification为LOCAL_HTTP_SLICE_OBSERVED或CONTRACT_CHANGE_REQUIRED（后者列精确缺口，不能冒充8场景通过）；customer_demand=UNKNOWN；production_ready/real_identity_verified/cross_system_revocation_verified/provider_verified/customer_validated/global_race_closed/product_core_changed全false。无注入与注入差异仅为人工接线夹具证据，不称原生开箱覆盖。

REPORT按公共v2.2模板给Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat、每AC、真实EV、成本与残余；DESIGN解释原生工厂、注入点、签名profile/信任假设、端口与方法继承边界。账本正式L2<=2、active_work_minutes<=240；network_calls/model_calls/provider_calls/external_runtime_calls=0；asgi_requests按实计<=160，单次完整HTTP观察<=40，Evaluator独立请求预算<=80。asgi_requests不得再写零。

## Budget

4主动小时/2次正式L2，串行一包、代理0。正常完成或精确CONTRACT_CHANGE_REQUIRED都交Evaluator；不能为了跑完8例而扩大原生代码范围。旧任务预算不重置。本地HTTP离线夹具成本中等、现有环境可复用，优先级高于继续本地锁修复；若证据显示必须重写商家，停止该切片。

## Stop conditions

父任务/冻结漂移、出现真实网络请求/新依赖/秘密落盘、需改原生实现/安全依赖、请求或时间预算耗尽、相同失败无新依据即停止交Evaluator。通过后STOP本HTTP切片，不无限加路由；后续比较真实授权来源/Provider合同与需求证据，无自动联网。失败则改商家部署/接入合同或停止，不自动H50R3。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## External requirement impact

已检查PCAC开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=仅本地方法证据，HTTP注入未知；after_target=固定本地HTTP夹具结果可复核，不升级产品/生产身份成熟度；Test=VP-01..08；Evidence=完整HTTP/DB/假PSP与独立L3；残余=可信用户签发、跨系统撤销、真实Provider/部署授权/需求未知；无监管合规结论。
