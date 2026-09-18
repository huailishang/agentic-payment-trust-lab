# Frozen Capability Contract

Task ID: `F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1`
Task name: AP2 v0.2.0 Bounded Adapter Protocol Boundary Gate
Task kind: `capability_experiment`
Contract state: `CONTRACT_FROZEN`
Baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-18-r47`
Active bottleneck: `B-06`
Hypothesis: `H-34`
Dispatch mode: `SINGLE`
Validation plan file: `docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

F0 `F0_AP2_V020_OFFICIAL_CONTRACT_COMPATIBILITY_MEASUREMENT_V1` 已由 Executor(执行者) L2 `6/6 PASS`，并由 Evaluator(评估者) 使用同一冻结 Validation Plan(验证计划)独立重跑 L3 `6/6 PASS`。

F0 对 AP2 v0.2.0 官方 release `b4587ac1d055888a73b4b21750973cffba961793` 的 12 维测量得到：

```text
SUPPORTED       3
PARTIAL         6
UNSUPPORTED     3
NOT_APPLICABLE  0
```

唯一 gap classification(差距分类)：

```text
BOUNDED_ADAPTER_GAP
```

第一个已证实断点发生在：

```text
AP2 official object / cryptographic-reference evidence
        ↓
current decoded-snapshot Adapter boundary
        ↓
Canonical Facts
        ↓
Trust Core
```

因此本任务不进入完整 F1 official SDK executable slice(官方 SDK 可执行切片)，先实现一个最小 AP2 protocol-boundary gate(协议边界门)，验证 F0 的核心判断：**只修 Adapter(适配器)边界即可关闭第一批真实断点，Canonical Core(规范化核心)无需 AP2 特判。**

## 2. Project impact hypothesis / 项目影响假设

Hypothesis `H-34`：

> 如果 F0 的 `BOUNDED_ADAPTER_GAP` 分类正确，那么只增加一个 AP2 v0.2.0 protocol-boundary verifier(协议边界验证器)，在 Canonical Facts(规范化事实)生成前 fail closed(失败即关闭)校验 exact `vct`、`checkout_jwt → checkout_hash`、`PaymentMandate.transaction_id → verified checkout_hash` 三个不变量，就能让合法对象进入现有 `adapt_ap2_snapshot`，让篡改/错版本/错绑定对象无法生成 Canonical `IntentMandate / TransactionRequest`；且无需修改任何 Canonical Core / Trust Core 规则。

Measurement status: `MEASURED_BASELINE_FROM_F0`
Metric baseline: `F0 exact-vct/hash/payment-binding boundary=ABSENT; project baseline=12/12; full unittest=708/708`

Baseline before H-34：

```text
exact official vct gate                  ABSENT
checkout_jwt -> checkout_hash verify     ABSENT
payment transaction_id -> checkout hash ABSENT
legacy decoded snapshot adapter          PRESENT
Canonical Core AP2-specific branches     0
project baseline                         12/12
full unittest                            708/708
```

Target after H-34：

```text
frozen AP2 boundary cases                7/7 PASS
valid official-boundary case             VALID + canonical adaptation ready
wrong/missing/tampered boundary evidence fail closed
legacy AP2 focused regression             unchanged
Canonical Core protected hashes           unchanged
project baseline                          12/12
full unittest                              zero failures
```

Estimated affected scope: 直接关闭 F0 中 `mandate_schema_version`、`checkout_hash_binding`、`payment_checkout_binding` 的**本任务子断点**；不声称关闭完整 open `payment.reference` delegate chain(委托链)、Receipt(回执)、`cnf`/KB-SD-JWT、完整 signature responsibility(签名责任)或 AP2 conformance(一致性认证)。

Expected project impact: `AP2 frozen boundary cases 0/7→7/7 while Canonical Core protected hashes and 12/12 project baseline remain unchanged`.

Expected material cost: low-to-medium; local CPU only, Python stdlib only, no new dependency, no network/API, no credential/wallet/payment.

Rollback condition: `any protected Core hash change, legacy AP2/project regression, boundary fail-open, dependency/network requirement, or need to widen into SD-JWT/Receipt/SDK`.

Bounded iteration budget: at most `2` complete implementation → L2 cycles. If the second cycle still cannot satisfy the frozen boundary checker without changing protected Core files, stop and return to Evaluator.

