# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-08-03-r4  
Last reviewed: 2026-08-03  
Map owner: Evaluator / Human Task Owner  
Status: ACTIVE  
> 适用协议：从下一个新任务开始使用 `evaluator-executor-workflow/v2.1`。当前进行中的 `P9-GOVERNED-PAYMENT-FACT-LINEAGE-V1` 继续按其冻结的 v2 合同完成，不中途迁移。

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
| 全量 unittest | 396/396 PASS | measured | 同上任务独立复核证据 |
| Attack Overlay 第一轮 | 6/6 PASS | measured | 项目中控与验证体系文档 |
| PayBench | 8/10 可执行 | measured | `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` |
| x402 离线一致性 | 第一轮已完成 | measured but bounded | P8-A 任务合同、报告与复核 |
| 多步骤自主购物项目级指标 | 12 项固定任务；GESR 0/12；重复副作用 1/12；产品权威轨迹 0/12；三次结果一致 | measured | `P9_PROJECT_IMPACT_BASELINE_MEASUREMENT_INTEGRITY_REPAIR_V1/REVIEW.md` |

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

项目级端到端统一命令尚未冻结。下一项评估者设计任务必须建立一个单命令、固定任务集、固定期望结果和可重复输出的项目基线。

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
| B-03 | Authoritative Trace | 产品公开输出的统一权威轨迹完整率为 0/12；评测器合成 Replay 只能作诊断 | 12/12 固定任务 | P9 Measurement Integrity Repair REVIEW：product-observed trace 0/12 | high | WATCH / MEASURED |
| B-07 | 副作用前重复付款保护 | T10 已有同一 request 的 SUCCEEDED payment，但 Runtime Gate 仍执行 callback=1，Sidecar 事后才阻断 | 1/12 固定任务；但属于零容忍支付副作用 | P9 Measurement Integrity Repair REVIEW：duplicate side effect 1/12，callback match 11/12 | high | ACTIVE |
| B-04 | 外部 Agent 行为 | 现有大量测试输入由固定样例提供，尚不能证明真实 Agent 在多步骤环境中不会走偏 | V3—V5 环境任务，比例 unknown | 验证体系统一路线 | high | WATCH |
| B-05 | 数据最小化 | PayBench D1 两题不可执行，缺少数据披露事实与必要性判断 | PayBench 2/10，后续收货和身份任务 | measured：PayBench 8/10 可执行 | high | WATCH |
| B-06 | 真实身份与外部协议 | 当前最高身份保证为 BOUND，未覆盖真实签名、SDK、facilitator 和网络故障 | 测试网、生产接入；当前主线影响有限 | measured boundary：P3 / P8 文档 | high | DEFERRED |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-07

### 为什么现在排第一

可信项目基线已经建立。当前最明确的支付安全失败是：

```text
同一 request 已经存在 SUCCEEDED payment
→ Runtime Gate 仍执行 callback = 1
→ Sidecar 事后才识别 duplicate_payment_blocked
```

重复付款、副作用后才阻断属于项目明确的零容忍失败。虽然它目前只出现在 T10 的 1/12 任务中，但一旦映射到真实支付，影响是直接资金或订单副作用，因此优先于纯可观测性缺口。

### 量级估算

- 直接影响：固定任务 T10，1/12；
- 当前重复或禁止副作用率：1/12；
- 当前 callback 次数匹配率：11/12；
- 风险等级：零容忍；
- 信心：高，已由 accepted result 和独立复核重复验证。

### 完全移除后的最大合理收益

```text
T10 callback：1 → 0
重复或禁止副作用率：1/12 → 0/12
callback 次数匹配率：11/12 → 12/12
```

GESR 预计仍为 0/12，因为产品权威轨迹仍为 0/12；但零容忍支付副作用得到可测改善，足以构成项目 `IMPROVED`。

### 竞争瓶颈

竞争瓶颈：`B-03 Authoritative Trace`。

产品观测权威轨迹为 0/12，影响范围明显更广，是消除 B-07 后的下一主线。

### 为什么竞争瓶颈暂不排第一

