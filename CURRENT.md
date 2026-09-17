# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1
task_kind: one_off
state: EXECUTING
current_role: Executor
baseline_commit: 8a1a484cf70b39c5c610947b1c4efa019bab41bc
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-09-17-r46
active_bottleneck_id: B-06
hypothesis_id: H-33
contract_path: docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/REPORT.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Global position / 全局位置

```text
A. 评测与治理底座                  [CLOSED / 12/12]
→ B. 授权、绑定、来源、执行前治理   [CLOSED]
→ C. 支付生命周期、恢复、补救证据链 [CLOSED]
→ D. 责任归因与可消费审计链         [CLOSED]
→ E. 主体真实性 / 凭证 / 签署指令   [LOCAL REPRESENTATIVE CLOSURE]
→ F. 外部真实协议 / SDK / 网络接入   [CURRENT: F0]
```

## Current bottleneck / 当前第一瓶颈

A-E 已经证明本地 Canonical Facts + Trust Core 在代表性支付场景中成立，但还没有证明**真实外部协议定义**能无语义漂移进入这套核心。

当前先选 AP2 v0.2.0 作为 F 阶段第一外部消费者/验证场：

```text
AP2 v0.2.0 official source / schemas / HNP samples
        ↓
现有 AP2 Adapter / Signed Instruction
        ↓
Canonical Facts
        ↓
A-E Trust Core
```

F0 不安装官方 SDK、不跑 Gemini/Vertex、不修改产品、不接 Sandbox、不碰钱包和真实资金。第一步只做官方合同兼容测量。

## Current task / 当前任务

Task：`F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1`

性质：`measurement-only / one_off`。

Executor 读取：

1. `docs/02_未来规划/F阶段公开验证路线_20260917.md`
2. `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/CONTRACT.md`
3. `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/VALIDATION_PLAN.yaml`
4. `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/EVALUATOR_AMENDMENT_A1.md`
5. `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evaluator_checks/ap2_source_matrix_audit.py`
6. `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evaluator_checks/report_attribution_audit.py`
7. `docs/reference/01_支付协议/AP2字段差距说明.md`

## Evaluator recheck / 再次复核结论

Executor 在 Amendment A1 冻结前已经完成过一轮旧版 L2：`4/4 PASS`。该轮内容测量可保留，但旧 Gate 已被 A1 的 6 项门禁 supersede（取代），不能作为最终提交依据。

已封存：

- `REPORT_ATTEMPT1_PRE_A1.md`
- `evidence/attempt1_pre_a1/`

Evaluator 对现有 source pin + 12 维 matrix 重新运行 A1 收紧后的 source/matrix checker，结果 `PASS`；说明 `BOUNDED_ADAPTER_GAP` 的主体测量目前没有被推翻。

当前唯一明确未通过的新检查是 REPORT attribution：旧 REPORT 没有冻结 `Next direction` / `Product changes` 精确字段，并且旧报告把 `BOUNDED_ADAPTER_GAP` 直接叫作 F1。按路线应改为：

```text
Gap classification: BOUNDED_ADAPTER_GAP
Next direction: BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE
Project impact candidate: NOT_APPLICABLE
Product changes: NONE
```

Executor 下一步不是重做 12 维研究，而是按 `EVALUATOR_AMENDMENT_A1.md`：补正 REPORT 归因字段，必要时补 spec↔SDK/schema 交叉证据，然后重跑新的 6 项 L2。只有 `6/6 PASS` + workflow validator OK 后才重新 `SUBMITTED_FOR_REVIEW`。

## Executor execution order / 执行顺序

```text
1. 只读获取官方 AP2 v0.2.0
   repository = google-agentic-commerce/AP2
   tag = v0.2.0
   commit prefix = b4587ac
   source → local_sources/third_party/ap2-v0.2.0

2. 记录 AP2_SOURCE_PIN.json

3. 从官方 v0.2.0 实际 source/schema/HNP samples 抽取 12 个冻结维度

4. 对照当前：
   adapters/ap2.py
   adapters/ap2_signed_instruction.py
   Canonical model / validator / trace
   accepted AP2 tests / REVIEW

5. 生成 AP2_V020_COMPATIBILITY.json
   status 只能是：SUPPORTED / PARTIAL / UNSUPPORTED / NOT_APPLICABLE

6. 给出 exactly one gap classification：
   NO_PRODUCT_GAP
   BOUNDED_ADAPTER_GAP
   CORE_SEMANTIC_GAP
   SOURCE_ENV_BLOCKED

7. 先写 REPORT.md 测量结论草稿，至少冻结：
   Gap classification
   Next direction
   Project impact candidate = NOT_APPLICABLE
   Product changes = NONE

8. 运行 A1 后冻结的完整 L2 Validation Plan

9. L2 全绿后补全 Gate summary，并将 Executor status 置为 SUBMITTED_FOR_REVIEW；失败则 BLOCKED

10. 跑 workflow validator 后交 Evaluator；不得自行修产品
```

## Hard boundaries / 硬边界

允许：

- 公开 GitHub `google-agentic-commerce/AP2` 仅允许只读 git clone/fetch 固定 `v0.2.0`；archive fallback 已由 Amendment A1 禁止；
- 本地 CPU 与静态 source/schema 分析；
- task-owned evidence / helper / REPORT。

禁止：

- 修改任何 `src/` / `tests/`；
- 安装 AP2 SDK、ADK、Gemini 或新依赖；
- Google API Key / Gemini / Vertex；
- 完整 AP2 多 Agent Demo；
- 支付宝 Sandbox、x402 testnet、京东真实购物；
- 钱包、银行卡、真实支付、生产凭证/PII；
- commit、push、history rewrite。

如果任何测量需要越过上述边界，立即停止并在 REPORT 中标记 `SOURCE_ENV_BLOCKED`，交回 Evaluator。

## Completion rule / 完成条件

```text
AP2 source pin = v0.2.0 / b4587ac...
12/12 frozen dimensions measured
all official evidence traceable to local pinned source
all local evidence traceable to repo artifacts
src/tests unchanged vs 8a1a484
existing AP2 tests PASS
project baseline repeat=3 remains 12/12
full unittest zero failures
L2 Validation Plan PASS
REPORT gives exactly one gap classification and one next direction
```

F0 PASS 只表示“测量可信”，不表示 AP2 conformance，也不表示已接入真实支付。
