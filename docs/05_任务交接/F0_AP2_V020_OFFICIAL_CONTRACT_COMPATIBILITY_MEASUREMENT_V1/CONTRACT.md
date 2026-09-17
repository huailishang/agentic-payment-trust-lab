# Execution Contract

Task ID: `F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1`  
Task kind: `one_off`  
Contract state: `CONTRACT_FROZEN`  
Baseline HEAD: `8a1a484cf70b39c5c610947b1c4efa019bab41bc`  
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-09-17-r46`  
Active bottleneck: `B-06`  
Hypothesis: `H-33`  
Validation plan file: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

A—E 已完成本地代表性闭环，固定项目基线为 `12/12`。当前进入 F 阶段，第一目标不是接真钱，而是验证外部官方协议对象能否无语义漂移进入现有 Canonical Facts + Trust Core。

AP2 v0.2.0 是第一外部协议验证场，因为它公开稳定 release、SDK source、JSON schemas 与 Human Not Present 场景，并直接覆盖 Mandate、Checkout/Payment Binding、Receipt 与 Agent 自主支付授权。

本任务采用 measurement-first：先固定官方来源并测兼容性，不修改产品代码。

## 1. Official source / 官方来源冻结

```text
repository: https://github.com/google-agentic-commerce/AP2
release: v0.2.0
release commit prefix: b4587ac
license: Apache-2.0
source destination: local_sources/third_party/ap2-v0.2.0
```

Executor 必须只读获取该 release/tag，不使用 rolling `main` 代替。`local_sources/` 已被 git ignore，不得把第三方仓库整体提交进本项目。

允许联网范围仅限：

- `github.com/google-agentic-commerce/AP2` 的 read-only clone/fetch；
- 若 GitHub clone 不可用，可下载 GitHub 官方 v0.2.0 source archive；
- 不调用 Google AI / Gemini / Vertex / 支付 API。

## 2. Principal measurement / 唯一主要任务

```text
AP2 v0.2.0 official source / schemas / HNP samples
        ↓
extract protocol facts and verification responsibilities
        ↓
compare with current:
  src/agentic_payment_experiment/adapters/ap2.py
  src/agentic_payment_experiment/adapters/ap2_signed_instruction.py
  Canonical Facts / Trust Core contracts
        ↓
produce deterministic compatibility matrix
        ↓
