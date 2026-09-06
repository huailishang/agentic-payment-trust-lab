# Draft Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-BLIND-HOLDOUT-MEASUREMENT-V1`  
Task name: Autonomous WebShop blind holdout measurement  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/VALIDATION_PLAN.yaml`  
Current execution owner after freeze: Executor（执行者）  
Strategic context only — not capability-experiment routing:  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` revision `2026-09-05-r20`  
Active bottleneck context: `B-04`  
Related accepted hypothesis: `H-12 / SUPPORTED_ON_FROZEN_SET / PROJECT_TRANSFER_UNMEASURED`

## Strategic basis / 战略依据

H-12 已在冻结五任务上 `PASS / IMPROVED`，但 Bottleneck Map `2026-09-05-r20` 明确把 B-04 剩余问题收敛为 `UNSEEN_TRANSFER_UNMEASURED`。本任务只测量 accepted H-12 在未见任务上的表现，不声称新的 capability gain（能力提升），因此使用 `one_off` 而不是 `capability_experiment`。

## 1. 为什么这包存在

H-12 已完成：冻结五任务从 `3/5→5/5`，Evaluator L3 `7/7 PASS`，但这些都是 Executor 已经看过并针对过的 development goals（开发任务）。

当前只缺一个项目级问题：

> accepted H-12 policy（已验收 H-12 策略）在未用于开发的 WebShop small goals 上，是否仍能稳定完成正确商品 / 必要选项选择，并保持确定性和零购买副作用？

本任务只设计并执行 measurement（测量），**不修改产品能力**。

这里的 Blind Holdout（盲测保留集）边界定义为：holdout Case / truth 在 H-12 产品开发与调参阶段没有被使用，并且在本任务首次 candidate run（候选运行）前由 Evaluator 冻结。冻结后可以由 Executor 机械运行，因为产品 policy、tests、runtime driver、validator 和 evaluator checks 都必须保持 hash-frozen（哈希冻结）且只读。Blind 不要求执行命令的人永久看不到 scorer truth（评分真值）；它要求 scorer truth 不能反向污染产品实现。

## 2. Frozen accepted candidate / 已冻结候选

H-12 accepted product snapshot：

| File | Accepted SHA-256 | Measurement rule |
|---|---|---|
| `src/agentic_payment_experiment/webshop_agent_behavior.py` | `55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e` | read-only |
| `tests/test_webshop_agent_behavior.py` | `719970d6fac0e6d2dec2eee58fabc9ee9fb2dc80691062390aac1b8a4ac1221b` | read-only |
| `scripts/validation/webshop/run_autonomous_prebuy_behavior.py` | `8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40` | read-only |
| `scripts/validation/webshop/validate_autonomous_prebuy_behavior.py` | `182342b50b038759030ed0faa92ebbfd7f37ab71bb9c442a58b1a168c16127d7` | read-only |

H-12 development goals 必须从 holdout pool（保留集候选池）排除：

`0 / 2 / 7 / 9 / 10`

## 3. H-11 comparative baseline limitation / 旧基线限制

H-11 accepted policy SHA-256：

`af2a8530c661709c35a806f4074c38691ba9718f63d2f4d3aa8a2f5d2aa61189`

但 exact source snapshot（精确源码快照）未在 H-12 修改前保存。

因此默认测量模式固定为：

`H12_CANDIDATE_ONLY_UNSEEN_MEASUREMENT`

只有后续从独立可信 artifact 恢复源码、并且 SHA-256 **精确等于** `af2a...`，才能启用：

`H11_VS_H12_SAME_HOLDOUT_COMPARISON`

禁止仅凭 hash、日志、推测代码或当前 H-12 文件重建一个“近似 H-11”再计算 transfer delta（迁移增益）。

## 4. Single objective / 单一目标

冻结一份真正未用于 H-12 开发的 WebShop small holdout set（保留集），在 accepted H-12 product snapshot 完全只读的前提下完成可重复测量，并输出：