## 3. External requirement impact / 外部要求映射

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids:
    - PCAC-06
    - PCAC-07
    - PCAC-09
    - PCAC-12
  applicability: ADAPTER
  maturity_before: M2
  maturity_after: M3
  test_evidence:
    - evaluator-owned AP2 boundary counterexamples
    - AP2 focused regression
    - project baseline repeat=3
  trace_evidence:
    - F0 official compatibility matrix
    - H-34 REPORT AC-to-evidence mapping
  residual_risk:
    - real Provider provenance remains unverified
    - full open-to-closed SD-JWT delegation chain remains unverified
    - checkout JWT issuer signature remains unverified in this package
    - cnf / KB-SD-JWT holder proof remains unverified
    - Receipt signature/reference/reuse semantics remain unimplemented
    - no Sandbox, testnet, production credential, wallet or real payment evidence
```

本任务只能声称工程边界能力提升，不能表述成监管合规、AP2 conformance(一致性认证)或真实支付可用性。

## 4. Single objective / 单一目标

只增加一条 AP2 v0.2.0 verified adapter entry(经边界验证的适配入口)：

```text
decoded AP2 v0.2.0 snapshot
  open_payment_mandate
  payment_mandate
  closed checkout_mandate
        ↓
AP2 protocol-boundary verification
  exact vct
  checkout_jwt raw hash == checkout_hash
  payment_mandate.transaction_id == verified checkout_hash
        ↓ VALID only
existing adapt_ap2_snapshot(...)
        ↓
Canonical IntentMandate / TransactionRequest
```

任何 boundary(边界)失败都不得继续生成 Canonical `IntentMandate` / `TransactionRequest`。

## 5. One principal change / 唯一主要变化

新增一个独立模块：

`src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py`

并从：

`src/agentic_payment_experiment/adapters/__init__.py`

暴露一个稳定入口，语义必须等价于：

```python
adapt_verified_ap2_v020_snapshot(snapshot) -> AP2VerifiedAdaptation
```

本任务不得改写现有 `adapt_ap2_snapshot` 的 legacy decoded-snapshot(旧解码快照)语义；新 verified entry(验证入口)在通过边界门后复用它。

### 5.1 Frozen result contract / 冻结结果合同

`AP2VerifiedAdaptation` 至少必须可机械读取：

```text
boundary_status          VerificationStatus.VALID / INVALID / MISSING_EVIDENCE
reason_codes             tuple[str, ...]
verified_checkout_hash   str | None
mandate                  IntentMandate | None
request                  TransactionRequest | None
missing_fields           tuple[str, ...]
ready                    bool
```

冻结语义：

- `ready == true` 仅当 `boundary_status == VALID` 且 `mandate/request` 均存在；
- `INVALID` 或 `MISSING_EVIDENCE` 时，`mandate is None` 且 `request is None`；
- 不得“先映射 Canonical Facts 再标记 boundary invalid”；
- 不得吞掉错误后回退到旧 snapshot path(快照路径)。

### 5.2 Frozen vct identities / 冻结对象身份

本包只接受 AP2 v0.2.0 官方 exact `vct`：

```text
open_payment_mandate.vct = mandate.payment.open.1
payment_mandate.vct      = mandate.payment.1
checkout_mandate.vct     = mandate.checkout.1
```

错误、未知、未来版本或缺失值全部 fail closed(失败即关闭)。

推荐稳定 reason codes(原因码)：

```text
ap2_open_payment_vct_invalid
ap2_payment_vct_invalid
ap2_checkout_vct_invalid
```

### 5.3 Frozen checkout hash binding / 冻结结账哈希绑定

本包只实现 AP2 v0.2.0 默认 `sha-256` 路径：

```text
expected_checkout_hash =
  base64url_no_padding(
    sha256(UTF8(checkout_mandate.checkout_jwt))
  )
