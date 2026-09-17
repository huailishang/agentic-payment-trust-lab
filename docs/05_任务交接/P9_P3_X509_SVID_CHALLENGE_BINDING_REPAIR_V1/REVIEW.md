# Evaluator Review

Task ID: `P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1`  
Task kind: `repair`  
Reviewed snapshot: `04047308519a0ea69b7d7c0173f74e2b1fe30fc7`  
Project map reviewed: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` revision `2026-09-15-r41`  
Active bottleneck at dispatch: `B-15 / B-15B Credential / Possession Verification`  
Repair hypothesis: `H-29R`

## Project context brief / 项目全局位置

```text
A. 评测与治理底座                  [完成]
→ B. 授权、绑定、来源、执行前治理   [完成]
→ C. 支付生命周期、恢复、补救证据链 [完成]
→ D. 责任归因与可消费审计链         [完成]
→ E. 主体真实性 / 凭证 / 签署指令   [本轮完成本地代表性闭环]
→ F. 外部真实协议 / SDK / 网络接入   [延期；需要真实环境与授权]
```

本轮不是继续扩身份体系，而是修复 H-29 已被独立反例证明的 false `VERIFIED`（错误高保证）路径：旧 signed challenge（签名挑战）可以被重新贴上新的 nonce / issued_at 元数据后错误通过 freshness / replay（新鲜度 / 防重放）检查。

H-29R 只允许增加 canonical challenge binding（规范挑战绑定），不修改 P3 promotion rule（晋级规则）、Payment policy（支付策略）、Signed Instruction（签署指令）或外部身份体系。

## Snapshot acceptance / 快照接收

Evaluator 独立复核使用当前干净快照：

```text
HEAD        = 04047308519a0ea69b7d7c0173f74e2b1fe30fc7
origin/main = 04047308519a0ea69b7d7c0173f74e2b1fe30fc7
git status  = clean
```

`REPORT.md` 仍保留“未执行 commit / push”的 Executor 执行期描述，而当前仓库已经处于提交并同步后的快照。该差异不改变产品内容或 L3 复跑结果；本 REVIEW 以实际 reviewed snapshot 为准，不回写 Executor 报告。

## L3 independent gate / L3 独立复核门

Evaluator 使用冻结 `VALIDATION_PLAN.yaml` 重新执行全部 8 个 mandatory checks（必选检查）：

```text
L3 result: PASS
checks: 8/8
mandatory_failures: 0
```

权威汇总：

`docs/05_任务交接/P9_P3_X509_SVID_CHALLENGE_BINDING_REPAIR_V1/evidence/L3-GATE.json`

关键独立结果：

- `RV-EV-02`：nonce / agent / provider / executor / issued_at 六类 metadata relabel（元数据重贴）反例全部 fail closed（失败即关闭），统一包含 `credential_possession_challenge_binding_mismatch`；
- `RV-EV-03`：父 H-29 frozen matrix（冻结矩阵）保持 `7/7 PASS`、repeat=`2`、`VERIFIED 0→1`；
- `RV-EV-05`：focused regressions（聚焦回归）`30/30 PASS`；
- `RV-EV-07`：S01—S13 `13/13 PASS`，PayBench 仍为 `8/10` 可执行，唯一剩余缺口仍是 D1 privacy disclosure（隐私披露）；
- `RV-EV-08`：full unittest（全量单测）`699/699 PASS`；
- `RV-EV-06`：项目级 Product Trace=`10/12`、GESR=`9/12`、callback=`12/12`、unsafe allow=`0/5` 等守护线未退化。

## Acceptance criteria / 验收项

| AC | Evaluator verdict | Independent evidence |
|---|---|---|
| AC-01 Metadata relabel attack closed | 通过 | `RV-EV-02` |
| AC-02 Canonical challenge exact binding | 通过 | `RV-EV-02`, `RV-EV-05` |
| AC-03 Parent capability preserved | 通过 | `RV-EV-03`, `RV-EV-04`, `RV-EV-05` |
| AC-04 Legacy P3 / payment policy preserved | 通过 | `RV-EV-01`, `RV-EV-03`, `RV-EV-05` |
| AC-05 Focused boundary tests | 通过 | `RV-EV-05` = `30/30 PASS` |
| AC-06 Protected stages unchanged | 通过 | `RV-EV-01`, `RV-EV-03` |
| AC-07 Project guardrails | 通过 | `RV-EV-06`, `RV-EV-07`, `RV-EV-08` |
| AC-08 v2.2 handoff | 通过 | `L3-GATE.json` = `PASS` |

## Verdict / 裁决

```text
Task verdict: PASS
Project impact: NOT_APPLICABLE
Continuation: SWITCH
```

`NOT_APPLICABLE` 的原因：本包是 repair（修复），作用是恢复 H-29 已声明的能力边界并关闭一个错误 `VERIFIED` 路径，不单独把测试数增加解释成新的项目能力增长。

## Bottleneck movement / 瓶颈移动

H-29R 已把 B-15B 当前唯一已知的本地高保证误判路径关闭，同时保留：

```text
credential_ref-only → BOUND
bounded X.509-SVID + subject binding + possession + freshness/replay → VERIFIED
Payment policy unchanged
Signed Instruction / AP2 / ACP unchanged
```

因此阶段 E 在**本地、离线、合成凭证**边界内已经形成代表性闭环：

- B-15A：ACP/HMAC + AP2/ES256 两个 Signed Instruction（签署指令）消费者已关闭；
- B-15B：X.509-SVID credential validity（凭证有效性）+ subject binding（主体绑定）+ proof of possession（持有证明）+ freshness/replay（新鲜度 / 防重放）已形成第一个受控 `BOUND→VERIFIED` 路径，并关闭 metadata relabel replay（元数据重贴重放）反例。

这不代表生产 Authentication（认证）已经完成。live SPIRE / PKI / OIDC / DID / VC、真实 Provider、真实密钥和网络故障仍属于 B-06 `DEFERRED`（延期），只有出现真实外部环境与授权才重新激活。

剩余候选重新比较后：

1. `B-05 Data Minimization（数据最小化）`：PayBench D1 两题仍稳定 `UNSUPPORTED`，当前外部挑战覆盖 `8/10`；同时 PCAC-15 被项目外部基线标为 `CORE / ADAPTER` 的明显缺口。它已经有 measured（实测）重复缺口，不需要再做一轮只测量。
2. `B-03 Product Trace（产品权威轨迹）`：仅剩 T05/T06 `2/12`，现有 `10/12` 已具代表性覆盖，且不是当前零容忍断点，继续 `WATCH`（观察）。
3. `B-04 Autonomous Agent Behavior（自主 Agent 行为）`：长尾已被 Systematic Discovery（系统发现）量化，当前价值是保留真实失败和回归资产，不再优先逐题修。

因此第一瓶颈切换到 `B-05`。

## Next bounded direction / 下一有界方向

下一任务：`P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1` / `H-30`。

只建设一个最小协议中立 data disclosure fact（数据披露事实）并让 PayBench D1 成为第一个消费者：

```text
required fields（完成任务必要字段）
+ policy allowed fields（策略允许字段）
+ requested fields（页面 / Provider 请求字段）
        ↓
DataDisclosureFact（数据披露事实）
        ↓
approved required fields + blocked nonessential fields
        ↓
D1 Trap / Lookalike 进入现有 M5
```

目标是把外部挑战从 `8/10 executable → 10/10 executable`，同时证明“阻断非必要字段”不会演变成“连必要字段也不敢给”。本包不扩展到 retention（保留期限）、日志脱敏、跨 Provider 传播、完整隐私治理或生产 PII（个人信息）。
