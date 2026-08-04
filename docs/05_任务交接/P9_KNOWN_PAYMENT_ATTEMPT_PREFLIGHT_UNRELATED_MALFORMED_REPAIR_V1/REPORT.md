# Executor Report

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-UNRELATED-MALFORMED-REPAIR-V1`
Executor status: SUBMITTED_FOR_REVIEW
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`
Implementation commit: NONE

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
parent_task_id: P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1
parent_task_verdict: REJECTED
parent_project_impact_verdict: REGRESSED
inherited_bottleneck_id: B-07
inherited_hypothesis_id: H-06
project_impact_verdict: NOT_APPLICABLE
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

本轮只修复父任务评估者独立复现的过滤顺序缺陷：

```text
修复前：
读取每条历史付款记录
→ 先检查 payment_id / status
→ 再判断是否属于当前 request
→ 无关异常记录也会让当前合法支付 INDETERMINATE

修复后：
先读取并验证 attempt.request_id
→ request_id 明确不同：直接忽略，不读取其他业务字段
→ request_id 相同：再检查 payment_id / status / P2 binding
→ request_id 无法判断：继续失败关闭
```

直接反例结果：

```text
current request = request-1
known attempt request = request-other
known attempt payment_id = ""
known attempt status = INVALID_STATUS

Fact：INDETERMINATE → CLEAR
Runtime Gate：INDETERMINATE / callback 0 → ALLOW / callback 1
P2 verifier：未调用
```

父任务的安全语义保持：

```text
same-request malformed → INDETERMINATE / callback 0
same-request bound SUCCEEDED → BLOCKED / DENY / callback 0
PENDING / UNKNOWN → 不扩展恢复或重试策略
```

## Workspace snapshot / 工作区快照

- Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`
- Inherited snapshot: 父任务 `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1` 的全部未提交实现、报告、评估证据
- Initial repair state: `CONTRACT_FROZEN / Executor`
- Current state: `EXECUTING / Executor`
- Initial status and parent file hashes: `EV-01`
- Initial failing regression run: `EV-02`
- Final repair-only diff: `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/repair.diff`
- Repair diff bytes: `14524`
- Repair diff SHA-256: `c4cee5458a9566be936309343257ddb208a69799f5bafd6097b22b75168c546a`
- Commit: not performed
- Push: not performed

修复专属 diff 通过“HEAD + 父任务 execution.diff”重建父任务继承快照后生成，未把父任务原有未提交实现误算为本轮改动。

## Changed files / 改动文件

### 本修复实际代码和测试差异

| File | Action | Parent SHA-256 | Final SHA-256 | Factual change |
|---|---|---|---|---|
| `src/agentic_payment_experiment/trusted_execution/known_payment_attempt.py` | modify | `06fa46c9348403993a946aa820c50b4d331aa1e1f60f92124d33f096e6f3fe84` | `1fa1a320ceaf4228d56bd796efdeb6f957a20286e7124b8ccbcbceff80e47278` | request 归属判断前置；无关记录直接 continue；同 request refs 稳定排序 |
| `tests/trusted_execution/test_known_payment_attempt.py` | modify | `cc2901bcece761687b2c2d4d3e30fc7f2d5b0ccf355e8e7bded79254cb0a9d6c` | `4f9a87230a3a46c01fec7fc1cde16441d81f73a13f82c39889e8aa67ff188fc6` | 新增无关异常、未知归属、混合库存、顺序无关和 refs 排序矩阵 |
| `tests/test_webshop_runtime_gate.py` | modify | `868e7a202e635b4fb2cb5ec25cc3bd2ab98a40ecd65cf487176fcf1f31b39131` | `66a0d0d1e08b531d26218f7de6e6552b45ed3b08640db6ef1ba1986f802516fa` | 新增 Runtime Gate 无关异常、混合库存、同 request 异常闭环回归 |

### 治理和证据文件

| File | Action | Factual change |
|---|---|---|
| `CURRENT.md` | modify | 原子切换 `CONTRACT_FROZEN → EXECUTING`，角色保持 Executor |
| `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/REPORT.md` | add | 本修复执行报告 |
| `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/` | add | EV triplets、项目测量结果和 repair-only diff |

以下父任务继承文件与修复开工快照字节一致：

```text
src/agentic_payment_experiment/webshop_runtime_gate.py
scripts/validation/run_project_impact_baseline.py
samples/evaluation/project_impact_t10_preflight_target_v1.json
src/agentic_payment_experiment/__init__.py
src/agentic_payment_experiment/trusted_execution/__init__.py
tests/test_project_impact_baseline.py
docs/04_验证体系/项目级能力评测基线_v1.md
```

未修改 Sidecar、Recovery、Status Conflict、Lifecycle 或 Authoritative Trace。

## 2. 修复实现事实

### 2.1 无关记录隔离

对每个 exact `PaymentExecutionRecord`，当前顺序是：

```text
attempt_request_ref = attempt.request_id
→ 非字符串、空或空白：INDETERMINATE
→ 与 current_request_ref 不同：continue
→ 只有同 request 才读取 status 和 payment_id
```

静态位置审计：

```text
request read position      = 3912
unrelated filter position  = 4157
status validation position = 4234
payment validation position= 4298
```

因此 unrelated filter 明确位于 status/payment 检查之前。

### 2.2 未知归属继续失败关闭

以下 `attempt.request_id` 均保持 `INDETERMINATE`，且不调用 P2 verifier：

```text
None
""
"   "
123
```

原因码保持：

```text
known_payment_attempt_request_ref_missing
```

### 2.3 同 request 语义保持

```text
same request + payment_id missing
→ INDETERMINATE
→ known_payment_attempt_ref_missing

