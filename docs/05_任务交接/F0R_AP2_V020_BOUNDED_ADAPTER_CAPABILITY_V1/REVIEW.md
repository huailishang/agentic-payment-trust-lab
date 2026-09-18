# Evaluator Review

Task ID: `F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: `capability_experiment`
Reviewed baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Active bottleneck: `B-06`
Hypothesis: `H-34`
Task verdict: `PASS`
Project impact verdict: `IMPROVED`
Continuation verdict: `CONTINUE`

## 1. Project context / 项目上下文

A-E 本地代表性闭环已完成，F0 又把 AP2 v0.2.0 的首个真实断点定位到 Adapter / external verifier boundary(适配器/外部验证器边界)，而不是 Canonical Core(规范化核心)。

H-34/F0R 本轮只处理该断点最上游三个可机械验证不变量：

```text
1. exact AP2 v0.2.0 vct identity
2. sha-256(raw checkout_jwt) == checkout_hash
3. PaymentMandate.transaction_id == verified checkout_hash
```

A1 只补强这三个字段自身的 string type boundary(字符串类型边界)，没有扩大到完整 JSON Schema、SD-JWT、Receipt、SDK 或真实 Provider。

## Pre-review checks / 评估前检查

Evaluator 未直接采信 Executor 的 L2，先确认：

- Executor `REPORT.md` 已提交，状态为 `SUBMITTED_FOR_REVIEW`；
- A1 后 evaluator-owned B01-B10 已在 L2 达到 `10/10 PASS`；
- 产品改动只位于冻结允许的三个路径；
- 11 个 protected Core files(保护核心文件)哈希保持不变；
- 未安装依赖、未访问网络/API、未接 Sandbox/testnet/钱包/真实资金；
- workflow validator(工作流校验器)在进入 L3 前返回 `OK`。

## L3 Independent Gate / L3 独立复核门禁

Evaluator 使用冻结 `VALIDATION_PLAN.yaml` 独立重跑：

- Validation plan: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/VALIDATION_PLAN.yaml
- Gate result: PASS
- Gate summary: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/L3-GATE.json

结果：

```text
Gate                         L3
checks_total                 7
VP-01..VP-07                 PASS
mandatory_failures           0
Evaluator-owned B01-B10      10/10 PASS
targeted boundary tests      13/13 PASS
existing AP2 regression      17/17 PASS
project baseline             12/12, repeat 3/3 identical
S01-S13                      13/13 PASS
PayBench                     10/10 PASS
AP2 minimal flow              2/2 PASS
Attack Overlay                6/6 PASS
full unittest               721/721 PASS
protected Core files         11/11 unchanged
```

此前发现的 fail-open(错误放行)也已独立确认关闭：

```text
checkout_jwt=123        -> INVALID
checkout_hash=123       -> INVALID
transaction_id=123      -> INVALID
```

三类输入均不生成 Canonical 对象，也不会进入旧 `adapt_ap2_snapshot`。

## RV-EV evidence / 独立证据

## RV-EV-01
- AC: AC-06, AC-09
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-01.stderr.log
- Observed result: allowed scope 正确，11 个 protected files 哈希不变。

## RV-EV-02
- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-02.stderr.log
- Observed result: B01-B10 10/10 PASS。

## RV-EV-03
- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-03.stderr.log
- Observed result: targeted boundary tests 13/13 PASS。

## RV-EV-04
- AC: AC-04, AC-07
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-04.stderr.log
- Observed result: existing AP2 regression 17/17 PASS。

## RV-EV-05
- AC: AC-07
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-05.stderr.log
- Observed result: project baseline 12/12，repeat 3/3 identical。

## RV-EV-06
- AC: AC-07, AC-08
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-06.stderr.log
- Observed result: S01-S13 13/13、PayBench 10/10、AP2 minimal 2/2、Attack Overlay 6/6。

## RV-EV-07
- AC: AC-06, AC-07, AC-08, AC-09
- Meta: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/F0R_AP2_V020_BOUNDED_ADAPTER_CAPABILITY_V1/evidence/RV-EV-07.stderr.log
- Observed result: full unittest 721/721 PASS。

## Acceptance matrix / AC 逐条裁决

| AC | Decision (`通过` / `不通过`) | Executor EV | Independent RV-EV | Specific basis |
|---|---|---|---|---|
| AC-01 | 通过 | EV-02, EV-03 | RV-EV-02, RV-EV-03 | exact AP2 v0.2.0 `vct` 在 Canonical mapping 前机械校验 |
| AC-02 | 通过 | EV-02, EV-03 | RV-EV-02, RV-EV-03 | raw `checkout_jwt` 独立 SHA-256/base64url(no padding) 后与 `checkout_hash` 比较 |
| AC-03 | 通过 | EV-02, EV-03 | RV-EV-02, RV-EV-03 | `PaymentMandate.transaction_id` 必须与 independently verified checkout hash 一致 |
| AC-04 | 通过 | EV-02, EV-03, EV-04 | RV-EV-02, RV-EV-03, RV-EV-04 | 只有 protocol boundary(协议边界)为 VALID 才调用原 `adapt_ap2_snapshot` |
| AC-05 | 通过 | EV-02 | RV-EV-02 | Evaluator-owned B01-B10 `10/10 PASS`，错误/缺证/类型非法均 fail closed |
| AC-06 | 通过 | EV-01, EV-07 | RV-EV-01, RV-EV-07 | 11 个 protected Core files 哈希不变，产品变化严格限定在三个 allowed paths |
| AC-07 | 通过 | EV-04, EV-05, EV-06, EV-07 | RV-EV-04, RV-EV-05, RV-EV-06, RV-EV-07 | AP2 17/17、项目 baseline 12/12、S01-S13 13/13、PayBench 10/10、721/721 均保持 |
| AC-08 | 通过 | EV-06 | RV-EV-06, RV-EV-07 | REPORT 与独立复跑都没有扩大到 issuer signature、SD-JWT、Receipt、SDK/Sandbox/真实支付能力 |
| AC-09 | 通过 | EV-01..07 | RV-EV-01..07 | L2 `7/7 PASS`，独立 L3 `7/7 PASS`，证据链完整 |
| A1-01 | 通过 | EV-02, EV-03 | RV-EV-02, RV-EV-03 | 三字段均增加非空 string type guard(字符串类型守门) |
| A1-02 | 通过 | EV-02 | RV-EV-02 | B01-B10 `10/10 PASS` |
| A1-03 | 通过 | EV-01 | RV-EV-01 | principal change(唯一主要变化)和 allowed scope 未扩大 |
| A1-04 | 通过 | L2-GATE | L3-GATE | 最终 L2/L3 均全绿 |

## Project impact verdict / 项目影响裁决

Impact verdict: `IMPROVED`

原因：

1. F0 时 exact vct、checkout hash verification、payment→checkout verified binding 均为未实现的真实 Adapter gap；
2. F0R 后这三个边界已形成可执行 gate(守门能力)，Evaluator 独立反例 `10/10`；
3. 非法、篡改、缺失、类型错误输入均在 Canonical mapping 前 fail closed；
4. Canonical Core / Trust Core 没有 AP2-specific branch(AP2 特判分支)；
5. 项目固定 guardrails(守护线)全部保持，721/721 全量无失败。

因此 H-34 的核心假设得到支持：F0 暴露的这部分差距确实可以在 Adapter boundary(适配器边界)有界关闭，不需要为了 AP2 改写核心支付语义。

## 6. Bottleneck movement / 瓶颈移动

本任务**缩小了 B-06**。

之前：

```text
official AP2 object
→ exact vct / checkout hash / payment→checkout binding 未验证
→ decoded snapshot adapter
→ Canonical Facts
```

现在：

```text
official AP2 object
→ bounded protocol-boundary gate【已验证】
→ existing decoded snapshot adapter
→ Canonical Facts
```

第一瓶颈因此前移到更真实的一层：**official SDK/types / official executable integration(官方 SDK/类型与可执行接入)**。

仍未解决：

- checkout JWT issuer signature(发行者签名)；
- open `payment.reference` delegate chain(委托链)；
- `cnf` / KB-SD-JWT holder proof(持有证明)；
- CheckoutReceipt / PaymentReceipt；
- rejection-receipt reuse state(拒绝回执复用状态)；
- AP2 official SDK / runtime types；
- Sandbox / Provider / wallet / production credential / real payment。

## 7. Continuation decision / 继续方向

Continuation: `CONTINUE`

下一优先方向是 F1 official SDK executable slice(官方 SDK 可执行切片)，原因是：

- F0 已证明 gap 位于 Adapter/external boundary；
- F0R 已关闭最上游三个机械边界；
- 继续在本地手写 snapshot 上叠更多规则的信息增益开始下降；
- 下一步更有价值的是让**官方 AP2 types / sample objects 真正经过现有边界和 Canonical mapping**，检查是否出现新的协议对象/运行时断点。

但 F1 必须单独冻结新合同；SDK/依赖安装、外部网络、Sandbox、Provider 与真实资金不能沿用本包授权。

## Final verdict

PASS

```text
Task verdict        PASS
Project impact      IMPROVED
Continuation        CONTINUE
L3                  7/7 PASS
B01-B10             10/10 PASS
full unittest       721/721 PASS
Core invariance     11/11 unchanged
B-06                SHRUNK / MOVED FORWARD
Next direction      F1 official SDK executable slice
```

本次 Evaluator 未修改产品实现、未安装依赖、未调用外部网络/API、未接 Sandbox/钱包、未使用真实凭证/PII/资金、未 commit、未 push。
