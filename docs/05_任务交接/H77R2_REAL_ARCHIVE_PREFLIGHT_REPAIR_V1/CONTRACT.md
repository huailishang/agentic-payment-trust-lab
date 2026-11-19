# H77R2：真实锁定归档的成员边界与发行前预检

Task ID: H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L2
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-17-r131
Active bottleneck: B-15
Hypothesis: H-77R2
Dispatch mode: SINGLE

## Strategic basis / 战略依据

最终目标为授权→可信主体→治理→支付→恢复→审计的可复核链。A–D本地阶段关闭、E受控本地代表闭合、F受控外部切片关闭。B-15独立来源未闭合；H77路径错误已由H77R修复，但唯一L3进入WSL后提取器150 MiB任意单文件阈值误拒官方Server，实际SPIRE服务0。原130回归通过、1812接受零漂移、独立清理通过。H77R最终REJECTED/NOT_APPLICABLE/CONTINUE，原门禁与次数不重写。

Metric baseline: measured：原archive SHA/长度匹配；完整11成员已只读核对，Server179,378,008字节、Agent78,437,656字节，均为唯一普通文件，合计257,815,664字节；原上限157,286,400字节。对应成员SHA已取得。unknown：实际发行/UID/持有链独立可重现性。

唯一主要变化：把提取器的任意单文件上限换成**由同一已锁定官方归档导出的精确成员profile（路径、长度、SHA）**，并强制用同一生产提取器先对真实archive做无服务预检。不是简单抬高上限，也不是更换SPIRE版本、放宽安全保护或增加身份能力。

Estimated affected scope: 两个固定成员及一个提取函数/唯一生产调用点；不改Server/Agent配置、UID、挑战、验证器、十负例或清理机制。
Expected project impact: 修复可独立判定的资产资格断点，先验证固定输入再测原来源目标；修复本身不声明产品改善。
Rollback condition: 任一摘要/范围漂移、链接/逃逸/重复通过、错误身份放行、私钥越界、原产品断言失败或新权限要求即停止。

## Single objective / 唯一目标

一个包完成：来源保全→精确成员边界修复→原15任务保护及成员攻击自检→真实固定资产预检→完整离线L2→统一提交→Evaluator接受不变快照→独立资产预检通过后唯一新根/nonce实际重演→原十负例/130回归/独立清理→逐AC验收。关键资产资格失败时不启动发行，不逐步骤Human复核。

## Dependencies and branches / 步骤依赖与分支

1. 先核BASELINE/FREEZE、BINARY_MEMBER_LOCK及H77R REVIEW/ARCHIVE_CATALOG/POSTCHECK。原H77R正式L3=1、发行尝试预算=1、SPIRE服务=0分别保留。
2. Executor只修本包WORKLOAD.extract_binaries及Collector.collect唯一extract_binaries调用，函数签名固定为(archive, destination, member_profile)，生产调用固定传read(self.task / "BINARY_MEMBER_LOCK.json")。按精确路径/唯一普通文件/长度/SHA逐流核对；任何漂移都拒绝，不接受范围型或浮动版本。
3. 原TASK_TESTS的15项名称/保护不删，仅归档fixture及对应两项归档测试可适配显式测试profile，避免将几十字节模拟输入冒充真实生产profile。可新增本修复必要负例：精确长度偏差、成员SHA偏差；路径逃逸/链接/重复仍拒绝。不得生成合成证书正例。
4. 实现ASSET_PREFLIGHT.py。它只在已有Ubuntu读取锁定archive，用同一个WORKLOAD.extract_binaries和冻结生产member_profile提取到自己创建的非敏感tmpfs，核SHA/长度后无条件清理；不执行任何提取出的二进制，不启动服务、sudo、取证或签名。禁网络、安装、subprocess/os.exec。采用120秒内部防挂并留足清理，外层180秒技术超时。总任务时间不设限。
5. QUALIFY.py为Evaluator冻结入口：先核实现范围/路径接口，再在L2内运行真实资产预检。预检失败立即停止该分支，不启动发行；只允许合同内修复并在最多2版/2L2内重试。不得调用旧WSL_LIVE/WSL_VERIFY，不向旧包写产物。
6. 全部L2强制项通过后统一提交。Evaluator审实现和全部原始预检输出，记录ACCEPTED.json（含files和l2_gate_path），置READY_FOR_REVIEW后正式L3；同一冻结QUALIFY先独立资产预检，通过才调用原CHECK.live的一次发行。任何首次实际运行失败均保全/清理并停止，不修后再跑。

