# H-39 Sandbox Fixture Route Assessment

Task: `H39_ALIPAY_SANDBOX_FIXTURE_READINESS_V1`
Date: 2026-09-20
Scope: measurement-only; transaction_create=0; payment_verify=0.
Revision: R1–R3 evidence repair after Evaluator review.

## 1. Measurement conclusion

Decision: **CONTRACT_CHANGE_REQUIRED**

The official account and sandbox surfaces are reachable at a read-only level, and the payment.verify schema documents the fields H-38 wants to bind. That is not enough to claim fixture readiness.

The key unresolved point is narrower: there are **two different sandbox routes** in the available official material, and they must not be merged:

1. a Machine Pay server-side sandbox integration route in the fixed official A2M test guide, where `--auto-complete` constructs a proof during automated integration; and
2. a traditional/manual Sandbox APP payment experience, where a developer application initiates a sandbox payment and a Human can complete it in the Sandbox APP.

The fixed A2M guide treats the manual payment experience as optional after the automated integration path. Therefore H-39 does not require Human payment as a prerequisite and does not infer that the manual route yields the Machine Pay Payment-Proof required by H-38.

## 2. Source and observation manifest

| ID | Type | Source | Version / observed time | Observation method / visible evidence | Scope and limitation |
| --- | --- | --- | --- | --- | --- |
| OFF-01 | OFFICIAL_WEB | https://aipay.alipay.com/products/agent-pay | observed_at=2026-09-20 | Public product/sandbox guidance describes simulated funds, sandbox test-account surfaces and manual sandbox payment experience. | Describes product/onboarding behavior; does not prove this account has obtained a buyer account or that manual payment yields Machine Pay proof. |
| OFF-02 | OFFICIAL_WEB | https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html | observed_at=2026-09-20 | Machine Pay protocol documentation describes Payment-Proof carrying payment_proof, trade_no and optional client_session. | Protocol documentation; does not establish how this sandbox account obtains a Provider-origin proof. |
| OFF-03 | OFFICIAL_WEB | https://aipay.alipay.com/docs/ai-receive/api-list/alipay-aipay-agent-payment-verify.html | observed_at=2026-09-20; page_updated_at=2026-09-17 16:23:08 | Request schema lists payment_proof as required with **maximum length 64**; response schema lists trade_no, amount, resource_id, active and out_trade_no. | Schema definition only. It does not prove those response business fields are non-empty in the sandbox. H-38's 64-character tampered case is a project test-shape constraint, not a claim that the field table defines an exact length. |
| OFF-04 | OFFICIAL_SOURCE | alipay/ai fixed revision f3183325f3e4777e53c3483e39954bae000c4778, a2m-sandbox-test.md; summarized by H-38 EVALUATOR_RESEARCH.md and independently rechecked by Evaluator | fixed revision; reviewed 2026-09-20 | Fixed A2M guide separates server-side `--auto-complete` integration from the later optional payment-experience step. | The automated route can construct proof in the sample/integration flow; that must not be labelled Provider-signed. Exact H-38-acceptable proof provenance/capture remains UNKNOWN. |
| BROWSER-OBS-01 | EXECUTOR_REPORTED_BROWSER_OBSERVATION | https://aipay.alipay.com/products/agent-pay | observed_at=2026-09-20 | OpenCLI Browser Bridge opened a new owned tab; page showed an authenticated account surface and product/onboarding UI. | Confirms page/session access only. Does not prove Agent Pay eligibility, buyer-account retrieval, product activation or fixture readiness. No identity value or secret is retained in this package. |
| BROWSER-OBS-02 | EXECUTOR_REPORTED_BROWSER_OBSERVATION | https://aipay.alipay.com/open-flow/console | observed_at=2026-09-20 | OpenCLI read-only state inspection showed product-selection/onboarding/workbench surfaces; no submit/activate/register action was executed. | Confirms UI reachability only. Does not prove the exact product/service prerequisite is enabled. |
| BROWSER-OBS-03 | EXECUTOR_REPORTED_BROWSER_OBSERVATION | https://open.alipay.com/develop/sandbox/app | observed_at=2026-09-20 | OpenCLI read-only navigation reached the sandbox application page and observed a visible “沙箱账号” navigation entry. | Confirms an account-page route exists, not that a buyer test account/UID/password was actually obtained. No buyer identifier or password was read into deliverables. |
| LOCAL-01 | LOCAL_HASH | H-39 BASELINE.json + sha256sum | observed_at=2026-09-20 | Four inherited H-38 implementation files were hashed. | Confirms only inherited-file integrity. |

## 3. Candidate fixture routes — keep separate

### Route A — Machine Pay automated sandbox integration

Source basis: fixed official `a2m-sandbox-test.md` at revision `f3183325f3e4777e53c3483e39954bae000c4778`.

Observed structure from the Evaluator recheck:

1. Server-side sandbox integration runs the documented automated path.
2. The fixed guide uses `--auto-complete` to construct proof and complete the server-side integration sequence.
3. The payment experience is presented later as an optional step, not a mandatory prerequisite for the automated integration path.

Proof production/capture classification:

