# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-ATTACK-OVERLAY-FAMILY-TOOLKIT-V1`  
Workflow: `evaluator-executor-workflow/v2.1`  
Task kind: `capability_experiment`  
Reviewed baseline HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`  
Task verdict: `PASS`  
Project impact verdict: `IMPROVED`

```yaml
review_state: PASS
project_impact_verdict: IMPROVED
commit_performed: false
push_performed: false
network_call_performed: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 裁决摘要

本 capability experiment 正式通过，并且对项目产生可测改善。

独立复核确认：

- T07/T08 不是两个专属 builder，而是一个 Attack Overlay Trace Toolkit + 两个固定 Profile；
- Profile 选择依赖 `blocked path + lineage/result` 不变量，不依赖 evaluator task ID、attack ID、title 或 source_ref 前缀；
- toolkit 不重跑 Policy、Lineage、validator、evaluator 或 attack evaluation；
- T07/T08 都形成精确 3-event / 1-binding 的产品权威轨迹；
- 两条轨迹均通过 frozen authoritative registry 验证；
- T07/T08 原有 decision、blocked path、lineage、callback/retry、trusted state 和副作用结果完全不变；
- 其他 10 项 `actual` 与上一轮 Evaluator accepted baseline 完全一致；
- 原有 T01/T02/T03/T04/T09/T10/T12 七条完整轨迹 Hash 全部不变；
- fixture、runner、authoritative registry、shared assembler byte-for-byte 不变；
- Product Trace `7/12 -> 9/12`；
- GESR `6/12 -> 8/12`；
- repeat=3 完全一致；
- 全量回归 `538/538`。

因此这不是“为了分数给 T07/T08 打补丁”，而是第二个多场景 family toolkit 对共享 Authoritative Trace 架构的有效验证。

## 2. 独立复核证据

### RV-EV-01 — Existing Attack Overlay regression

```text
Ran 10 tests
OK
```

证明原有攻击阻断行为没有因 trace 附着而退化。

证据：`evidence/RV-EV-01.*`。

### RV-EV-02 — Attack Overlay Trace Family

```text
Ran 15 tests
OK
```

包含：

- amount -> T07 Profile；
- payee -> T08 Profile；
- 改写 attack ID/title/source_ref 后仍正确选择；
- unsupported path；
- amount+payee 多匹配；
- blocked/lineage path 不一致；
- invalid lineage；
- trusted state changed；
- applied path 非空；
- decision drift；
- attack not attempted；
- existing trace 不覆盖；
- invalid profile container；
- duplicate matching profile；
- 单 assembly path / 无业务规则重执行。

证据：`evidence/RV-EV-02.*`。

### RV-EV-03 — Project-impact regression

```text
Ran 21 tests
OK
```

证据：`evidence/RV-EV-03.*`。

### RV-EV-04 — Full regression

```text
Ran 538 tests
OK
```

达到并超过合同 `>=533`。

证据：`evidence/RV-EV-04.*`。

### RV-EV-05 — Same-baseline repeat=3

```text
repeat_count = 3
all_identical = true
normalized_sha256 = fd0abca4e121187ce8ad3d172c2653d53ea06609870c20dfe70dc627ebecd647 × 3

Product Trace = 9/12 = 0.750000
GESR          = 8/12 = 0.666667

matched = T01,T02,T03,T04,T07,T08,T09,T12
```

T07/T08：

```text
matched = true
capability_gaps = []
product trace = VALID
source = attack_overlay_result
events = POLICY_DECISION_RECORDED, LINEAGE_DECISION_RECORDED, RESULT_RECORDED
```

证据：

- `evidence/RV-EV-05.meta.json`
- `evidence/RV-EV-05-baseline.json`
- `evidence/RV-EV-05.stdout.log`
- `evidence/RV-EV-05.stderr.log`

### RV-EV-06 — Independent invariance / architecture audit

独立输出：

```text
frozen_measurement_boundaries=PASS
src_delta_exact=attack_overlay.py+2_family_files
src_python_file_count=57
other_10_actual_outputs_unchanged=True
T07_T08_only_trace_fields_plus_authoritative_stage_changed=True
non_trace_projection_sha256=6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc
product_trace=9/12:0.750000
gesr=8/12:0.666667
valid_product_tasks=T01,T02,T03,T04,T07,T08,T09,T10,T12
absent_product_tasks=T05,T06,T11
T07_T08_registry_valid_and_id_independent=True
family_single_path_static_guardrail=PASS
RESULT=PASS
```

冻结旧轨迹 Hash：

```text
T01 7c47cb15b6dcc687f35ac158eae556979ad05520ec7f36f8511a4bcf13e66906
T02 fb1a79d73931f3e0bb87eafeffdaffe4004add137998d107ea425554605be624
T03 7f0e1ccb14cc9256c5c336fb460647ce040bf0549a3328764c061c7b766c92a7
T04 405e6b8971f9f5e3ad67069ace074df15af4fee6f80418a70466315dcd642c33
T09 a596f5f35697a878286b85b8e37792aeee34ab7c0800b27739bc91382032310e
T10 2b97fd1f81001086d4793bf21fd0dbe3ed950643e6d9e5031e18510fb7c99fb3
T12 ebb38113abb2582d52f434b1a1b30247cc68ee8f4b57c0c18f52efa37bb1c230
```

