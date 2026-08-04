# Frozen Repair Contract

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-UNRELATED-MALFORMED-REPAIR-V1`  
Parent task: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1`  
Task name: 无关异常付款记录误阻断修复 v1  
Task kind: `repair`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Inherited uncommitted snapshot: parent task `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-03-r4`  
Inherited active bottleneck: `B-07`  
Inherited hypothesis: `H-06`  
Parent verdict: `REJECTED / REGRESSED`

本修复包不提出新的能力假设，只修复父任务已经独立复现的过滤顺序缺陷。修复包的 project impact verdict 固定为 `NOT_APPLICABLE`；B-07 与 H-06 的正式项目影响需要在后续 capability revalidation 中重新裁决。

## Parent failure

Parent review: `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REVIEW.md`  
Parent verdict: `REJECTED / REGRESSED`  
Failed AC: `AC-02`、`AC-04`  
Inherited bottleneck: `B-07`  
Inherited hypothesis: `H-06`

Independent counterexample:

```text
current request_id = r1
known attempt request_id = other
known attempt payment_id = ""

expected:
CLEAR → legitimate checkout continues

actual:
INDETERMINATE → callback 0
```

Root cause:

```text
validate payment_id/status for every exact record
→ only afterwards filter same_request
→ malformed unrelated record fails closed against the current request
```

## Single objective

调整 `derive_known_payment_attempt_preflight` 的归属筛选顺序：对于 exact `PaymentExecutionRecord`，先只用合法、非空的 `request_id` 判断是否属于当前 request；明确属于其他 request 的记录必须直接忽略，不得因为其 `payment_id`、`status` 或其他绑定字段异常而阻断当前合法支付。

同一 request 的异常记录仍必须 `INDETERMINATE`，同一 request 的 bound `SUCCEEDED` 记录仍必须在 callback 前 `DENY`。

## Acceptance criteria

### AC-01 — 无关记录先隔离

对于 exact `PaymentExecutionRecord`：

- `request_id` 为合法非空字符串且与当前 request 不同：直接归类为 unrelated；
- unrelated 记录不得继续校验 `payment_id`、`status`、amount、currency、payee、authority、agent、order 或 transaction ref；
- unrelated 记录不得进入 `related_attempt_refs`、`blocking_request_refs` 或 P2 verifier；
- unrelated 记录即使 `payment_id=""`、`status` 非法或其他字段异常，也不得阻断当前合法支付。

Mandatory evidence: Fact 层矩阵 + P2 verifier `assert_not_called`。

### AC-02 — 无法判断归属时仍失败关闭

以下情况不能证明记录与当前 request 无关，必须 `INDETERMINATE`：

- attempt `request_id` 不是字符串；
- attempt `request_id` 为空或仅空白；
- known attempts 不是 exact tuple；
- tuple member 不是 exact `PaymentExecutionRecord`。

不得通过猜测把未知归属记录视为 unrelated。

### AC-03 — 同 request 安全语义不退化

- same-request bound `SUCCEEDED` → `BLOCKED`；
- same-request `SUCCEEDED` binding `INVALID/MISSING_EVIDENCE` → `INDETERMINATE`；
- same-request 缺 `payment_id` 或非法 `status` → `INDETERMINATE`；
- same-request `PENDING/UNKNOWN` 继续保持父合同限制，不新增恢复或重试策略；
- 继续只调用现有 `verify_payment_execution_binding`，不得复制 P2 规则。

### AC-04 — Runtime Gate 两层反例闭环

必须新增 Runtime Gate 回归：

```text
unrelated + payment_id missing
→ decision ALLOW
→ callback 1
→ preflight CLEAR
```

同时证明：

```text
same-request malformed
→ INDETERMINATE
→ callback 0

same-request valid SUCCEEDED
→ DENY
→ callback 0
```

### AC-05 — 混合库存确定性

至少覆盖：

