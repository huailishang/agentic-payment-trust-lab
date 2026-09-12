# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-REMEDIATION-ACCOUNTABILITY-CONSUMPTION-MEASUREMENT-V1`  
Task name: Remediation Accountability / Closure Consumption Measurement  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `d26fa658b970f84ca25859d7c3739994cae10a61`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-12-r34`  
Active bottleneck: `B-14`  
Hypothesis: `H-23`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_ACCOUNTABILITY_CONSUMPTION_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

B-13 is `RESOLVED / STAGE_CLOSED`. Accepted H-22/H-22R evidence proves:

```text
remediation evidence = 5/5
same-journey remediation continuity = 5/5
R05 original-transaction binding = INVALID preserved
Product Authoritative Trace = VALID 5/5
public runtime fingerprint = live validator contract
```

The existing H-22 runner already calls `consume_authoritative_trace()` and projects Action Origin（动作来源） from the generic Read Model（读取模型）. Therefore there is no evidence that a new Consumer（消费器） must be implemented.

What remains unknown is whether all five frozen remediation branches can pass through the **existing** generic Consumer + Player（通用消费器 + 播放器） with complete, deterministic, read-only visibility of remediation evidence and the R05 negative control（负向控制）.

Metric baseline: systematic five-branch consumption coverage = `unknown`; existing B-08 Consumer/Player representative-family coverage = 4 families; H-22 Consumer use exists inside measurement but no five-branch Player/accountability measurement exists.  
Estimated affected scope: all 5 frozen post-payment remediation branches and any later auditor/UI consumer of their Closure（结束状态） evidence.  
Expected project impact: measurement only; determine whether B-14 is already satisfied by existing generic consumption or has one/shared consumer breakpoint.  
Rollback condition: any measurement requires changing Consumer/Player/Action Origin/H-22 product behavior, re-executing business rules inside the consumer, network access, or real side effects.

## Single objective / 单一目标

Measure the accepted H-22 five-branch remediation family through the existing generic read-only consumption stack:

```text
accepted H-22 same-journey branch
→ Product Authoritative Trace
→ consume_authoritative_trace()
→ AuthoritativeTraceReadModel
→ Action Origin projection
→ existing Trace Player payload / HTML
```

Record exactly where consumption first breaks, if anywhere.

## Measurement-only rule / 只测量规则

Task PASS means the measurement is complete, deterministic and auditable. **Task PASS does not require all five branches to be consumer-ready.**

If one or more branches fail a continuity check, record the failure and mechanically derived `first_breakpoint`; do not repair product code inside H-23.

## Frozen branches / 冻结 5 分支

Reuse the exact accepted H-21/H-22 branch family:

1. `R01_FULL_REFUND`
2. `R02_PARTIAL_REFUND`
3. `R03_DISPUTE_OPEN`
4. `R04_DISPUTE_RESOLVED_OUTCOME_UNVERIFIED`
5. `R05_REFUND_PAYMENT_BINDING_MISMATCH`

Use the accepted H-21 matrix and accepted H-22 result as expectations. Each branch must run `repeat=2`.

## Consumption continuity order / 消费连续性顺序

For every branch, record these booleans in this exact order:

1. `AUTHORITATIVE_TRACE_VALID`
2. `CONSUMER_ACCEPTED`
3. `READ_MODEL_EVENT_PARITY`
4. `SOURCE_BINDING_PARITY`
5. `REMEDIATION_ROLES_VISIBLE`
6. `BINDING_STATUS_EXPECTATION_VISIBLE`
7. `CLOSURE_STATE_VISIBLE`
8. `ACTION_ORIGIN_PROJECTABLE`
9. `PLAYER_PAYLOAD_ACCEPTED`
10. `PLAYER_RENDER_DETERMINISTIC`

Definitions:

- `AUTHORITATIVE_TRACE_VALID`: product trace validates `VALID` before consumption.
- `CONSUMER_ACCEPTED`: existing `consume_authoritative_trace()` returns the accepted/ready status and a non-null Read Model.
- `READ_MODEL_EVENT_PARITY`: read-model event count/order/event-role/event-type/source-binding refs exactly preserve the product trace.
- `SOURCE_BINDING_PARITY`: every event binding ref resolves exactly once and read-model source-binding count/identity/projection matches product trace.
- `REMEDIATION_ROLES_VISIBLE`: `REMEDIATION_OBSERVATION`, `ORIGINAL_TRANSACTION_BINDING_FACT`, `REMEDIATION_CLOSURE_OUTCOME` are visible in the Read Model.
- `BINDING_STATUS_EXPECTATION_VISIBLE`: binding-fact projection exposed by the Read Model matches the accepted H-22 branch status and reason codes.
- `CLOSURE_STATE_VISIBLE`: task/remediation/next-action/case-ref closure fields are visible through the read-model source projection.
- `ACTION_ORIGIN_PROJECTABLE`: existing `project_authoritative_trace_origins()` succeeds from the read-model primitive with the expected closed origin classes.
- `PLAYER_PAYLOAD_ACCEPTED`: existing `build_trace_player_payload()` accepts the read model and preserves the exact read-model primitive without business enrichment.
- `PLAYER_RENDER_DETERMINISTIC`: existing player payload hash and HTML hash are byte-identical across repeat=2 for the same branch.

`continuity_pass = all(10 checks)`.  
`first_breakpoint = first false check in the frozen order`, otherwise `null`.

## R05 negative-control requirement / R05 负向控制

R05 must remain visibly and mechanically negative through consumption:

```text
OriginalTransactionBindingFact.status = INVALID
reason_codes contains original_transaction_payment_ref_mismatch
no relation from REMEDIATION_OBSERVATION to PAYMENT_EXECUTION_OUTCOME/CURRENT_PAYMENT_CANDIDATE
Player/read-model must not relabel INVALID as VALID
```

Failure of this requirement is a material finding, not permission to repair H-23 product code.

## Frozen product snapshot / 冻结产品快照

These files must remain byte-for-byte unchanged during H-23:

```text
src/agentic_payment_experiment/authoritative_trace.py
f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492

