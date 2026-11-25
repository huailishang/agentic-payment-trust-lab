# H90 整份委托停止的本地跨操作执行

Task ID: H90_STORED_MANDATE_SHUTDOWN_V1
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-25-r149
Active bottleneck: B-26
Hypothesis: H-90-STORED-MANDATE-SHUTDOWN
Metric baseline: H89 L2/L3 各 6/6，12 行同库业务关系独立复算，A/B 合法单次撤回各只阻断目标。整份停止表示 0，受理后行为不可判定。H90 制包同输入正常控制 A/C/D 各创建一次，已建 B 查询和模拟点击各一次。
Estimated affected scope: 一个受信任的本地调用方，一个 SQLite 账本，两个既有 stored 入口，三种同委托业务状态及另一委托对照。
Expected project impact: 可受理整份停止表示 0→1，同键 A/B/C 受理后在副作用前明确 DENY，D 与旧历史保持。
Rollback condition: 错主体或错版本受理、读不到可信事实仍放行、已受理后副作用、历史漂移、对照失败或新增外部权限时停止并保全证据。

A/C/D 已有本地代表性证据，B 的单次确认撤回保持关闭。B-26 缺的是共同接收和按委托键读取，H89 已在两个独立业务状态定位。B-24 缺实际消费者逐次证据，B-20 人工延期。在途顺序、已签发凭证失效和预算预占分别有独立因果变量，等本次建立可验证的停止事实后再排。E/F 的真实认证、渠道与采用边界沿用当前地图。

FluxA 的借鉴用于写清约束由谁执行和拿什么证明生效。这里只使用已归档的产业对照及项目自身证据。控制事实由账本受理，既有执行门禁负责拦截，证据将两者通过停止事件引用和操作快照摘要连接。

## Single objective

引入一种本地持久化的整份委托停止事实。事件在账本提交后，两个既有 stored 入口从原快照推导同一委托键，匹配时在 provider 创建、GET 或模拟付款前返回原生 DENY。H89 的三种同键状态 A/B/C 都受约束，D 与历史路径行为保持。

## Frozen behavioral contract

- `record_mandate_shutdown(anchor_operation_id, *, expected_sha256, subject_ref, mandate_id, authority_version, event_id, received_at)` 由既有受信任本地控制边界调用。核对原操作、已验不可变快照、原用户、委托 ID 和版本。入参用于绑定，调用方负责提供可信主体。生效键为 `(subject_ref, mandate_id, authority_version)`，锚操作及快照仅用于证明原绑定。时间应带时区且不早于锚快照登记和原确认，标准化 UTC 作证据。SQLite 提交划定顺序。
- `get_mandate_shutdown(operation_id, *, expected_sha256)` 从该操作的已验历史快照推导键并验证停止事实及原锚。不同操作查询同一事实时回同一回执。无匹配、且状态可信时返回 `None`。公开最小回执字段为 `event_id, subject_ref, mandate_id, authority_version, anchor_operation_id, anchor_snapshot_sha256, received_at, source`，来源固定 `LOCAL_USER_CONTROL`。新表 `mandate_shutdowns` 以生效键与全局唯一事件 ID 保证同一事实，提交事务完成校验、冲突处理和写入。
- 完全一致的同事件重放返回最初回执。相同键的第二事件、同事件字段或锚变更、跨键事件 ID 复用均拒绝。坏输入、坏锚、坏绑定、不可读查询均按失败处理。验收在临时库模拟查询不可用以及匹配停止事实的锚摘要损坏，任何返回或受控异常都须在副作用前拒绝。
- 已停止同键的 A 尚未创建、B 已有会话未付、C 提交停止后才登记并保存新业务快照，均由创建或付款的现有门禁返回 DENY，回调 0。C 保存快照服务于留证，实际准入在执行入口。D 是同用户另一委托，保持正对照。验收时保持 A/B/C 原生业务状态与原批准记录。未匹配停止仍由 H88 单次撤回门禁及原控制负责。
- 原图和 H88 单次事件继续可回查。旧 schema 增量初始化，历史已付恢复保持 `RECOVERED` 且无新增支付。动作开始后的竞争窗口留给后续验证。停止前已有的已付事实和历史证据仍可读取。

## Acceptance criteria

| AC | 独立可判定结果 |
| --- | --- |
| AC-01 | HEAD、H88/H89 终验及冻结保护项保持，产品差异限制在两个指定文件。 |
| AC-02 | 舍弃无效输入，原用户/委托/版本/锚摘要及时间绑定成立。合法事件返回最小事实，重复同事件同回执，三类冲突拒绝，另一委托无停止事实。 |
| AC-03 | 独立临时库重开后，A/B/C 均 DENY、回调 0、创建/GET/模拟付款增量 0，三行均可回指同一事件；后登记的 C 按同键读取停止事实。 |
| AC-04 | 无停止路径与制包基线一致，D 隔离保持；匹配事实的锚摘要失配或查询不可读，两个门禁均无副作用。 |
| AC-05 | 原快照字节和批准状态保持，旧 schema 正常迁移，H88 单次隔离和错误拒绝保持，已付历史恢复无支付增量。 |
| AC-06 | 原 124 项零跳过，较早任务的源及运行证据不改，临时库清理成功。 |
| AC-07 | 统一提交两侧原始矩阵、事件/操作/原快照关联、源差异及摘要、运行三件套与成本账本。评估者接受同一快照后独立 L3、逐 AC 裁决。 |

