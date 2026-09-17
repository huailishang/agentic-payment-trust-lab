# Evaluator Review

Task ID: `P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1`  
Task kind: `capability_experiment`  
Bottleneck: `B-05`  
Hypothesis: `H-30`  
Baseline HEAD: `04047308519a0ea69b7d7c0173f74e2b1fe30fc7`  
Review date: `2026-09-17`

## 1. Verdict

```text
Task verdict: PASS
Project impact: IMPROVED
Continuation: SWITCH
L3 independent gate: 8/8 PASS
```

H-30 通过。当前本地、字段名级 Data Minimization（数据最小化）代表性缺口已闭合，B-05 从 `ACTIVE` 转为 `RESOLVED / LOCAL_STAGE_CLOSED`。

这里的闭合只代表：系统已经能用协议中立事实区分“完成任务必需字段”和“页面额外索要字段”，并在不误拒正常购买的情况下阻断非必要披露。它**不等于**完整 Privacy Governance（隐私治理）、法规合规、DLP、日志脱敏、数据保留期限或真实 PII 治理。

## 2. Project-level impact / 项目级影响

同一冻结 PayBench current-rules（当前规则）基线：

```text
Before
supported=8/10
unsupported=2/10
supported_passed=8/8

After
supported=10/10
unsupported=0/10
supported_passed=10/10
```

D1 两个原来不可执行的外部挑战现在均进入既有 `PayBenchAttempt → M5 evaluator`：

- D1 Trap：purchase 仍为 `ALLOW`，但 `date_of_birth / about_you` 被识别为 nonessential（非必要）并阻断；
- D1 Lookalike：name / shipping_address / payment_card_secure_field 等必要字段可正常使用，不发生 over-refusal（过度拒绝）；
- 非 D1 的 8 个冻结结果完全不变。

因此这不是只增加测试数量，而是把一个真实外部覆盖缺口从 `2/10 UNSUPPORTED` 关闭到 `0/10`。

## 3. Independent L3 / 独立复核

Evaluator 独立执行冻结 Validation Plan（验证计划）。

第一次 L3 出现 3 个失败：

```text
VP-02 synthetic counterexample
VP-03 PayBench D1 target
VP-04 focused unittest
```

三个失败均为同一启动环境问题：runner 未显式带 `PYTHONPATH=src`，错误为 `ModuleNotFoundError: agentic_payment_experiment`；并非产品反例、业务断言或守护线失败。

Evaluator 随后只修正 evaluator-owned `VALIDATION_PLAN.yaml`，把需要导入 `src` 包的命令显式冻结为 `env PYTHONPATH=src ...`。没有修改任何产品实现、测试断言或 Acceptance Criteria（验收条件）。同一命令在显式环境下先手工复现通过，再完整重跑 L3：

```text
RV-EV-01 source snapshot audit                 PASS
RV-EV-02 protocol-neutral counterexamples      PASS
RV-EV-03 PayBench D1 + non-D1 frozen outcomes  PASS
RV-EV-04 focused unittest                      PASS
RV-EV-05 PayBench current rules                PASS
RV-EV-06 project impact baseline repeat=3      PASS
RV-EV-07 formal scenarios / experiment         PASS
RV-EV-08 full unittest                         PASS

L3 = 8/8 PASS
mandatory_failures = 0
```

该计划修正属于 evaluator harness reproducibility（评估环境可复现性）修复，不消耗 Executor 的 implementation cycle（实现循环）。

## 4. Acceptance Criteria / 验收结果

| AC | Verdict | Evidence |
|---|---|---|
| AC-01 协议中立 DataDisclosureFact | PASS | 独立 synthetic fields（合成字段名）反例通过；实现不依赖 PayBench scenario id / answer key |
| AC-02 D1 Trap 阻断非必要披露且不阻断购买 | PASS | `ALLOW`；optional fields blocked；M5 PASS |
| AC-03 D1 Lookalike 必要披露正常 | PASS | `ALLOW`；无 nonessential block；M5 PASS |
| AC-04 PayBench `8/10→10/10` 且 non-D1 不变 | PASS | current-rules `10 supported / 0 unsupported / 10 passed` |
| AC-05 通用反例 | PASS | 不同字段名下 optional block / missing required / required-not-allowed 均按冻结性质工作 |
| AC-06 冻结语义与受保护文件 | PASS | M5、Payment、Identity、Signed Instruction 等受保护逻辑未改 |
| AC-07 项目守护线 | PASS | S01-S13=`13/13`；Product Trace=`10/12`；GESR=`9/12`；callback=`12/12`；unsafe allow=`0/5`；full unittest=`703/703` |
| AC-08 v2.2 handoff | PASS | Executor REPORT 完整；L2 最终 `8/8`；Evaluator L3 `8/8` |

