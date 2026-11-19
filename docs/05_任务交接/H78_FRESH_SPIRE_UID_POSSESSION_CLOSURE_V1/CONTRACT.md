# H78：新鲜 SPIRE 来源、UID 与密钥持有完整闭环（冻结执行包）

Task ID: H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Risk: L2
Contract state: CONTRACT_FROZEN
Contract owner: Evaluator；候选已独立审定，Human明确批准本包新运行范围；原候选与未授权记录保留，不追改历史。
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-17-r133
Preparation map revision: 2026-11-17-r132（原制包依据，原字节已封存）
Active bottleneck: B-15
Hypothesis: H-78
Dispatch mode: SINGLE
Validation plan file: docs/05_任务交接/H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

目标为授权→可信主体→交易治理→支付→恢复→审计。r132的A–D本地阶段关闭，E受控本地代表闭合，F受控外部切片关闭且真实接入受授权约束。H77R3已独立签收，来源快照2085项；4正/21负、原16/130与L3 5/5均成立，但没有新发行。H77R2虽完成真实资产资格、Server/Agent启动、管理根/列表/创建，UID/SVID/持有仍未独立闭合。最前关键未知仍为B-15，优先于凭据生命周期建设、第二身份平台或已关闭支付切片扩例。

Metric baseline: measured：原新鲜完整来源独立签收0，实际观察最远到创建响应；历史实际样本与离线验证成立。unknown：本次同源完整UID/SVID/持有链能否成立，失败概率、完整主动成本与系统网络字节。
Estimated affected scope: 单一受控来源/目标/Ubuntu；不外推组织、用户或生产身份。
Hypothesis: 已验收采集器在一次新根/nonce发行中，能让原验证器判定合法持有、拒绝既定十负例及错误UID，并保留完整管理/内核/清理原文。
Principal change: 用已验收的同一来源采集器完成一次独立新鲜测量；产品src、原tests和凭据机制不变。时钟/失败收尾仅修正新测量入口，不扩大信任语义。
Same-baseline comparison: 同目标/归档/版本/UID/十负例/原130；before为完整独立链未签收，after仅按本包实际证据计0或1个受控代表闭环。
Expected project impact: 若全AC成立，仅闭合受控实际来源代表切片；整项E、用户强认证、轮换/撤销和生产采用不升级。
Rollback condition: 任一错误身份放行、漏确认/越权、私钥外泄、来源/范围漂移、原断言失败即停止保全，不重发。
Expected material cost: low-to-medium；两次约246MiB临时资产提取、一次短时服务链、原130及完整人工来源回查；无模型/付费API/付款/安装。实际分钟未知保留UNKNOWN。
Expected value vs alternatives: 来源直接决定最前真实性证据是否闭合；继续解析扩例边际收益已低。缺本包权限则停止实测，不换平台或先建生命周期。

## Single objective / 唯一目标

一个有界包连续完成：历史保全→离线门禁/协议检查→Executor真实无服务资产预检→统一L2→Evaluator接受不变快照→独立资产预检→唯一新根/nonce实际发行→管理list/create/show→UID1001取证与持有签名、UID1002真实RPC拒绝→原验证器/十负例/原130→所有退出分支独立清理→逐AC裁定。满足前置自动继续，不逐步骤请求Human复核。

## Dependencies and branches / 步骤与分支

1. 当前可做且已补全的是Windows本地候选制包、读取既有证据与离线自检，不运行WSL。原草案和治理原字节见references/before_executor_completion，原H77R3的2085接受项及后续审查字节由PREPARATION_BASELINE保护。
2. 冻结前Evaluator须核EXECUTOR_ASSESSMENT与原始L1，确认候选CHECK/CONTROL/QUALIFY等验收工具；把最新项目地图的当前假设/任务与H78同步，再补合同最终revision、明确Human新授权记录并切换唯一CURRENT。Executor不得自行改父PASS、地图、授权或将候选视作冻结。
3. Evaluator运行BUNDLE.py seal生成最终BASELINE/FREEZE；须已有H78冻结路由、GRANTED授权与Human原话/来源，且原HEAD与来源保持。seal不启动WSL/服务，不自动生成授权。
4. Executor用BOOTSTRAP.py --mode executor跑公共L2。VP-02先核来源副本、原16、实际历史4正/21负和8门禁自检，再做本角色唯一真实资产预检；不执行提取binary、生成凭据或发行。预检失败即停止。
5. L2全部通过后一次提交REPORT/SUBMISSION与原始EV、预检输出、失败/费用账本。Evaluator接受快照须含SUBMISSION本身和l2_gate_path，核全部输入后才置READY_FOR_REVIEW/Evaluator；报告/实现/证据随后不可变。
6. Evaluator唯一正式L3：同一QUALIFY先独立资产预检，通过才调用CHECK.live唯一发行。原WORKLOAD/RUN逐字复用H77R3；根/登记/内核UID/持有/拒绝/清理机制不变。不允许Executor现场预演或修后追加发行。
7. 任一失败保全并清理。成功索引缺失时从INDEPENDENT_ISSUANCE_ATTEMPT定位唯一失败目录核CLEANUP/raw，不要求伪造成功索引；清理通过不把来源失败改成成功。
8. 完整L3、人工管理/内核/证据/成本回查后Evaluator一次逐AC签收。成功即停止同类扩例并重排瓶颈；失败按具体阶段区分INPUT_LIMIT/实现缺陷/机制反例，不补发父或本包次数。

