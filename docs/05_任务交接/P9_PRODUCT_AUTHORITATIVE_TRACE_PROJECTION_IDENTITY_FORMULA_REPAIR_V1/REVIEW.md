# Evaluator Review

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-PROJECTION-IDENTITY-FORMULA-REPAIR-V1`  
Parent task: `P9-PRODUCT-AUTHORITATIVE-TRACE-REFERENCE-MODEL-GROUNDING-REPAIR-V1`  
Contract baseline HEAD: `979ffc505bec0b626858d0d186f655867b5491bf`  
Live reviewed HEAD: `b4eff597ebffe79c575522b91642f82b26ad5247`

```yaml
workflow: evaluator-executor-workflow/v2.1
task_kind: repair
task_verdict: PASS
project_impact_verdict: NOT_APPLICABLE
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-08-04-r5
active_bottleneck_id: B-03
hypothesis_id: H-03
commit_performed_by_task: false
push_performed_by_task: false
concurrent_commit_accepted: true
```

## 1. 裁决

本轮修复通过。

```text
Evaluator independent checks: 181/181 PASS
Blocking findings: 0
Task verdict: PASS
Project impact verdict: NOT_APPLICABLE
```

父任务唯一剩余缺口已经关闭：`PROJECTION_HASH_IDENTITY` 不再只是一个模式名，而是具备权威、机器可读、可独立重算的完整公式。

```text
权威设计
→ PROJECTION_HASH_IDENTITY_V1
→ 9 个 registry entry 使用相同参数
→ 独立重算 source_object_ref
→ 再独立重算 binding_ref
→ T10 / T12 固定值保持不变
```

B-03 仍是第一瓶颈，H-03 未被否定；项目地图保持 `2026-08-04-r5`。

## 2. 独立复核证据

### RV-EV-01 — Projection Identity 独立重算

- Script: `evidence/RV-EV-01-independent-formula-review.py`
- Meta: `evidence/RV-EV-01.meta.json`
- Stdout: `evidence/RV-EV-01.stdout.log`
- Stderr: `evidence/RV-EV-01.stderr.log`
- Result: `181/181 PASS`

初次复核为 `158/159`，唯一失败是复核期间仓库 HEAD 发生变化。原始证据保留为：

- `evidence/RV-EV-01-initial.meta.json`
- `evidence/RV-EV-01-initial.stdout.log`
- `evidence/RV-EV-01-initial.stderr.log`

该 HEAD 变化经独立审计确认不是本执行包产生：

```text
commit = b4eff597ebffe79c575522b91642f82b26ad5247
subject = docs: add shared CodexPro shell safety rules
changed files = AGENTS.md only
commit time = Executor REPORT / EV-04 之后
EV-04 submission snapshot 已记录 ?? AGENTS.md
```

因此它属于提交后的并发公共规则提交，不计为执行者擅自 commit/push。下一任务使用实时 HEAD `b4eff597...` 作为基线。

同时复核了 EV-04 中的执行者产物哈希：

```text
22/22 非路由产物保持完全一致
CURRENT.md 仅因 Evaluator 接管由 EXECUTING 切为 READY_FOR_REVIEW
```

## 3. 公式复核

权威公式已经冻结：

```text
formula_id = PROJECTION_HASH_IDENTITY_V1

payload = {
  projection_schema,
  projection
}

payload_bytes = UTF-8 canonical JSON
- sort_keys = true
- separators = (",", ":")
- ensure_ascii = false
- allow_nan = false

digest = SHA-256 lowercase-hex-64

source_object_ref =
  <source_object_type>
  + ":projection-sha256:"
  + digest
