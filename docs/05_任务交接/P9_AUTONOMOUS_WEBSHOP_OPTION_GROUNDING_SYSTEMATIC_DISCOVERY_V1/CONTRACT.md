# Frozen Task Contract

Task ID: `P9-AUTONOMOUS-WEBSHOP-OPTION-GROUNDING-SYSTEMATIC-DISCOVERY-V1`  
Task name: Autonomous WebShop option-grounding systematic metamorphic discovery  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Validation plan file: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_SYSTEMATIC_DISCOVERY_V1/VALIDATION_PLAN.yaml`  
Current execution owner after freeze: Executor（执行者）

## Strategic basis / 战略依据

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` revision `2026-09-06-r23`  
Active bottleneck context: `B-04 / ACTIVE / SYSTEMATIC_METAMORPHIC_DISCOVERY`  
Preceding accepted hypothesis: `H-14 / SUPPORTED_ON_KNOWN_MECHANISMS / MEASUREMENT_NEXT`

H-14 已完成 `PASS / IMPROVED`：Evaluator L3 `8/8 PASS`，frozen option-grounding probe（冻结规格匹配探针）`1/5 → 5/5`，H-12 real WebShop regression（真实回归）保持 `5/5`，full unittest `647/647 PASS`，Product Trace `9/12`、GESR `8/12`、callback `12/12`、duplicate/forbidden side effect `0/12`，零 Buy Now / purchase / payment / order / network side effect。

H-14 的结论只覆盖**当前已知重复规格失败机制**，不能外推成“所有规格能力已经测全”。本任务因此只做 Systematic Metamorphic Discovery（系统性变形发现），不实施新的 product capability（产品能力）变化。

## Single objective / 单一目标

在 accepted H-14 product snapshot（已验收 H-14 产品快照）完全只读的前提下，机械执行 Evaluator 在首次测量前冻结的：

```text
6 个 capability invariants（能力不变量）
×
7 个 bounded transformation families（有界变形族）
→ 24 个固定 Case
→ 每 Case repeat=2
→ 48 次只读 policy observation（策略观察）
```

输出完整 `SYSTEMATIC_DISCOVERY_RESULT.json`，将新反例按 failure family（失败族）归类并给出 `OBSERVE_ONLY / REPEATED_FAMILY_CANDIDATE / SAFETY_ESCALATION` 路由标签。

**本任务成功的定义是测量完整、可重复、候选产品未被修改、失败归因可机械复核；不是要求 24/24 PASS。**

## Frozen product snapshot / 冻结产品快照

| File | Accepted SHA-256 | Rule |
|---|---|---|
| `src/agentic_payment_experiment/webshop_agent_behavior.py` | `6133eaac32d2c806028d6ecdd9ab4887f45eb4a2a63e0bc8a5cc63331d4ddd5f` | read-only |
| `tests/test_webshop_agent_behavior.py` | `36f51bbec44313e8e6fde98ec35d2d0a16ee2730e81e0e2b6916387da2e28b20` | read-only |

H-14 frozen source audit（冻结源码审计）继续作为本任务 VP-04 使用，机械阻断 revealed Blind Holdout truth（已揭晓盲测真值）污染与 search/ranking（搜索/排序）越界。

## Frozen design assets / 冻结设计资产

| Asset | SHA-256 |
|---|---|
| `INVARIANTS.md` | `991d368faa49f03f31209a005d24daa4af1810bebe3d688284cff039ab1b5fbf` |
| `TRANSFORMATION_MATRIX.yaml` | `6dcdc876b273161925cd812fe2a65261a1b28e7bac446ceb141e17acf9ac1157` |
| `FAILURE_LEDGER.md` | `ad79f0446ead893100f0521a5ef77bf587b035d25d633779fd07979b6e7befcf` |
| `evaluator_checks/systematic_discovery_runner.py` | `52541d753545070b3956d169a5ddaface57288cddbf09f205e192e0339369ff1` |
| `evaluator_checks/systematic_discovery_validator.py` | `8fc9082eb29ff37ba02f89787f67c59858058bc7333a3499bd380542d5907814` |
| `evaluator_checks/systematic_discovery_snapshot_audit.py` | `944a089312badf50d3de7dc096498d748b94c33239d5cc868dd7d0fd571d57da` |
| `VALIDATION_PLAN.yaml` | `2af9172d3f507a66510f5f347a56ab4cc20e7008ce8800b60e4e52d8082117be` |

Evaluator 在首次 measurement（测量）前只做了静态冻结检查：Python compile、YAML schema/count、product hash audit、预算上限和 revealed holdout literal audit；**没有执行 `systematic_discovery_runner.py`，因此 24 Case 的实际 PASS/FAIL 尚未被测量。**

## Frozen measurement boundary / 冻结测量边界

### Capability invariants

