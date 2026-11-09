# Competition Workspaces / 比赛工作区

> 原则：主项目提供能力，比赛工作区选择、组合、验证和包装能力；任何比赛都不能反向定义主项目架构。

## 1. 总体关系

```text
agentic-payment-trust-lab
        │
        ├── Canonical Facts
        ├── Trust Core
        ├── Runtime Gate
        ├── Payment Lifecycle / Recovery
        ├── Evidence / Trace / Replay
        └── Harness / Evaluation
                 │
                 ├── competition/payathon-2026/
                 │      ├── Agent Pay
                 │      └── Machine Pay
                 │
                 └── competition/jinmi-cup-2026/
                        └── 金融智能体能力增强与安全验证
```

## 2. 强制规则

1. **主项目优先**：`CURRENT.md`、`PROJECT_BOTTLENECK_MAP.md` 和主项目能力路线不因比赛改写。
2. **比赛只做 Profile**：每个比赛只选择与赛题最相关的能力组合、场景、Demo、评测和提交材料。
3. **Core 不复制**：比赛目录不得复制一套新的 Trust Core / Payment State Machine。
4. **Adapter 优先**：赛事协议、平台、SDK、数据格式首先通过 Adapter 接入现有 Canonical Facts。
5. **比赛专属代码隔离**：赛题专属 UI、Demo、fixture、submission assets 优先留在对应比赛目录。
6. **回写必须有 Gate**：只有跨比赛/跨协议重复出现的协议中立缺口，且有失败证据、能做 before/after 验证，才允许进入主项目。
7. **能力声明以证据为准**：比赛包装不能把本地/离线能力写成生产、监管合规或完整协议一致性。
8. **比赛结束可删除**：删除整个比赛目录后，主项目仍应保持完整、可运行、可理解。

## 3. 当前比赛

### Payathon 2026

目录：`payathon-2026/`

主要复用：

- Delegated Authority；
- Payment Binding；
- Runtime Gate；
- Payment Lifecycle / Recovery；
- Authoritative Trace；
- AP2 / x402 / WebShop 适配经验。

产品验证面：

- Agent Pay；
- Machine Pay。

### 金密杯 2026

当前状态：`HUMAN_DEFERRED`（2026-10-11）。保留路线，暂缓参赛投入；下一优先方向为外部商城交易链适用性与交易团队需求核验，以项目地图 r74 为准。

目录：`jinmi-cup-2026/`

当前关注赛题方向：

> 面向金融应用的智能体能力增强与安全验证工程实践。

主要复用：

- Security Harness；
- Identity / Credential；
- Authorization / Delegation；
- Transaction / Payment Binding；
- Context / Tool Integrity；
- Runtime Policy / Gate；
- Replay / Idempotency；
- Attack Overlay / Adversarial Eval；
- Evidence / Trace / Responsibility；
- Payment Lifecycle / Recovery。

金密杯重点是“**怎么证明金融 Agent 在攻击、越权、篡改和异常条件下仍然受控**”；Payathon 重点是“**如何把同一 Trust Core 放进真实支付产品和协议链路**”。

## 4. 回写主项目判定

```text
比赛中发现问题
      ↓
是否只是赛题/平台/协议私有要求？
      ├─ 是 → 留在比赛目录
      └─ 否
          ↓
是否在第二个独立消费者/比赛/协议中重复出现？
      ├─ 否 → 继续观察
      └─ 是
          ↓
是否影响协议中立 Trust Contract？
      ├─ 否 → Adapter / Profile 解决
      └─ 是
          ↓
是否有可复现失败 + bounded repair + before/after evidence？
      ├─ 否 → measurement first
      └─ 是 → 交 Evaluator 冻结后，才进入主项目
```