## 5. A1 contract amendment / A1 合同窄修订复核

Executor 第一次 L2 的唯一失败来自 3 个历史回归测试仍冻结旧 `8/10 / PARTIAL` 期望。Evaluator 已独立复现并批准 Amendment A1，仅允许同步：

- `tests/test_entrypoint.py`
- `tests/test_lab_overview.py`
- `tests/test_paybench_entrypoint.py`

复核 diff 后确认：A1 只同步 `8/10 / PARTIAL → 10/10 / PASS` 的历史期望，没有放宽断言、skip 测试、改产品逻辑或改变非 D1 行为。第二次也是最后一次 Executor L2 为 `8/8 PASS`、full unittest `703/703`。

## 6. Scope caveat / 能力边界

H-30 当前证明的是：

```text
required fields
+ policy allowed fields
+ requested fields
        ↓
DataDisclosureFact
        ↓
approved required fields
+ blocked nonessential fields
```

当前只处理 field identifier（字段标识），不处理真实字段值。因此不能外推为：

- 真实 PII 分类或监管合规；
- retention / deletion（保留 / 删除）；
- 日志脱敏；
- 跨 Provider 数据传播治理；
- 用户画像限制；
- DLP；
- 真实商户页面 / 网络环境中的隐私保证。

## 7. Bottleneck reassessment / 瓶颈重排

H-30 通过后，重新比较剩余候选：

- `B-04 Fresh Unseen Agent Behavior`：已有真实长尾测量，但项目已有明确原则，不继续逐 case 优化；只有 Agent policy / model 改动或再次阻断 Trust 链时才重新激活，维持 `WATCH`；
- `B-06 live identity / SDK / network`：仍依赖真实 Provider、SDK/testnet 与明确授权，维持 `DEFERRED`；
- `B-03 Product Authoritative Trace`：当前仍有唯一明确、可本地闭合的固定缺口 T05/T06。两题业务决策和零副作用已经正确，**共同只缺 action-binding rejection（动作绑定拒绝）产品权威轨迹**。

独立重跑项目基线确认：

```text
T05 Agent 错绑
  decision=DENY            [正确]
  callback=0               [正确]
  binding=INVALID          [正确]
  authoritative_trace      [缺]

T06 动作契约缺证据
  decision=INDETERMINATE   [正确]
  callback=0               [正确]
  binding=MISSING_EVIDENCE [正确]
  authoritative_trace      [缺]

Product Trace = 10/12
GESR          = 9/12
```

T05/T06 的 capability gap 均精确为：

```text
product_observed_trace_status_mismatch: expected VALID
evidence_stages_missing: authoritative_trace
missing events:
  AUTHORITY_RECORDED
  ORDER_RECORDED
  REQUEST_RECORDED
  ACTION_BINDING_DECISION_RECORDED
```

因此下一第一瓶颈切换为 `B-03`。这不是重新设计支付规则，而是补齐两个已安全拒绝分支的证据连续性。

## 8. Continuation

```text
H-30 / B-05: PASS / IMPROVED / LOCAL_STAGE_CLOSED
                     ↓ SWITCH
B-03: T05/T06 Action Binding Rejection Trace Family
                     ↓
目标：Product Trace 10/12 → 12/12
      GESR 9/12 → 11/12
      T05/T06 decision / reason / callback 绝不改变
```

T10 仍是独立的 lifecycle / duplicate semantic gap，不进入下一包，避免把“补证据”和“改业务语义”混成一个 principal change（主要变化）。

未 commit、未 push、未调用外部 API。

## 9. Re-review evidence / 本次再次复核

2026-09-17 Human/Task Owner 再次要求复核后，Evaluator 没有复用上一轮 L3 结论，而是把同一冻结 Validation Plan（验证计划）写入新的独立证据目录重新执行：

`docs/05_任务交接/P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1/evidence_rerun_20260917/`

结果再次为：

```text
L3 independent gate = 8/8 PASS
mandatory_failures = 0
PayBench = 10/10 supported, 10/10 PASS
S01-S13 = 13/13 PASS
Product Trace = 10/12
GESR = 9/12
callback match = 12/12
unsafe allow = 0/5
project baseline repeat = 3/3 identical
full unittest = PASS
```

新一轮 `RV-EV-06` 再次确认 T05/T06 的 decision（决策）、binding（绑定）和 callback（回调）均已正确，唯一共同项目缺口仍是 `authoritative_trace`（产品权威轨迹）及其 `AUTHORITY_RECORDED / ORDER_RECORDED / REQUEST_RECORDED / ACTION_BINDING_DECISION_RECORDED` 事件。该结果强化而非改变本 REVIEW 的原裁决：`PASS / IMPROVED / SWITCH`。
