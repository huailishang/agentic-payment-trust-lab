# H77R3：实际登记创建响应的离线解析修复

Task ID: H77R3_ENTRY_CREATE_RESPONSE_OFFLINE_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-17-r132
Active bottleneck: B-15
Hypothesis: H-77R3
Dispatch mode: SINGLE

## Strategic basis / 战略依据

最终目标为授权→可信主体→交易治理→支付→恢复→审计。A–D本地阶段关闭，E受控本地代表闭合，F受控外部切片关闭且后续接入仍受授权约束。B-15完整实际来源仍未独立复验。H77R2真实资产资格已通过，唯一正式L3实际启动Server与Agent，先导出新管理根；实际entry create退出0且唯一批结果status.code=0，但旧one_entry只支持entries/entry/直接对象，不能解析results[0].entry。原130回归、1939接受保持和独立清理通过。历史拒收、次数及UNKNOWN费用均不回写。

Metric baseline: measured：本包固定两份H77R2实际脱敏CLI响应可离线重放；旧解析器对外层创建响应报entry object schema，内层父ID/目标/唯一UID1001校验通过。unknown：entry show及完整UID/持有/消费的独立新鲜闭环。
唯一主要变化：只在本包副本WORKLOAD.one_entry支持实际唯一成功批结果封装，并对错误状态、缺失/多项/歧义封装拒绝；不改变信任含义或发行机制。
Estimated affected scope: 一个纯解析函数；无产品行为改变。
Expected project impact: 修复已知测量断点，避免再消费发行机会验证同一已知错误；修复本身不提升产品成熟度或闭合B-15。
Rollback condition: 旧字节漂移、范围越界、非法/歧义响应通过、原断言失败、新权限需求即停止。
Expected material cost: low，标准库离线解析、现有Python及原130回归；无网络/新依赖/服务/凭据/付款。

## Single objective / 唯一目标

保全H77R2→修复唯一纯函数→用实际脱敏响应贯穿one_entry→entry_identity→validate_entry及拒绝矩阵→原16保护/130回归→完整L2统一提交→接受不变快照→独立离线L3逐AC验收。全部限Windows本地离线；本包没有资产预检、binary执行、WSL或新发行分支。

## Dependencies and branches / 步骤与分支

1. 读SOURCE_LOCK、BASELINE/FREEZE、父REVIEW/MANUAL_FACTS与两份fixtures。先运行CHECK baseline，只确认旧实际失败可重复，不把它当修复成功。
2. 只改新WORKLOAD.one_entry；原WORKLOAD其余AST（语法树）、TASK_TESTS及产品/共享工具不变。使用明确字段解析，不能递归搜任意id或忽略业务错误状态。
3. 对results封装要求：results为恰好一项列表；该项为对象，status为对象且code为真正int 0（bool/浮点/字符串不算）；entry为对象。拒绝空/多项、缺字段、非0/错误类型状态以及results与entry/entries/直接id形态并存。既有entry/entries/直接对象合法输入保持；它们与results共存不能靠优先级挑一个。
4. 冻结CHECK protocol使用实际响应与原父列表，核完整三函数串联；负向覆盖外层状态/形状及内层父ID/目标/UID/登记ID。不能改冻结checker或将其测试fixture当真实性新证据。
5. 在2实现版本/2正式L2内可做合同内普通修复；首次零容忍反例/原断言失败、范围或预算变化即停止。成功统一REPORT/SUBMISSION，不逐步骤请Human确认。
6. Evaluator接受快照后仅1次离线正式L3；失败不修后重跑。PASS只表示响应兼容修复，实际来源仍未闭合，后续运行必须另行冻结范围与权限，不能自动续给H77R2已消费的发行机会。

## Acceptance criteria / 验收标准

### AC-01 历史与范围保持

H77R2所有提交/接受/L2/L3/失败原文/清理/REVIEW及此前任务全部保持；旧治理字节以明确别名保护。HEAD、产品src、原tests、共享工具不变。WORKLOAD除one_entry外AST逐字一致；原16任务保护完整且TASK_TESTS字节不变。仅允许修改本包one_entry、REPORT/SUBMISSION/账本及执行证据。

### AC-02 实际成功封装及旧合法路径

固定实际results[0].entry响应贯穿one_entry、entry_identity、validate_entry，得到原确切登记ID/目标/父/唯一UID1001，输入对象不被修改。原entry、entries和直接对象三合法形态仍通过。证据声明严格限脱敏历史材料离线兼容，不冒称新发行或实际用户身份。

### AC-03 拒绝与信任边界

