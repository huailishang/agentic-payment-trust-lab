# Evaluator Continuation Note — H-12 复核后的路由

> Owner: Evaluator（评估者）  
> Date: 2026-09-05  
> Status: `REALIZED / SUPERSEDED_BY_REVIEW（已执行，以 REVIEW 为准）`  
> H-12 verdict: `PASS / IMPROVED / CONTINUE`  
> Authoritative review: `REVIEW.md`

## 1. H-12 已完成

H-12 已由 Evaluator 独立复核：

```text
frozen five-goal development set
3/5 → 5/5

L3 independent gate
7/7 PASS

full unittest
643/643 PASS

Buy Now / purchase / payment / order / network side effect
0
```

因此不再给 Executor 继续调 goals `0 / 2 / 7 / 9 / 10`。B-04 仍保持 ACTIVE，因为 frozen-set（冻结开发集）成功不等于 unseen-task transfer（未见任务迁移）成立。

## 2. Evaluator 反例

Evaluator 对 goal 2 报告中的 encoded-color ambiguity（编码颜色歧义）构造了等价 UI 顺序反例：

```text
instruction = black loafers

[black1901, black2003] → black2003
[black2003, black1901] → black1901
```

`order_invariant=false`。

这个结果不推翻 H-12 的 Task PASS，因为“等价 UI 重排不变性”不是冻结 mandatory AC（强制验收项）；但它限制了项目级解释：当前 `5/5` 不能外推为通用语义泛化。

证据：`evidence/RV-EV-08-TIEBREAK-COUNTEREXAMPLE.json`。

## 3. H-11 比较基线的证据限制

H-11 是 accepted-but-uncommitted（已验收但未提交）快照。H-12 Contract 记录的 H-11 policy SHA-256 为：

`af2a8530c661709c35a806f4074c38691ba9718f63d2f4d3aa8a2f5d2aa61189`

但 H-12 修改同一个未跟踪文件之前，没有保存 H-11 exact source snapshot（精确源码快照）。因此当前仓库不能机械重跑真正的 H-11 policy。

后续规则固定为：

- 不得把当前 H-12 policy 冒充 H-11 baseline；
- 不得仅凭 H-11 hash 伪造 before / after（前后对比）；
- 如果以后从独立可信 artifact 恢复源码，只有 SHA-256 精确等于 `af2a...` 才能作为 H-11 comparative baseline（比较基线）；
- 在此之前，Blind Holdout（盲测保留集）的默认口径是 **accepted H-12 candidate-only unseen measurement（只测 H-12 已验收候选在未见任务上的绝对表现）**。

当前 H-12 submitted snapshot（提交快照）已保存：

`evaluator_baseline/H12_SUBMITTED_webshop_agent_behavior.py.snapshot`

SHA-256：`55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e`。

## 4. 下一步 Blind Holdout Measurement

下一包：

`P9-AUTONOMOUS-WEBSHOP-BLIND-HOLDOUT-MEASUREMENT-V1`

Task kind：`one_off`。当前处于 `DRAFT_CONTRACT / Evaluator`；评估者先冻结 holdout Case / truth / checker / Validation Plan，冻结后再按 v2.2 转给 Executor 做只读机械测量。

只回答：

> accepted H-12 policy 在 Executor 未针对过的 WebShop small goals 上，表现是否足以支持 B-04 继续向后收敛？

必须冻结：

- accepted H-12 policy hash；
- 排除 H-12 开发 goals `0 / 2 / 7 / 9 / 10` 的 unseen goal selection（未见任务选择）；
- scorer truth（评分真值）；
- runtime / seed / repeat；
- exact target + required-option measurement（完全匹配测量）；
- failure attribution（失败归因）；
- normalized trace determinism（标准化轨迹确定性）；
- Buy Now / purchase / payment / order / network side-effect guardrail（副作用护栏）；
- stop condition（停止条件）。

Blind Holdout 测量期间，以下文件默认只读：

```text
src/agentic_payment_experiment/webshop_agent_behavior.py
tests/test_webshop_agent_behavior.py
scripts/validation/webshop/run_autonomous_prebuy_behavior.py
scripts/validation/webshop/validate_autonomous_prebuy_behavior.py
local_sources/third_party/webshop/**
Journey / Trace / payment product chain
```

不得边测边修，也不得因为 holdout 失败就直接给产品打补丁。

## 5. Blind Holdout 之后的路由

```text
unseen evidence 足够、主要失败已明显收敛、安全护栏不退化
→ Evaluator 结合剩余失败簇与边际收益判断 B-04 是否足够收敛
→ 只有证据支持时才激活 H-13 Action Origin（行为来源）

unseen evidence 暴露集中、可泛化的新失败族
→ B-04 保持 ACTIVE
→ Evaluator 冻结一个新的 generalization hypothesis（泛化假设）
→ 再给 Executor 一个新的有界能力包

measurement 本身不可靠
→ INCONCLUSIVE
→ 先修测量，不改产品
```

x402、Cross-Rail、Cross-Protocol、真实钱包 / 密钥 / 测试网、剩余 Trace coverage 继续作为 Future / WATCH（未来 / 观察）方向，不因 H-12 五题通过而提前抢占主线。
