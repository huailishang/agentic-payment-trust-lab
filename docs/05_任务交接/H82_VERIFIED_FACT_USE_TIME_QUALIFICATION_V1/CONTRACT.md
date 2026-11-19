# H82：凭据事实使用时点与撤销/轮换责任边界——只读资格验证（正式冻结）

Task ID: `H82_VERIFIED_FACT_USE_TIME_QUALIFICATION_V1`  
Task kind: capability_experiment
Execution mode: **measurement-only(仅测量)**  
Workflow: `evaluator-executor-workflow/v2.2`  
**Contract state: CONTRACT_FROZEN / Evaluator 已制定，下一角色 Executor**  
Dispatch: `SINGLE`  
Baseline HEAD: `61414d05521f7c9fe15cf0299b48b25916f5fa0e`  
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-19-r138
Active bottleneck: B-24
Hypothesis: H-82-CANDIDATE
地图原候选编号现在由本任务冻结，不代表地图已有后续成果。  
Previous verdict: H81 `PASS / IMPROVED / STOP`；不得重开、覆盖或追认旧H80失败。  
Validation plan file: docs/05_任务交接/H82_VERIFIED_FACT_USE_TIME_QUALIFICATION_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

Metric baseline: H81独立签收原observed时点事实；当前可信使用时点、上游撤销/轮换来源与生产刷新证据UNKNOWN；消费者签名无use_time_epoch，产品能力增量尚未测量。
Estimated affected scope: 共享身份消费函数1个、支付P3入口1个、凭据验证来源1个、原5组回归、15个锁定原文件；产品文件改动0。
Expected project impact: 优先将B-24事实来源/责任资格从UNKNOWN整理为可复算的接口层证据，不推论生产安全提升；独立评估可判NO_MEASURABLE_GAIN或INCONCLUSIVE。
Rollback condition: 原件SHA漂移、合成基准不一致、回归失败、需要实时来源/外部授权或触碰产品策略立即停止并报告，不回写历史。

## 1. 为什么是这个包

项目链路为用户授权→可信Agent及执行者→交易绑定和执行前治理→支付/恢复→审计。A–D本地代表验证已完成，E有H78真实公开来源代表验证与H81身份归因闭合；但H81只证明**捕获时刻**的凭据归属，不证明之后付款时依旧有效。优先B-24是因为它直接关系下一次身份晋级的证据资格，且可以在不启动新服务、不签发证书、不发生支付的情况下先界定责任；优先级高于额外PSP/第二平台的昂贵外部研究。

**已实现且不得重建：** X.509证书在`observed_at_epoch`有效期、挑战`max_age_seconds`、Nonce列表防重放、`identity.status=inactive/revoked`、凭据引用不一致降级、H81 Agent/Provider/Executor三元归属、HMAC/ES256签署指令有效期。来源及限定见`EXISTING_CONTROL_REVIEW_20261119.md`。原支付P3策略**允许 BOUND 与 VERIFIED 两级**；没有新业务授权不得改为只接收VERIFIED。

既有可测基线（2026-11-19源码只读检查）：`verify_x509_svid_credential_possession`验证函数接收历史`observed_at_epoch`，而`verify_agent_executor_identity`和`execute_with_payment_binding_gate`签名没有`use_time_epoch`或动态发行方撤销状态；原H81 L2/L3各5/5，33消费观测/10密码学负例保持。**没有可靠的当前可信使用时间、当前撤销事件、真实轮换事件和生产上游调用证据**；由此无法判断现在的真实凭据是否有效。这是输入资格未知，不是已经证实的漏洞。

## 2. 唯一目标、假设和反方解释

**唯一可交付结果：** 形成原代码及历史证据→当前消费者输入→身份晋级→支付P3策略的、可机器复算的**事实血缘与责任资格判定**，用最小同输入离线探针确认“原已验证Fact在消费者内部有没有使用时刻刷新”，并明确哪些真实场景不可判定。

H-82-CANDIDATE的可证伪假设：在当前受保护源码中，消费者使用传入的`credential_possession_fact`布尔/绑定状态，却没有独立可信使用时间；只改变调用者的**假设使用时刻标签**、不更新Fact，不会令该函数自动撤销VERIFIED晋级。若函数真实接受可信时间/撤销权威、并在相同身份场景中重新计算，假设为假，本轮停止。

**主要变化仅一项：** 将B-24从静态“猜测缺口”提升为有原字节锁、公开输入边界、单变量合成接口对照、不可判定项与独立复算记录的**资格测量**。本任务**无任何产品代码修改**，不以新增测试或报告页数宣称产品安全能力改善。

