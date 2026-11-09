# H53 商家授权消费合同收敛草案

Task ID: H53_MERCHANT_AUTHORIZATION_CONSUMER_CONTRACT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: evaluator_design
Contract state: DRAFT_CONTRACT
Owner: Evaluator
Dispatch status: NOT_DISPATCHED
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-31-r85
Active bottleneck: B-17

## 全局位置与唯一目标

项目目标是令高风险支付的授权、绑定、执行、恢复与审计可独立复核。A–D阶段关闭，E仅本地受控代表性验证，F当前；H52只测量并已PASS，产品能力未升级。B-17从组合未知缩为已测出的签验事实/业务投影断口及商家消费合同缺失。

下一目标只收敛一个商家执行前的授权消费合同：明确来自哪份已验证原文、由哪个预置信任责任方确认、怎样与现有claim（持久执行占用）中的同一checkout快照绑定。优先解决此输入合同，再考虑版本迁移或服务方接入；不继续扩大H52材料矩阵、不重做H51锁/HTTP切片。

## 尚未满足的精确冻结条件

本草案不等于实现授权。冻结Executor任务前，Evaluator须用既有材料先关闭以下问题，并直接形成最终CONTRACT与VALIDATION_PLAN，不增加另一套交接规范：

1. **载荷与版本边界**：选定一个完整原生checkout样本及其规范来源、完整字段/未知字段保留、签名覆盖范围、complete请求与ap2.checkout_mandate的确切格式；给出AP2 v0.2.0两跳SD-JWT与2026-08-25 UCP凭据的可复用和不可互换部分。H52四字段compact JWS不能直接充当该样本。必须比较“完整2026-08-25升级”与“明确声明边界的本地消费切片”，不能预设全面升级是最小改动。
2. **序列化与独立判定**：现有零安装环境是否已有适用的完整JCS（JSON规范化）机制和可独立校验的输入向量；若没有，准确列出所缺依赖/样本，不能用排序JSON替代完整JCS或默默安装。冻结前必须确定可执行的正负判据。
3. **可信来源与接线责任**：选定一种明确的研究信任模型及本地公钥/确认事件的来源、时效、checkout绑定、撤销与claim先后；核对H51既有确认及商家工厂可复用部分，指定任务副本的唯一不可绕过入口及读取/写入边界。允许明确标记的合成研究角色，不能要求先找到付费客户，也不能把合成确认升级为真人身份或生产同意。
4. **可冻结的最小范围**：列出允许修改的新任务副本文件、保持只读的产品/旧任务、确切验证命令和预算。对金额/币种/收款方的已签原文、投影与执行快照做同值约束，且密码学失败必须阻止下游执行；证明无需另建通用授权服务或重写已有锁/恢复机制。

这些是Evaluator需补的技术证据，当前不要求Human提供账号、密钥、资金或客户。若材料不足且需要新增依赖、外网或新的运行方式，再明确申请对应最小授权；不能把草案当授权。

## 候选验收方向（未冻结、未执行）

正常可信原文经验证后只生成一次绑定付款；替换根、签验失败、原文/投影/执行快照金额币种收款方不一致、缺确认、更新后仍用旧授权、重复/换键重放及直连旁路均不能形成错误付款。恢复沿用既有稳定引用，不重复扣款。协商锁定与完整JCS若纳入下一合同，须有独立向量和负例；否则必须写清切片不具完整UCP/AP2兼容性。

实际AC与验证计划须在上述输入就绪后冻结，此处不伪造可运行计划，不统计未来测试为通过。

## 提议预算与停止条件

后续设计工作建议最多2主动小时，只读既有资料/源码；零模型、外网、ASGI、Provider（支付服务方）、付款、安装、对外联系及Git写操作。该预算是未派发草案，不沿用H52剩余预算。不运行新商家、不修改src/tests或H37/H47–H52。若只能形成完整商家重写、缺可判定输入、或继续设计无新证据，STOP并保留精确缺项；若就绪，另冻结一个有界实现合同，不能自动执行。

## 外部要求与残余风险

已复用PCAC开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=H52离线测量已复核、商家消费未建；after目标=仅合同与判定可冻结，产品成熟度不变；Test/Evidence=待精确样本/命令冻结，不宣称已测；残余=真实主体、完整协议兼容、生产密钥治理、跨系统撤销、Provider与客户未知。无监管合规结论。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
