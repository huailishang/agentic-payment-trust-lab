# H77R：独立测量入口的Windows路径调用方修复

Task ID: H77R_NATIVE_PATH_CALLER_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r130
Active bottleneck: B-15
Hypothesis: H-77R
Dispatch mode: SINGLE

## Strategic basis / 战略依据

目标为授权→可信主体→治理→支付→恢复→审计的可独立复核信任链。A–D本地阶段关闭、E受控本地代表闭合、F受控外部切片关闭。B-15实际来源仍待独立新鲜复验；生命周期未系统测量、第二支付平台不能补来源，均不抢占当前已定位断点。

Parent: H77_WSL_REAL_SOURCE_INDEPENDENT_CLOSURE_V1；AC-02/03/04/06/07失败。原L2六项通过，唯一L3六项中三项通过、三项失败。CHECK.live传str(relative_path)，Windows反斜杠被严格POSIX入口拒绝，发生在wsl.exe调度前；实际SPIRE启动0。1693接受输入未变，原130回归通过。原失败/账本/门禁不回写。

唯一主要变化：**新包调用方把--out参数改为out.relative_to(ROOT).as_posix()**。保留RUN的严格路径拒绝、所有角色/接受/次数/清理边界，且保留原实际来源测量范围。不是让Executor修改原H77或放宽路径白名单。

修复由Evaluator在新复制冻结CHECK中明确落地，差异检查必须证明只有该一处调用方变化。RUN/WORKLOAD/TASK_TESTS/AUDIT/BOOTSTRAP与H77接受版本字节相同，以新目录独立执行；原文件只读。本包任务类型repair，代码修复不声明新产品能力；若新鲜测量成立，只据独立证据更新B-15窄切片，不宣称E整体完成。

Metric baseline: measured：原H77正式L3=1、WSL调度=0、SPIRE运行=0；同一目录用.as_posix()可通过原入口只读保护。unknown：新鲜实际发行可重现性。
Expected project impact: 修复确定的测量前置断点并完成原目标独立复验；不改产品能力。
Estimated affected scope: 单个Windows调用方参数，原同一SPIRE1.16.0/Ubuntu/UID/直接EC根。
Rollback condition: 任一摘要漂移、安全反例、放宽路径保护或需要改源脚本/权限即停止。

## Single objective / 唯一目标

一个包完成：冻结差异与历史保持→真实调用表达式到严格入口的离线联调→正式离线L2→统一提交→Evaluator接受不变快照→唯一一次新根/nonce实际WSL重演→十负例/原130回归/独立清理→逐AC验收。执行者实际发行0，不逐步骤Human确认。

## Acceptance criteria / 验收标准（全部强制）

### AC-01 历史与修复边界

保护原H77全部提交/接受/L2/L3/拒收和旧H76/H75记录；旧地图/路由原字节别名保存。原src/tests/共享工具不变。COPY_MANIFEST证明AUDIT/RUN/WORKLOAD/TASK_TESTS/BOOTSTRAP与H77一致，CHECK只有该一处.as_posix()差异；新BASELINE/FREEZE保持。Executor真实发行0。

### AC-02 调用接口与新鲜来源

SEAM_CHECK从新CHECK.live AST（语法树）取得实际subprocess argv表达式，在专属离线目录计算原参数并调用原严格RUN.output_path，正例通过；原native反斜杠输入及逃逸/绝对路径等反例仍拒绝。无WSL/发行预演。随后L3必须是真实新根、新nonce、同锁定archive成员与执行二进制摘要绑定、管理根先于Agent启动；真实观测时间在Evaluator测得窗内，与H76旧根/nonce不同。失败不重试。

### AC-03 管理登记、内核身份与持有

继承H77原AC-03与原RUNTIME_PROTOCOL全部测量标准：本轮管理Agent列表/entry原始脱敏JSON逐字段关联真实父ID、唯一UID1001和目标；三操作进程内核PID/UID/EUID可回查；UID1001唯一SVID并同UID私钥签名，UID1002同接口真实PermissionDenied且0身份；私有目录0700、密钥0600/owner1001。管理员仍受信，不声称组织或硬件证明。

### AC-04 原消费者与十负例

原验证器本次真实材料VALID/四true，独立复算EC直接根/叶/URI/签名；原十负例0 VALID且原因不变。模拟过期不等于真实撤销；身份不覆盖无效/撤销授权，金额/用户意愿未新增测量。付款/API副作用0。

### AC-05 原130回归

原28+19+9+74项全部断言通过；不改/跳过原tests或产品。新离线联调不是新增产品用例，原15项任务保护不删除。

### AC-06 清理、次数与成本

继承H77原AC-06的所有权/PID启动标识/专属tmpfs路径保护、失败也记账、独立资源与私钥检查；本包Executor发行0，Evaluator最多1实际运行/1正式L3，失败也消费，不能以新ID续期。旧H77正式L3=1/实际0分别保留；旧H76三轮偏差和费用不追认。记录实际/估计/UNKNOWN，无总体工作时间上限；防挂单命令180秒、单发行≤20分钟及无条件清理。

### AC-07 统一提交与独立复核

