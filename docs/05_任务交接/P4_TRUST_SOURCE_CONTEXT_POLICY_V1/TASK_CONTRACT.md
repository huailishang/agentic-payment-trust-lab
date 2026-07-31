# P4 Trust Source / Context / Policy Input v1 冻结任务契约

## I. Frozen task contract

```text
Task ID: P4-TRUST-SOURCE-CONTEXT-POLICY-V1
Task name: 可信事实来源、上下文覆盖规则与支付前策略输入
Source: 用户确认 + 整体修正执行计划 P4 + Agent Trust Control Plane 最小领域模型 v1
Risk: L1
Contract state: CONTRACT_FROZEN
Freezing role: Evaluator
Branch: main
Baseline commit: 063dd539589d8e50258b9d2c6225ec45763a776c
Pre-existing changes: none
Baseline validation: PYTHONUTF8=1 下完整回归 Ran 218 tests / OK
```

冻结基线原始证据：

```text
Working directory: <REPO_ROOT>
Command: $env:PYTHONUTF8='1'; python -m unittest discover -s tests -v
Exit code: 0
Stdout/Stderr: docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/evidence/FREEZE-EV-01_baseline_218_tests.log
Bytes: 72258
SHA-256: E2ED26AAA47F8DCD8268562C652351FA17B4E8F1749196BFB648B36D85591D4E
Observed result: Ran 218 tests; OK
```

## 1. Single objective

建立协议中立、确定性的 P4 Trust Source / Context / Policy Input v1：
每个进入支付执行前控制点的关键事实都带有来源类型；系统按“来源 × 目标事实域”
决定候选更新能否建立或覆盖事实；低可信输入不能静默改写用户授权、已确认交易对象、
支付请求或执行身份，同时合法的支付机构状态观察等更新仍能被允许。

P4 可信执行层只返回可回放事实，不替支付域直接决定业务动作。支付域在模拟 callback
之前消费 P1—P4：缺少必要来源或策略证据时 fail-closed 为 `INDETERMINATE`，
已经发生未授权可信状态改写时为 `DENY`；被规则安全阻断且可信状态未变化的攻击尝试，
可以保留原有 P1—P4 判断，不因“不可信文本出现”自动拒绝合法交易。

## 2. Design boundary

P4 不采用单一数值可信等级覆盖所有事实，因为权限取决于事实域：

```text
PAYMENT_PROVIDER_OBSERVED
    可以建立支付状态观察
    不能修改 Delegated Authority

MERCHANT_PROVIDED
    可以建立候选 Offer / Order
    不能覆盖 USER_CONFIRMED 的确认订单或支付请求

SYSTEM_POLICY
    可以提供 policy version 和策略输入
    不能静默改写 amount、payee、currency 或 items
```

实现可以使用显式矩阵、规则表或等价封闭结构，但必须稳定、可测试，并默认拒绝未知组合。

## 3. Acceptance criteria

### AC-01：来源类型与事实域模型

```text
Type: domain model / protocol-neutral fact
Given: 支付控制面需要表达事实来源和事实所属域
When: 构造来源、事实域和候选更新对象
Must observe:
- SourceType 至少包含 USER_CONFIRMED、SYSTEM_POLICY、AGENT_DECLARED、AGENT_INFERRED、MERCHANT_PROVIDED、PROTOCOL_VERIFIED、PAYMENT_PROVIDER_OBSERVED、EXTERNAL_TOOL_UNTRUSTED、WEB_UNTRUSTED、LLM_GENERATED；
- 目标事实域使用封闭、可序列化类型，至少区分 AUTHORITY、TRANSACTION/ORDER、PAYMENT_REQUEST、PAYMENT_STATUS、EXECUTOR_IDENTITY、POLICY/CONTEXT；
- 每个候选更新至少包含 source_type、target path/domain、value或value reference、source_ref；
- 核验结果至少包含 status、reason_codes、allowed/blocked paths 和 policy_version。
Must not observe:
- 用任意字符串或单一数值分数替代全部来源×事实域规则；
- 把 source_type 标签描述成已经完成来源认证。
Evidence required: EV-01 focused model tests + EV-02 source/diff evidence
Mandatory: yes
```

### AC-02：确定性覆盖矩阵与默认拒绝

