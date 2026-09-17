# Executor Report

Task ID: `F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1`  
Task kind: `one_off`  
Executor status: `SUBMITTED_FOR_REVIEW`  
Baseline HEAD: `8a1a484cf70b39c5c610947b1c4efa019bab41bc`  
Implementation commit: `NONE`  
Current state: `EXECUTING / Executor`  
Active bottleneck: `B-06`  
Hypothesis: `H-33`  
Gap classification: `BOUNDED_ADAPTER_GAP`
Next direction: `BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE`
Project impact candidate: `NOT_APPLICABLE`
Product changes: `NONE`

## 1. 执行结论

F0 已完成。Executor 只读固定官方 `google-agentic-commerce/AP2` 的 `v0.2.0` tag：

```text
resolved commit = b4587ac1d055888a73b4b21750973cffba961793
license         = Apache-2.0
source root     = local_sources/third_party/ap2-v0.2.0
acquisition     = git clone pinned tag
```

没有安装 AP2 SDK / ADK / Gemini 依赖，没有调用 Google API / Vertex / Gemini，没有修改任何 `src/` / `tests/` 产品代码，也没有执行钱包、Sandbox、testnet 或真实支付。

基于官方 specification、JSON schemas、Python SDK source 与 Human Not Present samples，12 个冻结维度全部完成静态兼容测量：

```text
SUPPORTED       3
PARTIAL         6
UNSUPPORTED     3
NOT_APPLICABLE  0
TOTAL          12
```

最终且唯一 gap classification（差距分类）：

```text
BOUNDED_ADAPTER_GAP
```

含义不是“AP2 已支持”，而是：**当前第一个已验证断点在 AP2 官方对象 / 协议证据进入 Canonical Facts 之前的 Adapter / external verifier（外部验证器）边界；F0 没有发现需要为了 AP2 给 Canonical Trust Core 增加协议特判的证据。**

A1 后最终正式 L2：`6/6 PASS`，mandatory failures=`0`；A1 前旧 `4/4` Gate 已封存，不作为最终提交依据。

## 2. Official source pin（官方来源冻结）

证据：

`evidence/AP2_SOURCE_PIN.json`

冻结结果：

```text
repository        https://github.com/google-agentic-commerce/AP2
requested release v0.2.0
resolved tag      v0.2.0
resolved commit   b4587ac1d055888a73b4b21750973cffba961793
prefix match      true
license           Apache-2.0
```

本地源保存在 git-ignored：

`local_sources/third_party/ap2-v0.2.0`

正式 VP-01 已机械确认 tag commit、HEAD、官方路径、12 维证据路径和 `src/tests` 冻结状态。

### Auxiliary checker note

Task 目录中另有一个未进入 frozen `VALIDATION_PLAN.yaml` 的 `source_pin_audit.py`。它对两个描述字段使用比正式 VP-01 更窄、且互不兼容的字符串枚举：

```text
source_pin_audit.py       expects source_acquisition_method = git_clone_tag
formal VP-01 matrix audit expects source_acquisition_method = git

source_pin_audit.py       expects network_scope = official_github_read_only
formal VP-01 matrix audit expects network_scope string contains official repository URL
```

两组约束没有单一字符串交集。Executor 没有修改 evaluator checker，而是以 frozen Validation Plan 为执行权威：

- `source_acquisition_method = git`
- `source_acquisition_detail = git_clone_tag`
- `network_scope` 同时记录只读策略与官方仓库 URL
- `network_scope_policy = official_github_read_only`

实际 source/tag/commit 均已由 Git 自身和 VP-01 独立机械确认，因此这不是 `SOURCE_ENV_BLOCKED`。

## 3. 12-dimension compatibility matrix

完整机器可读矩阵：

`evidence/AP2_V020_COMPATIBILITY.json`

