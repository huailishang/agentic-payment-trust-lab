# Evaluator Amendment A1

Task ID: `F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1`
Amendment: `A1 / protocol-field type boundary hardening`
Date: `2026-09-18`

## Why this amendment exists

Evaluator 在 Executor 已开始实现、但尚未提交 `REPORT.md` / L2 最终门禁前做独立复核，发现 H-34 主方向正确、现有 B01-B07 全部通过，但有一个真实 fail-open(错误放行)：

官方 AP2 v0.2.0 schema 明确要求：

```text
checkout_mandate.checkout_jwt  type=string
checkout_mandate.checkout_hash type=string
payment_mandate.transaction_id type=string
```

当前实现会对 `checkout_jwt` 做 `str(...)` 后再 hash，因此下面这个非法对象可以被错误接受：

```text
checkout_jwt = 123        # 非 string，官方 schema 非法
checkout_hash = sha256("123")
transaction_id = same hash
→ current result = VALID / ready=true
```

这是当前冻结三字段边界本身的类型缺口，不是要求完整 schema validator，也不扩大到 SD-JWT / Receipt / SDK。

## A1-01 — Current three fields must be non-empty strings

在原 H-34 三个不变量之前，增加最小类型前置条件：

```text
checkout_mandate.checkout_jwt  must be non-empty str
checkout_mandate.checkout_hash must be non-empty str
payment_mandate.transaction_id must be non-empty str
```

冻结语义：

1. 缺失 / 空字符串继续走既有 `MISSING_EVIDENCE`；
2. 存在但类型不是 `str`，必须 fail closed 为 `INVALID`；
3. 不得用 `str(value)`、JSON dump、repr 或其他隐式转换把非法值转成可 hash / 可比较字符串；
4. 类型失败时不得调用 `adapt_ap2_snapshot`，不得生成 Canonical `IntentMandate / TransactionRequest`。

新增稳定 reason codes：

```text
ap2_checkout_evidence_type_invalid
ap2_payment_checkout_binding_type_invalid
```

其中：

- `checkout_jwt` 或 `checkout_hash` 非字符串 → `ap2_checkout_evidence_type_invalid`
- `transaction_id` 非字符串 → `ap2_payment_checkout_binding_type_invalid`

## A1-02 — Evaluator-owned cases expand B01-B07 → B01-B10

新增三个冻结反例：

| Case | 输入变化 | 期望 |
|---|---|---|
| B08 | `checkout_jwt=123`，并人为给出与 `"123"` 匹配的 hash | `INVALID`，reason=`ap2_checkout_evidence_type_invalid`，无 Canonical 对象 |
| B09 | `checkout_hash` 为非字符串 | `INVALID`，reason=`ap2_checkout_evidence_type_invalid`，无 Canonical 对象 |
| B10 | `transaction_id` 为非字符串 | `INVALID`，reason=`ap2_payment_checkout_binding_type_invalid`，无 Canonical 对象 |

最终 evaluator-owned matrix：

```text
B01-B10 = 10/10 PASS
```

## A1-03 — Scope remains unchanged

本 Amendment **不改变** principal change(唯一主要变化)，仍然只是：

```text
exact vct
+ checkout_jwt → checkout_hash
+ PaymentMandate.transaction_id → verified checkout_hash
```

只是在这三个字段自己的边界上禁止隐式类型转换。

仍不增加：

- 完整 JSON Schema 验证；
- checkout JWT issuer signature；
- SD-JWT / open-to-closed delegation；
- `cnf` / KB-SD-JWT；
- Receipt；
- SDK / Sandbox / Provider / network / wallet / real payment。

Allowed product files 不变，Protected Core 不变，iteration budget 不变。

## A1-04 — Final gate

Executor 下一步：

```text
1. 只修 ap2_protocol_boundary.py 的三字段 type guard
2. 同步 tests/test_ap2_protocol_boundary.py
3. 先跑 evaluator-owned B01-B10
4. 再跑完整冻结 L2 Validation Plan
5. L2 7/7 PASS 后写/补 REPORT.md
6. workflow validator OK
7. SUBMITTED_FOR_REVIEW → Evaluator L3
```

如果修复需要改 `adapters/ap2.py`、Canonical Core 或引入完整 schema/SDK，立即停止交回 Evaluator。

本 Amendment 在 Executor 尚未提交正式 REPORT / 最终 L2 前冻结；属于验收边界补强，不改变 H-34 战略方向。