1. unrelated malformed only → CLEAR；
2. unrelated malformed + same-request valid SUCCEEDED → BLOCKED；
3. unrelated valid + same-request malformed → INDETERMINATE；
4. 多个 unrelated malformed → CLEAR；
5. unrelated valid SUCCEEDED → CLEAR。

结果与输入顺序无关，reason codes 和 refs 稳定排序。

### AC-06 — 父任务目标保持

不得修改：

- `samples/evaluation/project_impact_t10_preflight_target_v1.json`；
- `scripts/validation/run_project_impact_baseline.py`；
- 项目指标定义。

使用现有冻结 target repeat=3，必须继续达到：

```text
T10 decision = DENY
T10 callback = 0
duplicate_or_forbidden_side_effect_rate = 0/12
callback_count_match_rate = 12/12
non-T10 projection digest unchanged
```

### AC-07 — 回归守护

必须通过：

- known payment attempt 专项；
- WebShop Runtime Gate 专项；
- project impact baseline 专项；
- Payment Binding、Sidecar、Recovery、Status Conflict；
- 全量测试不少于父任务 `445`；
- 正式入口 `13/13`。

不得删除、跳过或放宽既有测试。

### AC-08 — 证据与边界

REPORT 必须包含：

- 初始和最终 git status；
- 父任务继承快照说明；
- 反例修复前后结果；
- changed files 和完整 diff；
- 逐 AC EV triplets；
- frozen target/runner hash 未变；
- 未运行项、限制与授权；
- workflow validator `OK`。

本 repair 的 project impact verdict 固定为 `NOT_APPLICABLE`；不得在修复报告中重新声明父 capability experiment 已 `IMPROVED`。

## Allowed scope

May modify only:

- `src/agentic_payment_experiment/trusted_execution/known_payment_attempt.py`
- `tests/trusted_execution/test_known_payment_attempt.py`
- `tests/test_webshop_runtime_gate.py`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-*`
- `CURRENT.md`（仅原子路由）

No other file may change in this repair beyond inherited parent-task changes and evaluator review evidence already present before repair start.

## Exclusions

- 不修改 target fixture、runner 或 metric definitions；
- 不修改 `webshop_runtime_gate.py` 产品逻辑；
- 不修改 Sidecar、Recovery、Status Conflict、Lifecycle 或 Authoritative Trace；
- 不扩展 PENDING / UNKNOWN 策略；
- 不新增第二套 Payment Binding；
- 不执行真实 WebShop、Buy Now、网络、LLM、支付、钱包或外部副作用；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理或回退父任务继承改动。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 先运行父 review 的 unrelated malformed Fact/Gate 反例 | 修复前可复现，修复后 Fact=CLEAR、Gate=ALLOW/callback1 |
| VP-02 | known attempt 新矩阵 | unrelated 隔离；unknown ownership fail closed；same-request 语义保持 |
| VP-03 | WebShop Runtime Gate 专项 | unrelated malformed 不阻断；same-request malformed/duplicate 仍阻断 |
| VP-04 | frozen target repeat=3 | T10 与父目标指标不退化，hash 不变 |
| VP-05 | 相关能力回归 | 全部通过 |
| VP-06 | `PYTHONPATH=src python3 -m unittest discover -s tests -v` | 不少于 445，全部通过 |
| VP-07 | `python3 run_experiment.py` | 13/13 PASS |
| VP-08 | scope/hash/static audit | 仅允许文件新增差异，无 P2 复制或外部副作用 |
| VP-09 | workflow validator | `OK` |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- 修复需要修改 runner、target 或指标定义；
- 无法在不修改 Runtime Gate 产品逻辑的情况下隔离 unrelated records；
- same-request malformed 被错误放行；
- same-request valid SUCCEEDED 不再 callback 前 DENY；
- target T10 或任一非 T10 任务漂移；
- 需要网络、新依赖或外部副作用；
- 需要新的业务风险容忍度决定。

## Amendments

None.
