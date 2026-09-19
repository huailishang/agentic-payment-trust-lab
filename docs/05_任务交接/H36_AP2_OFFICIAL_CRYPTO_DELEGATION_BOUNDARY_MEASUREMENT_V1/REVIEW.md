# Evaluator Review

Task ID: `H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: `evaluator_design`
Reviewed baseline HEAD: `e6931273a983459f167b6e72287a6f05d53a8c26`
Active bottleneck: `B-06`
Hypothesis: `H-36`
Task verdict: `PASS`
Project impact verdict: `NOT_APPLICABLE`
Continuation verdict: `HUMAN_REQUIRED`

## 1. Project context / 项目上下文

项目最终目标不是“接一个支付协议”，而是证明智能体支付在高风险交易里，授权、绑定、身份真实性、上下文完整性、支付生命周期、恢复和审计证据能够形成可验证、可回放、可拒绝异常输入的可信执行链。

当前全局路线：

```text
A 评测与治理底座                         [CLOSED]
→ B 授权 / 绑定 / 来源 / 执行前治理       [CLOSED]
→ C 支付生命周期 / 恢复 / 补救 / 证据连续性 [CLOSED]
→ D 责任归因 / Read Model / Consumer       [CLOSED]
→ E Actor Authenticity 本地代表性真实性     [LOCAL REPRESENTATIVE CLOSURE]
→ F 外部真实协议 / SDK / Provider           [CURRENT]
   F0 compatibility measurement             [PASS]
   F0R AP2 boundary gate                    [PASS / IMPROVED]
   F1 official SDK executable slice         [PASS / IMPROVED]
   H-36 crypto/delegation boundary          [THIS REVIEW]
