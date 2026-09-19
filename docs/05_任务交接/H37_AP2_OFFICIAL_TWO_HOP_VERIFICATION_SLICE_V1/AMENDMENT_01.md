# Amendment 01 — Evaluator-owned validation repair

Task ID: `H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1`
Amendment state: `FROZEN`
Issued by: Evaluator
Issued date: 2026-09-19
Principal change: `NONE` — product hypothesis, allowed product scope, AC semantics and official AP2 boundary remain unchanged.

## Why this amendment exists

Executor correctly stopped after L2 exposed two defects in the evaluator-owned frozen package, not two demonstrated product defects:

1. `baseline drift(基线漂移)`: H-37 was actually dispatched from HEAD `2b57248af464623402a71d65a2098244819519e3`, while CONTRACT/CURRENT/VP-01 still named `e6931273a983459f167b6e72287a6f05d53a8c26`. Independent diff confirms the commits between those points contain governance/task-package changes and no `src/**` or `tests/**` changes.
2. `signature mutation defect(签名篡改构造缺陷)`: the C03/C04 helper changed only the last Base64URL character. For a 64-byte ES256 signature this can alter only unused trailing bits, so text can change while decoded signature bytes stay identical.

These are evaluator validation-package defects. Executor was correct not to patch product code or evaluator-owned checks to satisfy them.

## Effective baseline correction

The effective H-37 baseline is:

```text
2b57248af464623402a71d65a2098244819519e3
```

This supersedes the stale `e6931273...` baseline only for H-37. H-36 historical artifacts remain unchanged.

## Frozen mutation repair

C03 and C04 semantics do not change:
- C03 must alter the decoded root issuer signature bytes.
- C04 must alter the decoded terminal holder signature bytes.

The evaluator checker must mutate decoded signature bytes deterministically and re-encode Base64URL, rather than changing an arbitrary textual tail character.

C01-C08 expected outcomes remain unchanged. AC-06 label is clarified from `Audience/freshness binding` to `Audience/nonce binding` because the frozen C06/C07 evidence tests `aud` and `nonce`, not a separate expiry/freshness counterexample.

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-12]
  applicability: CORE
  maturity_scope: H37 bounded AP2 official two-hop delegation-verification slice only
  maturity_before: M1 MODELLED
  maturity_after_target: M5 REGRESSION_GATED
  test_evidence:
    - evaluator-owned C01-C08 matrix
    - focused H37 unittest
    - existing AP2 / signed-instruction regressions
  trace_evidence:
    - H37 L2/L3 gate evidence
    - H37 project baseline evidence
  residual_risk:
    - no production key governance or real Provider trust establishment
    - no Sandbox/testnet/wallet or real payment
    - no Checkout/Payment typed business-constraint verification
    - no Receipt verification
    - this is not a regulatory-compliance conclusion
```

## Budget repair

Original `2 / 2` implementation→L2 budget is not reopened.

One `validation-only rerun(仅验证重跑)` is authorized after this amendment because both mandatory failures were caused by evaluator-owned package defects. During this rerun:
- product code must remain unchanged from the stopped Executor snapshot;
- dependency pins remain unchanged;
- evaluator-owned repaired checkers may run;
- if any repaired mandatory check exposes a real product defect, Executor must stop and return to Evaluator rather than starting a third implementation cycle.

## Authorization remains unchanged

No commit, push, history rewrite, Sandbox/testnet/provider/wallet, production credential/PII, or real-payment authority is added.
