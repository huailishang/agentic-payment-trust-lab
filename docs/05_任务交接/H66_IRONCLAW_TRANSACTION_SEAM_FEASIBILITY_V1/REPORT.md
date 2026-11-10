# H66 Executor REPORT：IronClaw 固定版本金融执行消费者资格研究

- Task ID: `H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1`
- Role: Executor；`CURRENT.md` 保持 `EXECUTING / Executor`（待 Evaluator 复核）
- Fixed upstream: `nearai/ironclaw@b0b999d96781516ee05e6ba961d6f3ead900da96`
- Baseline HEAD: `f3e3235e2cd220f1b03cdc217c49820cdebf02b0`
- Workflow: evaluator-executor-workflow/v2.2
- Project map: r108 / B-19
- **Decision: `STOP_REFERENCE_ONLY`**
- Gate: **L2 PASS，4/4 mandatory checks，mandatory_failures=0**；独立 L3 与逐行语义审阅尚未进行。

## 1. 项目位置与本次判断

项目目标是让高风险智能体交易的身份、授权、绑定、确认、执行、恢复和审计形成独立可复核的信任链。A–D已有本地代表性闭合，E是受控本地代表闭合，F处于外部证据阶段。H65R源事实已验证但因无法独立计量完整读取次数被拒收；本次不再重读CartTrace六例。B-19要测的只有：在固定IronClaw源码版本中，是否已经有一个**具体金融执行消费者**，并且它在本仓现有验证边界之外带来一个可以独立测量的新增问题。

**本次有界视图未找到这样的具体消费者。** 找到了通用的 `HostRuntime` / `CapabilityHost` 工具调用入口、`ApprovalResolver` 授权租约及 `HostWasmRuntimeCredentials` 宿主凭据注入；但没有逐代码引用串起“固定金融准备对象 → 用户/账户独立批准 → 消费一次资金执行权 → 资金/签名凭据 → 金融结果回执/失败恢复”。通用工具/HTTP能力≠已接线金融交易执行器；许可证、计划Issue或README也不是运行证明。结论仅限本次固定视图，**不声称整个项目没有金融扩展**。

## 2. 来源版本、许可证和可追溯引用

所有成功封存的源码文件均从 `nearai/ironclaw` 固定SHA取得**完整原文**，归档在 `sources/Sxx.json`；包括固定提交、完整blob SHA和original content。`RESULT.json` 引用每份归档的 `artifact / line_start / line_end / text_sha256`，由冻结CHECK复算。

| 证据 | 固定来源/观察 | 语义限制 |
| --- | --- | --- |
| S01 | `Cargo.toml:62–76`，声明 `MIT OR Apache-2.0` | 仅是根Cargo包许可证声明；没有逐依赖/逐文件法律尽调、未导入上游代码 |
| S02 | `README.md:208–219`，WASM/凭据/白名单安全特性 | 自述不是执行证据 |
| S03 | `crates/kernel/ironclaw_approvals/src/lib.rs:1–5,139–150` | 审批服务不执行工具；重发租约可能产生新的grant id，不能推断为重复付款漏洞 |
| S04 | `crates/kernel/ironclaw_host_runtime/src/lib.rs:3–23,91–108` | 通用宿主及内置工具名清单，非具体金融付款工具 |
| S05 | `crates/kernel/ironclaw_host_runtime/src/wasm_credentials.rs:27–36,152–189` | 受控凭据暂存/一次秘密租约/宿主注入，非付款真实性或外部签名证明 |
| S06 | `crates/kernel/ironclaw_capabilities/src/lib.rs:1–5` | 通用授权、审批恢复、进程及中立运行时调度 |
| S09 | `crates/kernel/ironclaw_authorization/src/lib.rs:182–212` | 通用CapabilityLease状态；不是资金结算状态 |
| S10 | `crates/product/ironclaw_host_ingress/src/lib.rs:1–36` | 受保护/公开路由挂载词汇，本身不是金融消费者 |
| S14 | `crates/kernel/ironclaw_capabilities/src/host/mod.rs:1–20` | 描述invoke/authorize/resume/obligations的宿主通用工作流 |
| S13 | Issue #1712 的本轮动态快照（closed） | Read/Prepare/Spend为金融方案，不能替代具体已交付的主分支调用链 |
| S15 | Issue #6532 的本轮动态快照（open） | 签名方案仍不能替代固定代码里的可执行消费者 |

