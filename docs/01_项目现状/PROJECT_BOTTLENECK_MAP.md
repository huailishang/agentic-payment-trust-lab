# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-09-12-r36
Last reviewed: 2026-09-12
Map owner: Evaluator / Human Task Owner  
Status: ACTIVE  
> 当前新任务统一使用 `evaluator-executor-workflow/v2.2`，按“瓶颈—假设—同基线实验—保留或回滚”闭环推进。

## Project outcome / 项目结果

### 可观察的项目结果

在本地、离线、可重置的实验边界内，证明智能体代表用户完成购物与支付任务时：

```text
用户授权
→ Agent / 外部环境产生动作和事实
→ 订单、支付请求、身份、来源和状态持续绑定
→ 每个副作用前经过统一治理闸门
→ 正常任务正确完成
→ 越权、冲突、缺证据任务被阻断或要求确认
→ 支付、履约、恢复和最终状态可回放、可解释、可独立复核
```

### 主要用户与业务价值

- 给开发者提供一个协议中立的智能体支付可信实验室；
- 用可运行环境说明“为什么允许、为什么阻断、为什么需要确认”；
- 用外部任务和固定评测避免“自己出题、自己判卷”；
- 为后续接入 WebShop、x402、UCP / ACP、银行沙箱提供可复用的治理和评测底座。

### 风险容忍度与禁止失败

以下失败采用零容忍守护线：

```text
错误放行产生受控 callback 或支付副作用
漏掉必须的人工确认
重复下单、重复付款或 UNKNOWN 状态下盲目重试
低可信网页、LLM 或工具事实静默覆盖用户确认事实
动作、订单、请求、支付、Agent、Executor 或授权错绑
没有前置治理证据的副作用
```

### 当前评测边界

包含：

- 本地 Python 确定性规则与回归；
- S01—S13、M5、PayBench、AP2、Attack Overlay；
- P1—P6 Trust Control Plane；
- x402 离线一致性；
- WebShop 上游预检、small smoke、Commerce Adapter、Buy Now Gate、Payment / Fulfilment Sidecar；
- 已验收的 Governed Action、Fact Lineage、Payment Lifecycle / Recovery、Remediation / Closure、Authoritative Trace Consumer / Player；
- 当前 B-15A Signed Instruction Verification（签署指令验证）的第一个有界能力实验：协议中立验证事实 + ACP 2026-04-17 Webhook HMAC consumer（消费者）。

明确不包含：

- 真实资金、真实信用卡或生产支付网络；
- 生产商户、生产凭证、主网资产；
- 完整 Agent PKI 或生产身份认证；
- 未授权的外部 API、测试网、钱包和网络调用；
- 对生产安全、监管合规或业务合法性的证明。

## Global capability roadmap / 全局能力路线

评估者以后先从这 6 个大阶段定位项目，再看具体 `B-* / H-*`。任务编号不是路线，能力阶段才是路线。

```text
A. 评测与治理底座                  [已完成]
→ B. 授权、绑定、来源、执行前治理   [已完成]
→ C. 支付生命周期、恢复、补救证据链 [已完成]
→ D. 责任归因与可消费审计链         [已完成]
→ E. 主体真实性 / 凭证 / 签署指令   [当前]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权与环境约束]
```

| 阶段 | 要解决的核心问题 | 当前代表能力 / 证据 | 状态 |
|---|---|---|---|
| A 评测与治理底座 | 怎么知道一次修改真的让项目变好，而不是测试数量变多 | 12 项项目基线、GESR、零副作用守护线、Evaluator / Executor、L2/L3 独立复核 | `CLOSED` |
| B 授权、绑定、来源、执行前治理 | Agent 能不能在明确授权、正确对象、可信来源下安全触发副作用 | P1 Delegated Authority、P2 Payment Binding、P3 BOUND Identity、P4 Context Policy、Governed Action、Fact Lineage、重复付款保护 | `CLOSED` |
| C 生命周期、恢复、补救证据链 | 支付后 UNKNOWN、履约失败、退款、争议、原交易错绑时能不能安全恢复并留下连续证据 | Payment Lifecycle / Recovery、Finality、Remediation / Closure、Product Authoritative Trace `10/12`，B-12/B-13 阶段关闭 | `CLOSED` |
| D 责任归因与可消费审计链 | 事后能不能回答“谁做的、依据什么、发生了什么”，并让 UI / 审计消费者稳定读取 | Action Origin、Same-Journey Responsibility、Consumer、Read Model、Player；H-23 五分支消费 `5/5` | `CLOSED` |
| E 主体真实性 / 凭证 / 签署指令 | ID 对得上之后，能否证明执行者真的持有对应凭证/密钥，授权/指令真的由对应主体签署 | H-24 已证明 P3 凭证/持有证明与 AP2/ACP 签名验证是两类真实缺口；B-15A 先做 Signed Instruction Verification，B-15B 凭证/持有证明后置 | `CURRENT` |
| F 外部真实协议 / 网络接入 | 本地机制在真实 SDK、钱包、测试网、身份提供方、facilitator 下是否仍成立 | x402 仅离线一致性；真实 AP2/ACP/x402 网络、真实凭证/签名、银行沙箱尚未进入 | `DEFERRED` |

### 已完成的能力，不再默认继续扩

- 项目级同基线评测与独立复核；
- Delegated Authority（委托授权）、Confirmation Binding（确认绑定）；
- Order / Request / Payment 连续 Binding（绑定）；
- Agent / Executor `DECLARED / BOUND` 身份保证边界；
- Context / Tool Integrity（上下文 / 工具完整性）与来源策略；
- Idempotency / Replay（幂等 / 重放防护）、UNKNOWN 查询恢复、支付最终性 / 状态冲突；
- Governed Action（受治理动作）与 Fact Lineage（事实血缘）；
- Same-Journey Responsibility（同旅程责任链）；
- Payment Lifecycle / Recovery（支付生命周期 / 恢复）；
- Refund / Dispute / Closure（退款 / 争议 / 结束状态）证据连续性；
- Product Authoritative Trace（产品权威轨迹）的代表性覆盖；
- Consumer / Read Model / Player（消费器 / 读取模型 / 播放器）只读审计消费链。

### 当前与后续能力

