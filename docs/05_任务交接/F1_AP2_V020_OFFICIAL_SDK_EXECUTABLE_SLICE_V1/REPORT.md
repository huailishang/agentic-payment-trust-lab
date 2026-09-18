# Executor Report

Task ID: `F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1`
Executor status: SUBMITTED_FOR_REVIEW
Task kind: `capability_experiment`
Baseline HEAD: `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`
Project map revision: `2026-09-18-r49`
Active bottleneck: `B-06`
Hypothesis: `H-35`
Implementation commit: `NONE`（authorization_commit=false）

## Execution conclusion / 执行结论

Human 已明确批准只在 `.task_envs/f1_ap2_v020/` 中隔离安装 `pydantic==2.12.5` 及其必要传递依赖。Contract 随后按既定 freeze condition(冻结条件)从 `DRAFT_CONTRACT` 切为 `CONTRACT_FROZEN`，CURRENT 路由到 Executor。

F1 principal change(唯一主要变化)已完成：新增极薄 `ap2_sdk_bridge.py`，只做：

```text
exact official loaded class identity
→ model_dump(mode="python", exclude_none=True)
→ build existing snapshot shape
→ delegate to adapt_verified_ap2_v020_snapshot(...)
```

Bridge 不复制 exact-vct / checkout-hash / payment→checkout binding 规则，不修改 H-34 boundary，不修改 Canonical Core / Trust Core。

Evaluator-owned official SDK cases：`S01-S09 = 9/9 PASS`。
F1 focused unit tests：`10/10 PASS`（隔离 SDK 环境）。
最终 L2：`9/9 PASS`，mandatory failures=`0`。

## Workspace snapshot / 工作区快照

- HEAD 仍为冻结 baseline `0a9b74873e9aedbc3d1c2e4e37b24e9129bf20ef`。
- Official AP2 local source pin 仍为 `b4587ac1d055888a73b4b21750973cffba961793`。
- F0R inherited files(继承文件)保持冻结 hash。
- 11 个 protected Core files(保护核心文件)保持冻结 hash。
- `.task_envs/f1_ap2_v020/` 当前约 `24M`。
- 安装：`pydantic==2.12.5`、`pydantic-core==2.41.5`、`annotated-types`、`typing-extensions`、`typing-inspection`。
- `cryptography 41.0.7` 未重新安装；任务 venv 通过 `--system-site-packages` 读取系统已有版本。
- 未安装完整 AP2、jwcrypto、sd-jwt、pytest、Gemini、Vertex、ADK。
- 未调用 Sandbox/testnet/Provider/wallet/真实支付；未使用真实凭证/PII/资金。
- 未 commit、未 push、未 history rewrite。

## Changed files / 改动文件

F1 新增/修改的产品文件：

| File | Action | SHA-256 | F1 作用 |
|---|---|---|---|
| `src/agentic_payment_experiment/adapters/ap2_sdk_bridge.py` | new | `c861699db59cf9dc8a3f99011a2d23c70ffeab01e9c87552daa9ff5e8064e1bd` | exact official class identity + model_dump + delegate |
| `src/agentic_payment_experiment/adapters/__init__.py` | modified | `f3e2ec69f84b5ed4aa98f97179b7fee87365bf54e8ca9dfa063559be71db6c0c` | 追加 F1 bridge export；保留 F0R exports |
| `tests/test_ap2_sdk_bridge.py` | new | `6cafc0b4c46d817d7764e5726f4d5057ca04315eec39e69096d3f8dd4ff80148` | official SDK Bridge focused tests |

Task-owned artifacts：`CURRENT.md`、本 `REPORT.md`、`evidence/*`、任务隔离环境。

Source-scope audit(源码范围审计)看到的其他 `ap2_protocol_boundary.py` / `test_ap2_protocol_boundary.py` 是上一任务 F0R 的未提交继承改动；F1 对其 hash 零变化。

## Dependency/environment result / 依赖与环境结果

首次定向运行时，任务 venv 虽已装好 `pydantic`，但没有看到系统已有 `cryptography 41.0.7`，导致主项目 import 失败。没有扩大依赖安装范围，而是将任务 venv 切为 `--system-site-packages`，复用系统已存在的 cryptography。

