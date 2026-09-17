# Evaluator Amendment A1

Task ID: `F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1`  
Amendment: `A1 / source pin + report attribution + regression gate hardening`  
Date: `2026-09-17`

## Why this amendment exists

Evaluator 在 Executor 实际开始前再次复核 F0 执行包，确认主方向正确，但发现四个可提前收紧的验收漏洞：

1. 原合同允许 `github_archive` 作为 clone 失败后的替代来源，但现有 checker 无法机械证明本地解压目录与 `v0.2.0 / b4587ac` 是同一源码快照；
2. 原执行顺序是先跑 L2，再写 `REPORT.md`，导致 AC-07 的 gap classification / next direction 没进入冻结 L2；
3. AC-06 明确要求 S01-S13 不退化，但 Validation Plan 原版没有单独执行 `run_experiment.py`；
4. AP2 官方仓库公开 issue 已显示 specification 与 SDK/schema 可能出现漂移，因此 F0 不能只引用规范正文就把能力标成 `SUPPORTED`，必须在存在实现/schema 的维度交叉核对。

本 Amendment 不改变 H-33 假设、12 个冻结维度、零产品修改原则和 F0 measurement-only 定位。

## A1-01 — Source acquisition 收紧

本轮只允许 `git` 方式获取官方 release：

```text
repository = https://github.com/google-agentic-commerce/AP2
release = v0.2.0
resolved commit prefix = b4587ac
source_acquisition_method = git
source_root = local_sources/third_party/ap2-v0.2.0
```

不再允许 `github_archive` fallback。

若 read-only clone/fetch 无法完成，Executor 不得换另一份源码继续测量，直接标记：

```text
Gap classification: SOURCE_ENV_BLOCKED
Next direction: SOURCE_ENV_PREPARATION
```

并停止，不运行需要 source/matrix 的完整 L2。

## A1-02 — specification ↔ SDK/schema cross-check

12 个维度保持不变，但测量规则补充：

- 当某个语义同时存在于 `docs/` 规范与 `code/sdk/` / `schemas/` 实现时，`official_evidence` 必须至少同时指向规范侧和实现/schema 侧；
- 若二者语义不一致，不得标 `SUPPORTED`；应标 `PARTIAL` 或 `UNSUPPORTED`，并在 `gap_reason` 明确写出 `OFFICIAL_SPEC_SDK_DRIFT`；
- 若该维度在 v0.2.0 只有规范、没有对应 SDK/schema，则可以只引用规范，但 `gap_reason` / `first_breakpoint` 必须如实说明 `SPEC_ONLY`；
- 不得用 rolling `main` 的后续修复替代 v0.2.0 的真实状态。

这一步是为了测“v0.2.0 release 实际合同”，不是评价 AP2 最新主干质量。

## A1-03 — REPORT 归因字段先于最终 L2

Executor 必须先写出 `REPORT.md` 的测量结论草稿，至少冻结 classification / next direction / impact / product change 四个归因字段，再运行最终 L2 Validation Plan。L2 通过后再补全 Gate summary 并将最终 `Executor status` 置为 `SUBMITTED_FOR_REVIEW`；若 L2 失败，则状态改为 `BLOCKED`。

`REPORT.md` 最终除 v2.2 固定结构外，必须包含以下四个唯一结论字段：

```text
Gap classification: <ONE_VALUE>
Next direction: <ONE_VALUE>
Project impact candidate: NOT_APPLICABLE
Product changes: NONE
```

允许的 classification 与 next direction 必须一一对应：

```text
NO_PRODUCT_GAP
→ F1_OFFICIAL_SDK_EXECUTABLE_SLICE

BOUNDED_ADAPTER_GAP
→ BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE

CORE_SEMANTIC_GAP
→ CORE_SEMANTIC_REASSESSMENT

SOURCE_ENV_BLOCKED
→ SOURCE_ENV_PREPARATION
```

F0 是测量包，因此无论结果是哪一类，本轮产品影响都只能记为 `NOT_APPLICABLE`；不能把“发现兼容/不兼容”写成产品能力提升或回退。

## A1-04 — Validation Plan 补强

最终 L2 必须包含：

1. AP2 source pin + 12 维 matrix audit；
2. REPORT attribution audit；
3. 现有 AP2 focused tests；
4. project 12-task baseline repeat=3；
5. `run_experiment.py`，明确覆盖 S01-S13；
6. full unittest discovery。

只有完整 L2 全部通过，且 workflow validator 通过，Executor 才可把 `Executor status` 写成 `SUBMITTED_FOR_REVIEW`。

## Explicitly forbidden

A1 不增加任何产品实现权限。仍禁止：

- 修改任何 `src/` / `tests/`；
- 安装 AP2 SDK、ADK、Gemini 或其他新依赖；
- 使用 Google API Key、Gemini、Vertex；
- 跑完整 AP2 多 Agent Demo；
- 支付宝 Sandbox / x402 testnet / wallet / real payment；
- 生产 credential / PII；
- commit、push、history rewrite。

## Final execution order after A1

```text
1. git 只读固定 AP2 v0.2.0 / b4587ac
2. 写 AP2_SOURCE_PIN.json
3. 按 12 维抽官方 spec + SDK/schema/HNP evidence
4. 对照本项目 Adapter / Canonical Core
5. 写 AP2_V020_COMPATIBILITY.json
6. 写 REPORT.md（含唯一 classification + next direction）
7. 跑完整冻结 L2 Validation Plan
8. L2 全绿后跑 workflow validator
9. SUBMITTED_FOR_REVIEW → Evaluator L3
```

本 Amendment 在 Executor 尚未产生 F0 evidence / REPORT / 产品改动前冻结，因此不消耗 implementation/L2 retry 配额。