- production location: **sample/integration server-side flow**;
- mechanism: `--auto-complete` constructs proof in the official sandbox integration path;
- provenance status for H-38: **UNKNOWN / not Provider-signed merely because the official sample constructed it**;
- exact safe capture point for H-38: **UNKNOWN** until an execution contract identifies what in-memory output is retained and how its provenance is labelled.

Implication: this route is the primary candidate for a narrow fixture-acquisition contract, but the contract must explicitly state the upstream method/transport and must not upgrade locally constructed proof into Provider-issued evidence.

### Route B — Traditional/manual Sandbox APP payment experience

Source basis: public sandbox/product guidance.

Observed structure:

1. A developer application/site initiates a sandbox payment.
2. A Human may complete the simulated payment in the official Sandbox APP using a sandbox buyer account.

Proof production/capture classification:

- trade creation/payment experience: documented at a high level;
- Machine Pay `payment_proof` generation location: **UNKNOWN**;
- mechanism for extracting Machine Pay `payment_proof` from this manual route: **UNKNOWN**;
- Provider provenance: **UNKNOWN**.

Implication: this is **not** a mandatory H-38 fixture step and must not be imposed on Human unless a future source-supported contract proves that this route yields the exact Machine Pay fixture required. A visible buyer-account entry or successful manual payment alone would not close H-38.

## 4. Method / endpoint boundary

| Stage | Route | Method / surface | H-39 status |
| --- | --- | --- | --- |
| Account/page access | shared | HTTPS read-only AIPay / Open Platform pages | CONFIRMED as Executor-reported browser observation only |
| Sandbox buyer-account entry | Route B support | Open Platform Sandbox account page | Entry observed; actual buyer account retrieval UNKNOWN |
| Merchant trusted expected values | shared | local in-memory values | input category documented; live values not created |
| Automated Machine Pay fixture | Route A | fixed official A2M `--auto-complete` integration | candidate documented; exact approved upstream method/transport and H-38 proof capture still NOT FROZEN |
| Manual sandbox payment | Route B | developer app/site + Sandbox APP | optional candidate experience; Machine Pay proof retrieval UNKNOWN |
| H-38 verification | downstream | HTTPS gateway + `alipay.aipay.agent.payment.verify` | already frozen in H-38; H-39 budget remains zero |

## 5. Binding and proof constraints

### 5.1 API schema vs live evidence

The payment.verify page observed on 2026-09-20 shows:

- page updated at **2026-09-17 16:23:08**;
- request `payment_proof`: required, **maximum length 64** in the parameter table;
- business response schema includes `trade_no`, `amount`, `resource_id`, `active`, `out_trade_no`.

This supports **documented_schema=CONFIRMED** only.

It does **not** establish that a sandbox live response will return non-empty `out_trade_no` and `resource_id`. The fixed official sandbox guide warns that these fields can be empty in sandbox flows. Therefore:

- `live_returned_fields=UNKNOWN`;
- overall H-39 `binding_fields=UNKNOWN`;
- H-38 must keep fail-closed behavior if live fields are absent.

### 5.2 Local H-38 proof-shape constraint

H-38's tampered negative intentionally preserves a **64-character shape**. That is a project acceptance/test constraint to avoid a trivial malformed-input negative. It must not be described as if the API field table itself specified “exactly 64 characters”.

### 5.3 Failure interpretation

For H-38:

- missing required binding evidence → `MISSING_EVIDENCE`;
- mismatched field → fail closed;
- expiry, prior consumption or transaction-state change can make a tampered case `INCONCLUSIVE`;
- network/provider error is not a security rejection;
- local proof-string comparison does not prove Provider validation;
- a locally constructed sample proof is not automatically Provider-origin evidence.

## 6. Why execution still requires a contract change

1. H-39 transaction-create and payment.verify budgets are both zero.
2. Route A is the more relevant Machine Pay path, but its exact allowed upstream method/transport and safe in-memory proof capture are not frozen.
3. The previously inspected sample contains behavior outside the H-38 whitelist; H-39 may not execute it or silently rewrite transport.
4. Route B is optional and does not currently have evidence tying manual Sandbox APP payment to the exact Machine Pay proof required by H-38.
5. Sandbox-account navigation visibility does not prove an actual buyer account has been obtained.
6. API response-field documentation does not prove live sandbox field population or Provider provenance.

## 7. Minimal next contract for Evaluator consideration

Do **not** freeze “one Human Sandbox APP payment” as the default next step.

Instead, the Evaluator should first select and freeze one evidence-supported upstream route:

### Preferred candidate: Route A

Freeze a minimal Machine Pay fixture-acquisition slice only if the fixed official source can support all of:

- exact upstream method/transport;
- one bounded sandbox fixture execution;
- no new dependency;
- no production call;
- no automatic retry;
- no temporary secret/proof files;
- explicit distinction between locally constructed proof and Provider-origin evidence;
- an in-memory handoff containing trusted pre-verification expected values and the resulting fixture fields;
- zero weakening of H-38 strict binding and negative-case rules.

### Route B only if later proven necessary

Require Human Sandbox APP interaction only if official evidence establishes that the manual route is necessary and specifies how the required Machine Pay proof is produced/captured. Until then, keep it optional and UNKNOWN.

If neither route can be frozen without violating current transport/secret/provenance requirements, STOP this fixture path rather than lowering H-38 acceptance criteria.
