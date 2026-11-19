# H76：实际签发与工作负载持有证明测量包

Task ID: H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: capability_experiment
Experiment mode: measurement-only
Risk: L2
Contract state: CONTRACT_FROZEN
Readiness: OWNER_AUTHORIZED_EXECUTOR_ACTIVE
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r128
Active bottleneck: B-15
Hypothesis: H-76
Dispatch mode: SINGLE
Parallel probe group: NONE
Sibling hypotheses: NONE

## Strategic basis / 为什么做这个包

项目要证明授权、可信主体、交易绑定、执行前治理、支付、恢复、审计形成可独立复核的链。A–D本地阶段关闭，E仅受控本地代表闭合，F仅受控Stripe切片关闭。B-21和B-22本地代表切片继续停止扩展。

Metric baseline: measured：已有X.509-SVID直接根/持有证明验证器及合成固定向量；unknown：实际SPIRE签发、内核UID选择器、原持有者签名是否可被原验证器消费。此前实际SPIRE运行0。Docker客户端存在、Linux engine此前未连通是前置未知，不能写成环境可用。

单一可证伪假设：新鲜、受控的SPIRE发行者按真实Unix调用者UID签发的EC叶证书与同UID持有者产生的挑战签名，可以由原有直接根验证器判定；不匹配UID无法取得该身份。单主要变化是**凭据来源从本地合成向量换为实际运行发行者/Workload API（工作负载取证接口）**，产品代码保持不变。

Estimated affected scope: 一个新鲜测试信任域、一套Server/Agent、UID1001匹配工作负载和UID1002不匹配对照；不外推企业/KYC身份、精确应用/PID、硬件密钥或远程主机真实性。节点以一次性join token（加入令牌）受控引导，管理者/root和宿主机仍在信任边界内。

Expected project impact: 取得此前没有的实际发行/选择器/持有证明到现有消费者的代表证据，或锁定一个具体兼容缺口；不是通用身份平台或生产支付能力。继续stored字段、重复支付或第二PSP不能补最前面的真实性来源缺口；真实用户强认证/机构凭证依赖更多授权，当前本包信息收益更高。

Rollback condition: 任一零容忍错误放行、私钥越界、需要放宽原验证器/中间链/RSA、额外平台/权限，即STOP并交Evaluator。不得把失败改为换平台或生成本地正例证书。

## Single objective / 唯一目标

一次完成“环境资格→固定资产→新鲜发行→匹配/不匹配UID→持有者签名→原验证器及反例→必要回归→清理→L2→独立L3”，用原始证据确定上述假设是否成立。只是测量，不修改src/或原tests/。Executor在合同内实现任务脚本、修复脚本和自检，不逐步交Human；最后统一提交。

## Dependencies and automatic branches / 连续步骤与分支

1. 核BASELINE.json、冻结文件及AUTHORIZATION.md；未授权不执行运行步骤。只使用现有Docker Desktop Linux endpoint：`npipe:////./pipe/dockerDesktopLinuxEngine`。若未连通，授权后最多启动既有Docker Desktop一次并重新检查；不安装/升级、切换backend、修复WSL、改变Docker设置或影响别的容器。仍失败→INPUT_LIMIT_ENV，保留原始返回，停止。
2. 按ASSET_LOCK.json下载唯一SPIRE包、三个wheel（预编译Python依赖包），每个完成后核长度/SHA-256；拉取唯一固定linux/amd64 Python镜像摘要。任何来源/摘要不符即STOP。无在线安装脚本、无apt、无源码构建外部依赖、无浮动latest。构建仅在容器内离线`pip --no-index --require-hashes`，宿主Python环境不变。
3. 单容器内同一PID/网络命名空间运行实际Server/Agent和两个UID，避免跨容器/proc证明歧义。server管理socket/root私有目录与Workload API公共socket分开。新鲜EC根由Server生成；禁用UpstreamAuthority与dummy CA。先从本地管理socket取得并固定bundle，再启动Agent/取得工作负载证书；不把工作负载自带bundle当权威根。
4. 固定登记SPIFFE ID：`spiffe://h76.test/agent/h76-agent/executor/h76-executor`，selector只有`unix:uid:1001`。节点父ID来自本次真实加入结果；join token和包含它的原始字段不出私有tmpfs。实际Agent身份及parentID关联需可复核；公开投影对令牌字段脱敏并标记，不伪称未脱敏原件。
5. UID1001通过`spire-agent api fetch x509`取凭据并在同UID边界内用私钥签规范挑战；不得把SVID私钥复制到Windows或其它UID后称为原持有者证明。UID1002使用相同可访问socket、自己的可写目录请求，必须得到接口拒绝且0身份。文件权限错误、连接失败、超时均不算选择器拒绝。
6. 本机原验证器消费公共证书/签名、管理通道根与冻结期望值。若叶链不符现有直接EC根profile（约束），记录实测不兼容、准确失败原因及证书链后停止；不修产品。若正常成立，连续完成冻结反例和必要回归。
7. 所有退出分支均清除本包容器/tmpfs密钥、加入令牌与任务构建缓存；只删除所有权标签/ID均匹配的资源。保留公开证书、签名、脱敏日志、版本/配置/选择器和摘要。Executor统一L2与完整报告；Evaluator接受原字节后以新容器/新根/新nonce独立L3，不复用旧私钥或旧正例结果。

