# H47 冻结执行包：外部商家交易链适用性与交付切口串行测量

Task ID: H47_UCP_COMMERCE_APPLICABILITY_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H47_UCP_COMMERCE_APPLICABILITY_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-15-r75
Active bottleneck: B-17
Hypothesis: H-47
Measurement status: 官方完整商家应用离线可运行与部分签名/幂等行为 measured；完整矩阵、现有产品忠实映射及商业需求 unknown。
Metric baseline: 准备检查 `[401,400,201,200,200]`；同键重复完成只有 1 个订单、1 次模拟处理、库存 5→4；确认保留数量 1 后原生更新数量 2 可行。正式 9 条路径重复测量尚未执行。
Estimated affected scope: 一个固定 UCP Python 商家、九种脚本条件各重复两次、17 项字段/机制适用性、3 个公开团队工作流；不是市场覆盖率。
Expected project impact: 给出可复核的接入适用性和下一预算决策；one_off，不预承诺产品能力改善或客户成立。
Rollback condition: 有效不支持/无增量结果保留，不通过改源码、确认、签名策略或检查器求通过。

目标是证明智能体交易从授权到恢复和审计可信。A–D 已完成，E 在本地代表性边界完成，F 当前。B-17 优先于重开本地已关闭能力；H46 已停止，银行任务不适配不能成为无限扩建理由。支付宝 B-06 与金密杯继续 Human 后置，支付宝支付马拉松不成为本包前提。相比立即写 UCP 适配器，本包先确定业务语义及原生保护能覆盖什么；相比继续检索更多商城，已固定候选可以直接测量。

Human 已要求评估后形成较长串行包，整包后统一评估。阶段间不等 Evaluator 签字；允许修复本包驱动/材料，发现产品缺口只记录，不改核心。改变假设、冻结辅助代码、权限或预算时才硬停止。

## Single objective / 唯一目标

用完整固定商家应用的可复跑状态证据、17 项忠实映射和 3 个公开团队工作流，形成一份可执行的下一步判断：最小适配候选、核心语义缺口、无额外价值或环境/证据不足。

本包是 measurement-only（只测量），唯一新增实现是任务内测量驱动；没有产品功能建设，不提前宣称“接入后比原生更安全”。

## 固定来源与运行边界

- UCP samples commit `99724a32da48bd0f4962c83e25f17c8345ce055e`，49 个原文文件，Apache-2.0，见 SOURCE_LOCK.json。选用 `rest/python/server`，不运行维护冻结的 A2A 样例。
- 运行时按固定商家 profile 的 `2026-04-08` 与 `ucp-sdk==0.4.6`，不能误称当前所有 UCP 版本都兼容。
- 完整 app/routes/SDK/service/SQLAlchemy/SQLite/原生签名校验不改。ASGI（应用内部请求通道）代替 TCP 服务；不执行 `server.main`，不监听 `0.0.0.0`，不启动公开服务。
- FROZEN_RUNTIME 是冻结的测试夹具，不是产品适配器。配置 `require_signatures=True`、`allow_insecure_profile_urls=False`；每条路径使用临时密钥、独立临时 SQLite。固定虚拟 profile 通过 respx 返回合成公钥与无 webhook 配置；DNS 仅为夹具返回固定公网形状地址，不发查询。除 Windows asyncio 标准库内部 socketpair 唤醒连接外，应用 TCP 连接被阻断。
- 仅 `mock_payment_handler` 与 `success_token` / `fail_token`；不存在真实卡、真实商户凭据、支付服务方调用或资金。
- 请求签署使用上游 helper，校验使用原生 middleware；只证明该夹具下原生检查实际运行，不是独立密码算法认证或生产身份验证。
- 明确合成授权：用户在实验中仅确认 fixture 商家的一朵 rose，USD 1000 个最小货币单位；初始真实 checkout 返回作为用户同意的固定快照保留。后续更改不重建确认。商家 endpoint 是实验身份，不是已认证真实商家/收款人。
- 三个团队 README 和 LICENSE 已固定于 TEAM_SOURCE_LOCK.json。只作工作流/既有保护/需求假设研究；没有客户痛点、预算或购买证据。
- `.task_envs/H47/.venv` 已由 Evaluator 准备、准备检查通过。requirements.lock 含哈希；ENVIRONMENT.json 固定实际全部包版本。系统 Python 未修改。Executor 不安装、升级、运行 uv sync 或重新解析锁；环境丢失即停止，不能换 WSL/新 Python 求通过。未安装生成器与 CLI extras，因为使用已生成路由和内部请求通道，不执行代码生成/CLI 服务。

