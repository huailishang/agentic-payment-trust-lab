# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-09-17-r46
Last reviewed: 2026-09-17
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
- B-15 Actor Authenticity（主体真实性）已在本地离线边界形成代表性闭环；H-30 又把 PayBench Data Minimization（数据最小化）从 `8/10` 补到 `10/10` 可执行；当前剩余第一本地缺口回到 B-03 T05/T06 Action Binding Rejection Trace（动作绑定拒绝轨迹）。

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
→ E. 主体真实性 / 凭证 / 签署指令   [本地代表性闭环已完成]
→ F. 外部真实协议 / SDK / 网络接入   [未来，受授权与环境约束]

横切补强：B-05 Data Minimization（数据最小化）【本地阶段关闭】
B-03 Product Authoritative Trace（产品权威轨迹）【固定 12 项覆盖已闭合】
当前本地主线：本地代表性基线阶段收口【12/12；等待新证据或外部环境触发】
```

| 阶段 | 要解决的核心问题 | 当前代表能力 / 证据 | 状态 |
|---|---|---|---|
| A 评测与治理底座 | 怎么知道一次修改真的让项目变好，而不是测试数量变多 | 12 项项目基线、GESR、零副作用守护线、Evaluator / Executor、L2/L3 独立复核 | `CLOSED` |
| B 授权、绑定、来源、执行前治理 | Agent 能不能在明确授权、正确对象、可信来源下安全触发副作用 | P1 Delegated Authority、P2 Payment Binding、P3 BOUND Identity、P4 Context Policy、Governed Action、Fact Lineage、重复付款保护 | `CLOSED` |
| C 生命周期、恢复、补救证据链 | 支付后 UNKNOWN、履约失败、退款、争议、原交易错绑时能不能安全恢复并留下连续证据 | Payment Lifecycle / Recovery、Finality、Remediation / Closure、Product Authoritative Trace `10/12`，B-12/B-13 阶段关闭 | `CLOSED` |
| D 责任归因与可消费审计链 | 事后能不能回答“谁做的、依据什么、发生了什么”，并让 UI / 审计消费者稳定读取 | Action Origin、Same-Journey Responsibility、Consumer、Read Model、Player；H-23 五分支消费 `5/5` | `CLOSED` |
| E 主体真实性 / 凭证 / 签署指令 | ID 对得上之后，能否证明执行者真的持有对应凭证/密钥，授权/指令真的由对应主体签署 | B-15A 已由 ACP/HMAC + AP2/ES256 两个消费者闭合；B-15B 已由 bounded X.509-SVID + proof-of-possession + challenge binding 形成首个受控 `BOUND→VERIFIED` 路径 | `CLOSED_WITH_LOCAL_BOUNDARY` |
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

阶段 E 已在本地、离线边界形成代表性闭环：

```text
B-15A Signed Instruction Verification（签署指令验证）【STAGE CLOSED】
  → ACP/HMAC + AP2/ES256 两个独立消费者复用同一通用验证事实

B-15B Credential / Possession Verification（凭证 / 持有证明验证）【LOCAL STAGE CLOSED】
  → credential_ref-only 仍为 BOUND
  → bounded X.509-SVID + subject binding + proof-of-possession + freshness/replay 可产生受控 VERIFIED
  → H-29R 已关闭 signed challenge metadata relabel replay
