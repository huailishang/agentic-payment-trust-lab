# Frozen Measurement Contract

Task ID: `H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1`
Task name: AP2 v0.2.0 Official Cryptographic / Delegation Boundary Measurement
Task kind: `evaluator_design`
Contract state: `CONTRACT_FROZEN`
Baseline HEAD: `e6931273a983459f167b6e72287a6f05d53a8c26`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-19-r51`
Active bottleneck: `B-06`
Hypothesis: `H-36`
Dispatch mode: `SINGLE`
Validation plan: `docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

## Strategic basis

F1/H-35 已正式 `PASS / IMPROVED / CONTINUE`。已经验证：

```text
official AP2 v0.2.0 generated model objects
        ↓
thin SDK Bridge
        ↓
H-34 protocol-boundary gate
        ↓
existing AP2 adapter
        ↓
Canonical Facts / Trust Core
```

因此 B-06 的第一断点不再是 SDK 对象接入，而是 official cryptographic/delegation verification(官方密码学/委托验证)：官方对象本身是否经过真实签名、持有证明和委托链验证，以及这些能力与项目现有 generic ES256 verifier(通用 ES256 验签器)究竟能复用到什么程度。

本任务坚持 measurement-first(先测量后编码)：**不修改任何产品实现，不安装新依赖，不进入 Sandbox/Provider/真实支付。**

## 2. Official source pin / 官方来源固定

```text
repository  google-agentic-commerce/AP2
tag         v0.2.0
commit      b4587ac1d055888a73b4b21750973cffba961793
source      local_sources/third_party/ap2-v0.2.0
```

本地已确认的官方候选边界包括但不限于：

```text
code/sdk/python/ap2/sdk/mandate.py
  MandateClient.verify(...)
  → ap2.sdk.sdjwt.chain.verify_chain(...)

code/sdk/python/ap2/sdk/checkout_mandate_chain.py
  CheckoutMandateChain.parse(...)
  CheckoutMandateChain.verify(...)

code/sdk/python/ap2/sdk/payment_mandate_chain.py
  PaymentMandateChain.parse(...)
  PaymentMandateChain.verify(...)

code/sdk/python/ap2/sdk/receipt_wrapper.py
  ReceiptClient.verify_receipt(...)
```

Executor 必须从 pinned v0.2.0 source 复核这些事实，不得根据本合同文字直接当作测量结论。

## 3. Single objective / 单一目标

回答一个问题：

> AP2 v0.2.0 从 generated models 继续向前时，**第一条可执行 cryptographic/delegation verification(密码学/委托验证)切片到底在哪里；需要哪些最小依赖；哪些能力可直接复用当前 generic ES256 verifier，哪些必须保留为 AP2-specific protocol glue(AP2 协议特有胶水层)**？

本任务只做定位、依赖分解、复用判定和下一实验设计，不编码 capability。

## 4. Required outputs / 必须输出

### 4.1 Boundary matrix

生成：

`docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/H36_OFFICIAL_BOUNDARY_MATRIX.json`

必须恰好覆盖以下 10 个 measurement surface(测量面)：

1. `mandate_facade_verify`
2. `sdjwt_chain_verify`
3. `root_issuer_signature`
4. `key_provider_and_cnf_delegation`
5. `kb_aud_nonce_holder_proof`
6. `checkout_chain_semantics`
7. `payment_chain_semantics`
8. `receipt_verification`
9. `local_generic_es256_reuse`
10. `first_executable_slice`

每项必须包含：

```json
{
  "surface": "...",
  "status": "OBSERVED|PARTIAL|NOT_PRESENT|BLOCKED_BY_DEPENDENCY",
  "official_evidence": [
    {"path": "source-relative path", "symbol": "exact symbol", "fact": "short factual summary"}
  ],
  "local_evidence": [
    {"path": "repo-relative path", "symbol": "exact symbol", "fact": "short factual summary"}
  ],
  "reuse_classification": "REUSE_DIRECT|REUSE_PRIMITIVE_ONLY|AP2_SPECIFIC_GLUE_REQUIRED|NOT_COMPARABLE",
  "first_executable_boundary": "...",
  "implementation_needed": true,
  "notes": "..."
}
```

`official_evidence` 不得为空。只有 `local_generic_es256_reuse` 和 `first_executable_slice` 可以使用聚合后的多路径证据；其余项必须至少指向一个 AP2 v0.2.0 源码符号。

### 4.2 Minimum dependency set

生成：

`docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/H36_MINIMUM_DEPENDENCIES.json`

至少列出从官方源码静态 import graph(导入关系)观察到的候选依赖，并明确：

```text
package
required_for_surface
source_evidence
already_present
install_required_for_next_experiment
pin_source
notes
```

必须单独判断 `pydantic`、`jwcrypto`、`sd-jwt`/对应 import package、`cryptography`。不得在 H-36 中安装它们。

### 4.3 Next-slice decision

`REPORT.md` 必须给出 exactly one(只能一个)总体分类：

```text
BOUNDED_REUSE_SLICE
AP2_SPECIFIC_CRYPTO_ADAPTER
DEPENDENCY_BLOCKED
NO_JUSTIFIED_NEXT_SLICE
```

并给出 exactly one 下一动作：

- 若存在有界可执行切片：提出一个 H-37 capability experiment(能力实验)候选，明确唯一 principal change(主要改动)；
- 若依赖/环境阻断：列明缺什么和为什么必须 Human 再授权；
- 若信息增益不足：明确 STOP AP2 并建议重新评估 F2，而不是自动进入 Sandbox。

## 5. Measurement questions / 冻结问题

Executor 必须逐项回答：

