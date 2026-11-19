# H79：真实凭据事实的消费上下文保真测量

Task ID: H79_VERIFIED_FACT_CONTEXT_CONSUMER_MEASUREMENT_V1
Task kind: evaluator_design
Workflow: evaluator-executor-workflow/v2.2
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-17-r134
Active bottleneck: B-23
Hypothesis: H-79
Dispatch mode: SINGLE
Validation plan file: docs/05_任务交接/H79_VERIFIED_FACT_CONTEXT_CONSUMER_MEASUREMENT_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

最终目标为授权→可信主体→交易治理→支付→恢复→审计。H78已独立签收受控新鲜来源：L2/L3各6/6，真实根/登记/UID/SVID/持有/十负例/原130/清理成立；B-15窄来源切片关闭，停止同类发行。E整体、组织/用户身份及生命周期不升级。

Metric baseline: measured：原消费者verify_agent_executor_identity接受credential_possession_fact，使用credential_ref和状态/五条件晋级；execute_with_payment_binding_gate允许BOUND或VERIFIED，现有测试明确两者采用相同支付策略。unknown：H78真实事实在跨主体/Provider/Executor消费时的上下文是否保持，没有系统测量结果。
Hypothesis: 一个真实VALID凭据事实不应因换成另一套自洽的消费者主体/Provider/Executor，就把不匹配上下文晋级为VERIFIED。
Principal measurement: 只将同一H78已签收公开证明按其原observed时刻复算，送入现有身份/支付消费者并观察六个固定输入；不改产品或实现策略。
Expected impact: 消除事实消费接缝的具体未知，发现反例才形成修复包，不把测量任务PASS当产品安全PASS。
Estimated affected scope: 一个共享身份消费者与支付门禁，范围未知、先测量；相比生命周期建设/第二平台，此接缝更靠前、成本更低。
Rollback/stop: 记录首个跨上下文错误VERIFIED或原revoked守护反例后停止余下探针，保全并统一提交；不修、不扩大矩阵、不执行真实支付。

## Single objective / 唯一目标

来源/历史保持→六槽固定观测（或首个反例后明确余项未执行）→输入/结果/计数/因果原因原文→公共L2→不变提交接受→独立离线L3→事实与策略边界分类。这里是measurement-only（只测量），不是能力建设或支付策略决策。

## Fixed probes / 固定探针与解释边界

SCENARIOS.json依次为M01同主体/Provider/Executor正对照；M02另一自洽Agent上下文；M03另一自洽Provider；M04另一自洽Executor；M05另一自洽credential_ref；M06原identity.status=revoked。事实对象始终由真实H78公开证书/签名经原验证器产生，不能手写VALID或修改事实的subject/状态。业务对象来自现有PaymentExecutionBindingTests.setUp，只调整冻结字段；原execute回调只向本地列表添加标记，不接任何支付服务。

只有“source_context不匹配却晋级VERIFIED”或“revoked原守护失效”触发反例停止。BOUND下允许callback是既有明确策略，不能单凭ALLOW/callback认定漏洞；本包不决定必须强制VERIFIED。M05若降为BOUND属于测量结果，不自动判风险。未执行探针必须标NOT_RUN_AFTER_COUNTEREXAMPLE，不补造全六项结果。

## Acceptance criteria / 验收标准

### AC-01 来源与范围保持

完整H78接受/L2/L3/签收/公开材料/清理及此前证据保持；HEAD、src、原tests、共享工具不变，旧治理字节用BASELINE别名保护。SOURCE.json固定H78唯一run目录及公开输入SHA；只读root/leaf/payload/signature/记录RESULT，私钥从未导出或读取。固定RUN/CHECK/SCENARIOS/PLAN与工具只读，不新增凭据、服务或源码修复。

### AC-02 原始事实与正对照

使用原credential_possession验证器，固定h76.test、Agent/Provider/Executor、nonce、issued/observed原记录及原签名，复算VALID/四true/非replay。明确CAPTURED_OBSERVATION_REPLAY_NOT_CURRENT_AUTHENTICATION，不假称凭据目前仍有效或新鲜。M01完整VERIFIED、binding/context均VALID且本地callback恰1，否则停止为输入/实验限制，不擅改产品。

### AC-03 六槽测量及首反例停止