```

阶段 E 的剩余真实 Provider、生产 credential/key、live SPIRE / PKI / OIDC / DID / VC 统一归入 B-06 / 阶段 F，只有出现明确外部环境与授权后再进入；不为了增加 Provider 数量继续扩本地 synthetic verifier。

H-30 已把 B-05 Data Minimization（数据最小化）的本地字段名级代表性缺口关闭：PayBench current rules 从 `8/10 executable` 提升为 `10/10 executable + 10/10 PASS`，非 D1 八题保持不变。完整 Privacy Governance、真实 PII 与监管合规仍明确不在当前能力声明内。

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

当前 B-03 T05/T06 优先于剩余备选项的原因：

- B-05 已由 H-30 `PASS / IMPROVED` 达成本地阶段关闭，不继续扩完整隐私治理；
- B-04 Fresh Unseen Agent 行为已有真实长尾基线，但项目已明确不沿逐 Case 意图/规格优化继续主线，保持 `WATCH（观察）`；
- B-06 真实 SDK / testnet / network 依赖额外授权与环境，保持 `DEFERRED（延期）`；
- B-03 是当前唯一明确且无需外部授权即可闭合的固定项目缺口：T05/T06 的 decision、binding 与 callback 已正确，共同只缺 action-binding rejection 的产品权威轨迹，Product Trace=`10/12`、GESR=`9/12`。
- 下一包严格只补证据连续性，不修改 T05/T06 业务决策，也不把独立的 T10 lifecycle/duplicate semantic gap 混进来。

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
| 全量 unittest | 703/703 PASS | measured | `P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1/REVIEW.md` |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 10/10 可执行且 10/10 PASS | measured | `P9_DATA_MINIMIZATION_DISCLOSURE_FACT_V1/REVIEW.md` |
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

项目级端到端基线已冻结为 12 项固定任务和 `run_project_impact_baseline.py`，可用于同 target 的 capability experiment（能力实验）前后比较。B-11—B-15 与 B-05 已分别完成责任链、生命周期 / 恢复、补救 / 结束状态、Consumer / Player、本地主体真实性和字段名级数据最小化的代表性闭环；当前 Product Trace=`10/12`、GESR=`9/12`，剩余 T05/T06 业务决策正确但缺 action-binding rejection 产品权威轨迹，因此 B-03 重新成为第一本地瓶颈。

### 已知盲区

- 当前测试数量增长不能直接等价为项目能力增长；
- H-14 当前 `5` 个 synthetic/metamorphic probe（合成 / 变形探针）只覆盖**已经暴露出来的规格失败机制**，不是 option-grounding（规格匹配）能力全集；即使达到 `5/5`，也只能证明当前假设在冻结代表样本上成立，不能声称“规格问题已经测全”；
- 规格能力仍存在未系统发现的组合空间，例如同义表达、大小写/空格/标点变化、单位与数字格式、多个干扰选项、多个规格组、缺失规格、歧义候选、页面顺序变化、部分匹配与冲突请求；这些未知细节不能靠人工逐条穷举，而要用 property/metamorphic testing（性质 / 变形测试）系统发现；
- 已揭晓 Blind Holdout 只能作为回归证据；任何新的“泛化成立”结论都必须来自下一轮产品修改前冻结的 fresh unseen evidence（新鲜未见证据）；
- WebShop 已形成多个离线切片，但还没有冻结统一的多步骤 Agent 任务集；
- 当前没有生产网络、真实支付、真实身份和真实 LLM 行为；
- PayBench D1 字段名级数据最小化已由 H-30 覆盖，但真实 PII、retention、日志脱敏、跨 Provider 传播、监管分类与 DLP 仍未覆盖；
- 当前多数结果是组件或局部纵向切片结果，不是统一项目指标；
- 冻结 runner 的 `trace_provenance_separated` 诊断只在“产品轨迹不存在”时返回真；T10 同时存在产品轨迹与评估器 Replay 后产生误报。原始来源字段已明确分离，下一包先修复该测量诊断，再扩展第二个产品轨迹场景。

## Bottleneck register / 瓶颈登记表

| ID | 阶段 | 可观察失败 | 估计影响范围 | 证据 | 信心 | 状态 |
|---|---|---|---:|---|---|---|
| B-01 | 项目级评测 / V3 环境 | 固定 12 项任务、统一 runner、独立副作用护栏和轨迹来源分类已建立；H-32 已将 T10 主 fixture 对齐到此前独立验收的 preflight 安全语义 | 固定 12 项当前全部匹配；GESR / evidence completeness / Product Trace 均 12/12 | H-32 Evaluator REVIEW：L3 `6/6 PASS`、708/708；T10 保持 `DENY/callback0/BLOCKED`，仅修 5 个 stale expected 字段；repeat=3/3 | high | RESOLVED / BASELINE_RECONCILED |
| B-02 | Fact Lineage | 组件级来源传播已通过，但尚未测量它在固定端到端任务中减少了多少来源丢失、错误放行或证据缺口 | 所有包含派生事实的外部环境任务；具体比例 unknown | P9 Fact Lineage REVIEW：16/16 矩阵、12/12 专项、Overlay 投影不变 | medium | WATCH / IMPLEMENTED_UNMEASURED |
| B-03 | Authoritative Trace | H-31 已补齐 T05/T06 action-binding rejection trace，固定 T01-T12 均有 `VALID` 产品权威轨迹；T05/T06 决策/binding/callback 原样保持 | 固定 12 项 Product Trace `12/12`；当前无剩余 trace coverage gap | H-31 Evaluator REVIEW：L3 `8/8 PASS`、708/708、PayBench 10/10、S01-S13 13/13；Product Trace `10/12→12/12`、GESR `9/12→11/12` | high | RESOLVED / FIXED_12_TASK_TRACE_COVERAGE |
| B-08 | Trace Consumer / UI Read Model | 通用只读 Consumer 与 Trace Player 已贯通：T01/T02/T07/T10 四类代表轨迹均可由同一 Read Model 进入同一只读 UI，事件、relation、source binding 可机械回指 | 当前 4 个已验证结构族；UI-ready 4/4 | P9 Authoritative Trace Player REVIEW：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready 0/4→4/4 且旧轨迹/UI/Consumer hash 不变 | high | RESOLVED / TRACE_PLAYER_READY |
| B-09 | WebShop Journey 多事实源合同 | WebShop runtime、experiment context、Commerce Adaptation、payment authoritative trace 四类证据已能在一个 deterministic Journey Read Model 中分层保存并机械关联；错绑 fail closed | 第一轮 1 条固定 WebShop smoke/T01 正常购买路径，Journey source-classified 1/1 | P9 Journey Fact Source Read Model REVIEW：27/27 专项、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；17 条 correlation 全 true，来源边界不变 | high | RESOLVED / SOURCE_CLASSIFIED_JOURNEY_READY |
| B-10 | WebShop Journey UI composition | 固定脚本 Journey 已能按来源安全进入一个 deterministic Player；accepted-input schema/source-classification 两个反例已全部 fail closed | 第一轮固定脚本 Journey UI-ready 1/1 | Journey Player 父任务合法路径 1/1；accepted-input repair L2/L3 4/4、Player 27/27、两个反例 4 个入口组合全拒绝 | high | RESOLVED / SAFE_JOURNEY_PLAYER_READY |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 已形成真实多步骤 autonomous behavior、H-12 `5/5` 开发/回归证据、Blind Holdout `3/8` 泛化边界、H-14 通用修复与 Systematic Discovery `19/24`；已证明 Agent 可产生真实行为，也证明意图/规格存在难穷举长尾 | 当前价值已从“继续提高购物理解准确率”转为向信任链提供真实 Agent 行为与已知限制；H-15 `2/5` probe 保留为回归资产，不再阻塞主线 | H-14 `PASS / IMPROVED`；Systematic Discovery `PASS / NOT_APPLICABLE`、L3 `4/4 PASS`、48 observations all reproducible、safety hits 0；H-15 在 Executor 开始前 superseded | high | WATCH / BEHAVIOR_BASELINE_ESTABLISHED |
| B-11 | Action Origin / Responsibility Trace | H-13 已完成 Action Origin `0/5→5/5`；H-17 修正跨 policy 版本基线后，同一 autonomous journey 的 Agent→Order/Request→Runtime→offline Payment/Fulfillment→Trace 连续关联 `8/8`，五类 origin 可投影 | 代表性 happy-path responsibility chain 已闭合；不再继续扩 Action Origin 字段 | H-17 Evaluator REVIEW：Task `PASS`、Project impact `NOT_APPLICABLE`、L3 `8/8 PASS`、same-journey `8/8`、657/657 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-12 | Same-Journey Payment Lifecycle / Recovery Continuity | H-20 已将 H-18 三个同类证据链断点统一闭合：semantic `4/4` 保持，continuity `1/4→4/4`，四条 Trace 均 VALID 且 Action Origin 可投影 | L5-L7 支付执行、状态、恢复、冲突与履约的代表性同旅程证据连续性已闭合 | H-20 Evaluator REVIEW：Task `PASS`、Project impact `IMPROVED`、L3 `7/7 PASS`、Product Trace `9/12→10/12`、GESR `8/12→9/12`、658/658 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-13 | Same-Journey Remediation / Closure Continuity | H-21 定位 5/5 共同补救证据断点；H-22 以一个通用 extension 将 remediation evidence `0/5→5/5`、continuity `0/5→5/5`；H-22R 又使 public runtime fingerprint 与 live validator contract 完全一致，R05 全程保持 `INVALID` | 支付后退款/争议/原交易绑定/Closure 的代表性同旅程证据生产与合同身份已闭合，不再继续扩 R01-R05 或补救产品字段 | H-22R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；effective projection/profile/runtime hash 全部与 live contract 一致；H-22 复验 SHA-256 完全相同；662/662、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-14 | Remediation Accountability / Closure Consumption | H-23 已对冻结 5 个补救分支完成现有 Product Trace → Consumer → Read Model → Action Origin → Player 系统测量；Consumer/Player/continuity 均 `5/5`，R05 `INVALID` 原样可见且无虚假 payment relation | 代表性退款/争议/原交易错绑证据已经可被现有通用只读消费链稳定消费，无需新增 Consumer/Player 特判 | H-23 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `7/7 PASS`，first breakpoint=`NONE:5`，51/51 专项、662/662 全量、真实副作用 0 | high | RESOLVED / STAGE_CLOSED |
| B-15 | Actor Authenticity / Credential / Signed Instruction Verification | B-15A 已由 ACP/HMAC + AP2/ES256 形成跨协议/跨算法两个 Signed Instruction 消费者；B-15B 已由 bounded X.509-SVID + subject binding + proof-of-possession + freshness/replay 形成首个受控 `BOUND→VERIFIED` 路径，H-29R 关闭 metadata relabel replay | 当前本地、离线真实性边界已具代表性闭环；真实 Provider / 生产凭证 / live identity 迁入 B-06 | H-29R Evaluator REVIEW：Task `PASS / NOT_APPLICABLE / SWITCH`，L3 `8/8 PASS`；relabel counterexample fail closed；H-29 `7/7` 保持；30/30 focused、699/699 full unittest、项目 guardrails 不退化 | high | RESOLVED / LOCAL_REPRESENTATIVE_CLOSURE |
| B-05 | 数据最小化 | H-30 已建立协议中立 `DataDisclosureFact`，机械比较 required / allowed / requested；D1 Trap 阻断非必要字段但保持购买可执行，Lookalike 必要字段正常 | PayBench 字段名级隐私挑战 `8/10→10/10` 可执行；完整 Privacy Governance 仍不在当前范围 | H-30 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，L3 `8/8 PASS`；PayBench `10/10 PASS`，703/703，全项目守护线不退化 | high | RESOLVED / LOCAL_STAGE_CLOSED |
| B-06 | 真实身份与外部协议 | A-E 已完成本地代表性闭环，但尚未证明官方协议对象、SDK、真实 Provider、网络与后续真实支付环境可以无语义漂移进入现有 Canonical Facts + Trust Core | 当前先从 AP2 v0.2.0 官方 release 做 source/schema/HNP compatibility measurement；真实 SDK、Sandbox、testnet、production 逐级后置 | H-33 / F0：官方 AP2 v0.2.0 `b4587ac` 已由公开资料确认，第一包只测 12 维兼容矩阵，不改产品、不装依赖、不碰资金 | high | ACTIVE / OFFICIAL_PROTOCOL_COMPATIBILITY_MEASUREMENT |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-06

### 当前判断

H-32 已由 Evaluator 独立 L3 复核通过：

```text
Task verdict: PASS
Project impact: NOT_APPLICABLE
L3: 6/6 PASS
full unittest: 708/708
PayBench: 10/10 PASS
S01-S13: 13/13 PASS
matched: 12/12
GESR: 12/12
evidence completeness: 12/12
Product Trace: 12/12
gap: []
```

T10 产品行为没有被修改，仍是 `DENY / callback0 / preflight BLOCKED / trace VALID`。H-32 只把主项目 baseline 的 5 个旧 expected 字段对齐到此前已经独立验收的 B-07 target，因此 `GESR 11/12→12/12` 属于 corrected measurement，不是新增产品能力。

用户已明确授权项目进入 F 阶段的第一层公开外部验证。当前第一瓶颈切换为 B-06，但不是直接接真钱，而是先回答一个更基础的问题：**官方 AP2 v0.2.0 的真实协议对象、schema 与 Human Not Present 语义，能否无语义漂移进入现有 Canonical Facts + Trust Core。**

因此 H-33 / F0 只做 measurement-first：

- 固定 AP2 v0.2.0 官方 release `b4587ac`；
- 只读获取官方 source/schema/HNP samples；
- 对照当前 AP2 Adapter、Signed Instruction 与 Canonical Core；
- 形成 12 维 compatibility matrix；
- 不修改 `src/` / `tests/`，不安装 SDK，不调用 Gemini/Vertex，不接支付、不碰钱包和真实资金。

如果测量显示只是 Adapter 层有界差距，再进入 F1 official SDK executable slice；如果出现 Core 语义缺口，先回 Evaluator 重新判断，不允许为了 AP2 改写核心支付规则。

### 当前主线

```text
A-D【STAGE CLOSED】
        ↓