```

当前第一瓶颈仍是 `B-06`。F1 已证明 official AP2 generated types 可以进入现有 H-34 boundary gate(协议边界门)并到达 Canonical Facts，但“官方对象是否真的经过签名、持有证明和委托链验证”仍没有运行证据。H-36 的作用是 measurement-only(只测量)：先把这条验证链拆清楚，不提前实现 H-37。

## Pre-review checks / 评估前检查

Evaluator 没有直接采信 Executor 的 L2，先检查并确认：

- Executor REPORT 的实质结论与 L2 `5/5 PASS` 一致；
- pinned AP2 source 仍为 `v0.2.0 / b4587ac1d055888a73b4b21750973cffba961793`；
- baseline HEAD 为 `e6931273a983459f167b6e72287a6f05d53a8c26`；
- `src/**` / `tests/**` 没有 H-36 产品改动；
- H-36 没有安装、升级依赖，没有网络 API、Sandbox/testnet、Provider、wallet、生产 credential、PII 或真实资金副作用；
- workflow validator 在进入最终 L3 前返回 `OK`。

复核过程中发现一个纯 governance formatting drift(治理格式漂移)：通用 v2.2 validator 要求可识别的无反引号 `Executor status`，而冻结的 H-36 task-specific checker 又要求带反引号的同一状态行。首次 L3 因这个文本兼容冲突导致 VP-03 失败；在不修改测量数据、AC、Validation Plan、checker、产品代码或总体分类的前提下，仅对 REPORT 增加兼容状态行后，通用 validator 与冻结 checker 同时通过。该修正不改变任何 observed result(观测结果)。

## L3 Independent Gate

- Validation plan: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- Gate summary: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/L3-GATE.json
- Gate result: PASS
- Checks: `5/5 PASS`
- Mandatory failures: `0`

独立结果：

```text
VP-01 source pin + product scope             PASS
VP-02 official boundary inventory            PASS
VP-03 matrix / deps / classification         PASS
VP-04 project baseline smoke                 PASS
VP-05 existing experiment smoke              PASS

boundary surfaces                              10
minimum dependency rows                         4
overall classification              DEPENDENCY_BLOCKED
project baseline                            12/12
formal scenarios                            13/13
PayBench                                    10/10
AP2 minimal                                  2/2
Attack Overlay                               6/6
```

## 2. 核心核查结论

H-36 的测量结论成立，且把 B-06 的问题进一步收窄了。

第一，official mandate verification(官方授权凭证验证)不是一个单一黑盒。真实链路是：

```text
MandateClient.verify
→ parse_token
→ sdjwt.chain.verify_chain
   → root SD-JWT signature + disclosure + root PublicKeyProvider
   → verified cnf.jwk
   → terminal KB-SD-JWT holder signature
   → previous-token binding
   → aud / nonce / time semantics
```

第二，CheckoutMandateChain / PaymentMandateChain 的 `verify` 主要是 typed business constraint / binding semantics(类型化业务约束/绑定语义)，不能把它们当作密码学验签证据。Receipt 又是另一条 compact-JWS(紧凑 JWS) 路径，不应和 mandate delegation 混成一个 verifier。

第三，现有 generic ES256 verifier(通用 ES256 验签器)不能直接当 AP2 verifier 使用。它可以复用 compact JWS、P-256/ES256、签名输入和 ECDSA 验证等 primitive(密码学原语)，但 AP2 还需要 SD-JWT disclosure、root key provider、`cnf.jwk` key transition、previous-token binding、KB-SD-JWT `typ`、terminal/intermediate `cnf`、`aud` / `nonce` 和 AP2 chain time semantics。因此复用级别应保持：

`REUSE_PRIMITIVE_ONLY(仅复用密码学原语)`

第四，第一条值得真正执行的 official crypto slice(官方密码学切片)已经唯一收敛为：

```text
root SD-JWT
→ root signature / root key provider
→ verified root cnf.jwk
→ terminal KB-SD-JWT
→ holder signature
→ previous-token binding
→ expected aud / nonce
→ STOP
```

暂时不把 Checkout/Payment business semantics 或 Receipt 混进第一条能力实验。

## AC 逐条裁决

| AC | 裁决 | 独立依据 |
|---|---|---|
| AC-01 Source pin | 通过 | RV-EV-01、RV-EV-02：AP2 v0.2.0 / b4587ac1 固定来源与关键符号可复核 |
| AC-02 Boundary matrix complete | 通过 | RV-EV-03：10 个 surface 恰好齐全，枚举与字段合法 |
| AC-03 Crypto vs semantics separated | 通过 | RV-EV-02、RV-EV-03：mandate crypto chain 与 Checkout/Payment constraint semantics 已分层 |
| AC-04 Reuse claim bounded | 通过 | RV-EV-02、RV-EV-03：结论为 REUSE_PRIMITIVE_ONLY，没有把同为 ES256 误写成直接协议复用 |
| AC-05 Dependency set bounded | 通过 | RV-EV-03：pydantic / jwcrypto / sd-jwt / cryptography 四项边界已固定，没有扩成完整 AP2/ADK/demo 安装 |
| AC-06 First slice explicit | 通过 | RV-EV-03：唯一切片为 root SD-JWT + terminal KB-SD-JWT two-hop verification |
| AC-07 Product frozen | 通过 | RV-EV-01、RV-EV-04、RV-EV-05：src/tests 无 H-36 改动，12/12 baseline 与既有回归保持 |
| AC-08 Honest report | 通过 | RV-EV-03、RV-EV-05：没有声称完整 AP2/SD-JWT/Receipt/Sandbox/真实支付已验证 |

## RV-EV-01 — Source pin and product scope
- AC: AC-01, AC-07
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-01.stderr.log

## RV-EV-02 — Official boundary inventory
- AC: AC-01, AC-03, AC-04
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-02.stderr.log

## RV-EV-03 — Measurement contract check
- AC: AC-02, AC-03, AC-04, AC-05, AC-06, AC-08
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-03.stderr.log

## RV-EV-04 — Project baseline smoke
- AC: AC-07
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-04.stderr.log

## RV-EV-05 — Existing experiment smoke
- AC: AC-07, AC-08
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/RV-EV-05.stderr.log

## Project impact verdict / 项目影响裁决

Impact verdict: NOT_APPLICABLE

H-36 是 `evaluator_design` / measurement-only，没有新增产品 capability(能力)，所以不能写成 `IMPROVED`。它的价值是把 B-06 从“官方 crypto/delegation 边界未知”缩小成“第一条 two-hop slice 已定位，但执行环境依赖尚未获授权”。

## 3. Bottleneck movement / 瓶颈移动

本任务**缩小了瓶颈，但没有关闭 B-06**。

新的第一断点已经不是“AP2 的 verifier 在哪里”，也不是“generic ES256 能不能直接复用”，而是：

```text
已明确 two-hop official verification slice
→ 需要 faithful pinned isolated environment
→ 缺 jwcrypto==1.5.6
→ 缺 sd-jwt==0.10.4
→ cryptography 41.0.7 需与 official pin 46.0.5 对齐
→ 才能产生第一条 official runtime verification evidence
```

F2 Alipay Agent Pay Sandbox(支付宝 Agent Pay 沙箱)仍不是当前更优先方向。现在 H-37 已有明确、很小、可证伪的切片；直接跳到 F2 会同时引入第二协议、Sandbox、回调/查询/finality 等更多变量，反而不利于判断 cryptographic/delegation 缺口。

## 4. Continuation decision / 后续决策

Continuation verdict: `HUMAN_REQUIRED`

原因不是技术方案不清楚，而是 **dependency install authority(依赖安装授权) 缺失**。H-36 当前权限明确禁止安装/升级依赖，而 H-37 的 faithful execution(忠实执行)至少需要一个新的 task-local isolated environment(任务级隔离环境)，固定：

```text
pydantic==2.12.5
jwcrypto==1.5.6
sd-jwt==0.10.4
cryptography==46.0.5
```

授权范围应只覆盖 H-37 的任务级隔离环境，不扩到系统 Python，不授权网络 API、Sandbox/provider/wallet、生产凭证、PII、真实资金，也不自动授权 commit/push。

## Final verdict

PASS