## Acceptance criteria / 验收标准（全部强制）

### AC-01 历史、范围与固定资产

HEAD、原src/tests/共享工具和H77R2/H77R3提交/接受/门禁/拒收/签收/清理不变；治理更新只能用明确旧字节别名。受保护数量以最终BASELINE实际计算，不把旧2034误当新全集。WORKLOAD/RUN/TASK_TESTS/BINARY_MEMBER_LOCK/AUDIT/ASSET_PREFLIGHT/PROTOCOL_CHECK与COPY_MANIFEST的byte_exact来源一致。
官方archive 70,187,551字节、SHA=7bcf5e167151a1fc58293768462b44e155ba8784214582aefa6adf18c633d1d5；Server179,378,008、Agent78,437,656及成员SHA以固定BINARY_MEMBER_LOCK为准。两角色分别同一提取器预检，总257,815,664字节、scratch完整清理，预检binary执行/服务/新下载0。

### AC-02 同一次新鲜来源与时间边界

唯一本次run_id/nonce绑定接受输入/调度/产物，nonce不同历史；新EC直接根与所有已保存历史根不同，管理根原文先于Agent启动；管理list/create/show真实原文能逐字段关联父ID、登记ID、精确目标和唯一UID1001。
挑战issued/observed与source started/finished仅在WSL同一时钟域比较，顺序正确且挑战年龄≤300秒；证书在原验证器使用的实际observed时刻有效。Windows时间单列编排账本，不假定与WSL同步，不以放宽年龄替代校验。受信管理员/本机时钟是残余边界，不宣称外部可信授时。
entry show形态或任一未观察运行边界仍UNKNOWN，只有本次原文能闭合，不靠历史或合成输出。

### AC-03 UID、SVID与密钥持有

实际管理返回、工作负载/proc PID/start/boot、内核UID/EUID及原始握手可回查；matching/nonmatching/signing分别为1001/1002/1001，同次同socket来源。UID1001恰好一个SVID、目录0700、私钥0600且owner1001，签名由该UID读取密钥完成；UID1002同接口真实PermissionDenied/no identity issued、非0退出且0身份。连接失败/系统权限拒绝不得冒充选择器拒绝；公钥证书可复制不等于持有事实。

### AC-04 验证与拒绝语义保持

同次公开材料经原credential_possession验证器VALID且四true；独立复算单EC根/叶/URI/挑战/签名。原十负例wrong_root/domain/agent/executor/provider/nonce/signature/replay/stale/expired全部非VALID且原因不变；历史响应4正/21负和原身份授权守护保持。错父/目标/UID/ID由原管理验证/协议拒绝守护覆盖，不新增不受控真实负向发行。模拟过期不是实际撤销，身份持有不替代支付授权、用户意愿或金额确认。

### AC-05 原测试和来源保护

TASK_TESTS原16项及原28+19+9+74=130原断言全部通过，无skip/减少/替换断言；候选8项门禁自检通过。不得更改原测试、unittest.fail或产品来适配验收。

### AC-06 副作用、失败收尾与累计成本

仅现有Ubuntu，固定SPIRE版本/目标/UID；允许服务间127.0.0.1回环及专属Unix socket，不发起外部网络请求、不下载/安装/创建用户账户/改全局WSL设置/付款/API/Git。原生WSL不等价于网络强隔离，系统总网络字节不能证明为0时记UNKNOWN。
唯一发行尝试、服务实际启动数、匹配同步重试、预检与正式门禁分别记账，失败也消费。成功/失败均有按PID/start/boot和tmpfs所有权清理的原文、第二条独立检查命令/输出；本次残余进程/私有目录/公开私钥0。成功索引缺失不影响从失败目录核清理，但来源仍判失败。
Windows监督器不设会中断清理的外层强杀超时；原发行进程1100秒防挂、单SPIRE命令≤180秒保持，清理不因活跃窗口到期而跳过。记录本任务及父失败/UNKNOWN，不能因服务未启动就返还尝试。

### AC-07 统一证据与独立复核

公共L2六项PASS才SUBMITTED；六组EV三件套命令/长度/SHA和真实预检原文均封存。Evaluator接受后一次公共L3，六组RV-EV及公共索引完整，逐AC二元判断并引用证据；任务、项目影响和继续价值分开。任何强制来源证据缺失不得PASS；现场失败不改CHECK/实现后重跑。

## Allowed scope / 允许范围

