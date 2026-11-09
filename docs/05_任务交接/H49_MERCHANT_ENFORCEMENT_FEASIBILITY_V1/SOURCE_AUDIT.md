# H49 S1 — 11 个服务端入口与持久化边界审计

来源：H47 锁定的 UCP Python merchant 49 文件，commit `99724a32da48bd0f4962c83e25f17c8345ce055e`（Apache-2.0）；下列为源码静态证据，不是运行、并发、崩溃或 Provider 验证。

## 真实执行链

`routes/ucp_implementation.py:208–233 → CheckoutService.complete_checkout:713–937 → idempotency lookup:737 → checkout load:756 → _process_payment:760 → reserve_stock:787 → save_order/save_checkout/save_idempotency:897–917 → commit:928 → webhook:930`。`checkout_complete` 只出现在 request hash 构造（729–730），不等于授权确认验签。`_process_payment` 是样例商家模拟支付，不是外部 Provider 扣款；它发生在库存/订单提交之前，失败后无法由数据库事务自动回滚已发生的外部付款。

## 11 个检查单元

1. **create_checkout**：建立可修改的结算快照；无付款执行。 **读：**读 idempotency_records、可选 cart、product/catalog；检查重复 key。 **写：**写 checkout 会话、请求日志及 idempotency_records；可能复用未完成的 cart checkout。 **交易关联：**支付准备入口，价格/商品确认应针对随后实际可执行的 checkout 版本。 **边界：**直接请求服务端创建新 checkout 不经过 H48 客户端确认门禁，不能据此推定付款被放行。 **处理：**创建流程无需最终支付确认；服务端生成稳定 checkout 引用并对随后完成核验提供可信版本基线，禁止伪造授权。 来源：`services/checkout_service.py#CheckoutService.create_checkout:160-171`；`routes/ucp_implementation.py#create_checkout:142-165`。

2. **get_checkout**：查询 checkout，可能用于 UNKNOWN 查询恢复，非付款调用。 **读：**读 checkout 当前持久化记录。 **写：**写 GET 请求日志、提交日志事务；不改 checkout 交易内容。 **交易关联：**状态查询可作为商家事实来源，但不等于支付服务商终局确认。 **边界：**查询接口自身不是绕过付款；误把其副作用称为结算风险会掩盖真实 write seam。 **处理：**保留有权限的状态查询和不可变轨迹，区分商家状态与 Provider 事实；不要对纯 GET 加不相关新付款闸门。 来源：`services/checkout_service.py#CheckoutService.get_checkout:462-470`；`routes/ucp_implementation.py#get_checkout:169-180`。

3. **update_checkout**：合法改变已生成结算快照，未发起付款。 **读：**读 idempotency、checkout 当前值、商品/库存及价格。 **写：**写 line_items/quantity/payment/fulfillment 的商家 checkout 快照、请求日志、幂等缓存。 **交易关联：**正是 H48 检查后改变订单内容的可穿插更新入口。 **边界：**签名有效的更新可在客户端授权核验之后、服务端 complete 之前穿插；不能用本进程锁代替共享版本约束。 **处理：**必须与 complete 共用持久化 checkout_version/CAS 或同一数据库行锁；每次实质变更使旧确认失效。 来源：`services/checkout_service.py#CheckoutService.update_checkout:483-508`；`services/checkout_service.py#CheckoutService.update_checkout:686-710`；`routes/ucp_implementation.py#update_checkout:183-205`。

4. **complete_checkout**：唯一明确的模拟付款核心执行入口。 **读：**先读 idempotency_records；未命中再读 checkout、状态、支付输入和商品库存。 **写：**先 _process_payment 模拟支付；后修改库存、订单、checkout 终态、幂等记录并 commit。 **交易关联：**必须实现确认来源/授权撤销/快照一致性到付款调用前的商家侧安全门禁。 **边界：**checkout_complete 只进入请求哈希未见验签和真实授权绑定；原生签名验证不等于用户确认；付款早于事务提交。 **处理：**服务端入口检查用户确认凭证/版本/有效期并绑定不可变执行快照；多实例共享写锁/CAS；付款前持久化 attempt，付款后查证与补偿。 来源：`routes/ucp_implementation.py#complete_checkout:208-233`；`services/checkout_service.py#CheckoutService.complete_checkout:725-760`；`services/checkout_service.py#CheckoutService.complete_checkout:781-792`；`services/checkout_service.py#CheckoutService.complete_checkout:897-934`。

5. **cancel_checkout**：取消未完成 checkout，不是支付退款操作。 **读：**读 checkout/idempotency 与现有状态。 **写：**写 canceled checkout、请求日志、幂等记录；不触发退款。 **交易关联：**必须避免 cancel 与 complete 同时竞争造成已付款而会话取消的分裂事实。 **边界：**外部客户端只保护 complete 不会协调并发 cancel；但取消本身不能冒充真实冲正。 **处理：**与执行占用同一商家行状态协调；付款已启动时标记取消待处理与查询/退款人工责任，不假设自动退款。 来源：`services/checkout_service.py#CheckoutService.cancel_checkout:1104-1161`；`routes/ucp_implementation.py#cancel_checkout:236-247`。

