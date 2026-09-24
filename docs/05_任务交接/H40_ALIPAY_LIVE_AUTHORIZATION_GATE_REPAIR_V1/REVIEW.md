# H-40 Independent Evaluator Review

Date: 2026-09-22
Verdict: **PASS / REPAIR_ACCEPTED** — R1/R2 closed; H39 R4 closed within the H40 offline contract. H38 remains PARTIAL / LIVE_BLOCKED.

## Third review — 2026-09-22 — final acceptance

Goal: continuous verifiable authorization, payment effects and evidence. A–D closed, E locally closed, F active. B-06 Alipay fixture/provider evidence remains the first business bottleneck, ahead of AP2 expansion and horizontal attack WATCH. H40 repairs its zero-tolerance authorization prerequisite. That bounded repair is now accepted: STOP H40 implementation work and SWITCH to Evaluator design of the Route A minimum fixture-acquisition contract. No external execution is authorized by this acceptance.

### Findings disposition

- R1: CLOSED. Opening and closing fences consistently recognize 0–3 leading spaces. Unsupported deeper/tab-indented fence-like input is explicitly rejected. The six independent outer-example/second-state variants now reject before inspect/sign/reservation/opener/network.
- R2: CLOSED for the demonstrated scalar defects. Python expression evaluation is removed; scalar validation applies to metadata as well as security fields. Both original malformed-scalar cases remain denied.
- H39 R4: CLOSED within the frozen offline gate scope. The actual probe reads fixed ROOT/CURRENT.md after argument parsing and before key inspection/signing, then re-reads immediately before reservation. No force/skip/alternate-path option was introduced.
- No remaining actionable finding was identified in this bounded review. This is not exhaustive Markdown/YAML compatibility or proof against arbitrary concurrent CURRENT mutation; the contract explicitly excludes atomic transaction guarantees.

### Independently rerun evidence

Existing evaluator interpreter: Python 3.12.14. All five commands below exited **0**; the three suites used `PYTHONPATH=src`.

| Command / entry | Result |
|---|---|
| `python -m unittest discover -s tests -p test_h38_authorization_gate.py -v` | 12/12 PASS |
| `python -m unittest discover -s tests -p test_alipay_agent_pay_sandbox.py -v` | 16/16 PASS |
| `python -m unittest discover -s docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks -p test_*.py -v` | 14/14 PASS |
| H40 `evaluator_checks/independent_gate_audit.py` | 10/10 expectations PASS |
| H40 `evaluator_checks/independent_gate_recheck.py` | 6/6 denial expectations PASS |

The independent inputs use the inspected fake-transport harness. Positive control makes exactly one fake call. First-check denial cases perform no key inspection, signing, reservation or transport. Mid-run task change is denied before reservation/transport. Executor regression additionally covers mid-run revocation, dry-run, replay reservation, gateway, missing fixture and output-path guards. AC-01 through AC-06 are accepted within these boundaries. Full project regression was not rerun because no Trust Core/adapter change is part of this repair; the inherited Windows WebShop failure remains recorded, not claimed fixed.

All four protected BASELINE hashes still match. Independently calculated implementation hashes match REPORT:

- probe: `9de063f46f541b92248e2a1f1bf7af535cce39cf7298e14b0f24420493d1d6a9`
- authorization gate: `19147a6f3a82ca29c13c79079ddf74a779630bf7f75a5700e3e1ebc2095cb511`
- product gate tests: `41888959f05204220208ea59c964975432e694a6f9708a43159c5db3b7b793f9`
- first independent checker: `cda090fd883765556b6a381dec2393be31a6cf9eb2b697cafbb95f0a8af7eb24`
- second independent checker: `17b5be2394495895e11b7da61f5e1243fe62513483047363d572ca7d0a47a32d`

Whitespace check passed. Reviewer performed zero live calls, real key reads, dependency installations, reservation deletions, commits or pushes. Test reservations remain confined to temporary directories.

### External requirements and next condition

PCAC-AGENTPAY / PCAC-07, PCAC-09, PCAC-20 / CORE: the scoped H38 workflow gate advances from M0 MISSING to the contracted M3 TESTED. Contract, probe/gate code, product tests and these two independent evidence entries support that statement. No provider authenticity, production assurance or regulatory compliance is implied.

H38 remains PARTIAL / LIVE_BLOCKED. Before any external call, Evaluator must separately freeze Route A method/endpoint/transport, secret flow, in-memory proof capture/provenance, call budget and stop conditions using H39's established evidence. Unsupported secure transport or binding must lead to STOP/UNSUPPORTED or a narrower measurement contract. This review creates no fixture-acquisition contract and enables no live authorization. CURRENT returns to Evaluator with all authorization flags false.

The earlier reviews below are historical; their open-finding status is superseded by this acceptance.

## Second review — 2026-09-22

Latest verdict: **CHANGES_REQUIRED**. The original five counterexamples are fixed. R2's demonstrated scalar defects are closed; R1's Markdown-context requirement remains open for indented fences. This section supersedes the initial finding status below; the initial review is retained as evidence history.

### R1 follow-up / P1 — Indented fences are silently ignored

`scripts/h38_authorization_gate.py:21,100` matches opening fences only at column zero. An outer four-backtick text fence prefixed by one, two or three spaces is ignored, allowing its inner example YAML to become active authorization. Similarly, a second YAML state block whose fence lines have these prefixes is ignored, allowing the first block to authorize despite multiple state blocks. Supporting these forms is optional, but silently skipping them and authorizing is incompatible with the frozen conservative/fail-closed contract.