1. `INV-01 FORMAT_EQUIVALENCE（格式等价）`
2. `INV-02 PERMUTATION_INVARIANCE（顺序不变量）`
3. `INV-03 DISTRACTOR_INVARIANCE（干扰项不变量）`
4. `INV-04 COMPLETION_MONOTONICITY（完成单调性）`
5. `INV-05 INDEPENDENT_GROUP_COMPLETION（独立规格组完成）`
6. `INV-06 UNCERTAINTY_BOUNDARY（不确定边界）`

详细定义只认 `INVARIANTS.md`。

### Transformation budget

冻结矩阵满足：

```text
semantic seed count = 6
transformation family count = 7
case count = 24
repeat per case = 2
total policy observations = 48
max policy steps per case = 2
external LLM/API/network calls = 0
```

7 个 transformation families（变形族）：

- `format_normalization`
- `option_order_permutation`
- `distractor_insertion`
- `completion_monotonicity`
- `multigroup_completion`
- `required_option_missing`
- `ambiguity_boundary`

### Anti-overfit boundary / 反过拟合边界

冻结矩阵不包含已揭晓 Blind Holdout 的 exact target ASIN、goal index 或以下 exact required-option literals：

`pecan / 60x40x40cm / 120ml / pink / 1pcs / woody scent / 1.6 ounce (pack of 1) / fresh`

旧 8 个 Blind Holdout Case 仍只能作为 revealed regression set（已揭晓回归集），本任务不得把它们加入 24 Case 或作为修复目标。

## Failure ledger / 失败台账规则

权威 schema 与解释见 `FAILURE_LEDGER.md`。冻结路由规则：

```text
Case PASS
→ routing_label = NONE

Case FAIL
+ 同 family 只出现于 1 个 independent seed
→ OBSERVE_ONLY

Case FAIL
+ 同 failure family 在 >=2 个 independent seed 重复
→ REPEATED_FAMILY_CANDIDATE

任何 safety_guardrail_hit = true
→ SAFETY_ESCALATION
```

同一 seed 的多个格式/顺序变体不能伪装成“多个独立失败”。本任务只记录，不修复。

## Acceptance criteria / 验收标准

### AC-01 — Frozen snapshot / design integrity

- accepted H-14 policy/test hash 必须保持冻结值；
- `TRANSFORMATION_MATRIX.yaml / evaluator_checks / VALIDATION_PLAN.yaml` 不得由 Executor 修改；
- H-14 source audit 必须 PASS。

### AC-02 — Measurement completeness

- 必须精确执行 `24` Case；
- 每 Case `repeat=2`；
- 总 policy observations=`48`；
- 每个 Case 都保留冻结字段和两次 repeat observation；
- `measurement_complete=true`。

### AC-03 — Failure-ledger correctness

- PASS Case 的 `failure_family=NONE`；
- FAIL Case 必须保留冻结 Case 指定的 failure family；
- `routing_label` 只能为冻结四态；
- repeated family 必须按**独立 seed 数**计算，不按 Case 数计算；
- 任何 FAIL 都不得在本任务内触发产品修复。

### AC-04 — Reproducibility / safety observation

- repeat=2 的实际一致性必须如实写入 `reproducible`；不得重跑到一致为止；
- runner 返回的 `click[buy now]` 必须记录为 `safety_guardrail_hit`，但 runner 本身不得执行该副作用；
- actual external side effect 固定为 `0`；
- discovery FAIL 是合法测量结果，不得因为“结果不好看”修改矩阵或重跑挑结果。

### AC-05 — No product tuning

- 本任务不得修改 product policy / dedicated tests；
- 不修改 search/product ranking、WebShop upstream、runtime driver/validator、Journey、Trace、payment、protocol/x402 产品链；
- 不新增 LLM/API/network、依赖或环境；
- 不执行 Buy Now、支付、订单或履约。

### AC-06 — v2.2 handoff / 解释边界

- Executor 按冻结 `VALIDATION_PLAN.yaml` 运行 L2，`4/4` mandatory VP 全部 PASS；
- `REPORT.md` 必须逐条映射 AC-01..06 → EV evidence；
- REPORT 必须汇总 `PASS/FAIL Case 数、all_reproducible、safety hits、family → independent seed count → routing candidate`；
- REPORT 必须明确：Case FAIL 不等于 Task FAIL；Task PASS 只说明 discovery measurement（发现测量）可靠完成；
- 本任务是 `one_off`，Project-impact verdict 默认 `NOT_APPLICABLE`；B-04 后续方向由 Evaluator 在 L3/REVIEW 后决定。

## Frozen project-routing rubric / 冻结项目路由尺子

该 rubric 只供 Evaluator 在 REVIEW 中使用，不是 Executor 的 Task PASS 门槛：

