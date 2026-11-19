# H81 Evaluator boundary addendum / 2026-11-19

Task: `H81_VERIFIED_FACT_CONSUMPTION_CLOSURE_V1`  
Decision owner: Evaluator  
Decision: **TRANSPORT_EXCEPTION_APPROVED_FOR_NEW_FORMAL_RUN; PRODUCT_ACCEPTANCE_PENDING**  
Status: **Evaluator governance decision only; H81 L2=0, L3=0 at the time of this decision**

## 1. 全局判断与理由

本项目证明高风险智能体支付的“授权→可信主体→交易绑定/执行前治理→执行/恢复→可消费审计”信任链。A–D本地阶段代表性完成；E当前第一瓶颈B-23是已验证身份事实在消费端被错误归属给另一个Agent/Provider/Executor；F外部代表切片已有成果但真实生产接入未获证明。H79已提供跨Agent错误晋级独立反例，优先于尚未独立观测的凭据生命周期或第二支付平台。H81是同输入对照、原消费安全边界与回归的**能力归因闭合包**，不是重做SPIRE发行或新增支付功能。

已检查本地CURRENT r137、H81 CONTRACT/VALIDATION_PLAN/CHECK/BOOTSTRAP/REPORT、11月19日`evidence/executor_wsl_diagnostic_20261119/REPORT.md`和原测试输入。已有**非正式**诊断显示原目标6/6、33项消费观察、10密码学负例及原必要回归成功，M01 VERIFIED→VERIFIED、M02 VERIFIED→BOUND，跨Agent错误晋级1→0；但非正式诊断并非H81正式L2。此前原WSL Python cryptography 41.0.7不能完成行为脚本，现有Windows Conda agent Python 46.0.7完成。**独立L3和产品正式结论仍未产生，B-23 OPEN / INCONCLUSIVE。**

## 2. 单一执行传输例外：适用条件与优先级

Human已明确批准使用本机现有WSL和Conda `agent`，并说明Docker不可用。作为Evaluator，**只为H81尚未消耗的正式离线验证**批准一个窄例外：允许由当前CodexPro WSL Bash入口**启动既有Windows Conda `agent` 的 `python.exe`**，执行项目内原封不动的H81 BOOTSTRAP、CHECK、COMPARE、EVIDENCE、SEAL及其既有本地子进程。

此项**明示取代**原H81 CONTRACT S0、Frozen behavior第5项、Exclusions及EXECUTOR_README中“命令父进程必须直接来自原生PowerShell、禁止Bash/WSL中转”的**启动传输限制，仅限上述Windows解释器启动链**。旧文档保留以供审计，不能对原运行记录追溯授权。此例外不改变其余合同条款、五项AC、原始冻结校验器、预算、产品范围或L2/L3责任分离。

`CURRENT.md` 的 `authorization_existing_wsl: false` 及其他 `authorization_*=false` 标志**继续禁止WSL内原生发行/服务/凭据/钱包/外部执行工作负载**；此单独签署的父进程**传输例外**用 `execution_transport_exception_path` 显式记录，不将它伪装为“原生命令入口已满足”。如果团队无法接受这种精确的传输例外解释，必须在正式启动前STOP并另制版本化、重冻结的任务包；不得静默修改原CHECK/BOOTSTRAP或授权标志绕过控制。

允许的解释器仅为项目已记录路径 `D:/SoftWare/Anaconda/workspace/.conda/envs/agent/python.exe`，不得使用WSL的`python3`替代正式运行；没有新解释器安装、下载或环境升级授权。正式每个入口的原始证据必须记录：父WSL Bash/Windows解释器的真实启动方式、`sys.executable`、`sys.platform`、`os.name`、`cryptography.__version__`、工作目录、传入解释器与子进程的环境要点、完整argv与exit code、stdout/stderr、UTC时钟及摘要。不能仅依赖`win32`布尔值宣称原生PowerShell。

## 3. 执行者单包续行：S0→S3，不再建小修包

