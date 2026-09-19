# Evaluator Review

Task ID: `H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Baseline HEAD: `2b57248af464623402a71d65a2098244819519e3`
Project map before review: `2026-09-19-r53`
Active bottleneck: `B-06`
Hypothesis: `H-37`

## Final verdict / 最终裁决

- Task verdict: `PASS`
- Project-impact verdict: `IMPROVED`
- Continuation decision: `HUMAN_REQUIRED`
- L3 independent gate: `8/8 PASS`
- Mandatory failures: `0`

H-37 已把 official AP2 two-hop runtime verification 从 `ABSENT` 推进为 `BOUNDED_EXECUTABLE_SLICE`。继续在同一 AP2 本地路径补 Checkout/Payment typed semantics 或 Receipt 的边际信息增益，低于切换第二个真实外部 Sandbox 的项目价值；但 Sandbox/network/API/credential authority 不继承 H-37 授权，因此下一步必须由 Human 明确授权。

## Project context brief / 项目全局位置

```text
A 评测与治理底座                         [CLOSED]
→ B 授权/绑定/来源/执行前治理            [CLOSED]
→ C 支付生命周期/恢复/补救证据链          [CLOSED]
→ D 责任归因/可消费审计链                 [CLOSED]
→ E Actor Authenticity                   [LOCAL REPRESENTATIVE CLOSURE]
→ F External Protocol / SDK / Provider   [CURRENT]
```

F 阶段已经依次完成 AP2 official contract compatibility、bounded protocol boundary、official generated SDK objects 和 official two-hop cryptographic/delegation verification。H-37 打的是 B-06 当前最前的密码学运行断点，而不是新增业务支付规则。

## Submission acceptance / 提交快照接收

Executor 按 Amendment 01 完成唯一一次 validation-only L2 rerun(仅验证重跑)：

- L2: `8/8 PASS`
- effective baseline: `2b57248...`
- product stopped snapshot hashes 与 Amendment 前一致：
  - `ap2_official_verification.py = 7a094c9d...270a`
  - `adapters/__init__.py = 1a7aafae...872c`
  - `test_ap2_official_verification.py = 4321882e...c780`
- pinned AP2 source 未修改
- 无第三轮产品实现
- 无 commit / push / Sandbox / provider / wallet / 生产 credential / PII / 真实资金

Workflow validator 在接收前返回 `OK`，随后路由进入 `READY_FOR_REVIEW / Evaluator`。

## Independent L3 / 独立 L3

Evidence gate:
`docs/05_任务交接/H37_AP2_OFFICIAL_TWO_HOP_VERIFICATION_SLICE_V1/evidence/L3-GATE.json`

结果：

```text
VP-01 source scope                    PASS
VP-02 dependency preflight            PASS
VP-03 official two-hop cases          PASS
VP-04 H37 focused unittest            PASS
VP-05 existing AP2 / ES256 regressions PASS
VP-06 project baseline repeat=3       PASS
VP-07 formal experiment entrypoint    PASS
VP-08 full unittest                   PASS

total=8
mandatory_failures=0
L3=PASS
```

### Frozen C01-C08

Independent `RV-EV-03`：

```text
C01 valid two-hop chain               VALID
C02 wrong root key                    INVALID
C03 root signature byte tamper        INVALID
C04 terminal signature byte tamper    INVALID
C05 broken cnf delegation             INVALID
C06 wrong expected_aud                INVALID
C07 wrong expected_nonce              INVALID
C08 previous-token binding tamper     INVALID

