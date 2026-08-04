# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-08-04-r5  
Last reviewed: 2026-08-04  
Map owner: Evaluator / Human Task Owner  
Status: ACTIVE  
> 当前新任务统一使用 `evaluator-executor-workflow/v2.1`，按“瓶颈—假设—同基线实验—保留或回滚”闭环推进。

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
- 当前正在建设的 Governed Action 与 Fact Lineage。

明确不包含：

- 真实资金、真实信用卡或生产支付网络；
- 生产商户、生产凭证、主网资产；
- 完整 Agent PKI 或生产身份认证；
- 未授权的外部 API、测试网、钱包和网络调用；
- 对生产安全、监管合规或业务合法性的证明。

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
| 全量 unittest | 451/451 PASS | measured | `P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_CAPABILITY_REVALIDATION_V1/REVIEW.md` |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 8/10 可执行 | measured | `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` |
| x402 离线一致性 | 第一轮已完成 | measured but bounded | P8-A 任务合同、报告与复核 |
| 多步骤自主购物项目级指标 | 12 项固定任务；GESR 0/12；重复副作用 0/12；callback 匹配 12/12；产品权威轨迹 0/12；三次结果一致 | measured | `P9_KNOWN_PAYMENT_ATTEMPT_PREFLIGHT_CAPABILITY_REVALIDATION_V1/REVIEW.md` |

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

项目级端到端基线已冻结为 12 项固定任务和 `run_project_impact_baseline.py`，可用于同 target 的 capability experiment 前后比较；当前主要缺口不是测量命令，而是产品公开输出缺少可计入指标的权威轨迹。

### 已知盲区

- 当前测试数量增长不能直接等价为项目能力增长；
- WebShop 已形成多个离线切片，但还没有冻结统一的多步骤 Agent 任务集；
- 当前没有生产网络、真实支付、真实身份和真实 LLM 行为；
- PayBench D1 数据最小化仍未覆盖；
- 当前多数结果是组件或局部纵向切片结果，不是统一项目指标。

## Bottleneck register / 瓶颈登记表

| ID | 阶段 | 可观察失败 | 估计影响范围 | 证据 | 信心 | 状态 |
|---|---|---|---:|---|---|---|
| B-01 | 项目级评测 / V3 环境 | 固定 12 项任务、统一命令、独立副作用护栏和轨迹来源分类已经建立并独立复核 | 所有未来 capability experiment 的 100% | P9 Measurement Integrity Repair REVIEW：三次一致、15/15 专项、428/428 全量 | high | RESOLVED / BASELINE_ESTABLISHED |
| B-02 | Fact Lineage | 组件级来源传播已通过，但尚未测量它在固定端到端任务中减少了多少来源丢失、错误放行或证据缺口 | 所有包含派生事实的外部环境任务；具体比例 unknown | P9 Fact Lineage REVIEW：16/16 矩阵、12/12 专项、Overlay 投影不变 | medium | WATCH / IMPLEMENTED_UNMEASURED |
| B-03 | Authoritative Trace | 产品公开输出的统一权威轨迹完整率为 0/12；评测器合成 Replay 只能作诊断 | 12/12 固定任务 | P9 Capability Revalidation REVIEW：product-observed trace 仍为 0/12，GESR 仍为 0/12 | high | ACTIVE / MEASURED |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 现有大量测试输入由固定样例提供，尚不能证明真实 Agent 在多步骤环境中不会走偏 | V3—V5 环境任务，比例 unknown | 验证体系统一路线 | high | WATCH |
| B-05 | 数据最小化 | PayBench D1 两题不可执行，缺少数据披露事实与必要性判断 | PayBench 2/10，后续收货和身份任务 | measured：PayBench 8/10 可执行 | high | WATCH |
| B-06 | 真实身份与外部协议 | 当前最高身份保证为 BOUND，未覆盖真实签名、SDK、facilitator 和网络故障 | 测试网、生产接入；当前主线影响有限 | measured boundary：P3 / P8 文档 | high | DEFERRED |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-03

### 为什么现在排第一

B-07 的重复付款 callback 已从 `1/12` 降为 `0/12`。当前最广泛、最明确的剩余失败是：

```text
产品内部已有 Authority / Order / Request / Decision / Payment 等事实
→ 各结果对象只暴露局部记录
→ 项目 runner 无法从产品公开输出获得统一权威轨迹
→ product-observed trace = 0/12
→ GESR = 0/12
```

评测器可以自行拼装 ReplayEvent，但那只能证明“评测器能重放”，不能证明产品真实产生了可审计轨迹。B-03 影响全部 12 项固定任务，是当前覆盖范围最大的已测瓶颈。