H-24 已回答阶段 E 的第一层问题：真实性缺口真实存在，但不是一个大而全机制，应拆为：

```text
B-15A Signed Instruction Verification（签署指令验证）【当前】
  → AP2 HP / AP2 HNP / ACP 三个独立入口重复出现

B-15B Credential / Possession Verification（凭证 / 持有证明验证）【后续】
  → P3 当前最高 BOUND，尚无 credential validity / possession verifier
```

当前先进入 B-15A 的最小 capability package（能力建设包）：建立协议中立 `SignedInstructionVerificationFact`，用 ACP 2026-04-17 `Merchant-Signature` HMAC Webhook 作为第一个真实消费者和负例。AP2 SD-JWT、P3 `VERIFIED`、完整 PKI / 钱包 / Passkey / 区块链仍不进入本包。

阶段 F 只有在出现明确外部消费者、测试环境和授权后才进入：真实 SDK / 身份提供方 / 钱包 / 测试网 / facilitator / 银行沙箱。它不是当前 B-15A 本地能力实验的默认下一步。

### 第一瓶颈选择公式 / 决策顺序

```text
项目最终目标与零容忍风险
→ 哪个大阶段还没有代表性闭环
→ 该缺口影响范围 / 风险严重度
→ measured / estimated / unknown 的证据强度
→ 是否有重复共同失败，而不是单一 Case
→ 修复成本、复杂度、外部授权依赖
→ 与 WATCH / DEFERRED 备选项比较 expected project value（预期项目价值）
→ 选第一瓶颈
```

当前 B-15 优先于几个主要备选项的原因：

- B-03 Product Trace 剩余 T05/T06 只是 `2/12` 未覆盖，已有 `10/12` 代表性覆盖且不是当前零容忍失败，保持 `WATCH（观察）`；
- B-04 Fresh Unseen Agent 行为仍有长尾，但当前已能提供真实行为给 Trust 链，不再是支付信任链的第一断点，保持 `WATCH（观察）`；
- B-05 Data Minimization（数据最小化）仍有 PayBench 缺口，但当前影响范围小于“执行主体/签署指令真实性”，保持 `WATCH（观察）`；
- B-06 真实 SDK / testnet / network 依赖额外授权与环境，保持 `DEFERRED（延期）`；
- B-15 同时出现在 P3、AP2、ACP 多个独立入口，直接关系“谁在代表用户行动”和“授权是否真实”，因此先测量其是否为共性高风险安全缺口。

## End-to-end capability chain / 端到端能力链

```text
用户任务 / 授权
→ 外部协议、Agent 或 WebShop 环境
→ Commerce / Protocol Adapter
→ Governed Action + Explicit Facts
→ Authority / Order / Request / Payment / Identity Binding
→ Source Registry / Fact Lineage
→ Context Policy + Runtime Authorization Gate
→ ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE
→ Controlled Action Seam
→ Payment / Query / Fulfilment / Recovery
→ Authoritative Trace / Replay
→ M5 + 外部任务 + 项目级影响评测
```

## Measurement basis / 测量基础

### 已固定或已独立复核的组件基线

| 边界 | 当前事实 | 性质 | 证据入口 |
|---|---:|---|---|
| S01—S13 正式入口 | 13/13 PASS | measured | `python run_experiment.py` 与历次独立复核证据 |
| Governed Payment Action 类型边界 | 18/18 动作矩阵，13/13 专项，31/31 Runtime Gate | measured | `docs/05_任务交接/P9_GOVERNED_PAYMENT_ACTION_OBJECT_TYPE_BOUNDARY_REPAIR_V1/REVIEW.md` |
| 全量 unittest | 658/658 PASS | measured | `P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/REVIEW.md` |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 8/10 可执行 | measured | `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` |
| x402 离线一致性 | 第一轮已完成 | measured but bounded | P8-A 任务合同、报告与复核 |
| 多步骤自主购物项目级指标 | 12 项固定任务；GESR 9/12；重复/禁止副作用 0/12；callback 匹配 12/12；产品权威轨迹 10/12；三次结果一致 | measured | `P9_WEBSHOP_LIFECYCLE_EVIDENCE_CONTINUITY_CLOSURE_V1/REVIEW.md` |

### 主要指标

`Governed End-to-End Task Success Rate`：

```text
同时满足以下条件的固定端到端任务数
────────────────────────────
固定端到端任务总数
```

单个任务必须同时满足：

1. 最终环境状态正确；
2. 四态决策正确；
3. callback / 副作用次数正确；
4. 必要确认没有遗漏；
5. 动作、授权、订单、请求、支付、身份和来源证据连续；
6. 轨迹与 reason codes 能解释最终结果。

### 守护指标

| 指标 | 目标线 |
|---|---:|
| 错误放行率 | 0 |
| 漏人工确认率 | 0 |
| 重复副作用率 | 0 |
| 禁止状态写入率 | 0 |
| 来源链完整率 | 100%（在纳入 lineage 的任务内） |
| 权威轨迹完整率 | 100%（在纳入 trace 的任务内） |
| 决策—原因一致率 | 100% |
| 既有正式入口 | 不低于 13/13 |
| 既有全量回归 | 不允许出现新增失败 |

### 测量命令或证据路径

当前组件回归可复用：

