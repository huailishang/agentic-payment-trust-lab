# Executor Report

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1`
Executor status: SUBMITTED_FOR_REVIEW
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
Actual start HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`
Implementation commit: NONE

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: capability_experiment
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-03-r4
active_bottleneck_id: B-07
hypothesis_id: H-06
state_preserved: EXECUTING
current_role_preserved: Executor
commit_performed: false
push_performed: false
history_rewrite_performed: false
network_call_performed: false
api_call_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
workflow_validator: OK
```

## 1. 执行结论

本轮实现了“已知成功付款尝试前置闸门”：

```text
同一 request 的历史 SUCCEEDED PaymentExecutionRecord
→ 复用现有 verify_payment_execution_binding
→ 绑定有效：送入现有 duplicate_request 闸门
→ Runtime Gate 在 checkout callback 前 DENY
→ callback_count = 0
```

绑定无效或证据缺失时返回 `INDETERMINATE` 且 callback 为 0；不同 request、空 tuple、`PENDING` 与 `UNKNOWN` 不扩展新策略。

本轮只修复 B-07 的重复付款前置阻断，不实现 B-03 产品 Authoritative Trace。GESR 和产品观测权威轨迹仍为 `0/12`，没有被包装成已解决。

## Workspace snapshot / 工作区快照

- Contract baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
- Actual start HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`
- Initial state: `CONTRACT_FROZEN / Executor`
- Execution state: `EXECUTING / Executor`
- Initial source snapshot: `EV-01`
- Final saved diff: `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/execution.diff`
- Diff bytes: `96355`
- Diff SHA-256: `15d81e418459c3be0bcc6e383bd14393e0afab5e3cdec94e21f0068b515319c1`
- Commit: not performed
- Push: not performed

最终工作区为未提交任务快照；`CURRENT.md` 按 v2.1 保持 `EXECUTING / Executor`，等待 Evaluator 接受，不由 Executor 切换为 `READY_FOR_REVIEW`。

## Changed files / 改动文件

| File | Action | SHA-256 | Factual change |
|---|---|---|---|
| `src/agentic_payment_experiment/trusted_execution/known_payment_attempt.py` | add | `06fa46c9348403993a946aa820c50b4d331aa1e1f60f92124d33f096e6f3fe84` | 新增 frozen、primitive-only 已知付款尝试预检事实；严格外层类型校验；复用 P2 verifier |
| `src/agentic_payment_experiment/webshop_runtime_gate.py` | modify | `1aa1c3e4ddaaf5f360a75bda2224d83c5b5b6e4b981567795816e62a0600bf93` | 新增 keyword-only `known_payment_attempts`，在 callback 前执行预检并复用 duplicate gate |
| `src/agentic_payment_experiment/trusted_execution/__init__.py` | modify | `d64dbc7241b720838cd5c0d37f0fd57b9d393fbfc63193fc6bf00c116d813393` | 导出新事实、状态、派生函数与限制 |
| `src/agentic_payment_experiment/__init__.py` | modify | `0013d57a92bd2d544d4d811b048ac4bf06ee9277e2d416fa04d2a9e8b87a947f` | 包根导出新公共 API |
| `scripts/validation/run_project_impact_baseline.py` | modify | `a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4` | 冻结 target runner；T10 注入历史成功付款；记录 preflight；不合成产品轨迹 |
| `samples/evaluation/project_impact_t10_preflight_target_v1.json` | add | `f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee` | 独立 T10 target：DENY、callback 0、重复保护 true |
| `tests/trusted_execution/test_known_payment_attempt.py` | add | `cc2901bcece761687b2c2d4d3e30fc7f2d5b0ccf355e8e7bded79254cb0a9d6c` | 事实矩阵、严格类型、P2 复用、primitive 序列化与 frozen 不可变测试 |
| `tests/test_webshop_runtime_gate.py` | modify | `868e7a202e635b4fb2cb5ec25cc3bd2ab98a40ecd65cf487176fcf1f31b39131` | Runtime Gate callback 前阻断、INDETERMINATE、无关请求、PENDING/UNKNOWN、异常类型矩阵 |
| `tests/test_project_impact_baseline.py` | modify | `3e323fe913d67876a2cf2095dd2c257ece4f5d17110da5757abaca59ba25d2b6` | 独立 target 回归和非 T10 完全一致断言 |
| `docs/04_验证体系/项目级能力评测基线_v1.md` | modify | `17181fa930954b75e247353cfb66a414c94d60cb9de5d5e7cd3bd64a2778a47f` | 记录本轮冻结边界、BEFORE/AFTER、未解决 B-03 |
| `CURRENT.md` | modify | `96f34b1123262ffa8adfc32db28345d88d176dd9d9afabd6a21ec5da3dcdce20` | 仅从 `CONTRACT_FROZEN` 切到 `EXECUTING`；角色保持 Executor |
| `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/` | add | see EV metadata | 保存 BEFORE/AFTER、delta、冻结哈希、diff、原始日志与过程偏差 |
| `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REPORT.md` | add | finalized after validator | 本执行报告 |

