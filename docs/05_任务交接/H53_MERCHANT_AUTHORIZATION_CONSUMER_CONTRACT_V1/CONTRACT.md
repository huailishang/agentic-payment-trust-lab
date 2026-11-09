# H53 本地商家授权消费与执行快照绑定

Task ID: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L2
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r86
Active bottleneck: B-17
Hypothesis: H-53

目标是高风险支付的授权、绑定、执行、恢复与审计可复核。A–D阶段关闭，E仅本地受控代表性验证，F当前。H52 PASS/NOT_APPLICABLE/STOP同类就绪测量，H51本地锁/HTTP切片STOP不变。B-17最前断口是已验签原文与业务投影、独立确认和实际执行快照未被同一消费者强制结合。

Human于2026-10-31要求“继续完善”，Evaluator据此补齐样本/环境/接线判定并冻结本包；原草案保存在DRAFT_BEFORE_FREEZE_20261031.md。当前合同把未冻结的设计草案收窄为任务副本one_off（一次性样机），不扩大网络、生产或Git权限，不宣称产品核心能力提升。

Measured baseline（已测基线）：H52 Q04金额投影变化仍ALLOW、Q06币种变化被归一；H51已有持久claim（执行占用）、同库确认、一次模拟付款/恢复及无控制拒绝。PREP-05进一步用H51已接受C01创建响应的完整10字段checkout做真实JWS+官方两跳签验，正常/已签金额冲突/已签币种冲突3例均经既有局部接口ALLOW。未运行商家，不能当成错误付款实证。

Expected impact（预期作用）：验证固定本地消费者能在同一claim事务结合这些事实并拒绝共同断口。Estimated cost（估计成本）：中等，6主动小时/2次正式L2，零安装/模型/外部调用。优于继续锁/HTTP重复样本；完整2026-08-25迁移或Stripe/Medusa增加新变量，当前不优先。

## Single objective / 唯一目标

**受信SDK原文、完整商家签名载荷、请求投影、同库确认和当前数据库快照全部相符，才提交claim并触发一次模拟付款。** 验签/绑定/确认失败须零占用、零授权记录、零付款、零订单；不能只放在可绕过的客户端。

商家仍UCP 2026-04-08，不广告AP2扩展、不建设2026-08-25协商锁定或完整JCS（JSON规范化）。使用保存原始字节的完整普通compact JWS（紧凑签名），不是detached JWS（分离载荷签名）。这是明确声明边界的本地研究切片，不是完整UCP/AP2符合性。

## Inputs, versions and trust / 输入、版本与信任

1. INHERITED_COPY固定H51已接受36商家文件及许可；SAMPLE_CHECKOUT来自正式L3/C01创建响应，含id/ucp/currency/line_items/totals/fulfillment/links/payment/status/discounts。create把同一response_body存入checkouts.data，完整当前对象可在claim事务内读取。
2. 复用H47 Windows Python3.12及旧H37纯Python依赖，固定AP2 v0.2.0/b4587ac1d055888a73b4b21750973cffba961793、cryptography46.0.7、pydantic2.13.4、jwcrypto1.5.6、sd-jwt0.10.4、ucp-sdk0.4.6、PyYAML6.0.3。四个常见JCS模块名不可导入只证明该次检查，不声称穷尽实现；本切片无需安装或实现JCS。
3. 四合成角色user/agent/merchant/attacker各一把内存P-256私钥，仅公钥/公开合成材料落证据，SDK日志只写.task_envs/H53/runs。不由请求自带公钥、身份字符串或consent布尔值建立信任。
4. ExecutionControl新增authorization_context=None构造参数，可信字段见FIXTURES.context：trusted_root_public_jwk、merchant_public_jwk、expected_aud、固定experiment_context；merchant/payee沿用受信构造值。无配置可构造/初始化以便明确拒绝，但claim必须拒绝，不可回退旧放行。
5. 继续使用既有issue/revoke与h50_confirmations，夹具从真实创建快照签发独立合成确认，不新建确认服务/端点。请求confirmation_ref只是查库索引；到期/撤销/checkout及快照绑定在原同库事务检查，不自动重签旧确认。
6. complete仍用risk_signals：h50_confirmation_ref沿用，h53_authorization为本地信封，schema=h53-local-authorization-envelope/v1，字段payment_token、checkout_jws、projection。它不是标准ap2.checkout_mandate。projection只包含open_payment_mandate/payment_mandate，必须与官方验签返回的唯一两类原文完全一致，不能直接信任其业务字段。
7. payment_token为官方OpenPaymentMandate→PaymentMandate两跳，root cnf.jwk绑定代理。可信aud=h53-local-merchant，nonce=h53:<实际confirmation_ref>，时钟=self.now，均不可由请求替换。复用既有验签适配/官方SDK，从verify结果取有效载荷；不得从另一个未验签JSON代造可信字段。SDK验证使用clock_skew_seconds=0，并明确要求当前时刻早于root/terminal exp。
8. checkout_jws签署完整checkout UTF-8字节，验受信商家ES256公钥/算法，保留原compact字符串；PM.transaction_id必须等于base64url(SHA256(compact字符串))。完整JSON不经schema丢字段，签名对象须与事务内完整checkouts.data一致，包括未知字段。可用严格确定性的本地JSON表示比较，不得称通用JCS；有歧义的输入拒绝，不能补默认值。
9. 金额取唯一type=total的整数minor-unit（最小货币单位）总额，PM金额须与checkout总额一致；PM币种、root AmountRange币种和checkout币种分别读取并相等，payee等于受信收款方，禁止用根币种覆盖终端币种。复用既有适配/validate_request，仅ALLOW继续；业务时间取可信时钟，不采信请求occurred_at。
10. 旧AP2正式CheckoutMandate类型与新UCP ap2.checkout_mandate位置只作后续参考；本包不实现此标准凭据。完整普通checkout签名/旧支付两跳链不能升级为完整协议授权结论。

