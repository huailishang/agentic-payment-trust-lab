# Evaluator Review

Task ID: `F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: `capability_experiment`
Reviewed baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Active bottleneck: `B-06`
Hypothesis: `H-35`
Task verdict: `PASS`
Project impact verdict: `IMPROVED`
Continuation verdict: `CONTINUE`

## 1. Project context / 项目上下文

A-D 的支付可信主链和 E 的本地代表性真实性能力已经闭合。F0 将 AP2 v0.2.0 的首个外部协议断点定位到 Adapter / external verifier boundary(适配器/外部验证器边界)；F0R/H-34 又把 exact `vct`、checkout hash、payment→checkout binding 三个最上游边界关闭。

因此 F1 不再继续给手写 snapshot 加规则，而是验证更真实的一步：

```text
official AP2 v0.2.0 generated model objects
        ↓
thin SDK Bridge
        ↓
existing H-34 protocol-boundary gate
        ↓
existing adapt_ap2_snapshot
        ↓
Canonical Facts
        ↓
Trust Core
```

本任务只允许一个极薄 SDK Bridge(SDK 桥)，不允许为了 AP2 修改 Canonical Core / Trust Core，也不进入完整 SD-JWT、Receipt、Sandbox 或真实支付。

## Pre-review checks / 评估前检查

Evaluator 未直接采信 Executor 的 L2，先确认：

- Executor `REPORT.md` 状态为 `SUBMITTED_FOR_REVIEW`，L2 `9/9 PASS`；
- F1 三个产品文件 hash 与 REPORT 完全一致；
- F0R `ap2_protocol_boundary.py` 与其测试 hash 保持冻结值；
- official AP2 source 仍固定为 `v0.2.0 / b4587ac1d055888a73b4b21750973cffba961793`；
- dependency gate(依赖门)严格限定在 `.task_envs/f1_ap2_v020/`，实测 `pydantic==2.12.5` 及必要传递依赖；未安装完整 AP2、jwcrypto、sd-jwt、pytest；
- `.task_envs/f1_ap2_v020/pyvenv.cfg` 仅通过 `include-system-site-packages=true` 复用系统已有 `cryptography 41.0.7`；
- 未 commit、未 push、未 history rewrite；
- workflow validator 在进入 L3 前返回 `OK`，`git diff --check` 通过。

复核中还发现并修正了两类 governance wording drift(治理文字漂移)：CURRENT/Contract 中残留的“尚未授权 / DRAFT”旧描述；未改变 H-35、产品实现、AC、allowed scope 或 Validation Plan。

## L3 Independent Gate / L3 独立复核门禁

Evaluator 使用冻结 `VALIDATION_PLAN.yaml` 独立执行 VP-01..VP-09，生成 fresh(新鲜) `RV-EV-01..09`。九份 meta 的 `exit_code` 全部为 `0`。

长命令在控制通道返回前超时，但九项独立检查已经全部完成并落盘；Evaluator 随后按 `run_validation.py` 相同的 gate schema(门禁结构)和判定规则，从这九份 fresh RV-EV meta 机械汇总 `L3-GATE.json/.md`，没有改写任何 observed result(观测结果)。

- Validation plan: `docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/VALIDATION_PLAN.yaml`
- Gate summary: `docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/L3-GATE.json`
- Gate result: PASS
- Checks: `9/9 PASS`
- Mandatory failures: `0`

独立结果：

```text
official SDK source pin                     PASS
pydantic                                    2.12.5
official generated class identities         3/3 PASS
Evaluator-owned SDK cases                   9/9 PASS
F1 focused Bridge tests                    10/10 PASS
H-34 boundary counterexamples              10/10 PASS
existing AP2 regression                    17/17 PASS
project baseline                           12/12 repeat=3
S01-S13                                    13/13 PASS
PayBench                                   10/10 PASS
AP2 minimal                                 2/2 PASS
Attack Overlay                              6/6 PASS
system full unittest                       731 OK, skipped=10
protected Core files                       11/11 unchanged
F0R inherited boundary/test hashes          unchanged
```

系统全量中的 10 个 skip 正是 F1 official SDK focused tests：系统 Python 故意不安装 `pydantic/AP2`，所以这些测试在系统 suite 中 skip；同一 10 个测试已在隔离 SDK 环境中独立 `10/10 PASS`。这符合 AC-07 的 optional dependency(可选依赖)边界。

## RV-EV-01
- AC: AC-08, AC-10
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-01.stderr.log
- Observed result: official AP2 pin 正确；13 个冻结 hash 全部保持；产品变化只位于 F0R 继承文件与 F1 allowed scope。

## RV-EV-02
- AC: AC-01, AC-07
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-02.stderr.log
- Observed result: `pydantic=2.12.5`；三类真实 official generated classes 均从固定 AP2 v0.2.0 source 成功 import。

## RV-EV-03
- AC: AC-02, AC-03, AC-04, AC-05, AC-06
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-03.stderr.log
- Observed result: evaluator-owned S01-S09 `9/9 PASS`；真实官方对象可进入现有 H-34→Canonical 链，dict 冒充、wrong vct、checkout tamper、wrong binding 与缺 context 均 fail closed。

## RV-EV-04
- AC: AC-02, AC-03, AC-04, AC-05, AC-06, AC-07
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-04.stderr.log
- Observed result: F1 focused tests `10/10 PASS`。

## RV-EV-05
- AC: AC-04, AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-05.stderr.log
- Observed result: H-34 B01-B10 `10/10 PASS`，F1 没有削弱前一层 protocol-boundary gate。

## RV-EV-06
- AC: AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-06.stderr.log
- Observed result: existing AP2 regression `17/17 PASS`。

## RV-EV-07
- AC: AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-07.stderr.log
- Observed result: 固定项目 baseline `12/12`，repeat `3/3` 一致，capability gaps 为空。

## RV-EV-08
- AC: AC-09, AC-10
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-08.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-08.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-08.stderr.log
- Observed result: S01-S13 `13/13`、PayBench `10/10`、AP2 minimal `2/2`、Attack Overlay `6/6`。

## RV-EV-09
- AC: AC-07, AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-09.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-09.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/RV-EV-09.stderr.log
- Observed result: system full suite `Ran 731 tests ... OK (skipped=10)`；10 个 skip 与隔离环境中已 `10/10 PASS` 的 official SDK tests 完全对应。

## Acceptance matrix / AC 逐条裁决

| AC | Decision (`通过` / `不通过`) | Executor EV | Independent RV-EV | Specific basis |
|---|---|---|---|---|
| AC-01 | 通过 | EV-01, EV-02 | RV-EV-01, RV-EV-02 | source 固定为 AP2 v0.2.0 / b4587ac1；真实 generated classes 可 import |
| AC-02 | 通过 | EV-03, EV-04 | RV-EV-03, RV-EV-04 | 真实 official class instances → Bridge → H-34 → `VALID / ready=true` |
| AC-03 | 通过 | EV-03, EV-04 | RV-EV-03, RV-EV-04 | plain dict / 非官方对象均在 Bridge fail closed，不生成 Canonical objects |
| AC-04 | 通过 | EV-03, EV-04, EV-05 | RV-EV-03, RV-EV-04, RV-EV-05 | wrong vct / tampered checkout / wrong payment binding 继续由现有 H-34 gate 拒绝；Bridge 未复制安全规则 |
| AC-05 | 通过 | EV-03, EV-04 | RV-EV-03, RV-EV-04 | official Amount 52000 CNY → Canonical 520.00 CNY；Merchant.id 与 transaction_id 映射正确 |
| AC-06 | 通过 | EV-03, EV-04 | RV-EV-03, RV-EV-04 | experiment_context 缺字段或非 Mapping 时不生成半成品 Canonical objects |
| AC-07 | 通过 | EV-02, EV-04, EV-09 | RV-EV-02, RV-EV-04, RV-EV-09 | 产品模块不要求系统安装 AP2/pydantic；official focused tests 在隔离环境 10/10，系统 suite 保持可运行 |
| AC-08 | 通过 | EV-01, EV-05, EV-06, EV-09 | RV-EV-01, RV-EV-05, RV-EV-06, RV-EV-09 | official source、H-34、11 个 protected Core 不变；变化未越出允许产品范围 |
| AC-09 | 通过 | EV-05..09 | RV-EV-05..09 | H-34 10/10、AP2 17/17、baseline 12/12×3、13/13、PayBench 10/10、731 tests zero failures |
| AC-10 | 通过 | EV-01, EV-08, REPORT | RV-EV-01, RV-EV-08, 本 REVIEW | 能力表述严格限定为 local official-generated-types executable slice，不宣称完整 AP2 conformance / crypto / Sandbox / real payment |

## Project impact verdict / 项目影响裁决

Impact verdict: `IMPROVED`

F1 的可测增量是：

```text
Before:
official AP2 generated model objects
→ project boundary executable path = ABSENT

