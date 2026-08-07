# Executor Report

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-ATTACK-OVERLAY-FAMILY-TOOLKIT-V1`  
Executor status: SUBMITTED_FOR_REVIEW  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Implementation commit: `NONE`  
task_verdict_candidate: PASS_CANDIDATE  
project_impact_candidate: IMPROVED_CANDIDATE

## Workspace snapshot

- Workflow: `evaluator-executor-workflow/v2.1`。
- Route: `EXECUTING / Executor`；任务开始只执行 `CONTRACT_FROZEN -> EXECUTING`，提交时不切换角色。
- Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` revision `2026-08-07-r11`。
- Active bottleneck / hypothesis: `B-03 / H-03`。
- 本任务继承此前已接受但未提交的 P9 工作区；未 reset、clean、revert 或改写继承产物。
- Authorization: commit/push/history rewrite/API/network/dependency install/environment/WebShop runtime/Buy Now/payment/order side effect 均为 `false`；本轮均未执行。

## Principal change

本轮只做一个产品变化：

```text
AttackOverlayResult 正常业务结果已生成
→ 一个 Attack Overlay Trace Toolkit 只读现成结果
→ 两个固定 Profile 根据 blocked path + lineage/result facts 做 exactly-one 选择
→ 一个共享 3-event / 1-binding assembly path
→ 回填可选 authoritative_trace
```

固定 Profile：

```text
request.amount blocked -> ATTACK_OVERLAY_T07_V2
request.payee blocked  -> ATTACK_OVERLAY_T08_V2
```

没有根据 evaluator task ID、attack ID、title 或 source_ref 前缀选择 Profile。

## Changed files

本任务直接变化：

| File | Action | SHA-256 | 本任务作用 |
|---|---|---|---|
| `src/agentic_payment_experiment/attack_overlay.py` | modified | `8fc4200f7d6eb871860897e2117d9c3eea0590643294acff684733186fb5968c` | `AttackOverlayResult` 增加可选 `authoritative_trace`；正常 result 完成后唯一一次调用 family builder，再通过 immutable `replace` 附着 trace。 |
| `src/agentic_payment_experiment/attack_overlay_trace_profiles.py` | added | `297b6bbec815a3599a33f02fa927e8bc5f212644279008098f8728182a66d132` | 两个固定声明式 Profile。 |
| `src/agentic_payment_experiment/attack_overlay_trace_toolkit.py` | added | `97d93b390784bef4c998f0f1083be90609c58f2da325b752440d9593e3bf5dda` | exactly-one 选择、accepted projection、共享 3-event trace assembly。 |
| `tests/test_attack_overlay_trace_toolkit.py` | added | `557104e4687428d4216dd34d8198bda4dc5718f9d9bc6226868b429d7fb5b7f6` | 15 项正向/负向/架构证伪。 |
| `tests/test_project_impact_baseline.py` | modified | `e82bc3ed50724d33f8b22e9367bf2858d009870766db4fbc31ca011daf104078` | 只更新 T07/T08 成为真实产品轨迹后直接变化的 matched/source/metric/gap 硬编码期望。 |
| `CURRENT.md` | modified | current route | 仅 `CONTRACT_FROZEN -> EXECUTING`。 |
| 本任务 `REPORT.md` / `evidence/EV-*` | added | 见 evidence | 保存边界、测试、repeat=3、不变量、Hash、full regression 与 workflow evidence。 |

`tests/test_attack_overlay.py` 未修改，仍为 task-start SHA：

```text
afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27
```

仓库 `git diff` 包含前序 accepted-but-uncommitted P9 产物，不能把 HEAD diff 直接当成本任务 diff；EV-01 使用冻结 entering hashes 与 task-start src manifest 区分本任务变化和继承工作区。

## Family architecture

### Profile selection

T07/T08 Profile 都要求：

```text
attack_attempted = true
applied_paths = []
trusted_state_changed = false
decision_drift = false
baseline_decision == defended_decision
lineage_status = VALID
evaluation = PASS
forbidden_side_effect = false
exactly one lineage fact
lineage fact path == blocked path
lineage fact source type == result source type
contains_untrusted_ancestry = true
```