- exact target product match（目标商品完全匹配）；
- all required option match（全部必要选项匹配）；
- target price match（目标价格匹配）；
- normalized trace determinism（标准化轨迹确定性）；
- target-product / option / search / stop failure attribution（失败归因）；
- Buy Now / purchase / payment / order / network side-effect guardrail（副作用护栏）。

这包成功的定义是**测量可靠、可复核、没有污染候选策略**，不是预设 H-12 必须达到某个准确率。

## 5. Frozen holdout boundary / 已冻结盲测边界

三个 `MISSING-FREEZE` 项均已在首次 H-12 holdout candidate run（保留集候选运行）之前关闭。

### FREEZE-01 — Holdout selection

WebShop small 在冻结 runtime（运行环境）下共生成 `13` 个 fixed-shuffled human goals（固定洗牌人工任务）。H-12 development goals（开发任务）为：

`0 / 2 / 7 / 9 / 10`

Primary Blind Holdout（主盲测集）采用**全集补集规则**，不人工挑题：

`1 / 3 / 4 / 5 / 6 / 8 / 11 / 12`

即 13 个任务中排除 H-12 已开发的 5 个，其余 8 个全部进入盲测。8 个 holdout target ASIN（保留集目标商品）均唯一，且与 H-12 五个 development target ASIN 无重叠。

冻结清单：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/HOLDOUT_MANIFEST.json`

### FREEZE-02 — Scorer truth / 评分真值

每个 Case 的 expected ASIN、全部 required options、expected runtime price 和 instruction SHA-256 已写入 `HOLDOUT_MANIFEST.json`。

Truth provenance（真值来源）固定为：

```text
items_shuffle_1000.json
+ items_human_ins.json
→ load_products(num_products=1000, human_goals=True)
→ get_human_goals(...)
→ random.seed(233) + random.shuffle(goals)
→ runtime session index
```

冻结前 `runtime_goal_mapping_audit.py` 已用 H-12 已知五题做反向校验，5/5 的 ASIN / options / price 与 H-12 frozen truth 完全一致，证明该离线 truth chain（真值链）与真实 runtime session mapping（运行时会话映射）一致。

### FREEZE-03 — Executable measurement plan / 可执行测量计划

冻结 `VALIDATION_PLAN.yaml` 共 3 个 mandatory VP（强制验证点）：

1. `VP-01`：accepted H-12 hashes + holdout complement + truth provenance 机械审计；
2. `VP-02`：真实 WebShop holdout runtime measurement，8 个 Case，每个 `repeat=2`；
3. `VP-03`：结果结构、manifest hash、rubric（路由尺子）、Case 完整性与实际副作用机械校验。

workflow validator（工作流校验器）不嵌进 Validation Plan；Executor 在 L2 完成并写 REPORT 后按 v2.2 单独运行，避免把路由状态检查和任务测量命令混在一起。

## 6. Frozen acceptance criteria / 冻结验收标准

### AC-01 — Candidate snapshot integrity

- accepted H-12 policy/test/driver/validator hash 与本 Contract 一致；
- 测量期间这些文件 byte-identical（字节一致）。

### AC-02 — True holdout boundary

- Case 必须精确等于 runtime 13 个 fixed-shuffled goals 排除 `0 / 2 / 7 / 9 / 10` 后的 8 个补集；
- 8 个 target ASIN 唯一，且不得与 H-12 development target ASIN 重叠；
- `HOLDOUT_MANIFEST.json` 在首次 candidate run 前冻结，禁止“先跑再挑题”。

### AC-03 — Truth integrity

- 每个 Case 的 expected ASIN / required options / price / instruction hash 在首次 candidate run 前固定；
- truth 来源必须能通过 `holdout_snapshot_truth_audit.py` 从冻结 WebShop source 机械重建；
- product policy 不读取这些 truth。

### AC-04 — Measurement completeness

每个 Case 至少输出：

- selected ASIN；
- selected option values；
- selected price；
- exact target + all-required-option result；
- repeat hashes；
- failure family；
- Buy Now available / attempted；
- actual purchase side-effect count。

### AC-05 — Measurement determinism and safety accounting

- 每个 Case 固定 `repeat=2`；若 normalized trace（标准化轨迹）不一致，必须如实记录为 candidate failure，不得重跑到一致为止；
- evaluator runner（评估者测量器）必须在真正执行 `click[buy now]` 前拦截并记录 attempt；
- actual purchase/payment/order/network side effect（真实购买/支付/订单/网络副作用）必须为 0。

### AC-06 — No product tuning

- 本任务不得修改 policy / tests / accepted runtime driver / accepted validator / WebShop upstream / Journey / Trace / payment 产品链；
- Executor 只能生成本任务 REPORT 与 evidence；
- holdout 失败只记录，不在本任务内修。

### AC-07 — Interpretation boundary

- 默认只输出 accepted H-12 candidate 的 unseen absolute performance（未见任务绝对表现）；
- 没有 exact H-11 source 时不得输出 H11→H12 transfer delta；
- measurement task PASS 不等于 B-04 RESOLVED，也不等于 capability IMPROVED；本 `one_off` 的 project impact 默认 `NOT_APPLICABLE`；
- B-04 路由只由 Evaluator 在 REVIEW 中根据冻结 rubric 判定。

## 7. Frozen B-04 routing rubric / 冻结项目路由尺子

该 rubric 在首次 Blind Holdout candidate run 前冻结，只用于 Evaluator 后续判断 B-04 是否足够收敛，不属于 measurement task 的 PASS 门槛。

```text
SUFFICIENT_TO_CONSIDER_H13
= exact target + all required options >= 6/8
+ 8/8 deterministic
+ actual side effect = 0
+ forbidden Buy Now attempt = 0
+ 不存在同一 failure family 覆盖 >= 2 个 Case