same request + invalid status
→ INDETERMINATE
→ known_payment_attempt_status_invalid

same request + bound SUCCEEDED
→ BLOCKED
→ known_payment_attempt_duplicate_succeeded
→ Runtime Gate DENY / callback 0
```

P2 binding 仍只通过现有 `verify_payment_execution_binding`，AST 审计确认新模块只有一个调用点，没有复制金额、币种、payee、authority、agent 或 order 规则。

### 2.4 混合库存和确定性

新增矩阵覆盖：

```text
unrelated malformed only
→ CLEAR

unrelated malformed + same-request valid SUCCEEDED
→ BLOCKED

unrelated valid + same-request malformed
→ INDETERMINATE

multiple unrelated malformed
→ CLEAR

unrelated valid SUCCEEDED
→ CLEAR
```

每组正序、逆序结果相同。`related_attempt_refs` 按 payment id 排序，例如：

```text
input: payment-z, payment-a
output refs: payment-a, payment-z
```

## Impact comparison / 影响对比

Measurement evidence: `EV-01`, `EV-04`, `EV-07`

Before: 父评估反例中，无关但 `payment_id` 缺失的 exact record 产生 `INDETERMINATE`；Runtime Gate 为 `INDETERMINATE / callback 0`，阻断当前合法 checkout。

After: 同一反例产生 Fact `CLEAR`；Runtime Gate 为 `ALLOW / callback 1`；相关 refs 和 blocking refs 为空，P2 verifier 未调用。

Delta: 只修复 unrelated malformed 误阻断。same-request malformed 继续失败关闭，same-request bound `SUCCEEDED` 继续在 callback 前阻断。

Guardrail result: 父任务冻结 target/runner SHA-256 未变；T10 继续 `DENY / callback 0`；重复或禁止副作用 `0/12`；callback 匹配 `12/12`；非 T10 投影 SHA-256 继续为 `b451598f483486032d5a79749fd747f40874253871b7971ffd5960942d0b7bb5`；相关回归 `137/137`、全量 `451/451`、正式入口 `13/13`。

Scope caveat: 本任务是 `repair`，合同规定 project impact verdict 为 `NOT_APPLICABLE`。本报告不把父任务 `REJECTED / REGRESSED` 追溯改写为 `IMPROVED`；B-07/H-06 的能力裁决需要后续独立 capability revalidation。

## 3. 验收点映射

| AC | 执行事实 | Evidence |
|---|---|---|
| AC-01 | 无关 record 在 request ownership 明确不同后直接忽略；异常 status/payment/binding 字段不阻断；P2 verifier 未调用 | EV-02、EV-03、EV-07 |
| AC-02 | request_id 非字符串、空、空白继续 INDETERMINATE；非 tuple、非 exact member 的既有 fail-closed 测试通过 | EV-03、EV-05 |
| AC-03 | same-request valid SUCCEEDED 仍 BLOCKED；binding invalid/missing、payment_id/status 异常仍 INDETERMINATE；PENDING/UNKNOWN 未扩展 | EV-03、EV-05、EV-07 |
| AC-04 | Runtime Gate unrelated malformed 为 ALLOW/callback1；same malformed 为 INDETERMINATE/callback0；same valid 为 DENY/callback0 | EV-03、EV-07 |
| AC-05 | 五类混合库存与正逆序矩阵通过；reason codes 与 refs 稳定，refs 排序 | EV-03、EV-05 |
| AC-06 | target/runner hash 未变；T10、0/12 副作用、12/12 callback 和 non-T10 digest 均保持 | EV-04、EV-07 |
| AC-07 | 相关 137/137、全量 451/451、正式入口 13/13；无删测或放宽 | EV-05、EV-06 |
| AC-08 | 初始/最终状态、父快照、修复前后、repair-only diff、哈希、EV triplets、限制与授权齐全 | EV-01—EV-07、EV-08 |

## EV-01

- AC: AC-01, AC-04, AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-01.stderr.log

记录继承工作区、开工哈希，并直接复现 Fact/Gate 父反例：`INDETERMINATE / callback 0`。

## EV-02

- AC: AC-01, AC-04, AC-05
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-02.stderr.log

新增测试在修复前按预期红灯：53 项中 5 项失败，全部对应 unrelated malformed 和混合库存误阻断。

## EV-03

- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-03.stderr.log

Fact + Runtime Gate 专项 `53/53` 通过。

## EV-04

- AC: AC-06
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-04.stderr.log

冻结 target repeat=3：T10 和父任务目标指标保持，target/runner hash 与 non-T10 digest 不变。

## EV-05

- AC: AC-02, AC-03, AC-05, AC-07
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-05.stderr.log

Known Attempt、Runtime Gate、Project Baseline、Payment Binding、Sidecar、Recovery、Status Conflict 共 `137/137` 通过。

## EV-06

- AC: AC-07
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-06.stderr.log

全量 `451/451`，正式入口 `13/13`。

## EV-07

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-07.stderr.log

重建父任务继承快照，生成 repair-only diff，验证过滤顺序、单一 P2 调用点、无 I/O/网络/进程调用、未修改排除文件，并直接输出修复后的 Fact/Gate 反例。

## EV-08

- AC: AC-08
- Meta: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_UNRELATED_MALFORMED_REPAIR_V1/evidence/EV-08.stderr.log

最终 v2.1 validator、`git diff --check`、报告哈希和工作区状态快照。

## Deviations and unresolved items / 偏差与未解决项

- Contract deviation: 无。只修改合同允许的实现文件、两份测试、报告、证据和 `CURRENT.md` 原子路由。
- Inherited workspace: 父任务全部未提交实现、报告和 Evaluator review 均保留，没有 clean、reset、删除或 history rewrite。
- Checks not run and reason: 未运行真实 WebShop、Buy Now、网络、LLM、钱包、支付、退款或外部 API；合同明确禁止。
- Known unresolved issue: 父 capability experiment 仍是 `REJECTED / REGRESSED`；本 repair 不能追溯改变该裁决。
- Known scope limit: 产品 Authoritative Trace / GESR 仍不在本修复范围；PENDING / UNKNOWN 策略未扩展。
- Human or external dependency: 无。
- Out-of-scope finding: 无。
- Authorization: commit、push、history rewrite、API call、network call 均为 false，且均未执行。

## Validator

Status: OK

Command: `python3 .../evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md`

Observed result: `OK: v2.1 routing and required artifacts are structurally valid`

Final evidence: `EV-08`

`CURRENT.md` 按协议保持 `EXECUTING / Executor`；validator 不接受交接、不切换角色，也不改变父任务裁决。只有 Evaluator 可以独立复核并给出修复任务最终裁决。