固定六VP全部强制；L2在历史源复算基础上增加真实调用表达式联调。统一REPORT/SUBMISSION及EV原始三件套后才能提交。Evaluator封存完整ACCEPTED（含l2_gate_path），READY_FOR_REVIEW后唯一L3；前后提交字节不变，管理/内核/清理原始证据人工回查，逐AC二元结论。原H77拒收不被新包通过追改。

## Allowed scope / 允许范围

Executor只新增REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl、evidence/executor_*、evidence/l2或l2_retry_02以及任务runtime。复制实现、CHECK/AUDIT/BOOTSTRAP/SEAM_CHECK、合同、计划、基线、冻结、来源清单与references均只读。Executor不需要实现新功能，也不得修运行脚本后自行再试。

Evaluator拥有接受快照、evaluator_runs/l3/REVIEW及最终治理。CURRENT仅本任务动作/状态，地图/REMOTE仅Evaluator按证据更新。任何源脚本新缺陷都停止并另议，不顺手扩成第二个主要变化。

## Exclusions / 明确排除

原H77/H76文件、产品src、原tests和共享workflow只读。无新依赖/下载、安装/WSL配置/系统服务修改、Docker/其它发行版、钱包/链、外部API/付款、提交/推送、产品验证器放宽、轮换/撤销/第二支付平台。不能用合成正例或旧证书冒充新运行。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/VALIDATION_PLAN.yaml

VP-01保持AC-01；VP-02在Executor使用SEAM_CHECK完成实际argv表达式联调+历史复算，Evaluator用CHECK live完成AC-02/03；VP-03原验证器/十负例对应AC-04；VP-04原130对应AC-05；VP-05零发行/本轮清理对应AC-06；VP-06最终保持及人工独立程序对应AC-01/07。命令、工作目录及期望退出均冻结于YAML，不改公共Runner。

技术来源及输出字段完整继承原H77/RUNTIME_PROTOCOL.md与REVIEW_PROCEDURE.md，原字节由BASELINE保护；将“本任务/H77”实例化为本H77R目录，但不改变测量/权限/停止语义。新RUN/WORKLOAD使用自身目录，公共挑战仍为h76.test及原Agent/Provider/Executor。所有新产物写本包，不向旧包落盘。

## Authorization / 授权

负责人原H76/OWNER_WSL_AUTHORIZATION_20261116.md允许同一Ubuntu实际来源/签名实验并交Evaluator仔细评估；本轮要求评估触发已冻结的独立审查。原H77实际WSL/SPIRE运行0，本包只为该未执行的目的准备一次独立运行，不授予Executor新发行次数，不扩平台/权限。

existing_wsl/local_service/ephemeral_test_credentials=true，仅Evaluator接受后单次；artifact_download/install/dependency_install/api_call/browser/payments/commit/push/history_rewrite=false。新机制/后续运行无自动续权。

## Cost and budget / 成本与预算

Expected material cost: low，1个调用参数修复、离线接口检查及原目标一次本地重演；0下载/付费服务/API/付款。
Bounded retry / iteration budget: 已冻结实现1版；最多2离线L2（仅任务提交/环境导入类问题可在预算内修复，产品断言失败停止）；1正式L3/1实际发行，Executor实际0。成功充分就停止。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 离线接口恢复+原来源目标全部独立AC
Max total attempts: 2 offline L2, 1 L3, 1 live issuer
Max parallelism: 1
Max attempts per unit: 3 matching fetches, 1 nonmatching, 1 signature within the single live run
Retryable failure families: 原单运行启动同步；不得重启发行或删除一次性标记。
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H77R_NATIVE_PATH_CALLER_REPAIR_V1/ATTEMPT_LEDGER.jsonl

## Stop conditions / 停止条件与后续分支

范围/摘要/授权漂移、SEAM不通过、需要改冻结源脚本、固定archive/依赖/sudo不可用、零容忍反例、原产品断言失败或预算耗尽均停止并保全。缺环境不能说明SPIRE机制失败。唯一L3失败后禁止当场修复重跑，所有分支先清理本次资源。

全部AC通过→修复任务PASS、影响NOT_APPLICABLE（修复本身不宣称产品改善），另据本次实际证据判断来源代表切片是否闭合并STOP同类加例。失败→REJECTED，按新具体断点重排，不自动扩功能。后续生命周期/用户真实性/真实消费者只有新测量或授权条件具备才进入下一包。

## External requirement impact / 外部指标

profile=PCAC-AGENTPAY；PCAC-03/05（CORE）、06（CORE/ADAPTER）、12/15/20（CORE）与原来源/证据测量关联；PCAC-07/08/09/10保持授权守护。before=既有产品M2、独立实际来源UNKNOWN；修路径本身after不变，只有未来实际来源AC全部通过才单列窄切片M3，不升级整项。

对象/Contract=根/登记/UID/叶/挑战/不可变提交；代码=原credential_possession/identity_assurance；Test=VP-02/03/04；Evidence=路径联调、完整L2与新鲜L3/清理。残余为受信任管理员、UID非组织身份、无用户强认证/硬件持有/长期轮换/真实撤销/生产采用及监管合规结论。
