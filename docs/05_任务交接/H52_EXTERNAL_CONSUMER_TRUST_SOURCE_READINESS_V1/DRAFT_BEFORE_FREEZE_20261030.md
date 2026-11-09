# H52 外部消费者与可信确认来源就绪判断（草案）

Task ID: H52_EXTERNAL_CONSUMER_TRUST_SOURCE_READINESS_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: evaluator_design
Contract state: DRAFT_CONTRACT
Owner: Evaluator
Dispatch status: NOT_DISPATCHED
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-29-r83
Active bottleneck: B-17
Candidate hypothesis: H-52（尚未冻结）

## 2026-10-30 评估补充（不授权实现）

Human提供UCP花店+AP2、Stripe沙箱、Medusa双协议候选路线及Google官方教程。已核对项目与官方来源，详见EXTERNAL_INTEGRATION_ASSESSMENT_20261030.md。公开受控研究无需先有付费客户：已有固定UCP商家可作为第一技术消费者，当前应先明确UCP版本/扩展支持、可信签发角色和真正执行接缝。花店固定2026-04-08与教程2026-08-25不能直接混用；教程使用模拟影院与程序生成用户key，不证明真实身份。H37官方签验可复用，H51已接受切片不重做。

因此下面“缺失输入”不再一概解释为等待Human提供外部团队。下一候选收敛为最多2主动小时的只读版本/信任边界就绪核查；不安装、不运行云/模型/商家/Provider，不新增产品实现。完成后按明确差距决定一个最小授权到执行包、商家合同变化或STOP。Stripe与Medusa保持后续条件候选，非自动开发排期；当前仍DRAFT_CONTRACT/NOT_DISPATCHED，实际来源快照和验证计划未冻结，四项授权不变。

## 全局位置与选择理由

目标是授权、绑定、执行、恢复、审计可信；A–D阶段关闭、E仅本地代表性闭环、F当前。H51已PASS/NOT_APPLICABLE/STOP，证明人工接线下8个本地HTTP场景，默认工厂仍拒绝、确认仍由合成夹具签发。继续同类测试不能证明真实消费者适用性或可信签发来源。

B-17整体不关闭。相比继续锁/路由测试，本草案优先取得能决定下一能力投入的具体消费方事实；相比直接建设真实签发/Provider（支付服务提供方）适配器，先明确对象和责任。支付宝/比赛仍延期。公开团队名单不是已验证需求，不重复堆名单或重做H49商家通用设计。

## 唯一候选目标

仅对一个指定消费者工作流判断：是否已有足够证据，将可信确认来源、商家执行边界和一个可复核结果冻结为下一有界任务。输出只能为READY_FOR_ONE_BOUNDED_TASK、MISSING_CONSUMER_EVIDENCE或STOP_NO_JUSTIFIED_NEXT_IMPLEMENTATION；事实分已测、估计及未知。

## 精确缺失输入／就绪阻塞

1. 一个明确的目标消费方及具体交易流程；研究消费者亦可，不强制商业客户。
2. 可使用且经许可的脱敏样例、现有故障轨迹或外部验收要求，以及来源和使用边界；不接收真实支付敏感数据。
3. 谁有权签发用户确认、确认绑定哪些对象；谁可接线部署商家，谁负责执行/查询/撤销。未知写未知，不能用测试夹具回答。
4. 如果选择商业交付，另需问题负责人、现有解决方案不足之处及预算意愿；技术研究不伪造采购要求。

2026-10-29初始草案尚无以上具体消费者事实。2026-10-30补充了公开研究消费者候选；真实部署/客户事实仍未给出，但不构成本地受控就绪核查的机械前置条件。草案目前缺精确版本/源码快照与签发/执行责任的固定结果，不机械触发第二套讨论或规格流程。

## 候选范围与预算（待冻结）

输入就绪后，建议只读复用H47–H51证据及一个指定样例，最多2主动小时、一次判断，形成证据/责任表和一个下一合同或STOP。不实现产品、不新增签发端点、不运行消费者/Provider、不联系团队、不扩大名单，不联网、安装、读取秘密、执行付款或Git写操作。仅本目录治理材料可写。

第一候选已是固定UCP商家与AP2官方扩展/教程，精确兼容版本、来源快照及责任边界尚未固定。因此当前不生成占位验证计划、不冻结、不派Executor。Evaluator可先完成上述只读就绪核查，再冻结实际范围、AC、验证计划、保护基线及预算；若只能再造一个同样合成信任的演示且无新可判定边界，保持实现分支STOP。

## 外部要求与边界

已检查PCAC映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；适用性待实际流程判断；maturity_before=UNCHANGED；maturity_after=UNCHANGED；Test=NOT_RUN；Evidence=H51 REVIEW与缺失输入清单；残余=真实签发/部署责任/跨系统撤销/Provider/消费者证据未知。无成熟度升级或监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
