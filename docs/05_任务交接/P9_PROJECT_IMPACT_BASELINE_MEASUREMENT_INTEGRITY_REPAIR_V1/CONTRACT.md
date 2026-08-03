# Frozen Task Contract

Task ID: `P9-PROJECT-IMPACT-BASELINE-MEASUREMENT-INTEGRITY-REPAIR-V1`  
Parent task: `P9-PROJECT-IMPACT-BASELINE-V1`  
Task name: 项目影响基线测量完整性修复 v1  
Task kind: `repair`  
Risk: `L0`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-03-r3`  
Inherited active bottleneck: `B-01`  
Inherited hypothesis: `H-01`  
Parent verdict: `REJECTED / NOT_APPLICABLE`

本修复包不改变产品能力，只修复评测器测量语义。修复后的项目影响裁决仍为 `NOT_APPLICABLE`。

## Failed parent ACs and exact counterexamples

### Parent AC-01 / AC-02 / AC-03 / AC-06

T10 的冻结事实：

```text
user_goal = 同一请求已有成功付款时不产生第二次付款副作用
known_payment_attempts = [same_request_succeeded]
limitations includes no_second_payment_executed
```

但 fixture 同时写入 `expected_callback_count=1`。当前产品实际执行一次 callback 后，Sidecar 才记录 `duplicate_payment_blocked=true`，runner 却把 T10 判为 matched，并把重复副作用率记录为 0/12。

### Parent AC-02 / AC-03 / AC-06

T01、T09—T12 的 `trace_status=VALID` 来自 runner 自行构造 ReplayEvent。该证据只能证明 evaluator-synthesized replay 可校验，不能证明产品实际产出 authoritative trace。

### Parent AC-08

accepted package 未保存最终 git status、完整 diff 文件和 diff SHA-256，且 REPORT 中 AC—EV 编号映射与冻结合同发生偏移。

## Single objective

修复项目级基线的测量完整性，使重复副作用、产品观测轨迹和评测器合成 Replay 被严格区分；重新计算真实项目指标，并补齐完整、可审计的证据包。

不修复产品代码，不让当前基线变绿，不预设最终 GESR。

## Acceptance criteria

### AC-01 — T10 副作用前重复保护语义

- Given: 同一 request 已存在 `SUCCEEDED` 付款记录。
- When: 评测 T10。
- Must observe:
  - fixture 的 `expected_callback_count=0`；
  - fixture 明确禁止 `duplicate_payment_callback_executed`；
  - 当前产品若仍产生 callback，actual callback 必须保留为 1，不能被改写；
  - T10 必须标记为 capability gap；
  - `duplicate_payment_blocked=true` 不能抵消已经发生的 callback。
- Must not observe:
  - 通过修改 user_goal、known attempts 或 limitations 让 callback=1 合法化；
  - 将 callback 解释为“只是测试 seam”并从副作用指标中排除。
- Evidence: fixture audit、T10 raw result、独立手算。

### AC-02 — 零容忍副作用指标不可被 expected 值掩盖

- Given: 任一任务具有已有成功付款、禁止 callback 或禁止 retry 的前置事实。
- When: actual callback/retry 超过业务语义允许值。
- Must observe:
  - 生成稳定 gap code，例如 `duplicate_payment_callback_executed`；
  - `duplicate_or_forbidden_side_effect_rate.count >= 1`；
  - 当前未改产品前提下，T10 不计入 GESR；
  - GESR matched count 不得高于 4/12，除非执行者提供产品观测证据证明另一个原 gap 被真实消除；本任务禁止修改产品，因此预期不会发生。
- Must not observe: 用 fixture expected callback=1 把 actual callback=1 判为安全。
- Evidence: repeat-3 result、metric audit、至少 T01/T07/T10/T12 四项手算。

### AC-03 — 区分产品轨迹与合成 Replay

- Given: runner 可以为测试 Replay API 手工构造 ReplayEvent。
- When: 输出轨迹相关字段和指标。
- Must observe:
  - 分离 `product_observed_trace_status` 与 `evaluator_synthesized_replay_status`，或使用语义等价的两个明确字段；
  - evaluator-synthesized replay 可以为 VALID，但不得满足 `authoritative_trace` 产品证据阶段；
  - 只有来自现有产品返回对象或产品实际产出的事件，才能计入产品轨迹完整率；
  - 若当前没有产品轨迹，明确记录 `NOT_AVAILABLE / unknown`，不得乐观升级；
  - 重新计算 evidence-stage completeness 与 GESR。
- Must not observe: runner 自己创建 ReplayEvent 后直接把同一结果标为产品 authoritative trace。
- Evidence: runner static audit、逐任务 trace provenance、结果 JSON。

### AC-04 — fixture 与 expected 不可反向生成

- Given: 修复后的 fixture。
- When: 临时篡改 T10 expected callback 或 trace provenance。
- Must observe:
  - actual 产品行为保持不变；
  - runner 产生 mismatch，而不是反向修改 expected；
  - 原 fixture 字节和 SHA-256 不变。
- Evidence: targeted unittest and raw output。

### AC-05 — 三次确定性与机器可读输出

- Given: 同一 HEAD、fixture、runner 和本地环境。
- When: 连续运行三次。
- Must observe:
  - 规范化 task results、metrics、gap codes 和 trace provenance 三次 digest 完全一致；
  - 输出 fixture/runner hashes、limitations、project summary；
  - capability gaps 不导致 runner 非零退出。
- Evidence: repeat-3 EV triplet。

### AC-06 — 只修评测器，不修改产品

- Must observe:
  - 开工前后所有 `src/**/*.py` SHA-256 完全一致；
  - 不修改 P1—P6、Fact Lineage、Runtime Gate、Sidecar、Replay 或任何产品决策；
  - 不使用 monkeypatch 或复制第二套业务规则。
- Evidence: protected source hash audit、git diff audit。

### AC-07 — 回归守护

- Must observe:
  - 项目基线专项全部通过；
  - 相关能力回归不少于 104 且全部通过；
  - 全量测试不少于 425 且全部通过；
  - 正式入口 13/13 PASS。
- Must not observe: 删除、跳过或降低既有测试。
- Evidence: 完整 EV triplets。

### AC-08 — 完整证据包与正确映射

- Must observe:
  - 初始 git status；
  - 最终 git status；
  - 保存本任务允许范围的完整 `.diff` 或 `.patch`；
  - diff SHA-256；
  - 改动文件 SHA-256；
  - REPORT 中 AC-01 至 AC-08 与 EV 编号逐条一致；
  - Impact comparison 写明 parent before=invalid measurement、after=corrected measurement；
  - project impact verdict=`NOT_APPLICABLE`；
  - workflow validator=`OK`。
- Must not observe: commit、push、history rewrite、网络或支付副作用。

## Allowed scope

May add or modify only:

- `samples/evaluation/project_impact_baseline_v1.json`
- `scripts/validation/run_project_impact_baseline.py`
- `scripts/validation/project_impact_baseline_*.py`
- `tests/test_project_impact_baseline.py`
- `docs/04_验证体系/项目级能力评测基线_v1.md`
- `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/REPORT.md`
- `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/EV-*`
- `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/evidence/*.diff`
- `CURRENT.md`（仅按 v2.1 原子路由）

No `src/` file may change.

## Exclusions and forbidden side effects

- 不修复重复付款产品逻辑；只把它如实测为 gap；
- 不建设新的 Authoritative Trace 产品能力；只修正 provenance 分类；
- 不新增 Agent、LLM、浏览器、UI、UCP/ACP、测试网或银行沙箱；
- 不执行 WebShop runtime、Buy Now、真实 callback、支付、查询、履约、退款或钱包副作用；
- 不安装依赖、不创建环境、不启动后台进程；
- 不修改 parent REVIEW、accepted REPORT 或 accepted EV-01—EV-08；
- 不 commit、不 push、不清理继承改动。

## Validation plan

| VP | Command | Expected |
|---|---|---|
| VP-01 | `PYTHONPATH=src python3 scripts/validation/run_project_impact_baseline.py --spec samples/evaluation/project_impact_baseline_v1.json --repeat 3 --output <evidence>/corrected_project_impact_baseline.json` | 三次一致；T10 gap；重复副作用 count≥1；产品轨迹与合成 Replay 分离 |
| VP-02 | `python3 -m unittest tests.test_project_impact_baseline -v` | 所有测量完整性测试通过 |
| VP-03 | `python3 -m unittest tests.trusted_execution.test_fact_lineage tests.test_attack_overlay tests.test_webshop_runtime_gate tests.test_webshop_payment_sidecar tests.test_payment_recovery tests.test_payment_status_conflict -v` | 不少于 104，全部通过 |
| VP-04 | `PYTHONPATH=src python3 -m unittest discover -s tests -v` | 不少于 425，全部通过 |
| VP-05 | `python3 run_experiment.py` | 13/13 PASS |
| VP-06 | source hash + scope + diff audit | `src/` 哈希不变；完整 diff 与 SHA-256 已保存 |
| VP-07 | `python3 <workflow-skill>/scripts/validate_workflow.py --repo . --current CURRENT.md` | OK |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- 需要修改任何 `src/` 产品文件；
- 无法在评测输出中区分 product-observed trace 与 synthesized replay；
- T10 的业务目标被认为允许 callback=1；
- 为了提高 GESR 删除任务、放宽 expected 或隐藏 gap；
- 三次结果不稳定；
- 既有回归失败；
- 需要网络、新依赖或任何外部副作用。

## Amendments

None.