```

必须满足：

```text
checkout_jwt  is non-empty str
checkout_hash is non-empty str
expected_checkout_hash == checkout_mandate.checkout_hash
```

存在但类型不是字符串：

`INVALID / ap2_checkout_evidence_type_invalid`

不得先 `str(...)` 再参与 hash / compare。

缺少 `checkout_jwt` 或 `checkout_hash`：

`MISSING_EVIDENCE / ap2_checkout_evidence_missing`

哈希不一致：

`INVALID / ap2_checkout_hash_mismatch`

本包不实现非默认 `_sd_alg`；如果输入明确要求非 `sha-256` 算法，必须 fail closed 并返回：

`MISSING_EVIDENCE / ap2_checkout_hash_algorithm_unsupported`

不得悄悄退回 `sha-256`。

### 5.4 Frozen payment → checkout binding / 冻结支付到结账绑定

只有 checkout hash 已独立验证后，才检查：

```text
payment_mandate.transaction_id is non-empty str
payment_mandate.transaction_id == verified_checkout_hash
```

存在但类型不是字符串：

`INVALID / ap2_payment_checkout_binding_type_invalid`

不得用 `str(...)` 隐式转换后比较。

不一致：

`INVALID / ap2_payment_checkout_binding_mismatch`

一致后才允许进入现有 Canonical mapping(规范化映射)。

### 5.5 Success reason / 成功原因码

合法边界至少包含：

`ap2_v020_protocol_boundary_verified`

并暴露实际 `verified_checkout_hash`。

## 6. Evaluator-owned frozen cases / 评估者冻结案例

Evaluator checker(评估者检查器)固定验证以下 7 个案例：

| Case | 输入变化 | 期望 |
|---|---|---|
| B01 | 官方 exact vct + 正确 checkout hash + transaction_id 一致 | `VALID`，`ready=true`，Canonical 对象存在 |
| B02 | open payment vct 错误 | `INVALID`，无 Canonical 对象 |
| B03 | closed payment vct 错误 | `INVALID`，无 Canonical 对象 |
| B04 | closed checkout vct 错误 | `INVALID`，无 Canonical 对象 |
| B05 | checkout_jwt 被改、hash 保持旧值 | `INVALID`，无 Canonical 对象 |
| B06 | payment transaction_id 与 verified hash 不一致 | `INVALID`，无 Canonical 对象 |
| B07 | checkout_hash 缺失 | `MISSING_EVIDENCE`，无 Canonical 对象 |
| B08 | checkout_jwt 为非字符串，但人为给出 `str(value)` 对应 hash | `INVALID / ap2_checkout_evidence_type_invalid`，无 Canonical 对象 |
| B09 | checkout_hash 为非字符串 | `INVALID / ap2_checkout_evidence_type_invalid`，无 Canonical 对象 |
| B10 | transaction_id 为非字符串 | `INVALID / ap2_payment_checkout_binding_type_invalid`，无 Canonical 对象 |

最终 evaluator-owned matrix 为 `B01-B10 = 10/10 PASS`。

这些案例不使用真实 JWT 私钥或真实商户数据；`checkout_jwt` 只作为确定性 raw string(原始字符串)做 hash-binding(哈希绑定)验证。

## 7. Allowed scope / 允许范围

Product(产品)：

- `src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py`【新增】
- `src/agentic_payment_experiment/adapters/__init__.py`【只允许导出新 verified entry / result type】

Tests(测试)：

- `tests/test_ap2_protocol_boundary.py`【新增】

Task-owned(任务自有)：

- `docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/REPORT.md`
- `docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/*`

Executor 不得修改 Evaluator-owned(评估者拥有) `evaluator_checks/*`、`CONTRACT.md`、`VALIDATION_PLAN.yaml`。

## 8. Protected / frozen files

以下文件必须保持当前 SHA-256：

```text
src/agentic_payment_experiment/models.py
d38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65

src/agentic_payment_experiment/validator.py
9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb

src/agentic_payment_experiment/trusted_execution/payment_binding.py
139cc77fa57689cd46e9b2716c5877b012d5366e520bab812d8ad121fdcf9e87

src/agentic_payment_experiment/trusted_execution/signed_instruction.py
6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2

src/agentic_payment_experiment/trusted_execution/credential_possession.py
ecea0b6d674d71b92de0cf148be2aff0b158cb11d5f62d5ac61a37d66b38650c

src/agentic_payment_experiment/data_disclosure.py
42fb3ffff4bbb034f9d1fe3840f58931b9281fa4f691b5303eb7ff0775da3d26

src/agentic_payment_experiment/lifecycle.py
8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92

src/agentic_payment_experiment/authoritative_trace.py
f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492

src/agentic_payment_experiment/payment_execution.py
d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49

src/agentic_payment_experiment/adapters/ap2.py
22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867

src/agentic_payment_experiment/adapters/ap2_signed_instruction.py
c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae
```

## 9. Acceptance criteria / 验收标准

### AC-01 — Exact AP2 object identity gate
三个冻结 `vct` 全部 exact match(精确匹配)；任一错误/缺失均 fail closed，且不得生成 Canonical 对象。

### AC-02 — Checkout hash independently verified
`checkout_jwt` 与 `checkout_hash` 必须先确认是非空字符串，再对 `checkout_jwt` raw string(原始字符串)独立计算 hash 并与 `checkout_hash` 比较；不得通过 `str(...)` 隐式转换非法类型。tampered JWT 或字段类型非法必须 `INVALID`。

### AC-03 — Payment is bound to verified checkout
只有在 checkout hash 已验证后，且 `PaymentMandate.transaction_id` 是非空字符串，才可与其比较；非字符串或错绑必须 `INVALID`，不得隐式转换。

### AC-04 — Canonical mapping is downstream of the gate
B01 合法案例 `ready=true` 且生成现有 `IntentMandate / TransactionRequest`；B02-B07 不得生成这两个对象。现有 `adapt_ap2_snapshot` 不修改。

### AC-05 — Evaluator-owned counterexamples
冻结 B01-B10 `10/10 PASS`，包括三项非字符串类型反例；不得按 Case ID 或 fixture literal(固定夹具字面值)特判。

### AC-06 — Core invariance
Protected hashes 全部不变；产品改动只能出现在 Allowed scope(允许范围)。

### AC-07 — Existing AP2 and project guardrails
至少保持：

```text
existing AP2 focused regression  = PASS
S01-S13                           = 13/13 PASS
PayBench                          = 10/10 PASS
project matched                   = 12/12
GESR                              = 12/12
evidence completeness             = 12/12
Product Trace                     = 12/12
callback match                    = 12/12
unsafe allow                      = 0/6
duplicate/forbidden effects       = 0/12
project repeat                    = 3/3 identical
full unittest                     = zero failures
```

### AC-08 — Honest scope attribution
REPORT 必须明确：

- 本包只验证 object identity + checkout hash + closed payment transaction binding；
- 没有验证 checkout JWT issuer signature(发行者签名)；
- 没有验证 open `payment.reference` delegate chain；
- 没有验证 `cnf` / KB-SD-JWT；
- 没有 Receipt ingestion(回执摄取) / receipt-governed reuse(回执治理复用)；
- 没有安装 AP2 SDK，也没有证明 AP2 conformance；
- 没有真实 Provider / Sandbox / wallet / payment。

### AC-09 — v2.2 evidence gate
Frozen Validation Plan(冻结验证计划) L2 全部 mandatory checks(强制检查) PASS；REPORT 映射 AC-01..09，列出 before/after、残余风险、变更文件和零真实副作用。

## 10. Exclusions / 明确不做

- 不安装 AP2 SDK / ADK / Gemini / Vertex 或任何新依赖；
- 不调用 Google API、支付 API 或外部 Provider；
- 不实现完整 SD-JWT verification(验证)；
- 不实现 checkout JWT signature verification(签名验证)；
- 不实现 open `payment.reference` 对 open Checkout delegate chain 的验证；
- 不实现 `cnf` / KB-SD-JWT holder proof(持有证明)；
- 不实现 CheckoutReceipt / PaymentReceipt；
- 不实现 rejection-receipt reuse state machine(拒绝回执复用状态机)；
- 不修改 Canonical Core / Trust Core；
- 不接支付宝 Sandbox、x402 testnet、真实钱包、银行卡、生产凭证、真实 PII 或真实资金；
- 不 commit、push 或 history rewrite，除非 Human/Task Owner 后续明确授权。

## Stop conditions / 停止条件

立即停止并返回 Evaluator：

1. 需要修改任一 Protected file(保护文件)才能让 B01-B07 通过；
2. 发现 AP2 官方 v0.2.0 对默认 checkout hash 算法的事实与本合同冲突；
3. 合法 B01 无法在不改 Core 的情况下形成现有 Canonical 对象；
4. 为通过负例必须引入完整 SD-JWT / Receipt / SDK；
5. 现有 AP2、S01-S13、PayBench、项目 baseline 或 full unittest 出现退化；
6. 超过 `2` 个完整 implementation → L2 cycles。

Continuation rule(继续规则)：

- 若 H-34 `PASS / IMPROVED` 且 Core hashes 不变 → Evaluator 决定是否进入 F1 official SDK executable slice；
- 若合法对象必须修改 Core 才能表达 → `SWITCH` 回 B-06 重新评估 `CORE_SEMANTIC_GAP`；
- 若只是本包未覆盖的 SD-JWT/Receipt/cnf 证据阻塞 → 不扩大本包，记录 residual risk(残余风险)后交回 Evaluator。

## 12. Authorization / 授权

- local CPU: true
- dependency install: false
- network/API: false
- external source refresh: false
- production credential/key: false
- wallet/testnet/sandbox: false
- real PII: false
- real payment: false
- commit: false
- push: false
- history rewrite: false
