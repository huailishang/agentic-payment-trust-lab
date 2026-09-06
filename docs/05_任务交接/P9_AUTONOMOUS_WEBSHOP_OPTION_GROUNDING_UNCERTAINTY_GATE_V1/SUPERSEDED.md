# H-15 Superseded Before Execution

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-UNCERTAINTY-GATE-V1`  
Evaluator decision date: 2026-09-06  
Disposition: `SUPERSEDED_BEFORE_EXECUTION`

## Why this package is no longer CURRENT

H-15 was frozen after Systematic Metamorphic Discovery found a repeatable `INV-06 UNCERTAINTY_BOUNDARY` limitation. Before Executor execution began, the project owner and Evaluator rechecked the higher-level P9 roadmap and confirmed that the payment-trust project is not intended to optimize WebShop intent / option understanding until its long tail is exhausted.

The purpose of B-04 was to establish and pressure-test real autonomous Agent behavior in an external commerce environment, expose representative failure modes, and make that behavior available to the trust / payment chain. That evidence now exists:

- autonomous pre-Buy-Now behavior has been captured and independently reviewed;
- H-12 real five-goal set reached `5/5`;
- Blind Holdout measured `3/8` and proved non-trivial generalization limits;
- H-14 repaired one repeated option-grounding mechanism from `1/5 -> 5/5`;
- Systematic Discovery measured `19/24`, with all 48 observations reproducible and zero safety hits;
- the remaining uncertainty / intent long tail is therefore a known capability boundary, not the next project-level mainline.

## Execution status at supersession

No Executor work had started under H-15 when the route changed:

- no `REPORT.md` existed;
- no H-15 L2 `evidence/**` existed;
- `src/agentic_payment_experiment/webshop_agent_behavior.py` and `tests/test_webshop_agent_behavior.py` had not changed after H-15 was frozen;
- no commit / push / API / network authorization had been used.

Therefore no completed Executor work is discarded by this reroute.

## What remains useful

Do not delete this package. Keep the following as `Known Limitation / Regression Asset（已知限制 / 回归资产）`:

- `evaluator_baseline/BASELINE_UNCERTAINTY_GATE.json` (`2/5 PASS` baseline);
- `evaluator_checks/uncertainty_gate_probe.py`;
- Systematic Discovery `19/24` result and failure ledger;
- H-14 `5/5` probe and prior real WebShop regressions.

These assets can be reused when the Agent policy/model is materially changed, or when later project evidence shows that intent / option uncertainty is blocking a trust-chain capability.

They are no longer a blocking gate for H-13.

## New routing principle

```text
Autonomous Agent behavior
→ representative capability + failure evidence established
→ long-tail intent / option errors recorded as WATCH / regression assets
→ Action Origin / Responsibility Trace becomes the next mainline
→ Governed Payment Action
→ Payment / Finality / Fulfillment / Recovery
→ Evidence / Replay / Accountability
```

No Task PASS or Project IMPROVED verdict is claimed for H-15 because the capability experiment was never executed.