1. **正式门禁之前**：只读确认HEAD仍为`61414d05521f7c9fe15cf0299b48b25916f5fa0e`、H81冻结文件和BASELINE/FREEZE摘要，确认受保护2548条与原来源未漂移。确认唯一已修测试行精确对应冻结指定的`identity=replace(self.identity, credential_ref="different-credential")`；原fixture与两产品不得再次改动。先运行一次无副作用的Windows解释器与依赖预检并留完整启动祖先声明；失败即停止，且不得改原校验器或升级依赖。
2. 如上述前提满足，通过**同一个现有Windows Conda agent Python**在WSL父入口调用H81原`BOOTSTRAP.py --mode implementation --attempt 1`，在报告中如实注明这是**对前次已经发生的非正式一行修复进行正式周期登记**，而不是声称修复在登记后才发生。不得补写、倒填或覆盖11月19日原诊断时间。
3. 原`BOOTSTRAP.py --mode executor --attempt 1`按原`VALIDATION_PLAN.yaml`统一正式运行五项VP；至少含锁定before_h80两旧源码且同一历史输入M01/M02的真实独立子进程对照、当前33消费观察及十密码学负例、原28/18/6、130、来源16、协议4正21负、离线门禁8。原始三件套、摘要、冻结校验、同源同输入、error reason、P2/P4和本地callback语义逐项核对；不添加新样本或修改原断言。
4. 完成正式`CLOSURE.json`、统一`REPORT.md`、`SUBMISSION.json`和`SEAL`后停止重跑，并以不可变提交快照交给Evaluator。Evaluator先接受、核快照，再用本轮允许的相同解释器执行**唯一独立L3**（五项VP并逐AC审查）；L3要有独立调用、独立原始输出与环境记录，不能复用诊断和Executor L2冒充。
5. 正式L2首次失败时，仅合同已冻结的单项测试前提/子进程冷启动导入问题可按原attempt2限额处理；产品需要改动、任何新零容忍安全失败、其余回归失败、来源漂移、冻结checker不支持新传输或预算用尽，立即STOP并交Evaluator。L2一次通过即不得重跑；此传输例外不创造额外重试预算。

## 4. 预算、权限、独立门槛

- H80历史：2实现/2 L2 FAIL/0 L3，原结论REJECTED/INCONCLUSIVE不追认；H80R：0/0/0，已被替代。H81迄本决定：非正式修复及诊断已有实际成本（主动分钟UNKNOWN），**形式账本0实现登记/0 L2/0 L3**，不得把它们计为正式通过。余量仍为最多2实现周期/2正式L2/1独立L3，且不得隐瞒非正式工作。
- 无Docker、新SPIRE服务、真实签发、私钥/新凭据、钱包、浏览器、网络/API、下载、安装、真实资金或测试支付、Git提交/推送、历史重写。只有允许的离线本地Python子进程及既有公开历史材料。
- AC-01原件与唯一输入变更；AC-02错误晋级1→0和M01保持；AC-03完整三维/密码学与旧策略守护；AC-04全部原必要回归；AC-05可独立复算封存和Evaluator唯一L3。缺任一证据即`INCONCLUSIVE`，不得以诊断PASS提前关闭B-23。
- `external_requirement_impact`: `PCAC-AGENTPAY`；原H81 PCAC-03/05/06/09/12/20适用性不变；成熟度before=M2，after须独立签收才按窄切片提高，**不等于监管合规证明**。
- 全部正式AC成立，Evaluator方可判`IMPROVED`并关闭B-23的**本地代表消费切片**；停止此同类扩例，再比较凭据真实生命周期/撤销等只读资格测量。否则继续保留OPEN，按错误性质CONTINUE或SWITCH，不自动升级E整个阶段。

## 5. 冻结完整性

本文件仅为Evaluator**新增**的2026-11-19执行传输边界增补，不修改旧CONTRACT、PLAN、CHECK、BOOTSTRAP、BEFORE、COMPARE、EVIDENCE、BASELINE、FREEZE、原H80/H80R报告或历史运行证据；旧根地图r137在H81保护集合内，正式L2/L3完成前**不改地图正文/版号**，待独立验收后做新revision和历史字节归档。H81仍是唯一在执行任务；本文件不宣布L2、L3或产品PASS。
