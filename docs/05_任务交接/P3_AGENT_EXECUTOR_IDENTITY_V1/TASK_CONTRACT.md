# P3 Agent / Executor Identity v1 冻结任务契约

## I. Frozen task contract

```text
Task ID: P3-AGENT-EXECUTOR-IDENTITY-V1
Task name: Agent / Executor Identity 保证等级与支付前绑定闸门
Source: 用户授权 + 项目中控 P3 路线 + Agent Trust Control Plane 最小领域模型 v1
Risk: L1
Contract state: CONTRACT_FROZEN
Freezing role: Evaluator
Branch: main
Baseline commit: dd093ff272f34e4a2e2c9a19ffa2ca4f0dd2b873
Pre-existing changes: none（冻结前 git status --short 无输出）
Baseline validation: PYTHONUTF8=1 下完整回归 Ran 210 tests / OK
```

## 1. Single objective

在不引入真实身份认证或外部副作用的前提下，建立协议中立的 Agent / Executor Identity v1：明确区分声明身份与已绑定执行主体事实，输出可审计的身份保证等级，并在模拟支付回调发生前 fail-closed 消费该事实。

本任务最多证明固定离线证据达到 `DECLARED` 或 `BOUND`。没有真实 credential verifier、provider attestation、workload identity 或同等验证器时，任何路径都不得产生或宣称 `VERIFIED`。

## 2. Acceptance criteria

### AC-01：身份模型与保证等级语义

```text
Type: domain model / deterministic fact
Given: Agent 声明、授权期望、当前 executor 与可选凭证引用
When: 构造 P3 身份对象或身份核验事实
Must observe:
- 保证等级使用稳定、可序列化的 DECLARED / BOUND / VERIFIED 枚举或等价封闭类型；
- Agent 与 executor instance 是不同引用；
- 结果至少包含 status、reason_codes、assurance_level，以及可回放的 agent/provider/executor/credential 引用；
- VERIFIED 仅能由显式的额外验证证据与验证结果产生，不能由字符串相等、字段非空或 credential_ref 存在自动升级。
Must not observe:
- 把 declared identity reference match 命名为 authenticated、verified 或等价生产身份结论；
- 修改既有 VerificationStatus 三态含义。
Evidence required: EV-01 focused tests + EV-02 source/diff evidence
Mandatory: yes
```

### AC-02：确定性绑定、缺证据与冲突聚合

```text
Type: trusted execution verification
Given: 授权 Agent 引用、请求 Agent 引用、执行记录 Agent 引用，以及身份对象中的 provider/executor/credential/status
When: 独立运行 P3 身份核验函数
Must observe:
- 必需身份或 executor 证据缺失返回 MISSING_EVIDENCE；
- Agent 替换、executor 替换、provider 冲突、inactive/revoked/unsupported 状态或显式凭证冲突返回 INVALID；
- 同一层出现多个冲突时，以稳定顺序聚合全部适用 reason_codes；
- 只有所需引用完整且一致时才能返回 VALID；
- 仅声明引用成立时最高为 DECLARED；执行主体与授权/交易链被确定性绑定后最高为 BOUND。
Must not observe:
- 缺失 provider/credential 被静默当作 VERIFIED；
- verifier 直接决定 ALLOW、DENY、重试、退款或其他支付业务动作。
Evidence required: EV-03 table-driven positive/negative unit tests
Mandatory: yes
```

### AC-03：支付副作用前 fail-closed 消费

```text
Type: payment-domain integration / side-effect gate
Given: 上游 prepayment decision、P2 continuous binding、P3 identity fact 与一个可计数的模拟支付 callback
When: 运行支付执行闸门
Must observe:
- callback 仅在上游为 ALLOW、P2 为 VALID、P3 为 VALID 且 assurance_level 至少 BOUND 时恰好调用一次；
- P3 MISSING_EVIDENCE 或仅 DECLARED 时返回 INDETERMINATE，callback 调用次数为 0；
- P3 INVALID 时返回 DENY，callback 调用次数为 0；
- 上游非 ALLOW 或 P2 非 VALID 时继续保持既有 fail-closed 行为，callback 调用次数为 0；
- outcome 暴露 P3 fact，供证据和 UI 技术详情消费。
Must not observe:
- 先调用 callback 再检查身份；
- P3 自动覆盖 P1/P2 的更严格结果；
- 真实支付、网络调用或外部写入。
Evidence required: EV-04 focused gate tests with callback counter
Mandatory: yes
```