仅本包候选文件与以后本包报告/账本/执行证据/runtime。冻结前候选脚本由Evaluator审定；冻结后WORKLOAD/RUN/原16及所有CHECK/CONTROL/QUALIFY/PLAN/负例/资产锁均只读。Executor可补REPORT/SUBMISSION、次数/费用账本及evidence/executor_*、l2或l2_retry_02，不能改验收器或已接受输入。Evaluator拥有接受/L3/REVIEW及最终地图/路由更新。

## Exclusions / 明确排除

不改产品src、原tests、共享workflow、旧任务/旧门禁，不扩强认证、组织/用户身份、RSA/中间链、轮换/撤销、钱包、区块链或第二来源。不导出私钥/token，不生成合成证书作本次正例，不直接运行旧解压缓存，不复用历史根/nonce/成功材料。不进行生产接入、外部API/浏览器/付款/下载/安装/提交推送或宽泛清理。

## Validation plan / 验证计划

精确argv、cwd、退出码和Evaluator分支已写VALIDATION_PLAN.yaml：VP-01保持；VP-02离线资格→角色真实资产预检→仅Evaluator单次发行；VP-03历史或本次原验证器/十负例及独立raw回查；VP-04原130；VP-05独立清理/接受保持；VP-06最终保持。公共Runner可在失败后继续读证据/回归，但只有VP-02包含发行路径，其他步骤不得隐式重发。人工义务见REVIEW_PROCEDURE.md。

## Authorization / 当前授权与冻结条件

Human对紧接上一条明确列举H78新运行范围的确认问题答复“批准”。AUTHORIZATION.json记录真实原话、前置问题和来源，状态GRANTED；仅本包existing_wsl/local_service/ephemeral_test_credentials三项生效，限固定现有Ubuntu、双方各一次无服务资产预检及Evaluator唯一一次发行、Server1+Agent1。此前候选NOT_GRANTED及EVALUATOR_READINESS记录保留为批准前事实。
其余commit/push/history/api/install/download/browser/payments保持false。此次新授权不重置H77/H77R/H77R2预算，不追认父失败，不给后续机制自动续权。代码不会自行授权、改CURRENT或重写地图。

## Cost and bounded budget / 有界预算

Bounded retry / iteration budget: 任务辅助准备实现最多2版；正式L2最多2次，Evaluator L3最多1次；Executor发行0，Evaluator发行尝试1。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 1个完整同次新鲜来源代表闭环与全部原拒绝/回归/清理
Max total attempts: 2 L2 / 1 L3 / 1 Executor asset preflight / 1 Evaluator asset preflight / 1 issuer
Max parallelism: 1
Max attempts per unit: Server1、Agent1；单次发行内匹配取证最多3次仅同步、非匹配1次、签名1次；管理列表最多14轮原同步轮询
Retryable failure families: 原单发行内既定同步；正式第二L2仅在未消费Executor预检且无安全/原断言失败时用于预算内非语义问题。已产生预检START、真实发行START或零容忍反例即不补发。
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H78_FRESH_SPIRE_UID_POSSESSION_CLOSURE_V1/ATTEMPT_LEDGER.jsonl；Evaluator另用evidence/EVALUATOR_ATTEMPT_LEDGER.jsonl
Asset preflight: 内部120秒，外层180秒；每次临时提取257,815,664字节上限，清理后才发布成功RESULT
Issuer live watchdog: 原WORKLOAD 1100秒；单SPIRE CLI≤180秒；外围监督器等待清理完成，不设任务总时长上限
成本字段未知保持UNKNOWN，不将来源时钟与Windows时钟相减当实际主动耗时。

## Stop conditions / 停止与迭代

权限/冻结/HEAD/来源/成员/接受漂移、原断言失败、错误身份放行、私钥越界、清理不能证明、预算耗尽或需要更改假设/AC/范围均停止并保全。完整闭环成立→仅受控B-15来源切片IMPROVED后STOP同类扩例，重新比较生命周期/真实主体/消费者；前置失败不等于机制反证，唯一发行失败不得修后重跑，Evaluator再判断修复/切换或需要Human决策。

## External requirement impact / 外部指标

profile=PCAC-AGENTPAY。PCAC-03/05为CORE、06为CORE/ADAPTER、12为CORE、15为CORE/ADAPTER、20为CORE/EVIDENCE_ONLY；07–10原授权守护保持。对象/Contract=同次根/登记/UID/SVID/挑战及接受快照；代码=原credential_possession/identity_assurance与本任务采集/检查工具；Test=VP-02/03/04及原守护；Evidence=新鲜预检/实际L3/管理与内核原文/独立清理。
before/after：整项既有产品M2不因测量升级，完整实际来源UNKNOWN只有全AC通过才记受控代表切片M3，不升级整体KYA或合规。残余：管理员受信、UID非用户/组织/硬件身份，缺长期轮换/真实撤销/生产消费者与外部可信授时。