## Execution package and dependencies

| 步骤 | 交付证据 | 继续或停止 |
| --- | --- | --- |
| S0 核基线 | 原生 Windows Conda agent Python 3.12、冻结输入、同一 H89 业务正对照及既有差异。 | 通过进入 S1；仅本进程 PATH/编码可恢复，锁错立即停止。 |
| S1 解决最难接收点 | 在既有账本增加一种绑定停止事实及事务，测输入、幂等、冲突和重开读取。 | 受理结果可复算后进入 S2，错绑定受理立即停止。 |
| S2 接通既有消费者 | 两个 stored 入口使用同一停止事实和原生拒绝结果，确认执行位置位于首个外部替身动作前。 | 同一事实可回查后进入 S3。若需其它模块或新授权，交 Evaluator。 |
| S3 后登记与隔离 | 固定 A/B/C/D 两个分支，复现无停止与已停止、重开及未来动作，交行为矩阵。 | 同键前置拒绝、D 隔离成立后进入 S4。受理后有副作用立即停止。 |
| S4 状态损坏守护 | 丢失读取能力或锚摘要不一致时两入口均前置拒绝。 | 通过进入 S5。读取失败仍放行即停止。 |
| S5 历史与业务保全 | 核原图、旧库增量初始化、已付恢复和 H88 单次撤回守护。 | 保持后进入 S6。历史漂移或恢复重扣风险即停止。 |
| S6 完整回归 | 跑原 124 项、核保护清单和临时清理，生成最小责任与证据对应表。 | 通过进入 S7。冻结测试失败保留原证据。 |
| S7 统一交付 | 公共 L2、原始输出、成本与提交快照。 | L2 PASS 统一提交。可恢复环境、证据或普通合同内缺陷可作一次范围内修正并重跑。 |

S0→S7 前置满足自动继续，末尾一次提交。公共 runner 会继续后续固定检查，每条均前后核锁。发现零容忍反例时保全该轮所有原件并停止候选修复。Evaluator 做独立 L3 和语义复核。

## Allowed scope

产品只允许 `src/agentic_payment_experiment/stripe_checkout_lab.py` 与 `src/agentic_payment_experiment/adapters/stripe_checkout.py`。本任务 REPORT、SUBMISSION、运行证据、只增账本和标准路由元数据可写。冻结检查器、父任务、既有回归、地图和其它源码均只读。证据只使用合成操作标识、事件引用及摘要，临时库随测试清理。

## Exclusions

本地受信任控制调用与合成账本是唯一边界。真实用户认证、实时竞态中止、旧支付凭证失效、渠道撤销、退款、累计预算、外部适配器和真实资金分别待证。网络、服务、浏览器、WSL、下载、安装、凭据、模型接口以及 Git 提交、推送和历史改写均无授权。

## Validation plan

Validation plan file: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/VALIDATION_PLAN.yaml

S0 的启动前命令为 `python -B docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/CHECK.py baseline`。正式六检查分别覆盖接收、传播、损坏路径、历史、原回归和保护，现有运行器顺序执行。L3 在独立进程创建新临时库，复跑冻结 argv，人工核代码中的执行责任、排序和完整证据链。对照采用本任务制包基线的同一 H89 输入角色、时间、原生动作及摘要。

## Authorization

负责人要求复核后继续推进，并要求将同目标必要步骤纳入较长包。继续授权限本地既有实验和冻结范围，全部附加权限为 false。

## Cost and stop conditions

最多两版实现、两次正式 L2、一次独立 L3，总预算包含所有失败尝试。第二版只用于普通合同内缺陷、环境或证据修正，前述零容忍条件必须先交回 Evaluator。盲目增加案例、调整 AC、扩大文件或重置预算均需新冻结。估计中等本地成本，执行和复核约 90–180 分钟用于排序，记录实际命令时间和角色墙钟，不可知的主动时间写 UNKNOWN。外部运行成本为 0。三状态和原守护独立通过后可停止本地同类扩展，再比较凭证消费、竞态和真实控制来源。失效假设或证据不足则 STOP/SWITCH。

## external_requirement_impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-10, PCAC-12, PCAC-22]
  applicability: CORE
  maturity_before: M1
  maturity_after: M4
  maturity_scope: 仅整份委托在受信任本地控制方及两个既有 stored 入口的代表切片目标，M4 取决于独立终验
  test_evidence: [AC-02, AC-03, AC-04, AC-05, AC-06]
  trace_evidence: [VP-01, VP-02, VP-03, VP-04, VP-05]
  residual_risk: [真实控制主体, 读取后竞态, 旧凭证失效, 渠道级撤销, 一键关闭界面, 累计额度]
```

PCAC-10 是主项。PCAC-07/09/12 为绑定、门禁和证据守护，PCAC-22 仅引用停止语义。成熟度仅针对验收切片。
