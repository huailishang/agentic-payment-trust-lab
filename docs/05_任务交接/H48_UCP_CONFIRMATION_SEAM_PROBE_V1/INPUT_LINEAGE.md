# H48 输入来源 / Input Lineage

本表记录固定 H47 UCP 商家返回值与本任务显式合成信任配置之间的边界，不作为生产可信性证据。实现代码只执行纯数据投影，不访问外网、商家或支付接口。

| 内部 Order 字段 | 确切来源 | 限制 |
|---|---|---|
| order_id, checkout_ref | 真实商家 checkout.id | order_id 加本地 `h48-checkout:` 前缀；不是完成后的商家订单 |
| items.item_id, name, unit_amount, quantity | 商家 line_items[].item.id/title/price、quantity | 全部保留；价格为整数美分，经 Decimal / 100 |
| items.category | TRUST_FIXTURE.category_by_item[item_id] | 合成测试配置；不可通过商品名称推断 |
| total_amount | 商家 totals 中唯一 type=total.amount | 不加 subtotal；缺失、重复、负数、bool、字符串/浮点均拒绝 |
| currency | 商家 currency | 只支持显式 USD；绝不默认 CNY |
| merchant, payee | TRUST_FIXTURE 的 merchant/payee | 合成身份与收款配置，非真实身份验签 |
| mandate_ref, authority_version_ref | TRUST_FIXTURE authority_id/authority_version | 合成授权引用，非持有证明 |
| service_id, fulfilment_terms | TRUST_FIXTURE 显式字段 | 仅实验约定，非完整 UCP 履约标准 |
| quote_expires_at | TRUST_FIXTURE 显式带时区日期 | 不是原生服务端锁定的报价有效性 |
| order_version | 本项目 canonical_hash(confirmation_order_payload(order)) | 本地内容摘要，不是 UCP version，也不代表 CAS/原子绑定 |
| candidate_rails | 固定空 tuple | 不进行实际支付通道识别 |
| final_order_ref | 投影阶段始终 None | 只能从完成后原生商家响应另取，不提前编造 |

## 输入失败规则

所有必填身份、收款、授权、分类、服务、到期时间及商家快照数据缺失时，`project_checkout` 返回 `order=None` 与非空 `missing`，不通过默认字段、假造订单编号、合成 Provider proof 或调用 merchant 完成路径来弥补。函数不改变输入和全局对象。

## 控制边界

已有 confirmation_order_payload、create_confirmation_record、verify_confirmation_binding 和 execute_with_confirmation_gate 只作用于使用这些方法的客户端路径。必须通过 H48 正式九场景双轮观测确认其结果。检查后发生变化和直接调用 Merchant complete 的绕过路径应完整保留在证据中；不把它们称作 UCP 官方漏洞，也不声称生产服务端得到原子性保护。