```text
python run_experiment.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

项目级端到端基线已冻结为 12 项固定任务和 `run_project_impact_baseline.py`，可用于同 target 的 capability experiment（能力实验）前后比较；当前 Product Trace 已达 `10/12`，剩余 T05/T06 轨迹缺口降为 `WATCH（观察）`。B-11—B-14 已把责任归因、支付生命周期 / 恢复、补救 / 结束状态以及 Consumer / Player（消费器 / 播放器）代表性链路阶段关闭；当前主线已经切换到 B-15 Actor Authenticity / Signed Instruction Verification（主体真实性 / 签署指令验证），先用 H-24 做跨 P3 + AP2 + ACP 的 measurement-only（只测量）验证。

### 已知盲区

- 当前测试数量增长不能直接等价为项目能力增长；
- H-14 当前 `5` 个 synthetic/metamorphic probe（合成 / 变形探针）只覆盖**已经暴露出来的规格失败机制**，不是 option-grounding（规格匹配）能力全集；即使达到 `5/5`，也只能证明当前假设在冻结代表样本上成立，不能声称“规格问题已经测全”；
- 规格能力仍存在未系统发现的组合空间，例如同义表达、大小写/空格/标点变化、单位与数字格式、多个干扰选项、多个规格组、缺失规格、歧义候选、页面顺序变化、部分匹配与冲突请求；这些未知细节不能靠人工逐条穷举，而要用 property/metamorphic testing（性质 / 变形测试）系统发现；
- 已揭晓 Blind Holdout 只能作为回归证据；任何新的“泛化成立”结论都必须来自下一轮产品修改前冻结的 fresh unseen evidence（新鲜未见证据）；
- WebShop 已形成多个离线切片，但还没有冻结统一的多步骤 Agent 任务集；
- 当前没有生产网络、真实支付、真实身份和真实 LLM 行为；
- PayBench D1 数据最小化仍未覆盖；
- 当前多数结果是组件或局部纵向切片结果，不是统一项目指标；
- 冻结 runner 的 `trace_provenance_separated` 诊断只在“产品轨迹不存在”时返回真；T10 同时存在产品轨迹与评估器 Replay 后产生误报。原始来源字段已明确分离，下一包先修复该测量诊断，再扩展第二个产品轨迹场景。

## Bottleneck register / 瓶颈登记表

| ID | 阶段 | 可观察失败 | 估计影响范围 | 证据 | 信心 | 状态 |
|---|---|---|---:|---|---|---|
| B-01 | 项目级评测 / V3 环境 | 固定 12 项任务、统一命令、独立副作用护栏和轨迹来源分类已经建立并独立复核 | 所有未来 capability experiment 的 100% | P9 Measurement Integrity Repair REVIEW：三次一致、15/15 专项、428/428 全量 | high | RESOLVED / BASELINE_ESTABLISHED |
| B-02 | Fact Lineage | 组件级来源传播已通过，但尚未测量它在固定端到端任务中减少了多少来源丢失、错误放行或证据缺口 | 所有包含派生事实的外部环境任务；具体比例 unknown | P9 Fact Lineage REVIEW：16/16 矩阵、12/12 专项、Overlay 投影不变 | medium | WATCH / IMPLEMENTED_UNMEASURED |
| B-03 | Authoritative Trace | T01/T02/T03/T04/T07/T08/T09/T10/T11/T12 已形成 `VALID` 产品权威轨迹；仅 T05/T06 尚未公开产品轨迹 | 剩余 2/12 固定任务 | H-20 Evaluator REVIEW：通用 failed-fulfilment Profile 使 T11 Product Trace 真实进入 `VALID`，Product Trace `9/12→10/12`、GESR `8/12→9/12`，L3 `7/7 PASS`、658/658 全量 | high | WATCH / REPRESENTATIVE_COVERAGE_SUFFICIENT |
| B-08 | Trace Consumer / UI Read Model | 通用只读 Consumer 与 Trace Player 已贯通：T01/T02/T07/T10 四类代表轨迹均可由同一 Read Model 进入同一只读 UI，事件、relation、source binding 可机械回指 | 当前 4 个已验证结构族；UI-ready 4/4 | P9 Authoritative Trace Player REVIEW：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready 0/4→4/4 且旧轨迹/UI/Consumer hash 不变 | high | RESOLVED / TRACE_PLAYER_READY |
| B-09 | WebShop Journey 多事实源合同 | WebShop runtime、experiment context、Commerce Adaptation、payment authoritative trace 四类证据已能在一个 deterministic Journey Read Model 中分层保存并机械关联；错绑 fail closed | 第一轮 1 条固定 WebShop smoke/T01 正常购买路径，Journey source-classified 1/1 | P9 Journey Fact Source Read Model REVIEW：27/27 专项、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；17 条 correlation 全 true，来源边界不变 | high | RESOLVED / SOURCE_CLASSIFIED_JOURNEY_READY |
| B-10 | WebShop Journey UI composition | 固定脚本 Journey 已能按来源安全进入一个 deterministic Player；accepted-input schema/source-classification 两个反例已全部 fail closed | 第一轮固定脚本 Journey UI-ready 1/1 | Journey Player 父任务合法路径 1/1；accepted-input repair L2/L3 4/4、Player 27/27、两个反例 4 个入口组合全拒绝 | high | RESOLVED / SAFE_JOURNEY_PLAYER_READY |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 已形成真实多步骤 autonomous behavior、H-12 `5/5` 开发/回归证据、Blind Holdout `3/8` 泛化边界、H-14 通用修复与 Systematic Discovery `19/24`；已证明 Agent 可产生真实行为，也证明意图/规格存在难穷举长尾 | 当前价值已从“继续提高购物理解准确率”转为向信任链提供真实 Agent 行为与已知限制；H-15 `2/5` probe 保留为回归资产，不再阻塞主线 | H-14 `PASS / IMPROVED`；Systematic Discovery `PASS / NOT_APPLICABLE`、L3 `4/4 PASS`、48 observations all reproducible、safety hits 0；H-15 在 Executor 开始前 superseded | high | WATCH / BEHAVIOR_BASELINE_ESTABLISHED |
| B-11 | Action Origin / Responsibility Trace | H-13 已完成 Action Origin `0/5→5/5`；H-17 修正跨 policy 版本基线后，同一 autonomous journey 的 Agent→Order/Request→Runtime→offline Payment/Fulfillment→Trace 连续关联 `8/8`，五类 origin 可投影 | 代表性 happy-path responsibility chain 已闭合；不再继续扩 Action Origin 字段 | H-17 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `8/8 PASS`、same-journey `8/8`、657/657 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-12 | Same-Journey Payment Lifecycle / Recovery Continuity | H-20 已将 H-18 三个同类证据链断点统一闭合：semantic `4/4` 保持，continuity `1/4→4/4`，四条 Trace 均 VALID 且 Action Origin 可投影 | L5-L7 支付执行、状态、恢复、冲突与履约的代表性同旅程证据连续性已闭合 | H-20 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`、Product Trace `9/12→10/12`、GESR `8/12→9/12`、658/658 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-13 | Same-Journey Remediation / Closure Continuity | H-21 定位 5/5 共同补救证据断点；H-22 以一个通用 extension 将 remediation evidence `0/5→5/5`、continuity `0/5→5/5`；H-22R 又使 public runtime fingerprint 与 live validator contract 完全一致，R05 全程保持 `INVALID` | 支付后退款/争议/原交易绑定/Closure 的代表性同旅程证据生产与合同身份已闭合，不再继续扩 R01-R05 或补救产品字段 | H-22R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；effective projection/profile/runtime hash 全部与 live contract 一致；H-22 复验 SHA-256 完全相同；662/662、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-14 | Remediation Accountability / Closure Consumption | H-23 已对冻结 5 个补救分支完成现有 Product Trace → Consumer → Read Model → Action Origin → Player 系统测量；Consumer/Player/continuity 均 `5/5`，R05 `INVALID` 原样可见且无虚假 payment relation | 代表性退款/争议/原交易错绑证据已经可被现有通用只读消费链稳定消费，无需新增 Consumer/Player 特判 | H-23 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `7/7 PASS`，first breakpoint=`NONE:5`，51/51 专项、662/662 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-15 | Actor Authenticity / Signed Instruction Verification | H-24 已系统测量 6 个探针：P3 三条路径均只到 `BOUND`；AP2 HP/HNP 与 ACP 三个独立入口均显式保留签名/真实性 `not_verified`。结论不是一个大而全模块，而是 B-15A Signed Instruction 与 B-15B Credential/Possession 两类机制族 | B-15A 直接影响授权/订单/Webhook 指令的真实性与完整性，已跨 3 个独立入口重复；B-15B 影响执行主体凭证/持有证明，目前主要证据集中在 P3 | H-24 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / CONTINUE`，L3 `7/7 PASS`，6/6 deterministic，product `VERIFIED=0/6`，AP2/ACP 三入口 signature gap 重复；34/34 专项、662/662 全量、真实副作用 0 | high | ACTIVE / B-15A CAPABILITY_EXPERIMENT |
| B-05 | 数据最小化 | PayBench D1 两题不可执行，缺少数据披露事实与必要性判断 | PayBench 2/10，后续收货和身份任务 | measured：PayBench 8/10 可执行 | high | WATCH |
| B-06 | 真实身份与外部协议 | 当前最高身份保证为 BOUND，未覆盖真实签名、SDK、facilitator 和网络故障 | 测试网、生产接入；当前主线影响有限 | measured boundary：P3 / P8 文档 | high | DEFERRED |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-15

### 当前判断

H-24 已由 Executor L2 与 Evaluator L3 独立复核通过：

```text
Task verdict: PASS
Project impact: NOT_APPLICABLE
Continuation: CONTINUE
L3: 7/7 PASS
six probes: 6/6
repeat=2 deterministic: 6/6
product VERIFIED authenticity: 0/6
P3 P01-P03: VALID / BOUND / ALLOW
explicit signature/authenticity not_verified: P04 / P05 / P06
cross-surface repeated signature mechanism: true
focused regression: 34/34
full unittest: 662/662
real payment / credential / key / signature / network: 0
```

H-24 证明 B-15 是真实高风险边界，但也证明不能把它做成一个“万能身份模块”。当前分成：

- **B-15A Signed Instruction Verification（签署指令验证）**：AP2 HP、AP2 HNP、ACP 三个独立入口重复出现，升为当前第一子瓶颈；
- **B-15B Credential / Possession Verification（凭证 / 持有证明验证）**：P3 仍最高 `BOUND`，是真实缺口，但当前独立消费者证据更少，后置。

ACP 2026-04-17 官方 Webhook 合同已经给出明确 signer / signed payload / key relation（签署者 / 被签内容 / 密钥关系）：`Merchant-Signature: t=<unix>,v1=<64_hex>`，HMAC-SHA256 签 `timestamp + "." + raw_body`，并要求时间窗验证。因此当前不再继续 measurement-only，而进入第一个有界 capability experiment（能力实验）。

### 当前主线

```text
A-D【STAGE CLOSED】
        ↓