浏览入口（只读）：[固定Cargo](https://github.com/nearai/ironclaw/blob/b0b999d96781516ee05e6ba961d6f3ead900da96/Cargo.toml)、[固定审批源码](https://github.com/nearai/ironclaw/blob/b0b999d96781516ee05e6ba961d6f3ead900da96/crates/kernel/ironclaw_approvals/src/lib.rs)、[固定Host源](https://github.com/nearai/ironclaw/blob/b0b999d96781516ee05e6ba961d6f3ead900da96/crates/kernel/ironclaw_capabilities/src/host/mod.rs)、[固定WASM凭据](https://github.com/nearai/ironclaw/blob/b0b999d96781516ee05e6ba961d6f3ead900da96/crates/kernel/ironclaw_host_runtime/src/wasm_credentials.rs)、[Issue 1712](https://github.com/nearai/ironclaw/issues/1712)、[Issue 6532](https://github.com/nearai/ironclaw/issues/6532)。

## 3. 六边代码链审查

| 边 | 本轮证明 | 仍缺的金融链路事实 |
| --- | --- | --- |
| `entry` | `STATIC_PROVEN`：HostRuntime向CapabilityHost委托通用权限执行 | 未定位具名付款/签名/资金副作用消费者 |
| `prepared_object` | `UNKNOWN` | 未定位主分支里的金融PaymentSpec及不可修改的交易对象 |
| `approval_authority` | `STATIC_PROVEN`：通用审批发放受限租约 | 未绑定具体金融账户主人、金额、收款对象和一次支付确认 |
| `execution_consumption` | `UNKNOWN` | 没有逐边证实某资金工具原子消费执行授权 |
| `credential_injection` | `STATIC_PROVEN`：通用宿主隔离WASM凭据 | 未证实支付凭据/钱包私钥在该金融消费者中被使用 |
| `outcome_recovery` | `UNKNOWN` | 无具体PSP/签名广播结果、UNKNOWN查询或原交易恢复证据 |

**关键反推限制**：`ApprovalResolver::retry_lease_issue_for_dispatch` 中说底层重发可获得新grant id，只能说明消费端需要审查同一授权的租约管理；它既不是“已经原子执行一次支付”的证明，也不是“存在重复扣款漏洞”的证明。反过来，宿主保护凭据和租约也不能证明某第三方WASM财务工具的授权、钱包签名或付款已安全。没有用未合并设计、Issue关闭、README声称、通用工具名或静态测试目录充当金融生产证明。

## 4. 与本仓六项既有能力对照

`RESULT.json.existing_coverage_comparison` 提供六项本仓保护路径及理由，关键对照为：

1. `trusted_execution/governed_action.py`：本地付款动作对象及绑定已有模型；上游固定金融准备对象未知。
2. `trusted_execution/payment_binding.py`、`confirmation.py`：已有用户确认与支付动作绑定；通用能力租约不是新的金融签收语义。
3. `trusted_execution/context_policy.py`、`known_payment_attempt.py`：上下文信任与已知支付执行前护栏已有代表性覆盖；没见真实外部资金工具绕过的具体反例。
4. `payment_recovery.py`、`trusted_execution/original_transaction.py`：本地有原交易/未知状态恢复语义；上游的具体PSP恢复接线未知。
5. `trusted_execution/credential_possession.py`：本地证明局部凭据持有能力，IronClaw提供通用宿主注入参考；没有金融消费者时不升级为可测量的新项目缺口。
6. `trusted_execution/replay.py`、`known_payment_attempt.py`：已有幂等重放约束；通用租约重试不等于资金副作用重放已发生。

本次没有可供独立复现的**新增金融消费边界**，所以不设计H67能力包、不添加支付模块、不改变项目安全成熟度。

## 5. 请求、失败、预算和副作用

请求审计在 `REQUEST_LEDGER.jsonl` 中从 `START` 到每次 `RESERVE → FINISH` 追加，前后哈希串接。官方Github Connector与同仓官方API仅做公开匿名只读读取；先预留、失败照计、单请求顺序，不使用整仓clone/安装/运行/付款。

- **公开来源请求**：15 / 20；成功11（9个固定完整文件+2份动态Issue元数据），失败4，均已闭合，未把失败计数抹去。
- **失败S07**：`crates/substrates/ironclaw_secrets/src/lib.rs` 完整原文触发本地secret-looking写入保护；按失败封存错误对象。未脱敏伪造原文/sha，也未重试或绕过安全策略。
- **失败S08**：`crates/kernel/ironclaw_capabilities/src/host.rs` 返回404；随后读取实际固定 `host/mod.rs`（S14），作为新目标独立计数。
- **失败S11/S12**：第一轮`fetch_issue`返回结构与读取方预期不一致，故本地封存报错。S13/S15使用官方仓库Issue GET新预留后成功；分别是同目标第2次，未超过上限。
- **归档体积**：304,999 / 8,388,608字节；单文件≤1MiB。
- **墙钟**：763.844 / 5,400秒（从 `CHECK init`起，约12分44秒）；最后一次请求及L2均处于90分钟合同预算内。
- **并发**：1；`RESULT.json`一版；正式L2 1 / 2。
- **禁止副作用**：未安装/运行IronClaw；未调用外部模型、商户/支付产品、钱包、签名、真实支付、旧CartTrace分析；未执行git commit/push；未改受保护本仓源码和历史测量。仅写H66允许的账本/结果/归档/检查辅助/报告和CURRENT状态。

## 6. 正式L2门禁及证据路径

公共runner：`.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01 --mode executor`

| 检查 | 对应AC | 正式L2 |
| --- | --- | --- |
| VP-01 | AC-01，冻结/历史/产品保护 | PASS：`EV-01` |
| VP-02 | AC-02/03，来源引用/结果边界 | PASS：`EV-02` |
| VP-03 | AC-04，预算/反例守卫 | PASS：`EV-03`（7类合成损坏拒绝） |
| VP-04 | AC-01/04，完整来源及最终账本 | PASS：`EV-04` |

Gate结果文件：`evidence/l2_executor_01/L2-GATE.json`，原始输出为相邻 `EV-01..04.{meta.json,stdout.log,stderr.log}`。已在L01预留后运行，并用CHECK finish把 `L2-GATE.json` 的字节数与摘要封存。随后单独运行冻结 `CHECK.py final`：`package/source/analysis/PASS`、source_requests=15、l2_attempts=1、archive_bytes=304999、elapsed_seconds=763.844。**L2仅为执行者门禁，不代替评估者独立L3逐源与语义审查。**

## 7. 去留与下一步条件

提交判断：`STOP_REFERENCE_ONLY`。代码中通用批准/凭据/调用机制可继续作为“设计参考”，但**本轮不构成金融安全能力新增证据**，不承担IronClaw适配工程，也不因为剩余请求预算追更多模块或PR。只有之后出现明确的、固定可引用的资金执行消费者、逐边授权/凭据/执行/恢复代码及一个可独立观察且超过本仓现有覆盖的判别边界，Evaluator才可另冻测量任务。若依赖真实凭据/资金/外部授权，继续维持后置限制。

`CURRENT.md` 保持 `EXECUTING / Executor`，`REPORT.md` 供Evaluator接收；未自行写 `REVIEW.md`、未声称正式L3 PASS或合规、无提交推送权限。本次PCAC-AGENTPAY（PCAC-07/08/09/11/12/14/18/20）只做外部要求参考映射；成熟度before/after不变，真实主体/签名/清算/客户价值/合规仍未知。

## Submission metadata / 交接字段

Task ID: H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1

Baseline HEAD: f3e3235e2cd220f1b03cdc217c49820cdebf02b0

Executor status: SUBMITTED_FOR_REVIEW

### Workspace snapshot / 工作区快照

启动时 `main...origin/main`，基线为冻结的 `f3e3235...`；正式检查 `CURRENT.md` 保持 `EXECUTING / Executor`，未暂存、未commit或push。冻结合同、受保护194文件、上游固定版本及公共 runner 均未修改。外部证据仅为官方公开只读GET的封存副本。

### Changed files / 改动文件

本执行者明确写入的范围为 `CURRENT.md`，以及H66任务包允许的新增 `RESULT.json`、`REPORT.md`、`REQUEST_LEDGER.jsonl`、`sources/S01..S15.json`、`derived/` 检查辅助脚本和 `evidence/l2_executor_01/`；未主动修改 `src/`、`tests/`、旧H65R或任意上游源码。末次 `git status --short --untracked-files=all` 另出现 H46、H49–H64 等历史任务文件的**已跟踪改动（M）**，不属于H66交付范围，本执行者没有调用这些文件的编辑，也无法在此判定其成因或归属；保留不覆盖、不暂存、不清理，交由Evaluator检查是否存在并发或工作区外部变动。不作自动Git发布。

### Deviations and unresolved items / 偏差与未解决项

S07完整上游内容触发安全落盘拦截；S08路径404后转到另一实际路径并独立计数；S11/S12初次Issue连接器结果解析不符后分别用第二次预留请求成功，未修改任务上限。全部失败写入请求账本，无未闭合请求。未获得具体金融付款消费者，因此Prepared/Spend/Recovery仍为UNKNOWN；这不是推断上游不存在金融能力。

## Impact comparison / 影响对比

Measurement evidence: `RESULT.json` 的六条阶段边、六项本仓覆盖对照及九份固定版本代码归档，`REQUEST_LEDGER.jsonl` 的15次顺序请求和 `L2-GATE.json` 的四项检查结果；仅研究证据，没有资金或产品实验。

Before: B-19的“金融执行消费者是否已经接入”未知，只有IronClaw通用架构研究笔记和静态设计方案。

After: 已确认固定版本的通用HostRuntime、CapabilityHost、ApprovalResolver和WASM凭据注入机制；本次有界视图仍未证实具体金融交易消费者或端到端执行/恢复链，判为STOP_REFERENCE_ONLY。

Delta: 外部候选机制认识更明确，具体金融消费者可执行资格从待查收束为`NOT_FOUND_IN_VIEW`；对支付产品成熟度、控制效果和真实支付能力的增量均为0，不把未找到上升为全项目否定。

Guardrail result: `PASS`；15/20次顺序来源访问、归档304999/8388608字节、墙钟763.844/5400秒、1版结果、正式L2 1/2、7种合成损坏全部拒绝；禁止副作用计数0。

Scope caveat: 只覆盖冻结提交、选定九份完整固定代码和两份Issue动态元数据；未进行全仓静态搜索、未合并PR历史穷举、上游运行、产品测试或真实付款。不将通用模块、静态测试名或Issue/README描述当作实际金融消费证明。

## L2 Task Gate / L2 任务门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/L2-GATE.json
- Validation plan: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/VALIDATION_PLAN.yaml
- Checks total: 4
- Mandatory failures: 0
- Remarks: 对象来源/许可/保护、语义结构、累计请求账本、合成损坏与副作用边界均按冻结计划验证；独立L3与逐源代码核查待评估者完成。

## EV-01 — VP-01 source / AC-01

- AC: AC-01
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-01.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-01.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-01.stderr.log
- Observed result: PASS / exit_code=0.

## EV-02 — VP-02 analysis / AC-02, AC-03

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-02.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-02.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-02.stderr.log
- Observed result: PASS / exit_code=0.

## EV-03 — VP-03 guards / AC-04

- AC: AC-04
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-03.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-03.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-03.stderr.log
- Observed result: PASS / exit_code=0.

## EV-04 — VP-04 final / AC-01, AC-04

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-04.meta.json
- Stdout: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-04.stdout.log
- Stderr: docs/05_任务交接/H66_IRONCLAW_TRANSACTION_SEAM_FEASIBILITY_V1/evidence/l2_executor_01/EV-04.stderr.log
- Observed result: PASS / exit_code=0.