### 量级估算

- 产品观测权威轨迹完整率：0/12；
- GESR：0/12；
- 直接影响：全部 12 项固定任务；
- 当前决策、副作用和绑定守护线已稳定，适合开始补产品可观测链；
- 信心：高，已由同一项目基线多轮独立复核确认。

### 分阶段原则

不一次性重构全部任务。先冻结最小统一轨迹合同和现有产品输出映射，再选择一个代表性纵向切片做 capability experiment；只有该切片可归因改善后，才扩大覆盖。

### 竞争瓶颈

竞争瓶颈：`B-02 Fact Lineage`。

Fact Lineage 已在组件级实现但未测量项目影响；它与轨迹互补，但当前 0/12 的产品轨迹缺口更直接阻断 GESR 和独立回放，因此 B-03 先行。

## Active hypothesis / 当前假设

Hypothesis ID: H-03

### 可证伪假设

如果产品公开 outcome 直接携带由实际运行过程中已有不可变事实生成的最小统一轨迹，并明确标记来源为 product-observed，而不是由评测器事后合成，那么至少一个代表性纵向切片的产品轨迹可以从 `NOT_AVAILABLE` 提升为 `VALID`，且决策、callback、绑定和状态结果完全不变。

### 当前基线

```text
固定任务：12
GESR：0/12
产品观测权威轨迹：0/12
重复或禁止副作用：0/12
callback 次数匹配：12/12
决策—理由一致：12/12
```

### 估计影响范围

- 最终潜在影响 12/12 固定任务；
- 第一阶段只定义统一合同和覆盖映射，不宣称项目改善；
- 首个 capability slice 应覆盖真实产品 outcome 中已有的 Authority、Order、Request、Decision 和 Payment/Policy 事实；
- 不引入网络、真实支付或生产身份。

### 第一阶段单一主要变化

只冻结“产品轨迹最小合同”：

```text
产品实际 outcome / observed records
→ 统一 trace envelope
→ 事件类型、引用、来源、顺序、完整性状态
→ runner 只读取产品公开 trace
```

第一阶段不得修改产品逻辑、runner 指标或伪造 `VALID` 结果。

### 成功阈值

1. 明确区分 product-observed trace 与 evaluator-synthesized replay；
2. 为 12 项任务逐项列出当前产品可提供的真实事件、缺失事件和来源对象；
3. 冻结最小 trace schema、顺序、引用完整性和 fail-closed 规则；
4. 选择一个最小代表性 slice，并冻结 before/after target；
5. 证明方案复用现有 RuntimeGateRecord、PaymentExecutionRecord、Policy/Lineage facts，不复制业务绑定规则；
6. 不修改任何现有决策、callback 或状态语义。

### 无可测收益阈值

- 只把 runner 生成的 ReplayEvent 改名为产品轨迹；
- 只写文档概念，没有逐任务产品输出映射和冻结 target；
- trace schema 依赖自由文本或不可验证对象；
- 首个 slice 无法形成同基线 before/after。

### 回归或回滚阈值

- evaluator 可以在产品未产出事件时自行补齐并计为 `VALID`；
- 轨迹事件与 Authority、Order、Request、Decision 或 Payment 引用不一致仍被接受；
- 为了轨迹修改决策、callback、状态或支付执行顺序；
- 一次性跨越全部产品路径，导致无法归因；
- 引入网络、真实支付、未授权副作用或新的业务绑定规则。

## Candidate experiments / 候选实验与设计任务

| 优先级 | 假设 | 主要变化 | 同基线比较 | 预期收益 | 成本 / 风险 |
|---:|---|---|---|---:|---|
| 1 | H-03 | 先冻结最小产品轨迹合同与 12 项产品输出映射，再做一个代表性 slice | 当前 product trace 0/12 与首个 slice before / after | 首个产品轨迹从 NOT_AVAILABLE → VALID，决策和副作用不变 | 中；先设计后小范围实现 |
| 2 | H-02 | Fact Lineage 能消除派生来源丢失 | 同一端到端来源攻击任务 before / after | lineage 完整率提高，错误放行不增加 | 中 |
| 3 | H-04 | 外部 Agent 多步骤运行会暴露固定案例未发现的问题 | 固定 Agent / 环境任务与当前手工输入对比 | 新失败可被沉淀为规格 | 高；需要稳定环境 |
| 4 | H-05 | 数据披露事实能覆盖 PayBench D1 | 固定 D1 任务 before / after | PayBench 8/10 → 10/10，守护指标不退化 | 中高 |

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