## Acceptance criteria / 验收标准（全部强制）

### AC-01 历史、范围与固定资产

原H77R提交/接受/L2/L3/拒收/清理/只读目录及H77/H76/H75全部保持；治理旧字节以别名保护。固定archive及BINARY_MEMBER_LOCK完整SHA不变；新CHECK/BOOTSTRAP/AUDIT/RUN/SEAM与H77R逐字节一致。WORKLOAD除提取函数和唯一传profile调用以外AST（语法树）不变；原产品/tests/共享工具不改。Executor发行0。

### AC-02 真实资产资格与新鲜来源

真实archive=70,187,551字节及原SHA；仅目标两个成员可提取，精确大小/成员SHA/提取后SHA匹配BINARY_MEMBER_LOCK。生产提取器预检必须实际通过，不以tiny fixture代替；预检无binary执行、服务、下载、凭据并清理。原Windows调用表达式联调/非法路径保护保持。只有独立预检通过后才允许L3实际发行；本轮新根/nonce/真实观察窗、管理根先于Agent启动、实际执行二进制与archive成员绑定均按原H77标准满足。

### AC-03 真实登记、UID与持有

完整继承H77/RUNTIME_PROTOCOL与REVIEW_PROCEDURE：管理Agent列表及entry脱敏原件逐字段关联真实父ID/唯一UID1001/目标；三操作进程内核PID/UID/EUID/命令可回查；UID1001唯一SVID并同UID私钥签名，UID1002同接口真实PermissionDenied且0身份；目录0700、密钥0600/owner1001。管理员仍受信，不宣称组织/硬件/用户真实性。

### AC-04 原消费与十负例

本轮真实材料经原验证器VALID/四true；独立复算单EC直接根、叶/URI/签名；原十负例0 VALID且原因不变。模拟过期不当真实撤销，凭据不覆盖无效/撤销授权，金额/用户付款意愿未新增验证，付款/API副作用0。

### AC-05 原回归与防护

原130=28+19+9+74全部原断言通过；任务15防护保留，成员精确长度/SHA负例通过，Windows实际argv接口联调保持。不能修改产品/原tests、跳过/减少断言、改unittest.fail或继承。

### AC-06 清理、账本与成本

真实资产预检有独立阶段ID、次数/结果/实际提取字节、非敏感tmpfs路径/所有权和清理证据；每次失败也消费次数。发行仍仅Evaluator最多1次，全部退出分支保留独立清理原始输出、残余进程/私有tmpfs/公开私钥0及接受快照保持。原H77/H77R失败和旧费用/UNKNOWN累计分列；不将“服务未启动”说成“尝试未消费”。防挂单命令≤180秒/单发行≤20分钟，清理不受阶段预算阻断。

### AC-07 统一提交及独立L3

正式L2六项全部通过才SUBMITTED；包括真实预检命令/原始输出/结果摘要，全部提交引用由SUBMISSION封存。Evaluator接受后输入不可变，独立预检后唯一正式发行、十负例/回归与人工管理/内核/清理回查。成功索引缺失时从失败目录人工回查清理，不能改原FAIL或补造来源产物。逐AC二元判断、任务/影响/继续价值分开结论；不得追改H77R拒收。

## Allowed scope / 允许范围

Executor可修改本包WORKLOAD.py的extract_binaries和Collector.collect唯一调用；TASK_TESTS.py仅make_archive、两项归档测试可适配显式fixture profile，可新增本修复必要归档负例，其余原保护不变。可新增ASSET_PREFLIGHT.py、REPORT/SUBMISSION/ATTEMPT_LEDGER及evidence/executor_*、evidence/l2或l2_retry_02、asset_preflight/executor_01/02和任务runtime。

Evaluator冻结QUALIFY、CHECK/BOOTSTRAP/AUDIT/RUN/SEAM、CONTRACT/PLAN、BINARY_MEMBER_LOCK、初始复制索引、BASELINE/FREEZE/准备材料；这些只读。Evaluator拥有接受/L3/真实发行及最终治理。不能修改原H77R或其它任务源代码。

## Exclusions / 明确排除

无产品src/原tests/共享workflow更改，无SPIRE版本/配置/链型/RSA/中间链/选择器/挑战/验证器/清理机制变化，无新平台/钱包/链/组织或用户强认证/轮换撤销能力。无下载/安装/升级/WSL配置/其它发行版/Docker/API/付款/Git提交推送。禁止随意加大上限、extractall、链接/特殊文件、逃逸/重复、缓存二进制替代和模拟资产替代真实预检。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/VALIDATION_PLAN.yaml

