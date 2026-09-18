# Frozen Capability Contract

Task ID: `F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1`
Task name: AP2 v0.2.0 Official SDK Executable Slice
Task kind: `capability_experiment`
Contract state: `CONTRACT_FROZEN`
Baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-18-r49`
Active bottleneck: `B-06`
Hypothesis: `H-35`
Dispatch mode: `SINGLE`
Validation plan file: `docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-34/F0R 已正式 `PASS / IMPROVED / CONTINUE`：L3 `7/7`、B01-B10 `10/10`、721/721、11 个 protected Core hashes 不变。B-06 的第一断点已经从 decoded snapshot 的协议边界前移到 official SDK/types executable integration(官方 SDK/类型可执行接入)。

目标链：

```text
official AP2 Python generated objects
        ↓
SDK Bridge
        ↓
existing H-34 protocol-boundary gate
        ↓
existing adapt_ap2_snapshot
        ↓
Canonical Facts → Trust Core
```

## 2. Project impact hypothesis / 项目影响假设

**H-35**：如果 H-34 的边界设计正确，那么只增加一个极薄 SDK Bridge(SDK 桥)，将 AP2 v0.2.0 官方 `OpenPaymentMandate / PaymentMandate / CheckoutMandate` 通过官方 `model_dump(...)` 转成现有 snapshot 结构，就能直接复用 `adapt_verified_ap2_v020_snapshot` 并进入 Canonical Facts；不需要修改 Canonical Core / Trust Core，也不需要完整 SD-JWT / cryptography runtime。

Metric baseline: `official generated SDK objects executable through project boundary = ABSENT; H-34 boundary=10/10; project baseline=12/12; full unittest=721/721`.

Target: official generated objects 可实例化并通过 bridge；evaluator-owned SDK cases `9/9 PASS`；H-34 `10/10` 保持；Core hashes 不变；project baseline `12/12 repeat=3`；full unittest zero failures。

Expected project impact: `official SDK generated types: ABSENT → EXECUTABLE_LOCAL_SLICE`.

Estimated affected scope: `src/agentic_payment_experiment/adapters/ap2_sdk_bridge.py`, `src/agentic_payment_experiment/adapters/__init__.py`, `tests/test_ap2_sdk_bridge.py`, plus task-owned evidence/report and `.task_envs/f1_ap2_v020/` only.

## 3. Official source pin / 官方来源固定

```text
repo    google-agentic-commerce/AP2
tag     v0.2.0
commit  b4587ac1d055888a73b4b21750973cffba961793
path    local_sources/third_party/ap2-v0.2.0
sdk     code/sdk/python/ap2/sdk/generated
```

必须真实实例化官方 generated classes，不得复制类到项目里冒充官方 SDK。

## 4. Dependency gate / 依赖门

当前系统 Python 3.12.3 实测：`pydantic MISSING`；`cryptography 41.0.7 PRESENT`；`jwcrypto / sd_jwt / pytest MISSING`。本切片逐文件检查只需要官方 pin 的 `pydantic==2.12.5`；完整 AP2 依赖不需要。

Human 已于 2026-09-18 明确批准：仅在 `.task_envs/f1_ap2_v020/` 隔离环境安装 `pydantic==2.12.5` 及其必要传递依赖；不得全局安装或扩大到完整 AP2 依赖。因此本合同的 dependency gate(依赖门)已满足并进入 `CONTRACT_FROZEN`。

Human 批准后的安装边界固定为任务隔离环境：

```text
.task_envs/f1_ap2_v020/
```

只允许 `pydantic==2.12.5` 及 resolver 自动带入的传递依赖；禁止全局安装、禁止 `pip install .` 安装完整 AP2、禁止顺带安装 jwcrypto/sd-jwt/pytest/Gemini/Vertex/ADK。

## 5. Single objective / 单一目标

新增 `src/agentic_payment_experiment/adapters/ap2_sdk_bridge.py`，稳定入口语义：

```python
adapt_verified_ap2_v020_sdk_objects(
    open_payment_mandate,
    payment_mandate,
    checkout_mandate,
    *,
    experiment_context,
) -> AP2VerifiedAdaptation
```

Bridge 只做：官方 class identity 校验 → `model_dump(mode="python", exclude_none=True)` → 构造 snapshot → 调用现有 `adapt_verified_ap2_v020_snapshot(...)`。不得复制 vct/hash/payment-binding 逻辑。

产品代码不得 import `pydantic` 或 `ap2`；官方 SDK 保持 optional dependency(可选依赖)。

## 6. Exact accepted class identity

只接受：

```text
ap2.sdk.generated.open_payment_mandate.OpenPaymentMandate
ap2.sdk.generated.payment_mandate.PaymentMandate
ap2.sdk.generated.checkout_mandate.CheckoutMandate
```

plain dict、fake BaseModel、同名不同 module 对象不得作为官方 SDK 对象放行。建议 reason codes：`ap2_sdk_open_payment_object_invalid`、`ap2_sdk_payment_object_invalid`、`ap2_sdk_checkout_object_invalid`、`ap2_sdk_model_dump_invalid`、`ap2_sdk_experiment_context_invalid`。

禁止 `dict(obj)`、`vars(obj)`、`repr`、JSON round-trip fallback；dump 结果必须是 Mapping。

## 7. Allowed product scope / 允许产品改动

```text
src/agentic_payment_experiment/adapters/ap2_sdk_bridge.py
src/agentic_payment_experiment/adapters/__init__.py
tests/test_ap2_sdk_bridge.py
```

F0R 已有实现必须继承且冻结：