### AC-04：真实消费路径与可回放证据

```text
Type: vertical slice / evidence contract
Given: 当前固定离线场景中至少一条到 PaymentExecutionRecord 的正式路径
When: 运行正式场景或等价主结果入口
Must observe:
- 该路径真实构造并消费 P3 fact，而不是仅在孤立单测中调用；
- 结果证据稳定暴露 identity status、assurance level、reason codes、agent ref、executor instance ref 和 provider/credential 可用性；
- 至少覆盖一条 BOUND 正向路径、一条身份替换 INVALID 路径和一条缺 executor 证据 MISSING_EVIDENCE 路径；
- 用户可见文案明确这是离线确定性绑定，不是真实身份认证。
Must not observe:
- 通过硬编码最终 decision 绕过 verifier；
- 在主 UI 展开结构性重构或堆叠原始凭证内容。
Evidence required: EV-05 integration/result-contract tests + generated local artifact
Mandatory: yes
```

### AC-05：兼容性与安全回归

```text
Type: regression
Given: P3 实现完成
When: 运行 P3 专项、P1/P2/生命周期/恢复相关测试、完整 unittest 回归与正式入口
Must observe:
- 所有新增 P3 测试通过；
- 既有 P1/P2、UNKNOWN 查询原交易、幂等和禁止第二次支付不变量继续通过；
- 完整 unittest 回归为 OK；
- python run_experiment.py 成功，S01—S13 保持 13/13 PASS、内部冻结基线 PASS、M5 PASS，除非先通过契约 amendment 明确新增正式场景与基线变化。
Must not observe:
- 为通过测试而弱化冻结基线、删除负向断言或把 UNKNOWN 当 FAILED 后重扣；
- 未记录的快照/基线更新。
Evidence required: EV-06 focused regression + EV-07 full regression + EV-08 formal entrypoint
Mandatory: yes
```

### AC-06：边界文档与无夸大声明

```text
Type: documentation / claim audit
Given: P3 实际实现与证据
When: 检查 docstrings、README、项目中控和 P3 执行记录
Must observe:
- 文档准确描述 DECLARED、BOUND、VERIFIED 的差异；
- 明确当前离线实现是否只能达到 DECLARED/BOUND；
- 记录未实现的 credential validity、possession、provider attestation、PKI、federation、生产防篡改和真实支付边界；
- 新增 P3 执行记录只陈述证据支持的能力。
Must not observe:
- “已完成真实 Agent 身份认证”“生产安全/合规已成立”等无证据结论。
Evidence required: EV-09 claim search + doc diff
Mandatory: yes
```

## 3. Allowed scope

```text
May modify:
- src/agentic_payment_experiment/models.py
- src/agentic_payment_experiment/trusted_execution/execution_facts.py
- src/agentic_payment_experiment/trusted_execution/__init__.py
- src/agentic_payment_experiment/payment_execution.py
- 为真实消费 P3 事实所必需的现有 validator/runner/result-card/presentation/scenario 装配文件
- 与上述行为直接对应的 tests/ 文件
- README.md
- docs/01_项目现状/项目中控.md
- docs/02_未来规划/后续任务包.md
- docs/03_架构设计/支付与可信执行模块边界.md

May add:
- tests/trusted_execution/test_identity_assurance.py（或一个语义等价的单一 P3 专项测试文件）
- tests/test_identity_gate.py（仅当支付域测试不适合放入现有测试文件）
- docs/04_验证体系/P3_Agent_Executor_Identity_执行记录_20260731.md
- docs/05_任务交接/P3_AGENT_EXECUTOR_IDENTITY_V1/evidence/ 下的原始日志和生成证据
- docs/05_任务交接/P3_AGENT_EXECUTOR_IDENTITY_V1/EXECUTOR_REPORT.md
```

若真实消费必须修改一个未列出的现有装配文件，执行者必须停止并申请 amendment，不得自行扩大范围。

## 4. Exclusions and forbidden side effects

