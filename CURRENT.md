# Evaluator ↔ Executor Current State

<!-- evaluator-executor-workflow:v2.2 -->

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1
task_kind: evaluator_design
state: CONTRACT_FROZEN
current_role: Executor
baseline_commit: e6931273a983459f167b6e72287a6f05d53a8c26
project_map_path: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
project_map_revision: 2026-09-19-r51
active_bottleneck_id: B-06
hypothesis_id: H-36
contract_path: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/CONTRACT.md
executor_report_path: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/REPORT.md
evaluator_review_path: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/REVIEW.md
next_artifact_path: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/REPORT.md
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
```

## Global position / 全局位置

```text
A-D core payment/trust chain          [CLOSED]
E actor authenticity                 [LOCAL REPRESENTATIVE CLOSURE]
F external protocol / SDK / provider [CURRENT]
  F0 compatibility measurement       [PASS]
  F0R AP2 boundary gate              [PASS / IMPROVED]
  F1 official SDK executable slice   [PASS / IMPROVED]
  H-36 crypto/delegation measurement [CONTRACT_FROZEN / EXECUTOR]
```

## Why H-36 now / 为什么现在做 H-36

F1/H-35 已证明 official generated AP2 types 可以经过 thin SDK Bridge → H-34 → Canonical Facts，且不修改 Trust Core。

当前 B-06 第一断点已经前移到 official cryptographic/delegation verification(官方密码学/委托验证)。H-36 不建设新 verifier，而是先测清：

```text
MandateClient.verify
      ↓
sdjwt.chain.verify_chain
      ↓
root signature / key provider / cnf / KB aud+nonce
      ↓
CheckoutMandateChain / PaymentMandateChain semantics
      ↓
与现有 generic ES256 verifier 的真实复用边界
```

同时单独测量 ReceiptClient.verify_receipt，不把 receipt 路径和 mandate delegation 路径混为一个黑盒。

## H-36 execution boundary / H-36 执行边界

Executor 只允许：

- 读取 pinned AP2 `v0.2.0 / b4587ac1...` source；
- 读取现有 generic ES256 / AP2 adapter 代码和 accepted F0/F0R/F1 evidence；
- 写本任务 `REPORT.md`、`evidence/**`，以及确有必要的 task-local executor helper；
- 最多做 2 个 measurement → L2 cycles。

Executor 不允许：

- 修改 `src/**` / `tests/**`；
- 安装新依赖或扩装现有 `.task_envs`；
- 调用网络 API、Sandbox、Provider、wallet；
- 使用生产 credential、PII 或真实资金；
- 直接实现 H-37；
- commit / push / history rewrite。

## Required decision / 本轮必须形成的决策

H-36 必须最终只给一个分类：

```text
BOUNDED_REUSE_SLICE
AP2_SPECIFIC_CRYPTO_ADAPTER
DEPENDENCY_BLOCKED
NO_JUSTIFIED_NEXT_SLICE
```

目标不是“把 AP2 跑起来”，而是回答：

> 第一条值得编码的 official cryptographic/delegation slice 在哪里，以及它到底能复用现有 Trust 能力到什么程度。

## Next condition / 后续条件

只有 H-36 的 L2 通过并经 Evaluator 独立复核后，才决定：

- 开 H-37 bounded capability experiment；
- 因依赖/授权转 HUMAN_REQUIRED；
- 或停止继续深挖 AP2，重新评估 F2 Alipay Agent Pay Sandbox。

F2/Sandbox、Provider、真实资金不继承任何 H-36 授权。

## Authorization / 权限

本轮 Human 授权的是 Evaluator 完成 H-36 执行包并交给 Executor；Executor 的 commit/push/API/install 权限仍为 false。
