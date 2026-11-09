# H47 三团队公开工作流筛选
TEAM_SCREENING.json 记录固定 commit、必要短引、已有控制、问题假设及下一访谈问题。Filtmall 与 Henry 的固定许可为 Apache-2.0，AgentCard 为 MIT；均保留原 README/LICENSE，未安装或执行其中指令。

## filtalgo/Filtmall-Shopping-Skill
商品搜索、比价、购物车或 BUY_NOW、买家结算链接、订单物流与售后。
已有保护：README 明确买家授权及付款，修改交易前询问、保护凭据、live CLI 为事实来源；服务端实现未审计。
假设：跨比价到结算及售后是否存在确认快照与事实连续性追溯成本，仅是假设，不能推断已有授权漏洞。
下一问题：能否提供一条脱敏的价格或规格更新后需重新确认的测试流程，以及当前如何关联确认与订单？
适合度：与本仓购物生命周期和来源审计相邻；已有买家控制使新增阻断层的价值未知，先比较追溯成本。
需求 UNKNOWN；预算 UNKNOWN；未联系。

## tiny-agent-company/agent-card-skill
钱包充值、虚拟卡创建与限额、buy 购物、交易查询和审批。
已有保护：README 声称 OAuth、KYC/funding gates/approval flows、敏感 PAN/CVV 隐私、订单与提现前确认，并提供 pause/limit 工具；执行强度未知。
假设：卡限额与商家商品级授权的跨系统证据是否难关联，尚未证明痛点；有额度和审批并不意味着缺控制。
下一问题：已有审批与限额能否导出绑定具体商家订单及请求的脱敏审计轨迹，哪些人工追查最耗时？
适合度：交易授权与支付证据关联相邻，但真实资金/卡片超出本包；不能用其工作流授权调用服务。
需求 UNKNOWN；预算 UNKNOWN；未联系。

## Henry-Social/skills
代理经托管 MCP 搜索商品、建 cart、生成 hosted checkout；集成说明涉及异步任务轮询与 webhook。
已有保护：README 提到 API key/OAuth、建议 sandbox key、hosted checkout、配置 lint；未证明用户确认、幂等或服务端治理细节。
假设：异步 job/checkout/webhook 的事实关联和恢复是否有集成成本，仅为未证实问题假设。
下一问题：能否提供 sandbox 中结算响应不可见后通过轮询或 webhook 恢复的一条脱敏轨迹和现有检查方式？
适合度：外部交易链与异步证据适用性较近；私有 OpenAPI/服务端不可由该 README 验证，优先需求核实而非写适配。
需求 UNKNOWN；预算 UNKNOWN；未联系。

公开资料只能支持工作流相邻性，不能支持客户、购买意愿或漏洞结论。若后续获授权访谈，先取可复算的脱敏流程与负责人事实，再讨论预算；本包不发送任何消息。