最终 official SDK preflight(官方 SDK 预检)：

```text
pydantic = 2.12.5
OpenPaymentMandate = ap2.sdk.generated.open_payment_mandate.OpenPaymentMandate
PaymentMandate     = ap2.sdk.generated.payment_mandate.PaymentMandate
CheckoutMandate    = ap2.sdk.generated.checkout_mandate.CheckoutMandate
result             = PASS
```

产品模块自身不 import `pydantic` 或 `ap2`，官方 SDK 仍是 optional dependency(可选依赖)。

## Official SDK behavior / 官方对象行为

Evaluator-owned S01-S09：

| Case | Result |
|---|---|
| S01 official three generated objects | VALID / ready=true |
| S02 dict as OpenPaymentMandate | INVALID / no Canonical |
| S03 dict as PaymentMandate | INVALID / no Canonical |
| S04 dict as CheckoutMandate | INVALID / no Canonical |
| S05 wrong checkout vct | existing H-34 rejects |
| S06 tampered checkout_jwt / stale hash | existing H-34 rejects |
| S07 transaction_id mismatch | existing H-34 rejects |
| S08 Amount.amount + Merchant.id | Canonical 520.00 CNY / merchant-boundary |
| S09 missing context.category | MISSING_EVIDENCE / no Canonical |

结果：`9/9 PASS`。

Class identity 使用“对象实际 class + 已加载官方 module 中同一 class object”判断；不是只比字符串类名。因此 plain dict、同名不同 module 对象不能冒充官方 generated object。

## L2 Task Gate

- Validation plan: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/VALIDATION_PLAN.yaml
- Gate summary: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/L2-GATE.json
- Gate result: PASS

| VP | Result | Observed |
|---|---|---|
| VP-01 | PASS | source scope + official source + inherited H-34/Core hashes |
| VP-02 | PASS | pydantic 2.12.5 + exact official classes |
| VP-03 | PASS | evaluator-owned S01-S09 9/9 |
| VP-04 | PASS | F1 focused tests 10/10 |
| VP-05 | PASS | H-34 B01-B10 10/10 |
| VP-06 | PASS | existing AP2 regression 17/17 |
| VP-07 | PASS | project baseline 12/12, repeat 3/3 identical |
| VP-08 | PASS | S01-S13 13/13; PayBench 10/10; AP2 minimal 2/2; Attack Overlay 6/6 |
| VP-09 | PASS | system full unittest: Ran 731, OK, skipped=10 |

VP-09 的 10 个 skip 是本任务新增的 official SDK focused tests：系统 Python 故意不安装 pydantic/AP2，所以按 AC-07 在系统 full suite 中 skip；同一 10 个测试已在 VP-04 的隔离 SDK 环境中 `10/10 PASS`。因此主项目仍保持 optional dependency，不把 F1 环境依赖扩散到系统 Python。

## Acceptance-criterion evidence map

| AC | Executor result | Evidence |
|---|---|---|
| AC-01 official source pin + classes import | PASS | EV-01, EV-02 |
| AC-02 real official instances → VALID | PASS | EV-03, EV-04 |
| AC-03 non-official objects fail closed | PASS | EV-03, EV-04 |
| AC-04 S05-S07 reuse H-34 safety gate | PASS | EV-03, EV-04, EV-05 |
| AC-05 Amount/Merchant canonical mapping | PASS | EV-03, EV-04 |
| AC-06 incomplete experiment_context no half Canonical | PASS | EV-03, EV-04 |
| AC-07 optional dependency boundary | PASS | EV-02, EV-04, EV-09 |
| AC-08 official source/H-34/Core invariance + allowed scope | PASS | EV-01, EV-05, EV-06, EV-09 |
| AC-09 inherited project guardrails | PASS | EV-05, EV-06, EV-07, EV-08, EV-09 |
| AC-10 honest local-slice scope | PASS | EV-01, EV-08, 本 REPORT |

## EV-01 — Source scope and frozen hashes
- AC: AC-08, AC-10
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-01.stderr.log