反方解释：真正的实时凭据有效性由上游可信发行者/支付执行边界重新认证；当前纯函数只承诺处理已验证事实。若该解释成立，B-24应定性为**接口责任与事实来源契约**，而非当前模块的安全漏洞；对上游真实现状仍标`UNKNOWN`。

## 3. 受控输入、冻结脚本与强制运行环境

- 固定原件：`SOURCE_LOCK.json`对15项原源码、相关原测试、H81独立终验文件、原项目地图r138与本轮前置审计按SHA-256锁定；`baseline_head`仅锁原提交，不覆盖工作区已存在、尚未提交的H80/H81代码。不能用`git show HEAD`代替已冻结工作树版本。
- 固定测量工具：`CHECK.py` SHA-256=`2ba0801715263b681ba25ac61498c0a2e0b76d8ce5013447302aef43256f38e0`。
- 固定输入清单：`SOURCE_LOCK.json` SHA-256=`07c376a0febe04b7e936e9d56dc940c6d9b965a7ffef20af180dcd1ca385c47f`。
- 固定验证计划：`VALIDATION_PLAN.yaml` SHA-256=`38f509761447365d39f3bf74ca90a9e83ed8ff79d80cca51382a003264ab356e`。
- 前一任务H81已接受SUBMISSION SHA-256=`72cd569ad2f5274c32511135c1c97c0e4469c5f0e5cf742ff3cd1ab590a762ba`，其2647项接受与独立L3不因本任务重复验收。
- **只允本机原生Windows + 既有Conda `agent` Python运行冻结验证。** WSL/Bash作为Windows Python传输桥、WSL原生运行、Docker/新增服务、安装/下载均**不授权**；`CHECK.py`主动拒绝非Windows运行。若原生入口不可用，直接交`BLOCKED`证据，不以环境变通替代授权。
- 测量脚本只读，原生Python标准库驱动已存在模块与测试；所构造Fact是**合成对象、不经加密验证**，仅用于消费者接口资格判断；不发证书，不联网，不打开钱包，不执行真实支付callback。

## 4. 完整执行步骤（在同一合同内自动推进）

| 阶段 | 执行者行动 | 继续/停止条件 |
| --- | --- | --- |
| S0 原件锁与运行入口 | 记录基线/当前git状态，核15项SHA、冻结脚本和计划摘要；核既有原生Windows Conda `agent`入口，无新安装 | 输入漂移或无允许的原生运行入口→BLOCKED，不得修产品/冻结文件 |
| S1 现有能力及输入资格 | 执行`VP-02 inventory`，列出历史观察时刻、证书有效期、Nonce、撤销标志、引用轮换、身份晋级、支付P3现有语义；四类权威来源标`MEASURED/UNKNOWN/OUT_OF_SCOPE` | 没有真实权威来源→继续做**接口层**合成探针；不得假装生产事实 |
| S2 单变量离线探针 | `VP-03 probe`：正常事实晋级VERIFIED；只变化**外部模拟使用时刻**不注入函数，比较输出；各单变量对照分别改`identity.status`、当前credential ref、fact的`freshness_valid`、已验证Agent上下文 | 基线或控制结果偏离合同时停止；外部时间标签结果仅能解释为“本函数不使用该输入”，不是真实过期/安全失效 |
| S3 最小守护回归 | `VP-04 regressions`对原五组凭据、上下文、身份、支付绑定和ES256测试重新执行；禁止skip/削弱/修原代码 | 有任何新回归失败→BLOCKED/REJECTED候选，不为成功改旧测试 |
| S4 分类、提交与独立复核 | `VP-05 qualification`明确`NOT_JUDGEABLE`、上游责任未知，补充`REPORT.md`、原三件套/L2-GATE与一次统一提交；下一角色Evaluator接受冻结后运行唯一独立L3 | 五项L2通过才可`SUBMITTED_FOR_REVIEW`；L3通过+独立逐项签收才可PASS |

## 5. 原子验收条件