```text
Type: trusted execution policy fact
Given: 已有事实来源、候选更新来源、目标事实域/路径与 policy version
When: 独立运行来源覆盖核验
Must observe:
- WEB_UNTRUSTED、LLM_GENERATED、EXTERNAL_TOOL_UNTRUSTED、AGENT_INFERRED 不能覆盖 USER_CONFIRMED authority、confirmed order、payment request、payee、amount、currency 或 executor identity；
- PAYMENT_PROVIDER_OBSERVED 可以建立/更新 PAYMENT_STATUS 观察，但不能修改 AUTHORITY、PAYMENT_REQUEST 或 EXECUTOR_IDENTITY；
- MERCHANT_PROVIDED 可以建立候选 offer/order，但不能覆盖 USER_CONFIRMED 的确认订单或已验证支付请求；
- SYSTEM_POLICY 可以提供 POLICY/CONTEXT 输入，但不能改写具体交易值；
- 至少一个允许建立/更新案例和一个禁止覆盖案例；
- 未知 source、未知 target domain、缺 source_ref、缺 policy_version 或未声明组合默认 MISSING_EVIDENCE/BLOCKED，不得静默允许；
- 多个禁止覆盖以稳定顺序聚合全部 blocked paths/reason codes。
Must not observe:
- “来源更可信”就获得全部字段写权限；
- verifier 直接执行支付、重试、退款或网络动作。
Evidence required: EV-03 table-driven allow/deny/missing tests
Mandatory: yes
```

### AC-03：安全上下文合并与不可变可信输入

```text
Type: deterministic context merge
Given: 可信状态快照和一组带来源候选更新
When: 运行 P4 合并/评估函数
Must observe:
- 只应用覆盖矩阵明确允许的更新；
- 被阻断更新不改变原始输入或输出可信事实；
- 返回 applied paths、blocked paths、来源和原因，顺序稳定；
- 任一未授权更新实际进入可信状态时能够被检测为 INVALID；
- 输入使用不可变复制或等价隔离，调用方原对象不被就地修改。
Must not observe:
- 先写入可信状态再回滚；
- 静默丢弃 blocked attempt 证据；
- 自动修改 amount、payee、currency、items 后继续支付。
Evidence required: EV-04 mutation/copy/aggregation tests
Mandatory: yes
```

### AC-04：支付副作用前消费 Context / Policy fact

```text
Type: payment-domain integration / runtime authorization input
Given: 上游 decision、P2 binding、P3 identity、P4 context-policy fact 和可计数模拟 callback
When: 运行支付执行前闸门
Must observe:
- callback 仅在上游 ALLOW、P2 VALID、P3 VALID且至少BOUND、P4 VALID、policy_version 和 current_action 完整时恰好执行一次；
- P4 MISSING_EVIDENCE 映射为 INDETERMINATE，callback 为 0；
- P4 INVALID 或可信状态已被未授权改写时映射为 DENY，callback 为 0；
- 不可信覆盖已被安全阻断、可信状态未变化且其余证据完整时，可以保持原有 ALLOW 路径；
- outcome 暴露 P4 fact、policy_version、current_action、applied/blocked paths。
Must not observe:
- P4 覆盖 P1/P2/P3 的更严格结果；
- callback 发生在 P4 检查之前；
- 真实支付、网络调用或外部写入。
Evidence required: EV-05 callback-counter integration tests
Mandatory: yes
```

### AC-05：Attack Overlay 升级为来源规则压力测试

```text
Type: vertical slice / adversarial integration
Given: 当前 Attack Overlay 固定离线套件
When: 运行 overlay 模块和正式主结果入口
Must observe:
- overlay 输入显式携带 SourceType/source_ref，而不是仅有自由文本 source；
- 每个 proposed override 经过同一 P4 覆盖矩阵，而不是 Attack Overlay 内硬编码“全部阻断”；
- 至少覆盖：网页/LLM 改 amount/payee/agent 被阻断；PAYMENT_PROVIDER_OBSERVED 更新 payment status 被允许；普通无更新内容不误报；
- 未授权改写若实际进入可信状态，M5 标记 forbidden side effect/FAIL；
- 输出暴露 applied paths、blocked paths、reason codes、policy_version 和 trusted_state_changed；
- 不执行真实 LLM，不解析自然语言生成工具调用。
Must not observe:
- 为增加数量新增无消费者异常枚举；
- 把攻击文本存在本身当作禁止副作用；
- 修改冻结 S01—S13 行为基线。
Evidence required: EV-06 attack-overlay tests + generated report artifact
Mandatory: yes
```