E. Actor Authenticity【LOCAL REPRESENTATIVE CLOSURE】
        ↓
LOCAL REPRESENTATIVE BASELINE【12/12 CLOSED】
        ↓
F. External Protocol / SDK / Provider【CURRENT】
        ↓
F0 AP2 v0.2.0 Official Contract Compatibility Measurement
        ↓
先证明外部协议能无语义漂移进入 Canonical Core，再决定 F1
```

## Active hypothesis / 当前假设

Hypothesis ID: H-33
Hypothesis status: `CONTRACT_FROZEN / AP2_V020_OFFICIAL_COMPATIBILITY_MEASUREMENT`

### 假设

> 如果现有 Canonical Facts + Trust Core 的协议中立边界成立，那么 AP2 v0.2.0 官方 Mandate、Checkout/Payment Binding、Receipt、HNP 与验证责任，应能被逐项映射并明确归类；即使存在差距，也应主要暴露在 Adapter / external integration boundary，而不是迫使核心授权和支付规则按 AP2 特判。

本轮不以“12 项全 SUPPORTED”为成功标准。成功标准是：官方来源固定、12 维测量可复核、未知诚实暴露、首个真实断点分类正确，而且 `src/tests` 完全冻结。

## Candidate experiments / 候选实验与设计任务

| 优先级 | 方向 | 当前状态 | 触发条件 | 当前动作 |
|---:|---|---|---|---|
| 1 | H-33 / F0 AP2 v0.2.0 官方合同兼容测量 | CURRENT | 用户已授权公开外部验证；官方 release 可固定 | 只读获取 source/schema/HNP samples，形成 12 维兼容矩阵 |
| 2 | F1 AP2 official SDK executable slice | GATED | F0=`NO_PRODUCT_GAP` | 再授权必要依赖，接真实 AP2 types，不碰真钱 |
| 3 | F0R bounded AP2 Adapter capability package | GATED | F0=`BOUNDED_ADAPTER_GAP` | 只修 Adapter 共同断点，复核通过后再进入 F1 |
| 4 | F2 Alipay Agent Pay Sandbox | GATED | F1 稳定进入 A-E | 接官方 Sandbox 验证 callback/query/finality/recovery |
| 5 | F3/F4 Identity Provider + 极小额线上证据 | DEFERRED | Sandbox 稳定且 Human 明确资金授权 | 再进入真实 credential / production-like payment |
| 6 | B-04/B-02 | WATCH | 新证据显示其真实阻断 Trust / Payment 主链 | 才重新激活，不抢占 F0 |


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
| `2026-09-13-r37` | 2026-09-13 | H-25 Evaluator REVIEW：Task `PASS / IMPROVED / CONTINUE`，L3 `10/10 PASS`；ACP signed-webhook `0/6→6/6`、5/5 negative fail-closed、13/13 focused、675/675 full unittest，H-24 accepted hash 不变，真实网络/支付/生产凭据密钥 0 | B-15A 明显缩小：已获得 ACP 第一个真实 Signed Instruction consumer，但跨协议/跨算法复用尚未由第二消费者证明；B-15B 继续后置 | 激活 H-26 evaluator-design：先冻结 AP2 第二消费者的 pinned source、exact signed object、key relation 与正负验证样例；证据不足则不进入 AP2 verifier 编码并重排方向 |
| `2026-09-13-r38` | 2026-09-13 | H-26 evidence gate：官方 AP2 `v0.2.0` release / merchant-signed JWT / deterministic verification 提供稳定协议依据；冻结 evaluator-owned ES256/P-256 synthetic fixture、六案例正负矩阵；本机已有 `cryptography 41.0.7`，无需网络或安装 | B-15A 从“第二消费者证据是否存在”前移为“第二消费者能否真实复用同一 Fact”；完整 SD-JWT / Credential / AP2 conformance 继续排除 | 激活 H-27 capability experiment：generic ES256 compact-JWS verifier + AP2 merchant-authorization adapter；目标 AP2 `0/6→6/6`、real consumers `1→2`、H-25 accepted hash 不变 |
| `2026-09-13-r39` | 2026-09-13 | H-27 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，L3 `10/10 PASS`；AP2 ES256 `0/6→6/6`、real consumers `1→2`、5/5 negative fail-closed、17/17 focused、692/692 full unittest，H-25 accepted hash 不变，真实网络/支付/生产凭据密钥 0 | B-15A `RESOLVED / STAGE_CLOSED`：ACP/HMAC + AP2/ES256 已提供跨协议/跨算法第二消费者证据；第一子瓶颈切换为 B-15B Credential/Possession，P3 仍最高 `BOUND` | 激活 H-28 evaluator-design：冻结 credential validity、subject binding、proof-of-possession、freshness/replay 与 `BOUND→VERIFIED` promotion rule；证据不足则保持 `BOUND` |
| `2026-09-15-r40` | 2026-09-15 | H-28 evidence gate 完成：SPIFFE X.509-SVID / Trust Bundle / Workload API 与 RFC 9449 PoP 语义足以冻结四条件升级门；Evaluator 生成不含私钥的 synthetic X.509-SVID 正例与 wrong-trust/wrong-subject/no-proof/bad-proof/replay/stale 六类负例；本机 `cryptography 41.0.7` 可离线执行 | B-15B 保持第一瓶颈，但从“真实 verifier 语义未定义”前移为“有界 X.509-SVID credential/PoP 能否第一次合法产生 VERIFIED”；B-06 live identity/network 继续 DEFERRED | 激活 H-29 capability experiment：protocol-neutral CredentialPossessionVerificationFact + bounded X.509-SVID verifier + P3 promotion wiring；目标 product VERIFIED `0→1` 且 legacy credential_ref-only 保持 BOUND |
| `2026-09-15-r41` | 2026-09-15 | H-29 Executor L2 `8/8`、冻结七案例 `7/7`、698/698 与项目 guardrails 均通过，但 Evaluator 独立 `RV-EV-09` 复现 metadata relabel replay：旧 signed payload/signature 保持不变，仅重贴 fresh nonce/issued_at 即错误返回 `VALID / credential_possession_verified` | B-15B 保持第一瓶颈；H-29 `REJECTED / REGRESSED`，失败位置收敛到 signed challenge 与 freshness/replay 元数据未密码学绑定；不是 X.509-SVID 方向整体失败 | 激活 H-29R bounded repair：只增加 canonical signed challenge binding，冻结 P3 promotion / Payment policy / Signed Instruction；先关闭 false VERIFIED 再决定是否继续 B-15B |
| `2026-09-17-r42` | 2026-09-17 | H-29R Evaluator L3 `8/8 PASS`：六类 metadata relabel attack 全部 fail closed，父 H-29 `7/7` 与 `VERIFIED 0→1` 保持；30/30 focused、13/13 正式场景、699/699 全量、Product Trace 10/12、GESR 9/12。同期复跑 PayBench current rules=`8/10`，唯一 unsupported 为 D1 Trap/Lookalike | B-15 在本地离线边界达到代表性闭合并转 `RESOLVED`；真实 identity 归 B-06 `DEFERRED`。B-05 从 WATCH 升为第一瓶颈，因为 D1 两个独立外部挑战共同缺 data disclosure fact | 激活 H-30 capability experiment：一个最小协议中立 DataDisclosureFact + PayBench D1 首个消费者；目标 executable `8/10→10/10`，不扩完整隐私治理 |
| `2026-09-17-r43` | 2026-09-17 | H-30 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，修正 evaluator plan 的 `PYTHONPATH=src` 可复现性后 L3 `8/8 PASS`；PayBench `8/10→10/10` 可执行且 `10/10 PASS`，703/703 全量，守护线不退化。重新测量 T05/T06：decision/binding/callback 均正确，共同只缺产品权威轨迹 | B-05 `RESOLVED / LOCAL_STAGE_CLOSED`；B-03 从 WATCH 升为第一本地瓶颈，范围严格限定 T05/T06 action-binding rejection trace；B-04 WATCH，B-06 DEFERRED | 激活 H-31：复用现有 Trace Assembler / frozen profile contract，为 T05/T06 拒绝分支附加一个通用产品权威轨迹族；目标 Product Trace `10/12→12/12`、GESR `9/12→11/12`，不修改决策语义 |
| `2026-09-17-r44` | 2026-09-17 | H-31 Evaluator REVIEW：Task `PASS / IMPROVED / SWITCH`，独立 L3 `8/8 PASS`、708/708、PayBench 10/10、S01-S13 13/13；Product Trace `10/12→12/12`、GESR `9/12→11/12`，仅剩 T10。历史回查确认 B-07 已独立验收 T10 `DENY/callback0/BLOCKED`，而主 fixture 仍保留更早 `ALLOW + lifecycle` 期望；临时机械对齐 accepted target 后 GESR/evidence/Product Trace 均 `12/12`、gap=0、repeat=3 | B-03 `RESOLVED / FIXED_12_TASK_TRACE_COVERAGE`；B-01 因 T10 主 baseline expectation drift 重新激活为第一瓶颈；B-04 WATCH，B-06 DEFERRED | 激活 H-32 measurement repair：只允许主 fixture T10 五个 stale expected 字段与 accepted B-07 target 对齐，并同步直接依赖测试；零产品/runner 修改，Project impact 固定 `NOT_APPLICABLE` |
| `2026-09-17-r45` | 2026-09-17 | H-32 Evaluator REVIEW：Task `PASS / NOT_APPLICABLE`，独立 L3 `6/6 PASS`、708/708、PayBench 10/10、S01-S13 13/13；protected product/runner/accepted target 不变，仅 T10 五个 stale expected 字段与 B-07 target 对齐；fresh repeat=3 得到 matched/GESR/evidence/Product Trace 全部 `12/12`、gap=0 | B-01 `RESOLVED / BASELINE_RECONCILED`；当前固定本地代表性项目基线无 active gap。B-02/B-04 保持 WATCH，B-06 保持 DEFERRED | H-32 `PASS / CLOSED`；不自动激活新本地假设，等待新项目级失败、新外部评测或真实环境授权再重排 |
| `2026-09-17-r46` | 2026-09-17 | Human 明确授权进入 F 阶段公开外部验证；公开资料复核确认 AP2 `v0.2.0` release=`b4587ac`，重点覆盖 Human Not Present，官方规范/SDK/source/schema 可作为独立外部合同来源 | B-06 从 DEFERRED 激活为第一瓶颈，但先做 `OFFICIAL_PROTOCOL_COMPATIBILITY_MEASUREMENT`，不直接接 SDK 依赖、Sandbox 或真实资金 | 激活 H-33 / F0：冻结 AP2 v0.2.0 只读 source，做 12 维兼容矩阵；`src/tests` 冻结，结果只允许导向 NO_PRODUCT_GAP / BOUNDED_ADAPTER_GAP / CORE_SEMANTIC_GAP / SOURCE_ENV_BLOCKED |
