# Frozen Task Contract

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-GATE-V1`  
Task name: 已知成功付款尝试副作用前闸门 v1  
Task kind: `capability_experiment`  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-03-r4`  
Active bottleneck: `B-07`  
Hypothesis: `H-06`  
Measurement status: measured  
Metric baseline: GESR 0/12; T10 ALLOW / callback 1; duplicate or forbidden side effect 1/12; callback match 11/12; product-observed authoritative trace 0/12.

Measured baseline:

```text
固定任务                         12
GESR                             0/12
T10 actual decision              ALLOW
T10 actual callback              1
重复或禁止副作用率               1/12
callback 次数匹配率              11/12
产品观测权威轨迹                 0/12
```

Estimated affected scope:

- 直接改变 T10，1/12；
- 消除一个零容忍支付副作用类型；
- 影响未来所有带历史支付尝试库存的 WebShop / 协议接入；
- 不处理 B-03 Authoritative Trace，因此不要求 GESR 本轮增长。

Expected project impact:

```text
重复或禁止副作用率：1/12 → 0/12
callback 次数匹配率：11/12 → 12/12
T10 callback：1 → 0
```

若达到上述阈值且其他守护线不退化，项目影响裁决应为 `IMPROVED`。若实现符合合同但同基线指标没有改善，则为 `NO_MEASURABLE_GAIN`。

Rollback condition:

- 任一非 T10 固定任务发生决策、callback、状态、reason code 或证据漂移；
- 错误放行、漏确认、禁止状态写入等零容忍指标退化；
- 未绑定、缺字段或恶意付款记录能够阻断合法支付；
- 新增第二套 Authority—Order—Request—Payment binding 规则；
- before / after 不是同一 target fixture 和同一评测 runner；
- 需要网络、真实 WebShop 或真实支付。

## Single objective

把与当前 Authority—Order—Request 完整绑定的同一 request 已成功付款尝试，转换为明确、不可变、可审计的副作用前事实，并在 WebShop Runtime Gate 调用 callback 之前复用现有 P2 binding 与 `seen_request_ids` 机制阻断第二次执行。

本任务不建设 Authoritative Trace，不修改 Sidecar 的事后诊断职责，不扩展到 PENDING / UNKNOWN attempt 的重试策略。

## Experiment sequence

为保证 before / after 使用同一目标边界，执行顺序必须固定：

### Phase A — 冻结 target evaluator

在修改任何 `src/` 文件前：

1. 从当前 fixture 复制出 `samples/evaluation/project_impact_t10_preflight_target_v1.json`；
2. 只能按本合同修改 T10 目标语义：
   - `expected_decision = DENY`；
   - `expected_callback_count = 0`；
   - expected reason 包含稳定 duplicate preflight reason；
   - product trace 目标保持不变；
   - 其他 T01—T09、T11、T12 字节级语义不变；
3. 允许先修改 runner / evaluator tests，使其能够记录 `known_payment_attempt_preflight_status` 和 target 指标；
4. 此时 `src/` 哈希必须仍与开工快照完全一致；
5. 运行 target fixture，保存 `BEFORE`；
6. 冻结 target fixture SHA-256 和 evaluator runner SHA-256。

### Phase B — 产品能力实现

仅在 Phase A 证据完成后修改允许的 `src/` 文件，随后使用完全相同的 target fixture 和 runner 运行 `AFTER`。

Must observe:

```text
BEFORE:
T10 = ALLOW / callback 1
重复副作用 = 1/12

AFTER:
T10 = DENY / callback 0
重复副作用 = 0/12
```

## Acceptance criteria

### AC-01 — 明确的已知付款尝试前置事实

- 新增 frozen、primitive-serializable 的 preflight fact；
- 必须显式包含：status、reason codes、current request ref、相关 attempt refs、阻断 request refs、限制；
- 只接受精确 tuple 容器和精确 `PaymentExecutionRecord`；
- dict、list、子类、proxy 或缺字段对象不得进入属性读取；
- fact 只表达证据，不直接执行 callback、支付、查询或恢复。

Mandatory evidence: 类型反例、primitive JSON、immutability、静态无副作用审计。

### AC-02 — 复用现有 P2 binding，不建立第二套规则

对于 request_id 与当前 request 相同的 `SUCCEEDED` attempt：

- 必须调用现有 `verify_payment_execution_binding(mandate, order, request, attempt)`；
- binding `VALID` 才能形成可信 duplicate preflight；
- binding `INVALID` 或 `MISSING_EVIDENCE` 必须失败关闭为 `INDETERMINATE`，callback=0；
- 不同 request_id 的 attempt 不得阻断当前合法支付；
- 不复制 amount、currency、payee、authority、agent、order 等字段比较规则。

Mandatory evidence: valid、mismatch、missing、unrelated、malformed 矩阵和静态调用审计。

### AC-03 — Runtime Gate 在 callback 前消费事实

- `gate_webshop_buy_now` 增加 keyword-only 已知付款尝试输入或等价 typed preflight 输入；
- 同一 request 的 bound `SUCCEEDED` attempt 必须在 `checkout_callback` 之前阻断；
- final decision=`DENY`；
- callback count=0、checkout_executed=false、callback result ref=None；
- reason codes 至少包含稳定 duplicate request / preflight 依据；
- outcome 暴露 preflight fact，供 runner 和后续轨迹消费；
- 不允许先 callback 再由 Sidecar 标记 blocked。

Mandatory evidence: callback spy、异常 callback、调用顺序反例。

### AC-04 — 非重复任务保持原行为

以下情况不得被错误阻断：