冻结矩阵中非0/缺失/非int0状态、无/多结果、缺失或错误类型entry、歧义包装全部拒绝；原内层错父、错目标、错UID、重复/缺失选择器、错登记ID仍拒绝。禁止日志回退、任意字符串猜ID、异常吞掉、强行返回固定fixture或修改unittest断言体系。

### AC-04 原保护与回归

原16任务测试及原28+19+9+74=130原断言全部通过；无跳过/删减、产品/tests/原CHECK修改。冻结协议检查输出原始日志及可复核计数，不只报告预期数。

### AC-05 离线预算与独立提交

最多2实现版本/2离线正式L2/1离线正式L3，失败也入账；所有服务/发行/凭据生成/WSL/网络/下载/安装/API/付款/Git操作0。L2五项全通过才能SUBMITTED。SUBMISSION封存本包非runtime实现/报告/全部L2原始证据/固定材料，Evaluator另封SUBMISSION本身并独立L3；逐AC二元判断，任务/影响/继续价值分开。原H77R2唯一L3与实际服务阶段不改变。

## Allowed scope / 允许范围

Executor仅修改本包WORKLOAD.py的one_entry函数，可新增REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl、evidence/executor_*、evidence/l2或l2_retry_02及本包runtime。其余本包CHECK/BOOTSTRAP/PREPARE/TASK_TESTS/CONTRACT/PLAN/fixtures/SOURCE_LOCK/BINARY_MEMBER_LOCK/BASELINE/FREEZE/references均冻结只读。
Evaluator拥有接受/L3/REVIEW及治理材料；不得修改产品实现。没有新平台、算法、证书链、生命周期、选择器、挑战或清理机制建设。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H77R3_ENTRY_CREATE_RESPONSE_OFFLINE_REPAIR_V1/VALIDATION_PLAN.yaml

VP-01保持与AST对应AC-01；VP-02实际响应/拒绝矩阵对应AC-02/03；VP-03原16任务保护和VP-04原130对应AC-04；VP-05最终保持对应AC-01/05。真实发行/资产预检不在计划内。Evaluator还必须人工核原始fixture来源、三函数调用、无外部副作用、账本与接受保持；不能将公共Runner的PASS直接当终态。

## Exclusions / 明确排除

不修改产品src、原tests、共享workflow、父任务或本包one_entry以外的WORKLOAD函数；不改变资产/发行/UID/挑战/验证器/清理机制，不运行WSL、SPIRE binary、资产预检、服务或凭据生成；无网络/下载/安装/API/付款/提交/推送。本包不证明新鲜来源、用户强认证、轮换或真实撤销，也不自动续给发行机会。以上均为本合同既有范围/权限的显式汇总，不新增验收或实现义务。

## Authorization / 授权

commit/push/history_rewrite/api_call/install/artifact_download/browser/test_payments/local_service/existing_wsl/ephemeral_test_credentials=false。reference_read=true仅限已有本地材料；本地离线Python解析/测试获本任务授权。未调用外部机制研究；实际有来源原文与确定checker，普通修复无需新研究。

## Cost and bounded budget / 成本与预算

Bounded retry / iteration budget: 2实现版本、2正式L2、1Evaluator离线L3；无总体时长自设上限，实际主动时间未知时保留UNKNOWN。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 固定实际响应和旧合法形态通过、全部冻结拒绝、原16及130通过、快照不变
Max total attempts: 2 L2, 1 offline L3, 0 issuer
Max parallelism: 1
Max attempts per unit: 2 implementation versions
Retryable failure families: 预算内同函数普通离线修复；外部执行/新权限/原断言失败不可继续
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H77R3_ENTRY_CREATE_RESPONSE_OFFLINE_REPAIR_V1/ATTEMPT_LEDGER.jsonl

## Stop conditions / 停止与下一步

历史或冻结漂移、越界、原断言失败、零容忍拒绝反例通过、缺依赖、需要WSL/服务/新发行或预算耗尽均停止保全交Evaluator。PASS→STOP同类解析扩展，再评估原来源独立重演的完整合同与权限；失败→按具体断点修复或SWITCH，不重写父失败、不自动新发行。真实主体/凭据生命周期仍先测量，不因纯解析成功就建设能力或宣称E整体关闭。

## External requirement impact / 外部要求

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-03/05/06/12/15/20关联来源测量和证据完整性；适用CORE/ADAPTER/EVIDENCE_ONLY按原映射。before/after既有产品M2不变、完整实际来源UNKNOWN不变；本包只提升任务采集兼容性。对象/Contract=固定登记响应/父列表及one_entry；代码=任务WORKLOAD纯函数；Test=VP-02/03/04；Evidence=实际fixtures、原始L2/L3及接受快照。残余：可信管理员、UID非组织/用户强认证，无完整新鲜SVID/轮换/真实撤销/生产采用证据，不作合规结论。
