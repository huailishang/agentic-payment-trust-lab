# H83 WebShop 付款时点身份凭据资格

Task ID: H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Branch: main
Baseline HEAD: 69a0512d9b4235b01acec173765a35ab2939f827
Dispatch mode: SINGLE

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-23-r140
Active bottleneck: B-24
Hypothesis: H-83-P3-AUTHORITY-SOURCE

项目要证明高风险 Agent 付款的授权、身份、交易绑定、执行治理、恢复和审计可以独立复核。A–D 的本地代表阶段已关闭。当前 E 阶段验证付款时点的身份事实，F 的外部接入仍受授权约束。B-24 首先影响付款使用时点的身份等级。B-06 额外支付网络和 B-20 工具幂等方向均无法补齐该证据，本轮优先复用已有来源和 WebShop 入口。

Metric baseline: H82 证明共享 P3 在消费者输入未变时保留合成 VERIFIED，仓内 WebShop 调用未传凭据 Fact。H83 制包预检使用 H78 已签收公开证明，7 个公共输入摘要相符，复算采集时点为 VALID。同一 WebShop 模拟订单经未改入口为 BOUND / ALLOW / 1 次测试回调。原六组 86 项回归通过、零跳过。预检原始证据见 `evidence/preparation/PRE-01.*` 和 `PRE-02.*`。

Estimated affected scope: 本地 WebShop 一个入口及其 P3 调用，产品候选改动一个文件，既有用户授权、付款准入、来源验证和旧回归均沿用。
Expected project impact: 受控路径新增可观测的使用时点认证资格。同一入口接收合格的当次事实可给 VERIFIED，接收旧事实不会从 BOUND 晋级。原入口不存在已测出的错误 VERIFIED，不能把缺少接线的基线说成已发生错误放行。真实发行者实时撤销、轮换、时钟和生产部署仍为 UNKNOWN。
Rollback condition: 证据锁、正对照、付款回调、既有策略或测试有任一漂移，停止并保留 diff，由评估者决定是否撤销该单文件实验。

## Single objective / 唯一目标

在本地 WebShop 正常结账函数与共享 P3 的接缝处，接收**受信调用边界提供的、当次验签产生的身份凭据事实**，只将该动作时点有资格的事实送入原 P3 晋级。实验假设是一次明确的时点检查能在同一入口保留合法 VERIFIED、排除历史事实误晋级，同时保持已有的付款准入。

- 增加两个可选的 keyword-only 输入 `credential_possession_fact` 和 `credential_use_at_epoch`。前者为现有 `CredentialPossessionVerificationFact`，后者为可信执行边界为本次动作固定的整数 UTC epoch 秒。受控测试驱动是本轮唯一资格来源。测试用 H78 公共证据原字节在历史观测时点重新验签，模拟本次执行现场出具事实。应用调用边界需独立提供动作时点，产品函数不得从 Fact 自身、交易请求时间、网页、用户字段或字符串回填。
- 只有原生 Fact、有效整数时点且 `observed_at_epoch` 等于本次动作时点才转交原有 P3。两个时点都须是正整数，排除布尔、缺失和其他类型。该约定对应同一动作复用的一次固定观测，避免两个调用各采一次系统时钟。照常使用现有 P3 的主体、提供者、执行者、凭据引用、撤销标志和密码学结果语义。快照时点一致只能支持本地实验的输入资格，真实状态、发行者可信度与调用边界保护仍需另证。
- 缺失 Fact 时沿用原调用。若有 Fact 但类型错误、时点缺失或无效、时点不匹配，不传该 Fact 并分别记录 `webshop:credential_fact_invalid_type`、`webshop:credential_use_time_missing_or_invalid`、`webshop:credential_use_time_mismatch`。类型与时点两者都不合格时先判 Fact 类型。仍由原 P3 决定身份等级和是否付款。若基础身份已撤销，原 P3 的 DENY 优先。
- 同一固定订单、委托和 P1/P2/P4 上下文保持一致，执行者用捕获时点 +1 秒作为不匹配对照，独立评估用 +301 秒并额外查早于观测 1 秒。H78 原始凭据来自已归档的历史实验，使用参考时点 1794903858，实际调用回调只是测试计数。相符时点不声称发现生产撤销。该包接受 BOUND 按原规则付款。

## Acceptance criteria / 验收条件

