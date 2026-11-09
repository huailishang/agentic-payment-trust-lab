# H44 P0：外部对照是否值得做的就绪任务设计

> 后续约定（2026-10-11）：Human 要求串行长包、完成后统一评估，已冻结 H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1，吸收本页的来源/判卷/适用性测量并增加候选复核材料。执行入口以 CURRENT 和 H46/EXECUTOR_START 为准。本页保留为历史设计；H44 完整模型对照仍 DRAFT。

Parent task: H44_AGENTDOJO_EXTERNAL_COMPARISON_V1
Stage: P0_SOURCE_CHECKER_AUTHORIZATION_READINESS
Owner: Evaluator
State: DRAFT_CONTRACT / NOT_DISPATCHED / NOT_EXECUTABLE
Baseline observed: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Map basis: 2026-10-11-r71；B-16
Predecessor: H42 REVIEW，PASS / NOT_APPLICABLE / STOP

## 全局位置与唯一问题

项目 A–D 关闭、E 本地代表性闭环，F 外部实证未闭合。B-06 支付宝实证按 Human 安排后置；当前优先 B-16 的外部可测量性。H42 证明一个固定授权合成分支被阻断，却没有外部任务、真实模型或可信确认来源证据。继续同类合成标题测试的信息收益小；直接做 H45 又缺外部结果。

本阶段只回答：能否找到一个外部任务，用可信、独立的授权事实和真实模拟工具状态，公平比较现有控制？不是建设新 Runtime，也不是证明模型安全。

大白话：先核实“别人的题目、付款按钮和判卷方式”能不能接到我们这里，再花钱让模型考试。

## 有界范围与顺序

1. **来源锁。** 使用已解析的 AgentDojo v0.1.35 commit a75aba7631d3ca5fb7ab938965c97ead2f9ff84b；从 v1 UserTask0/3/4 仅选择一个候选。固定具体 suite 注册、继承链、工具、环境初始状态、任务、攻击和许可证的文件路径与原文 SHA-256。若必须改选 suite，显式记录依据，不滚动跟随 main。
2. **独立授权来源。** 列清用户原话授权了什么、哪些事实来自不可信文档/工具、何时必须确认。上游 Gold 只供判卷，不能生成授权或喂给模型。无法从可信输入独立确定允许金额/收款方时，保留 WAIT/CONFIRM 或 UNSUPPORTED；追加独立用户授权信封须标派生 profile，并与原生上游成绩分开。
3. **判定器有效性。** 对固定初始状态及“仅正确交易、仅禁止交易、正确+额外禁止交易”四种状态，分别计算上游 utility、上游 attack success、本项目禁止副作用。禁止只用 utility 一个布尔值。初始历史交易必须与本轮状态差分开，不能把旧交易当本轮成功。
4. **产品入口语义。** 按实际 send_money 参数映射现有控制入口；金额、币种、收款方、主体、授权、确认、幂等键与执行副作用逐项标可表达/不支持/派生。优先已有协议中立对象；不能为了走 WebShop gate 编造商业订单、商品、merchant 或用户确认标签。需要修改核心则停在缺口报告。
5. **下轮方案。** 只有上述成立，才设计一个任务、一个攻击入口的离线工具调用重放。调用必须来自已标明来源的固定轨迹；人工编排轨迹只算合成控制测量。离线无模型结果验收后，再比较模型在环价值及费用，不立即执行父合同 36 episode 提案。

不安装依赖、不导入运行上游工程、不调用模型/Provider、不读取密钥、不改产品、不提交或公开发布。本文件提供待冻结范围，不是执行授权。

## 待冻结交付与验收

| 交付 | P0 完成判据 | 当前状态 |
|---|---|---|
| SOURCE_LOCK.json | commit/suite/继承链/所用原文 hash/MIT attribution/依赖逐项固定 | release 已解析；具体 suite、文件 hash 与运行依赖未固定 |
| AUTHORITY_PROVENANCE.md | 可信授权与非可信内容、Gold、派生确认分开；不跟随污染重建 | 未完成 |
| CHECKER_VALIDITY.md | 四状态 × 三类判定有预期与实际结果；正确+额外禁止交易必须被附加检查识别 | 只有静态源码风险识别；无状态执行证据 |
| SEMANTIC_MAPPING.md | 每个字段与实际现有入口对应；UNSUPPORTED 不补猜 | 未完成 |
| VALIDATION_PLAN.yaml / 独立检查器 | exact argv/cwd/exit、保护 hash、正负对照与 I/O 守护；L2/L3 可复现 | NOT_FROZEN；不能用本文冒充可运行计划 |
| P0_DECISION.md | 单一 READY_FOR_OFFLINE_REPLAY / SOURCE_BLOCKED / CHECKER_INVALID / SEMANTIC_GAP 决策 | 等待上述测量 |

缺项分两层：Evaluator 先完成来源/语义审计及可执行检查器冻结，才能另派离线 P0 测量；模型预算不阻塞这层设计，却阻塞父合同完整模型在环实验。当前任何 P0 PASS 或外部对照成绩都未产生。

## 预算提案与停止线

冻结后的 P0 候选规模最多一个任务、一个攻击入口、四种状态；模型/支付 API 调用 0、真实副作用 0，正式 L2 最多两次。依赖安装、上游运行入口与离线工具隔离尚未审定，不在当前路由放行。

- CONTINUE：来源锁完整、授权可独立确定、四状态判卷有效、映射忠实 → 冻结最小离线工具调用重放；再决定模型在环预算。
- STOP：只能从污染输入或 Gold 建授权，判卷发现不了额外禁止交易，或正对照无效 → 不做完整对照。
- SWITCH：银行转账无法忠实表达为现有 Trust Contract → 保留不支持证据，改比较能映射现有购物/授权边界的外部任务，不新增通用 Runtime。
- 若得到产品失败，先复现共同断点再冻结修复；本包不修改产品求通过。

父合同 36 episode 是总规模提案。若后续启用模型，建议先一个任务 × 良性/污染 × 有/无闸门 × 三次预注册重复，共 12 episode；须另定具体模型、token/费用上限、超时、重试及 L3 审计方式。三次重复不是三个独立攻击，也不形成泛化证明；当前允许模型调用数仍为 0。

## 与 H45 及外部要求的关系

P0 就绪证据、离线重放、模型在环和第三方独立运行各自标明 measurement_level。H45 先消费已接受快照；只有实际收到第三方运行产物，才声称已独立复跑。比赛报名/提交暂不作为瓶颈或验收标准。

external_requirement_impact：profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20。适用性 CORE 控制评估 / ADAPTER 映射逐项记录；before/after 当前均未新增成熟度；Test/Evidence=NONE for P0。风险：上游判卷偏差、可信授权缺失、银行转账语义错配、少样本与模型随机性。不是合规评估结论。

当前只完成评估与任务设计。执行入口仍为 CURRENT；H42 已结束，本草案不通知执行者、不自动派发。