8/8 PASS
```

这证明的不是“字符串长得像签名”，而是官方 verifier(官方验证器)实际接受合法链、拒绝错误 root key、真实签名字节篡改、错误 delegation、错误 audience/nonce 和错误上一跳绑定。

## Acceptance criteria / 验收逐项

- AC-01 `通过`：task-local env 四个 direct pins 精确匹配；无系统 Python / 主项目依赖改写。
- AC-02 `通过`：直接使用 pinned AP2 v0.2.0 / `b4587ac1...`；未复制 official verifier 规则。
- AC-03 `通过`：C01 返回 `VALID / hops=2 / official_verifier_completed=true`。
- AC-04 `通过`：C02-C04 全部 fail closed。
- AC-05 `通过`：C05/C08 全部 fail closed。
- AC-06 `通过`：C06/C07 audience/nonce mismatch 全部 fail closed。
- AC-07 `通过`：结果仅保留最小 verification fact；不保存 raw token/signature/private key/disclosures/full payload；protocol semantics 继续由 official verifier 拥有。
- AC-08 `通过`：optional dependency boundary 保持；系统 Python 下既有主项目回归可运行。
- AC-09 `通过`：25/25 existing AP2+generic ES256 focused regression；project baseline `12/12 repeat=3`；S01-S13 `13/13`；PayBench `10/10`；AP2 minimal `2/2`；Attack Overlay `6/6`；full unittest `733 OK / 10 expected skips`。
- AC-10 `通过`：能力声明严格限定为 AP2 official root SD-JWT + terminal KB-SD-JWT two-hop crypto/delegation slice；不外推为 Checkout/Payment typed business constraints、Receipt、完整 AP2 conformance、Sandbox/provider/wallet 或真实支付。

## Project-impact verdict / 项目影响裁决

Before:

```text
official AP2 two-hop cryptographic/delegation runtime verification = ABSENT
```

After:

```text
root SD-JWT
→ official issuer signature/disclosure verification
→ verified cnf.jwk delegation
→ terminal KB-SD-JWT holder signature
→ previous-token binding
→ aud / nonce
= BOUNDED_EXECUTABLE_SLICE
```

因此 project impact = `IMPROVED`。

这不是测试数量意义上的“变好”，而是 B-06 的第一条 official cryptographic/delegation runtime capability 从没有运行证据变成可执行、可负测、可独立复核。

## Iteration-value assessment / 继续迭代价值

H-37 本轮收益高：关闭了 F1 之后最大的 authenticity gap(真实性缺口)，而且只增加一个薄 AP2 adapter，没有修改 Trust Core。

但继续 AP2 本地扩展的边际收益开始下降：

- Checkout/Payment typed constraints 已被 H-36 明确为 downstream business semantics(下游业务约束语义)，不是当前密码学真实性断点；
- Receipt 是单独 post-payment path(支付后路径)，不应为了“AP2 做全”机械扩张；
- 当前项目目标是验证 protocol-neutral trust control plane(协议中立信任控制面)能否跨真实外部协议/环境成立，而不是成为 AP2 全量实现。

与之相比，第二个真实外部 Sandbox 能第一次引入：

```text
真实外部 endpoint
→ sandbox credential/key
→ request/response
→ payment proof / verification
→ callback / async evidence
→ provider-observed state
```

其 expected project value(预期项目价值)高于继续本地 AP2 加 Case。

## Bottleneck movement / 瓶颈移动

H-37 **清除了 B-06 的 official two-hop runtime 断点**。

B-06 没有关闭，而是前移到：

> **能否在不使用真实资金的公开 Sandbox 中，让第二个真实支付协议/Provider 产生外部可验证的请求、凭证、回调/状态证据，并进入现有 Trust / Trace 边界。**

下一优先方向：`H-38 / F2 Alipay Agent Pay Sandbox first external slice`。

当前官方公开资料已明确提供 Agent Pay 沙箱路线，沙箱不使用真实资金；AI按量付费链路包含 `402 Payment Required`、`Payment-Proof`、商户向支付宝验证支付凭证以及异步履约/通知。下一包不进入生产环境、不使用真实资金。

## Continuation / 下一步

Machine continuation decision: `HUMAN_REQUIRED`.

原因不是技术路线不清楚，而是下一步需要新的权限：

- 允许访问支付宝 Agent Pay Sandbox / sandbox OpenAPI；
- 允许使用**沙箱专用** app id / key / test account，且只从 task-local environment 读取，不写入仓库/报告；
- 允许 sandbox 模拟交易和 sandbox callback/notification；
- 继续禁止生产支付宝、生产 credential、真实 PII、真实资金、commit/push/history rewrite，除非另行授权。

下一草案：`docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/`。

Final verdict: `PASS`