E. B-15 Actor Authenticity / Signed Instruction Verification【CURRENT】
        ↓
H-24 cross-surface measurement【PASS】
        ├─ B-15A Signed Instruction：AP2 HP + AP2 HNP + ACP【PRIMARY】
        └─ B-15B Credential / Possession：P3【SECONDARY】
        ↓
H-25 Signed Instruction Verification Fact + ACP Webhook HMAC【NEXT】
        ├─ protocol-neutral verification fact
        ├─ generic HMAC-SHA256 verifier
        ├─ ACP Merchant-Signature parser / consumer
        ├─ valid + tamper + wrong-key + stale + malformed/missing negatives
        └─ signature VALID != business ALLOW / identity VERIFIED
        ↓
根据真实 consumer 复用价值决定：接 AP2 / STOP / SWITCH
```

B-03 T05/T06 Product Trace、B-04 Fresh Unseen、B-05 Data Minimization 继续 `WATCH（观察）`；B-06 真实 SDK/testnet/network 继续 `DEFERRED（延期）`。H-25 仍完全本地离线，不恢复 B-06 网络授权。

## Active hypothesis / 当前假设

Hypothesis ID: H-25
Hypothesis status: `ACTIVE / SIGNED_INSTRUCTION_FACT_ACP_FIRST_CONSUMER`

### 假设

> H-24 已证明跨协议重复的 Signed Instruction（签署指令）验证缺口。当前最小有价值 principal change（主要变化）不是建设完整身份/密钥平台，而是建立一个协议中立、可回放、不会泄露 secret/payload 的签署指令验证事实，并让 ACP 2026-04-17 Webhook HMAC 成为第一个真实协议消费者。如果同一事实模型能表达合法签名、篡改、错误密钥、过期时间戳和缺失/畸形证据，同时保持“signature VALID 不等于业务 ALLOW / actor VERIFIED”，则 B-15A 获得第一个可复用能力锚点。

H-25 是 `capability_experiment（能力实验）`，只建设本地离线 verification fact（验证事实）与 ACP HMAC consumer（消费者）；不实现 AP2 SD-JWT，不升级 P3 `VERIFIED`，不引入网络、生产密钥、钱包或 PKI。

### 冻结主要变化

唯一主要变化：新增协议中立 `SignedInstructionVerificationFact` + HMAC-SHA256 verifier，并由新 ACP Webhook adapter 解析官方 `Merchant-Signature` 后真实消费该 verifier。

```text
raw_body + Merchant-Signature + test-only secret + observed_at
        ↓
