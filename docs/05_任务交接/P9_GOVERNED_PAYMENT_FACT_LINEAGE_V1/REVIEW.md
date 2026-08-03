# Evaluator Review

Task ID: P9-GOVERNED-PAYMENT-FACT-LINEAGE-V1  
Workflow: evaluator-executor-workflow/v2  
Reviewed baseline HEAD: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6  
Evaluator verdict: PASS

## 1. 裁决摘要

独立复核确认本轮事实血缘能力满足冻结合同：

- 只有精确 tuple 容器和精确 FactLineageNode 对象能进入字段读取。
- SimpleNamespace、dict、list、string、子类和 ExplodingProxy 均稳定返回 INVALID，无属性访问异常。
- missing upstream、duplicate、self-reference 和 cycle 均失败关闭，不返回部分 resolved_facts。
- WEB_UNTRUSTED 经 LLM_GENERATED 或 USER_CONFIRMED 派生后仍保留在 effective_source_types 中。
- trust_upgrade_evidence_ref 只记录证据，不清除不可信祖先。
- AGENT_DECLARED 被保留并明确分类为非权威祖先。
- resolver 不执行 I/O、网络、进程、环境操作或支付业务决策。
- Attack Overlay 只增加 lineage 证据，原 Context Policy 决策和策略投影完全不变。

独立结果：

```text
独立反例与静态审计       PASS
Fact Lineage 矩阵        16/16 matched
Fact Lineage 专项        12/12 PASS
Attack Overlay           10/10 PASS
Context Policy           10/10 PASS
Governed Action / Gate   44/44 PASS
全量 unittest            413/413 PASS
正式入口                 13/13 PASS
Overlay 策略投影         完全一致
workflow validator       OK
```

## 2. 关键独立反例

### 类型边界

六类非正式节点对象全部得到：

```text
status = INVALID
reason_codes = fact_lineage_node_invalid_type
resolved_facts = []
```

ExplodingProxy 没有触发属性读取，证明类型检查发生在字段访问前。

### 图完整性

“正常 root + 两节点循环”的混合图得到：

```text
status = INVALID
reason = fact_lineage_cycle_detected
resolved_facts = []
unresolved = [cycle-a, cycle-b]
```

缺失上游的混合图同样返回 MISSING_EVIDENCE、空 resolved_facts 和明确 unresolved ref。

### 不允许静默升级

WEB_UNTRUSTED 上游派生为 USER_CONFIRMED，并附带升级证据后，结果仍为：

```text
effective_source_types = [USER_CONFIRMED, WEB_UNTRUSTED]
contains_untrusted_ancestry = true
```

证据：evidence/RV-EV-01.*

## 3. Overlay 独立对比

重新运行冻结投影比较：

```text
overlay_policy_projection_equal = PASS
lineage_is_additive_evidence_only = PASS
no_decision_drift = PASS
```

原六项结果仍为 6/6 PASS，blocked_attack_cases=4，decision_drifts=0。唯一状态变化仍是合法支付提供方状态观察。

证据：evidence/RV-EV-09.*

## 4. 独立证据

| 证据 | 内容 | 结果 |
|---|---|---|
| RV-EV-01 | 类型、图失败、传播、升级、分类、冻结、无业务裁决 | PASS |
| RV-EV-02 | 血缘矩阵 | 16/16 matched |
| RV-EV-03 | Fact Lineage 专项 | 12/12 PASS |
| RV-EV-04 | Attack Overlay | 10/10 PASS |
| RV-EV-05 | Context Policy | 10/10 PASS |
| RV-EV-06 | Governed Action / Runtime Gate | 44/44 PASS |
| RV-EV-07 | 全量 unittest | 413/413 PASS |
| RV-EV-08 | 正式入口 | 13/13 PASS |
| RV-EV-09 | Overlay 策略投影 | 完全一致 |
| RV-EV-10 | 范围、哈希和静态审计 | PASS |
| RV-EV-11 | v2 workflow validator | OK |

fact_lineage.py 当前 SHA-256：7608b0f9997eb357a7ca733343eb359183f29bcc52eae6d941c3c83efb9737b5。

保护文件 context_policy.py、governed_action.py、webshop_runtime_gate.py、hashing.py、models.py、validator.py 和 payment_execution.py 哈希均与执行报告一致。HEAD 未变化。

## 5. AC 裁决

| AC | 裁决 | 依据 |
|---|---|---|
| AC-01 | 通过 | frozen、精确类型、primitive serialization |
| AC-02 | 通过 | 必填字段与类型具有稳定分类 |
| AC-03 | 通过 | 图失败无部分解析 |
| AC-04 | 通过 | 所有直接和上游来源均保留 |
| AC-05 | 通过 | 升级证据不清除 WEB_UNTRUSTED |
| AC-06 | 通过 | 所有 SourceType 显式分类 |
| AC-07 | 通过 | Overlay 共享 resolver，策略投影不变 |
| AC-08 | 通过 | 16/16 矩阵通过 |
| AC-09 | 通过 | 无 I/O、业务裁决和禁止副作用 |
| AC-10 | 通过 | 全部强制回归和证据通过 |

## 6. 最终结论

PASS

Fact Lineage V1 已完成组件级闭环：系统不仅知道事实直接来自哪里，还能保留最终依赖过的全部上游来源。它仍是来源事实引擎，不是支付授权引擎。

## 7. v2.1 兼容与后续

本任务在 v2.1 启用前已按 v2 冻结，因此不追溯补写 task_kind 或项目影响裁决。

现有证据只能证明组件正确；由于尚无统一端到端 before/after，不能声称完整购物任务能力已经提高。项目地图应记录：B-02 组件实现已通过，但项目影响尚未测量。

下一包：

```text
Task ID: P9-PROJECT-IMPACT-BASELINE-V1
Task kind: evaluator_design
Active bottleneck: B-01
Hypothesis: H-01
Initial state: CONTRACT_FROZEN / Executor
```

下一包只建立固定端到端任务集、统一运行命令和项目指标，不修改 P1-P6、Fact Lineage、Runtime Gate 或支付业务决策。
