# P3 Agent / Executor Identity v1 执行者报告

```yaml
workflow: evaluator-executor-workflow/v1
task_id: P3-AGENT-EXECUTOR-IDENTITY-V1
executor_state: READY_FOR_REVIEW
baseline_commit: dd093ff272f34e4a2e2c9a19ffa2ca4f0dd2b873
implementation_commit: 1bed1e021553df3bfc8101d0e34282372c0667c7
executor_verdict: NOT_ISSUED
requested_next_role: Evaluator
```

## 1. 执行结论

冻结契约要求的候选实现、测试、正式结果契约、边界文档和原始证据已经完成。执行者状态为 `READY_FOR_REVIEW`，不代表任务已经 PASS。

实现保持以下边界：

- 固定离线身份核验最高只到 `BOUND`；
- `VERIFIED` 只作为未来封闭枚举值存在，当前核验器没有任何产出路径；
- `credential_ref` 存在不会升级保证等级；
- 可信执行域只返回身份事实，支付域映射 `DENY / INDETERMINATE / ALLOW`；
- 回调只在上游 `ALLOW`、P2 `VALID`、P3 `VALID` 且至少 `BOUND` 时执行；
- 没有网络身份服务、真实凭证、真实支付或外部写入。

## 2. AC → Evidence 映射

| AC | 实现 / 证据 |
|---|---|
| AC-01 | `IdentityAssuranceLevel`、`IdentityAssuranceFact`、`AgentIdentity.executor_instance_id`；EV-01、EV-02 |
| AC-02 | `verify_agent_executor_identity()` 的缺证据、冲突聚合、状态和最高 BOUND 规则；EV-01、EV-03（表驱动测试包含于 EV-01） |
| AC-03 | `execute_with_payment_binding_gate()` 同时消费 P2/P3，回调计数正负测试；EV-04、EV-06 |
| AC-04 | 正式结果卡三条 P3 路径和可回放 EvidenceRef；EV-05 日志与 JSON artifact |
| AC-05 | P1/P2/生命周期/恢复专项、218 项全量回归、正式入口；EV-06、EV-07、EV-08 |
| AC-06 | README、项目中控、边界文档、P3 执行记录和声明审计；EV-09 |

原始证据目录：

```text
docs/05_任务交接/P3_AGENT_EXECUTOR_IDENTITY_V1/evidence/
```

完整摘要：

- VP-01：6 tests / OK；
- VP-02：46 tests / OK；
- VP-03：44 tests / OK；
- VP-04：218 tests / OK；
- VP-05：S01—S13 13/13，内部冻结基线 PASS，M5 13/13 且禁止副作用 0；
- VP-06：命中均为限制性表述、保留枚举、测试名或历史研究材料，未发现 P3 夸大声明；
- VP-07：候选实现位于冻结允许范围；`CURRENT.md` 和 `TASK_CONTRACT.md` 是评估者冻结前交接产物，执行者未修改。

## 3. 主要代码变化

```text
src/agentic_payment_experiment/models.py
    AgentIdentity 增加 executor_instance_id，与 agent_id 保持独立。

src/agentic_payment_experiment/trusted_execution/execution_facts.py
    新增 IdentityAssuranceLevel、IdentityAssuranceFact、
    verify_agent_executor_identity()。

src/agentic_payment_experiment/payment_execution.py
    支付回调闸门同时消费 P2 和 P3；
    新增 P3 EvidenceRef 映射。

src/agentic_payment_experiment/runner.py
src/agentic_payment_experiment/result_card.py
    正式结果卡真实运行 BOUND、身份替换、缺 executor 三条路径，
    并提供明确的离线非认证文案。
```

## 4. 正式路径观察值

| case | identity status | assurance | decision | callback_count |
|---|---|---|---|---:|
| `P3-BOUND` | VALID | BOUND | ALLOW | 1 |
| `P3-AGENT-SUBSTITUTED` | INVALID | DECLARED | DENY | 0 |
| `P3-EXECUTOR-MISSING` | MISSING_EVIDENCE | DECLARED | INDETERMINATE | 0 |

每条记录均暴露：

```text
identity status
assurance level
reason codes
authorized / request / execution / identity Agent refs
provider ref
executor instance ref
credential availability / credential ref
```

## 5. 评估者应重点复核

1. `BOUND` 的最低证据是否符合冻结解释：完整 Agent 链 + identity binding record + 当前 provider / executor instance 一致。
2. 身份对象缺失、executor 缺失、Agent/provider/executor/credential 冲突和 inactive/revoked/unsupported 是否按约定 fail-closed。
3. 支付域的判断顺序是否保持上游和 P2 更严格结果，且没有先回调后核验。
4. 正式结果卡的离线身份 fixture 是否足够构成 AC-04 所称的“等价主结果入口”，同时没有冒充真实认证。
5. `VERIFIED` 在当前代码中是否确实不可由固定离线路径产生。

## 6. 已知边界

- 正式 P3 路径复用 S10 的离线交易链，并在 runner 中装配固定身份 fixture；它用于验证结果契约和闸门，不是外部身份来源。
- 当前不校验 credential validity、possession、签名、证书、attestation 或 federation。
- 当前不提供生产级身份注册、撤销同步、记录防篡改或外部 provider 查询。
- S01—S13 冻结样品和内部 baseline 未修改；P3 是结果卡中的独立纵向切片，没有新增 S14。

## 7. 交还规则

请独立评估者以 `implementation_commit`、本报告和 evidence 目录为输入，输出 `PASS` 或 `REWORK`。若为 `REWORK`，请引用具体 AC、失败证据和最小修正范围；执行者不自行签发最终 verdict。