### AC-06：主结果、最小 UI 契约与 M5 消费

```text
Type: result contract / evaluation
Given: 正式 run_scenarios/run_experiment 输出
When: 运行主结果、Lab Overview 与最小 UI 契约测试
Must observe:
- 正式结果中存在独立 P4 context-policy/trust-source 技术结果；
- 至少展示 allowed update、blocked override、missing evidence或invalid case；
- M5 继续统计 forbidden_side_effect，正常安全阻断不被误记为副作用；
- 中文边界说明明确“来源标签未认证来源真实性”“离线规则不等于生产策略/合规”；
- P3 BOUND 和 P1/P2 结果继续可见。
Must not observe:
- 主 UI 结构性重构；
- 在普通用户界面暴露凭证内容或大块原始 JSON；
- 把本地规则写成生产风控、监管合规或外部策略引擎结论。
Evidence required: EV-07 runner/result-card/lab-overview/presentation tests
Mandatory: yes
```

### AC-07：兼容性、范围与文档边界

```text
Type: regression / claim audit
Given: P4 实现完成
When: 运行专项、Attack Overlay、P1—P3/生命周期/恢复测试、完整回归、正式入口和声明审计
Must observe:
- 新增 P4 测试全部通过；
- 完整 unittest 回归为 OK；
- python run_experiment.py 成功，S01—S13 13/13 PASS、内部冻结基线 PASS、M5 无 forbidden side effect；
- Attack Overlay 使用 P4 矩阵后保持全部安全期望通过；
- README、项目中控和执行记录准确陈述来源类型、允许范围和限制；
- diff 仅包含 Allowed scope。
Must not observe:
- 修改 samples/regression/internal_baseline_v1.json；
- 弱化 P1—P3 fail-closed、UNKNOWN 查询原交易或禁止第二次支付不变量；
- 声称接入 Cedar/OPA/OpenFGA、真实来源认证、生产支付安全或监管合规。
Evidence required: EV-08 focused regression + EV-09 full regression + EV-10 formal entrypoint + EV-11 claim/scope audit
Mandatory: yes
```

## 4. Allowed scope

```text
May modify:
- src/agentic_payment_experiment/models.py
- src/agentic_payment_experiment/trusted_execution/__init__.py
- src/agentic_payment_experiment/attack_overlay.py
- src/agentic_payment_experiment/payment_execution.py
- src/agentic_payment_experiment/runner.py
- src/agentic_payment_experiment/result_card.py
- src/agentic_payment_experiment/lab_overview.py
- 为真实消费 P4 结果所必需的 presentation/html_report 装配文件
- tests/test_attack_overlay.py
- tests/test_attack_overlay_entrypoint.py
- tests/trusted_execution/test_payment_binding.py
- tests/test_runner.py
- tests/test_lab_overview.py
- 与最小 UI/结果契约直接对应的现有 tests 文件
- samples/attacks/attack_overlay_v1.json
- README.md
- docs/01_项目现状/项目中控.md
- docs/02_未来规划/后续任务包.md
- docs/02_未来规划/整体修正执行计划_20260729.md
- docs/03_架构设计/支付与可信执行模块边界.md

May add:
- src/agentic_payment_experiment/trusted_execution/context_policy.py
- tests/trusted_execution/test_context_policy.py
- 一个必要的支付域 P4 gate 专项测试文件
- docs/04_验证体系/P4_Trust_Source_Context_Policy_执行记录_20260731.md
- docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/evidence/ 下的执行者原始证据
- docs/05_任务交接/P4_TRUST_SOURCE_CONTEXT_POLICY_V1/EXECUTOR_REPORT.md
```

若实现确需修改未列出的业务或装配文件，执行者必须停止并申请 amendment。

## 5. Exclusions and forbidden side effects