After:
real OpenPaymentMandate / PaymentMandate / CheckoutMandate
→ thin SDK Bridge
→ H-34 verified boundary
→ existing Canonical mapping
→ ready=true
```

并且该增量没有要求 AP2-specific Core branch(AP2 核心特判)：

- Bridge 不 import `pydantic` 或 `ap2`；
- Bridge 不复制 exact-vct / hash / payment-binding 安全规则；
- H-34 与 11 个 protected Core hashes 不变；
- 项目固定 guardrails 全部保持。

因此 H-35 得到支持：**当前 Adapter 架构不仅能处理手写 decoded snapshot，也能接住 AP2 v0.2.0 官方 generated model objects。**

## 6. Bottleneck movement / 瓶颈移动

本任务再次**缩小并前移 B-06**。

之前：

```text
official generated AP2 types
→ 能否进入现有可信边界 = 未验证
→ H-34 gate
→ Canonical Facts
```

现在：

```text
official generated AP2 types
→ thin SDK Bridge【已验证】
→ H-34 gate【已验证】
→ Canonical Facts【已验证】
```

新的第一断点已经不再是“类型能不能接进来”，而是更深的 official protocol verification(官方协议验证)能力：

- checkout JWT issuer signature(发行者签名)；
- open `payment.reference` delegation chain(委托链)；
- `cnf` / KB-SD-JWT holder proof(持有证明)；
- CheckoutReceipt / PaymentReceipt；
- official SDK helper / MandateChain 的真实运行时语义；
- 再往后才是 Sandbox / Provider / wallet / production credential / real payment。

这里仍不能声称 official class identity 是 production provenance(生产来源真实性)证明；F1 证明的是**固定官方 source 下的本地 generated-type interoperability(生成类型互操作性)**。

## 7. Continuation decision / 继续方向

Continuation: `CONTINUE`

下一步优先级应继续沿 B-06 向更真实的 AP2 cryptographic / delegation boundary(密码学/委托边界)推进，而不是再给 SDK Bridge 增加更多类型特判。

更合适的下一包应先做 bounded evaluator-design / measurement(有界评估设计/测量)，明确：

1. official SDK 中哪一个 verifier / helper 是从 generated models 进入真实签名/委托验证的第一个可执行边界；
2. 为该边界最少还需要哪些 pinned dependencies；
3. 哪些能力已经由现有 generic ES256 SignedInstruction verifier 可复用，避免重写；
4. 仍然禁止直接跳到 Sandbox、真实 Provider 或真实资金。

F2 Alipay Agent Pay Sandbox 继续后置，等 AP2 的第一条官方 cryptographic verification slice(密码学验证切片)被测清或明确不值得继续，再决定是否切协议。

下一任务已冻结：

```text
Task ID: H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1
Task kind: evaluator_design
State: CONTRACT_FROZEN / Executor
Path: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/
```

H-36 只做 official verifier/helper、最小依赖与 generic ES256 复用边界测量；不修改产品、不安装依赖、不进入 Sandbox/Provider/真实资金。

## Final verdict

PASS

```text
Task verdict          PASS
Project impact        IMPROVED
Continuation          CONTINUE
L3                    9/9 PASS
Official SDK cases    9/9 PASS
F1 focused tests      10/10 PASS
H-34 boundary         10/10 PASS
Existing AP2          17/17 PASS
Project baseline      12/12 repeat=3
S01-S13               13/13 PASS
PayBench              10/10 PASS
Full unittest         731 OK (10 expected SDK skips)
Core invariance       11/11 unchanged
H-35                  SUPPORTED / CLOSED
B-06                  SHRUNK / MOVED FORWARD
```

本次 Evaluator 未修改产品实现、未新增依赖、未调用 Sandbox/Provider/钱包/真实支付、未使用真实凭证/PII/资金、未 commit、未 push。