## EV-02 — Official SDK environment preflight
- AC: AC-01, AC-07
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-02.stderr.log

## EV-03 — Evaluator-owned official SDK cases
- AC: AC-02, AC-03, AC-04, AC-05, AC-06
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-03.stderr.log

## EV-04 — F1 focused unit tests
- AC: AC-02, AC-03, AC-04, AC-05, AC-06, AC-07
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-04.stderr.log

## EV-05 — H-34 boundary regression
- AC: AC-04, AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-05.stderr.log

## EV-06 — Existing AP2 regression
- AC: AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-06.stderr.log

## EV-07 — Project impact baseline
- AC: AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-07.stderr.log

## EV-08 — Formal experiment entrypoint
- AC: AC-09, AC-10
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-08.stderr.log

## EV-09 — System full unittest
- AC: AC-07, AC-08, AC-09
- Meta: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-09.meta.json
- Stdout: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-09.stdout.log
- Stderr: docs/05_任务交接/F1_AP2_V020_OFFICIAL_SDK_EXECUTABLE_SLICE_V1/evidence/EV-09.stderr.log

## Impact comparison

- Measurement evidence: EV-01..EV-09, F1_PROJECT_BASELINE.json, L2-GATE.json
- Before: official generated SDK objects executable through project boundary=ABSENT; H-34 boundary=10/10; project baseline=12/12; full unittest=721 tests OK.
- After: real official OpenPaymentMandate/PaymentMandate/CheckoutMandate execute through thin Bridge→H-34→existing adapter; evaluator SDK cases=9/9; focused Bridge tests=10/10; H-34=10/10; project baseline=12/12 repeat 3/3; system full unittest=731 tests OK with 10 expected SDK skips.
- Delta: official generated types moved from ABSENT to an executable local slice without changing H-34 or Canonical/Trust Core.
- Guardrail result: H-34=10/10; existing AP2=17/17; project baseline=12/12 repeat 3/3; S01-S13=13/13; PayBench=10/10; AP2 minimal=2/2; Attack Overlay=6/6; system full suite zero failures.
- Scope caveat: this is a local official-generated-types executable slice only. It is not full AP2 SDK/conformance evidence and does not verify issuer signatures, open payment.reference delegation, cnf/KB-SD-JWT, receipts, MandateChain, Sandbox/provider/wallet interoperability, production credentials, real PII, or real payment.

Executor 不给出最终 `IMPROVED / NO_MEASURABLE_GAIN / REGRESSED` Project Impact verdict(项目影响裁决)；由 Evaluator L3 独立复核后裁决。

## Deviations and unresolved items / 偏差与未解决项

- Contract deviation: NONE。
- Workflow structural fix: validator 首次只报 Contract 模板缺少可识别的 `Strategic basis / Estimated affected scope / Rollback condition` 标签；已用原有冻结内容补齐这些结构字段，未改变 H-35、AC、principal change、allowed scope 或 Validation Plan。
- Frozen product checks skipped: NONE。
- Dependency authority: Human explicitly approved `pydantic==2.12.5` + necessary resolver dependencies in `.task_envs/f1_ap2_v020/`。
- Environment adjustment: task venv switched to `--system-site-packages` to reuse already-present `cryptography 41.0.7`; no new direct dependency was installed。
- Complete implementation→L2 cycles consumed: `1/2`。
- Remaining unresolved items are exactly the frozen exclusions: full SDK helpers/MandateChain, issuer verification, delegation, cnf/KB-SD-JWT, receipts, Sandbox/provider/wallet, real credentials/PII/funds。
- Authorization respected: commit=false, push=false, history_rewrite=false, api_call=false（the explicitly approved package installation was limited to the dependency gate）。

## Submission boundary / 提交边界

```text
REPORT status = SUBMITTED_FOR_REVIEW
L2            = PASS 9/9
workflow      = OK
next owner    = Evaluator
commit/push   = not authorized
```

Evaluator 下一步应独立执行 L3，裁决 Task verdict / Project impact verdict / Continuation，并决定 B-06 是否继续前移到更完整的 official SDK helper / cryptographic verifier / provider-sandbox 层。
