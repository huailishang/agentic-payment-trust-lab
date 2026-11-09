# H50 固定UCP商家本地副本：持久化执行占用样机

Task ID: H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L2
Contract state: CONTRACT_FROZEN
Owner: Executor
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H50_UCP_LOCAL_MERCHANT_GUARD_PROTOTYPE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-20-r79
Active bottleneck: B-17
Hypothesis: H-50
Measurement status: H49只读工程设计已PASS，商家执行约束未实现；Evaluator准备重新运行两个原生方法级对照，正常库存5→4、改数量后5→3，均一次原模拟付款调用。原付款方法没有金额/收款人/快照参数，原生金额绑定基线为NOT_OBSERVABLE，不能伪造before数值。
Metric baseline: 固定原生源码仍可完成修改后的两件；H48客户端窗口为继承证据。新增可观察付款接口后的安全结果只代表改合同后的本地样机，不作原协议原生能力或全产品改善宣称。
Estimated affected scope: 一个固定商家方法级副本、15个保护场景、两个原生对照；无HTTP、真实身份/Provider/客户代表性。
Expected project impact: 判断持久化执行占用能否在真实原生业务流程内协调写入口、保持付款绑定并安全查询恢复；不升级产品核心/生产成熟度。
Rollback condition: 要改范围外业务、重写商家、不能独立观察快照或完成并发/崩溃判定则停止，不扩接口或预算。

目标仍是授权→绑定→执行→恢复→审计；A–D完成、E本地闭环、F当前。B-17优先于延期支付宝/比赛和继续客户端案例。唯一主改变是持久化执行占用；可信确认存储、付款观察和恢复记录只是验证它所需配套，不抽通用平台。

## Single objective / 唯一目标

在固定UCP商家本地方法级副本内实现执行占用机制，使complete/update/cancel共同遵守付款前冻结快照和持久状态，正常可完成、错绑定/第二次付款被拒，付款前已提交的引用支持异常查询恢复。保留原生创建、商品/履约校验、库存预留、订单及幂等流程；不得另写理想化商家满足判卷器。

这是一次性任务内原型，不是项目级提升实验。完整HTTP签名、真实用户身份、跨系统撤销、真实付款/退款和商业收益均不在证明范围。

## Fixed source / 来源与环境

来源H47固定commit `99724a32da48bd0f4962c83e25f17c8345ce055e`，Apache-2.0；35个server文件已复制merchant/，SOURCE_COPY记录原hash，UPSTREAM_LICENSE保留许可。H47/H48/H49原件、src/tests与公共工作流只读。复用`.task_envs/H47/.venv/Scripts/python.exe`的Python3.12/固定30包，不安装升级。

FROZEN_TESTS直接调用真实CheckoutService方法，不走客户端包装、不启动ASGI/HTTP；socket拒绝联网，状态只在`.task_envs/H50/runs`临时目录。preparation_20261020是Evaluator准备：原生2条已测、模拟账本自测/脚本语法/副本局部性通过；15保护场景未执行，控制实现当前不存在。准备不等于Executor结果或H50通过。

## Frozen interfaces / 冻结调用约定

### 原生入口与付款

CheckoutService保留原路径和方法签名，仅构造函数末尾增加可选keyword `execution_control=None`。创建/查询保持原义；complete/update/cancel缺控制时拒绝风险执行。本包不证明HTTP迁移兼容性。

complete由risk_signals里的`h50_confirmation_ref`携带确认引用；此不可信字段仅用于查可信存储，不能把请求正文当授权。同键异正文拒绝；同键历史成功只返回旧结果，撤销后查旧成功亦可返回，不新增付款。

`_process_payment(payment, *, execution=None)`保留原付款工具/凭据校验语义，在执行记录独立提交后，将`execution['payment_ref']`和`execution['snapshot']`送注入付款端口。不能在别处造成功再让原付款方法空跑；冻结观察器直接截获这个原生方法入参。

### 任务内ExecutionControl

新增`merchant/services/execution_control.py`，导出：

```python
ExecutionControl(transactions_path, payment_port, *, now, hook, merchant, payee)
await control.initialize()
confirmation_ref = await control.issue(snapshot_dict, *, expires_at)
await control.revoke(confirmation_ref)
outcome = await control.recover(checkout_id)
```