## 串行阶段与产物

| 阶段 | 工作 | 继续与停止边界 |
|---|---|---|
| S0 保护检查 | 核对实际 HEAD、继承 dirty 工作区、原文哈希、既有隔离环境 | 漂移或缺包立即 BLOCKED，不自行重建来源/环境 |
| S1 来源与原生边界 | 读源代码，审计签名、结算、状态、幂等、查询、外部 profile/webhook 行为 | SOURCE_AUDIT；对原生已解决项如实记账 |
| S2 九路径测量 | 实现 MEASUREMENT.run_case，按固定步骤驱动完整 app，九路径各重复两次 | 原生不符合预计但证据有效时记差异；不改商家或冻结夹具 |
| S3 语义与执行接缝 | 填 17 项映射及出处，核对本项目真实类型、付款前控制和证据消费者；记录创建/更新/完成/取消/查询的副作用 | MAPPING.json、SEMANTIC_MAPPING、EXECUTION_SEAMS；只做设计，不能把 checkout ID 当最终 order ID，不能造支付凭证 |
| S4 商业工作流 | 逐个分析已锁定 Filtmall、AgentCard、Henry 的场景和已有保护 | TEAM_SCREENING.json/.md；明确 UNKNOWN，形成三条下一访谈问题，不对外发消息 |
| S5 统一判断 | 比较最小适配、继续原生、换环境/方向，写一次 DECISION 与 LIMITATIONS | 不为形成正结论补模块；安全原生已覆盖就记覆盖 |
| S6 整包交接 | 完整 L2、报告与成本账、中央结构校验，一次提交 | Evaluator 后续统一 L3；不逐阶段评估，不自行签 PASS |

S2 固定条件见 CASE_SPEC：正常；确认后数量改变；同键重复；同键不同正文；完成后新键重试；完整处理后向客户端隐藏响应再查询；模拟支付失败；签署后改正文；缺签名。重复两次是可重复性，不是 18 个独立场景。

“隐藏响应”只在服务完整处理、观察者已取得响应后向模拟客户端返回 None；不是实际网络超时/进程崩溃/任意提交点故障测试。查询结果来自真实持久状态，不从动作预期生成。

“数量改变但请求签名有效”是客户端发出合法签名的不同指令；不是攻击者攻破签名。与固定用户确认不一致只能说明派生业务合同需要对齐，不自动归类为 UCP 官方漏洞。原生状态与预期不同允许写入 source_expectation_matches=false；积极正常/缺签名/正文篡改三条准备护栏必须成立。

## Executor 接口与可观测性

新增 `MEASUREMENT.py`，提供 `run_case(ctx, case) -> None`。按 `case.steps` 顺序调用 `ctx.request(operation, key=..., quantity=..., token=...)`；不打印/返回预填的商家事实，不直接写数据库或改变 ctx、上游模块、付款计数、确认与网络拦截。固定 ctx 独立观察请求、响应、前后数据库与模拟支付处理次数。允许函数内部处理日志，但不能改动作列表。

L2/L3 由独立冻结检查器创建新商家状态、调用执行者驱动并重新读取状态；比较九路径两次的语义摘要。生成 `evidence/measurements_l2.json` 与独立 `measurements_l3.json`，每次另存时间命名原始副本，不覆写前次原始观察。这里是脚本客户端，没有模型运行或自动购物智能体泛化结论。

MAPPING.json schema=`h47-mapping/v1`：fields 必须覆盖检查器 MAPPING_FIELDS 中 17 项。每项含 field、status=`NATIVE/DERIVED/ABSENT/UNVERIFIED`、reason、project_target、source_refs（path/line 指向固定 sources）、observation_refs（测量条目或明确无运行记录）。支持项同时写源 JSON 字段与本项目类型/函数；派生项写转换与信任来源；缺失项解释审计范围，不能借占位值把 ABSENT 升为 NATIVE。是否忠实、控制入口是否足够必须人工 L3 审阅，结构检查不能替代。

EXECUTION_SEAMS 必须分别回答：谁能写、哪些操作持久化/占用库存、核验后到执行时是否可能变化、是否原子绑定版本或交易快照、是否存在绕过通道、只加日志能否达到控制目标。未测并发则明确标未测，不能用一次先读后写宣称竞态已消除。列出拟复用模块和最小候选变更，不实现。

