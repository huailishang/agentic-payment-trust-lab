# H77：WSL真实发行来源的独立证据闭合

Task ID: H77_WSL_REAL_SOURCE_INDEPENDENT_CLOSURE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Experiment mode: measurement-only
Risk: L2
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r129
Active bottleneck: B-15
Hypothesis: H-77
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE

## Strategic basis / 战略依据

最终目标是在可重置边界中证明授权→可信主体→交易绑定→执行前治理→支付→恢复→可消费审计。A–D本地关闭；E只有受控本地代表闭合；F受控外部切片关闭。真正用户强认证、组织身份、长期凭据治理和生产采用均未闭合。

Metric baseline: measured：Evaluator只读复算H76的20个公共文件摘要、真实根/叶/签名及十负例通过，1502受保护文件未漂移，原28+19+9+74=130项回归复跑成功；历史WSL有3轮发行、1个成功切片。unknown：新鲜来源/持有者事实的独立重现。原Docker正式L2/L3=0，当前旧路由结构校验exit=1，H76未获正式签收。详见evidence/preparation/ASSESSMENT.json；离线复算不是新鲜认证。

单一假设：在负责人已授权的同一WSL Ubuntu、同一锁定SPIRE 1.16.0、相同UID和直接EC根约束内，评估者能用**独立新根和新nonce（一次性挑战值）**重现实际发行→UID选择器→同UID签名→原消费者判定，而不依赖历史脚本自报成功或旧私钥。

单主要变化：将已有WSL实际来源切片纳入事前冻结、原始证据可回查的独立测量。补齐的二进制摘要、管理响应和内核观测是该测量的必要证据，不是产品能力或第二个假设。产品实现、交易挑战格式、十负例及原回归保持。

Estimated affected scope: 同一trust domain（测试信任域）、目标Agent/Provider/Executor、UID1001正例和UID1002接口拒绝对照。只新增一次Evaluator真实运行；Executor真实运行预算为0。

Expected project impact: 若独立重演成立，B-15的“受控实际发行源可被原验证器消费”切片获得独立证据；否则定位具体证据/兼容断点。不会使E整体关闭，不会证明组织/KYC身份、用户付款意愿、金额签署、硬件持有或生产可信执行。

Rollback condition: 任一错误身份放行、负例VALID、私钥越界或原产品断言失败立即停止；保留所有证据，服务清理优先，不修src/tests、不放宽验证器。

Expected material cost: estimated，中等测量脚本整理、一次低资源本地SPIRE重演及两角色回归；0新下载、0付费服务、0付款、0外部模型/API。实际主动分钟与完整网络字节不可观测时保留UNKNOWN。负责人既有“不用自设时间”保持，不设置任务总主动时间或墙钟上限。

Bounded retry / iteration budget: 最多2版任务脚本、2次离线正式L2、1次正式L3；Executor/预演真实发行0次，Evaluator真实Server/Agent启动1套且失败也消费次数，禁止以新ID续跑。L1离线修复限于合同内；不能本地生成正例证书验证发行机制。达到证据充分目标即停止。

Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 原1个实际切片离线L2 + 1个独立新根/nonce实际切片L3；各10个原消费负例及必要回归
Max total attempts: 1 new live issuer run, 2 offline L2, 1 L3
Max parallelism: 1
Max attempts per unit: 3 matching fetches; 1 nonmatching fetch; 1 holder signature per live run
Retryable failure families: 同一运行内启动同步/管理接口暂未就绪；仅匹配取证可在3次内重试。摘要/权限/选择器/证据/产品安全失败不可重试。
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H77_WSL_REAL_SOURCE_INDEPENDENT_CLOSURE_V1/ATTEMPT_LEDGER.jsonl
Expected value of another round if successful: 停止同类发行/合成证书扩展；仅重新比较尚未测得的凭据生命周期或真实消费者边界，不预先授权下一能力包。

## Single objective / 唯一目标

一个包完成：历史保全/偏差对账→任务测量脚本整理→离线L2→统一提交→Evaluator接受不变快照→唯一一次独立WSL新鲜发行→同次十负例/原回归/清理→逐AC验收和地图重排。中间不逐步骤交Human；不把历史H76失败或第三次尝试追认为合规成功。

## Dependencies and branches / 步骤依赖与分支

