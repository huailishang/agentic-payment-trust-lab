# H47 执行接缝与最强反对理由
## 谁能写与副作用
在本夹具 require_signatures=True 下，持有 profile 所列临时私钥的客户端能发出签名请求。这不是端用户、收款人或 executor 的完整身份鉴别。原生 complete 未读取本项目 ConfirmationRecord/IntentMandate。创建持久化 checkout/幂等记录，检查库存但不预占；更新改数量/总价并持久化，不预占。完成先调用 _process_payment，再校验履约，然后 reserve_stock 原子减库存、生成独立 order.id，与 checkout/幂等记录提交。取消持久化 canceled，不扣库存、不退款；GET checkout 写 request log 并读当前状态。创建/更新/完成/查询有运行记录；取消只有源码证据（checkout_service.py:1104–1161）。

## 核验至执行与旁路
C02 体现签名合法但结算已不同于初次确认。外部先 GET 再验 ConfirmationRecord 再 POST complete 仍可能被另一个更新穿插。checkout 数据表无版本字段；完成请求 hash 不包含先读快照的摘要，也无预期版本 CAS。库存条件更新只解决库存计数，并不原子绑定用户确认。并发、崩溃和竞争均未测，不宣称消除竞态。
只包装客户端 callback 不控制直接 REST、PUT /orders、入站 webhook、cart 或 shipping simulation。签名验证也不是本项目授权闸门。日志在副作用后记录不能阻断不同意的数量变化，也不能提供付款原子性。

## 最小候选边界与反对理由
可先考虑任务内只读 checkout snapshot 投影，保留 checkout_ref、最终 order_ref、USD 整数总额、来源路径、缺失清单；复用 models、confirmation.confirmation_order_payload、validator.validate_request 的输入规则与 authoritative_trace_consumer 的事实消费边界。禁止占位 payee、mandate、agent/provider/executor 或支付证明。
若未来要执行控制，需可信独立授权输入，并在真正完成入口中绑定已核验快照且封闭旁路；这超出单纯客户端薄适配。现有 governed_action 仅 execute_payment/PAYMENT_EXECUTION，不能硬套 create/update/cancel。最强反对理由是当前缺关键身份/支付事实且无 CAS，适配可运行并不证明安全增益；应先冻结缺证据失败关闭与快照绑定的可证伪小实验，而非立即扩核心或接真实支付。本包未实现任何候选。
