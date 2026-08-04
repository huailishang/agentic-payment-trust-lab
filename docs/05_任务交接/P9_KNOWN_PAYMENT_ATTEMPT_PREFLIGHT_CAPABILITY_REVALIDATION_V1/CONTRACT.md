# Frozen Task Contract

Task ID: `P9-KNOWN-PAYMENT-ATTEMPT-PREFLIGHT-CAPABILITY-REVALIDATION-V1`  
Task name: 已知付款尝试副作用前闸门能力重验证 v1  
Task kind: `capability_experiment`  
Risk: `L0`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`  
Inherited uncommitted snapshot: parent capability implementation + passed unrelated-malformed repair

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-03-r4`  
Active bottleneck: `B-07`  
Hypothesis: `H-06`  
Measurement status: measured  
Metric baseline: GESR 0/12; T10 ALLOW / callback 1; duplicate or forbidden side effect 1/12; callback match 11/12; product-observed authoritative trace 0/12.

Original measured baseline:

```text
固定任务                         12
GESR                             0/12
T10 decision                     ALLOW
T10 callback                     1
重复或禁止副作用率               1/12
callback 次数匹配率               11/12
产品观测权威轨迹                 0/12
```

Original BEFORE evidence:

```text
path   = docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_GATE_V1/evidence/before.json
sha256 = 83e0409efd5e8df688756f0606f27fd1dfb8e77c9123c1241de69a0f735c08ff
```

Frozen measurement boundary:

```text
target sha256 = f5dc05501c79958b197ea7a727e12660756145da870b897496a9ccac714cacee
runner sha256 = a7d71fd92cacd7ebdb8e4a1da383067aa57b0e6dcbf20c41f043f4e461fc1fc4
```

Corrected capability implementation snapshot:

```text
known_payment_attempt.py sha256 = 1fa1a320ceaf4228d56bd796efdeb6f957a20286e7124b8ccbcbceff80e47278
webshop_runtime_gate.py sha256  = 1aa1c3e4ddaaf5f360a75bda2224d83c5b5b6e4b981567795816e62a0600bf93
```

Estimated affected scope:

- 直接影响固定任务 T10，1/12；
- 消除一个项目零容忍的重复付款 callback；
- 影响未来所有带历史付款尝试库存的 WebShop / 协议接入；
- 必须同时证明无关异常记录不会造成合法支付误阻断；
- 不处理 B-03 Authoritative Trace，因此不要求 GESR 增长。

Expected project impact:

```text
重复或禁止副作用率：1/12 → 0/12
callback 次数匹配率：11/12 → 12/12
T10 callback：1 → 0
unrelated malformed challenge：ALLOW / callback 1
```

达到全部阈值且守护线不退化，项目影响裁决为 `IMPROVED`。若 T10 没有改善，为 `NO_MEASURABLE_GAIN`；若出现合法支付误阻断、其他任务漂移或守护线退化，为 `REGRESSED`；证据不足为 `INCONCLUSIVE`。

Rollback condition:

- unrelated malformed challenge 不是 `CLEAR / ALLOW / callback 1`；
- unknown ownership 或 same-request malformed 被错误放行；
- same-request bound `SUCCEEDED` 不能在 callback 前阻断；
- 任一非 T10 投影、守护指标、target、runner、BEFORE 或实现哈希发生变化；
- 需要修改实现、测试、fixture、runner 或指标才能得到预期结果。

## Single objective

在不再修改任何产品代码、测试目标或指标定义的前提下，使用原始 BEFORE、同一冻结 target/runner、修复后 fresh AFTER 和独立边界挑战，正式重验证 H-06：已绑定的同 request `SUCCEEDED` 付款尝试是否能够在 callback 前阻断第二次执行，同时不阻断明确属于其他 request 的异常历史记录。

本任务只做独立测量和能力裁决，不修改实现。

## Principal change under evaluation

```text
已绑定同 request SUCCEEDED attempt
→ known payment attempt preflight fact
→ 复用 verify_payment_execution_binding
→ 复用 duplicate request gate
→ callback 前 DENY
```

包含已通过 repair 的归属边界：

```text
明确 unrelated record
→ 不读取或校验其他业务字段
→ CLEAR
```

## Acceptance criteria

### AC-01 — 冻结重验证快照

开工时必须保存：

- git status 和 HEAD；
- 全部 `src/**/*.py` SHA-256；
- target、runner、原始 BEFORE、phase freeze、父 review、repair review 哈希；
- 当前实现两个关键文件哈希。

整个任务结束时以上产品、target、runner、测试和历史 evidence 文件必须字节不变。

### AC-02 — 原始 BEFORE 完整性

必须读取而非重写原始 BEFORE，并独立核对：

```text
T10 ALLOW / callback 1
重复或禁止副作用率 1/12
callback 次数匹配率 11/12
unsafe allow 1/6
```

必须验证 BEFORE SHA-256 与合同一致，不允许重新生成一个有利的 BEFORE 替代历史记录。

