# 数字人民币、IMF与BIS代币化路线辨析

## 结论

数字人民币、IMF 的 Tokenized Finance（代币化金融）框架和 BIS 2026 的“稳定币 vs 代币化存款”路线值得放在同一张比较图里研究，但不能把它们强行合并成同一个制度方案。

当前最稳妥的处理仍是拆成：**官方事实 / 国际研究框架 / 受控试点证据 / 待证主张**。

| 层级 | 当前可确认内容 | 项目处理 |
|---|---|---|
| 人民银行官方基线 | 数字人民币定位 M0，是央行负债，实行中心化管理和双层运营；可加载不损害货币功能的智能合约 | 作为中国零售 CBDC 基线 |
| IMF 研究框架 | Tokenized Finance 讨论 wCBDC、代币化存款、稳定币及受公共信用支持的安排，并强调结算资产、法律终局性、流动性和代码治理 | 作为比较框架，不替任何国家作制度分类 |
| BIS 2026 货币信任框架 | 重点比较 Singleness（单一性）、Interoperability（互操作性）、Financial Integrity（金融完整性）和央行货币结算锚；认为当前稳定币设计不适合作为通用货币体系核心，更看好建立在两层银行体系上的代币化存款 | 用于校准 Settlement Asset / Finality 边界，不把 BIS 路线等同任何国家既定政策 |
| Project Agorá 受控实证 | 代币化商业银行存款与代币化央行准备金可在共享可编程平台上进行多币种、原子化批发跨境结算；2026 年 7 月已完成真实价值测试 | 证明“银行负债 + 央行结算锚 + Tokenisation”已进入受控实证，不等于成熟生产生态 |
| CBMT 沙盒 | 各参与银行分别发行本行存款代币，通过 Bridge 做跨银行 / 跨网络互操作；官方还列出带 Agent 身份与人工确认的跨境 B2B Agentic Payment 场景 | 作为 Cross-Rail / Cross-Institution 的未来实验样本；不把沙盒写成生产网络 |
| Project Hangang Phase II | 商业银行存款代币面向客户，机构型央行数字货币支撑底层结算，并继续测试可编程支付 | 用于验证 Payment Instrument 与 Final Settlement Anchor 分层，不直接外推其他国家制度路线 |
| 俄罗斯数字卢布 2026 扩围 | 零售 CBDC 平台自身存在额度、准入和交易规则 | 用于明确 Agent Trust Policy 与 Rail / Wallet Policy 分层；`ALLOW` 不等于支付一定被接受 |
| 待证主张 | “数字人民币2.0”“数字存款货币”“CLT+分布式账本技术（DLT）双账本”“按机构属性形成广义/狭义银行双轨 sCBDC”等 | 只有取得人民银行正式文件和清晰定义后才能升级为事实 |

## BIS 2026 带来的关键校准

德科斯在 2026-08-28 Jackson Hole 演讲中强调：货币不仅是技术对象，更依赖共同记账单位、单一性、流动性弹性、互操作性和金融完整性。

这对项目最重要的含义不是“稳定币一定失败、代币化存款一定成功”，而是：**技术上同样写着 `100 USD` 的支付对象，可能对应完全不同的负债主体、兑付机制、最终结算锚和异常恢复路径。**

因此以下对象不能混为一层：

```text
Unit of Account（记账单位）
        ↓
Payment Instrument（支付工具）
        ↓
Payment Rail / Network（支付轨道 / 网络）
        ↓
Settlement Asset（结算资产）
        ↓
Issuer / Obligor（发行方 / 负债主体）
        ↓
Finality / Redemption / Recovery（最终性 / 赎回 / 恢复）
```

稳定币、代币化存款和央行数字货币都可以使用 Tokenisation（代币化）或 Programmability（可编程性），但“用了相似技术”不能推出“具有相同货币属性或法律属性”。

## 对实验的实际影响

1. 将智能体（Agent）委托、商务订单、支付授权、支付轨道和结算资产拆开，不能把“可编程货币”当成解决全部授权问题的捷径。
2. 卡、账户、数字人民币、代币化存款和稳定币只作为未来可替换实验变量；当前第一阶段不接任何真实资金轨道。
3. Cross-Rail（跨支付轨道）未来要拆成两层：上层验证 Identity / Authority / Binding / Budget / Idempotency / Evidence 等 Shared Trust Invariants（共享信任不变量）；下层允许不同轨道拥有不同 Finality / Query / Redemption / Recovery 语义。
4. 对实时 / 原子结算增加流动性、撤销、错误恢复、状态冲突和紧急中断测试，验证“减少摩擦也减少缓冲”的风险。
5. 智能合约只执行确定规则；概率性智能体负责提出行动，不能直接绕过 Runtime Gate 执行不可逆资金转移。
6. BIS 提到的 AML/CFT、自托管钱包和钱包间转移风险，当前只作为 External Authoritative Compliance Fact（外部权威合规事实）的未来输入，不在本项目内部自造 AML 规则或声称生产合规能力。
7. 研究结论必须标注来源级别，避免用相似架构强行推出同一法律属性，也避免把 BIS 管理层观点写成全球央行统一监管结论。
8. 保持 `Trust Decision = ALLOW ≠ Payment Rail Accepted ≠ Settlement Final ≠ User Task Success`：Agent 授权判断、支付网络规则、结算终局性和用户任务完成必须分别取证。

## 对当前主线的影响

**不改变 B-12 / H-18。** 当前项目仍先完成 Same-Journey Payment Lifecycle（同一旅程支付生命周期）中 UNKNOWN → Query Recovery、履约失败和状态冲突的连续性测量。

BIS 材料反而强化了一个判断：Payment Finality / Recovery（支付最终性 / 恢复）是未来银行卡、账户、稳定币、代币化存款等多种轨道都需要的共同底座，所以应该先把这一层测扎实，再进入 Cross-Rail。

```text
当前 B-12 / H-18
→ 先测生命周期连续性
→ 固化 Finality / Recovery 的公共控制边界
→ 未来 Cross-Rail 升为第一瓶颈
→ 再把 Settlement Asset / Finality 差异作为实验变量
```

## 统一原则

> **Agent 支付控制解决“这笔钱该不该花”；支付轨道解决“钱怎么走”；结算资产解决“最终收到的到底是什么钱、由谁保证、什么时候真正结束”。**

详细来源与项目映射见：

- [德科斯“稳定币与代币化存款”对项目的影响分析](../reference/05_产业与机构资料/bis/德科斯_稳定币与代币化存款_项目影响分析_20260908.md)
- [数字货币三路线与可信基础设施：项目影响分析](../reference/02_支付与银行基础设施/数字货币三路线与可信基础设施_项目影响分析_20260908.md)