TEAM_SCREENING.json schema=`h47-team-screening/v1`：teams 三项必须与锁定 repo/commit 一致；每项 1–2 段原文短引（8–160 字符）、workflow、existing_controls、unverified_pain_hypothesis、next_question、fit_reason；customer_demand=UNKNOWN、budget=UNKNOWN、contacted=false。先检查已有保护，不能预设对方有重复扣款或授权漏洞。只引用足以说明工作流的必要片段，许可证随来源保留。

DECISION.json schema=`h47-decision/v1`：classification=`BOUNDED_ADAPTER_CANDIDATE/CORE_SEMANTIC_GAP/NO_INCREMENTAL_VALUE/ENVIRONMENT_OR_EVIDENCE_GAP`，reason、strongest_alternative；source_expectation_differences 为测量中 source_expectation_matches=false 的去重排序 case ID 列表（没有则 []）；product_improved/third_party_verified/provider_proof_verified/model_attack_measured/customer_demand_validated/production_authentication_proven 全 false；full_product_gate_comparison=NOT_MEASURED。结论必须能追溯到运行条目和映射行，不能只复述方案。

## Acceptance criteria

### AC-01 — 来源、继承工作区与环境可信

Given 固定 HEAD、锁定源码和包环境；When 运行 baseline 与回归；Must observe 实际保护哈希、全部固定来源/许可和依赖一致、没有包外新文件；Must not observe 修改继承改动、重装或换源；Evidence=VP-01/05、最终文件清单及人工 diff。Mandatory: yes。

### AC-02 — 完整商家真实执行与可重复观察

Given 九条固定动作各两次；When 检查器驱动 MEASUREMENT；Must observe 18 条独立初始状态、原始请求/响应、前后 SQLite、固定确认、实际模拟处理次数及重复一致语义摘要；Must not observe 直接填答案/改 DB/跑片段冒充完整 app；Evidence=VP-02 与原始 JSON。Mandatory: yes。

### AC-03 — 判定不夸大且失败关闭

Given 原生签名和业务状态；When 自检及负例；Must observe 正常可完成、缺签名与篡改被拒、九种材料破坏拒绝；其余原生期望差异如实保留；Must not observe 从全阻断推导安全、把合法签名数量更新说成攻破签名；Evidence=VP-02/04、NATIVE_BASELINE 与人工审阅。Mandatory: yes。

### AC-04 — 语义映射与执行点结论有出处

Given 17 项映射和现有类型/执行控制；When 结构检查与人工逐项审阅；Must observe 字段、来源等级、缺失、转换和最小下一步齐全，TOCTOU（核验与执行之间的变化）和绕过问题单列；Must not observe checkout/order 混同、占位身份/凭证/支付结果升级；Evidence=VP-03、MAPPING、SEMANTIC_MAPPING、EXECUTION_SEAMS。Mandatory: yes。

### AC-05 — 三个公开团队的有据筛选

Given 固定 README/许可；When 检查短引和人工阅读；Must observe 三条真实工作流、已有控制、未证实问题假设与下一问题，需求/预算保持 UNKNOWN；Must not observe 宣称客户、漏洞或成交概率、对外联系；Evidence=VP-03、TEAM_SCREENING。Mandatory: yes。

### AC-06 — 一次性决策与交接

Given 全部测量和审计；When 完整 L2 后提交；Must observe 单一分类、最强备选比较、残余风险、实际成本账与 L2 triplet，回归实际发现测试且通过；Must not observe 产品改善、真实支付、完整模型攻防或外部第三方验收声明；Evidence=VP-03/05、REPORT、DECISION、中央校验。Mandatory: yes。

## Allowed scope

Executor 可新增/修改：MEASUREMENT.py、SOURCE_AUDIT.md、SEMANTIC_MAPPING.md、EXECUTION_SEAMS.md、NATIVE_BASELINE.md、TEAM_SCREENING.md/.json、MAPPING.json、DECISION.md/.json、LIMITATIONS.md、REPORT.md、ATTEMPT_LEDGER.json、本目录 evidence/。

CURRENT 只准将本任务 CONTRACT_FROZEN→EXECUTING，保持 Executor，更新 execution_phase/next_artifact_path 为本包阶段/REPORT；提交后仍 EXECUTING/Executor，由 Evaluator 接受后转 READY_FOR_REVIEW。不能改授权、任务 ID、合同路径/地图链接，不能修改“Global position”历史。REVIEW、CONTRACT、CASE_SPEC、FROZEN_RUNTIME、EVALUATOR_*、SOURCE_LOCK、TEAM_SOURCE_LOCK、sources、requirements.*、ENVIRONMENT、BASELINE、VALIDATION_PLAN、EXECUTOR_START 全部冻结。