1. 先读本合同、BASELINE、FREEZE、INPUT/历史审查及H76负责人授权。SHA漂移、安全反例或需要新权限即停止。H76全部原103文件及新增REVIEW只读。
2. Executor只整理RUN.py/WORKLOAD.py和本任务离线检查，实现RUNTIME_PROTOCOL.md；不可启动SPIRE，也不运行旧WSL_LIVE.py。新脚本输出必须在本任务目录；旧WSL_VERIFY.py会重写旧产物，禁止调用它。
3. 运行BOOTSTRAP.py的executor模式。计划事先冻结为**非对称测量**：L2只核既有真实样本与实现可审阅性；L3的对应evaluator_command才真正新鲜发行。因此L2不声称新鲜来源已复验，未变更原L2/L3公共Runner。
4. 全部L2强制项通过后提交REPORT、SUBMISSION摘要及完整原始证据。Evaluator先审实现/白名单/次数/授权，记录evidence/ACCEPTED.json（files为repo相对路径→SHA-256），覆盖合同、计划、基线、冻结工具、RUN/WORKLOAD、报告、L2及全部提交引用；接受后提交输入不可更改。
5. Evaluator将CURRENT置READY_FOR_REVIEW，再一次BOOTSTRAP evaluator。仅用既有Ubuntu；允许为本次已授权实验启动该发行版一次，不启动docker-desktop/其它发行版。若sudo -n、既有Python依赖、固定archive或管理接口证据不可用，INPUT_LIMIT并停止，不安装/改配置/下载。
6. 只有新鲜重演、来源人工回查、10负例和必要回归全部成立才签收窄切片。失败即统一交回，不在L3后修脚本再跑；所有分支清理临时私钥及本包拥有进程。

## Acceptance criteria / 验收标准（全部强制）

### AC-01 历史、范围与权限保真

原1502输入、H76冻结文件与103份提交文件保持；治理文件原字节通过references/before_h77保留。历史3轮与“首次＋一次修复”的补充文档偏差、Docker失败、旧费用/UNKNOWN逐项列明；不把该次数上限伪称负责人原话。当前授权与实现一致；Executor新发行0次。

### AC-02 官方执行来源与独立新鲜性

L2离线验证旧实际样本。L3从已锁定archive重新安全提取所需二进制，逐一比较archive成员与实际执行文件SHA、版本；不信任历史解压缓存。Evaluator生成run_id/nonce，真实SPIRE生成新根；根与nonce均不同于H76，issued_at处于Evaluator测得运行窗，观察时间与采集后真实时间相容；管理根在Agent启动前获取。不得导入旧根/叶/签名充当本轮，不能用证书自带bundle作为权威来源。

### AC-03 实际管理登记、UID与持有边界

来自本轮Server管理接口的Agent列表及entry详情可逐项解析、关联父身份及唯一unix:uid:1001选择器；保留明确脱敏投影，不能只存CLI成功布尔量或回退到日志猜父身份。UID1001恰好取得1个目标SVID并在同UID用私钥签名；UID1002同socket实际PermissionDenied且0身份。记录三个真实操作进程的/proc/PID/status原始UID/EUID、PID、命令及同socket引用，不能仅硬编码1001或print自报。私有目录0700、叶私钥0600、owner=1001；root/宿主管理员仍受信，不声称可抵御管理员。

### AC-04 原验证器、十负例与授权守护

原验证器返回VALID及四true；独立检查单EC根直接签叶、叶非CA/KeyUsage/唯一SPIFFE URI、规范挑战与签名。固定十负例各非VALID且原因匹配原NEGATIVE_ORACLES，不增加或删除用例。过时/过期明确模拟观察时间；不得把该历史复算称当前认证。真实支付/API回调0。凭据真实性不得覆盖无效/撤销的既有授权基础。

### AC-05 原回归和产品不变

原credential_possession/identity_assurance/上下文28项、Stripe19、安全9、业务74共130项及原全部断言通过；不跳过、不改继承、不改src或原tests。首次基线回归已在准备期通过；正式L2/L3仍各保留原始回归输出。

### AC-06 清理、成本与尝试账本

唯一新鲜运行启动前追加事件，成功/失败/超时/清理结果均追加；失败不能删除标记或更换ID续跑。只回收自身PID/创建时标识匹配的进程及经realpath/owner校验的专属tmpfs路径，无通配进程kill或系统配置操作。单命令≤180秒、整次发行≤20分钟仅作防挂回收；清理不受上限阻断。独立命令检查残余进程0、私有tmpfs不存在、公开私钥0。所有原始耗费/UNKNOWN与旧3轮成本累计分列，不将新预算回溯覆盖旧超限。现有公开archive保留，无新网络下载。

### AC-07 统一L2、不可变接受及独立L3

公共Runner六项全部通过才能SUBMITTED_FOR_REVIEW；L2明确只复算历史。接受输入在L3前后逐SHA保持；Evaluator亲自启动新运行、检查真实命令/管理响应/内核记录和独立清理，不能仅通过SOURCE.json自报布尔量签收。逐AC二元判断，任务/影响/继续价值分别出结论。结构通过不等于能力通过；H76原Docker强制项不转成已满足。

## Allowed scope / 允许范围