| Dimension | Status | 大白话结论 |
|---|---|---|
| `mandate_schema_version` | PARTIAL | 官方要求 exact `vct` 版本；当前 snapshot 有 `vct`，但 Adapter 没有把 wrong/future vct fail closed |
| `hnp_open_closed_constraints` | PARTIAL | HNP、预授权、trigger 和一部分支付约束可映射；完整 open→closed SD-JWT chain / constraints 未验证 |
| `checkout_hash_binding` | UNSUPPORTED | 官方 `checkout_jwt ↔ checkout_hash` 没有被当前 Adapter 计算/验证 |
| `payment_checkout_binding` | PARTIAL | 本地已有 ID/amount/merchant/order-payment 连续绑定，但官方 `transaction_id/payment.reference ↔ checkout hash` 没验证 |
| `amount_currency` | SUPPORTED | minor unit → Decimal、currency 与 limit 语义可忠实进入 Canonical Core |
| `payee_merchant` | SUPPORTED | stable merchant identifier + allowed payee membership 可直接映射 |
| `agent_key_cnf_identity_boundary` | PARTIAL | 本地有协议中立真实性/持有证明边界，但 AP2 `cnf` / KB-SD-JWT 没接入 |
| `checkout_payment_receipts` | UNSUPPORTED | 核心能表达 lifecycle/trace，但没有 AP2 Receipt JWT signature/reference ingestion |
| `rejection_receipt_reuse_prevention` | UNSUPPORTED | 有通用幂等/重放保护，但没有“收到 rejection receipt 才允许继续复用 open mandate”的 AP2 状态机输入 |
| `selective_disclosure_data_minimization` | PARTIAL | H-30 DataDisclosureFact 可复用，但 AP2 SD-JWT nested disclosure 还没 bridge |
| `signature_verification_responsibility` | PARTIAL | 已有 AP2 merchant ES256 小切片；完整 mandate chain / checkout JWT / receipt signature 责任未覆盖 |
| `canonical_core_rule_invariance` | SUPPORTED | 当前真实断点都在 AP2 协议对象/证据层；没有证据要求 Trust Core 出现 `if AP2` 业务特判 |

### 3.1 已直接支持的 3 维

`amount_currency`、`payee_merchant`、`canonical_core_rule_invariance`。

这三项的共同点是：一旦上游字段真实性已经成立，其业务语义可以直接落到现有 Canonical Facts / neutral validator，不需要为了 AP2 改写核心支付规则。

### 3.2 PARTIAL 的 6 维

`mandate_schema_version`、`hnp_open_closed_constraints`、`payment_checkout_binding`、`agent_key_cnf_identity_boundary`、`selective_disclosure_data_minimization`、`signature_verification_responsibility`。

共同原因不是“字段不存在”，而是**当前项目主要消费已经 decode 后的 snapshot，缺少官方 AP2 object / SD-JWT / key-binding / exact schema 这一层真实协议证据验证**。

### 3.3 UNSUPPORTED 的 3 维

```text
checkout_hash_binding
checkout_payment_receipts
rejection_receipt_reuse_prevention
```

这三项不能因为项目里“有 Order Binding / Lifecycle / Idempotency”就写成已支持。官方 AP2 要求的是具体的 checkout JWT hash、signed receipt reference、receipt-governed open-mandate reuse；当前 AP2 Adapter 没有消费这些官方证据。

## 4. First real breakpoint（第一个真实断点）

```text
AP2 v0.2.0 official objects / SD-JWT / receipts
        ↓
【BREAK】current decoded-snapshot AP2 Adapter boundary
        ↓
Canonical IntentMandate / TransactionRequest / verification facts
        ↓
Trust Core
```

最上游已经可复现的断点是：

> 当前 Adapter 没有以 AP2 v0.2.0 官方 type/schema 身份为入口，先验证 exact `vct`、open→closed chain、checkout hash、`cnf` proof-of-possession、receipt signature/reference，再把可信事实交给 Canonical Core。

所以本轮没有依据把分类升级为 `CORE_SEMANTIC_GAP`。

需要特别保留一个限制：官方 open mandate 还定义 budget、payment instrument/PISP、payment reference、checkout line-item 等约束。F0 只证明**第一个断点已经出现在 Adapter/external-verifier 层**；F1 使用官方 SDK 真正执行这些 constraints 后，如果发现必须新增协议中立 Canonical Fact 才能表达某个业务约束，Evaluator 才应重新考虑 `CORE_SEMANTIC_GAP`。F0 不提前猜这个结论。

## 5. Why BOUNDED_ADAPTER_GAP

本轮没有选另外三类：

### `NO_PRODUCT_GAP` — 不成立

9/12 维不是完整 `SUPPORTED`，其中 3 个明确 `UNSUPPORTED`。不能因为旧 snapshot 流程 2/2 能跑，就声称官方 AP2 合同已覆盖。

### `CORE_SEMANTIC_GAP` — 当前证据不足