## Interface and atomic seam / 接口与原子接线

唯一principal change（主要变化）是claim内强制消费授权：

- checkout_service.py仅给现有claim调用新增authorization=risk_signals.get("h53_authorization")，精确替换由CHECK.scope固定，其余代码不变。risk_signals已计入原request_hash，同键不同正文冲突保持；完全相同的已完成请求可返回原缓存响应，不再付款，无须把历史查询当新授权执行。
- execution_control.py只可改__init__、initialize、claim；claim新增keyword authorization=None。保持before_claim钩子、timeout=0锁、原确认/快照检查、占用提交及恢复接口。**校验必须在BEGIN IMMEDIATE之后，读本次确认及完整当前checkout之后、写任何attempt/evidence之前完成**，不先验证再释放锁，不依赖客户端提前检查。输入字典可变，必须在钩子之后按本次实际输入验证，禁止缓存可变ALLOW对象。
- 新merchant/services/ap2_authorization.py承载验证，建议单入口verify_authorization(envelope, *, trusted_context, current_checkout, confirmation_snapshot, confirmation_ref, merchant, payee, now)。可调整模块内部实现细节，不扩大核心或改SDK。
- initialize仅新增h53_authorizations表：checkout_id主键、token_sha256、checkout_sha256、confirmation_ref、decision。两摘要为原始token/compact JWS UTF-8字符串SHA256十六进制，decision=ALLOW，与h50_attempts同事务提交/回滚。不得给旧表加列破坏原方法。claim仍返回payment_ref和snapshot，复用原付款/订单/恢复；不改付款端口隐藏重复。

## Acceptance criteria

### AC-01 — 范围、来源与环境

Given冻结源/样本/环境；When VP-01/02/03；Must observe HEAD、保护和冻结摘要、34不可改商家文件及两文件指定修改范围正确，零安装/版本声明诚实；Must not observe旧任务/src/tests/SDK改动、自动升级/网络/真实密钥；Evidence=BASELINE/INHERITED_COPY/准备记录/EV-01..03。Mandatory: yes。

### AC-02 — 原文、投影与支付字段同源

Given真实签名和受信配置；When VP-04/05；Must observe T01正常可执行，T02–T11及T24–T27类型化拒绝且零占用/授权记录/付款/订单；尤其已签金额/币种冲突必须拒绝，不能只修未签投影；Must not observe自带根、未验签JSON或币种归一掩盖冲突；Evidence=原始信封/公钥/DB/付款观察、独立SDK复算与源码审阅。Mandatory: yes。

### AC-03 — 事务内执行不可绕过

Given同库确认与真正claim入口；When VP-04/05；Must observe T12–T19/T22/T23拒绝零副作用，T17更新穿插/T18未知字段变化拒绝、T28完整未知字段保持可执行，T16直接claim无授权仍拒绝；Must not observe客户端检查/默认无配置回退/刷新确认/丢未知字段/付款后比较；Evidence=真实方法/独立SQLite/事件/审计记录和源码位置。Mandatory: yes。

### AC-04 — 一次执行、并发与恢复

