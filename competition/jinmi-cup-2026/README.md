# 金密杯 2026 比赛工作区

> 状态：HUMAN_DEFERRED（2026-10-11 暂缓推进，保留已有路线与资产）
> 日期：2026-09-28
> 当前关注方向：**面向金融应用的智能体能力增强与安全验证工程实践**。
> 目标：复用 `agentic-payment-trust-lab` 已有可信支付与安全验证能力，形成面向赛题的安全工程作品；不为比赛重写主项目。

Human 最新决定：当前优先补外部商城交易链接入适用性与交易团队需求证据，金密杯不占当前执行资源。安全赛题与主项目授权、绑定、篡改、重放及恢复能力相关，延期理由是现阶段优先级，而非领域无关。以下路线作为保留参考，不构成参赛执行安排。

## 1. 一句话定位

如果 Payathon 验证的是：

> “可信 Agent 能不能进入真实支付产品和商业闭环？”

那么金密杯验证的是：

> **“我们怎么证明一个金融 Agent 在越权、身份冒用、上下文污染、重复支付、状态不确定和恶意输入下仍然受控、可解释、可复核？”**

因此金密杯主要消费的是主项目已经较成熟的 **A-E 安全可信能力 + Harness**，而不是再造支付产品。

## 2. 参赛作品建议形态

暂定产品表达：

**Financial Agent Trust & Security Validation Lab**
中文可表述为：**金融智能体可信执行与安全验证平台**。

它不是支付 App，也不是支付机构，而是：

```text
金融 Agent / Payment Agent
        ↓
Security & Trust Harness
        ↓
Identity / Authorization / Binding
        ↓
Context / Tool Integrity
        ↓
Runtime Policy / Gate
        ↓
Controlled Side Effect
        ↓
Lifecycle / Recovery
        ↓
Evidence / Trace / Replay
        ↓
Attack / Regression / Independent Review
```

## 3. 从主项目复用什么

### 第一组：授权与身份

- Delegated Authority；
- Confirmation Binding；
- Agent / Executor Identity；
- Credential Possession 的本地代表性验证；
- Signed Instruction Verification。

### 第二组：交易完整性

- Intent / Order / Request / Payment 连续 Binding；
- Governed Payment Action；
- Runtime Authorization Gate；
- Idempotency / Replay；
- duplicate payment protection。

### 第三组：Agent 特有攻击面

- Context / Tool Integrity；
- Trust Source / Fact Lineage；
- Prompt / Context Tampering 的 Attack Overlay；
- 来源事实不能被低可信网页/LLM 静默覆盖；
- Action Origin / Responsibility Trace。

### 第四组：支付异常与恢复

- UNKNOWN Payment Recovery；
- Payment Finality / Status Conflict；
- Fulfillment Failure；
- Refund / Dispute / Remediation；
- 原交易绑定与补救证据连续性。

### 第五组：验证与证据

- 固定回归场景；
- PayBench；
- AP2 / x402 / WebShop 外部样品；
- Project Impact Baseline；
- Authoritative Trace；
- Consumer / Read Model / Player；
- Evaluator / Executor 独立复核机制。

## 4. 与 Payathon 的边界

| 维度 | 金密杯 | Payathon |
|---|---|---|
| 核心问题 | Agent 安全与可信是否可证明 | Agent 支付产品能否真实闭环 |
| 主复用能力 | A-E + Harness + Attack + Evidence | Trust Core + F 阶段 Provider/协议 |
| Demo 中心 | 攻击/异常前后是否受控 | 下单/支付/Proof/履约 |
| 外部平台依赖 | 可较低，优先可复现实验 | 较高，需要支付宝协议/Provider |
| 主要产出 | 安全验证体系、攻击集、证据链、评测结果 | Agent Pay / Machine Pay 产品 |
| 是否改变主 Core | 否 | 否 |

两个比赛共享同一个 Core，但**不能提交成同一个故事换皮**：

- 金密杯强调 Security Engineering / Assurance；
- Payathon 强调 Product / Payment Integration / Commerce Closure。

## 5. 强制隔离原则

1. 不因赛题增加一套“金密杯专用 Trust Core”。
2. 不为了展示攻击数量随机增加大量 Case。
3. 不把密码技术等于“多加签名/上链”；只有真实 Trust Gap 需要时才引入。
4. Strong Authentication、Credential/Key Governance、生产级 Cryptographic Verification 未有真实证据时，不写成已完整解决。
5. 赛题需要的新能力先做 measurement；如果只是比赛专属展示需求，留在本目录。
6. 主项目 `src/` 只有满足 `competition/README.md` 的回写 Gate 才允许修改。
7. 不修改当前主项目 F 阶段优先级来追比赛细节。

## 6. 当前文档

- [能力复用矩阵 v1](docs/CAPABILITY_REUSE_MATRIX_v1.md)
- [最小执行路线 v1](docs/MINIMUM_EXECUTION_ROUTE_v1.md)
- [参赛再评估与官方资料核查（2026-10-11）](docs/参赛再评估与官方资料核查_20261011.md)：已读取官方规则、赛程与模板；建议有条件轻量参加创新赛，尚未恢复参赛执行。

## 7. 赛题信息边界

当前目录固化的是内部关注方向与项目复用策略；上文方向尚未核验为官方赛题名称。

2026-10-11 已读取官方规则、赛程概述与参考模板，详见上述核查记录。规则支持创新赛自拟题目、每队 2–5 人，报名截止暂只精确到 10 月下旬。完整赛题、评分权重、精确报名/作品截止日、具体团队资格与报名协议仍需核验；不能把未确认项写成执行约束。HUMAN_DEFERRED 状态保持。