现有 Canonical Core 已有金额/币种/商户/时间/次数、Order/Request/Payment binding、签署指令事实、Credential/PoP 边界、Idempotency、DataDisclosure、Lifecycle、Trace。当前已经观察到的 AP2 缺口首先发生在这些 neutral facts 生成之前。

F0 没有修改 Core，也没有出现“只有给 Core 加 AP2-specific rule 才能表达现有官方事实”的已验证反例。

### `SOURCE_ENV_BLOCKED` — 不成立

官方 tag、commit、license、spec/schema/SDK/HNP sample 均已成功只读获取并可本地复核；完成静态测量不需要安装新依赖或调用外部 API。

因此本轮唯一分类为：

```text
BOUNDED_ADAPTER_GAP
```

## 6. Exactly one next direction（唯一下一主方向）

只建议一个方向：

> **`BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE`：先做一个有界 AP2 Adapter 能力包，围绕当前第一个真实断点补 exact `vct` / official object identity、open→closed mandate relation、checkout/payment cryptographic binding 到 protocol-neutral verification facts 的最小桥接；Canonical Core 冻结。**

这一步**不是直接进入完整 F1 official SDK executable slice**。只有该有界 Adapter 包先证明断点确实能在协议边界闭合、且不需要改 Core，Evaluator 才决定是否进入后续官方 SDK executable slice。

下一包仍不得同时扩到支付宝 Sandbox、x402 testnet、真实钱包或真实资金，也不应一次性实现完整 Receipt/reuse 生命周期。若下一包需要安装 AP2 SDK / 依赖，必须由 Evaluator 新合同显式授权；F0 没有安装任何新依赖。

## L2 Task Gate

- Validation plan: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/VALIDATION_PLAN.yaml`
- Gate result: PASS
- Gate summary: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/L2-GATE.json`

```text
checks_total       = 6
VP-01..VP-06       = PASS
mandatory_failures = 0
```

| VP | Result | 关键结果 |
|---|---|---|
| VP-01 | PASS | source pin + 12/12 matrix + official/local evidence traceability；`src/tests` frozen |
| VP-02 | PASS | REPORT attribution：`BOUNDED_ADAPTER_GAP → BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE`；impact=`NOT_APPLICABLE`；product changes=`NONE` |
| VP-03 | PASS | AP2 focused regression `17/17 PASS` |
| VP-04 | PASS | project baseline repeat=3；matched/GESR/evidence/Product Trace=`12/12`；gap=[] |
| VP-05 | PASS | S01-S13=`13/13 PASS`；PayBench=`10/10`；AP2 minimal=`2/2`；Attack Overlay=`6/6` |
| VP-06 | PASS | full unittest=`708/708 PASS` |

## 7. Existing project guardrails

F0 之后仍为：

```text
AP2 focused tests             17/17 PASS
S01-S13                       13/13 PASS
PayBench                      10/10 PASS
AP2 minimal flow              2/2 PASS
Attack Overlay                6/6 PASS
project matched               12/12
GESR                          12/12
Evidence completeness         12/12
Product Trace                 12/12
callback match                12/12
unsafe allow                  0/6
duplicate/forbidden effects   0/12
project repeat                3/3 identical
full unittest                 708/708 PASS
```

本任务没有新增产品能力，因此不报告 project metric gain。

## Impact comparison

Measurement evidence: `AP2_SOURCE_PIN.json`, `AP2_V020_COMPATIBILITY.json`, `EV-01..EV-06`, `F0_PROJECT_BASELINE.json`  
Before: local A-E baseline=`12/12`, AP2 compatibility against the pinned official v0.2.0 contract was not mechanically measured; current AP2 path was known to be decoded-snapshot / non-conformance only  
After: official source is pinned and 12/12 dimensions are measured as `SUPPORTED=3 / PARTIAL=6 / UNSUPPORTED=3`; project baseline remains `12/12` and product code is unchanged  
Delta: measurement knowledge increased; product capability delta=`0`; first external breakpoint is now localized to AP2 Adapter / external-verification boundary  
Guardrail result: AP2 focused=`17/17 PASS`; matched/GESR/evidence/Product Trace=`12/12`; callback=`12/12`; unsafe allow=`0/6`; duplicate/forbidden=`0/12`; repeat=`3/3`; full unittest=`708/708 PASS`  
Scope caveat: F0 is static source/schema/HNP compatibility measurement only. It does not prove AP2 conformance, official SDK executable integration, full SD-JWT validation, live identity, Sandbox connectivity, provider interoperability, compliance, wallet control or real payment.

