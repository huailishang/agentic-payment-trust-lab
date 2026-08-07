# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROVENANCE-DIAGNOSTIC-REPAIR-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `repair`  
Review date: `2026-08-06`  
Baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

```yaml
task_verdict: PASS
project_impact_verdict: NOT_APPLICABLE
accepted_state: READY_FOR_REVIEW
review_owner: Evaluator
project_map_revision: 2026-08-06-r6
commit_performed: false
push_performed: false
network_call_performed: false
payment_or_order_side_effect_performed: false
```

## 1. 复核结论

本 repair 通过。

大白话：

```text
以前：
产品轨迹和评估器 Replay 同时存在
→ 即使两者来源不同
→ runner 仍错误报警“来源没有分开”

现在：
产品来源 = webshop_gate_outcome
Replay 来源 = runner_constructed_from_fixed_facts
→ 两者明确不同
→ 正确判定为已分离
```

修复只清除了错误诊断：

```text
T10 trace_provenance_separated: false → true
T10 measurement_diagnostics_matched: false → true
T10 measurement_integrity_gaps:
[trace_provenance_not_separated] → []
```

产品能力没有变化：

```text
Product Trace = 1/12
T10 target GESR = 1/12
T10 product trace = VALID
T10 matched = true
T10 capability_gaps = []
```

因此任务裁决为 `PASS`，项目影响为 `NOT_APPLICABLE`。

## 2. 独立复核证据

### RV-EV-01 — 专项测试

```text
python3 -m unittest tests.test_project_impact_baseline -v

Ran 20 tests
OK
```

证据：

- `evidence/RV-EV-01.meta.json`
- `evidence/RV-EV-01.stdout.log`
- `evidence/RV-EV-01.stderr.log`

### RV-EV-02 — 全量回归

```text
python3 -m unittest discover -s tests -p 'test_*.py'

Ran 489 tests
OK
```

证据：

- `evidence/RV-EV-02.meta.json`
- `evidence/RV-EV-02.stdout.log`
- `evidence/RV-EV-02.stderr.log`

### RV-EV-03 / RV-EV-04 — repeat=3

| 项目 | 独立结果 |
|---|---|
| Runner SHA-256 | `70bf2142c303c01c6fb3270fb364c46bc220b821c5e554fa2e6af3355dc57dd3` |
| Baseline output SHA-256 | `992653a63194c391ae30f7c48bf02c34ed50cfe0b87c12914851f8572f95e26a` |
| Baseline normalized SHA-256 | `f1aa119f14e88b7a15bdcc40760391692d6ba5c9a5d795f093d0bda0d8dfb5bc` |
| T10 target output SHA-256 | `4d447be2ed752455dab1c29e0da838c515fecebf379c573b6991ae216522f95b` |
| T10 target normalized SHA-256 | `5593a59562b42378dd95f78c4a95bc906884b515cad6acac6f20e4c81b4c8421` |
| Non-trace projection SHA-256 | `6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc` |

三次 normalized hash 各自完全一致。

证据：

- `evidence/RV-EV-03-after-baseline.json`
- `evidence/RV-EV-03.meta.json`
- `evidence/RV-EV-04-after-target.json`
- `evidence/RV-EV-04.meta.json`

### RV-EV-05 / RV-EV-06 — 字段级审计

第一次独立审计因评估者脚本把列表变化路径写成字段路径而失败；失败证据保留。修正审计脚本后通过。

修复前后精确变化只有：

```text
runner_sha256
repeatability.normalized_sha256[0..2]
T10 measurement_diagnostics.trace_provenance_separated
T10 measurement_diagnostics_matched
T10 measurement_integrity_gaps
```

最终结果：

```text
product_trace=1/12
target_gesr=1/12
t10_measurement_integrity_gaps=[]
non_trace_projection_sha256=6eb5...9099dc
RESULT=PASS
```

证据：

