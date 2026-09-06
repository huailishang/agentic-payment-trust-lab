# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-GENERALIZATION-V1`  
Task name: Autonomous WebShop option-grounding generalization  
Task kind: `capability_experiment`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-06-r22`  
Active bottleneck: `B-04`  
Hypothesis: `H-14`  
Dispatch: `SINGLE`  
Metric baseline: H-14 synthetic/metamorphic option-grounding probe `1/5 PASS`；H-12 five-goal real WebShop regression `5/5`。  
Estimated affected scope: Blind Holdout 5 个失败中 4 个属于 `REQUIRED_OPTION_MISMATCH`，约占当前已知失败的 `4/5`；这是 failure-family scope estimate（失败族范围估算），不是 revealed holdout 提分承诺。  
Expected project impact: H-14 synthetic/metamorphic probe `1/5 → 5/5`，H-12 real regression 保持 `5/5`，并保持 Product Trace `9/12`、GESR `8/12`、callback `12/12`、duplicate/forbidden side effect `0/12`。  
Rollback condition: synthetic probe 无法稳定到 `5/5`、H-12 regression 或项目守护线退化、需要第二个 principal change、需要 revealed holdout truth、或需要修改 search/product ranking。

Blind Holdout（盲测保留集）已由 Evaluator 独立复核：8 个原未见任务 exact target + all required options（目标商品 + 全部必要规格完全匹配）为 `3/8`，deterministic（确定性）为 `8/8`，且 Buy Now / purchase side effect（购买副作用）为 `0 / 0`。5 个失败中：

```text
REQUIRED_OPTION_MISMATCH = 4
TARGET_PRODUCT_MISMATCH = 1
```

因此当前最值得投入的单一方向是 option grounding（规格依据用户要求进行匹配），而不是同时修改 search/product ranking（搜索 / 商品排序）。H-13 Action Origin（行为来源）继续后置。

## Inherited accepted product snapshot / 继承快照

H-12 accepted product snapshot（已验收产品快照）仍为未提交工作区状态，本任务继承该快照而不是假设 baseline HEAD 已包含实现：

| File | Baseline SHA-256 |
|---|---|
| `src/agentic_payment_experiment/webshop_agent_behavior.py` | `55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e` |
| `tests/test_webshop_agent_behavior.py` | `719970d6fac0e6d2dec2eee58fabc9ee9fb2dc80691062390aac1b8a4ac1221b` |
| `scripts/validation/webshop/run_autonomous_prebuy_behavior.py` | `8c3b1b893449502dd2096cc86ac5b6ada693468667acde10f1c01c2064109a40` |
| `scripts/validation/webshop/validate_autonomous_prebuy_behavior.py` | `182342b50b038759030ed0faa92ebbfd7f37ab71bb9c442a58b1a168c16127d7` |

Evaluator 另存的 H-14 baseline snapshots（基线快照）：

- `evaluator_baseline/H14_BASELINE_webshop_agent_behavior.py.snapshot` = `55f2...436e`；
- `evaluator_baseline/H14_BASELINE_test_webshop_agent_behavior.py.snapshot` = `7199...221b`。

## Measured baseline / 已测基线

H-14 不把已揭晓的 8 个 Blind Holdout Case 直接作为开发目标。Evaluator 在首次 H-14 产品修改前冻结了一组与其 exact values（精确值）不同的 synthetic/metamorphic probe（合成 / 变形探针）：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/evaluator_checks/option_grounding_probe.py`

- checker SHA-256: `87ec6a9bff918fd06de2ab47723436466c2dc2c3aa4ce72b4e27b2649f4f9932`；
- baseline artifact: `evaluator_baseline/BASELINE_OPTION_GROUNDING.json`；
- baseline artifact SHA-256: `e18fab13f975e8c451c788a3e89029849f09d02b568cf06ce008fbfdb0b8edee`；
- baseline: `1/5 PASS`；
- target: `5/5 PASS`。

