# H92 Executor checkpoint — BLOCKED_REGRESSION

Date: 2026-11-25
Role: Executor
Status: STOPPED_PENDING_EVALUATOR; not submitted for formal acceptance.

## Recovery and scope

CodexPro Funnel restored local workspace read/write and Bash access. The initial CodexProshl session had terminated; no formal run was consumed there. Funnel shell initially lacked conda on PATH (exit 127). Native Windows Conda agent Python 3.12.13 was invoked via Windows cmd.exe (transport shell only; no Linux Python, no service or WSL test environment). Local evidence/RUN_NATIVE.cmd sets the native Python path. CURRENT state changed CONTRACT_FROZEN → EXECUTING. HEAD and inherited mutable baselines matched at preserve_pre. No commit/push, external API, browser, installation, actual payment, or credentials.

S0 CHECK.py preserve_pre exit 0: {"protected":575,"result":"PASS","pre_implementation":true}.
Candidate 1 changed only the two permitted product files. Product hashes at stop:
- stripe_checkout_lab.py: 33dae1f07a332d1f1720bb6ad03133f4a898dbc1e6df387efe8896820a385daf
- adapters/stripe_checkout.py: 4d02f7c60b15ae6bc9eda62de164d9dbe4a0a2bb8a0fbfe85ef82b32487db970

## Candidate implementation and L1 evidence

One stored_action_control_events table with sequence, canonical payload/digest, partial unique admission/outcome/stop indexes. Stop receipt and control event in one write transaction; begin validates original binding, current control, prior action and operation state and commits before provider callbacks. Stored create/browser use existing gate, attach terminal evidence and preserve UNKNOWN on exception. Native view and recover_original link history; recovery uses original reference and leaves historical facts unchanged.

- protocol exit 0: {"protocol":"PASS","ordering":"ADMITTED_BEFORE_STOP","negative_controls":4,"cleanup":"PASS"}.
- matrix exit 0: evidence/L1_matrix_stdout.json and stderr; six families, 13 rows, O5/O6 DENY and no effect, O7 ALLOW/[0,1,1], pending view, R1–R5 existing recovery checks.
- uncertain exit 0: evidence/L1_uncertain_stdout.json and stderr; two lost-return scenarios and admission-only restart passed.
- guards exit 0: evidence/L1_guards_stdout.json and stderr; inherited H88/H90, unreadable/damaged control table, trusted legacy stop.
- regressions exit 1: evidence/L1_regressions_stderr.txt. 109 tests ran; 107 passed, 2 failed, 15 of 124 not run after assertion. Do not infer later assertions executed.
- Formal L2 not started. No public validation three-piece set; no validator acceptance; independent L3 reserved for Evaluator. No claim of M4 or full capability improvement.

## Stop condition and next bounded decision

S6 original regression failure triggers mandatory preservation/stop per CONTRACT lines 87–90,112. Candidate preserved; checker and historical tests unmodified.

Two failures in tests/test_stripe_authority_context.py:
1. test_cancel_C01_never_calls_browser_or_create_again, line 160: StripeCheckoutError not raised.
2. test_R01_paid_unknown_recovers_read_only_after_confirmation_expiry, line 191: StripeCheckoutError not raised.

Likely cause: the adapter now converts the ledger's DENY for original non-new/non-open terminal state into a gate return; predecessor contract expected a controlled exception. Because these tests stopped at assertRaises, their subsequent no-effect assertions were not executed. Do not treat this as a proven full regression pass. No zero-tolerance effect was reported by the completed matrix/uncertain checks; no claim beyond those observations.

Proposed next candidate (requires Evaluator routing per stop condition): distinguish verified native DENY for stop/replay/unknown versus original business-state mismatch; preserve prior controlled exception for terminal paid/cancelled state when no stop governs; ensure stop precedence, native denial evidence, and no callbacks. Re-run frozen L1/full original regressions, then formal L2 only if prerequisites satisfy. No checker modification or budget reset.

## Costs and residual risk

1/2 product candidates used (candidate 1 preserved). 0/2 formal L2, 0/1 independent L3. Actual active minutes/role wall time UNKNOWN. External costs 0. Source-level semantic review still pending, including integrity/reference checks, NO_EFFECT evidence, and native unresolved state. Actual production cancellation, real authentication, malicious storage rollback, refunds/fulfillment and external channel closure not established.
