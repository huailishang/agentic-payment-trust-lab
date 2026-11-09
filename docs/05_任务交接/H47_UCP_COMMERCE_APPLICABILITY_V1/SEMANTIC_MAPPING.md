# H47 语义映射
MAPPING.json 是逐项权威清单，共 17 项，每项列固定 source path/line、状态、项目真实目标和观察引用。观察短名对应 evidence/measurements_l1.json 与后续 measurements_l2.json 的 cases[].case；两轮 repeat 0/1。最终证据以 L2 为准。

原生可直接保留 checkout.id、完成响应 order.id、currency、totals 中唯一 total 的 amount、幂等和持久查询。订单创建前 checkout 与最终 order 不是同一对象；不可为满足 Order 必填字段提前制造最终订单。USD 从最小单位转 Decimal/100，禁止浮点及默认 CNY；项目类别、有效期、履约规范等也需明确映射，不能默认等同。
初次快照的合成确认属于 DERIVED 且来源是实验显式 fixture；HTTP 签名证明临时私钥可用，不证明用户授权。merchant URL、profile/keyid 不提供可信 payee/provider/executor；mock completed 无 receipt/payment_id/Provider proof。缺字段应维持缺失，让产品失败关闭，不能靠赋默认值运行出 ALLOW。
ucp.version 是协议协商，不是订单版本。可派生内容摘要作为观测版本，但不提供服务端 CAS。GovernedPaymentAction 需要 authority/order/request/payment 多重引用；当前不能忠实构造已验证完整实例。因此本包不运行完整 gate/consumer 对照，full_product_gate_comparison=NOT_MEASURED。

## 项目代码出处与复用约束
路径均相对仓库根；下列为实际类型/函数，未在本包调用它们构造伪造事实。

| 映射组 | 项目代码出处 | 约束 |
| --- | --- | --- |
| user_authority/confirmation_origin | src/agentic_payment_experiment/models.py:91 IntentMandate；trusted_execution/confirmation.py:28 ConfirmationRecord、create_confirmation_record、verify_confirmation_binding | 用户授权与确认需独立可信来源及有效期，不从商家当前状态反推 |
| checkout_id/final_order_id/order_version | models.py:132 Order；trusted_execution/governed_action.py:45 GovernedPaymentAction | 保留两个外部 ID 的因果关系，缺版本/授权不能用占位值补齐 |
| amount/currency/merchant/payee | models.py:106 TransactionRequest、132 Order；trusted_execution/confirmation.py:66 confirmation_order_payload | USD 最小单位精确转换，确认覆盖商家/收款人/数量/总额及履约；可信收款人缺失 |
| agent_identity/credential_possession | models.py:82 AgentIdentity；trusted_execution/credential_possession.py:29 CredentialPossessionVerificationFact、51 verify_x509_svid_credential_possession | UCP 临时 HTTP 签名不是 X509-SVID 验证事实，不可直接移植算法/证书或升格 |
| request_payment_binding/payment_result/idempotency | models.py:149 PaymentExecutionRecord；trusted_execution/payment_binding.py:74 verify_payment_execution_binding；webshop_runtime_gate.py:73 gate_webshop_buy_now | 独立 payment/request/authority 引用缺失，不能把幂等 key 当 payment_id 或把 completed 当 Provider 证明 |
| query_recovery/execution_seam | models.py:167 PaymentStatusObservation；payment_execution.py:observe_payment_execution_gate；webshop_runtime_gate.py:gate_webshop_buy_now | callback 是注入式接缝，未控制 UCP 服务端，查询只是商家事实 |
| trace_consumer | authoritative_trace.py:198 ProductAuthoritativeTrace；authoritative_trace_consumer.py:143 consume_authoritative_trace | consumer 先校验闭合合同才开放 read model，原生日志未满足来源绑定及事件合同 |

除 models.py 外，表中 trusted_execution 等文件均位于 src/agentic_payment_experiment/。类别、quote_expires_at、mandate_ref、fulfilment_terms 等 Order 必填语义也没有在本包填入默认值；它们与 17 项主矩阵一同阻止“造完整对象即可接入”的推论。核心改变需多个独立消费者重复证明需要，本样例不足以授权扩核心。