五类 probe（探针）覆盖：

1. 普通文本规格；
2. 已满足请求规格后不得被商品描述词误覆盖；
3. 尺寸格式规范化；
4. 数量词与 `Npcs` 映射；
5. 多个独立 option group（规格组）连续完成。

**Coverage boundary（覆盖边界）**：这 5 个 probe 是针对当前已暴露失败族冻结的代表性机制样本，不是 option-grounding（规格匹配）能力全集。Executor 即使把 `1/5 → 5/5`，也只能声明“当前 H-14 已知失败机制得到修复并通过冻结验证”，不得声明“规格细节已经测全 / 泛化已经最终证明”。H-14 通过后的下一步由 Evaluator 单独冻结：

```text
Systematic Metamorphic Discovery（系统性变形发现）
→ Fresh Unseen Transfer Measurement（新鲜未见迁移测量）
→ Failure-family Reassessment（失败族重新归因）
```

其中系统性发现优先围绕 capability invariants（能力不变量）生成格式、顺序、干扰项、多规格组、缺失/歧义等变形反例；该阶段不属于本 H-14 Executor 的实现范围，不得为了“提前覆盖更多细节”扩大当前 principal change。

Source audit（源码边界审计）已冻结：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/evaluator_checks/option_grounding_source_audit.py`

SHA-256: `99879289129a308cb092be4759e20e05dbfd919501ab9c1354fb75bb3c2081d5`。

## Single objective / 单一目标

只修改 deterministic local policy（确定性本地策略）的 option-grounding rule family（规格匹配规则族），使同一通用机制能够：

```text
识别用户仍未满足的规格要求
→ 规范化匹配可见规格标签
→ 避免已满足规格被非请求属性覆盖
→ 支持多个独立规格组连续完成
```

并把冻结 H-14 synthetic/metamorphic probe 从 `1/5 → 5/5`，同时保持 H-12 五任务真实 WebShop regression（回归）`5/5` 与全部安全 / 项目守护线不退化。

本任务**不解决** Blind Holdout 中唯一的 `TARGET_PRODUCT_MISMATCH（目标商品不匹配）`。

## Principal change / 唯一主要变化

允许的 principal change（主要变化）仅为：

> `_instruction_option` 及其直接服务于 option grounding（规格匹配）的通用辅助逻辑，对“用户要求 → 可见规格 → 已满足规格状态”进行更可靠的匹配和跟踪。

可以实现通用的文本规范化、数字 / 尺寸 / 数量表达归一、requested attribute（用户请求属性）识别、已消费规格跟踪等；但不能加入与某个 WebShop goal / ASIN / exact holdout option 绑定的特例。

以下函数由 frozen source audit（冻结源码审计）保护，必须保持与 H-14 baseline byte-equivalent function source（函数源码等价）：

- `_search_query`
- `_significant_terms`
- `_budget`
- `_choose_result`

因此本包不得顺手修改搜索、商品排序或预算解析。

## Acceptance criteria / 验收标准

### AC-01 — Policy boundary / 策略输入与源码边界

- `AgentPolicyInput` 仍严格为五字段：`instruction_text / observation / available_actions / step_index / previous_actions`；
- policy 不读取 server、goal object/index、expected ASIN/options/price、product dict、evaluator labels 或 WebShop 数据文件；
- 不新增 network/runtime data import；
- `option_grounding_source_audit.py` PASS。

### AC-02 — Synthetic/metamorphic option-grounding capability

- 冻结 `option_grounding_probe.py --require-all` 必须从 baseline `1/5` 提升到 `5/5`；
- 五类行为均由同一 option-grounding rule family 通过；
- 不允许通过修改 evaluator checker、baseline artifact 或 Validation Plan 达成。

### AC-03 — Generic option semantics / 通用规格语义

实现必须能解释为通用机制，而不是五个 probe 各写一个分支：

- 已满足的显式 requested option（请求规格）不得被商品描述词等无关 visible option（可见规格）覆盖；
- 尺寸、数量、包装等表达允许通过通用 normalization（规范化）匹配；
- 多个独立 option group 中，只继续选择仍未满足的用户要求；
- dedicated tests（专用测试）应使用与 Blind Holdout 不同的合成值验证规则。

### AC-04 — Revealed holdout anti-overfit / 已揭晓盲测反过拟合

以下 8 个原 Blind Holdout Case 已揭晓，后续只能视为 revealed regression set（已揭晓回归集）。本任务不得在 product policy 或 dedicated tests 中引入它们的：

- target ASIN；
- goal index；
- exact required-option literals，包括 `pecan`、`60x40x40cm`、`120ml`、`pink`、`1pcs`、`woody scent`、`1.6 ounce (pack of 1)`、`fresh`；
- 任何等价的 Case 专用 action sequence（动作序列）或分支。

`option_grounding_source_audit.py` 必须机械阻断这些污染。

### AC-05 — One principal change / 不越界到商品排序

- Product behavior change 只允许落在 `src/agentic_payment_experiment/webshop_agent_behavior.py` 的 option-grounding 逻辑与其 dedicated tests；
- `_search_query / _significant_terms / _budget / _choose_result` 必须与 H-14 baseline 保持不变；
- runtime driver、result validator、WebShop upstream、Journey、Trace、payment、protocol 实现均不得修改。

### AC-06 — H-12 real WebShop regression / 既有五任务不退化

冻结 H-12 multigoal runtime audit（多任务真实运行审计）必须保持：

- goals `0 / 2 / 7 / 9 / 10` 全部 `5/5 PASS`；
- `repeat_per_goal=2`；
- target ASIN 与全部 required options 正确；
- normalized trace deterministic（标准化轨迹确定）；
- Buy Now 不执行；purchase / payment / order / network side effect 为 0。

注意：这五题是既有回归集，不是 H-14 的新 capability gain（能力增益）来源。

### AC-07 — Project guardrails / 项目守护线

- Journey Player + Journey Read Model focused regression PASS；
- `run_experiment.py` 正式入口保持 `13/13 PASS`；
- project-impact baseline repeat=3 PASS，并保持 Product Trace `9/12`、GESR `8/12`、callback match `12/12`、duplicate/forbidden side effect `0/12`；
- full unittest discovery 零新增失败；
- 不产生 Buy Now / purchase / payment / order / network / fulfilment side effect。

### AC-08 — v2.2 handoff / 证据与交接

- Executor 按冻结 `VALIDATION_PLAN.yaml` 运行 L2，8/8 mandatory VP 全部 PASS；
- `REPORT.md` 逐条映射 AC-01..08 → EV evidence（执行证据），并明确 H-14 metric `1/5 → 5/5`；
- REPORT 必须记录 changed files、最终 product/test hashes、实际 bounded repair 次数、任何失败/偏差；
- REPORT 必须单列 `Coverage / Residual Unknowns（覆盖与残余未知）`：明确 5 个 probe 只是已知失败机制代表样本，列出本包未穷举的规格空间，并禁止把 `5/5` 写成“规格能力已测全”；
- workflow validator 返回 `OK` 后才能提交；
- Executor 只能 `SUBMITTED_FOR_REVIEW`，不得自行给出 Task `PASS` / Project `IMPROVED`。

## Allowed scope / 允许修改

Executor 可修改：

- `src/agentic_payment_experiment/webshop_agent_behavior.py`
- `tests/test_webshop_agent_behavior.py`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/evidence/**`