Impact interpretation: measurement-only；本轮不计产品能力提升或回退。

## 8. AC → Evidence

| AC | Executor result | Evidence |
|---|---|---|
| AC-01 Official source pinned | PASS | `AP2_SOURCE_PIN.json`, `EV-01` |
| AC-02 12-dimension matrix complete | PASS | `AP2_V020_COMPATIBILITY.json`, `EV-01` |
| AC-03 Official evidence traceable | PASS | matrix official source-relative paths, `EV-01` |
| AC-04 Local evidence traceable | PASS | matrix repo-relative local paths, `EV-01` |
| AC-05 Product frozen | PASS | baseline diff `src/tests=[]`, `EV-01` |
| AC-06 Existing baseline preserved | PASS | `EV-03` AP2 17/17；`EV-04` project 12/12 repeat=3；`EV-05` S01-S13 13/13；`EV-06` full 708/708 |
| AC-07 Honest next-step attribution | PASS | `EV-02`：exactly one classification=`BOUNDED_ADAPTER_GAP`；next direction=`BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE`；impact=`NOT_APPLICABLE`；product changes=`NONE` |

## EV-01

- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Result: PASS — AP2 source pinned；12-dimension matrix complete/traceable；`src/tests` frozen.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-01.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-01.stderr.log`

## EV-02

- AC: AC-07
- Result: PASS — REPORT attribution deterministic：`BOUNDED_ADAPTER_GAP → BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE`；project impact=`NOT_APPLICABLE`；product changes=`NONE`.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-02.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-02.stderr.log`

## EV-03

- AC: AC-05, AC-06
- Result: PASS — AP2 adapter/flow/entrypoint/signed-instruction focused regression=`17/17 PASS`.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-03.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-03.stderr.log`

## EV-04

- AC: AC-05, AC-06
- Result: PASS — project baseline=`12/12`, gap=`[]`, repeat=`3/3 identical`, GESR/evidence/Product Trace=`12/12`.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-04.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-04.stderr.log`

## EV-05

- AC: AC-06
- Result: PASS — S01-S13=`13/13 PASS`；PayBench=`10/10 PASS`；AP2 minimal flow=`2/2 PASS`；Attack Overlay=`6/6 PASS`.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-05.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-05.stderr.log`

## EV-06

- AC: AC-05, AC-06
- Result: PASS — full unittest=`708/708 PASS`.
- Meta: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-06.meta.json`
- Stdout: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1/evidence/EV-06.stderr.log`

## 9. Scope / Authorization

Workspace snapshot: baseline HEAD=`8a1a484cf70b39c5c610947b1c4efa019bab41bc`; branch=`main`; router=`EXECUTING / Executor`; official source local clone is git-ignored and not a project product change.  
Changed files: F0 changes are task-owned `REPORT.md`, `evidence/*`, and `CURRENT.md` state transition. `PROJECT_BOTTLENECK_MAP.md` and F-stage route/contract are Evaluator/pre-existing task setup, not Executor product implementation. `src/` and `tests/` have no diff against F0 baseline.  
Deviations and unresolved items: no product-scope deviation. One unused auxiliary source-pin checker has string-enum expectations inconsistent with formal VP-01; Executor did not modify it and documented the mismatch above. Formal frozen L2 is fully PASS. Full AP2 constraint semantics and receipts remain intentionally unimplemented and honestly measured as PARTIAL/UNSUPPORTED.

Network use was limited to read-only clone of `https://github.com/google-agentic-commerce/AP2` at tag `v0.2.0`. No dependency installation, Google AI/API call, credential/PII, wallet, payment, testnet, commit, push or history rewrite was performed.

## 10. Executor handoff

```text
F0 official source pin: DONE
12-dimension measurement: DONE
classification: BOUNDED_ADAPTER_GAP
first breakpoint: AP2 official object/evidence → current decoded-snapshot Adapter
product code change: NONE
formal L2 after A1: PASS 6/6
AP2 focused: 17/17 PASS
S01-S13: 13/13 PASS
project baseline: 12/12
full unittest: 708/708 PASS
project impact candidate: NOT_APPLICABLE
product changes: NONE
Executor status: SUBMITTED_FOR_REVIEW
Next owner: Evaluator independent L3
Exactly one suggested next direction: BOUNDED_AP2_ADAPTER_CAPABILITY_PACKAGE
```