Reproduction is preserved in `evaluator_checks/independent_gate_recheck.py`. Six variants (two structures times three indentation widths) each return 0, call fake inspect/sign/opener/network once and create a temporary reservation. Expected: reject before inspection/signing/reservation/network. This is the same R1 failure family, not a request to implement general Markdown. Track permitted fence indentation consistently, or explicitly reject unsupported fence-like input before interpreting inner content. Add entry-point regressions for both structures; do not indiscriminately strip indentation from YAML field lines, which must still reject nested pseudo-fields.

### Second-review validation

- Existing Python 3.12.14; same three targeted commands as below: gate **11/11**, adapter **16/16**, evaluator **14/14**, all exit 0.
- Original `independent_gate_audit.py`: **10/10**, exit 0; all four protected BASELINE hashes match.
- `python docs/05_任务交接/H40_ALIPAY_LIVE_AUTHORIZATION_GATE_REPAIR_V1/evaluator_checks/independent_gate_recheck.py`: **0/6 denial expectations satisfied**, exit 1.
- Both independent checkers use synthetic fixtures and the inspected fake-transport harness. Actual live calls and actual key reads: **0**.
- AC-03 remains FAIL. The first-check/second-check placement, dry-run and reservation controls retain their targeted passing evidence. No broader regression or live-readiness claim.

Return only R1 follow-up to Executor under the existing contract. Preserve both independent checkers; rerun the three targeted suites and both independent audits after repair. H38 stays LIVE_BLOCKED; fixture contract design remains gated on R4 acceptance. PCAC-07/09/20 target M3 acceptance remains withheld for this gate.

## Global position

Goal: continuous, verifiable authorization, payment effects and evidence. A–D closed; E locally closed; F active. B-06 Alipay fixture/provider evidence remains the first business bottleneck. Its zero-tolerance prerequisite is the H38 authorization gate; AP2 expansion and horizontal attack WATCH do not supersede it. This review assesses an offline repair, not live readiness. Continue H40 parser repair; only after independent acceptance proceed to Route A contract design. All live budgets remain zero.

## Findings

### R1 / P1 — Markdown examples and comments can become executable authorization

`scripts/h38_authorization_gate.py:50` extracts matching substrings without tracking Markdown context. Wrapping a valid state block in an HTML comment or in an outer four-backtick text fence still authorizes the actual probe. Appending an unclosed second yaml state block containing `authorization_api_call: false` also leaves the first block accepted. These are not a unique valid active workflow block; the frozen contract requires comment spoofing, multiple state blocks and damaged format to fail closed.

Independent integration reproduction: all three inputs returned 0, inspected/signed once, created a temporary reservation and called fake transport once. Expected: nonzero, zero inspection/signing/reservation/transport. Parse block boundaries and context conservatively, reject ambiguous/unclosed workflow candidates, and add entry-point regressions. No general Markdown dependency is required.

### R2 / P1 — Python string syntax and unvalidated metadata admit damaged YAML

`scripts/h38_authorization_gate.py:37` uses `ast.literal_eval`, so `state: "EXEC" "UTING"` becomes `EXECUTING` although it is not a valid single YAML scalar. At line 70, non-security metadata bypasses scalar validation entirely: inserting `metadata: "unterminated` also authorizes the probe. Both contradict the contract's damaged-format rejection rule.

Both independent cases returned 0 and reached one fake transport call with a reservation. Implement the declared minimal scalar grammar for every accepted field, rejecting unsupported syntax; preserve ordinary metadata and paired quoted strings. Do not normalize malformed values into an authorized tuple.

## Validation evidence

Existing Python 3.12.14 was used; no dependencies installed. Commands below use that interpreter (not a newly installed `python`).

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -p test_h38_authorization_gate.py -v` | 10/10 PASS |
| `python -m unittest discover -s tests -p test_alipay_agent_pay_sandbox.py -v` | 16/16 PASS |
| `python -m unittest discover -s docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks -p test_*.py -v` | 14/14 PASS |
| `python docs/05_任务交接/H40_ALIPAY_LIVE_AUTHORIZATION_GATE_REPAIR_V1/evaluator_checks/independent_gate_audit.py` | 5/10 expectations satisfied; 5 false allows; script returns 1 |
| Four protected BASELINE hashes | All match |
| Baseline HEAD to actual HEAD | Only AGENTS.md committed delta |
| `git diff --check` before review writes | PASS |

Independent audit constructs its own input cases and reuses only the inspected Executor fake-transport harness. Correct cases: allowed synthetic control, wrong task, quoted true, prose spoof, and mid-run task change. Failure cases: the five inputs above. All reservations and outputs are temporary. No real credentials or provider calls were used. The first audit attempt required an explicit UTF-8 baseline read; a subsequent result-file write was denied, so the final script emits JSON to stdout without writing results. These harness issues were corrected before recording the findings.

AC-01/02/04: representative paths pass. AC-03: FAIL. AC-05: protected hashes and 30 inherited tests pass; no new live evidence. AC-06: report present, but broad parser rejection claims are disproved. L2 green does not close R4.

## Bounded return to Executor

Repair R1/R2 within the existing H40 contract and file scope; extend product tests and update REPORT. Preserve the independent checker. Do not change adapters, Trust Core, credentials, authorization or budgets. Re-run the three targeted suites plus the independent audit; no full-suite rerun required absent broader changes. No live calls, commit or push authorized by this review.

External requirement impact: PCAC-AGENTPAY / PCAC-07, PCAC-09, PCAC-20 / CORE. Gate implementation exists, but the target M3 acceptance is withheld due to demonstrated false allows. No compliance or production assurance claim.