VP-01保护AC-01；VP-02冻结QUALIFY，L2真实资产预检+入口联调/历史源，L3独立预检后CHECK.live对应AC-02/03；VP-03原验证器/十负例对应AC-04；VP-04原130对应AC-05；VP-05原收尾及预检账本对应AC-06；VP-06最终保持/人工审查对应AC-01/07。实际命令冻结于YAML，公共Runner顺序/角色不变。

ASSET_PREFLIGHT输出到QUALIFY指定的本包evidence/asset_preflight/<phase>_NN/RESULT.json，固定schema=h77r2-real-asset-preflight/v1，包含phase、archive_sha256/archive_size、extractor_sha256、binaries（name→archive_member/size/archive_member_sha256/extracted_sha256）、extracted_bytes=257815664、scratch_path/scratch_owner、scratch_removed=true、binary_executions=0、spire_service_starts=0、new_downloads=0。清理必须在RESULT发布成功前完成。所有路径严格限定本任务，manifest不可从外部参数替换。

## Authorization / 授权

继承负责人原H76同一现有WSL来源/签名实验及独立评估授权。本包允许Executor已安装Ubuntu中的无服务真实资产预检/非敏感临时提取；不允许Executor发行、生成密钥/token或执行SPIRE binary。Evaluator接受后独立预检及唯一一次原目标发行。后续机制不自动续权。

existing_wsl/local_service/ephemeral_test_credentials=true，其中服务/凭据仅Evaluator；reference_read=true限现有本地材料与固定公开archive。artifact_download/install/dependency_install/api_call/browser/payments/commit/push/history_rewrite=false。

## Cost and bounded budget / 成本与预算

Expected material cost: low-to-medium，固定70MB压缩包内两binary约246MiB临时提取/摘要，最多三次资产预检和一次原目标实测；0下载/付费服务/API/付款。实际主动分钟UNKNOWN时保持UNKNOWN，无任务总体时间自设上限。
Bounded retry / iteration budget: 2版任务实现、2正式L2/至多2次Executor真实资产预检、1次Evaluator预检/1正式L3/1发行尝试；L1不额外预检真实资产或发行。每次预检临时binary字节上限精确257815664，二者合计低于256MiB；不能借此导出到Windows或修改WSL全局内存设置。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 同一生产提取器真实资产资格+原完整独立来源目标
Max total attempts: 2 Executor asset preflights, 1 Evaluator asset preflight, 1 L3, 1 issuer attempt
Max parallelism: 1
Max attempts per unit: 原单运行最多3匹配取证、1不匹配、1签名
Retryable failure families: 原单发行内启动同步；资产预检脚本合同内修复可在两次L2内继续，安全边界或原断言失败停止。
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/ATTEMPT_LEDGER.jsonl

## Stop conditions / 停止条件与分支

实际archive/profile不符、预检失败/清理不完整、实现超范围、链接/逃逸/重复放行、原断言失败、缺现有依赖/权限、预算耗尽或需要更改假设/AC/权限均停止保全。独立预检不通过不得发行；唯一实际发行失败不得修后重跑。只在合同内普通修复与预算范围自动继续，不逐步请Human确认。

全部AC通过→repair PASS/NOT_APPLICABLE；仅据独立实际证据判断B-15受控来源切片能否关闭，停止同类加例。来源仍未成立→REJECTED或INPUT_LIMIT，据具体断点重排，不把前置环境/资产失败当SPIRE机制失败。生命周期/真实用户/消费者方向仍需后续独立测量或授权。

## External requirement impact / 外部指标

profile=PCAC-AGENTPAY；PCAC-03/05（CORE）、06（CORE/ADAPTER）、12/15/20（CORE）关联来源/证据测量，07/08/09/10保留原授权守护。before/after修复本身不提升既有产品M2或独立来源UNKNOWN；未来实际来源全部AC通过才单列窄切片M3，不升级整项或合规结论。

对象/Contract=固定资产、根/登记/UID/叶/挑战与不变提交；代码=原credential_possession/identity_assurance及任务提取器；Test=VP-02/03/04；Evidence=真实资产预检与完整L2/新鲜L3/清理。残余：受信任管理员、UID非组织身份、无用户强认证/硬件持有/长期轮换/真实撤销/生产采用。