Given合法信封；When VP-04/05；Must observe T01正常+同键重放总1付款1单，T20两独立连接竞争总1付款1单，T21付款后订单写失败时1付款0单、占用和授权记录持久，重新构造控制对象查询同一引用SUCCEEDED，重试不付款；付款快照与占用及已签原文的原有快照投影一致；Must not observe假并发、隐藏charge或把对象重构称新进程故障覆盖；Evidence=原始调用/DB/假PSP每次charge/查询/连接标识。Mandatory: yes。

### AC-05 — 回归、预算与完整交付

Given6主动小时/2正式L2/280材料case；When完整VP-01..09；Must observe76相关回归+H37八例保持，正式EV三件套/28完整观察/失败重跑保留、L3可复算、九项过度声明false；Must not observe未过L2即提交、覆盖旧观察或把准备/未来测试算能力PASS；Evidence=REPORT/RESULT/账本/原始门禁/保护核对。Mandatory: yes。

## Validation and budgets

FROZEN_TESTS固定28场景：T01/T20/T21/T28为正向或生命周期，其余24拒绝。测试调用真实复制商家方法/SQLite/独立假PSP，每次charge都记录。T21是异常注入与控制对象重构；新HTTP、跨系统撤销、全竞态与生产行为未测。

VP-01保护/环境，VP-02完整输入签验smoke，VP-03实现范围，VP-04方法28例，VP-05原始材料复算，VP-06相关76回归，VP-07旧H37八例，VP-08完整材料，VP-09检查器自测。准备已过完整签验/3例before/76+8回归；没有候选实现或28例执行成绩，不算Executor L2。

Executor最多360主动分钟、2次正式L2、280case（最多10次完整28例波次），每波先预留28、失败也计数，串行max_parallelism=1/代理0。Evaluator另账本上限112case，不改Executor账本。观察覆盖前按hash归档，方法失败保存公开输入/错误/可读状态，新正式目录不得复用。合同内失败可修，范围/预算变化即回Evaluator；整包后一次集中复核。

## Allowed scope and deliverables

Executor仅改merchant/services/checkout_service.py固定claim参数、merchant/services/execution_control.py三个方法，新增merchant/services/ap2_authorization.py，填写REPORT/RESULT/ATTEMPT_LEDGER及evidence。其他34商家文件、样本/合同/计划/冻结脚本/来源/BASELINE、src/tests、H37/H47–H52和依赖只读。临时输出仅.task_envs/H53/runs。

REPORT须逐AC、Impact comparison（前后比较）、完整L2和每条EV引用、失败/花费/局限，只有完整L2通过后SUBMITTED_FOR_REVIEW。RESULT schema=h53-result/v1、classification=LOCAL_AUTHORIZATION_CONSUMER_OBSERVED，customer_demand=UNKNOWN、remaining_gaps非空、CHECK.FALSE_FLAGS九项false。账本formal_l2_attempts<=2、active_work_minutes<=360、artifact_cases_run<=280且等于各波cases_reserved之和；network_calls/asgi_requests/model_calls/provider_calls/real_payment_calls/packages_installed全0，假PSP与真实支付计数分开。

CURRENT仅CONTRACT_FROZEN→EXECUTING/Executor及execution_phase更新，next_artifact=REPORT、任务/地图/权限不变，不得改Evaluator/PASS、向其他聊天发消息或调用代理。

## Exclusions and stop conditions

零外网/socket监听/DNS/ASGI/HTTP/模型/Provider/真实或沙箱支付/安装/真实账号密钥/个人信息/对外联系/Git写操作。不做协议迁移/扩展广告/完整JCS/标准CheckoutMandate接入/生产身份密钥治理/跨系统撤销/新审计产品，不改原业务/库存/订单/恢复/SDK/付款端口。

需要第三个既有商家文件、上述三个方法以外修改、核心/冻结测试/权限/预算变化或新架构义务时停止报精确原因，不能为通过测试扩张。保护漂移、秘密落盘、预算耗尽、相同失败无新机制也停止。通过后STOP此本地切片，后续协议/HTTP/主体/Provider按证据授权另评。

## External requirement impact

已核对PCAC指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=既有产品局部M3–M5证据、本切片未实现；after_target=固定合成本地切片可测试/留证，产品/生产身份成熟度不变；Test=VP-01..09；Evidence=合同/原始签名/DB/假PSP/独立L3；残余=真实主体和确定性确认来源、完整协议/JCS、跨系统撤销、Provider/部署/客户未知。无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