Evaluator 另外使用完全改名的 T07/T08 attack ID/title/source_ref 重新生成 trace，仍为 registry `VALID`，证明产品选择没有偷用 evaluator 场景标识。

证据：

- `evidence/RV-EV-06-independent-invariance-audit.py`
- `evidence/RV-EV-06.meta.json`
- `evidence/RV-EV-06.stdout.log`
- `evidence/RV-EV-06.stderr.log`

### RV-EV-07 — Workflow validator

```text
OK: v2.1 routing and required artifacts are structurally valid
```

证据：`evidence/RV-EV-07.*`。

## 3. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 One shared family implementation | 通过 | RV-EV-02 / RV-EV-06：2 Profiles、1 Toolkit、1 assembly path、无 T07/T08 builder |
| AC-02 Positive profile selection | 通过 | RV-EV-02 / RV-EV-06：amount/payee 正确选择，改名后仍成立 |
| AC-03 Fail-closed negative matrix | 通过 | RV-EV-02：合同全部负例通过 |
| AC-04 Exact product traces | 通过 | RV-EV-02 / RV-EV-05 / RV-EV-06：3 events、1 binding、registry VALID |
| AC-05 T07/T08 business invariance | 通过 | RV-EV-06：只新增 trace 字段和 authoritative evidence stage |
| AC-06 Other ten tasks unchanged | 通过 | RV-EV-06：其他 10 actual exact equality；T05/T06/T11 仍 absent |
| AC-07 Existing trace invariance | 通过 | RV-EV-06：七条旧 trace hash 全命中 |
| AC-08 Same-baseline project impact | 通过 | RV-EV-05 / RV-EV-06：Product Trace +2/12；GESR +2/12；repeat=3 |
| AC-09 Frozen measurement boundaries | 通过 | RV-EV-06：fixture/runner/registry/assembler hash 全命中 |
| AC-10 Tests and workflow | 通过 | 10/10、15/15、21/21、538/538；validator OK |

## 4. Project impact

```text
Project impact verdict: IMPROVED
```

同一 measurement baseline：

```text
Before
Product Trace = 7/12
GESR          = 6/12

After
Product Trace = 9/12
GESR          = 8/12

Delta
Product Trace = +2/12
GESR          = +2/12
```

守护线：

```text
other 10 actual outputs unchanged
all-12 non-trace projection unchanged
old 7 product trace hashes unchanged
T05/T06/T11 remain NOT_AVAILABLE
callback/retry/forbidden side effects unchanged
```

## 5. 对 B-03 的重新判断

本轮后仍有：

```text
T05,T06,T11
```

三个任务没有产品轨迹，因此 B-03 不能标记为完全解决。

但此时继续把 `9/12 -> 12/12` 作为第一优先级已经不合理，因为当前 9 条轨迹已经跨越四种明显不同结构：

```text
Sidecar family       -> T01/T09/T12
Prepayment family    -> T02/T03/T04
Attack Overlay       -> T07/T08
Duplicate/Preflight  -> T10
```

这已经足够验证下游“消费者”是否真的能统一消费产品轨迹。

项目目标不是轨迹覆盖率本身，而是：

```text
真实执行
-> 产品权威轨迹
-> 回放 / 解释 / 独立复核
-> UI 证据播放器
```

当前产品已经会产出轨迹，但 `html_report.py` / `interactive_lab.py` / `interactive_server.py` 尚未消费 `ProductAuthoritativeTrace`。因此新的更早瓶颈已经从“有没有轨迹”转成“轨迹有没有被真正消费”。

## 6. Continuation

更新 `PROJECT_BOTTLENECK_MAP.md` 到 revision `2026-08-07-r12`：

```text
B-03 Authoritative Trace
ACTIVE -> WATCH / REPRESENTATIVE_COVERAGE_SUFFICIENT
remaining = T05,T06,T11 = 3/12

B-08 Trace Consumer / UI Read Model
-> ACTIVE
```

下一能力实验：

```text
P9-AUTHORITATIVE-TRACE-CONSUMER-READ-MODEL-V1
```

目标不是马上做漂亮 UI，而是先建立一个只读、协议中立的 Trace Consumer：

```text
ProductAuthoritativeTrace
-> deterministic Trace Read Model / Timeline JSON
-> 后续 Replay / UI 共用
```

第一轮只拿四种结构的代表任务验证：

```text
T01 Sidecar
T02 Prepayment
T07 Attack Overlay
T10 Duplicate/Preflight
```

要求 Consumer：

- 只消费 frozen VALID trace；
- 保留 event sequence、entity role/ref、decision/status/reason codes、source binding、relations；
- 不调用 validator、Policy、Lineage、支付、runner 或 evaluator 重算事实；
- 同一 trace 多次消费输出一致；
- invalid / incomplete trace fail closed；
- 不修改任何现有产品 trace 或业务结果。

通过后再进入 `P9-E` 的 WebShop 购买轨迹可视化 UI，把 Read Model 当成证据播放器输入。

不继续机械发 T05/T06/T11 轨迹补齐包；它们保留在 B-03 WATCH，等 Consumer / UI 证明价值后再决定是否值得补到 12/12。