- attempt tuple 为空；
- 只有不同 request_id 的成功 attempt；
- 当前正常 T01；
- T02—T09、T11、T12。

必须保存非 T10 的 11 项 normalized task result 投影 before / after，并证明完全一致。

Mandatory evidence: 11-task projection digest equality。

### AC-05 — 同 target fixture 的项目影响

Phase A target fixture / runner hashes 在 BEFORE 和 AFTER 必须完全一致。

AFTER 必须达到：

```text
T10 decision                         DENY
T10 callback                         0
T10 duplicate gap                    absent
重复或禁止副作用率                  0/12
callback 次数匹配率                 12/12
错误放行率                          0
漏确认率                            0
禁止状态写入率                      0
```

允许：

```text
GESR                                 0/12
产品观测权威轨迹                    0/12
```

因为 B-03 不在本任务范围。

Mandatory evidence: BEFORE / AFTER JSON、delta、同 hash、三次 AFTER digest。

### AC-06 — target 不得根据 AFTER 反向修改

- target fixture 必须在任何 `src/` 修改前冻结并哈希；
- AFTER 阶段不得修改 target fixture、runner 或 metric definitions；
- 临时把 expected callback 放宽为 1，独立安全上限仍应阻止洗绿；
- 不删除 T10、不降低 max callback、不更换 denominator。

Mandatory evidence: phase boundary source hashes、target hashes、tamper test。

### AC-07 — 回归守护

必须通过：

- known payment attempt preflight 专项与反例矩阵；
- WebShop Runtime Gate 专项；
- Payment Binding、Sidecar、Recovery、Status Conflict；
- 项目基线专项；
- 全量测试不少于 428；
- 正式入口 13/13。

不得删除、跳过或放宽既有测试。

### AC-08 — 完整影响报告与证据

REPORT 必须包含：

- 初始、Phase A、Phase B、最终 git status；
- 开工、BEFORE、AFTER 的 `src/` hashes；
- target fixture / runner BEFORE-AFTER hashes；
- BEFORE / AFTER 项目指标和 delta；
- 非 T10 投影 digest；
- 完整允许范围 diff 和 SHA-256；
- 逐 AC 对应 EV triplets；
- project impact verdict 候选及 scope caveat；
- deviations、未运行项和已知限制；
- validator `OK`。

## Allowed scope

May add or modify only:

- `src/agentic_payment_experiment/trusted_execution/known_payment_attempt.py`
- `src/agentic_payment_experiment/trusted_execution/__init__.py`
- `src/agentic_payment_experiment/webshop_runtime_gate.py`
- `src/agentic_payment_experiment/__init__.py`（仅导出新公开类型 / 函数，如确需）
- `samples/evaluation/project_impact_t10_preflight_target_v1.json`
- `scripts/validation/run_project_impact_baseline.py`
- `tests/trusted_execution/test_known_payment_attempt.py`
- `tests/test_webshop_runtime_gate.py`
- `tests/test_project_impact_baseline.py`
- `docs/04_验证体系/项目级能力评测基线_v1.md`（只追加本实验 before / after）
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/REPORT.md`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/EV-*`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/*.json`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/*.diff`
- `CURRENT.md`（仅原子路由）

No other file may change for this task.

## Exclusions and forbidden side effects

- 不修改 `webshop_payment_sidecar.py`、payment recovery、status conflict 或 lifecycle；
- 不建设产品 Authoritative Trace；
- 不处理 PENDING / UNKNOWN attempt 的重试或恢复策略；
- 不把任意 caller 提供的 raw request ID 直接视为可信已付款事实；
- 不新增第二套 Payment Binding；
- 不修改 T01—T09、T11、T12 target；
- 不执行 WebShop runtime、真实 Buy Now、网络、LLM、支付、查询、履约、退款或钱包操作；
- 不安装依赖、不创建环境、不启动后台进程；
- 不 commit、不 push、不 rewrite history；
- 不清理继承工作区改动。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | Phase A target materialization + BEFORE run | src 未变；T10 ALLOW/callback1；target/runner hashes 冻结 |
| VP-02 | known attempt preflight 专项与反例矩阵 | valid success blocks；mismatch/missing fails closed；unrelated does not block |
| VP-03 | WebShop Runtime Gate 专项 | callback 前阻断，callback spy=0 |
| VP-04 | target fixture AFTER repeat=3 | T10 DENY/callback0；副作用0/12；callback12/12；三次一致 |
| VP-05 | BEFORE / AFTER 与 11-task projection comparison | 同 target/runner hashes；非 T10 完全一致 |
| VP-06 | 相关能力回归 | Payment Binding、Sidecar、Recovery、Conflict、project baseline 全通过 |
| VP-07 | `PYTHONPATH=src python3 -m unittest discover -s tests -v` | 不少于 428，全部通过 |
| VP-08 | `python3 run_experiment.py` | 13/13 PASS |
| VP-09 | scope / hash / diff / static audit | 仅允许文件变化，无第二规则引擎或外部副作用 |
| VP-10 | workflow validator | `OK` |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- 无法在修改 src 前冻结 target fixture / runner 和 BEFORE；
- 必须修改 Sidecar 或 Recovery 才能在 callback 前阻断；
- 无法复用 `verify_payment_execution_binding`；
- 正常或 unrelated attempt 被错误阻断；
- target / runner 在 AFTER 阶段发生变化；
- 任一非 T10 固定任务漂移；
- 需要网络、新依赖或外部副作用；
- 需要用户决定新的风险容忍度或业务语义。

## Amendments

None.
