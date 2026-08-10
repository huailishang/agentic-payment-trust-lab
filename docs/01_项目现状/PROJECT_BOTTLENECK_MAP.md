# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-08-10-r15
Last reviewed: 2026-08-10
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
| 全量 unittest | 486/486 PASS | measured | `P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/REVIEW.md` |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 8/10 可执行 | measured | `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` |
| x402 离线一致性 | 第一轮已完成 | measured but bounded | P8-A 任务合同、报告与复核 |
| 多步骤自主购物项目级指标 | 12 项固定任务；T10 target GESR 1/12；重复副作用 0/12；callback 匹配 12/12；产品权威轨迹 1/12；三次结果一致 | measured | `P9_PRODUCT_AUTHORITATIVE_TRACE_T10_DUPLICATE_PREFLIGHT_SLICE_V1/REVIEW.md` |

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
- 当前多数结果是组件或局部纵向切片结果，不是统一项目指标；
- 冻结 runner 的 `trace_provenance_separated` 诊断只在“产品轨迹不存在”时返回真；T10 同时存在产品轨迹与评估器 Replay 后产生误报。原始来源字段已明确分离，下一包先修复该测量诊断，再扩展第二个产品轨迹场景。

## Bottleneck register / 瓶颈登记表

| ID | 阶段 | 可观察失败 | 估计影响范围 | 证据 | 信心 | 状态 |
|---|---|---|---:|---|---|---|
| B-01 | 项目级评测 / V3 环境 | 固定 12 项任务、统一命令、独立副作用护栏和轨迹来源分类已经建立并独立复核 | 所有未来 capability experiment 的 100% | P9 Measurement Integrity Repair REVIEW：三次一致、15/15 专项、428/428 全量 | high | RESOLVED / BASELINE_ESTABLISHED |
| B-02 | Fact Lineage | 组件级来源传播已通过，但尚未测量它在固定端到端任务中减少了多少来源丢失、错误放行或证据缺口 | 所有包含派生事实的外部环境任务；具体比例 unknown | P9 Fact Lineage REVIEW：16/16 矩阵、12/12 专项、Overlay 投影不变 | medium | WATCH / IMPLEMENTED_UNMEASURED |
| B-03 | Authoritative Trace | T01/T02/T03/T04/T07/T08/T09/T10/T12 已形成 `VALID` 产品权威轨迹；仅 T05/T06/T11 尚未公开产品轨迹 | 剩余 3/12 固定任务 | P9 Attack Overlay Family REVIEW：Product Trace 7/12→9/12，GESR 6/12→8/12；T07/T08 统一 Toolkit 15/15 专项、538/538 全量、repeat=3 通过，其他 10 项 actual 不变 | high | WATCH / REPRESENTATIVE_COVERAGE_SUFFICIENT |
| B-08 | Trace Consumer / UI Read Model | 通用只读 Consumer 与 Trace Player 已贯通：T01/T02/T07/T10 四类代表轨迹均可由同一 Read Model 进入同一只读 UI，事件、relation、source binding 可机械回指 | 当前 4 个已验证结构族；UI-ready 4/4 | P9 Authoritative Trace Player REVIEW：21/21 Player、19/19 Consumer、21/21 project-impact、578/578 全量、13/13 正式入口、repeat=3；UI-ready 0/4→4/4 且旧轨迹/UI/Consumer hash 不变 | high | RESOLVED / TRACE_PLAYER_READY |
| B-09 | WebShop Journey 多事实源合同 | WebShop runtime、experiment context、Commerce Adaptation、payment authoritative trace 四类证据已能在一个 deterministic Journey Read Model 中分层保存并机械关联；错绑 fail closed | 第一轮 1 条固定 WebShop smoke/T01 正常购买路径，Journey source-classified 1/1 | P9 Journey Fact Source Read Model REVIEW：27/27 专项、21/21 Player、19/19 Consumer、21/21 project-impact、605/605 全量、13/13 正式入口、repeat=3；17 条 correlation 全 true，来源边界不变 | high | RESOLVED / SOURCE_CLASSIFIED_JOURNEY_READY |
| B-10 | WebShop Journey UI composition | 多事实源 Journey Read Model 已建立，但用户仍只能分别看支付 Trace Player，尚没有一个页面把“需求→搜索/点击→商品→Adapter→支付可信轨迹”按来源分区串成完整购买 Journey | 第一轮 1 条固定脚本 Journey；后续才扩自主 Agent | H-09 已证明四命名空间可安全合并到 UI-neutral Read Model；现有 WebShop UI 规划要求完整购买链且必须标注固定脚本/自主 Agent 区别 | high | ACTIVE / JOURNEY_UI_GAP |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 现有大量测试输入由固定样例提供，尚不能证明真实 Agent 在多步骤环境中不会走偏 | V3—V5 环境任务，比例 unknown | 验证体系统一路线 | high | WATCH |
| B-05 | 数据最小化 | PayBench D1 两题不可执行，缺少数据披露事实与必要性判断 | PayBench 2/10，后续收货和身份任务 | measured：PayBench 8/10 可执行 | high | WATCH |
| B-06 | 真实身份与外部协议 | 当前最高身份保证为 BOUND，未覆盖真实签名、SDK、facilitator 和网络故障 | 测试网、生产接入；当前主线影响有限 | measured boundary：P3 / P8 文档 | high | DEFERRED |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-10

### 为什么现在排第一

