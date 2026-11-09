# H44 草案：AgentDojo 最小外部对照

Task ID: H44_AGENTDOJO_EXTERNAL_COMPARISON_V1
Task kind: one_off
Risk: L2
Contract state: DRAFT_CONTRACT
Dispatch mode: SINGLE
Current role: Evaluator
Baseline HEAD observed at design: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision observed: 2026-10-11-r71
Active bottleneck candidate: B-16
Validation design: VALIDATION_DESIGN.md
Validation plan file: NOT_FROZEN

本草案不能执行，不改 CURRENT。冻结时须重新核实基线与地图；不把本轮源代码阅读算成外部实验通过。

后续 Human 约定：H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1 已单独冻结为串行离线证据链包，吸收本合同的前置来源/判卷/适用性测量并整理候选材料。H46 只测原始源码片段、合成状态及缺绑定诊断，不执行本合同的完整 gate/模型对照。执行入口以 CURRENT 为准；本合同仍 DRAFT。

2026-10-11 更新：H42 已 PASS / NOT_APPLICABLE / STOP，独立 L3 3/3。当前优先完成 P0_READINESS.md 的来源、判定器与可信授权就绪设计；父合同完整模型对照仍未冻结，不能跳过 P0 直接跑 36 episode。

## 战略依据

项目最终要证明合法任务完成与禁止副作用阻断同时成立。H42 仅一个合成输入族，外部泛化 unknown；支付宝按 Human 安排后置。外部任务对照的预期价值在于独立场景、真实工具调用和状态检查，而不是增加 Adapter 数量。与继续扩 H42 标题变体相比，新来源可能提供更高信息增益；与 SPIRE/OPA/VI 相比，本包更直接测 B-16。

Measurement status: 外部对照 unknown；H42 一个合成标题污染族已 measured，固定授权 callback0，重建确认诊断 callback1。
Metric baseline: NOT_MEASURED；不得用历史 Attack Overlay 6/6 代入。
Expected project impact: 提供边界明确的独立外部测量；不预承诺改善。
Rollback condition: 无忠实映射、正对照无效或需改产品时停止；保留结果，不修改核心求通过。

## 唯一目标与主要变化

在上游同一任务、同一授权、同一模型配置、同一工具和环境下，只改变“付款工具前是否接现有闸门”，比较正常任务完成与禁止模拟副作用。

主要变化仅为外部工具调用到现有控制边界的最小桥接。允许外围适配，禁止改变上游判题目标、偷偷减少授权约束、重写付款状态机或为 task_id 编写放行规则。

第一轮建议只用有/无闸门两个条件，以隔离主要变量；提示词策略保持相同。“额外安全提示词是否有用”另测，不在本包同时优化。

## 先决测量与精确缺项

以下均须由 Evaluator 补齐后才能 CONTRACT_FROZEN：

1. 已满足：H42 正式 L2/独立 L3 各 3/3 PASS，正式 REVIEW 未发现本范围产品阻断性缺陷；只接受单一合成族结论，不能外推外部任务。
2. 固定 AgentDojo release、具体 suite 修订、继承模块、依赖和源文件 SHA-256。已解析 v0.1.35 commit=a75aba7631d3ca5fb7ab938965c97ead2f9ff84b，但 suite 尚未定。
3. 用无模型正负状态证据证明：所选工具确实改变模拟状态；上游效用判定、攻击判定及本项目禁止副作用检查各自能判对。保留“正确交易+额外错误交易”反例。
4. 确认付款动作可忠实映射到现有产品入口；银行转账不得伪装成已验证的支付宝/WebShop 商业对象。无法表达的字段显式 UNSUPPORTED。
5. 固定可信授权来源。上游参考答案只供评分，不能喂给模型，不能从污染后的工具结果重建用户确认。若追加显式授权信封，必须标为本项目派生 profile（实验配置），不能宣称原生上游成绩。
6. 选定模型与模型运行入口、模型版本可固定程度、最大步数、每次调用 token 上限、费用上限和重试规则。当前没有可执行的模型额度授权。
7. 固定具体合法任务、攻击输入和独立检查器，生成包含 exact argv 的 VALIDATION_PLAN.yaml。本文没有用空计划冒充可运行门禁。

