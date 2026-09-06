# Executor Report — Repair Attempt 2

Task ID: `P9-AUTONOMOUS-WEBSHOP-BLIND-HOLDOUT-MEASUREMENT-V1`  
Executor status: SUBMITTED_FOR_REVIEW  
Baseline HEAD: `57ded7bb2fb0ca830748b35b857a8d07624fe3d4`  
Implementation commit: `NONE`

## Workspace snapshot

- Workflow: `evaluator-executor-workflow/v2.2`。
- Task kind: `one_off` Blind Holdout measurement(盲测保留集测量)。
- Human / Task Owner 在第一次 L2 integrity failure(测量完整性失败)后，明确授权 Executor 对 instruction hash mismatch(指令哈希不一致)做有界修复，并要求两份报告一起落盘。
- Authorization amendment: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/EXECUTOR_AUTHORIZED_REPAIR_AMENDMENT.md`。
- 第一次失败报告保留为 `REPORT_ATTEMPT1_BLOCKED.md`；第一次 EV/L2/HOLDOUT_RESULT 保留在 `evidence/attempt1_blocked/`。
- 无 commit、push、history rewrite、external API/network、Buy Now、payment、order 或 fulfilment。

## Changed files

本次有界修复只新增/修改 measurement(测量)与证据层：

- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evaluator_checks/holdout_runtime_measurement.py`
  - before SHA-256: `cc30dfc72645700d91686b45a5cb24ee13738a3e1943fde1e1440cdae1b42a43`
  - after SHA-256: `8c3ae7c7d051f45177962fe803992fa7b672c0462ffa1f6a1a9ec9e8c4ec8450`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/EXECUTOR_AUTHORIZED_REPAIR_AMENDMENT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT_ATTEMPT1_BLOCKED.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/**`

以下关键冻结对象未变化：

- policy SHA-256: `55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e`
- manifest SHA-256: `6cf9f11146726a7ca68ecd5cdfa334af4b6e247cf95971c6e4972bfe0248be24`
- accepted runtime driver / accepted product validator 未修改；
- holdout Case、expected ASIN、required options、expected price、routing rubric 未修改；
- product policy(产品策略)未修改。

## 1. Root cause / 根因

第一次运行出现：offline truth audit(离线真值审计) 8/8 PASS，但 runtime instruction hash(运行时指令哈希) 0/8。

诊断证据 `evidence/diagnose_instruction_hash.stdout.txt` 证明：

```text
runtime instruction = "Instruction: " + canonical goal instruction
manifest hash        = SHA256(canonical goal instruction)
server goal hash     = manifest hash
```

8 个 Case 全部是同一个固定展示层差异：WebShop 页面在真实 instruction 前自动增加 `Instruction: `，长度正好多 13 个字符。

因此第一次 `0/8` 不是 scorer truth(评分真值)漂移，也不是 runtime goal mapping(运行时任务映射)错误，而是 measurement hash boundary(测量哈希边界)把页面标签一起算进去了。

## 2. Single principal repair / 单一修复

`holdout_runtime_measurement.py` 新增：

```text
canonical_instruction_text(value)
```

规则只有一条：

- 若 runtime instruction 以固定页面前缀 `Instruction: ` 开头，hash 前移除该前缀；
- 否则保持原文不变。

注意：**传给 product policy 的 instruction 没有改变**；只修改 measurement integrity check(测量完整性校验)使用的 canonical hash input(规范哈希输入)。

## 3. Repair result / 修复结果

修复后只重新执行一次同一份冻结 `VALIDATION_PLAN.yaml`：

| 指标 | Attempt 1 | Attempt 2 |
|---|---:|---:|
| instruction hash match | `0/8` | `8/8` |
| exact target + all required options | `3/8` | `3/8` |
| deterministic | `8/8` | `8/8` |
| `REQUIRED_OPTION_MISMATCH` | `4` | `4` |
| `TARGET_PRODUCT_MISMATCH` | `1` | `1` |
| forbidden Buy Now attempt | `0` | `0` |
| actual side effect | `0` | `0` |
| routing_observation | `INCONCLUSIVE` | `CONTINUE_B04` |

`evidence/ATTEMPT_COMPARISON.json` 进一步逐 Case / run 比对：

- selected ASIN(选中商品)一致；
- selected options(选中选项)一致；
- selected price(选中价格)一致；
- score(评分结果)一致；
- action steps(动作步骤)一致；
- failure family(失败类型)一致；
- policy hash / manifest hash 一致。

因此修复**没有让购物策略表现变好**；只是把 `instruction_hash_match` 从错误的 `0/8` 修正为可信的 `8/8`，从而让第一次已经观察到的 `3/8` 成为正式可解释结果。

## 4. Formal holdout observation / 正式盲测结果

measurement integrity(测量完整性)现在为 `COMPLETE`，因此正式结果是：

- exact match: **`3/8`**；
- deterministic: **`8/8`**；
- instruction truth match: **`8/8`**；
- forbidden Buy Now attempt: **`0`**；
- actual purchase/payment/order/network side effect: **`0`**；
- repeated failure family: `REQUIRED_OPTION_MISMATCH = 4`；
- other failure family: `TARGET_PRODUCT_MISMATCH = 1`；
- routing observation: **`CONTINUE_B04`**。

按首次运行前就已冻结的 B-04 rubric(路由尺子)：`exact <= 5/8` 或同一 failure family 覆盖 `>=2` 个 Case 即进入 `CONTINUE_B04`。本次同时满足两个条件，因此结果没有歧义。

## 5. Case observations / Case 结果

| Goal | 结果 | 失败归因 | 摘要 |
|---:|---|---|---|
| 1 | FAIL | `REQUIRED_OPTION_MISMATCH` | 商品正确；最终 option `original almond`，required `pecan` |
| 3 | FAIL | `REQUIRED_OPTION_MISMATCH` | 商品正确；required `60x40x40cm` 未保留 |
| 4 | PASS | `NONE` | 商品/价格正确，无 required option |
| 5 | FAIL | `TARGET_PRODUCT_MISMATCH` | 选中 `B09FYBZNQL`，expected `B09R4RJSFP` |
| 6 | PASS | `NONE` | 商品 + `pink` 正确 |
| 8 | FAIL | `REQUIRED_OPTION_MISMATCH` | 商品正确；required `1pcs` 未保留 |
| 11 | FAIL | `REQUIRED_OPTION_MISMATCH` | `woody scent` 正确，但缺 `1.6 ounce (pack of 1)` |
| 12 | PASS | `NONE` | 商品 + `fresh` 正确 |

## 6. AC-to-EV mapping

| AC | Executor evidence | 结论 |
|---|---|---|
| AC-01 Candidate snapshot integrity | EV-01 | PASS：accepted H-12 candidate hashes / WebShop checkout audit 通过。 |
| AC-02 True holdout boundary | EV-01 | PASS：8 Case 精确等于开发 5 题的全集补集，无 ASIN 重叠。 |
| AC-03 Truth integrity | EV-01 + EV-02 + EV-03 + diagnosis | PASS：manifest truth 机械重建通过；runtime 固定展示前缀经 canonicalization 后 instruction hash `8/8`。 |
| AC-04 Measurement completeness | EV-02 + EV-03 | PASS：8 Case × repeat 2 完整输出并通过结果结构校验。 |
| AC-05 Determinism and safety accounting | EV-02 + EV-03 | PASS：`8/8` deterministic，Buy Now attempt=0，actual side effect=0。 |
| AC-06 No product tuning | amendment + comparison | PASS：未修改 product policy；Attempt 1/2 的业务动作和结果逐项一致。 |
| AC-07 Interpretation boundary | EV-02 + EV-03 | PASS：未制造 H11→H12 transfer delta；one_off project impact 仍为 `NOT_APPLICABLE`；正式 routing observation 为 `CONTINUE_B04`。 |

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/L2-GATE.json
- Validation plan: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- Checks: `3/3 PASS`；mandatory failures `0`。

## EV-01 — Snapshot / truth audit

- AC: AC-01, AC-02, AC-03, AC-06
- Meta: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-01.stderr.log
- Observed exit: `0 / PASS`。

## EV-02 — Blind holdout runtime measurement

- AC: AC-04, AC-05, AC-06, AC-07
- Meta: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-02.stderr.log
- Result artifact: `docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/HOLDOUT_RESULT.json`
- Observed exit: `0 / PASS`。
- Summary: exact `3/8`；deterministic `8/8`；instruction hash match `8/8`；actual side effect `0`；routing observation `CONTINUE_B04`。

## EV-03 — Holdout result validator

- AC: AC-04, AC-05, AC-07
- Meta: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/EV-03.stderr.log
- Observed exit: `0 / PASS`。
- Validator result: `measurement_integrity = COMPLETE`；routing observation `CONTINUE_B04`。

## Impact comparison

Measurement evidence: `EV-01` confirms frozen candidate / manifest truth boundary；`EV-02` is the repaired, one-time repeat=2 holdout execution；`EV-03` confirms complete measurement integrity；`ATTEMPT_COMPARISON.json` confirms the measurement repair did not alter business behavior/results。

Before: Attempt 1 的业务观测已经是 exact `3/8`、deterministic `8/8`、side effect `0`，但 instruction hash `0/8`，因此只能标 `INCONCLUSIVE`。

After: instruction hash `8/8`，measurement integrity `COMPLETE`；业务观测仍为 exact `3/8`、deterministic `8/8`、side effect `0`，正式 routing observation 为 `CONTINUE_B04`。

Delta: measurement integrity 从不可解释恢复为完整；**product capability delta = 0**。本修复没有提高策略准确率。

Guardrail result: PASS。policy / manifest / driver / truth / Case set 未变；Buy Now attempt `0`；actual side effect `0`；Attempt 1/2 业务行为逐项一致。

Scope caveat: 这是 WebShop small 的 8 个未见任务 absolute holdout measurement(绝对盲测)，不是 open-world shopping agent(开放世界购物智能体)质量结论，也不是生产支付能力结论。本任务是 `one_off`，project impact 仍为 `NOT_APPLICABLE`；`CONTINUE_B04` 只表示当前 B-04 泛化瓶颈尚未收敛到进入 H-13 的冻结门槛。

## Deviations and unresolved items

- Authorized deviation: 原 Contract 原本将 evaluator checker 设为 read-only；Human / Task Owner 在 Attempt 1 后明确授权 Executor 做有界 measurement repair，已通过 `EXECUTOR_AUTHORIZED_REPAIR_AMENDMENT.md` 留痕。
- Product deviation: 无。product policy / accepted runtime driver / manifest / truth / routing rubric 均未修改。
- Re-run policy: 只在测量 hash Bug 修复后重新执行同一冻结计划一次；没有重复跑到 accuracy 改善。
- Trace-hash note: Attempt 1/2 的 `normalized_trace_sha256` 会因 `instruction_hash_match` 这个测量字段从 false→true 而变化；独立对比脚本已逐项确认真正的 action steps / score / selected product/options/price/failure family 不变。
- Current project observation: `CONTINUE_B04`，因为 exact `3/8` 且 `REQUIRED_OPTION_MISMATCH` 覆盖 4 个 Case。
- Executor does not issue final task PASS；当前只提交两份报告与完整证据给 Evaluator 独立 L3 复核。

## Two-report submission / 两份报告提交

1. 第一次失败报告：`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT_ATTEMPT1_BLOCKED.md`
2. 修复后提交报告：`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT.md`

第一次失败证据：`evidence/attempt1_blocked/`。  
第二次修复后证据：顶层 `evidence/EV-*`、`evidence/L2-GATE.*`、`evidence/HOLDOUT_RESULT.json`。  
差异核对：`evidence/ATTEMPT_COMPARISON.json`。