Executor可新增/修复本任务RUN.py、WORKLOAD.py、TASK_TESTS.py、REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl、evidence/executor_*、evidence/l2或l2_retry_02、runtime。只能调整任务脚本的采集、同步、脱敏、路径与清理，不修改冻结验收器。

Evaluator拥有evidence/ACCEPTED.json、evaluator_runs、l3、接受后审查记录、REVIEW及治理最终更新。CONTRACT、VALIDATION_PLAN、CHECK、AUDIT、BOOTSTRAP、RUNTIME_PROTOCOL、REVIEW_PROCEDURE、BASELINE、FREEZE、references与preparation均只读。CURRENT仅本任务状态/动作路由可变；地图/REMOTE由Evaluator处理。

## Exclusions / 明确排除

产品src/、原tests/、公共workflow工具与旧任务内容只读；不得修原验证器、增加链构建/RSA/轮换/撤销模块，或接入新平台、钱包/链、第二支付服务方。无真实用户/机构/KYC验证、金额签署/付款、外部网络服务、安装/升级包、Docker操作、共享环境/PATH/WSL配置修改、系统服务重启。不得用新合成证书替换实际正例。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H77_WSL_REAL_SOURCE_INDEPENDENT_CLOSURE_V1/VALIDATION_PLAN.yaml

| VP | L2 / L3观察 | AC |
| --- | --- | --- |
| VP-01 | 原输入与冻结保持 | AC-01 |
| VP-02 | 旧真实样本离线复算 / 唯一新鲜发行及来源检查 | AC-02, AC-03 |
| VP-03 | 证书/签名及十负例独立复算 | AC-04 |
| VP-04 | 原130项回归 | AC-05 |
| VP-05 | Executor零发行 / L3资源清理与接受快照保持 | AC-06 |
| VP-06 | 最终历史/冻结保持，结合人工审阅 | AC-01, AC-07 |

BOOTSTRAP.py用当前解释器启动同级公共Runner，固定argv见计划；使用已验证的agent Python环境。准备期检查只代表制包自检，不伪装L2/L3。新RUN.py为已明确合同内实现义务，非未决产品选择。

## Authorization / 授权依据

继承H76/OWNER_WSL_AUTHORIZATION_20261116.md中负责人对同一WSL实际来源/签名实验及“交评估者仔细评估”的授权，并结合本轮负责人要求Evaluator审查现状、制定下一包。这里只安排原目标必需的**一次独立评估运行**，不授予Executor新的发行重试。旧补充次数偏差不追认；后续其它机制实验不继承这一次预算。

- existing_wsl / local_service / ephemeral_test_credentials: true，仅本次Evaluator独立重演
- reference_read: true，仅本地现有资料
- artifact_download / dependency_install / host_install / api_call / browser / payments / commit / push / history_rewrite: false

## Stop conditions / 停止条件

基线/摘要漂移、L2或提交不合格则不启动L3；历史只缺不可能补造的原始数据时列明UNKNOWN而不补写。固定archive/现有权限/现有依赖不可用→INPUT_LIMIT，不换来源或安装。真实运行首次失败/预算耗尽/发生零容忍反例/需要改假设、范围、AC、验证器或权限→立即停止并保全。普通离线脚本修复在既定两版/两次L2内继续，不逐步请求确认。到达成功充分条件后停止同类加Case。

## Decision branches / 结果分支

全部AC通过→PASS / IMPROVED，仅关闭实际来源代表切片并STOP同类发行；重排B-15余下的生命周期、用户真实性和真实消费者缺口。发现稳定产品兼容断点→REJECTED / INCONCLUSIVE或REGRESSED，据证据冻结最小修复。仅缺环境/权限/独立原始证据→不声明机制失败或改善，保留INCONCLUSIVE并停止。不得自动启动轮换/撤销/新支付接入。

## External requirement impact / 外部要求影响

profile=PCAC-AGENTPAY。PCAC-03/05（CORE，主体凭据和引用）、PCAC-06（CORE/ADAPTER，受控实际来源）、PCAC-12/15/20（CORE，证据/最小化/独立评估）适用。before：既有产品实现M2，H76实际切片只有执行者测量、独立证据UNKNOWN；target after：仅本受控切片独立实测M3，不提升整项成熟度。PCAC-07/08/09/10只作为原授权/撤销守护，成熟度不变。

对象/Contract=根、登记、UID、叶、挑战/nonce及不可变提交；代码=原credential_possession/identity_assurance；Test=VP-02/03/04；Evidence=L2历史复算+L3新鲜来源/拒绝/签名/清理原始记录。残余：受信任管理员和人为根引导、UID不等于应用/组织身份、无硬件/用户强认证、无长期轮换/真实撤销/生产采用。不得据此作监管合规结论。