- B-03 当前主要影响可解释性、回放和 GESR 完整性；
- B-07 已经发生受控 callback，属于实际副作用顺序错误；
- 项目风险容忍度明确规定重复付款和副作用后阻断为零容忍；
- 先消除直接副作用，再建设全链路轨迹，符合支付安全优先顺序。

## Active hypothesis / 当前假设

Hypothesis ID: H-06

### 可证伪假设

如果把与当前 Authority—Order—Request 完整绑定的已成功付款尝试，转换为明确的副作用前重复事实，并在 Runtime Gate 调用 callback 之前复用现有 `verify_payment_execution_binding` 和 `seen_request_ids` 校验，那么 T10 将在 callback 前被稳定阻断，而其他 11 项任务和既有回归不会退化。

### 当前基线

```text
固定任务：12
GESR：0/12
T10 decision：ALLOW
T10 callback：1
重复或禁止副作用率：1/12
callback 次数匹配率：11/12
产品观测权威轨迹：0/12
```

### 估计影响范围

- 直接影响 T10，1/12；
- 影响全部未来带支付尝试库存的 WebShop / 协议接入；
- 消除一个零容忍副作用类型；
- 不解决 Authoritative Trace 0/12。

### 单一主要变化

只增加“已绑定付款尝试 → 副作用前重复事实 → Runtime Gate”这条事实传递：

- 复用现有 PaymentExecutionRecord 和 P2 binding；
- 复用现有 `seen_request_ids` / `p1:duplicate_request` 闸门；
- 不新增第二套重复付款状态机；
- 不修改 Sidecar 的事后诊断职责。

### 预期项目影响

```text
duplicate_or_forbidden_side_effect_rate：1/12 → 0/12
callback_count_match_rate：11/12 → 12/12
T10 callback：1 → 0
```

允许 GESR 继续为 0/12，因为 B-03 尚未处理。

### 成功阈值

1. 使用同一冻结目标 fixture 做 before / after；
2. T10 已绑定成功付款时，decision 为 `DENY`，callback=0；
3. reason code 包含稳定的 duplicate preflight 依据；
4. 错绑、缺字段或伪造 attempt 不能被当成可信重复事实，且必须失败关闭；
5. 重复副作用率变为 0/12，callback 匹配变为 12/12；
6. 其余 11 项任务结果逐字段不变；
7. 全量回归和正式入口不退化。

### 无可测收益阈值

- T10 callback 仍为 1；
- 只在 Sidecar 事后增加 reason code；
- 通过放宽 expected 或删除 T10 得到全绿；
- 重复副作用率仍非 0；
- 无法提供同一 target fixture 的 before / after。

### 回归或回滚阈值

- 任一非 T10 固定任务发生决策、callback、状态或原因漂移；
- 任一错误放行、漏确认、禁止写入指标退化；
- 未绑定或恶意 attempt 可以阻断合法支付；
- 新增第二套 request/order/payment binding 规则而非复用现有事实；
- 引入网络、真实支付或未授权副作用。

## Candidate experiments / 候选实验与设计任务

| 优先级 | 假设 | 主要变化 | 同基线比较 | 预期收益 | 成本 / 风险 |
|---:|---|---|---|---:|---|
| 1 | H-06 | 已绑定成功付款事实进入副作用前闸门，可消除 T10 重复 callback | 同一 T10 target fixture before / after | 重复副作用 1/12 → 0/12，callback 匹配 11/12 → 12/12 | 中；支付安全零容忍 |
| 2 | H-03 | 统一权威轨迹能提高副作用可解释性 | 同一 12 项任务的 product trace before / after | 产品轨迹 0/12 提高，GESR 开始可增长 | 中高 |
| 3 | H-02 | Fact Lineage 能消除派生来源丢失 | 同一端到端来源攻击任务 before / after | lineage 完整率提高，错误放行不增加 | 中 |
| 4 | H-04 | 外部 Agent 多步骤运行会暴露固定案例未发现的问题 | 固定 Agent / 环境任务与当前手工输入对比 | 新失败可被沉淀为规格 | 高；需要稳定环境 |
| 5 | H-05 | 数据披露事实能覆盖 PayBench D1 | 固定 D1 任务 before / after | PayBench 8/10 → 10/10，守护指标不退化 | 中高 |

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
