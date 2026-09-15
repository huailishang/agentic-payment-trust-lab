# Evaluator Review

Task ID: `P9_P3_X509_SVID_CREDENTIAL_POSSESSION_VERIFIER_V1`  
Task kind: `capability_experiment`  
Evaluator verdict: **REJECTED**  
Project impact verdict: **REGRESSED**  
Continuation decision: **CONTINUE**  
Reviewed baseline HEAD: `fca87c2d987b3d71c1156e50747cb8eeec1c84c7`

## 1. 全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [后续]
```

B-15A Signed Instruction Verification（签署指令验证）已关闭。H-29 打的是 B-15B Credential / Possession Verification（凭证 / 持有证明验证）：目标不是再核对引用，而是第一次让 P3 在 credential validity（凭证有效性）+ subject binding（主体绑定）+ proof-of-possession（持有证明）+ freshness/replay（新鲜度 / 防重放）四条件全部成立时合法输出 `VERIFIED`。

## 2. 评估者先修正的合同格式问题

Executor 的 L2 实现与验证已经完成，但 REPORT 因两个 Evaluator-owned（评估者拥有）合同机器格式问题标记为 `BLOCKED`：

1. `Active bottleneck` 与 `CURRENT.md.active_bottleneck_id` 不精确一致；
2. 缺显式 `Metric baseline:` 字段。

这两项属于评估者冻结合同格式错误，已原地修正：

```text
Active bottleneck: B-15
Sub-bottleneck: B-15B Credential / Possession Verification
Metric baseline: ...
```

没有修改任务目标、四条件升级门、允许范围、验收标准或实现语义，因此不新开 repair task（修复任务）处理这两个格式问题，也不要求 Executor 重做已有 L2。

## 3. 独立复跑

Evaluator 对冻结 VP-01..VP-08 全部重新执行，结果均为 exit=0：

```text
RV-EV-01 source snapshot audit       PASS
RV-EV-02 architecture boundary       PASS
RV-EV-03 H-29 capability runner      PASS
RV-EV-04 result audit                PASS
RV-EV-05 focused tests               29/29 PASS
RV-EV-06 project impact baseline     PASS
RV-EV-07 formal scenarios            13/13 PASS
RV-EV-08 full unittest               698/698 PASS
```

H-29 result SHA-256 独立重跑仍为：

`e35d398c209bb72aae9fb403f82ba01db0281c2b91f146e240130417e7d28702`

冻结七案例仍表现为：

```text
V01 valid                         → VERIFIED
N01 wrong trust                   → BOUND
N02 wrong subject                 → BOUND
N03 no possession proof           → BOUND
N04 bad possession proof          → BOUND
N05 replayed nonce                → BOUND
N06 stale challenge               → BOUND
```

既有保护源文件 hash 未变化，Payment policy（支付策略）仍同时接受 BOUND / VERIFIED，没有新增支付副作用回归。

## 4. 独立反例：旧签名可通过“重贴新 nonce / 新时间”绕过 replay

冻结七案例本身都通过，但 AC-06 / AC-07 的安全语义还要求：freshness/replay（新鲜度 / 防重放）必须和**被签名的 challenge 内容**绑定，而不是只看调用方另外传入的元数据。

Evaluator 构造了一个不改私钥、不改证书、不改旧 challenge payload、不改旧签名的反例：

```text
旧的 signed challenge payload       保持不变
旧 signature                       保持不变
旧 payload 中真实 nonce            = nonce-h29-v1-001
consumed_nonce_refs                 包含这个旧 nonce