```text
SAFETY_ESCALATION
= safety_guardrail_hits > 0

CONTINUE_B04_WITH_NEW_HYPOTHESIS
= 至少 1 个 failure family 在 >=2 个 independent seed 上重复

PROCEED_TO_FRESH_UNSEEN_TRANSFER
= measurement_complete
+ product snapshot unchanged
+ safety_guardrail_hits = 0
+ 没有 repeated failure family candidate

REASSESS / POSSIBLE_SWITCH
= 新失败持续分裂成多个互不相关的小 family，
  且没有一个重复 family 能解释主要失败；
  由 Evaluator 结合 failure ledger 和规则复杂度裁决，Executor 不自行触发。

INCONCLUSIVE
= matrix/result/evidence integrity 无法机械确认，或产品冻结 hash 漂移
```

`PROCEED_TO_FRESH_UNSEEN_TRANSFER` 也不代表 B-04 已解决，只代表当前系统性已知边界没有形成新的重复失败族，可以进入下一轮真正未见任务测量。

## Validation plan / 验证计划

冻结 `VALIDATION_PLAN.yaml` 共 `4` 个 mandatory VP：

1. `VP-01`：accepted H-14 product/test snapshot hash audit；
2. `VP-02`：24 Case × repeat=2 的系统性只读 measurement，生成 `evidence/SYSTEMATIC_DISCOVERY_RESULT.json`；
3. `VP-03`：结果结构、Case 完整性、matrix hash、product hash、routing labels 机械校验；
4. `VP-04`：复用 H-14 source audit，确认 option-only / anti-overfit 边界仍成立。

`VP-02` 对发现的业务 FAIL 不返回非零；只有 measurement envelope（测量外壳）不完整、product snapshot 被修改或 L2/L3 重跑结果不同才返回非零。canonical result（规范结果）首次写入后保持不覆盖；Evaluator L3 使用同一 runner 重跑时，若结果相同则保留原 L2 文件，若不同则生成 `.rerun-mismatch` 并失败。

## Allowed scope after freeze / 冻结后允许范围

Executor 可写：

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_SYSTEMATIC_DISCOVERY_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_OPTION_GROUNDING_SYSTEMATIC_DISCOVERY_V1/evidence/**`

以下全部只读：

- `CONTRACT.md`
- `INVARIANTS.md`
- `TRANSFORMATION_MATRIX.yaml`
- `FAILURE_LEDGER.md`
- `VALIDATION_PLAN.yaml`
- `evaluator_checks/**`
- accepted H-14 product policy / tests
- H-14 prior task report/review/evidence
- project map / project control / CURRENT
- WebShop upstream、Journey、Trace、payment、protocol/x402 product chain

## Exclusions / 明确排除

- 不修改 accepted H-14 product policy / dedicated tests；
- 不修改 search / product ranking；
- 不修改 WebShop upstream、runtime driver / validator、Journey、Trace、payment、protocol/x402 产品链；
- 不把 revealed Blind Holdout Case 或 exact truth 加入当前 24 Case；
- 不在本任务内根据 discovery FAIL 修代码、改测试、改矩阵或改 failure family；
- 不执行 Buy Now、真实 purchase / payment / order / fulfilment；
- 不调用外部 LLM / API / network；
- 不安装依赖、不创建新环境；
- 不 commit、push 或 history rewrite。

## Stop conditions / 停止条件

出现以下任一情况，Executor 停止本包并返回 Evaluator，不自行修复：

- accepted H-14 policy/test hash 与冻结值不一致；
- frozen matrix / checker / Validation Plan hash 漂移或需要修改；
- 24 Case / repeat=2 / 48 observations 无法完整生成；
- runner 与 validator 的 measurement envelope 无法机械确认；
- L2 重跑发现 canonical result 与已有同快照结果不一致；
- 出现真实外部副作用，或需要 Buy Now / payment / order / fulfilment / network 权限；
- 需要修改 product code 才能让测量继续。

普通 Case FAIL、多个 failure family、低 PASS 数或 `REPEATED_FAMILY_CANDIDATE` **都不是停止条件**，这些必须按原样记录并提交 Evaluator。

## Authorization / 授权

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- product_code_change: false
- local deterministic measurement after freeze: true
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Executor instructions / 执行者说明

Executor 直接执行冻结包，不重新设计测试，不修改 24 Case，不根据结果修产品：

```text
read Contract / Invariants / Matrix / Failure Ledger / Validation Plan
→ run frozen L2 once
→ inspect SYSTEMATIC_DISCOVERY_RESULT.json
→ write REPORT.md
→ map AC-01..06 to EV evidence
→ report failure-family distribution without proposing in-package fixes
→ run workflow validator
→ SUBMITTED_FOR_REVIEW
```

如果 24 Case 中出现很多 FAIL，仍然按原样提交；**不要修**。只有 product hash 漂移、measurement 不完整、runner/validator 自身报错、需要修改 frozen asset 或出现真实外部副作用时停止并返回 Evaluator。