差异只在：

```text
T07 blocked_override_paths == [request.amount]
T08 blocked_override_paths == [request.payee]
```

选择仍可在 attack ID/title/source_ref 改成任意无关字符串时正确工作。

### Shared projection

唯一 source object：

```text
AttackOverlayResult
projection schema = attack-overlay-result-trace/v2
```

projection 严格只有 accepted registry 中的 15 个字段：

```text
attack_id
source_type
baseline_decision
defended_decision
attack_attempted
applied_paths
blocked_override_paths
trusted_state_changed
reason_codes
policy_version
decision_drift
lineage_status
lineage_reason_codes
lineage_fact_refs
lineage_effective_source_types
```

没有 raw untrusted content、title、source_ref、evaluator-only 字段。

### Exact trace

T07/T08 都生成：

```text
#1 POLICY_DECISION_RECORDED
   role = ATTACK_POLICY_RESULT

#2 LINEAGE_DECISION_RECORDED
   role = ATTACK_LINEAGE_RESULT

#3 RESULT_RECORDED
   role = FINAL_OUTCOME
```

三事件共享同一个 `TraceSourceBinding`：

```text
source = PRODUCT_OBSERVED
completeness_status = COMPLETE
source object type = AttackOverlayResult
projection schema = attack-overlay-result-trace/v2
unique source bindings = 1
```

冻结 registry validator 对 T07/T08 均返回 `VALID`。

## Fail-closed matrix

Dedicated family suite 共 15 tests，全部通过。其中包含合同要求的 10 类负例：

| Case | Expected | Result |
|---|---|---|
| unsupported `request.agent_id` | no trace | PASS |
| amount + payee 同时 blocked | no profile / no trace | PASS |
| blocked path 与 lineage fact path 不一致 | no trace | PASS |
| lineage status 非 VALID | no trace | PASS |
| `trusted_state_changed=true` | no trace | PASS |
| applied path 非空 | no trace | PASS |
| decision drift | no trace | PASS |
| attack not attempted | no trace | PASS |
| 已有 non-null trace | never overwrite | PASS |
| invalid profile container | fail closed | PASS |
| duplicate matching profiles | fail closed | PASS |

额外验证：

- T07/T08 的 Profile 选择不依赖 attack ID/title/source_ref；
- 两个真实场景都形成精确 3-event / 1-binding `VALID` trace；
- toolkit 仅一次 `assemble_product_trace`；
- toolkit 内 `evaluate_context_policy / resolve_fact_lineage / validate_request / evaluate_outcome / evaluate_attack_overlay` 调用数全部为 0；
- 不存在 `build_t07_*` / `build_t08_*`；
- 不存在 JSON/YAML 动态 profile loader、`eval`、`exec`、动态 import。

## T07/T08 business invariance

相对 Evaluator 已接受 repair baseline：

```text
T07 decision = ALLOW
T08 decision = ALLOW
T07/T08 callback count = 0
T07/T08 callback observations = 0
T07/T08 retry count = 0
T07/T08 forbidden side effects = []
T07/T08 trusted_state_changed = false
T07 blocked_paths = [request.amount]
T08 blocked_paths = [request.payee]
T07/T08 lineage_status = VALID
```

EV-06 证明：T07/T08 除以下字段外完全相等：

- `product_observed_trace_*`；
- `evidence_stages` 新增 `authoritative_trace`。

全 12 项 non-trace projection SHA 仍为：

```text
6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
```

## Other ten tasks unchanged

相对：

`P9_PRODUCT_AUTHORITATIVE_TRACE_REMAINING_FAMILY_MEASUREMENT_CONTRACT_REPAIR_V1/evidence/RV-EV-03-baseline.json`

除 T07/T08 外的其他 10 项 `actual` dict 全部逐项完全相等。

当前 VALID 集合精确为：

```text
T01,T02,T03,T04,T07,T08,T09,T10,T12
```

当前 absent 集合精确为：