Evaluator-owned frozen files（评估者冻结文件）全部只读：

- `CONTRACT.md`
- `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- `evaluator_baseline/**`
- `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
- `CURRENT.md`
- prior task reports / reviews / evidence

## Exclusions / 明确排除

- 不修改 `_choose_result` 或 search query generation；
- 不修 Blind Holdout 唯一 `TARGET_PRODUCT_MISMATCH`；
- 不使用已揭晓 holdout truth 指导 product/test 代码；
- 不修改 WebShop upstream；
- 不修改 runtime driver / validator；
- 不修改 Journey / Trace / payment / Runtime Gate / protocol / x402；
- 不新增 LLM / API / network / browser automation；
- 不安装依赖、不新建环境；
- 不执行 Buy Now、支付、订单、履约或外部 callback；
- 不 commit、push、history rewrite。

## Validation plan / 验证计划

Frozen plan:

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_GENERALIZATION_V1/VALIDATION_PLAN.yaml`

| VP | 检查 | AC |
|---|---|---|
| VP-01 | dedicated policy unit tests | AC-01,03,05,08 |
| VP-02 | frozen H-14 synthetic/metamorphic probe `5/5` | AC-02,03,08 |
| VP-03 | option-only + anti-overfit source audit | AC-01,04,05,08 |
| VP-04 | H-12 five-goal real WebShop regression `5/5` | AC-06,07 |
| VP-05 | Journey focused regression | AC-07 |
| VP-06 | formal experiment entrypoint | AC-07 |
| VP-07 | project-impact baseline repeat=3 | AC-07 |
| VP-08 | full unittest discovery | AC-07 |

## Bounded Executor loop / 有界执行循环

这是本地、无外部 API 成本的 capability experiment，但仍禁止开放式调参。

- max implementation→L2 cycles: `3`；
- 每轮必须保持同一 H-14 hypothesis、同一 principal change、同一 frozen probe、同一 source audit；
- L1（快速检查）可以在每轮内多次运行 dedicated tests / probe；
- 只有一轮准备提交时才需要完整跑全部 L2；若完整 L2 失败，可在剩余 cycle 内做 contract 内 repair（合同内修复）后再完整跑；
- 任何修改商品 ranking/search、checker、truth、Validation Plan 或允许范围的需求立即停止并返回 Evaluator；
- 不得因为 revealed holdout score（已揭晓回归分数）未提高而扩大本包。

## Expected project impact / 预期项目影响

Measured baseline（已测基线）：H-14 synthetic/metamorphic option-grounding probe `1/5`。  
Expected after（预期结果）：`5/5`，且 H-12 real WebShop regression `5/5` 与全部安全 / 项目指标不退化。  
Estimated affected scope（估计影响范围）：Blind Holdout 5 个失败中 4 个属于同一 `REQUIRED_OPTION_MISMATCH` failure family；因此该机制理论上覆盖当前已知失败的约 80%（4/5），但这只是 failure-family scope estimate（失败族范围估算），不是承诺 revealed holdout 必然提升到某个分数。  
Cost（成本）：本地 Python/WebShop runtime 与全量测试，无外部 API/网络/支付费用；主要成本为本地运行时间与少量 policy complexity（策略复杂度）。  
Rollback condition（回退条件）：synthetic probe 无法稳定到 5/5、H-12 real regression 退化、守护线退化、需要第二个 principal change、或需要任何 holdout truth / ranking/search 修改。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- local WebShop runtime execution: true
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Stop conditions / 停止条件

立即停止并交还 Evaluator，如果出现任一情况：

1. frozen probe / source audit / Validation Plan 需要修改；
2. 实现需要触碰 `_choose_result`、搜索逻辑或 `TARGET_PRODUCT_MISMATCH`；
3. 需要引入已揭晓 holdout exact values 或 hidden truth；
4. 需要修改 runtime driver / validator / upstream / Journey / Trace / payment chain；
5. 三个 bounded cycles 用完仍无法满足 L2；
6. H-12 five-goal regression 从 `5/5` 下降；
7. 任一安全守护线退化或出现 Buy Now / purchase / payment / order / network side effect；
8. 需要任何当前为 false 的授权。