## Acceptance criteria / 逐项验收（全部强制）

### AC-01 基线与权限

原src/tests/历史证据与冻结文件摘要不变；实际动作与负责人最终批准的本合同范围一致。仅任务脚本可修复。原H74拒收、H74R签收和旧成本记录不回写。缺权限或基线漂移不通过。

### AC-02 资产、隔离与真实发行

运行二进制/依赖与ASSET_LOCK一致，记录image ID、原base digest、version和配置。容器无外网、无host PID/network/privileged/Docker socket/宿主目录挂载；rootfs只读、密钥只在tmpfs。实际Server生成新根，经管理socket固定根指纹；新鲜运行、证书链与登记/Agent父ID有同一次运行关联证据。本地Python自造正例不通过。

### AC-03 真实选择器对照

UID1001取得恰好一个目标SVID；UID1002实际连到同一接口且因无匹配身份拒绝、0SVID。记录取证/签名进程UID、PID、命令、socket模式及登记选择器。只证明受信任容器内UID边界；不得写成精确可执行文件、企业或硬件证明。

### AC-04 持有与原消费

SVID私钥不离开UID1001私有目录；签名也在UID1001。规范载荷见RUNTIME_PROTOCOL.md，包含nonce、Agent、Provider、Executor及issued_at。原verify_x509_svid_credential_possession返回VALID及四项true。证书的URI、EC公钥、有效期、非CA/KeyUsage、叶直接由管理根签名由Evaluator独立复算。只拿到证书不算通过；仅项目脚本宣称VALID不算通过。

### AC-05 反例与身份/授权边界

以同一次实际正例逐项改一个量：错误管理根、错误trust domain、错误Agent、错误Executor、错误Provider、nonce绑定变化、签名损坏、重复nonce、挑战过时、证书过期观察，共10项；具体原因见NEGATIVE_ORACLES.json。0项VALID。过期用明确的模拟观察时间，不伪称墙钟等待/实际撤销。原identity_assurance回归证明凭据不能覆盖无效/撤销的授权基础。全包真实支付回调0，网络支付0。

### AC-06 必要回归

原credential_possession/identity_assurance、H74R的16项上下文测试及原Stripe19、安全9、业务74回归全部通过。真实新证据不替代原断言；不得改测试继承、覆盖unittest.fail或更改原方法。

### AC-07 清理、成本和证据连续性

各次运行有唯一ID、依赖与操作顺序、命令退出/失败阶段、消耗次数及可得字节（未取得则UNKNOWN）；尝试账本追加且失败也消费次数。结束前本包容器0/密钥导出0/宿主环境修改0，清理有独立Docker ID检查，原其它容器不动。实际主动分钟UNKNOWN时保留UNKNOWN；记录完整工作窗，**无主动分钟/制包墙钟上限**。Docker内部HTTP和主机网络字节不可观测时明确UNKNOWN，不伪称0或完整字节上限。

### AC-08 统一提交与独立复核

按冻结Validation Plan运行公共L2，全部通过才SUBMITTED_FOR_REVIEW；REPORT/SUBMISSION/引用证据完整且哈希一致。Evaluator保存接受快照，再同计划独立L3；L3新根/nonce/原始产物与L2不同、原接受文件不变。逐AC二元判定、任务结论、项目影响和CONTINUE/STOP/SWITCH分别记录。结构门禁或文档完成不当能力通过。

## Allowed scope / 可修改范围

可新增/修复本任务RUN.py、WORKLOAD.py、Dockerfile、任务内测试、运行/派生材料、REPORT.md、SUBMISSION.json、ATTEMPT_LEDGER.jsonl及evidence/、runtime/。CHECK.py、BOOTSTRAP.py、CONTRACT、VALIDATION_PLAN、RUNTIME_PROTOCOL、NEGATIVE_ORACLES、ASSET_LOCK、BASELINE、FREEZE均为Evaluator冻结文件，只读。CURRENT仅本任务状态/角色/授权与动作路由；最终地图仅Evaluator按证据更新。

全部src/、原tests/、旧任务/公共工具只读。共享Python、PATH永久设置、Docker配置、别人的容器/镜像不得更改。不新建通用Adapter/Runtime、数据库产品表、轮换/撤销体系或额外支付平台。

## Cost and bounded repair / 成本与包内修复

负责人要求不自设工作时间上限，本包不设主动分钟或整窗到点停止。记录测得/估计/UNKNOWN，不用上轮旧额度。估计工程成本中等、无新增模型API/付费服务，实际兼容性置信度低，正是测量对象。

Bounded retry / iteration budget: 单路线；最多2版任务运行实现、2次正式L2、1次正式L3、1次可选L1真实运行；真实容器总启动≤4（含失败）。匹配取证每运行最多3次（仅启动同步/临时接口不可用可重试）；不匹配请求每运行1次。成功充分后不增加Case或运行。不得绕过零容忍反例继续重试。