```

边界明确：

- `source_object_type` 进入固定前缀，不进入 hash payload；
- `projection_schema` 与 exact projection 都进入 payload；
- payload 不包含 `binding_ref` 或 `source_object_ref`；
- source identity hash 与 full-binding digest 是两个独立公式；
- float、NaN、Infinity fail closed；
- 当前只证明 envelope 内部一致性，不宣称签名或外部真实性。

## 4. Registry 与固定值

独立确认 9 个 hash identity schema 使用完全相同的机器参数：

```text
governed-action-binding-fact-trace/v2
governed-payment-action-missing-id-trace/v2
known-payment-attempt-preflight-fact-trace/v2
payment-recovery-result-trace/v2
payment-status-conflict-fact-trace/v2
runtime-gate-record-trace/v2
validation-result-trace/v2
webshop-buy-now-gate-outcome-result-trace/v2
webshop-payment-fulfilment-outcome-result-trace/v2
```

同时确认：

- 16 个 registry schema 名称与父任务完全相同；
- 9 个 hash schema 只增加 identity formula 参数，其他字段未变；
- 7 个 native schema 完全未变；
- T01—T12 profile、事件、关系和 projection 定义未变；
- 7 个父任务持久化 concrete vector 均能独立重算；
- 另外 2 个 schema 被明确标记为 derived conformance vector，没有冒充父固定事实。

## 5. T10 / T12 回归

T10：

```text
12 events = unchanged
11 unique bindings = unchanged
两个 Order role 共享同一个 binding = unchanged
所有 source_object_ref = unchanged
所有 binding_ref = unchanged
所有 relation target = resolved
```

T12：

```text
PaymentStatusConflictFact source/binding refs = unchanged
WebShopPaymentFulfilmentOutcome source/binding refs = unchanged
sidecar decision extraction = null
```

父固定 JSON 哈希全部未变。

## 6. 负例矩阵

以下边界均由 Evaluator 独立验证或核对 exact verdict：

- 缺少 `projection_schema`；
- payload 只有 projection；
- schema 字符串变化；
- projection 字段变化；
- source type / prefix 变化；
- prefix 大小写变化；
- digest 大写或非 64 hex；
- float / NaN / Infinity；
- payload 加入 `source_object_ref`；
- 使用父 EV builder 作为 resolver。

所有反例均 fail closed、产生 ref mismatch 或得到明确 `INVALID / FORBIDDEN`，没有模糊回退。

## 7. AC 裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 唯一公式 | 通过 | 设计文档完整冻结 prefix、payload、canonical JSON、hash、encoding 和边界 |
| AC-02 registry 可执行 | 通过 | 9 个 entry 参数完全一致，native entries 不变 |
| AC-03 固定正例不变 | 通过 | 7 个父固定 + 2 个透明 conformance vector 全部重算；T10/T12 父值不变 |
| AC-04 负例矩阵 | 通过 | 13 个 case 具有 exact verdict，关键变体由 Evaluator 独立重算 |
| AC-05 Measurement Adapter 同步 | 通过 | adapter 明确 native/hash 两条路径、envelope-only resolver、identity/binding 分层 |
| AC-06 NEXT_SLICE 条件状态 | 通过 | 仍为 `CONDITIONAL_NOT_FROZEN`，hash 均为 `TBD_AFTER_ADAPTER_ACCEPTANCE` |
| AC-07 独立规格充分性 | 通过 | Evaluator 不读取父 builder，按权威设计/registry 重算成功 |
| AC-08 报告与父 finding closure | 通过 | F-01、正反例、固定值、范围、差异和限制均有证据 |
| AC-09 范围与工作流 | 通过 | 产品代码/测试/runner 未改，无产品 trace producer，无外部副作用 |

## 8. 项目影响

```text
Project impact verdict: NOT_APPLICABLE
```

本任务是设计 repair，没有实现测量适配或产品轨迹：

```text
product-observed authoritative trace: 0/12 → 0/12
GESR: 0/12 → 0/12
```

不能宣称项目能力改善。它只消除了下一阶段实现时的规格歧义。

## 9. 下一步基线

Evaluator 使用当前旧 runner 重新运行 T01—T12，冻结 Measurement Adapter 的进入基线：

```text
live baseline HEAD
= b4eff597ebffe79c575522b91642f82b26ad5247

old runner SHA-256
= a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4

baseline fixture SHA-256
= 4ed2e1f35325cb840de834f5e8c964ff187c291133c958a2ee22111735b615f5

target fixture SHA-256
= f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee

old runner output SHA-256
= 58f27a115c2be350fbedcdf31c1453c8e82df6ed2fa8d180fca923bc1a36e852

non-trace business projection SHA-256
= 6eb5bca0c0aba10ac75eff3cf5d12ceed015b71d974d685dfa96b7e91e9099dc

repeatability normalized SHA-256
= 4dfc7743909374689ec7b437b3a1b774d4d2e1155e287f3f8dc23430498b7044
```

当前测量：

```text
product trace = 0/12
GESR = 0/12
callback match = 12/12
duplicate/forbidden side effect = 0/12
decision-reason consistency = 11/12
full unittest = 451/451 PASS
```

## 10. Continuation action

下一任务：

```text
P9-PRODUCT-AUTHORITATIVE-TRACE-MEASUREMENT-ADAPTER-V1
```

任务类型：`maintenance`。

目标只改测量层：

1. 实现纯 `ProductAuthoritativeTrace` 数据合同和严格 validator；
2. runner 只读取 `outcome.authoritative_trace`；
3. 产品没有 trace 时继续返回 `NOT_AVAILABLE`；
4. evaluator replay 不能回退成产品 trace；
5. 支持 `NATIVE_TEMPLATE` 与 `PROJECTION_HASH_IDENTITY_V1`；
6. 严格校验 binding、entity、relation 和 exact profile；
7. 产品 outcome 仍不产出 trace，重新冻结可信的 `0/12 BEFORE`；
8. 冻结 accepted runner、target、BEFORE 和 non-trace projection hash。

通过 Measurement Adapter 后，才允许把条件 T10 slice 冻结为 capability experiment。

## 11. Authorization

- commit: false
- push: false
- history rewrite: false
- network/API/download: false
- dependency/environment: false
- WebShop/Buy Now/payment/order side effect: false