未修改：

```text
src/agentic_payment_experiment/webshop_payment_sidecar.py
src/agentic_payment_experiment/payment_recovery.py
src/agentic_payment_experiment/payment_status_conflict.py
src/agentic_payment_experiment/lifecycle.py
产品 Authoritative Trace
外部协议适配器
```

## 2. 实现事实

### 2.1 事实对象

`KnownPaymentAttemptPreflightFact` 使用 frozen dataclass，字段只包含 enum、字符串与 tuple，并提供 primitive-only `to_dict()`。

外层边界按以下顺序 fail closed：

```text
known_attempts 必须是 exact tuple
→ 每个成员必须是 exact PaymentExecutionRecord
→ mandate/order/request 必须是 exact 类型
→ 之后才读取字段
```

因此 list、dict、`None`、proxy、subclass 和缺失引用不会先触发不可信属性访问。

### 2.2 P2 复用

同一 request 且状态为 `SUCCEEDED` 的尝试只通过现有：

```text
verify_payment_execution_binding(
    mandate,
    order,
    request,
    payment_execution_record,
)
```

判断是否属于同一 Authority—Order—Request—Payment 链。新模块没有复制金额、币种、payee、agent、authority 等 P2 绑定规则。

### 2.3 Runtime Gate 接线

新参数为 keyword-only：

```text
known_payment_attempts: tuple[PaymentExecutionRecord, ...] = ()
```

结果分支：

```text
BLOCKED
→ 把已验证 request ref 交给现有 validate_request(...seen_request_ids...)
→ p1:duplicate_request
→ DENY
→ callback 0

INDETERMINATE
→ callback 0

CLEAR / 参数省略
→ 保持原 Runtime Gate 路径
```

`WebShopBuyNowGateOutcome` 暴露 typed preflight fact；稳定 reason code 同时保留 P1 与 preflight 来源。

## Impact comparison / 影响对比

Measurement evidence: `EV-20`

Before: T10 为 `ALLOW`，callback 为 `1`；重复或禁止副作用率 `1/12`；callback 次数匹配率 `11/12`；不安全放行率 `1/6`；决策—理由一致率 `11/12`。

After: T10 为 `DENY`，callback 为 `0`，preflight 为 `BLOCKED`，禁止副作用为空；重复或禁止副作用率 `0/12`；callback 次数匹配率 `12/12`；不安全放行率 `0/6`；决策—理由一致率 `12/12`。

Delta: 唯一目标 T10 从“回调后由 Sidecar 识别重复”变为“回调前由 Runtime Gate 阻断”；T01—T09、T11、T12 normalized task result 完全一致。

Guardrail result: target 与 runner SHA-256 在 Phase A/Phase B 间保持不变；非 T10 投影 BEFORE/AFTER SHA-256 均为 `b451598f483486032d5a79749fd747f40874253871b7971ffd5960942d0b7bb5`；AFTER 连续 3 次归一化摘要一致。全量测试 `445/445`，正式入口 `13/13`。

Scope caveat: GESR 与产品观测 Authoritative Trace 仍为 `0/12`，因为本任务明确排除 B-03；不得把 evaluator 合成 replay 冒充产品轨迹。Executor 只提交上述测量事实，项目影响正式裁决由 Evaluator 独立复核后给出。

## 3. AC 映射

