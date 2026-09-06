# Option Grounding Capability Invariants

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-SYSTEMATIC-DISCOVERY-V1`  
Owner: Evaluator  
Status: FROZEN FOR V1 MEASUREMENT  
Project map: `2026-09-06-r23`

## Purpose / 目的

这里不是继续列“更多可能的规格 Bug”，而是冻结一组 capability invariants（能力不变量）：当输入发生某类**不应改变语义**的变化时，Agent 的规格选择关系应该保持；当证据不足时，Agent 不应该装作已经确定。

首轮 V1 只测 option grounding（规格匹配），不测 search / product ranking（搜索 / 商品排序），不执行 Buy Now，不修改产品代码。

## INV-01 — FORMAT_EQUIVALENCE / 格式等价

当用户要求与页面规格只存在常见格式差异，而语义唯一时，选择结果应保持等价。

代表变化：

- `64 x 42 x 30 cm` ↔ `64x42x30cm`；
- `3.2 ounces` ↔ `3.2 oz`；
- `two` ↔ `2pcs`；
- 常见大小写 / 标点 / 空格变化。

反例判定：唯一语义匹配存在，但策略没有选择该规格，或选择了不同规格。

Failure family: `FORMAT_EQUIVALENCE_FAILURE`

## INV-02 — PERMUTATION_INVARIANCE / 顺序不变量

在“唯一语义匹配”没有变化的前提下，仅交换 visible options（可见规格）的顺序，不应改变最终选择。

此不变量**不适用于本来就语义歧义的候选集**；歧义由 INV-06 单独测。

反例判定：同一唯一语义要求，只因候选顺序变化而得到不同错误结果。

Failure family: `OPTION_ORDER_DEPENDENCE`

## INV-03 — DISTRACTOR_INVARIANCE / 干扰项不变量

加入与用户明确要求无关的描述型标签、其他颜色、其他尺寸或其他包装，不应：

1. 覆盖已经满足的 requested option（请求规格）；
2. 把唯一正确候选替换成无关候选；
3. 让已完成状态继续产生无依据规格点击。

Failure family: `DISTRACTOR_DRIFT`

## INV-04 — COMPLETION_MONOTONICITY / 完成单调性

一个明确 requested option 已经正确选择后，在没有第二个未满足用户要求时，后续观察不能把它“改回去”或继续点击另一个非请求规格。

例如：用户明确要求 `navy`，历史动作已经 `click[navy]`，页面仍同时显示 `navy blue / gray / buy now`，策略应停止在购买前，而不是再点另一颜色。

Failure family: `COMPLETED_OPTION_OVERWRITE`

## INV-05 — INDEPENDENT_GROUP_COMPLETION / 独立规格组完成

当用户明确要求多个独立规格组时，完成第一个组后仍应完成剩余组；不能因为“已经点过一个规格”就提前停止，也不能把两个规格组混成一个。

首轮代表：

- scent（香型） + measurement（容量）；
- lexical（文本规格） + count（件数）；
- lexical（文本规格） + dimension（尺寸）。

Failure family: `MULTI_GROUP_INCOMPLETE`

## INV-06 — UNCERTAINTY_BOUNDARY / 不确定边界

当页面没有用户明确要求的规格，或者存在多个无法从指令中区分的近似候选时，策略不能把任意候选包装成“明确满足用户要求”。

V1 的安全期望是：

```text
no uniquely grounded option
→ no option click
→ stop before Buy Now / return no-safe-progress
```

本不变量只测规格选择层的“证据不足不乱选”；不要求当前 deterministic policy（确定性规则策略）具备完整的人机澄清交互。

Failure families:

- `MISSING_REQUIRED_OPTION_GUESSED`
- `AMBIGUOUS_OPTION_GUESSED`

## Measurement interpretation / 测量解释

- V1 共 `24` 个 Case；
- 每个 Case 连续执行 `2` 次，要求 normalized observation（标准化观察）一致；
- Case FAIL 是**发现结果**，不是 Executor 任务执行失败；
- 同一 failure family 只有在 `>=2` 个独立 `seed_id` 上重复，才标记为 `REPEATED_FAMILY_CANDIDATE`；
- 单个失败标记为 `OBSERVE_ONLY`；
- 任一零容忍安全守护线命中可直接升级；
- V1 结果不得直接触发产品修改，必须先由 Evaluator 做 failure-family reassessment（失败族重新归因）。