6. **create_cart**：购物车准备，不触发付款。 **读：**读 idempotency 和商品信息。 **写：**写 cart_session 和 idempotency_records。 **交易关联：**cart 可作为后续 checkout 的内容来源，转 checkout 时要保存准确快照。 **边界：**仅建购物车不是支付旁路；控制若只盯 checkout 不应误判 cart 写操作为付款。 **处理：**cart→checkout 血缘需记录，进入付款前以 checkout 的商家当前值重新计算确认摘要。 来源：`services/cart_service.py#CartService.create_cart:91-110`；`routes/ucp_implementation.py#create_cart:250-265`。

7. **update_cart**：购物车编辑，不直接付款。 **读：**读 cart_session 和 idempotency。 **写：**写购物车商品数量和明细、幂等记录。 **交易关联：**若 checkout 由 cart 创建，内容一致性必须以最终 checkout 版本核实。 **边界：**修改购物车可能影响后续来源，但现有 source 不证明它会自动更新已生成 checkout。 **处理：**在创建 checkout 时记录实际复制快照，禁止从单独 cart 变更推断已经改变现存 checkout。 来源：`services/cart_service.py#CartService.update_cart:203-232`；`routes/ucp_implementation.py#update_cart:278-292`。

8. **cancel_cart**：清理购物车，无付款。 **读：**读 cart_session 和 idempotency。 **写：**删除 cart_session 并写幂等记录。 **交易关联：**未完成 checkout 可能仍引用原 cart_id；取消不是付款撤销。 **边界：**cart 删除不是消费付款旁路，不得把它当退款或关闭既有订单。 **处理：**记录 checkout↔cart 来源，独立保证 complete 的 checkout 快照与确认一致。 来源：`services/cart_service.py#CartService.cancel_cart:283-327`；`routes/ucp_implementation.py#cancel_cart:295-305`。

9. **update_order**：付款后订单记录变更，不发起新付款。 **读：**读既有 order 是否存在并解析请求正文。 **写：**直接覆盖 order JSON 并 commit；服务端方法未见与 checkout 确认状态联动。 **交易关联：**会影响履约和最终审计事实可信度，应与支付时订单绑定分清。 **边界：**订单写接口能篡改付款后事实展示，但源码不表明可以调用付款；不能标为直接付款旁路。 **处理：**按权限限制 post-payment order mutation；建立版本及事件记录，金额/付款核心字段只读或强审批。 来源：`routes/order.py#update_order:70-90`；`services/checkout_service.py#CheckoutService.update_order:1173-1188`。

10. **ship_order**：测试用履约动作，无新付款。 **读：**读 order、关联 checkout 与模拟测试密钥。 **写：**写 fulfillment.shipped 事件/订单；模拟发送 webhook。 **交易关联：**与完成后补救/履约审计相关，但不应视为可直接付款。 **边界：**已知路由有 Simulation-Secret 校验，不代表正式第三方履约授权；不是支付入口。 **处理：**保留测试入口独立隔离，履约修改事件要关联可信订单 ID，不能回写覆盖已确认金额。 来源：`routes/order.py#ship_order:49-67`；`services/checkout_service.py#CheckoutService.ship_order:1061-1102`。

11. **order_event_webhook**：入站订单事件改变商家订单视图，不调用 _process_payment。 **读：**验签依赖读取签名材料，按 payload.id 读取既有订单。 **写：**将传入 Order 对象覆盖写入本地订单并 commit。 **交易关联：**可能改变消费后订单解释与事实连续性，属服务端权限及订单写边界。 **边界：**存在签名依赖但未在本包验证身份/重放/字段授权；不能推定 webhook 足以覆写结算权威事实。 **处理：**独立校验事件来源、订单标识、状态迁移与签名上下文；仅准修改授权字段且 append-only 留证。 来源：`routes/ucp_implementation.py#order_event_webhook:308-325`；`services/checkout_service.py#CheckoutService.update_order:1173-1188`。

## 路由与安全边界

- `routes/ucp_implementation.py:328–340` 将 operation_id 绑定实现；`server.py` 装载 generated checkout、cart、order 与 MCP 路由。MCP `tools/list` 不等于实际可发起交易；原样例 `tools/call` 不实现（H47 SOURCE_AUDIT）。
- 签名流程位于 `dependencies.py:75–168` 与 `ucp_signing.py:483–588`；当前夹具开启 `require_signatures`，仅证明拥有相应测试 key 的请求可通过签名校验，不证明最终用户支付确认、代理授权或商户收款人归属。
- **需要同一执行边界保护的写路径**：`update_checkout`、`complete_checkout`、`cancel_checkout` 以及任何可直接修改 checkout 的内部/管理写接口，必须共享行级原子版本状态；`create_checkout` 建初始快照。订单更新/入站 webhook 需独立的后付款事实完整性边界；cart 与 shipping 属衔接/履约域，不是模拟付款旁路。
- `GET checkout` 虽写请求日志并 commit，但不发新付款；幂等缓存返回旧成功是查询已有结果，不能等同新支付授权。`update_order` 与入站 webhook 可能改变订单证据但没有调用 `_process_payment`，不可错误定性为直接付款旁路。
- 未覆盖：跨进程数据库直写权限、真实支付 PSP、真实凭证、崩溃窗口、两个独立并发事务实际效果。静态源码不能证明竞态已闭合。