输入严格对应SCENARIOS，逐项保留source_context、consumer_input、proof引用/主体、identity状态/assurance、decision、callback_count及两组reason codes；排除P2/P4无效造成的混淆。正常则观察六项；首反例出现后只保留已观测前缀，余槽明确未执行并停止。CHECK独立复算是否上下文匹配及反例分类，不把产品反例抹成预期安全，也不把测量通过当产品通过。原始结果可由Evaluator在同一固定输入独立复现。

### AC-04 有界证据与角色

公共计划四项全通过才SUBMITTED，原始EV三件套与RESULT/代码/来源封存；Evaluator接受后仅一次离线L3，逐AC二元判定，任务/影响/继续价值分开。WSL/服务/新凭据/网络/下载/安装/API/真实付款/Git0。已产生结果的同角色后续L2只可读取不变结果，不重新扩大探针或覆盖事实；源/矩阵漂移拒绝。真实源被测时的十负例/原16/130结论保留；本包不重发或重跑已关闭来源，用冻结源码/证据保护和直接消费者观测验证本接缝。

## Allowed scope / 允许范围

固定本包RUN/CHECK/BOOTSTRAP/SCENARIOS/SOURCE/BASELINE/FREEZE/CONTRACT/PLAN/PREPARE只读。Executor可新增REPORT/SUBMISSION、ATTEMPT_LEDGER及本包evidence/executor_*、l2或l2_retry_02、executor_measurement；不改产品、测试、门禁或被接受材料。Evaluator拥有ACCEPTED/evaluator_measurement/独立L3/REVIEW及地图更新。报告中必须区分观察值与解释/风险推断。

## Exclusions / 排除

不建设轮换/撤销/强制VERIFIED策略、不修发现的反例、不更换真实来源、不读取/生成私钥、不运行WSL/SPIRE/binary/网络/模型/外部API/安装/付款/提交推送。严禁将普通列表callback的“paid”标记称为实际付款；不外推组织/用户强认证或监管合规。

## Validation plan / 验证计划

VP-01保护AC-01；VP-02运行冻结矩阵对应AC-02/03；VP-03读取原始RESULT独立核输入/分类/停止计数，对应AC-03；VP-04最终保护AC-01/04。精确argv/cwd/退出码/独立Evaluator命令在VALIDATION_PLAN.yaml。没有外部授权或新鲜发行分支。

## Authorization / 授权

reference_read=true仅本地；existing_wsl/local_service/ephemeral_test_credentials/api/install/download/browser/payments/commit/push/history_rewrite=false。本包是工作流要求的后续只读测量制包，H78新物理运行许可不继承；角色与权限由RUN.authority在观测前核验。无缺少的Human事实/权限；不预设产品应禁用BOUND。

## Cost and bounded budget / 预算

Expected material cost: low，6个以内纯本地回调、一次原证明验签及文件摘要，付费/外部调用0。
Bounded retry / iteration budget: 最多2正式L2、1独立离线L3；无总体时长自设上限，主动分钟UNKNOWN如实记录。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 原证明正对照+至多六槽观测/首反例停止+可独立重放原文
Max total attempts: 2 L2, 1 L3, 0 issuer
Max parallelism: 1
Max attempts per unit: 每角色每探针最多1次；复用既有结果不算新探针，须输入摘要相同
Retryable failure families: 无语义变化的报告/引用/结构问题；产品反例、源漂移或新增范围不修后重测
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H79_VERIFIED_FACT_CONTEXT_CONSUMER_MEASUREMENT_V1/ATTEMPT_LEDGER.jsonl

## Stop conditions / 下一步

来源/固定输入/原源码/范围漂移或新权限需求停止交Evaluator。若错误VERIFIED被确认，保留明确反例后再冻结最小修复；若无反例且已闭合代表消费链，STOP同类扩例，再比较生命周期等备选。结果不能客观复核时不签收强制AC。当前只冻结后续包，未执行测量、不预报漏洞。

## External requirement impact / 外部指标

profile=PCAC-AGENTPAY；PCAC-03/05/06/09/12/20为身份/来源/执行前完整性与证据映射，CORE/ADAPTER/EVIDENCE_ONLY沿原基线；07–10原授权守护不改。对象/Contract=已验证凭据事实与当前身份上下文；代码=credential_possession、execution_facts.verify_agent_executor_identity、payment_execution.execute_with_payment_binding_gate；Test=冻结矩阵/固定源码保护；Evidence=原H78公开输入与新L2/L3观测。before/after产品M2不因测量升级，残余为可信管理员、历史重放非当前认证、未测真实生命周期/生产采用。
