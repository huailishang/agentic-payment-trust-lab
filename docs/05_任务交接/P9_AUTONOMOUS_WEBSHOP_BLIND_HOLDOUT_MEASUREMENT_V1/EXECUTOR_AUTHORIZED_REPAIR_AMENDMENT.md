# Executor Authorized Repair Amendment

Task ID: `P9-AUTONOMOUS-WEBSHOP-BLIND-HOLDOUT-MEASUREMENT-V1`

## Authorization

2026-09-05，Human / Task Owner 明确授权 Executor(执行者) 对本次 Blind Holdout(盲测保留集) 中的 instruction hash mismatch(指令哈希不一致)进行有界修复，并要求保留第一次失败报告，再将修复后的第二份报告与第一份报告一起落盘提交。

该授权不包含 commit、push、history rewrite、external API/network、Buy Now、payment、order、fulfilment 或产品策略调参。

## Repair boundary

本 Amendment(修订)只放宽原 Contract 中对 measurement checker(测量校验器)只读的限制，允许：

- 诊断 runtime instruction(运行时指令) 与 manifest canonical instruction(清单规范指令) 的字节差异；
- 修复 `holdout_runtime_measurement.py` 的 instruction hash canonicalization(指令哈希规范化)；
- 在修复后重新执行同一份冻结 `VALIDATION_PLAN.yaml` 一次；
- 保留第一次 L2 FAIL 的全部 EV / L2 / HOLDOUT_RESULT 证据；
- 生成第二份 Executor 报告。

仍禁止：

- 修改 `HOLDOUT_MANIFEST.json`、holdout Case、expected ASIN、required options、expected price、routing rubric；
- 修改 `src/agentic_payment_experiment/webshop_agent_behavior.py`；
- 修改 accepted test / runtime driver / product validator；
- 根据第一次 `3/8` 结果调整商品搜索、排序、选项选择或 stop policy；
- 重跑直到 accuracy(准确率)提高；
- 执行 Buy Now / payment / order / fulfilment。

## Root-cause hypothesis

第一次运行显示：

- offline truth audit(离线真值审计)对 8/8 manifest instruction hash 全部 PASS；
- runtime measurement(运行时测量)对 8/8 instruction hash 全部 FAIL；
- 诊断证明 runtime 页面展示文本固定为 `"Instruction: " + canonical instruction`；
- `runtime.server.goals[index]["instruction_text"]` 的 SHA-256 与 manifest 8/8 一致。

因此本修复的 single principal change(单一主要变更)为：

> hash runtime instruction 前，仅移除 WebShop 页面固定展示前缀 `Instruction: `；若无该前缀则原样保留。

该规则不修改输入给 product policy(产品策略)的 instruction，不修改任何 scorer truth(评分真值)，只修正 measurement hash boundary(测量哈希边界)。

## Acceptance

修复后重新运行同一冻结 Validation Plan，应满足：

1. `VP-01` 继续 PASS，证明 candidate / manifest / truth 未漂移；
2. `VP-02` 的 `instruction_hash_match_count = 8/8`；
3. `VP-03` 通过 measurement integrity(测量完整性)校验；
4. exact match、failure family、determinism、Buy Now / side-effect 数值按真实结果原样保留，不要求提高；
5. policy SHA-256 仍为 `55f2f6cb2c59044b169152c217d6a6e63f092ccca2196fcf86f11772c1f2436e`；
6. manifest SHA-256 仍为 `6cf9f11146726a7ca68ecd5cdfa334af4b6e247cf95971c6e4972bfe0248be24`。

## Evidence preservation

第一次失败运行已封存到：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/evidence/attempt1_blocked/`

第一次报告已保留为：

`docs/05_任务交接/P9_AUTONOMOUS_WEBSHOP_BLIND_HOLDOUT_MEASUREMENT_V1/REPORT_ATTEMPT1_BLOCKED.md`

修复后的第二次运行继续使用顶层 `evidence/EV-*`、`evidence/L2-GATE.*`、`evidence/HOLDOUT_RESULT.json`，最终 `REPORT.md` 作为第二份 Executor 报告。