```text
Must not implement:
- 真实 PKI、签名/证书验证、OAuth/OIDC、DID、workload identity 或外部身份提供商接入；
- 把 credential_ref 非空视作 credential 已验证；
- Runtime Authorization Gate 的 P4/P5 完整能力；
- 新协议 SDK、数据库、远程服务或主 UI 结构性重构；
- 新的真实支付、退款、重试或资金动作。

Must not modify:
- samples/regression/internal_baseline_v1.json（除非 amendment 被重新冻结）；
- P1/P2 已冻结语义，使其变得更宽松的改动；
- CURRENT.md 与本冻结契约；
- 与 P3 无关的文档、样品和实验。

Must not call or write externally:
- 不访问网络身份服务；
- 不使用真实凭证、密钥、个人身份信息或支付数据；
- 不执行真实支付、发布、推送或外部系统写入。
```

## 5. Validation plan

所有命令工作目录均为仓库根目录：
`D:\SoftWare\VScode\install\Project\agentic-payment-trust-lab`

| VP | Type | Exact command or steps | Expected result | AC |
|---|---|---|---|---|
| VP-01 | focused | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_identity_assurance -v`（若采用获准的等价文件名，报告中记录精确命令） | P3 identity tests 全部通过 | AC-01, AC-02 |
| VP-02 | focused | `$env:PYTHONUTF8='1'; python -m unittest tests.trusted_execution.test_payment_binding tests.test_validator tests.test_lifecycle tests.test_payment_recovery -v` | P1/P2 与恢复安全不变量全部通过 | AC-03, AC-05 |
| VP-03 | integration | `$env:PYTHONUTF8='1'; python -m unittest tests.test_runner tests.test_presentation tests.test_interactive_lab -v` | 正式消费、结果契约及最小 UI 契约通过 | AC-04, AC-05 |
| VP-04 | full | `$env:PYTHONUTF8='1'; python -m unittest discover -s tests -v` | exit 0，最终摘要 `OK` | AC-05 |
| VP-05 | formal entrypoint | `$env:PYTHONUTF8='1'; python run_experiment.py` | exit 0；S01—S13 13/13 PASS；内部冻结基线 PASS；M5 PASS | AC-04, AC-05 |
| VP-06 | claim audit | `rg -n -i "authenticated|authentication|verified|认证|已验证|生产安全|合规" README.md docs src tests` | 所有命中均与实际保证等级和限制一致，无夸大声明 | AC-01, AC-06 |
| VP-07 | scope | `git diff --name-only dd093ff272f34e4a2e2c9a19ffa2ca4f0dd2b873` | 仅出现 Allowed scope 文件 | AC-01—AC-06 |

执行者须把每条命令的完整 stdout、stderr、exit code、工作目录写入 `evidence/`。日志过长时记录文件路径、字节数和 SHA-256；报告摘要不能替代原始日志。

## 6. Stop conditions

```text
- 当前 HEAD 或初始 git status 与冻结基线不一致，且差异不是本任务已记录产物。
- UTF-8 与正常项目写权限下，冻结基线的 210-test 回归不能复现。
- 工作需要修改 exclusions、冻结回归样品或未获准文件。
- 身份保证等级、BOUND 的最低证据或业务映射出现两种实质不同解释。
- 只有引入真实凭证、网络、外部服务或生产支付才能满足目标。
- 任何必需 AC 无法产生完整 E2 原始证据。
- 执行者发现必须宣称 VERIFIED 才能让正向路径通过。
```

## 7. Contract interpretation notes

- `VerificationStatus.VALID` 表示“给定证据足够且内部一致”，不等于 `IdentityAssuranceLevel.VERIFIED`。
- `BOUND` 是本轮允许执行模拟 callback 的最低等级，必须包含当前 executor 与授权 Agent/交易链之间的确定性绑定。
- `credential_ref` 只是引用；没有独立验证结果时，它不能提升保证等级。
- `VERIFIED` 可作为模型中的未来值存在，但本任务不要求、也默认不允许固定离线路径产出该等级。
- P3 verifier 只返回可信事实；支付域负责将 `MISSING_EVIDENCE → INDETERMINATE`、`INVALID → DENY`。

## 8. Amendments

```text
None.
```