```text
Must not implement:
- Cedar、OPA、OpenFGA 或其他外部策略引擎；
- 网络策略服务、数据库、来源认证、签名验证或远程查询；
- 全局数值信任分数或“高分来源可修改所有事实”的规则；
- P5 Evidence/Replay 事件链、hash chain 或 receipt；
- LLM 调用、提示注入成功率 benchmark 或自然语言到工具调用解析；
- 真实支付、退款、重试、资金动作或生产风控。

Must not modify:
- samples/regression/internal_baseline_v1.json；
- P3 及更早任务的契约、报告、评估和 evidence；
- CURRENT.md 与本冻结契约；
- 与 P4 无关的协议样品、研究原文或 UI 结构。

Must not call or write externally:
- 不访问网络策略/身份服务；
- 不使用真实凭证、个人身份信息或支付数据；
- 不发布、不推送、不执行外部系统写入。
```

## 6. Validation plan

所有命令工作目录均为仓库根目录：
`<REPO_ROOT>`

| VP | Type | Exact command or steps | Expected result | AC |
|---|---|---|---|---|
| VP-01 | focused | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_context_policy -v` | 来源模型、矩阵、默认拒绝和合并测试通过 | AC-01—AC-03 |
| VP-02 | gate | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_payment_binding -v`（加获准新 gate 文件时一并记录） | P1—P4 callback gate 正负路径通过 | AC-04 |
| VP-03 | overlay | `$env:PYTHONUTF8='1'; python -m unittest tests.test_attack_overlay tests.test_attack_overlay_entrypoint -v` | allowed/blocked/benign/forbidden-effect 路径通过 | AC-05 |
| VP-04 | result | `$env:PYTHONUTF8='1'; python -m unittest tests.test_runner tests.test_lab_overview tests.test_presentation -v` | P4 主结果、M5 与最小 UI 契约通过 | AC-06 |
| VP-05 | safety | `$env:PYTHONUTF8='1'; python -m unittest tests.test_validator tests.test_lifecycle tests.test_payment_recovery tests.trusted_execution.test_confirmation tests.trusted_execution.test_payment_binding -v` | P1—P3 与成熟支付安全不变量通过 | AC-04, AC-07 |
| VP-06 | full | `$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v` | exit 0，最终摘要 OK | AC-07 |
| VP-07 | formal | `$env:PYTHONUTF8='1'; python run_experiment.py` | exit 0；S01—S13 13/13；冻结基线 PASS；M5 无 forbidden side effect | AC-05—AC-07 |
| VP-08 | claim | `rg -n -i "cedar|open policy agent|openfga|authenticated source|来源认证|生产策略|生产安全|合规" README.md docs src tests` | 命中均为限制说明、研究材料或明确未实现项 | AC-07 |
| VP-09 | scope | `git diff --name-only 063dd539589d8e50258b9d2c6225ec45763a776c` | 仅出现 Allowed scope 与本任务交接证据 | AC-01—AC-07 |

执行者须保存每条命令的完整 stdout、stderr、exit code、工作目录。长日志必须记录
相对路径、字节数和 SHA-256；执行者报告必须显式包含 `Command / Exit code /
Stdout / Stderr / Deviations and unresolved items`，不能只写汇总。

## 7. Stop conditions

```text
- 当前 HEAD、branch 或初始 git status 与冻结基线不一致，且差异不是本任务已记录产物。
- UTF-8 与正常项目写权限下，218-test 冻结基线不能复现。
- 需要一个全局数值信任排序才能解释规则。
- 对 PAYMENT_PROVIDER_OBSERVED、MERCHANT_PROVIDED 或 SYSTEM_POLICY 的写权限出现两种实质不同解释。
- 工作需要修改冻结回归样品、P3 历史产物或未获准文件。
- 只有接入外部策略引擎、真实来源认证、网络或生产支付才能满足目标。
- 任一必需 AC 无法产生完整 E2 原始证据。
- 执行者发现必须自动修改 amount/payee/items 后继续支付。
```

## 8. Interpretation notes

- `SourceType` 是来源声明和规则输入，不证明来源已经认证。
- “允许更新”只表示该来源在该事实域具备本地规则允许的写入语义，不等于业务合法或监管合规。
- 被阻断的攻击尝试不等于可信状态已修改；只有 forbidden side effect 实际发生才让 M5 失败。
- P4 context-policy fact 是 Runtime Authorization Gate 输入，不是 P5 Replay receipt。
- `MODIFY` 不是当前业务 decision；关键支付字段不得被策略静默改写后继续执行。

## 9. Amendments

```text
None.
```