1. `MandateClient.verify` 到底验证哪些 cryptographic facts(密码学事实)，哪些只是解析？
2. `verify_chain` 如何使用 root key/provider、`cnf`、holder key、KB-JWT、`aud`、`nonce`？
3. `CheckoutMandateChain.verify` / `PaymentMandateChain.verify` 是密码学验证、业务约束验证，还是二者组合？
4. Receipt 路径是否走与 mandate 同一 verifier；若不同，其第一验证边界是什么？
5. 当前 `src/agentic_payment_experiment/trusted_execution/signed_instruction.py` 的 ES256 compact-JWS verifier 能复用：
   - 完整协议语义；
   - 仅底层 ES256 primitive(密码学原语)；
   - 还是基本不可复用？
6. 若下一步只做**第一条官方密码学验证切片**，最少需要哪几个 pinned dependencies；哪些完整 AP2/demo/ADK 依赖明确不需要？
7. 下一能力实验的最小负例应至少覆盖哪些 tamper/binding failure(篡改/绑定失败)？至少考虑 wrong root key、signature tamper、broken delegation/`cnf`、wrong `aud`/`nonce`，但不得在本任务实现。

## 6. Allowed scope / 允许范围

Executor 允许写：

```text
docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/REPORT.md
docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/**
docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/executor_helpers/**   # 仅在确有必要时
```

允许只读：

```text
local_sources/third_party/ap2-v0.2.0/**
src/agentic_payment_experiment/trusted_execution/signed_instruction.py
src/agentic_payment_experiment/adapters/ap2*.py
tests/** existing accepted tests
F0/F0R/F1 accepted CONTRACT/REPORT/REVIEW/evidence
```

Evaluator 已提供的 `evaluator_checks/**`、`CONTRACT.md`、`VALIDATION_PLAN.yaml` 不允许 Executor 修改。

## 7. Frozen exclusions / 明确不做

禁止：

- 修改 `src/**`；
- 修改 `tests/**`；
- 修改 pinned AP2 source；
- 安装或升级任何依赖；
- 创建新的全局/项目 virtualenv；
- 调用 Gemini/Vertex/Google payment API；
- 调用 Sandbox/testnet/Provider/wallet；
- 使用真实 API key、生产 credential、PII、银行卡、真实资金；
- 实现 H-37；
- 为了“跑起来”复制 AP2 verifier 代码到本项目；
- 把“同为 ES256”直接写成 `REUSE_DIRECT`；
- commit、push、history rewrite，除非 Human 后续明确授权。

现有 `.task_envs/f1_ap2_v020/` 只允许只读观察，不得扩装依赖。

## 8. Acceptance criteria / 验收标准

- **AC-01 Source pin**：本地 AP2 source 仍为 `v0.2.0 / b4587ac1...`，上述官方候选文件/符号可从 pinned source 复核。
- **AC-02 Boundary matrix complete**：10 个 surface 恰好全部存在，字段与枚举合法，每项都有 traceable official evidence(可追溯官方证据)。
- **AC-03 Crypto vs semantics separated**：REPORT 明确区分 `MandateClient/verify_chain` 的密码学链验证与 `CheckoutMandateChain/PaymentMandateChain.verify` 的约束/绑定语义，不允许混写为一个黑盒“AP2 verify”。
- **AC-04 Reuse claim bounded**：对现有 generic ES256 verifier 的复用结论必须有源码级对照；只有输入合同、key model、claim/binding semantics 均一致时才允许 `REUSE_DIRECT`，否则必须降为 `REUSE_PRIMITIVE_ONLY` / `AP2_SPECIFIC_GLUE_REQUIRED` / `NOT_COMPARABLE`。
- **AC-05 Dependency set bounded**：最小依赖清单必须从 pinned source import/pyproject 事实推出；H-36 不安装依赖，不把完整 AP2/ADK/demo 依赖默认列为下一实验必需。
- **AC-06 First slice explicit**：必须明确一个 `first_executable_slice`，或者明确 `DEPENDENCY_BLOCKED/NO_JUSTIFIED_NEXT_SLICE`；不得给多个同优先级“大方向”让 Executor 自选。
- **AC-07 Product frozen**：相对 baseline product HEAD `e6931273a983459f167b6e72287a6f05d53a8c26`，`src/**`、`tests/**` 无 H-36 修改；无真实外部副作用。
- **AC-08 Honest report**：不得声称 AP2 conformance、完整 SD-JWT、完整 delegation、Receipt、Sandbox、Provider 或 real payment 已验证；H-36 PASS 只代表测量可信。

## 9. Validation / 验证

Validation plan file: `docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml`

Executor 完成输出后运行冻结 `VALIDATION_PLAN.yaml`。L2 mandatory checks 必须全部 PASS 后才能把 REPORT 标为 `SUBMITTED_FOR_REVIEW`。

本包是 measurement/evaluator-design，不要求新增产品测试。项目 guardrail 只做现有 project baseline smoke，避免把测量包变成全量回归工程。

## 10. Stop conditions / 停止条件

立即停止并交回 Evaluator：

- pinned source tag/commit 不一致；
- 为回答问题必须联网安装/升级依赖；
- 必须修改 `src/**` 或 `tests/**` 才能继续；
- 必须调用 Sandbox/provider/真实 credential；
- 发现官方 source 与当前冻结问题本身冲突，导致 10-surface matrix 无法形成；
- 无法在一次静态测量 + 一次报告修正内形成单一 next-slice decision。

Bounded iteration budget: 最多 `2` 个 measurement → L2 cycles；不允许开放式研究。

## 11. Authorization / 权限

```text
local CPU/read-only source inspection  true
public network                         false
dependency install                     false
external API                           false
sandbox/testnet                        false
credential/PII                         false
real payment                           false
product code change                    false
commit                                 false
push                                   false
history rewrite                        false
```