src/agentic_payment_experiment/authoritative_trace_consumer.py
6ad65118a4ab50e648e4f6098f6c2c5009ce5731232ae0a4e11d2f60c0c431b5

src/agentic_payment_experiment/authoritative_trace_player.py
9cd38620ee966632191b376f13d95446711ff55d08b18aa844f9a7fb6ef74541

src/agentic_payment_experiment/action_origin.py
b43cf1338e7397107aae83a1fca78752b55cd15c900f0160d64a6983707fcada

src/agentic_payment_experiment/webshop_remediation_trace.py
961f6042bc48afc160b3373bd2b439da30127f32de44fa3937cc00d1dc3460ad

scripts/validation/webshop/run_same_journey_remediation_trace_closure.py
a90f0923ee6fdbb1c9b8d0cee76390f04d2786a8350bd8c09fafa7e62061d1fc

tests/test_authoritative_trace_consumer.py
dfa4a7717020819c96fdc0c21a8c7e68a9aee043a4fb02932b4d8252026100fc

tests/test_authoritative_trace_player.py
3101671e80139988c1b755a5f975c92f8f75f570498613ee223154111ffcf991

accepted H-22 result
ba1d4e562bef9ae975c81049b0c24399513cf62f6f8d1c7bb6ece4f2b4e09891
```

## Allowed scope / 允许修改范围

Main measurement implementation:

- `scripts/validation/webshop/run_remediation_accountability_consumption_measurement.py`

Task-owned outputs:

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_ACCOUNTABILITY_CONSUMPTION_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_ACCOUNTABILITY_CONSUMPTION_MEASUREMENT_V1/evidence/**`

Optional runner-focused test only if required to make the measurement runner itself auditable:

- `tests/test_remediation_accountability_consumption_measurement.py`

Evaluator-owned contract/plan/checker files are read-only.

## Required runner behavior / 运行器要求

The runner must:

- reuse existing H-21/H-22 branch builders and product functions; do not duplicate refund/dispute/original-transaction business rules;
- create/obtain the real H-22 extended Product Authoritative Trace for each frozen branch;
- feed that product trace into existing Consumer / Read Model / Action Origin / Player APIs;
- distinguish **product-observed trace facts** from measurement diagnostics;
- run each branch twice and record canonical result digests;
- record Consumer status, event parity, source-binding parity, required roles, binding status/reasons, closure fields, Action Origin types, Player payload hash and HTML hash;
- record R05 negative-control visibility explicitly;
- derive `continuity_pass` and `first_breakpoint` mechanically from the frozen order;
- make no network calls and create no real payment/refund/dispute side effects.

Expected result path:

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_REMEDIATION_ACCOUNTABILITY_CONSUMPTION_MEASUREMENT_V1/evidence/H23_ACCOUNTABILITY_CONSUMPTION_RESULT.json`

Expected schema:

`remediation-accountability-consumption-measurement/v1`

## Acceptance criteria / 验收标准

### AC-01 — Product and consumption stack frozen
All frozen hashes above remain unchanged. Measurement code contains no Consumer/Player replacement and no business-rule reimplementation.

### AC-02 — Five branches measured deterministically
Exactly 5/5 frozen branches are measured, each repeat=`2`; repeated branch observations/digests are identical. No branch may be skipped because it fails consumption.

### AC-03 — Consumer/read-model observations are real
For each branch, the result records Consumer status, event parity, source-binding parity, remediation roles and exact visible source projection facts from the existing Read Model. Evaluator diagnostics must not be represented as product/read-model evidence.

### AC-04 — Accountability and Closure visibility measured
For each branch, record Action Origin projectability/types and Closure visibility from existing source-bound evidence. Do not synthesize missing fields.

### AC-05 — R05 negative control preserved
R05 visible binding status remains `INVALID`, includes `original_transaction_payment_ref_mismatch`, and no false payment relation appears. Player/read-model must not normalize it.

### AC-06 — Existing Player measured read-only and deterministic
For all five branches, record whether existing Player accepts the read model. If accepted, payload must equal the existing read-model primitive contract and payload/HTML hashes must be identical across repeat=2. Measurement must not add network/external resources.

### AC-07 — First breakpoint mechanically recomputable
The result contains all 10 frozen continuity booleans, `continuity_pass`, and `first_breakpoint`; evaluator audit can recompute all three without running product business rules.

### AC-08 — Project guardrails unchanged
- existing consumer/player tests PASS;
- accepted H-22 product result hash unchanged;
- project-impact baseline repeat=`3`, `all_identical=true`;
- Product Trace >= `10/12`;
- GESR >= `9/12`;
- callback=`12/12`;
- duplicate/forbidden side effect=`0/12`;
- unsafe allow=`0/5`;
- full unittest zero failures;
- real payment/refund/dispute/network=`0`.

### AC-09 — v2.2 handoff
Frozen L2 mandatory checks all PASS; REPORT maps AC-01..09 to EV, includes five branch outcomes, first-breakpoint distribution, Player/read-model observations, R05 negative control, hashes, guardrails, deviations and stop-condition status; workflow validator `OK` before submission.

## Stop conditions / 停止条件

Stop and return `BLOCKED` if:

- any frozen product/Consumer/Player/Action-Origin/H-22 file must change;
- a Consumer or Player repair is needed to complete measurement;
- real side effects or network are required;
- evaluator evidence must be fabricated as product/read-model evidence;
- accepted H-22 result/matrix expectations must change;
- more than `2` complete measurement-runner→L2 cycles are required.

## Exclusions / 排除

- no changes to Consumer, Player, Action Origin, authoritative trace or remediation products;
- no new UI feature or styling work;
- no new trace event/profile/projection;
- no T05/T06 Product Trace repair;
- no Fresh Unseen Agent work;
- no legal/settlement finality claim;
- no network/API/dependency install;
- no commit/push/history rewrite.

## Budget / authorization

- max complete runner→L2 cycles: `2`
- local CPU only
- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- real payment/refund/dispute: false