```text
T05,T06,T11
```

没有为 T05/T06/T11 新增任何 trace。

## Existing trace hash invariance

七条此前 accepted 完整轨迹 canonical SHA-256 全部保持：

```text
T01 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906
T02 fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624
T03 7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7
T04 405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33
T09 a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e
T10 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
T12 ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230
```

全部再次通过 frozen `validate_product_authoritative_trace`。

## Frozen measurement boundaries

提交前以下 entering hash 保持精确不变：

```text
samples/evaluation/project_impact_baseline_v1.json
e7a1d338ece0c65c6417ce58384e8dc9eb2dc29b2e37ad461cf92b9deb9b89c0

scripts/validation/run_project_impact_baseline.py
70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3

src/agentic_payment_experiment/authoritative_trace.py
07c7341b62440ea22a6fb22daa2e5e8b48163bc70ba534ac9cb065ffb001414a

src/agentic_payment_experiment/webshop_trace_assembler.py
02d73682ec949d7a37be4e3824e614795f069efc26aafe2377ea18e7c69f70c8
```

没有 runner alias、event normalization、registry shortcut 或 evaluator replay laundering。

## Tests

```text
Existing Attack Overlay
Ran 10 tests
OK

Attack Overlay Trace Family
Ran 15 tests
OK

Project Impact
Ran 21 tests
OK

Full unittest
Ran 538 tests
OK
```

Full suite 超过合同最低 `533`。

## Impact comparison

- Measurement evidence: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-05.meta.json`、`EV-05.stdout.log`、`EV-AFTER-baseline.json`，并由 `EV-06` 独立核对业务不变量、Hash 和 frozen boundaries。
- Before: accepted remaining-family measurement repair baseline Product Trace=`7/12`、GESR=`6/12`；VALID=`T01,T02,T03,T04,T09,T10,T12`；T07/T08=`NOT_AVAILABLE`。
- After: unchanged runner + unchanged fixture 得到 Product Trace=`9/12`、GESR=`8/12`；VALID=`T01,T02,T03,T04,T07,T08,T09,T10,T12`；T07/T08 均 `matched=true`、`capability_gaps=[]`。
- Delta: Product Trace=`+2/12`，GESR=`+2/12`。
- Guardrail result: 其他 10 项 actual 完全不变；T07/T08 只变化 trace 字段和 derived evidence stage；non-trace SHA 不变；原有 7 条 full trace Hash 不变；T05/T06/T11 仍 absent；538/538 全量通过。
- Scope caveat: 本改善只证明 Attack Overlay Family 的 T07/T08 产品权威轨迹缺口被补齐；不代表 T05/T06/T11 已解决，也不扩展到真实网络、浏览器、LLM 或资金副作用。

Repeatability：

```text
repeat_count = 3
all_identical = true
normalized SHA-256 ×3
= fd0abca4e121187ce8ad3d172c2653d53ea06609870c20dfe70dc627ebecd647
```

Executor 因此提交 `IMPROVED_CANDIDATE`；最终 `IMPROVED` 只能由 Evaluator 独立复核签发。

## Acceptance criteria mapping

| AC | Executor result | Evidence |
|---|---|---|
| AC-01 One shared family implementation | PASS_CANDIDATE | EV-03 / EV-06：2 profiles、1 toolkit、1 assembler call、无 dedicated T07/T08 builder、无动态 loader。 |
| AC-02 Positive T07/T08 profile selection | PASS_CANDIDATE | EV-03：amount→T07、payee→T08，且 attack ID/title/source_ref 改为无关值仍正确。 |
| AC-03 Fail-closed negative matrix | PASS_CANDIDATE | EV-03：合同要求 10 类负例全部 fail closed。 |
| AC-04 Exact product traces | PASS_CANDIDATE | EV-03 / EV-05：T07/T08 均 registry VALID，exact 3 events / 1 binding，source=`attack_overlay_result`。 |
| AC-05 T07/T08 business invariance | PASS_CANDIDATE | EV-06：仅 trace + evidence stage 变化；non-trace SHA 不变；decision/state/lineage/side effects 不变。 |
| AC-06 Other ten tasks unchanged | PASS_CANDIDATE | EV-06：其他 10 actual 完全等于 accepted repair baseline；T05/T06/T11 absent。 |
| AC-07 Existing trace invariance | PASS_CANDIDATE | EV-06：T01/T02/T03/T04/T09/T10/T12 七条 full trace hash 精确保持。 |
| AC-08 Same-baseline project impact | PASS_CANDIDATE | EV-05 / EV-06：7→9/12 Product Trace；6→8/12 GESR；repeat=3 stable。 |
| AC-09 Frozen measurement boundaries | PASS_CANDIDATE | EV-01 / EV-06：fixture、runner、registry、shared assembler hashes 精确不变。 |
| AC-10 Tests and workflow | PASS_CANDIDATE | EV-02 10/10；EV-03 15/15；EV-04 21/21；EV-07 538/538；EV-08 workflow validator。 |

## EV-01 — Task boundary audit

- AC: `AC-09, AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-01.stderr.log`
- Additional: `EV-01-task-boundary-audit.py`、`SRC-start.sha256`、`BASELINE-accepted-repair.json`。
- Result: task-start hash anchor、frozen boundaries、task-local product/test files 均明确；`RESULT=PASS`。

## EV-02 — Existing Attack Overlay regression

- AC: `AC-05, AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-02.stderr.log`
- Result: `Ran 10 tests`；`OK`。

## EV-03 — Dedicated Attack Overlay Trace Family suite

- AC: `AC-01, AC-02, AC-03, AC-04, AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-03.stderr.log`
- Result: `Ran 15 tests`；`OK`。

## EV-04 — Project-impact regression

- AC: `AC-04, AC-08, AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-04.stderr.log`
- Result: `Ran 21 tests`；`OK`。

## EV-05 — Same-baseline repeat=3

- AC: `AC-04, AC-08`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-05.stderr.log`
- Additional: `EV-AFTER-baseline.json`。
- Result: Product Trace `9/12`；GESR `8/12`；T07/T08 matched、gaps=[]；repeat=3 stable。

