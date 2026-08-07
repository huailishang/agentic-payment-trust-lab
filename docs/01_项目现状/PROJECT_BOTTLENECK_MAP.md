# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-08-07-r12
Last reviewed: 2026-08-07
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
| B-08 | Trace Consumer / UI Read Model | 9 条产品轨迹已经机器可验证，但 `html_report.py` / `interactive_lab.py` / `interactive_server.py` 尚未消费 `ProductAuthoritativeTrace`；轨迹还没有形成协议中立、只读的下游时间线数据 | 当前 4 个已验证结构族，后续覆盖 9/12 已有轨迹 | P9 Attack Overlay Family REVIEW + `WebShop购买轨迹可视化UI规划_20260802.md`：UI 必须读取机器生成轨迹而非日志反推；当前 consumer baseline=0/4 代表结构族 | high | ACTIVE |
| B-07 | 副作用前重复付款保护 | 同 request 已成功付款时，Runtime Gate 已在 callback 前 DENY；无关异常记录不误阻断 | 1/12 固定任务；零容忍支付副作用已消除 | P9 Capability Revalidation REVIEW：duplicate side effect 1/12 → 0/12，callback match 11/12 → 12/12 | high | RESOLVED / MEASURED_IMPROVED |
| B-04 | 外部 Agent 行为 | 现有大量测试输入由固定样例提供，尚不能证明真实 Agent 在多步骤环境中不会走偏 | V3—V5 环境任务，比例 unknown | 验证体系统一路线 | high | WATCH |
| B-05 | 数据最小化 | PayBench D1 两题不可执行，缺少数据披露事实与必要性判断 | PayBench 2/10，后续收货和身份任务 | measured：PayBench 8/10 可执行 | high | WATCH |
| B-06 | 真实身份与外部协议 | 当前最高身份保证为 BOUND，未覆盖真实签名、SDK、facilitator 和网络故障 | 测试网、生产接入；当前主线影响有限 | measured boundary：P3 / P8 文档 | high | DEFERRED |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-08

### 为什么现在排第一

B-03 已通过多轮同基线实验把产品轨迹从 `0/12` 提升到 `9/12`，并覆盖四种不同结构族：Sidecar、Prepayment、Attack Overlay、Duplicate/Preflight。当前剩余 `T05/T06/T11` 三项仍没有产品轨迹，但继续追求 `12/12` 已不再是最早阻塞点。

当前新的可观察失败是：

```text
产品已经生成 VALID Authoritative Trace
→ 评测器可以验证
→ 但产品 UI / Interactive Lab 尚未真正消费这些轨迹
→ 普通用户仍看不到统一的“发生了什么、为什么允许/阻断”的时间线
```

`docs/02_未来规划/WebShop购买轨迹可视化UI规划_20260802.md` 已明确：UI 必须读取机器生成的轨迹文件，不允许从日志或文案反推事实。现在 9 条产品轨迹已经提供足够的代表性输入，应该先验证一个协议中立、只读的 Trace Consumer / Read Model，而不是继续机械补 T05/T06/T11。

### 量级估算

- 产品观测权威轨迹完整率：9/12；
- baseline GESR：8/12；
- 已验证产品轨迹：T01、T02、T03、T04、T07、T08、T09、T10、T12；
- 剩余 B-03 产品轨迹缺口：3/12（T05/T06/T11）；
- 已验证结构族：Sidecar、Prepayment、Attack Overlay、Duplicate/Preflight，共 4 类；
- Trace Consumer 代表结构覆盖 baseline：0/4；当前没有一个下游 read model 统一消费这四类 VALID trace；
- 信心：高，Attack Overlay family 独立复核 10/10 + 15/15 + 21/21 + 538/538，repeat=3，且其他 10 项 actual 与旧 7 条 trace hash 全部不变。

### 分阶段原则

不再以“补满 12/12”为默认推进方式。先用四种已验证结构族建立一个只读 Trace Consumer / Read Model，证明轨迹能够被下游统一消费；Consumer 通过后再进入 P9-E UI。T05/T06/T11 是否补齐，改为由下游真实需要和新增覆盖价值决定。

### 竞争瓶颈

竞争瓶颈：`B-03 Authoritative Trace` 与 `B-02 Fact Lineage`。

B-03 仍有 T05/T06/T11 三项缺口，但已有 9/12、四种结构族，继续补覆盖不会回答“这些轨迹能否真正被 UI / Replay 统一消费”。B-02 继续保留为组件已实现、项目影响待测；当前先解决 B-08 的消费缺口。

## Active hypothesis / 当前假设

Hypothesis ID: H-07