issue/revoke仅是可信测试夹具/内部入口，不暴露成普通商家请求。确认与撤销在同一事务数据库持久保存；引用不存在、过期、撤销或当前快照不匹配均拒绝新占用。合成merchant/payee、可信存储是测试前提，不证明身份或密码学签名。

snapshot严格包含冻结测试独立投影的checkout_id、merchant、payee、currency、完整line_items、totals及fulfillment；保留整数最小货币单位，不删字段/只比总额/信任客户端重建确认。

recover只能查询付款端口，不发款；返回字典decision为既有WAIT/QUERY。即使查明成功，本包允许保留待对账/订单补记，不实现自动退款/修复订单。正常完整付款仍返回原生Checkout。

拒绝/等待使用现有UcpError异常及status_code=400/403/409（DENY）或202（WAIT/QUERY），code/reason清楚；不能靠TypeError、数据库锁500或任意程序崩溃冒充安全拒绝。只有冻结故障注入场景允许预期RuntimeError，其他异常均需原范围修复。

### 持久化与事务

事务A在共享数据库核对当前checkout/确认/撤销，原子争抢唯一占用，写稳定payment_ref、冻结snapshot和IN_FLIGHT，成功COMMIT之后才发款。h50_attempts至少有checkout_id（唯一）、payment_ref、snapshot_json、state，可加请求键/hash等必要字段。所有相关写路径参加同一协调，不能先查标记再独立写。

claim提交后update/cancel不得改/取消该笔快照；撤销先提交则拒绝，claim先提交/撤销后到按已有在途处理。这仅定义本地共享事务先后，不推出跨服务撤销。

事务B保留原生库存/订单/checkout终态/幂等结果提交；B失败不能擦除A或推断退款。崩溃可发生在来不及写UNKNOWN之前，恢复用A引用查账。查询NOT_FOUND仍不得盲目重发，保持WAIT/QUERY；异常恢复后旧键/新键均不再付款。

必须数据库事务/条件写/唯一约束，不以进程锁替代。独立模拟账本记录每次charge，即使相同引用也计数，不让PSP去重掩盖二次调用。

### 调度与故障观察

调用`await hook(event, checkout_id)`，正常无故障时仅观察：

- before_claim：读取拟核验状态后、A取得写锁/写入前，不能持有阻塞另一合法update的写锁。
- before_claim_commit：A即将提交，可抛错；整体回滚，零付款/零持久占用。
- after_claim_commit：A已提交、付款前，独立连接可读IN_FLIGHT/引用/快照。
- after_payment：独立模拟账本已持久成功、B完成前，可直接退出进程。
- before_order_commit：原生库存/订单B提交前，抛错后库存/订单回滚但A与模拟付款仍在。

付款端口为`await charge(payment_ref, snapshot)`、`await query(payment_ref)`，使用与商家分离的SQLite账本。真实方法产生调用，不能由报告脚本造观察。并发来自不同AsyncSession/数据库连接，冻结测试记录其标识/屏障。

## Acceptance criteria

### AC-01 — 来源、范围与权限

Given固定HEAD/35副本/旧证据/环境；When VP-01/04；Must observe保护hash、未改定义、四旗、许可一致；Must not observe改产品/历史/计划、安装、网络或ASGI；Evidence=baseline/source_locality。Mandatory: yes。

### AC-02 — 正常进展与绑定拒绝

Given原生对照及G01–G06/G14；When VP-02/03；Must observe原生两个对照完成、保护后正常付款一次/一单、原生付款方法及独立账本收到完整确认快照；变更/缺确认/伪造引用/过期/撤销/缺控制均零付款；Must not observe全阻断、伪造金额绑定before、客户端包装替代；Evidence=原生/保护观测。Mandatory: yes。

### AC-03 — 共享写协调、幂等与竞争

Given G07–G10；When VP-03/04；Must observe同键重放无新付款、异正文/终态新键拒绝；update先则旧确认付款0；claim先则update/cancel拒绝、冻结交易付款1；claim后撤销不当自动退款；两个独立连接complete仅一单/一次charge；Must not observe串行重放/进程锁/PSP去重掩盖；Evidence=会话/连接/屏障/账本。Mandatory: yes。

### AC-04 — 分离提交、崩溃与恢复

Given G11/G12/G13/G15；When VP-03/04；Must observeA失败零付款/占用；付款后B失败订单/库存回滚但A保留；真实子进程付款后/前退出，重启仍按稳定引用查询，旧键/新键不再charge；Must not observe回滚等同退款、依赖未落盘对象/事后补UNKNOWN；Evidence=SQLite状态、worker exit71、模拟付款/查询。Mandatory: yes。