| AC | 执行事实 | Evidence |
|---|---|---|
| AC-01 | frozen、primitive-only fact；严格 tuple/exact member/type-first fail closed；显式不可变断言通过 | EV-21、EV-22 |
| AC-02 | 同 request `SUCCEEDED` 只调用现有 P2 verifier；有效 BLOCKED，无效/缺失 INDETERMINATE，无关请求 CLEAR | EV-21、EV-22 |
| AC-03 | Runtime Gate keyword-only 接线；DENY/INDETERMINATE callback 0；异常 callback 既有回归仍通过 | EV-21 |
| AC-04 | T10 AFTER 为 DENY/callback 0，并含 `p1:duplicate_request` 与稳定 preflight reason | EV-20、EV-21 |
| AC-05 | target/runner Phase A 后哈希冻结；BEFORE/AFTER 同 evaluator；3 次结果一致 | EV-20、EV-22 |
| AC-06 | 11 个非 T10 结果完全一致；Sidecar/Recovery/Status Conflict/Lifecycle 未修改 | EV-20、EV-22 |
| AC-07 | 全量 `445/445`、正式入口 `13/13`；无网络、支付、钱包或外部副作用 | EV-21、EV-22 |
| AC-08 | diff、状态、哈希、BEFORE/AFTER、范围限制、偏差与规范 evidence triplet 齐全 | EV-20、EV-21、EV-22 |

## EV-20

- AC: AC-04, AC-05, AC-06, AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-20.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-20.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-20.stderr.log

该证据使用冻结 target/runner 重跑 AFTER 三次，并逐项核对 target/runner 哈希、T10 BEFORE/AFTER、11 个非 T10 完全一致及关键指标。

## EV-21

- AC: AC-01, AC-02, AC-03, AC-04, AC-07, AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-21.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-21.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-21.stderr.log

该证据运行全量 unittest 与正式场景入口，观察到 `445/445` 和 `13/13`。

## EV-22

- AC: AC-01, AC-02, AC-05, AC-06, AC-07, AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-22.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-22.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-22.stderr.log

该证据运行 `git diff --check`、允许范围审计、AST 无 I/O/网络/进程调用审计、P2 verifier 单调用点检查、冻结哈希检查与最终状态快照。

## Deviations and unresolved items / 偏差与未解决项

- Contract deviation: 合同记录的 baseline 为 `8acaa9e...`，但任务开工时干净 HEAD 已是 `71a3acb...`，且当前合同也位于该后续提交中。未回退历史；报告同时保留合同 baseline 与实际开工 HEAD。
- Phase A restart: 第一次 target 沿用了“回调已发生后的 Sidecar/Lifecycle 状态”，与“回调前 DENY”及禁止修改 Sidecar 的合同边界冲突。探索运行发现后，已保存草案差异，恢复全部 `src/**/*.py` 到 EV-01 哈希，修正 target/runner，重新生成权威 BEFORE 并重新冻结；没有用 AFTER 结果偷偷修改冻结目标。
- Evidence capture deviation: 早期自制捕获脚本受桥接层 `/tmp` 不持久、shell 变量提前展开影响，部分 EV 失败；后续最终提交证据 EV-20—EV-22 全部使用 v2.1 官方 `capture_evidence.py`。
- Test correction: 首轮事实测试有一个断言少写现有 P2 reason code 的 `execution_` 前缀；实现逻辑未变，断言按真实公共 reason code 修正。
- Documentation correction: 一次 shell heredoc 中的 Markdown 反引号被桥接层解释为命令替换，导致新追加第 11 节临时损坏；原前 10 节未受影响。已按唯一 `## 11` 边界删除并用无插值载荷重写，最终 `git diff --check` 通过。
- Static audit correction: 第一次范围脚本因 Git 默认转义中文路径误报越界；使用 `core.quotePath=false` 后 `OUT_OF_SCOPE=[]`。
- Checks not run and reason: 未运行真实 WebShop、Buy Now、钱包、支付、退款、外部 API 或网络；合同明确禁止。
- Known unresolved issue: 产品 Authoritative Trace / GESR 仍为 `0/12`，继续属于 B-03；本任务没有解决。
- Known policy limit: 同 request 的 `PENDING` 与 `UNKNOWN` 已知尝试不在本轮定义阻断策略，仅在 fact limitations 中显式声明。
- Human or external dependency: 无。
- Out-of-scope finding: 无。
- Authorization: commit、push、history rewrite、API call 均未授权且未执行。

## Validator

Status: OK

Command: `python3 .../evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md`

Final capture label: `EV-24`

Observed result: `OK: v2.1 routing and required artifacts are structurally valid`

Validator 不改变 `CURRENT.md` 的角色或状态，也不代表 Evaluator 接受或项目影响裁决。