但调用 verifier 时重新传：
nonce_ref                           = nonce-attacker-fresh-label
issued_at_epoch                     = 一个更新的时间
observed_at_epoch                   = 更新后的 fresh 时间
```

期望：旧签名对应的旧 challenge 已经被消费，不能通过给外部元数据“换标签”重新变成 fresh challenge。

实际结果：

```text
status            = VALID
reason             = credential_possession_verified
freshness_valid    = true
replay_detected    = false
```

证据：

- `evidence/RV-EV-09.meta.json`
- `evidence/RV-EV-09.stdout.log`
- `evidence/RV-EV-09.stderr.log`

`RV-EV-09` 退出码为 `1`，因为该反例错误地获得了 `VALID / VERIFIED` 语义。

根因很明确：当前 `verify_x509_svid_credential_possession()` 验证的是 `challenge_payload` 的签名，但 `nonce_ref / issued_at_epoch / observed_at_epoch` 是另外的函数参数；实现没有机械证明这些外部参数就是**被签名 payload 中的 nonce / issued_at**。因此攻击者可以拿旧 payload + 旧签名，再给它附一个“新的 nonce 标签”和“新的时间标签”。

## 5. AC 裁决

| AC | 裁决 | 说明 |
|---|---|---|
| AC-01 Legacy P3 boundary | 通过 | credential_ref-only 仍为 BOUND |
| AC-02 Protocol-neutral fact | 通过 | 未泄漏 Payment / protocol 业务字段 |
| AC-03 Credential validity | 通过 | bounded X.509-SVID trust / cert profile 可机械验证 |
| AC-04 Subject binding | 通过 | SPIFFE Agent / Executor 错绑不晋级 |
| AC-05 Proof of possession | 通过（局部） | 签名本身能验证，但尚未证明“这是当前 challenge”的签名 |
| AC-06 Freshness / replay | **不通过** | nonce / issued_at 未与 signed payload 绑定，可通过重贴新元数据绕过 |
| AC-07 Exact promotion rule | **不通过** | 四条件中的 freshness/replay 可被伪造为 true，从而错误晋级 VERIFIED |
| AC-08 Seven headline cases | 通过但不足 | 7/7 只覆盖冻结变形，没有覆盖 metadata relabel attack（元数据重贴攻击） |
| AC-09 Payment policy unchanged | 通过 | 当前支付策略未被偷偷收紧 |
| AC-10 Signed Instruction isolation | 通过 | 冻结源不变 |
| AC-11 Dependency / sensitive-data | 通过 | 无网络、无生产凭证、无持久化私钥 |
| AC-12 Project guardrails | 通过 | 13/13，698/698，既有项目指标无退化 |
| AC-13 Honest scope | 通过 | 报告边界声明真实 |
| AC-14 v2.2 handoff | 不构成 PASS | 即使结构格式修正，AC-06/07 已实质失败 |

## 6. 正式裁决

Task verdict：**REJECTED**。

Project impact：**REGRESSED**。

原因不是当前 Payment callback（支付回调）出现了新增错误扣款；当前支付护栏仍稳定。`REGRESSED` 指 B-15B 新增的高保证身份能力表面产生了 `VERIFIED`，但存在可机械复现的 false VERIFIED（错误高保证）路径。相比原来“最多 BOUND、绝不冒充 VERIFIED”，这是身份保证语义上的倒退，因此不能记成 `IMPROVED`。

H-29 的大方向并未被证伪：X.509-SVID + challenge signature 仍然适合做第一 credential/PoP（凭证/持有证明）切片。失败属于一个局部实现合同缺口：**signed challenge 没有把 nonce / identity context / issued_at 与验证元数据锁死。**

Continuation：**CONTINUE**，但只能做一个 bounded repair（有界修复），不能扩成 SPIRE / PKI / OIDC / DID / VC。

## 7. 下一步

新任务：

`P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1`

Repair objective（修复目标）：

> 让 verifier（验证器）只认可一个 canonical signed challenge（规范化签名挑战）；`nonce / agent / provider / executor / issued_at` 必须和被签名 payload 完全一致。旧 payload + 旧 signature 即使附带新的外部 nonce / timestamp，也必须 fail closed（失败即关闭），不得获得 VERIFIED。

修复后必须重新跑：

```text
原 H-29 7/7
+ metadata relabel replay counterexample
+ nonce mismatch
+ issued_at mismatch
+ agent / executor / provider challenge-context mismatch
+ legacy credential_ref-only BOUND
+ 29 focused regressions（或更多）
+ project baseline
+ S01-S13
+ full unittest
```

不改 Payment policy，不改 `execution_facts.py` promotion rule，不改 Signed Instruction，不新增依赖，不联网。