### AC-05 — 有限结论与交付

Given全材料/15保护场景/2原生对照；When VP-04/05及完整L2；Must observe原始EV、报告/设计/账本/结果齐备，local原型与核心/生产/身份/跨系统撤销/Provider/客户分开；Must not observeH49未来14项全称已测、模拟身份称认证、客户或项目提升；Evidence=REPORT/DESIGN/RESULT/账本/自测。Mandatory: yes。

## Allowed scope / 允许范围

只可改merchant/services/checkout_service.py中的__init__/complete_checkout/update_checkout/cancel_checkout/_process_payment及必要新增私有辅助，其他原始方法AST不变。merchant/db.py可新增表/帮助函数，原定义AST不变。可新增merchant/services/execution_control.py。其他33副本/上游只读。

可写本目录REPORT.md、DESIGN.md、RESULT.json、ATTEMPT_LEDGER.json和evidence/执行者证据。CURRENT仅可CONTRACT_FROZEN→EXECUTING/Executor和phase更新，next_artifact保持REPORT，历史/关联/地图/权限不动。不能接受提交或签最终PASS。

冻结CONTRACT、计划、FROZEN_TESTS、EVALUATOR_CHECK、SOURCE_COPY、许可、PREPARE_FREEZE、EXECUTOR_START、REVIEW占位及BASELINE；其他目录只读。禁止改检查器迁就实现。

## Serial execution and deliverables

S0冻结baseline→S1最小占用/可信存储及原生接线→S2正常/拒绝/竞争/故障局部检查→S3完整测试与报告→S4完整L2/中央校验，一次交Evaluator。阶段间不等签字，仅硬边界/预算/假设变化停止。

DESIGN写保留/改变部分、A/B与锁范围、合成来源、hooks、恢复限制、最强反对理由。RESULT schema=h50-result/v1、classification=LOCAL_SERVICE_PROTOTYPE_ONLY、measurement_boundary=LOCAL_NATIVE_SERVICE_METHODS_SYNTHETIC_TRUST_FAKE_PSP_NO_HTTP、local_guard_implemented=true；product_core_changed/production_ready/real_identity_verified/cross_system_revocation_verified/provider_verified/customer_validated/global_race_closed全false；customer_demand=UNKNOWN、native_amount_binding_baseline=NOT_OBSERVABLE。

REPORT按公共v2.2模板，Task ID/HEAD、SUBMITTED_FOR_REVIEW、Workspace snapshot/Changed files、Before/After/Delta/Measurement evidence/Guardrail result/Scope caveat、AC、真实L2/EV、成本及偏差齐全。L2未通过不提交。

## Exclusions / 排除范围

前述限制保持：不改上游原件/产品核心/无关副本，不改冻结验证，不安装下载、调用网络/ASGI/模型/Provider、联系客户或进行Git操作；不验证真实身份/跨系统撤销/真实支付，不自动退款补单，不重做H49泛化研究。

## Validation / Budget

VP-01保护；VP-02原生2条；VP-03保护15条；VP-04材料/观测/来源局部性；VP-05结论检查器自测（模拟账本自测另有准备证据）。Evaluator原样复跑，仅观测输出改_l3。语义仍需人工源码复核。

主动6小时/正式L2最多2次，每次新目录保留失败；廉价L1可用guarded --case单项，不冒充完整验证。代理并发0、运行任务并发1；内部会话/故障worker属于冻结验证动作。账本记formal_l2_attempts、active_work_minutes（自报）、每次原因/目录/余额；asgi_requests/network_calls/model_calls/provider_calls/external_runtime_calls全0；内部方法、模拟charge/query和子进程成本按实际记录，不假称零。

## Stop conditions / 停止条件

保护/环境漂移、改范围/假设/检查器、新依赖/网络、超预算或同失败无新依据即BLOCKED交回Evaluator。完成不自动上生产/改核心。局部协调若成立再判断更大集成价值；若只是假商家或维护代价高于信号，停止/换候选。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## External requirement impact

已核对PCAC映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=H49设计已核查、执行约束未建；after_target=任务内本地合成方法级样机证据，核心/生产不升级；Test=VP-01..05；Evidence=固定源码/原生对照/冻结观测/本包L2及后续L3；残余=无真实身份/跨系统撤销/HTTP/Provider/客户，无合规结论。
