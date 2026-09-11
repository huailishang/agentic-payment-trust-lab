# Evaluator Amendment A1

Task ID: `P9-WEBSHOP-LIFECYCLE-EVIDENCE-CONTINUITY-CLOSURE-V1`  
Amendment: `A1 / baseline regression expectation repair`  
Date: `2026-09-11`

## Why this amendment exists

第一次完整 L2 得到 `6/7 PASS`。H-20 冻结能力目标已经达到，但通用 failed-fulfilment Trace Profile（失败履约轨迹配置）自然让项目固定基线中的 T11 Product Trace（产品轨迹）从 `NOT_AVAILABLE` 变为 `VALID`。

`tests/test_project_impact_baseline.py` 仍把旧的 T11 缺口、`8/12` matched、`4/12` gaps、GESR `8/12` 写成硬编码断言，因此 VP-07 full unittest discovery（全量单测发现）出现 5 个 stale expectation failures（过时期望失败）。Evaluator 已独立复现并确认这不是产品回归。

本 Amendment（修订）只解决 frozen contract（冻结合同）遗漏的测试范围问题，不改变 H-20 hypothesis（假设）、principal change（主要变化）、产品实现方向或测量边界。

## Allowed scope delta

在原 CONTRACT 的 Allowed Focused Tests（允许专项测试）之外，**额外允许且只允许**修改：

- `tests/test_project_impact_baseline.py`

允许修改内容仅限于：

- 将 T11 `payment_succeeded_fulfilment_failed` 的真实 Product Trace 状态更新为 `VALID`；
- 将与此直接派生的 matched/gap 计数从 `8/4` 更新为 `9/3`；
- 将与此直接派生的 GESR 从 `8/12` 更新为 `9/12`；
- 更新 `test_t10_target_closes_trace_and_end_to_end_dimensions` 中因 T11 现已 VALID 而变化的 matched/gap 计数；
- 保留 evaluator-synthesized replay（评估器合成回放）与 product-observed trace（产品观测轨迹）的 provenance separation（来源分离）断言，不得把两者混为一类证据。

## Explicitly forbidden

仍禁止修改：

- `scripts/validation/run_project_impact_baseline.py`；
- `samples/evaluation/project_impact_baseline_v1.json`；
- `samples/evaluation/project_impact_t10_preflight_target_v1.json`；
- H-18/H-20 runner、matrix、result audit；
- Payment / Recovery / Finality / Conflict / Lifecycle / Remediation；
- Sidecar Trace Toolkit；
- Authoritative Trace schema / validator / consumer / player；
- 已完成的 H-20 产品 registry 变化，除非原有测试证明其本身存在真实缺陷；
- 任何 T11/J03/fixture-id/金额/订单专用产品条件；
- 为了恢复旧 `8/12` 指标而人为让 T11 Product Trace 重新缺失。

## Frozen expected observations after repair

修复后的 `tests/test_project_impact_baseline.py` 必须与 runner 的真实输出一致，并继续验证：

```text
Product Trace completeness = 10/12
project matched tasks = 9/12
project gap tasks = 3/12
gap_task_ids = [T05, T06, T10]
GESR = 9/12
callback match = 12/12
duplicate/forbidden side effect = 0/12
unsafe allow = 0/5
repeat=3 all identical
```

其中 Product Trace `10/12` 与 matched/GESR `9/12` 不是同一个指标：T10 已有 VALID Product Trace，但其他冻结业务维度仍不匹配，因此仍是项目 GESR gap（端到端成功率缺口）。不得为了简化测试把两者混写。

## Evidence preservation

第一次失败已封存：

- `REPORT_ATTEMPT1_BLOCKED.md`
- `evidence/attempt1_blocked/**`

第二次执行继续使用顶层：

- `evidence/EV-*`
- `evidence/L2-GATE.json`
- `evidence/L2-GATE.md`
- `evidence/H20_LIFECYCLE_BRANCH_RESULT.json`
- `REPORT.md`

不得覆盖或删除 `attempt1_blocked`。

## Required rerun

Executor 在修改唯一允许新增的测试文件后，必须重新执行**原冻结 `VALIDATION_PLAN.yaml` 全部 7 项**，不能只跑 VP-07。

提交条件：

1. L2 `7/7 PASS`；
2. H-20 lifecycle `semantic=4/4`、`continuity=4/4` 保持；
3. Product Trace=`10/12`、GESR=`9/12` 与安全守护线保持；
4. full unittest discovery 零失败；
5. changed files 除原 H-20 五个文件外，只新增 `tests/test_project_impact_baseline.py`；
6. `REPORT.md` 明确说明 Attempt 1=`6/7 BLOCKED`、Attempt 2 的实际结果，以及本 A1 Amendment；
7. workflow validator（工作流校验器）通过后才可 `SUBMITTED_FOR_REVIEW`。

## Stop conditions

如果更新测试期望后仍存在以下任一情况，立即停止并交回 Evaluator：

- VP-07 仍有非 stale-expectation 类型失败；
- H-20 semantic 或 continuity 退化；
- T11 Trace 不能稳定复现；
- runner/fixture 必须修改才能通过；
- 安全守护线退化；
- 需要修改新的产品文件或增加 Case-specific logic（案例专用逻辑）。

## Authorization

本 Amendment 不增加任何外部权限：

- commit: false
- push: false
- history rewrite: false
- API/network: false
- dependency install: false
- real Buy Now/payment/order/fulfilment: false
