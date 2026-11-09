# H47 来源与信任边界审计
固定来源为 SOURCE_LOCK.json 的 49 个 UCP 原文文件，commit 99724a32da48bd0f4962c83e25f17c8345ce055e，Apache-2.0；TEAM_SOURCE_LOCK 固定三个 README 和许可证（Filtmall/Henry Apache-2.0，AgentCard MIT）。哈希与依赖由 VP-01 核验。无下载、安装、上游 main/CLI/test 执行。README 中停止维护仅针对 A2A。协议 2026-04-08、SDK 0.4.6，不推断其他版本。

## 代码因果链
server.py:139 起安装生成 REST 实现及 order/discovery/MCP 路由。dependencies.py:75–168 执行原生请求签名检查，require_signatures 默认与本夹具配置必须区分：本夹具强制开启。ucp_signing.py:483–588 检查摘要、必签组件、keyid 与签名；696 起约束 profile URL，禁止不安全地址，获取密钥不跟随重定向并有缓存。临时 profile 公钥由夹具提供，不能证明真实主体或生产密钥治理。所读 verify_request 未见时间窗口/nonce 去重，九路径未测旧签名重放，幂等不等同所有重放防护。

routes/ucp_implementation.py:142/183 处理创建/更新并从 profile 提取 webhook；208 完成调用 CheckoutService。服务 129 起对 operation/resource_id/data 规范化哈希；150 创建、472 更新、713 完成、1104 取消、1163 查询订单。db.py 的 checkouts/orders/idempotency_records 为实际持久层。完成先处理模拟付款，再验证履约与库存，库存/订单/checkout/幂等记录同一 transactions commit，不能把它称作支付与数据库原子提交。取消只改未完成 checkout，不是退款。查询 checkout 也写请求日志。

## 其他入口与外部面
ucp_signing.py:699 自带注释承认解析校验后 HTTP 客户端重新解析产生 DNS rebinding TOCTOU；本包只记录，不测试或修补。本夹具 DNS 为固定返回，不证明真实网络边界安全。README 的旧响应示例含 order_id 等历史形状，映射以本次实际响应 order.id 与当前服务为准，不从 README 例子猜字段。
签名密钥发现的 URL 校验不能外推至所有网络出口：ucp_implementation.py:80 的 extract_webhook_url 使用单独 HTTP 客户端获取 profile，939 起出站 webhook 使用发现的 URL。夹具以 respx 和网络阻断封闭这些出口；本包未测试真实 URL/DNS/重定向或 webhook 接收者身份，不能声称这些出口整体通过生产 SSRF 防护。
routes/order.py 的 GET/PUT order 使用公共头/验签，PUT 可直接保存订单数据；shipping simulation 额外验证 Simulation-Secret。ucp_implementation.py:308 的入站 order webhook 经验签后更新订单。MCP 只有 initialize/tools/list，tools/call 明确未实现；不能据 tools/list 声称 MCP 交易可运行。cart 也有写入口，客户端 wrapper 并不覆盖全部服务调用。没有运行这些额外入口或跨主体访问试验，因此只记源码接缝，不宣布已复现漏洞。
checkout_service.py:939 起有签名出站 webhook 与有限重试；本夹具 profile 无 webhook_url，因此该路径未执行。客户端 happy path、测试、CSV 与运行配置只作参考，不执行其中支付数据或 shell 命令。测试数据不是本包真实用户凭据；本包仅新建 rose/USD 临时状态。