### 可证伪假设

如果一个协议中立、只读的 Trace Consumer 只接受 frozen `VALID ProductAuthoritativeTrace`，把已有事件、引用、关系和 source binding 机械映射成 deterministic UI-neutral timeline，而不重跑任何业务规则，那么四个代表结构族可以被同一个 Consumer 正确消费，并且输出可回指原始 trace、重复消费完全一致、非法轨迹 fail closed。

代表结构冻结为：

```text
T01 = Sidecar
T02 = Prepayment
T07 = Attack Overlay
T10 = Duplicate / Preflight
```

### 当前测量状态

```text
固定任务：12
Product Trace：9/12
GESR：8/12
重复或禁止副作用：0/12
callback 次数匹配：12/12
已验证产品轨迹结构族：4
Consumer-ready 代表结构族：0/4
```

现状已经证明“产品会产轨迹”，但还没有证明“下游能统一消费轨迹”。因此 H-07 不再增加产品轨迹覆盖率，而是验证 Authoritative Trace 能否成为 Replay / UI 的稳定输入契约。

### 估计影响范围

- 第一轮直接影响：4 个代表结构族，T01/T02/T07/T10；
- 后续可复用范围：当前已有 `VALID` 产品轨迹的 9/12 任务；
- P9-E UI 将消费 Consumer Read Model，不直接解析各 family 产品对象；
- B-03 剩余 T05/T06/T11 暂不进入本轮；
- 不引入网络、真实支付、浏览器控制或生产身份。

### 当前单一主要变化

```text
ProductAuthoritativeTrace
→ 一个通用、只读 Trace Consumer
→ deterministic Timeline / Read Model JSON
```

本轮不做最终 UI，不扩展任何 trace producer，也不补 T05/T06/T11。

### 成功阈值

1. Consumer 输入必须先通过 frozen authoritative trace validator；
2. `INVALID / INDETERMINATE / malformed` 输入 fail closed，不生成伪造 timeline；
3. 对 VALID trace 精确保留事件顺序和事件数量；
4. 每个 Read Model event 至少保留 `sequence_no / event_type / entity_type / entity_role / entity_ref / source_binding_ref / decision / status / reason_codes / relations`；
5. source binding 可由 Read Model 回指原始 trace binding；
6. T01/T02/T07/T10 四类代表轨迹由同一个 Consumer 处理，不允许 profile/task 专属分支；
7. 同一 trace 连续消费 3 次输出规范化 SHA 完全一致；
8. Consumer-ready representative families 从 `0/4 -> 4/4`；
9. Product Trace 保持 `9/12`、GESR 保持 `8/12`，所有产品 trace hash 与业务结果不变；
10. Consumer 不调用支付、Policy、Lineage、validator 业务规则、runner 或 evaluator 重算事实。

### 无可测收益阈值

- 只支持某一个 profile / task 的特殊分支；
- 丢掉引用、关系或 reason codes，导致 UI 无法回指证据；
- 接受 INVALID trace 或自行补造缺失事件；
- 输出依赖对象 repr、自由文本或运行时随机值，无法稳定序列化；
- 只写 UI mock，没有稳定 Read Model 契约。

### 回归或回滚阈值

- 为 Consumer 修改现有 trace producer、registry、runner、fixture 或业务决策；
- 任何既有产品 trace hash 改变；
- Product Trace / GESR 或 non-trace 业务投影发生变化；
- Consumer 需要 task ID / profile 名硬编码才能工作；
- 引入网络、真实支付、未授权副作用或在消费阶段重新执行业务规则。

## Candidate experiments / 候选实验与设计任务

| 优先级 | 假设 | 主要变化 | 同基线比较 | 预期收益 | 成本 / 风险 |
|---:|---|---|---|---:|---|
| 1 | H-07 / Trace Consumer Read Model V1 | 一个协议中立、只读 Consumer，把 `ProductAuthoritativeTrace` 转成 deterministic timeline/read model | T01/T02/T07/T10 consumer-ready `0/4→4/4`；Product Trace 保持 `9/12`、GESR 保持 `8/12` | 首次证明四类产品轨迹可被统一 Replay/UI 消费 | 低中；不得修改任何 producer/registry/runner/fixture，不得重跑业务规则 |
| 2 | H-07 / P9-E UI V1 | UI 只消费 Trace Read Model，作为证据播放器展示购买、检查、支付/阻断过程 | UI 展示字段与 Read Model / 原始 trace 独立对账 | 把已有可信轨迹变成普通用户可理解的产品能力 | 中；UI 不能成为事实源、不能重新执行购买或决策 |
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