- `evidence/RV-EV-05.meta.json`（评估脚本首次失败）
- `evidence/RV-EV-05.stderr.log`
- `evidence/RV-EV-05-review-audit.py`
- `evidence/RV-EV-06.meta.json`
- `evidence/RV-EV-06.stdout.log`

### RV-EV-07 — 下一切片可执行性检查

评估者比较了剩余 11 项 fixture 事件目标与冻结 profile：

```text
可直接使用同一 fixture 做 capability experiment：
T01、T09、T11、T12

暂不能直接做：
T02—T06：fixture 仍使用旧 DECISION_RECORDED
T07—T08：fixture 仍要求旧 INPUT_SOURCE_RECORDED
```

证据：

- `evidence/RV-EV-07-next-slice-analysis.py`
- `evidence/RV-EV-07.meta.json`
- `evidence/RV-EV-07.stdout.log`

### RV-EV-08 / RV-EV-09 — 下一包路由校验

T01 合同首次校验因标题未使用机器要求的 `Allowed scope` 和缺少 `Validation plan` 被阻断。评估者只修正合同结构标题并补充验证计划表，没有改变目标、AC、范围或授权。最终结果：

```text
OK: v2.1 routing and required artifacts are structurally valid
```

证据：

- `evidence/RV-EV-08.meta.json`
- `evidence/RV-EV-08.stdout.log`
- `evidence/RV-EV-09.meta.json`
- `evidence/RV-EV-09.stdout.log`

## 3. AC 逐项裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 Closed provenance rule | 通过 | 纯函数只读取冻结的五类 measurement 字段；`RV-EV-01`、源码审计 |
| AC-02 Replay-only | 通过 | 无产品轨迹任务仍 separated=true、无 integrity gap；`RV-EV-01`、`RV-EV-03` |
| AC-03 Product + replay | 通过 | T10 两个不同来源正确分离，gap 清零；`RV-EV-04`、`RV-EV-06` |
| AC-04 Product-only | 通过 | 固定正例返回 true；`RV-EV-01` |
| AC-05 Negative matrix | 通过 | 缺失、矛盾、空白、未知、同源均失败关闭；`RV-EV-01` |
| AC-06 Capability invariance | 通过 | Product Trace 和 target GESR 均保持 1/12；`RV-EV-04`、`RV-EV-06` |
| AC-07 Business/product boundary | 通过 | non-trace hash 不变，产品文件与 fixture 哈希不变；`RV-EV-06` |
| AC-08 Freeze audit | 通过 | module、gate、builder、fixtures 和 registry 均保持接受值；`RV-EV-06` |
| AC-09 Tests/repeatability | 通过 | 专项 20、全量 489、baseline/target repeat=3；`RV-EV-01`—`RV-EV-04` |
| AC-10 Evidence/workflow | 通过 | 报告、原始 JSON、truth table、差异和三件套齐全 |

## 4. 两个裁决

### Task verdict

```text
PASS
```

执行者报告与独立复跑一致，未发现范围外产品改动或指标漂移。

### Project-impact verdict

```text
NOT_APPLICABLE
```

本任务只修测量误报，没有新增产品轨迹覆盖、GESR 或业务能力。

## 5. 延续动作

下一任务冻结为：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-T01-HAPPY-PATH-SLICE-V1
```

选择 T01 的原因：

1. T01 fixture 与冻结 profile 已对齐，不需要改尺子；
2. 它是正常授权、正常付款、正常履约的核心成功链；
3. T10 已证明拒绝链可以产出轨迹，T01 用于证明允许链也能形成完整产品证据；
4. 当前产品还缺少三项构轨迹必需的显式事实留存：授权订单快照、Governed Action 本体和执行前付款候选。下一包只做最小留存并产出 T01 轨迹，runner 不得补事实。

下一任务路径：

```text
docs/05_任务交接/
P9_PRODUCT_AUTHORITATIVE_TRACE_T01_HAPPY_PATH_SLICE_V1/
CONTRACT.md
```

路由：`CONTRACT_FROZEN / Executor`。

未执行 commit、push、网络、真实 WebShop、真实支付、钱包或订单副作用。