## EV-06 — Invariance / hash / architecture audit

- AC: `AC-01, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-06.stderr.log`
- Additional: `EV-06-invariance-architecture-audit.py`。
- Result: other-10 actual invariant、T07/T08 bounded delta、non-trace SHA、7 legacy hashes、architecture/frozen boundaries 全部 PASS；`RESULT=PASS`。

## EV-07 — Full regression

- AC: `AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-07.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-07.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-07.stderr.log`
- Result: `Ran 538 tests`；`OK`。

## EV-08 — Workflow validator

- AC: `AC-10`
- Meta: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-08.meta.json`
- Stdout: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-08.stdout.log`
- Stderr: `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_ATTACK_OVERLAY_FAMILY_TOOLKIT_V1/evidence/EV-08.stderr.log`
- Result: exit code `0`；`OK: v2.1 routing and required artifacts are structurally valid`。

## Deviations and unresolved items

- Contract deviation: 无。
- Product capability scope: 只新增 T07/T08；T05/T06/T11 未触碰。
- Measurement modification: 无；fixture、runner、registry、shared assembler hashes 均保持 entering 值。
- Business rule reexecution inside toolkit: 无。
- Existing Attack Overlay public report shape: 未增加 trace 序列化字段；原测试 10/10 保持。
- Remaining B-03 gaps: `T05,T06,T11`。
- Commit / push: 未执行，authorization 均为 `false`。

## Submission statement

Executor 已完成 Attack Overlay Family Toolkit、两个固定 Profile、共享 3-event 产品轨迹、15 项 fail-closed 证伪、同基线 repeat=3、业务/Hash/测量边界不变量和 538 项全量回归。当前证据支持 `PASS_CANDIDATE + IMPROVED_CANDIDATE`。`CURRENT.md` 保持 `EXECUTING / Executor`；仅 Evaluator 可接受 snapshot、独立复核并签发最终 verdict。