资产传输：4固定文件各≤2次，总文件尝试≤8，按收到字节逐块计数，总原始文件body≤160MiB；SHA/长度不符不能重试换资产。Docker只允许所锁定一个基础image、最多2次pull，image/layer声明压缩量约45.4MB，Docker实际传输量UNKNOWN；总量约120MB、重试约240MB为估计，不作为已测硬上限。registry认证/manifest由Docker处理，不声称HTTP总数；其它下载0。构建≤2次，仅本地固定文件且network=none。

Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 一个真实匹配正例+一个接口级拒绝对照+10个消费负例/每正式运行
Max total attempts: 4 actual containers
Max parallelism: 1
Max attempts per unit: 3 matching fetches, 1 nonmatching fetch per run
Retryable failure families: startup synchronization, transient public transport before complete asset; no hash drift/security/profile relaxation
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1/ATTEMPT_LEDGER.jsonl

技术防挂超时仅用于回收进程：单外部命令≤180秒、单容器≤20分钟，超时计失败并清理；它不构成总体任务计时上限。不得因到点换ID续期重试。资源：单容器≤2CPU、1GiB内存、128PID，tmpfs≤256MiB；无云服务/付费API/真实资金。清理不受失败次数耗尽限制。

## Validation plan

Validation plan file: docs/05_任务交接/H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1/VALIDATION_PLAN.yaml

| VP | 内容 | AC |
| --- | --- | --- |
| VP-01 | 权限、冻结、基线 | AC-01 |
| VP-02 | 实际全流程，L3重新发行 | AC-02, AC-03, AC-04 |
| VP-03 | 独立重算公共产物及10反例 | AC-04, AC-05 |
| VP-04 | 原身份/上下文/支付守护回归 | AC-06 |
| VP-05 | 无私钥产出、资源清理、次数账本 | AC-07 |
| VP-06 | 冻结/证据结构与原字节保护 | AC-01, AC-08 |

入口：`python -B <task>/BOOTSTRAP.py --mode executor`；独立复核用`--mode evaluator`。固定本机agent解释器只在进程内配置，绝不安装宿主包。RUN.py的唯一待实现义务是合同内任务测量脚本，不是未决产品方案。

## Authorization / 已获项目负责人运行授权

本合同技术内容完整。项目负责人于2026-11-16T11:59:25Z明确授权直接执行H76、完成后统一交Evaluator评估；AUTHORIZATION.md保留原话和具体运行范围。旧“先保留暂不运行”原件不改，当前授权取代其运行暂停决定。Evaluator不事前介入，Executor不自行宣布PASS。

- reference_read: true（公开来源元数据）
- artifact_download / container_dependency_install / local_service / ephemeral_test_credentials: true（本次负责人明确授权，详见AUTHORIZATION.md）
- host_install / api_call / browser / test_payments / commit / push / history_rewrite: false

本次已按负责人授权做一次性元数据收口：保留references/before_owner_run的获批前原件，合同状态改为CONTRACT_FROZEN，路由改为EXECUTING/Executor并更新四项运行权限，重生成FREEZE技术摘要；不改变AC、预算、资产、步骤或权限语义。评估者仅在执行者交付后统一独立复核。不得主动启动任意其他WSL发行版、不安装/升级Docker；必要时启动已有Docker Desktop可能连带其自有backend。

## Stop and next decision / 停止及下一步

环境资格失败、资产不符、原回归失败、计数耗尽、证据不足、私钥越界、错误身份被放行、需产品修复/新权限均停止并提交事实；不把INPUT_LIMIT写成已证明机制失败。正常拒绝消费负例不是零容忍反例。零容忍错误放行单独保留并立即回Evaluator。

全部AC通过→真实受控发行来源代表切片可记IMPROVED，但E整体仍未关闭，停止继续堆同类Case。若测出稳定兼容缺口→据实重排B-15后冻结最小修复，禁止Executor顺手改验证器。若只缺环境→INPUT_LIMIT，优先解决具体环境条件，不自动切平台。真实组织身份、长期轮换、硬件密钥、用户强认证、生产网络仍是未来独立阶段。

## External requirement impact / 外部指标

profile=PCAC-AGENTPAY。PCAC-03/05（CORE）：仅Agent凭据/链路引用窄切片；PCAC-06（CORE/ADAPTER）：受控发行来源；PCAC-12/15/20（CORE）：证据关联、私钥最小化、上线前独立评估。before：本地固定合成证据M2；target after：本切片经L2/L3后M3，**不是整项PCAC成熟度升级**，未通过保持before。PCAC-07/08授权/付款意愿为不扩权守护，不新增成熟度。对象=登记/根/叶/挑战/nonce；代码=既有credential_possession和identity_assurance；Test=VP-02/03/04；Evidence=实际发行、接口拒绝、原验证器事实及独立L3。残余：管理引导人为受信、root可管理密钥、UID不等于程序身份、无机构/KYC/轮换/撤销/用户强认证/监管合规结论。