- **AC-01 原件/范围**：15项SOURCE_LOCK精确SHA一致、冻结CHECK/PLAN/LOCK不变，H81终验和旧失败保全；变动仅本H82的报告/证据/CURRENT执行路由，无产品、旧测试、旧历史变动。VP-01。
- **AC-02 能力分层**：自动源码分析精确证明旧`observed`、签署指令过期、Nonce、撤销状态flag、引用及三元归属已有逻辑；消费者/支付入口当前签名的`use_time_epoch`不存在；真实权威状态、上游重新验证统一记UNKNOWN，既不宣称缺陷也不宣称已解决。VP-02。
- **AC-03 同输入对照**：合成Fact原消费者`VERIFIED`；仅改变**外部时间标签**，不变Fact仍`VERIFIED`；分别变成revoked→`INVALID/DECLARED`、credential引用错配→`BOUND`、freshness_bit false→`BOUND`、跨Agent事实→`BOUND`。标出合成Fact未加密验证、无真实当前时间/资金效果。VP-03。
- **AC-04 保持原防护**：VP-03不能绕开原身份守护，VP-04原五组测试真实通过，无跳过；不存在新凭据和真实支付或改变P3的BOUND/VERIFIED策略。VP-03/04。
- **AC-05 结论可消费、边界清晰**：VP-05输出三个可明确判定层次：已实现的历史时点校验、当前消费者函数内部未暴露use-time输入、生产或上游实时状态`NOT_JUDGEABLE/UNKNOWN`；REPORT逐项列原始证据/摘要/成本、最小缺失输入及竞争解释。五项L2原三件套齐全；Evaluator L3重复计算并独立签收或拒收。VP-05。

**这五项是“事实资格审查正确性”的验收标准，不是“支付安全新能力通过”。** 若本来就是上游提供新鲜Fact，则结论为接口契约/责任归属，不需要本包开发撤销服务。

## Allowed scope / 允许范围

## 6. 最终交付及权限

Executor可写：本H82下`REPORT.md`、`SUBMISSION.json`、`ATTEMPT_LEDGER.jsonl`、`evidence/executor_*`、`evidence/l2*`，以及`CURRENT.md`仅执行角色/状态/路径。**不能写**本H82的`CONTRACT.md`、`SOURCE_LOCK.json`、`CHECK.py`、`VALIDATION_PLAN.yaml`、`EXISTING_CONTROL_REVIEW_20261119.md`、旧H81/H78任何证据、产品源及旧测试。Evaluator独占`evidence/ACCEPTED.json`、L3原始证据、`REVIEW.md`、后续地图更新。

必须交付四层时点/状态血缘：`issuer/authority state`、`capture-time verification`、`consumer use-time`、`P3 payment decision`；每层写来源/状态/可信权威/不可判定性，并给出“下一次要证明真实有效，至少需要谁提供什么”的最小事实契约。正式L2原文`EV-*`/meta/stdout/stderr与`L2-GATE.json`由v2.2 runner保存，Evaluator在接受未变更快照后另跑唯一独立L3。报告不能凭工具PASS自行判产品PASS。

## Exclusions / 明确排除

不允许真实凭据/状态服务/支付、私钥、WSL、网络、安装下载和产品代码改动；不得借用H81专属环境例外。

## 7. Cost, authorization and stop conditions / 成本、停止条件与授权

预算：**1个只读测量周期；最多2次正式L2（第二次仅原生Python启动/环境错误且不动冻结代码时）；最多1次正式L3；并发1**。每项测试子进程上限100秒，5项门禁，0新服务、0真实凭据、0外部API/支付、0产品实现修改。廉价L1仅1轮。成功即停，禁止靠增加样本或重跑获得“产品改善”。原H80 2实现/2失败L2、H81实际1实现登记/1L2/1L3以及其它历史消耗独立保留，当前包预算不清零旧成本。

立即停止：15项源SHA任一不符、原生环境不可用、合成对照不符、原测试失败、时间/身份权威来源需要扩大权限、需要新增实现或修改支付策略、L2重试超限、任何新证书/私钥/网络/资金动作被提出。先交Evaluator，不自发扩包；非权威数据标`UNKNOWN/NOT_JUDGEABLE`是合规输出，不为求“找到漏洞”强改结果。

当前所有结构化授权标志只允许`authorization_reference_read=true`；commit、push、历史重写、API、安装、下载、WSL、服务、浏览器、测试/真实付款、容器、临时新凭据全部false。负责人授权**制定执行包**，不代表授权真实支付、对外接入或篡改冻结资料；合同授权的只是本地原生离线检查与报告工作。

## 8. 验收后项目决策

- 若全部证据一致：任务可`PASS`，**项目影响不能自动记IMPROVED**；本包不改产品。只证明使用时点责任输入未在这两个消费者签名内暴露，无法推出生产风险。优先`STOP`无来源假设扩例，或形成需要负责人单独审批的最小上游取证需求。
- 若证据揭示上游当前已有权威重验：标出真实调用链和权限来源，调整瓶颈归属，避免重复开发。
- 若真实上游证据缺失：`INCONCLUSIVE`（真实实时效力）、接口测量`PASS`可以同时成立；不得把疑问升级为已证漏洞，也不得复用H81的WSL桥接例外。

External requirement impact：`PCAC-AGENTPAY`中PCAC-03/05/06/09/12/20的**证据资格层**，不改变合规成熟度或生产采用状态。
