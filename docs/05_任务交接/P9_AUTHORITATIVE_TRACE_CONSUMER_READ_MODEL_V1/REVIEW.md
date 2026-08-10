# Evaluator Review

Task ID: `P9-AUTHORITATIVE-TRACE-CONSUMER-READ-MODEL-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Review date: `2026-08-10`  
Frozen project map revision: `2026-08-07-r12`  
Active bottleneck / hypothesis at task freeze: `B-08 / H-07`  
Frozen baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Observed review HEAD: `c18a24066973b3fb33742a0c5c59a0bd8a35e1ae`

## Final verdict

```text
Task verdict: PASS
Project-impact verdict: IMPROVED
```

本任务满足冻结合同。独立复核确认：一个协议中立、只读的 Authoritative Trace Consumer 已经能够把 T01/T02/T07/T10 四类代表 `VALID ProductAuthoritativeTrace` 机械投影为 deterministic Read Model，且没有通过修改旧产品轨迹、runner、fixture 或业务逻辑换取结果。

项目级收益成立：

```text
Consumer-ready representative families
0/4 -> 4/4

Product Trace
9/12 -> 9/12

GESR
8/12 -> 8/12
```

因此 H-07 获得直接支持。B-08 的最早可观察失败从“没有统一 Consumer / Read Model”下移为“用户可见 UI 尚未真正消费这个 Read Model”。

## Submitted snapshot acceptance

Executor 提交状态为 `SUBMITTED_FOR_REVIEW`，提交时 `CURRENT.md` 保持 `EXECUTING / Executor`，符合 v2.1 的 submit/accept 分离要求。

Evaluator 在接受前重新运行 workflow validator，结果为 `OK`，随后把路由切换为 `READY_FOR_REVIEW / Evaluator`。接受后对实现、专项测试、项目级基线、全量回归、正式入口和源码边界进行了独立复跑。

授权边界未被突破：commit、push、history rewrite、API/network、dependency install、environment creation、WebShop runtime、Buy Now、payment/order side effect 均未执行。

## Acceptance criteria

| AC | Evaluator verdict | Independent evidence | 结论 |
|---|---|---|---|
| AC-01 One generic consumer path | 通过 | `RV-EV-01`、`RV-EV-05` | production Consumer 仅依赖公共 authoritative trace 合同；无 T01/T02/T07/T10、profile 或 family 分支。 |
| AC-02 Frozen validation boundary and fail closed | 通过 | `RV-EV-01` | 仅 `VALID` 返回 `AVAILABLE + read_model`；wrong type / INVALID / INDETERMINATE 均 `REJECTED` 且无正常 timeline。 |
| AC-03 Exact event preservation | 通过 | `RV-EV-01` | 四类代表轨迹的 event 数量、顺序、字段、reason codes 精确保持。 |
| AC-04 Source binding and relation auditability | 通过 | `RV-EV-01` | `source_binding_ref` 可解析；source binding projection、relations、binding assertions 与源 trace 一致。 |
| AC-05 Deterministic primitive serialization | 通过 | `RV-EV-01` | T01/T02/T07/T10 同一 trace 连续消费 3 次 canonical SHA 一致。 |
| AC-06 Representative family coverage `0/4 -> 4/4` | 通过 | `RV-EV-01` | 同一个 Consumer 对四个代表结构全部 `AVAILABLE`。 |
| AC-07 Negative matrix | 通过 | `RV-EV-01` | wrong type、缺 binding、重复 sequence、非法 relation target、缺 binding ref、坏 projection、重复 binding、PARTIAL、坏 envelope、重复失败消费均 fail closed。 |
| AC-08 No business re-execution | 通过 | `RV-EV-01`、`RV-EV-05` | 无 Policy、Lineage、Attack Overlay、payment、WebShop runtime、runner、evaluator 重执行；无动态 loader/eval/exec。 |
| AC-09 Existing product/measurement invariance | 通过 | `RV-EV-02`、`RV-EV-03`、`RV-EV-05`、`RV-EV-06` | 57 个 task-start src 全不变；只新增 Consumer；Product Trace=9/12、GESR=8/12、旧 trace hashes 和正式入口保持。 |
| AC-10 Tests and workflow | 通过 | `RV-EV-01`、`RV-EV-02`、`RV-EV-03`、`RV-EV-04`、`RV-EV-08` | Consumer 19/19、project-impact 21/21、full 557/557、repeat=3、workflow validator OK。 |

## Independent rerun summary

### RV-EV-01 — Consumer dedicated suite

```text
python3 -m unittest tests.test_authoritative_trace_consumer -v
Ran 19 tests
OK
```

覆盖四类正例、精确字段/关系/source binding 投影、deterministic SHA、静态 generic-path 审计和完整 fail-closed 负例矩阵。

### RV-EV-02 — Project-impact regression suite

```text
python3 -m unittest tests.test_project_impact_baseline -v
Ran 21 tests
OK
```

冻结项目级 measurement contract、T10 零重复副作用语义、product trace provenance 和 guardrail 均未退化。

### RV-EV-03 — Same-baseline repeat=3

```text
repeat_count = 3
all_identical = true
normalized_sha256 = fd0abca4e121187ce8ad3d172c2653d53ea06609870c20dfe70dc627ebecd647 ×3
Product Trace = 9/12
GESR = 8/12
callback_count_match = 12/12
duplicate_or_forbidden_side_effect = 0/12
```

### RV-EV-04 — Full regression

```text
Ran 557 tests
OK
```

满足合同 `>=550`，无新增失败。

### RV-EV-05 — Boundary / invariance audit

独立重跑结果：

```text
task_start_existing_src_count = 57
current_src_count = 58
added_src = [authoritative_trace_consumer.py]
preexisting_src_unchanged = true
forbidden_family_literals = false
forbidden_business_calls = false
RESULT = PASS
```

冻结核心 SHA 与七条既有 accepted trace SHA 均精确不变。

### RV-EV-06 — Formal entrypoint

```text
S01-S13: 13/13 PASS
```

内部正式场景入口未退化。

### RV-EV-07 / RV-EV-08 — Workflow validation ordering correction

Evaluator 在最终裁决前曾先写入下一版 bottleneck map 草案 `r13 / H-08`，随后对仍路由到冻结 `r12 / H-07` 的当前任务运行 validator。`RV-EV-07` 因 map/router revision 与 hypothesis 不一致被正确判为 `BLOCKING`。

这属于 Evaluator 自己的治理落盘顺序偏差，不涉及 Executor 实现、合同、业务结果或证据篡改。Evaluator 随即把 bottleneck map 恢复到冻结 `2026-08-07-r12 / H-07`，重新运行 validator：

```text
RV-EV-08
OK: v2.1 routing and required artifacts are structurally valid
```

因此该偏差已在最终 verdict 前按 `FIX_IN_PLACE` 思路纠正，并保留失败证据，不覆盖、不删除。

## Project-impact comparison

### Before

```text
Consumer-ready representative families = 0/4
Product Trace = 9/12
GESR = 8/12
```

### After

```text
Consumer-ready representative families = 4/4
Product Trace = 9/12
GESR = 8/12
```

### Guardrails

- task-start 57 个既有 `src/**/*.py` 全部 byte-for-byte 不变；
- 只新增 `src/agentic_payment_experiment/authoritative_trace_consumer.py`；
- T01/T02/T03/T04/T09/T10/T12 accepted trace hashes 全部不变；
- project-impact frozen fixture 与 runner hash 不变；
- repeat=3 完全一致；
- full regression 557/557；
- formal entrypoint 13/13；
- 无网络、真实 WebShop、Buy Now、支付、订单或履约副作用。

这符合冻结合同对 `IMPROVED` 的定义：新增的是下游统一消费能力，而不是提高 Product Trace/GESR 数字。

## Findings

没有发现需要 `REJECTED` 或 repair 的实现缺陷。

需要保留的边界：

1. 本轮只证明四种代表结构可被同一个 Consumer 消费，不等于最终 UI 已完成；
2. T05/T06/T11 仍没有 product trace，但它们已不是当前最早阻塞点；
3. 没有验证真实浏览器、真实 WebShop runtime、LLM、钱包或资金网络；
4. Read Model 是权威轨迹的只读投影，不是新的事实源，也不得用于重新推导业务决策。

## Continuation action

下一包进入同一 B-08 的下一层，不回头机械补 T05/T06/T11：

```text
Next task ID:
P9-AUTHORITATIVE-TRACE-READ-MODEL-PLAYER-V1

Next target:
Trace Read Model JSON
-> generic read-only Trace Player UI
-> event playback + source-binding evidence drill-down

Expected metric:
UI-ready representative families 0/4 -> 4/4
while Consumer-ready remains 4/4,
Product Trace remains 9/12,
GESR remains 8/12.
```

Evaluator 在本 REVIEW 落盘后更新 bottleneck map 到 `2026-08-10-r13`：记录 H-07 已支持，激活 H-08，并冻结下一任务合同。下一任务将路由为 `CONTRACT_FROZEN / Executor`。