src/tests/scripts、其他 H-*、比赛和规划文档、公共工作流与已存在无关 dirty 改动全部只读。不得实现 UCP 产品适配器、改模型或执行词表，不接新身份系统、不新增界面、不打包成第三方已验收产品。

## Validation plan

VP-01 保护/来源/隔离依赖；VP-02 全部九路径重复运行；VP-03 结构化材料与声明；VP-04 独立检查器正对照与九个破坏负例；VP-05 WebShop runtime gate 和 payment binding 相关回归、diff 与保护检查。精确 argv、cwd、模式和输出分离见 VALIDATION_PLAN.yaml。

程序检查通过只证明所列结构及可观测事实。AC-04/05/06 的适配语义、证据因果关系、报告完整性仍由 Evaluator 人工复核后裁决。正式 L2 不包含未授权的网络；L3 用同一既有本机隔离环境，但独立运行新商家状态，不把准备日志当执行者报告。

## Exclusions / 明确排除

本包不运行模型、真实支付服务或生产身份基础设施，不实现产品适配器，不对外联系或发布。全部原始观测来自冻结的本地模拟商家；不得把声明范围扩大为真实支付、生产安全、客户或监管认证。

## Budget / Authorization

Expected material cost: medium，预计 1–2 个工作日；主动执行上限 12 小时。它是预算而非实测工期，不含等候 Human。
Bounded retry / iteration budget: 正式 L2 最多 3 次，保存每次原始 gate 目录与测量归档；连续两次同一失败且没有新依据即停止。廉价 L1 可在冻结范围与总预算内修本包驱动/材料。
Attempt execution mode: SEQUENTIAL
Max total attempts: 3（正式 L2）；Executor 包内 ASGI 请求总上限 500，单次 VP-02 为 42 次、VP-04 为 2 次，完整一次 L2 为 44 次；正式三次 132 次，其余留给 L1。Evaluator L3 独立一次 44 次，不重复外网。
Max parallelism: 1
Attempt ledger: ATTEMPT_LEDGER.json + REPORT / Iteration ledger

ATTEMPT_LEDGER schema=h47-attempt-ledger/v1：formal_l2_attempts、active_work_minutes、asgi_requests、external_runtime_calls=0、model_calls=0、provider_calls=0，另记录每轮时间、失败原因、证据目录和剩余额度。廉价 L1 汇总，正式 L2 逐轮列明。主动工时自报与客观 gate 时间分别记，不互相冒充。

- commit: false
- push: false
- history_rewrite: false
- api_call: false

全部公开下载与隔离安装已由 Evaluator 在准备阶段完成；Executor 外网预算为零。应用 ASGI 内部调用是本地模拟状态，不是外部 API 授权。禁止模型、支付宝、测试网/钱包、真实凭据、支付/真实卡、商品真实购买、赛事提交、上传、发邮件/issue/PR/消息。禁止执行 EVALUATOR_PREPARE/TEAM_SOURCES/LOCK_LICENSES/FREEZE 重新获取或改变冻结资产。

## Stop conditions

保护或环境漂移、需改冻结动作/夹具/判定/源码、需新依赖或外网、预算耗尽、无法形成原始证据时 BLOCKED，保存报告。普通源行为差异、映射缺失、无新增价值属于有效测量，继续完成其余阶段与材料。发现候选产品漏洞只归档，不执行真实攻击、不在本包修产品。

## External requirement impact

已核对 PCAC 开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；关联 PCAC-07/08/09/11（授权、确认、执行、限额适用性）、PCAC-12/18/20（证据、恢复、上线前评估），CORE/ADAPTER/EVIDENCE_ONLY。maturity_before=外部商家全面适用性未测；maturity_after_target=本固定模拟场景可复核测量与差距分类，不提高生产能力成熟度。Test=VP-01–05；Evidence=原始商家状态、映射出处、L2/L3、团队公开来源；残余风险=合成授权/公钥、模拟付款、ASGI 测试通道、无完整产品控制对照/真实模型/Provider/客户预算；不构成合规结论。

## 统一评估后的下一步

BOUNDED_ADAPTER_CANDIDATE → 只有忠实语义与可控制执行点成立，才另冻最小产品适配能力包；CORE_SEMANTIC_GAP → 比较是否多个独立消费者重复需要，不能因一个样例就改核心；NO_INCREMENTAL_VALUE → 停止该切口；ENVIRONMENT_OR_EVIDENCE_GAP → 按原始失败补最小前置或换候选。无一结果自动恢复支付宝、比赛、H44/H45 或对外联系。
