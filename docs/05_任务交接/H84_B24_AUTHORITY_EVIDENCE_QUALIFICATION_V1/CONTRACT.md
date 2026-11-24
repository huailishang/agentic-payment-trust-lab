# H84 付款使用时点的来源证据资格测量

Task ID: H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1
Task kind: evaluator_design
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: 69a0512d9b4235b01acec173765a35ab2939f827
Dispatch mode: SINGLE

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-24-r141
Active bottleneck: B-24
Hypothesis: H-84-B24-AUTHORITY-EVIDENCE-QUALIFICATION

A–D 本地代表闭合，E 当前 B-24，F 受授权约束。H78 实际 SPIRE 来源已独立验收，H83 本地 WebShop 资格已验收，六组86项回归。真实消费状态/可信时钟/调用责任仍未知。本轮只测量同一工作负载在受控来源资格变更前后的实际状态和模拟付款身份等级，不改产品。B-06 额外渠道与 B-20 幂等不能补齐该证据。预期范围一条路径、一次变更；无实际来源变化则保留 UNKNOWN，停止扩例。
原草案与原路由保留在 evidence/preparation。负责人授权原话见 AUTHORIZATION.json，S0 实际核验见 evidence/preparation/S0_ASSET_PREFLIGHT.json。H83 的已验收产品差异是本轮基线，不是本轮改动。

## Single objective / 唯一目标

固定已验证的 SPIRE 1.16.0、隔离 UID1001、原签名验证器和 WebShop 入口。测量一次删除本次新登记前后同一工作负载来源状态，关联两次模拟付款，观察 VERIFIED 是否降为 BOUND。保留原付款准入：BOUND/ALLOW/1 本身不是漏洞。测试驱动是受控动作/来源/时点关联责任方，不代表生产可信授时、旧证书全局吊销、用户撤销或生产调用边界。签名挑战本身未签订单；订单摘要与挑战关联属于受控测试证据。

## Acceptance criteria / 验收条件

| AC | 必须观察到的结果 |
|---|---|
| AC-01 | 原HEAD、冻结/保护清单保持；锁定归档和两个成员摘要、既有 WSL、本轮授权一致；只允许 H84 任务文件和路由变化。 |
| AC-02 | 正常同UID获取 SVID、签名与原验证器 VALID、同次动作关联、WebShop VERIFIED/ALLOW/1；保存证据。 |
| AC-03 | 仅删除本次隔离登记一次；同UID同socket在90秒观察窗、至多12次探针内得到明确 PermissionDenied/no identity issued，非连接失败；旧证书在记载有效期内。相同订单摘要、授权与隔离模拟状态，新动作时点不给旧Fact，WebShop BOUND/ALLOW/1。无明确来源拒绝为 UNKNOWN，停止。 |
| AC-04 | 历史样本离线接线对照、原六组86项零跳过回归；无误晋级、异常回调；清理本轮所有归属进程与tmpfs，无公开私钥，原始命令和索引可复算。 |
| AC-05 | L2 四条强制检查完整三件套，提交冻结快照，评估者独立一次L3（独立新隔离运行）；不得把离线样本当现场变化或自签PASS。 |

## Allowed scope / 允许范围

只允许本任务的冻结材料、实验脚本、证据、报告、提交快照和根CURRENT路由。禁止改动产品/原测试/原样本/历史任务；保留其他既有工作区变动。来源复用 H78 WORKLOAD.py 已验收字节，经 PREPARE.py 可复现生成本包采集器，修改仅为本轮门禁、同 UID 后观测、调用测量与移除不相关 UID。保留原防泄漏和归属清理机制。
## Exclusions / 明确排除

沿用本合同既有允许范围及授权限制：不修改产品、原测试、原样本或历史任务；不进行真实付款、外部 API、外部测试支付、安装、下载、Git 提交、推送或历史改写。不将隔离来源发放资格变化解释为旧证书全局吊销、生产可信授时或用户授权撤销。本节仅补齐结构校验要求，不改变原合同范围、权限、AC 或预算。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/VALIDATION_PLAN.yaml

VP-01 冻结和基线，VP-02 离线历史样本（不是现场），VP-03 原回归，VP-04 现场。公共 runner 以现有 /usr/bin/python3 执行。候选脚本语法、离线接线和86项回归已于冻结前通过，正式门禁独立重跑。任何前置失败不进入现场。L2 成功提交后评估者接受快照，独立 L3 使用 evaluator_command。

## Authorization / 授权

负责人 2026-11-24 14:29 +08:00 明确授权本轮既有 WSL、隔离 SPIRE 服务、临时测试凭据与本次隔离登记调整。见 AUTHORIZATION.json。仅本机回环、独占socket与私有tmpfs；真实资金、外部API、测试支付渠道、下载、安装、Git提交推送改写全为零。服务/凭据的旧任务授权不继承。

## Cost and stop conditions / 成本与停止条件

每角色最多一次正式门禁、一次现场观察窗、一次隔离发行根/Server/Agent各一次、一次登记创建与一次删除。原 H78 同UID初始取证最多3次就绪重试，单次签名；删除后90秒、最多12次同UID观测，间隔至多5秒；明确拒绝即止。现场采集继承1100秒看门狗和归属清理。主动上限执行者120分钟、评估者60分钟；正式单角色墙钟上限30分钟；不追加发行或重启。冻结前候选脚本调整一次，连接失败不当作成功也不擅自重开已登记现场尝试。源漂移、权限变化、误晋级、回调异常、清理失败或不明状态即停止。实际费用、主动时长未知如实记录。
## External requirement impact

Profile PCAC-AGENTPAY，PCAC-03/05 CORE，PCAC-06 CORE/ADAPTER：before/after 保留原 H83 本地证据，不提高生产成熟度；本次 Test 为同UID实际来源变更和消费者对照，Evidence 为原始脱敏命令、签名与动作记录、L2/L3。PCAC-09/12/20 原授权、回归、完整性守护不变。PCAC-10 用户撤销、旧证书全局吊销、轮换、可信授时与生产责任仍未知。