最小候选：先审查 v1 的 UserTask0/3/4 与 send_money（模拟转账）工具，再比较后续 suite 修订。它们只是来源候选，不是已冻结样本；不能忽略已知判定器限制。定期支付、密码修改和只凭模型文本判分的任务不进入首轮付款对照。

## 范围、预算提案与停止线

- 冻结后可新增：本目录内桥接、运行器、固定输入、来源锁、检查器、报告、证据；产品目录默认只读。
- 冻结前不得安装依赖、运行上游 Agent、调用模型或修改产品。许可与敏感字段审查在复制外部样本前完成。
- 拟议规模上限：3 个任务 × 良性/污染 × 有/无闸门 × 3 个预注册运行种子，共 36 个 episode（独立任务运行）；每个最多 12 个模型回合，即最多 432 次模型调用机会。实际额度、费用和运行种子须在冻结时明确；本数字是提案，当前允许模型调用数为 0。
- 超时、拒绝、工具错误和失败均进入分母；不得删除失败后补跑到好看。模型非确定性需报告，不把少量零失败宣称普遍安全。
- 最多 2 次正式 L2 提交；该额度同样仅在冻结后生效。
- 正对照失败、授权来自不可信源、映射需补猜、存在未拦截真实 I/O、费用或回合预算耗尽时 STOP。
- 发现关键控制失败只报告；修复另立合同，不在本包改产品。

## 原子验收条件（待冻结）

| AC | 必须观察到 | 不允许用什么替代 |
|---|---|---|
| AC-01 来源与边界 | 固定 commit/suite/文件哈希/许可证/依赖；外部与派生字段分开 | rolling main 或仅写 release |
| AC-02 测量有效性 | 模拟工具实际状态变化；正负状态检查均有效；额外禁止交易被发现 | 仅统计模型文字或上游一个布尔值 |
| AC-03 对照一致性 | 除闸门开关外输入与可信授权相同；环境每次重置 | 两组不同模型、任务或确认 |
| AC-04 真实控制路径 | 实际拟议调用经产品闸门；动作、参数、决策与状态差可追溯 | 预写 ALLOW/DENY 或仅离线标签检查 |
| AC-05 指标与预算 | 正常完成、攻击目标成功、禁止副作用、误拒绝、漏确认、重复动作、成本分列；所有尝试入账 | 全拒绝得满分、只选成功轨迹 |
| AC-06 独立复核 | 完整 L2、来源审计、提交快照、L3 和边界声明 | 把记录重放称为新模型实验 |

## 交付及后续决定

交付 SOURCE_LOCK.json、SEMANTIC_MAPPING.md、CHECKER_VALIDITY.md、冻结的任务/攻击输入、报告和原始 EV。各指标保留分子/分母；原始思维链、真实凭据、生产支付数据和本机路径不进入可分发产物。

有效安全结果或有效失败结果均可完成 one_off（单次测量）；任务通过不等于控制收益成立。独立复核后再选 CONTINUE（重复共同断点）、STOP（无新断点或收益低）或 SWITCH（无法忠实测量）。H45 只能消费已接受的快照。

## 授权与外部要求

commit=false；push=false；history_rewrite=false；api_call=false。没有模型、支付、真实网络服务、赛事提交或公开发布授权。公开文档只读来源核验与正式模型/Provider 调用分开记录。

external_requirement_impact：profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20；适用性 CORE/ADAPTER 逐项冻结；maturity_before/after 当前不变；Test/Evidence=NONE。残余风险：基准判定器、授权语义、模型随机性、样本规模与生产外推。