freeze first external gap / no-gap conclusion
```

不允许在本任务中修 Adapter 或 Core。

## 3. Required outputs / 必须输出

Executor 必须生成：

### 3.1 Source pin

`docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/AP2_SOURCE_PIN.json`

至少包含：

```text
repository
requested_release
resolved_tag
resolved_commit
commit_prefix_match
license
source_root
source_acquisition_method
network_scope
```

### 3.2 Compatibility matrix

`docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/AP2_V020_COMPATIBILITY.json`

必须恰好覆盖以下 12 个维度：

```text
mandate_schema_version
hnp_open_closed_constraints
checkout_hash_binding
payment_checkout_binding
amount_currency
payee_merchant
agent_key_cnf_identity_boundary
checkout_payment_receipts
rejection_receipt_reuse_prevention
selective_disclosure_data_minimization
signature_verification_responsibility
canonical_core_rule_invariance
```

每个维度必须有：

```text
status = SUPPORTED | PARTIAL | UNSUPPORTED | NOT_APPLICABLE
official_evidence
local_evidence
gap_reason
first_breakpoint
```

### 3.3 Measurement report

`REPORT.md` 必须总结：

- 12 维状态分布；
- 第一个真实断点；
- gap 属于 `NO_PRODUCT_GAP / BOUNDED_ADAPTER_GAP / CORE_SEMANTIC_GAP / SOURCE_ENV_BLOCKED` 哪一类；
- 下一包只建议一个主方向；
- 不把 `PARTIAL/UNSUPPORTED` 写成已覆盖。

## 4. Measurement rules / 测量规则

### 4.1 Source facts must be real

官方证据必须来自 v0.2.0 source tree 内实际文件，例如：

- `docs/ap2/specification.md`；
- `code/sdk/python/ap2/`；
- `code/sdk/python/ap2/schemas/`；
- Human Not Present sample/scenario files。

不得只根据本项目旧文档反推官方事实。

### 4.2 No source copying into product

允许在 evidence JSON 中记录文件路径、字段名、短摘要和 hash；不得复制大段第三方源码或规范正文到项目产品代码。

### 4.3 Honest status

若当前 Adapter 只处理 decoded snapshot，而官方对象包含未验证的 SD-JWT / Mandate signature / receipt relation，则应按真实能力标 `PARTIAL` 或 `UNSUPPORTED`，不得因为字段“名字类似”就标 `SUPPORTED`。

### 4.4 No dependency install

第一轮不安装 AP2 SDK、ADK、Gemini 或其他新依赖。只做 source/schema/static compatibility measurement。

若测量必须安装依赖，立即停止并在 REPORT 标记 `SOURCE_ENV_BLOCKED`，由 Evaluator 决定 F1 是否授权安装。

## 5. Allowed scope / 允许范围

允许修改：

- 本 task 目录下 `REPORT.md`、`evidence/*`；
- task-owned measurement helper（如确实需要）只能放本 task 目录；
- `local_sources/third_party/ap2-v0.2.0` 只读第三方源码，不提交。

允许读取：

- `src/agentic_payment_experiment/adapters/ap2.py`；
- `src/agentic_payment_experiment/adapters/ap2_signed_instruction.py`；
- Canonical model / validator / trace 相关源码；
- 现有 AP2 tests、H-27 REVIEW、AP2 field-gap reference。

## 6. Exclusions / 明确排除

禁止：

- 修改任何 `src/` 产品代码；
- 修改任何 `tests/` 产品回归测试；
- 修改 AP2 官方 source；
- 安装新依赖；
- 使用 Google API Key、Gemini、Vertex；
- 跑完整 AP2 多 Agent Demo；
- 真实支付、钱包、银行卡、测试币、生产凭证；
- 支付宝 Sandbox；
- x402 testnet；
- 京东真实购物；
- commit、push、history rewrite。

## 7. Acceptance Criteria / 验收条件

### AC-01 — Official source pinned

AP2 source 必须解析为 `v0.2.0`，resolved commit 必须以 `b4587ac` 开头，来源为官方仓库，Apache-2.0 可确认。

### AC-02 — 12-dimension matrix complete

12 个冻结维度恰好全部出现，无遗漏、无额外“凑分”维度；每项状态属于冻结枚举且证据字段完整。

### AC-03 — Official evidence traceable

每项 `official_evidence` 至少包含一个 v0.2.0 source-relative path；关键结论可从本地只读 source tree 重新核验。

### AC-04 — Local evidence traceable

每项 `local_evidence` 必须映射到当前项目源码/测试/已有 accepted REVIEW，不允许只有自然语言判断。

### AC-05 — Product frozen

`src/` 与 `tests/` 相对 baseline HEAD 不得因 H-33 产生修改；本任务不允许通过实现修复让 matrix 变绿。

### AC-06 — Existing project baseline preserved

现有 AP2 单测、S01-S13、项目 12-task baseline 与 full unittest 不退化。

### AC-07 — Honest next-step attribution

REPORT 必须给出 exactly one classification：

```text
NO_PRODUCT_GAP
BOUNDED_ADAPTER_GAP
CORE_SEMANTIC_GAP
SOURCE_ENV_BLOCKED
```

并只建议一个下一主方向。Task PASS 仅代表“测量可信”，不代表 AP2 conformance。

## 8. Stop conditions / 停止条件

立即停止并交 Evaluator：

- 官方 source tag/commit 对不上；
- 需要安装依赖；
- 需要真实 API/凭证；
- 需要修改 `src/` / `tests/`；
- 发现 v0.2.0 source 与本合同冻结事实冲突；
- 无法从官方 source 形成可复核的 12 维矩阵。

## 9. Authorization / 授权

- local CPU: true
- public GitHub read-only network: true
- dependency install: false
- external AI/API call: false
- real payment: false
- testnet/wallet: false
- credential/PII: false
- commit: false
- push: false
- history rewrite: false