H-09 已独立复核通过：同一条固定 WebShop/T01 路径已经能够形成 `WebShopJourneyReadModel`，并把 `webshop_runtime`、`experiment_context`、`commerce_adaptation`、`payment_authoritative_trace` 四类证据严格分开；17 条跨源 correlation 可机械验证，错绑 fail closed，Journey source-classified 从 `0/1 -> 1/1`。B-09 因此完成。

当前最早的新失败点是：

```text
完整 Journey Read Model（已完成 1/1）
→ 还没有用户可见 Journey Player
→ 用户仍不能在一个页面按步骤看“需求→搜索/点击→商品→Adapter→支付可信轨迹”
```

### 量级估算

- Product Trace：9/12；
- GESR：8/12；
- Trace Player UI-ready：4/4；
- Journey source-classified：1/1；
- Journey UI-ready：0/1；
- 自主 Agent Journey：0，继续由 B-04 WATCH；
- 信心：高，H-09 独立复核 27/27 Journey、605/605 全量、repeat=3，旧支付/轨迹指标不变。

### 分阶段原则

下一步只让一个新的只读 Journey Player 消费 accepted `WebShopJourneyReadModel`。页面必须把四类证据来源分区显示，并明确标记这是“固定脚本轨迹”，不是自主 Agent。通过后才进入 B-04 的自主 Agent 行为采集与展示。

### 竞争瓶颈

竞争瓶颈为 `B-04 外部 Agent 行为`、`B-03 Authoritative Trace` 与 `B-02 Fact Lineage`。当前先完成 B-10，因为事实合同已经干净，UI composition 是进入自主 Agent 展示前最后一个可直接验证的下游缺口。

## Active hypothesis / 当前假设

Hypothesis ID: H-10

### 可证伪假设

如果 Journey UI 只消费 accepted `WebShopJourneyReadModel` primitive，不重新读取 WebShop fixture、Commerce Adapter 或支付 Trace producer，那么一条固定脚本 Journey 可以被确定性地展示成完整购买链，同时四类来源标签、关联证据和“不代表自主 Agent”的边界保持不变。

### 当前测量状态

```text
Journey source-classified representative path：1/1
Journey UI-ready representative path：0/1
Trace Player UI-ready：4/4
Product Trace：9/12
GESR：8/12
```

### 当前单一主要变化

```text
accepted WebShopJourneyReadModel
→ generic read-only Journey Player
→ 完整购买链逐步展示
```

### 成功阈值

1. UI 唯一产品数据输入是 `WebShopJourneyReadModel` primitive；
2. 四类证据命名空间在 UI 中有明确来源标签，不扁平化成同一事实池；
3. 页面能展示用户 instruction、WebShop actions/selected product/Buy Now 状态、Commerce order/request、支付 authoritative trace 摘要与证据 drill-down；
4. 明确显示 `fixed_script_webshop_smoke_not_autonomous_agent`，不得标成自主 Agent；
5. cargo-pants instruction 与 console-table product 均原样展示，不声称匹配；
6. 页面字段与 Journey Read Model 可机械对账，重复 render 3 次 HTML/payload SHA 稳定；
7. Journey UI-ready 从 `0/1 -> 1/1`；
8. Journey source-classified 保持 `1/1`、Trace Player UI-ready 保持 `4/4`、Product Trace `9/12`、GESR `8/12`；
9. 不修改 Journey Read Model、Consumer、Trace Player、trace producer、fixture 或 Adapter；
10. 不执行 WebShop、Buy Now、支付、网络或任何副作用。

### 回滚阈值

- UI 把 experiment context 标成 WebShop verified；
- UI 隐藏或改写用户需求与实际商品不匹配的事实；
- UI 为展示而重新运行 Adapter/支付逻辑；
- 需要 task/profile 硬编码；
- 任何冻结指标或 accepted hash 退化。

## Candidate experiments / 候选实验与设计任务

| 优先级 | 假设 | 主要变化 | 同基线比较 | 预期收益 | 成本 / 风险 |
|---:|---|---|---|---:|---|
| 1 | H-10 / WebShop Journey Player V1 | 一个新的只读 Journey Player 只消费 accepted `WebShopJourneyReadModel`，按四类来源分区展示完整固定脚本购买链 | Journey UI-ready `0/1→1/1`；Journey source-classified 保持 `1/1`、Trace Player `4/4`、Product Trace `9/12`、GESR `8/12` | 首次把用户需求、商城动作、Adapter 与支付可信证据放到同一可审计页面 | 中；不得重跑 Adapter/WebShop/支付，不得冒充自主 Agent |
| 2 | B-04 / autonomous Agent journey capture | Journey Player 通过后，再定义真实 Agent 搜索/选择/点击行为的结构化轨迹合同和评测 | 固定脚本与 autonomous Agent 明确分开测量 | 从“固定脚本演示”进入真正自主购买行为验证 | 高；需要新的环境运行授权与行为评测合同 |
| 3 | H-03 / Action Binding family toolkit | 如 Consumer/UI 证明 T05/T06 有真实下游价值，再用统一 Action Binding family 表达最终 binding 状态 | 当前 9/12 baseline 上做同族 before/after | 可选补 2 项产品轨迹 | 中；暂缓，不为 12/12 数字机械开发 |
| 4 | H-03 / T11 design review | 如下游需要完整履约失败展示，再核对 T11 与 Sidecar Toolkit 的复用边界 | 只设计/测量，不先声称增益 | 决定最后 1 项是否值得补齐 | 中；避免为 T11 再造完整专属 builder |
| 5 | H-02 | Fact Lineage 能消除派生来源丢失 | 同一端到端来源攻击任务 before / after | lineage 完整率提高，错误放行不增加 | 中 |

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
