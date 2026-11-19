# H72R2 — 断言完整性与收据计数语义修复

Task ID: H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Contract state: CONTRACT_FROZEN
Owner authorization state: OWNER_AUTHORIZED_EXECUTION
Freeze authority: Project Owner direct authorization, 2026-11-15T12:39:00Z
Evaluator freeze: BYPASSED_BY_EXPLICIT_OWNER_AUTHORIZATION (not represented as evaluator approval)
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1/VALIDATION_PLAN.yaml

## Global position
Project objective remains independently verifiable agent payment trust from authorization and binding through controlled execution, recovery and audit. Latest map: 2026-11-15-r121, bottleneck B-21. H72 remains REJECTED. H72R's three repairs and its public L2 / independent L3 evidence remain intact, but H72R itself is REJECTED because its negative evidence was not trustworthy in two places. This task fixes only those two test-integrity defects.

## Single objective
1. Rename the parser helper so it does not shadow unittest.TestCase.fail. Preserve all 12 existing bilingual parser cases and add framework-integrity tests proving false dictionary assertions and inherited fail() raise AssertionError.
2. Compare every receipt command's label, metadata SHA-256, exit code and test_count; require the test_count key even when expected null. Reject the original commands[3].test_count mutation from 9 to 99. Preserve the top-level summary check.
3. Preserve the original H72R two-context 16-case semantics, restoring test 14 to the per-command mutation.
4. Add an independent HOLDOUT that invokes the actual checker entrypoint against isolated copies. It must not reuse the ordinary negative-test assertions.

## Owner authorization and budget
Project Owner directly authorizes execution without waiting for another Evaluator freeze. This is a deliberate workflow override because the Evaluator is unavailable; it is not an Evaluator review, approval or L3 verdict.
- Active ceiling: 30 minutes from 2026-11-15T12:39:00Z.
- Wall ceiling: 90 minutes; deadline 2026-11-15T14:09:00Z.
- Inherited absolute expiry: 2026-11-16T04:08:37Z; not extended.
- Mainline cumulative active budget: 480 minutes; H72 and H72R costs remain charged.
- One implementation approach; at most two H72R2 public L2 attempts; one independent L3 reserved to Evaluator.
- No commit, push, history rewrite, API, network, download, install, local service, browser, model call, CLI listener or payment.
- No mutation of H72/H72R contracts, code, reports, receipts, databases, signatures, gates, accepted snapshots or shared tools. Only this new task directory and root CURRENT.md route may change.

## Acceptance criteria
AC-01 Historical preservation: keep H72 REJECTED/L3 FAIL and H72R REJECTED/L3 evidence unchanged. Revalidate 2232 protected hashes, 2393 private evidence hashes, 69-file H72R accepted snapshot, H72 original receipt, H72R review, L2/L3 gates, source files and Git HEAD. CURRENT is the only intentional route change.
AC-02 Parser integrity: rename helper to assert_parse_rejected; do not override unittest methods. Preserve original 12 tests; add tests that ParserCases.fail is unittest.TestCase.fail, a false dictionary assertEqual raises AssertionError, and inherited fail() raises AssertionError. Expected suite 14/14.
AC-03 Receipt parity: compare each command's label, meta SHA, exit code and test_count; require test_count key even when expected null. Original receipt passes; commands[3].test_count 9->99 rejects. Preserve top-level safety=99 rejection.
AC-04 Original negative suite: all 16 original cases in explicit Executor and Evaluator contexts, with test 14 restored to the original single-command mutation. Add a 17th explicit case retaining the top-level summary count guard. Expected 17/17 per context; all 16 original semantics remain represented. Fixtures are NON_ADMITTING.
AC-05 Independent holdout: separate program calls the real CHECK.py entrypoint on isolated copies and independently proves parser framework failure semantics and receipt 9->99 rejection. It must not import NEGATIVE_TESTS or NATIVE_NEGATIVES assertions.
AC-06 Regression/inherited facts: run legacy 11, lifecycle 9, safety 9, regressions 74 and Stripe journey 6. Verify inherited H72R AC-04/AC-06 evidence and 13 saved read-only GETs by immutable digest. No Stripe access or repeated payment. D01 remains ledger/receipt recovery, not HTTP transport retry.
AC-07 Budget/provenance/handoff: record BEGIN/END, source attestation, L2 evidence triplets, failure outputs and time. Keep cumulative H72 mainline under 480 and inherited expiry. Submit report/result. H72R2 L3 NOT RUN, reserved to Evaluator. No commit/push.

## Scope
Allowed: new task-local CHECK.py, NATIVE.py, NATIVE_NEGATIVES.py, NEGATIVE_TESTS.py, HOLDOUT.py, BASELINE/FROZEN_INPUTS/AUTHORIZATION/SOURCE_ATTESTATION, plan/start, ledger, result/report, runtime userbase and evidence/l2_attempt_001 or _002. Root CURRENT route only.
Forbidden: edits to existing H72/H72R files, tests, artifacts, receipts, evidence, gates, shared scripts, dependencies/site-packages, project map or payment adapter. No new business cases or architecture.

## Stop conditions
Stop BLOCKED if any inherited hash changes, holdout counterexample still passes, parser harness self-test is ineffective, a required test fails after this single implementation approach, budget/deadline expires, or external action is required. No third L2 or L3.

## External requirement impact
profile=PCAC-AGENTPAY; PCAC-12/20 directly and PCAC-15 as applicable; CORE / EVIDENCE_ONLY. Verification-quality repair only. No maturity increase, strong authentication, credential/key governance, production settlement, merchant adoption or regulatory-compliance claim.

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-15-r121
Active bottleneck: B-21
Inherited hypothesis: H-72
The direct-owner H72R2 repair corrects two independent counterexamples from H72R (unittest framework failure shadow and command-level receipt test count omission). This is evidence-validation reliability work only, not a payment capability experiment. The prior H72/H72R verdicts remain unchanged.

## Allowed scope

Task-local checker, parser tests, negative suite, independent holdout, isolated copies, source attestation, capture triplets, report and evidence. Owner may authorize a time-bounded execution without representing Evaluator approval; one remaining L2 attempt is reserved for public schema compliance rerun.

## Exclusions

No H72/H72R file, gate, receipt, review or private evidence mutation; no changes to shared validation scripts, product payment adapters or project map. No API, network, card payment, installation, local server, browser, commit or push. Independent L3 only after separate Evaluator takeover.

## Post-L2 schema compliance addendum

The original first public L2 Gate remains immutable PASS 12/12. A separate public workflow structure validator identified missing required structural labels in the owner-authored contract. The owner has already authorized completion; this addendum changes no code, AC, amounts, test inputs or L2 plan, and the original pre-amendment contract and seals are retained in evidence/contract_schema_correction. The updated contract is re-sealed and requires an independent second public L2 execution before handoff.