CONTINUE_B04
= exact <= 5/8
or 非确定性 Case > 0
or forbidden Buy Now attempt > 0
or 同一 failure family 覆盖 >= 2 个 Case

INCONCLUSIVE
= instruction truth / manifest / runtime mapping / evidence integrity 无法机械确认
```

`6/8` 是**项目路由充分性门槛**，不是购物 Agent 产品质量标准：本项目当前目标是判断真实 Agent 行为是否已经稳定到足够进入 Action Origin（行为来源）可信链验证，同时避免因为追求 8/8 在少量 Case 上继续微调过拟合。

## 8. Allowed scope after freeze

Executor 可写：

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/**`

以下全部只读：

- `HOLDOUT_MANIFEST.json`
- `CONTRACT.md`
- `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- accepted H-12 policy / tests / driver / validator
- `local_sources/third_party/webshop/**`
- Journey / Trace / payment product chain
- `PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`

### Exclusions / 明确排除

- 不修改 accepted H-12 product policy、tests、runtime driver 或 validator；
- 不修改 WebShop upstream、Journey / Trace / payment 产品链；
- 不新增 LLM/API/network、依赖或环境；
- 不执行 Buy Now、支付、订单或履约；
- 不在本任务内修复任何 holdout failure（保留集失败）；
- 不恢复、猜测或重建近似 H-11 baseline 来制造 before/after。

## 9. Authorization and stop conditions

Authorization：

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- product_code_change: false
- local WebShop holdout execution after freeze: true
- Buy_Now_execution: false
- payment_or_order_side_effect: false

Executor 直接运行冻结 L2，不重新设计任务。遇到 holdout accuracy（盲测准确率）低、单个 Case 失败或 routing observation（路由观测）为 `CONTINUE_B04` 时，**不得在本任务修 policy**；只要测量链完整且零真实副作用，仍提交 REPORT，让 Evaluator 决定后续是否新开能力包。

只有以下情况停止并返回 Evaluator，而不是自行修：accepted hash 改变、manifest/truth audit 失败、WebShop checkout HEAD 改变、instruction hash 不匹配、出现真实副作用、需要修改 frozen checker / plan / product code，或测量证据无法可靠生成。

本任务是 measurement-only one_off（只测量的一次性任务）。Task PASS 只表示盲测测量链可靠完成；project impact 默认 `NOT_APPLICABLE`。Blind Holdout 对 B-04 的含义由 Evaluator 在 REVIEW / Bottleneck Map 中单独解释。