ACP parser：t=<unix>,v1=<64_hex>
        ↓
signed message = timestamp + "." + raw_body
        ↓
protocol-neutral HMAC-SHA256 verifier
        ↓
SignedInstructionVerificationFact
        ↓
VALID / INVALID / MISSING_EVIDENCE
```

### 成功信号

```text
ACP signed-webhook executable coverage: 0/6 → 6/6 frozen cases
valid signature → VALID
body tamper / wrong key / stale timestamp → INVALID
missing or malformed evidence → MISSING_EVIDENCE or INVALID per frozen contract
raw secret / full raw body never persisted in verification fact
signature VALID does not emit Payment ALLOW or Identity VERIFIED
AP2/P3 product behavior unchanged
H-24 result remains byte-stable when revalidated
project guardrails unchanged
```

## Candidate experiments / 候选实验与设计任务

| 优先级 | 假设 / 任务 | 主要变化 | 同基线比较 | 预期收益 | 成本 / 风险 |
|---:|---|---|---|---:|---|
| 1 | H-25 Signed Instruction Verification Fact + ACP Webhook HMAC【当前】 | 一个 principal change：协议中立验证事实 + 通用 HMAC-SHA256 verifier + ACP 2026-04-17 consumer | H-24 ACP `order_webhook_signature_not_verified` / 可执行签名验证 `0/6` → 冻结六案例语义 `6/6` | 让 B-15A 第一次从 limitation 进入真实可执行、可负测的能力 | 中；只用测试 secret，本地离线，不接 AP2 SD-JWT |
| 2 | AP2 Signed Mandate consumer【条件触发】 | 只有 H-25 证明通用 fact 有复用价值，且能冻结真实 AP2 cryptographic fixture / verifier 语义后才进入 | ACP first consumer → second protocol consumer | 验证协议中立层是否真正跨协议复用 | 中到高；SD-JWT / credential 复杂，禁止凭占位 fixture 假验证 |
| 3 | B-15B Credential / Possession + B-03/B-04/B-05 | H-25 后根据影响和证据重排 | secondary gaps | 保留执行主体凭证、剩余轨迹、Agent 长尾、数据最小化问题 | 低到中 |

## Reassessment triggers / 重新排序触发器

只有发生以下情况才更新或重排地图：

- B-01 的项目级任务集和主指标已经可重复测量；
- 当前 Fact Lineage 独立复核发现新的高影响错误放行；
- 两到三轮相同假设没有可测收益；
- 失败从来源传播转移到轨迹、Agent 行为或环境状态；
- 项目目标、外部授权或测试环境发生变化；
- PayBench、WebShop、x402 或其他外部评测提供新的实测结果。

不得因为“某个模块容易实现”就把它升为第一瓶颈。

## Revision log / 修订记录

| Revision | 日期 | 证据或原因 | 瓶颈变化 | 假设变化 |
|---|---|---|---|---|
| `2026-08-03-r1` | 2026-08-03 | 根据项目中控、整体修正计划、验证体系路线、ArbiterOS 吸收方案、P9 已复核任务和 v2.1 skill 初始化 | 首次建立；B-01 定为固定端到端评测边界缺失 | H-01 定为项目级基线设计 |
| `2026-08-03-r2` | 2026-08-03 | P9 Fact Lineage 独立复核 PASS：16/16 矩阵、12/12 专项、413/413 全量，Overlay 策略投影不变 | B-01 仍为第一瓶颈；B-02 更新为组件已实现、项目影响未测量 | H-01 不变，下一包建立统一项目基线 |
| `2026-08-03-r3` | 2026-08-03 | P9 Project Impact Baseline 独立复核 REJECTED：T10 的 expected callback=1 掩盖已有成功付款后的重复副作用；5 个 VALID trace 均为评测器合成 Replay | B-01 保持第一瓶颈并进入测量完整性修复；B-03 更新为产品轨迹覆盖率未测量 | H-01 暂不判定，先修复测量语义后重新建立可信基线 |
| `2026-08-03-r4` | 2026-08-03 | Measurement Integrity Repair 独立复核 PASS：可信基线 GESR 0/12、重复副作用 1/12、产品轨迹 0/12，三次一致 | B-01 完成；新增 B-07 并升为第一瓶颈，B-03 为竞争瓶颈 | H-01 已确认；激活 H-06 副作用前重复付款事实传递 |
| `2026-08-04-r5` | 2026-08-04 | Known Payment Attempt capability revalidation 独立复核 PASS / IMPROVED：T10 callback 1→0，重复副作用 1/12→0/12，其他 11 项不变，边界挑战无误阻断 | B-07 完成；B-03 从竞争瓶颈升为第一瓶颈 | H-06 SUPPORTED；激活 H-03 产品权威轨迹最小合同 |
| `2026-08-06-r6` | 2026-08-06 | T10 产品权威轨迹切片独立复核 PASS / IMPROVED：product trace 0/12→1/12，target GESR 0/12→1/12，12-event/11-binding VALID，非轨迹投影与安全守护线不变 | B-03 从影响 12/12 缩小到剩余 11/12，仍为第一瓶颈；同时登记 provenance 诊断误报 | H-03 SUPPORTED_BY_T10；先修测量诊断，再扩展第二个单任务 slice |
| `2026-08-06-r7` | 2026-08-06 | T01 正常购买轨迹切片独立复核 PASS / IMPROVED：product trace 1/12→2/12，baseline GESR 0/12→1/12，11-event/10-binding VALID，T10 与非轨迹投影均不退化 | B-03 缩小到剩余 10/12 产品轨迹缺口，仍为第一瓶颈；新增公共组装结构债务作为第三个切片前置维护 | H-03 同时被 T10 拒绝链和 T01 成功链支持；下一步先抽统一 Trace Assembler，再扩展第三个路径族 |
| `2026-08-06-r8` | 2026-08-06 | T09 UNKNOWN 支付恢复轨迹切片独立复核 PASS / IMPROVED：product trace 2/12→3/12，baseline GESR 1/12→2/12，11-event/10-binding VALID，20 项负例、T01/T10 完整轨迹和非轨迹投影均不退化 | B-03 缩小到剩余 9/12 产品轨迹缺口，仍为第一瓶颈；统一 Trace Assembler 已由第三个路径族验证 | H-03 获得支付恢复链支持；下一步选择真实状态冲突事实闭合的 T12 单任务切片 |
| `2026-08-06-r9` | 2026-08-06 | T12 执行前设计复核：T01/T09 builder 分别 597/595 行，T01/T09/T12 的 11 个事件中 9 个完全相同；旧 T12 合同会继续新增专属 builder，尚未执行 | B-03 测量值不变；新增 Sidecar builder 复制这一结构约束，先以场景族工具包方式扩展 | H-03 不变；T12 继续作为唯一新增覆盖，但实现改为统一 Sidecar Trace Toolkit + 声明式 Profile |
| `2026-08-06-r10` | 2026-08-06 | Sidecar Family Toolkit 独立复核 PASS / IMPROVED：T01/T09 迁移为 43/40 行兼容层，产品 sidecar 仅一个 Toolkit 调用，无 T12 专属 builder；Product Trace `3/12→4/12`、GESR `2/12→3/12`，512/512 全量通过 | B-03 缩小到剩余 8/12 产品轨迹缺口，仍为第一瓶颈；场景族工具化路线得到验证 | H-03 继续获支持；下一步一次覆盖结构完全相同的 T02/T03/T04 Prepayment 家族 |
| `2026-08-07-r11` | 2026-08-07 | Prepayment Family Toolkit completion 独立复核 PASS / IMPROVED：T02/T03/T04 用一个 Toolkit + 3 个固定 Profile，10/10 边界、152/152 focused、522/522 全量、repeat=3 通过；Product Trace `4/12→7/12`、GESR `3/12→6/12`，12 项 actual 与旧 trace hashes 全部不变 | B-03 缩小到剩余 5/12（T05/T06/T07/T08/T11）；同时发现剩余 fixture 有 4 个 stale event-name expectations，先统一修 measurement contract | H-03 获得 Prepayment family 支持；修尺子后优先进入 T07/T08 Attack Overlay family |
| `2026-08-07-r12` | 2026-08-07 | Attack Overlay Family Toolkit 独立复核 PASS / IMPROVED：10/10 existing、15/15 family、21/21 project-impact、538/538 全量、repeat=3；Product Trace `7/12→9/12`、GESR `6/12→8/12`；其他 10 项 actual、旧 7 条 trace hash 与 non-trace 全部不变 | B-03 降为 WATCH，仅剩 T05/T06/T11；新增 B-08 Trace Consumer / UI Read Model 并升为第一瓶颈，因为已有四种代表轨迹结构但下游 consumer=0/4 | H-03 获得 Attack Overlay family 支持；激活 H-07，先证明轨迹可被统一只读消费，再进入 P9-E UI |
| `2026-08-10-r13` | 2026-08-10 | Authoritative Trace Consumer 独立复核 PASS / IMPROVED：19/19 consumer、21/21 project-impact、557/557 全量、13/13 正式入口、repeat=3；Consumer-ready `0/4→4/4`，Product Trace `9/12`、GESR `8/12`、旧 src 与 accepted trace hashes 不变 | B-08 保持第一瓶颈，但失败位置从“缺统一 Consumer”下移到“UI 尚未消费稳定 Read Model”；B-03 继续 WATCH | H-07 SUPPORTED；激活 H-08，先做只读 Trace Read Model Player，再讨论完整 WebShop Journey UI |
| `2026-08-10-r14` | 2026-08-10 | Authoritative Trace Player 独立复核 PASS / IMPROVED：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready `0/4→4/4`，source-binding drill-down 与 hostile-string 边界通过，既有 Product Trace/GESR 不变 | B-08 完成；新增 B-09 WebShop Journey 多事实源合同并升为第一瓶颈，先解决商城事实、experiment context 与支付权威证据的来源分离 | H-08 SUPPORTED；激活 H-09，先做 UI-neutral source-classified Journey Read Model，再进入完整 Journey UI / 自主 Agent |
| `2026-08-10-r15` | 2026-08-10 | WebShop Journey Fact Source Read Model 独立复核 PASS / IMPROVED：27/27 Journey、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；Journey source-classified `0/1→1/1`，17 条跨源 correlation 全 true，错绑 fail closed，既有指标不变 | B-09 完成；新增 B-10 Journey UI composition 并升为第一瓶颈 | H-09 SUPPORTED；激活 H-10，只让 UI 消费 accepted Journey Read Model，之后再进入 B-04 自主 Agent |
| `2026-08-23-r16` | 2026-08-23 | WebShop Journey Player 独立复核 REJECTED / INCONCLUSIVE：合法代表路径可展示 1/1，但 `UNVERIFIED` source classification 与未知 schema 两个反例均正常渲染；AC-01/09 失败，相关回归与项目指标未退化 | B-10 保持第一瓶颈，失败位置收敛到 accepted-input guard；B-04 暂不提升 | H-10 尚未得到支持；先执行最小 accepted-input repair，复评通过后再切 B-04 |
| `2026-08-23-r17` | 2026-08-23 | Journey Player accepted-input repair 独立复核 PASS / NOT_APPLICABLE：L2/L3 4/4、Player 27/27、相关回归 67/67、正式入口 13/13；两个反例在 build/render 四个组合全部 fail closed，Product Trace/GESR/side-effect 守护线不变 | B-10 完成；B-04 提升为第一瓶颈，首轮范围固定为 WebShop small goal index 2 的自主 pre-Buy-Now 行为 | H-10 SUPPORTED；激活 H-11，先证明单任务真实环境行为正确且可评分，再扩多任务 |
| `2026-08-24-r18` | 2026-08-24 | Executor preflight 与 Evaluator 独立 runtime probe 一致：固定 shuffle 后 goal index 2=`B07S7HDC88` black loafers，index 10=`B099231V35` orange cargo pants，checkout HEAD=`64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`，两次 reset purchase count=0 | B-04 顺序与量级不变；仅纠正首轮 runtime selector 事实，原 r17 的 index 2 记录由本修订明确取代 | H-11 实质不变；首轮 selector 由 2 更正为 10，任务原地 Amendment A1 后继续 |
| `2026-09-02-r19` | 2026-09-02 | H-11 独立复核 `PASS / IMPROVED`：L3 `6/6 PASS`，goal 10 autonomous Journey/target+option `0/1→1/1`，零 Buy Now/支付副作用；随后 frozen multigoal checker 对 goals 0/2/7/9/10、repeat=2 复现 `3/5`，goal 2/7 均错选商品 | B-04 保持第一瓶颈，但失败位置从“无自主 Agent 行为”下移到“multi-goal product ranking / option matching 泛化不足” | H-11 `SUPPORTED(single-goal)`；激活 H-12，把同一五题 baseline `3/5→5/5`，禁止目标真值/goal-index 补丁 |
| `2026-09-05-r20` | 2026-09-05 | H-12 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`，冻结五目标 `3/5→5/5`，643/643 全量回归且零购买/支付副作用；额外等价 UI 顺序反例得到 `order_invariant=false`；同时发现 H-11 accepted-but-uncommitted policy 只保留 hash、未保留 exact source snapshot | B-04 保持第一瓶颈，但从“已知五题 generalization failure”下移为“unseen-task transfer / semantic robustness 未测量”；不再继续调五题 | H-12 `SUPPORTED_ON_FROZEN_SET`；下一步先做 Evaluator-only Blind Holdout Measurement；H-13 在盲测结论前不激活 |
| `2026-09-06-r21` | 2026-09-06 | Blind Holdout measurement Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `3/3 PASS`，L2=L3；8 个原未见任务 exact `3/8`、deterministic `8/8`、零 Buy Now/购买副作用；失败族 `REQUIRED_OPTION_MISMATCH=4`、`TARGET_PRODUCT_MISMATCH=1` | B-04 保持第一瓶颈，但从“unseen transfer 未测量”下移为“option-grounding generalization（规格匹配泛化）”；已揭晓 8 Case 降级为 regression set，不再作为无偏盲测集 | H-12 项目外推边界确认不足；激活 H-14，用不同值 synthetic/metamorphic probe `1/5→5/5` 验证通用规格匹配机制；H-13 继续后置 |
| `2026-09-06-r22` | 2026-09-06 | Human 明确要求防止把当前已知规格细节误当成“能力已测全”；Evaluator 补充能力不变量、系统性变形发现、新鲜未见迁移测量与失败族台账原则 | B-04 第一瓶颈不变；补充 H-14 后的测量收敛链，避免继续逐题补丁 | H-14 单一主要变化不变；`5/5` 只作为已知失败机制修复门，后续必须经过系统性变形发现 + fresh unseen evidence，再决定 CONTINUE / SWITCH / H-13 |
| `2026-09-06-r23` | 2026-09-06 | H-14 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `8/8 PASS`；frozen option-grounding probe `1/5→5/5`，H-12 real regression `5/5`，647/647 全量回归，Product Trace `9/12`、GESR `8/12`、零 Buy Now/外部副作用 | B-04 保持第一瓶颈，但“已知规格失败机制”已收敛；当前第一未知量转为系统性边界发现 + fresh unseen transfer | H-14 `SUPPORTED_ON_KNOWN_MECHANISMS`；下一步进入 Evaluator-owned Systematic Metamorphic Discovery，不直接继续改代码，也不进入 H-13 |
| `2026-09-06-r24` | 2026-09-06 | Systematic Discovery Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `4/4 PASS`；24 Case=`19 PASS / 5 FAIL`、48 observations 全可重复、safety hits 0；`AMBIGUOUS_OPTION_GUESSED=3` 跨 2 independent seeds；H-15 新 probe baseline `2/5` | B-04 保持第一瓶颈，但从“系统性边界未知”下移为“证据不足 / 候选不唯一时仍猜规格” | 激活 H-15 Option Grounding Uncertainty Gate；先修重复 uncertainty mechanism，再做 fresh unseen transfer |
| `2026-09-06-r25` | 2026-09-06 | 主线纠偏：确认 P9/WebShop 的目的不是穷举意图/规格准确率；B-04 已形成真实自主行为 + 泛化失败证据，H-15 在 Executor 开始前 superseded 并降为 WATCH；代码侧 GovernedPaymentAction / Runtime Gate / Authoritative Trace / Payment-Fulfillment 底座已存在，但 machine-readable Action Origin 仍为 0/5 | 新增并激活 B-11 Action Origin / Responsibility Trace；B-04 改为 WATCH / BEHAVIOR_BASELINE_ESTABLISHED | 冻结 H-13 read-only Action Origin minimal slice；Fresh unseen 不再是 H-13 强制前置门槛 |
| `2026-09-06-r26` | 2026-09-06 | H-13 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `8/8 PASS`；Action Origin `0/5→5/5`，657/657 全量回归；同时确认 autonomous behavior fixture 与 T01 payment trace 仍是独立证据，不能声称 same-journey responsibility chain | B-11 继续 ACTIVE，但瓶颈从“无机器可读 Action Origin”下移为“无同一 journey 连续责任关联” | H-13 `SUPPORTED`；激活 H-16 one-off Same-Journey Responsibility Correlation，先测现有组件能否自然串联，不预设产品修复 |
| `2026-09-06-r27` | 2026-09-06 | H-16 Executor L2 + Evaluator L3 均在 C01 复现 stale cross-policy trace baseline：历史 policy `af2a...` / trace `8c0a...`，当前 policy `6133...` / trace `b99e...`；最终商品/规格/价格与零副作用仍一致；Evaluator fresh current-policy replay 3/3 deterministic | B-11 继续 ACTIVE，但断点从“same-journey 未串通”进一步收敛为“baseline lifecycle 测量合同错误”，尚无证据表明下游产品链失败 | H-16 `REJECTED / INCONCLUSIVE / SWITCH`；激活 H-17，只修测量合同并直接重跑 C01..C08，不改任何产品/runner |
| `2026-09-06-r28` | 2026-09-06 | H-17 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `8/8 PASS`；baseline lifecycle 修正后现有 same-journey responsibility `C01..C08=8/8`、Action Origin 5/5、Trace VALID、657/657、真实副作用 0 | B-11 `RESOLVED / STAGE_CLOSED`；新增 B-12 Same-Journey Payment Lifecycle / Recovery Continuity 并升为第一瓶颈 | H-17 证明 H-16 主要是测量合同问题；激活 H-18 measurement-only 四分支测量，先测现有 Recovery/Finality/Lifecycle/Trace 组合，不预设产品修复 |
| `2026-09-10-r29` | 2026-09-10 | H-18 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `7/7 PASS`；同一 H-17 journey 四分支 semantic=`4/4`、continuity=`1/4`、J03 首断点=`AUTHORITATIVE_TRACE_AVAILABLE`、J02/J04 首断点=`ACTION_ORIGIN_PROJECTABLE`、657/657、真实副作用 0 | B-12 保持第一瓶颈，但从“生命周期组合未测量”下移为 Evidence / Accountability 连续性；先处理更上游的 J03 Trace 缺失 | H-18 完成测量并支持“现有生命周期语义正确但证据链不完整”；激活 H-19，只补失败履约声明式 Sidecar Trace Profile，目标 continuity `1/4→2/4`，不改 Toolkit / Action Origin |
| `2026-09-10-r30` | 2026-09-10 | 执行前重新评估任务粒度：H-18 的 J02/J03/J04 三个失败均属于 Lifecycle Evidence Registry Coverage；J03 缺通用 failed-fulfilment Profile，J02/J04 的既有 VALID Trace 扩展事件缺 Action Origin mapping | B-12 不变，但把三个同类证据链断点合并为一个中等大小的 registry closure，避免连续微修；Payment / Lifecycle / Trace Toolkit 继续冻结 | H-19 `SUPERSEDED_BEFORE_EXECUTION`；激活 H-20 Lifecycle Evidence Continuity Closure，统一目标 semantic `4/4` 保持、continuity `1/4→4/4` |
| `2026-09-11-r31` | 2026-09-11 | H-20 Evaluator REVIEW：Attempt 1 因 T11 旧基线期望 `6/7` 阻断，A1 仅修 regression expectation；Attempt 2 L2 `7/7`、Evaluator L3 `7/7 PASS`，semantic=`4/4`、continuity=`4/4`、Product Trace=`10/12`、GESR=`9/12`、658/658 全量、真实副作用 0 | B-12 `RESOLVED / STAGE_CLOSED`；新增 B-13 Same-Journey Remediation / Closure Continuity 并升为第一瓶颈；B-03 缩小为仅 T05/T06 WATCH | H-20 `SUPPORTED / STOP_THIS_DIRECTION`；激活 H-21 measurement-only，先测 full/partial refund、dispute 与原交易错绑在同一 journey 的 L8-L9 continuity，不预设产品修复 |
| `2026-09-12-r32` | 2026-09-12 | H-21 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，L3 `7/7 PASS`；5/5 semantics、5/5 original-transaction binding expectation、5/5 closure explicit、5/5 existing Product Trace VALID，但 remediation evidence in trace=`0/5`，共同 first breakpoint=`TRACE_REMEDIATION_EVIDENCE_PRESENT`；658/658、真实副作用 0 | B-13 保持第一瓶颈，但从“L8-L9 未测量”收敛为“post-payment remediation evidence registration 缺失”；不是退款/争议规则错误 | H-21 完成测量；激活 H-22，一个通用 remediation trace extension，把 Refund/Dispute + OriginalTransactionBindingFact + Closure outcome source-bound 接回同一 Product Authoritative Trace，不做逐 Case 修补 |
| `2026-09-12-r33` | 2026-09-12 | H-22 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`；remediation evidence `0/5→5/5`、continuity `0/5→5/5`、R05 保持 `INVALID`、662/662、真实副作用 0；Evaluator 独立 probe 发现 live projection hash=`71a4...3966`，但 public runtime hash 仍为 base `45ae...b4` | B-13 的核心补救证据链能力已闭合，但进入 Replay / Accountability 前仍有 contract identity / auditability 缺口；不再增加补救业务场景 | 激活 H-22R bounded repair：只修 historical base 与 effective runtime contract/hash 的分层和公开指纹一致性；修复后重新评估 B-13 是否 STAGE_CLOSED |
| `2026-09-12-r34` | 2026-09-12 | H-22R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；public effective projection/profile/runtime fingerprint 与 live validator contract 机械一致；historical base identity 保持；H-22 五分支复验 SHA-256 完全相同、662/662、真实副作用 0 | B-13 `RESOLVED / STAGE_CLOSED`；新增 B-14 Remediation Accountability / Closure Consumption 为第一瓶颈。Consumer 底座已有部分真实使用证据，但 5 个补救分支经 Consumer + Player 的完整消费仍未系统测量 | 激活 H-23 measurement-only：产品冻结，测现有 Consumer / Read Model / Action Origin / Player 对 5 个补救分支的完整性、确定性和 R05 负例保留；仅在共同断点出现后再考虑 capability package |
| `2026-09-12-r35` | 2026-09-12 | H-23 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `7/7 PASS`；冻结 5 个补救分支 Consumer/Player/continuity 全部 `5/5`、first breakpoint=`NONE:5`，R05 `INVALID` 原样可见，662/662、真实副作用 0 | B-14 `RESOLVED / STAGE_CLOSED`；不再开发 Consumer/Player。新增 B-15 Actor Authenticity / Signed Instruction Verification：P3 最高 BOUND，AP2/ACP 多个签名/身份边界明确 not_verified，但共同机制尚未系统测量 | 激活 H-24 cross-surface measurement-only：冻结产品，跨 P3 + AP2 HP/HNP + ACP 测 6 个真实性边界；只有出现重复共同 verifier gap 后才考虑最小通用真实性验证能力 |
| `2026-09-12-r36` | 2026-09-12 | H-24 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / CONTINUE`，L3 `7/7 PASS`；6/6 探针 deterministic，P3 三路径最高 `BOUND`，product `VERIFIED=0/6`；AP2 HP/HNP + ACP 三个独立入口重复出现 cryptographic signature `not_verified`，34/34 专项、662/662 全量、真实副作用 0 | B-15 继续 ACTIVE，但拆为 B-15A Signed Instruction【当前第一子瓶颈】与 B-15B Credential/Possession【后续】；不建设万能身份模块 | 激活 H-25 capability experiment：协议中立 SignedInstructionVerificationFact + HMAC-SHA256 verifier + ACP 2026-04-17 Merchant-Signature 首个消费者；AP2 SD-JWT、P3 VERIFIED、PKI/钱包/网络继续排除 |