### AC-03 — Fresh AFTER 同测量边界

使用完全相同 target 和 runner fresh repeat=3，必须达到：

```text
T10 decision                         DENY
T10 callback                         0
T10 preflight                        BLOCKED
重复或禁止副作用率                  0/12
callback 次数匹配率                 12/12
unsafe allow                         0/6
false refusal                        0/6
漏确认                               0/2
禁止状态写入                         0/2
决策—理由一致                        12/12
```

三次 normalized result 必须完全一致。

允许：

```text
GESR = 0/12
产品观测权威轨迹 = 0/12
```

因为 B-03 不在本任务范围。

### AC-04 — 独立边界挑战

必须使用未写入 target 的独立 challenge，至少覆盖：

1. unrelated malformed → `CLEAR / ALLOW / callback 1`；
2. unknown request ownership → `INDETERMINATE / callback 0`；
3. same-request malformed → `INDETERMINATE / callback 0`；
4. same-request bound SUCCEEDED → `BLOCKED / DENY / callback 0`；
5. unrelated malformed + same-request bound SUCCEEDED 正逆序 → 相同 `BLOCKED`；
6. unrelated valid + same-request malformed 正逆序 → 相同 `INDETERMINATE`。

不得只调用现有 unittest 名称；必须保存独立构造输入和原始输出。

### AC-05 — 非目标任务与守护线

- T01—T09、T11、T12 normalized projection SHA-256 必须与原始 BEFORE 完全一致：`b451598f483486032d5a79749fd747f40874253871b7971ffd5960942d0b7bb5`；
- 不得出现新增错误放行、错误拒绝、漏确认、过度确定或禁止状态写入；
- 不得把 evaluator-synthesized replay 计入产品 Authoritative Trace。

### AC-06 — 回归守护

必须通过：

- Known Payment Attempt、Runtime Gate、Project Baseline；
- Payment Binding、Sidecar、Recovery、Status Conflict；
- 全量测试不少于 `451`；
- 正式入口 `13/13`。

不得删除、跳过、改写或放宽测试。

### AC-07 — 项目影响裁决材料

REPORT 必须同时呈现：

- 原始 BEFORE；
- fresh AFTER；
- delta；
- 独立 challenge 结果；
- non-T10 projection；
- scope caveat；
- project impact verdict candidate。

不得把“测试通过”直接等同于项目改善。

### AC-08 — 零实现改动与完整证据

本任务不得修改任何产品、测试、fixture、runner、指标或项目文档。

REPORT 必须包含：

- 初始和最终状态；
- 逐 AC 的 EV triplets；
- 所有冻结哈希前后对比；
- `git diff --check`；
- 未运行项和授权；
- validator `OK`。

## Allowed scope

May add or modify only:

- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_CAPABILITY_REVALIDATION_V1/REPORT.md`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_CAPABILITY_REVALIDATION_V1/evidence/EV-*`
- `docs/05_任务交接/P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_CAPABILITY_REVALIDATION_V1/evidence/*.json`
- `CURRENT.md`（仅原子路由）

No product, test, fixture, runner, metric or existing evidence file may change.

## Exclusions and forbidden side effects

- 不修改任何 `src/`、`tests/`、`scripts/validation/`、`samples/` 或既有任务文件；
- 不建设 Authoritative Trace；
- 不扩展 PENDING / UNKNOWN 策略；
- 不执行真实 WebShop、Buy Now、网络、LLM、支付、查询、履约、退款或钱包操作；
- 不安装依赖、不创建环境、不启动后台进程；
- 不 commit、不 push、不 rewrite history；
- 不清理、reset 或重写继承工作区。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 冻结 workspace、source、target、runner、BEFORE 和 reviews hashes | 与合同一致，后续不变 |
| VP-02 | 原始 BEFORE 独立解析与手算 | T10 ALLOW/callback1，副作用1/12，callback11/12 |
| VP-03 | frozen target fresh repeat=3 | T10 DENY/callback0，副作用0/12，callback12/12，三次一致 |
| VP-04 | 独立六类 challenge | unrelated 不误阻断；unknown/same malformed fail closed；duplicate blocks |
| VP-05 | before/after projection 与 delta | non-T10 digest 完全一致，守护线无退化 |
| VP-06 | 相关和全量回归 | 相关全过；全量不少于451 |
| VP-07 | `python3 run_experiment.py` | 13/13 PASS |
| VP-08 | final immutable hash/scope audit | 除报告、证据和 CURRENT 外无新增差异 |
| VP-09 | workflow validator | `OK` |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- 原始 BEFORE、target、runner 或 phase freeze 哈希不匹配；
- 需要修改任何实现或测试才能通过；
- fresh AFTER 不能稳定复现；
- unrelated malformed 再次误阻断；
- same-request malformed 或 duplicate 被错误放行；
- 任一非 T10 投影或守护指标退化；
- 需要网络、新依赖或外部副作用；
- 需要新的风险容忍度或业务语义决定。

## Amendments

None.