```text
src/agentic_payment_experiment/adapters/ap2_protocol_boundary.py
  fae40678a356ecad4bd0cf5998476071499ab2c180c846f32ca75f3fb479d9ae
tests/test_ap2_protocol_boundary.py
  084439ff194656ec149d2c1bfcbecb8ca6ef5f16ec8b0df7c6f41a24ca65aed7
```

`adapters/__init__.py` 只允许追加 F1 export，不得删除 F0R export。

## 8. Protected Core / 保护核心

冻结以下哈希：

```text
models.py d38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65
validator.py 9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb
payment_binding.py 139cc77fa57689cd46e9b2716c5877b012d5366e520bab812d8ad121fdcf9e87
signed_instruction.py 6324a5912f1329b11abddb01a619a8088966ab562ef9f79ccad19b2d02d8c5a2
credential_possession.py ecea0b6d674d71b92de0cf148be2aff0b158cb11d5f62d5ac61a37d66b38650c
data_disclosure.py 42fb3ffff4bbb034f9d1fe3840f58931b9281fa4f691b5303eb7ff0775da3d26
lifecycle.py 8fc6df6f56d5aad47cc9c449340307324150f12760f0a124bd32296a659a4c92
authoritative_trace.py f1d06b9d0654f0a34954104b62b8555fe91e2b80fc34a0d4049d093928feb492
payment_execution.py d161be5afe73192491e20203651dc3b222fa37454235c1bacc37042c6254fb49
adapters/ap2.py 22325219bdcd02c69bedd26831608d3fe1752b0cc43e1e34a0442ff3a698b867
adapters/ap2_signed_instruction.py c0fad26bbeb44034a276d8bb491146a2d5cded3ae130baa611c77e341baa91ae
```

## 9. Evaluator-owned frozen cases / 评估者冻结案例

```text
S01 official three generated objects → VALID / ready=true
S02 plain dict as OpenPaymentMandate → INVALID / no Canonical
S03 plain dict as PaymentMandate → INVALID / no Canonical
S04 plain dict as CheckoutMandate → INVALID / no Canonical
S05 official CheckoutMandate wrong vct → existing H-34 rejects
S06 official CheckoutMandate tampered checkout_jwt / stale hash → existing H-34 rejects
S07 official PaymentMandate transaction_id mismatch → existing H-34 rejects
S08 official Amount.amount + Merchant.id → Canonical 520.00 CNY / merchant id
S09 missing required experiment_context → MISSING_EVIDENCE / no Canonical
```

目标 `9/9 PASS`。

## 10. Acceptance criteria / 验收标准

- **AC-01** source pin 仍为 `v0.2.0 / b4587ac1...`，官方三个 generated classes 可真实 import。
- **AC-02** S01 必须使用真实官方 class instance，返回 `VALID / ready=true`。
- **AC-03** S02-S04 非官方对象必须 fail closed，无 Canonical objects。
- **AC-04** S05-S07 仍由现有 H-34 boundary 拒绝，Bridge 不复制安全逻辑。
- **AC-05** 官方 `Amount.amount=52000/CNY` 映射为 Canonical `520.00 CNY`，Merchant.id、transaction_id、时间沿用现有 adapter 语义。
- **AC-06** experiment_context 缺关键字段时不得生成半成品 Canonical objects。
- **AC-07** 产品模块不得 import `pydantic/ap2`；系统 Python 无 pydantic 时主项目 import/原测试仍运行；官方 SDK focused tests 只在隔离环境执行。
- **AC-08** official source、H-34 boundary、11 个 protected Core 不变；产品变化仅 allowed scope。
- **AC-09** H-34 10/10、existing AP2 regression、project baseline 12/12 repeat=3、S01-S13、PayBench、full unittest zero failures。
- **AC-10** REPORT 明确这是 local official-generated-types executable slice，不是完整 AP2 conformance；不包含 issuer verification/delegation/cnf/Receipt/Sandbox/Provider/real payment。

## 11. Frozen exclusions / 明确不做

不做 MandateChain/full SDK helper、jwcrypto、sd-jwt、issuer signature、open payment.reference delegation、cnf/KB-SD-JWT、Receipt、SDK network calls、Gemini/Vertex/ADK、Sandbox/testnet、Provider/wallet/production credential、真实 PII/资金、Canonical/Trust Core 改动、commit/push/history rewrite（除非另行明确授权）。

## 12. Validation / 验证

Validation Plan: `docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/VALIDATION_PLAN.yaml`；完整 L2 目标 `9/9 PASS`。Executor L2 PASS 后写 `REPORT.md`，映射 AC-01..AC-10。

## 13. Stop conditions / 停止条件

Rollback condition: 任一以下 stop condition 成立，或 bounded iteration budget 用尽后仍有 mandatory L2 failure，则停止 F1 并交回 Evaluator，不得扩围。

立即停止并交回 Evaluator：未授权却需要联网安装；需要 pydantic 之外的新直接依赖；需要改 `ap2_protocol_boundary.py` / protected Core / official source；需要复制 H-34 逻辑；需要完整 SD-JWT/signature/Receipt 才能通过；第二个完整 implementation→L2 cycle 仍失败。

Bounded iteration budget: `2` complete implementation → L2 cycles。

## 14. Freeze condition / 冻结条件

该冻结条件已于 2026-09-18 满足：Human 明确批准仅在 `.task_envs/f1_ap2_v020/` 隔离安装 `pydantic==2.12.5` 及必要传递依赖。H-35、principal change、AC、allowed scope 与 Validation Plan 均保持不变。