| 条件 | 必须观察到的结果 | 证据 |
| --- | --- | --- |
| AC-01 来源与范围 | 28 份保护文件 SHA 一致，基线及治理快照锁定。H78 记录时点复算 VALID，已验证的 Agent/Provider/Executor 三元组确实进入测试。产品差异只在允许的 WebShop 文件 | VP-01/02，预检、原始 EV 与实际 diff |
| AC-02 当次身份保证 | WebShop 调原 P1–P4，合格 Fact 在同次动作时点晋级 VERIFIED，ALLOW 且一次测试回调。原路径省略两个新输入仍为 BOUND、ALLOW、一次回调 | VP-02，同一业务输入的前后观测 |
| AC-03 历史及缺失证据 | 历史 Fact、无可信时点、无效布尔时点、字典伪 Fact 均不晋级，原准入仍为 BOUND / ALLOW / 一次测试回调，原因明确。独立 L3 额外验证未来观测不会晋级 | VP-02，身份等级和最终决定分别记录 |
| AC-04 安全守护 | 原基础身份 revoked 仍为 DECLARED / DENY / 零回调。原 P1/P2/P4、确认和已知成功交易防重等回归真实通过。旧用例与断言保持 | VP-02/03 |
| AC-05 独立复算 | 六组原 86 项通过、零跳过。L2 五条 AC 对应三条 VP，保存完整原始三件套和成功/失败账本。评估者用冻结命令独立复核同一快照，逐项裁决并分别记明本地收益与真实来源 UNKNOWN | VP-03、完整 L2、独立 L3 |

## Allowed scope / 允许范围

- 只修改 `src/agentic_payment_experiment/webshop_runtime_gate.py` 一个产品文件。原数据模型、共享 P3、凭据验证器、Stripe、外部渠道、原测试和原样本全部保护。冻结的 `CHECK.py` 承担本包新验收，原 86 项运行命令见计划。
- 可写本任务的 `REPORT.md`、`SUBMISSION.json`、`ATTEMPT_LEDGER.jsonl`、`evidence/l2` 或 `evidence/l2_retry_02`，及独立的新执行日志。不可改 `evidence/preparation`，不可写 `ACCEPTED`、正式 L3 或 `REVIEW.md`。CURRENT 只允许按工作流记录进入 EXECUTING；评估者验收提交后转 READY_FOR_REVIEW。
- 其他已有工作区修改留在原位。初次执行核 `FREEZE.json` 摘要与路由，再核冻结文件、来源、原 HEAD 和单文件范围。保存 diff 与实际 SHA。工作区基线相同即可复算。

## Exclusions / 明确排除

仅在离线、可计数的测试回调中验证。真实付款、外部网络、服务、下载/安装、新凭据及私钥、Git 提交/推送/改写均无权限。不得接入真实价格源、调度服务、重试队列、凭据撤销服务或全局强制 VERIFIED。用户委托撤销是独立后续业务边界，当前包仅保护原委托有效期与确认策略，不替代 PCAC-10。

## Validation plan / 验证计划

Validation plan file: docs/05_任务交接/H83_P3_AUTHORITY_SOURCE_QUALIFICATION_V1/VALIDATION_PLAN.yaml

| 顺序 | 运行和决策 |
| --- | --- |
| S0 来源与基线 | 现有 Windows Conda `agent`，确认 Python 3.11+、PyYAML、cryptography。先验证冻结清单并运行原 WebShop baseline 对照。失败保留且 STOP |
| S1 限定实现 | 一个文件接入两项可选参数；先跑定向行为和原回归。若基线或非预期业务准入发生变化，停下检查范围 |
| S2 提交 | 用公共 v2.2 runner 串行运行 VP-01–03。首次成功即提交。首轮失败仅可按本合同做一次同范围修复/环境修复，保留第一轮原件 |
| S3 评估 | Evaluator 接受未变快照后使用冻结的 evaluator_command 完成唯一 L3，保留更换时点对照，逐 AC 签收 |

## Authorization / 授权

依据负责人要求制定执行包，冻结**本地单文件受控变更和离线验收**。现有 Conda `agent` 为已验证入口。当前网络、Git、安装、服务、WSL、浏览器、凭据发行/获取及测试/真实付款授权均为 false。新增权限只能由负责人明确授予。

## Cost and stop conditions / 成本与停止条件

- 串行，单一入口。最多 2 次登记实现、每次最多 1 轮聚焦行为检查、最多 2 次正式 L2 和 1 次独立 L3。每方旧测试首个正式门禁 86 项，准备阶段已跑一次并单列。执行阶段的 CPU 与墙钟、实际主动时间和失败重试据实记账。外部请求、费用、服务和真实付款均为 0。
- 源或路由漂移、首个基线失败、正对照退化、历史事实晋级、回调异常、尝试超限、需要额外文件/权限、出现不能在合同内解释的零容忍反例，立即停止，保留原始证据。
- 首次 L2 全过即停止执行迭代。独立 L3 通过后，只有本地具备可复现受控收益才完成 B-24 此切片。若下一目标是延后付款必须 VERIFIED 或取消委托后阻止付款，先取得该入口的明确业务规则与可信状态输入，再冻结后续包。

## External requirement impact

Profile `PCAC-AGENTPAY`。PCAC-03/05/06 从历史、接口证据候选推进至一个本地消费入口的使用时点资格证据，目标为受控用途。Test 为相同时点、历史时点和独立变体，Evidence 为 H78 公开证明摘要、WebShop 测试观测及 L2/L3。PCAC-09/12/20 保持原授权边界并记录原回归与证据完整性。PCAC-10 用户撤销仍为缺口。实际发行方状态、轮换、真实身份供应者和生产效力保持 UNKNOWN。

## Amendments

无。原草案及原路由保存在 `evidence/preparation`。
