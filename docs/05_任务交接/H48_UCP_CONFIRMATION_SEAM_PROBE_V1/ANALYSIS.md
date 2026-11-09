# H48 客户端确认边界分析

本任务唯一增量是受限 UCP checkout 到项目既有 Order 的忠实纯投影，并复用 P1 confirmation 记录与执行前核验。没有改变支付核心、商家源码、金额授权语义或真实 Provider 验签。依赖的 TRUST_FIXTURE 明确为合成数据，不能自动得出身份或交易安全认证。

## 本地 L1 真实观察

基于冻结原生 Merchant 和测试环境，9 类场景各重复两次、52 个进程内 ASGI 请求。G01 在订单无变化时 confirmed fact=VALID/ALLOW，商家 complete 1 次、mock payment 1 次、库存 5→4。G02 在确认后、核验前把数量改成 2，fact=INVALID/order_hash_mismatch，CONFIRMATION_REQUIRED，complete/payment/order 均 0，库存仍 5。G03/G04 缺合成 payee/authority、G06 删除响应复制件上的 currency，均为 MISSING_EVIDENCE/INDETERMINATE，不能进入模拟结算；G05 过期后 fact=INVALID，complete 0。

L01 在确认核验已通过（核验时数量 1）之后，外部模拟商家合法更新成数量 2，再执行已拿到的 fact，商家 complete 1、payment 1、库存 5→3；这说明本地检查与最终执行之间存在可穿插窗口，不是并发压力测试。L02 不调用确认门禁，而是直接调用原生商家 complete，同样完成修改后的 2 件交易。N01 原生对照也允许修改后正常结算；这是已冻结商家行为，不是 UCP 标准漏洞或通用服务端不可用结论。

## 有效结论与强备选

在固定合成商家和合成身份下，`CLIENT_GUARD_ONLY` 是本包合理分类：对于确实进入项目 P1 客户端闸门的调用，变更与缺证据能够 fail closed(证据不足拒绝)；服务端其他入口和检查后更新不在该局部控制内。不能宣称原子快照绑定、完整产品闸门、真实支付安全适配、Provider proof、模型攻击防护或客户需求已验证。

相对选择：继续增加同类客户端校验可积累局部样本，但不能覆盖不经过该客户端的入口；候选更值得测的是最小服务端原子绑定：以有来源且可验证的确认快照阻止交易内容变化后仍被 complete，并保持正常结算及原生幂等行为。此事目前未实现、未验证，必须由 Evaluator 另冻小包再执行。

公开商家/交易团队的商业筛选沿用 H47 的研究材料，需求仍为 UNKNOWN。本轮没有联系任何商家、客户或支付团队，也没有外部 API、模型或真实付款。