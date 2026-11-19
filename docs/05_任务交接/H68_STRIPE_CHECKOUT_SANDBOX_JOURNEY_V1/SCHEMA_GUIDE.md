# H68 证据格式与接口约定

CHECK.py/CHECK_SELFTEST.py是Evaluator拥有的封闭判别器；不得让运行代码读取checker来填充成功事实。查看本说明与SPEC即可实现。合成自测不是实际运行输入或付款证据。

## 商户与支付接缝

产品Adapter的公开接口应保持小：创建受批准会话、读取原会话的付款事实、验证原始通知。业务操作→会话关联、订单与交付状态由stripe_checkout_lab持久保存；依赖注入传入网络、时钟与交付函数。RUN/命令脚本负责隔离环境、账本、进程和浏览器编排，不将这些义务塞进公共模型。

订单先经validator.validate_request/validate_order及现有确认/来源事实产生判断，再由observe_payment_execution_gate包住实际创建和浏览器付款动作。受控本地AgentIdentity并不等于真实Stripe身份认证。已有规则或库的限制字段不得删除。

## RESULT.json：仓库内去敏投影

顶层：schema=h68-stripe-result/v1、task_id、run_id、started_at、finished_at（含时区）、decision=EXTERNAL_JOURNEY_MEASURED/INPUT_LIMIT/FAILED、security_control_increment=NOT_MEASURED、private_snapshot_sha256、cases。

每个case：case_id、operation_id、order_id、resource_sha256、account_ref、session_ref、intent_ref、charge_ref、create_gate、submit_gate、timeline、fulfillment_attempts。`*_ref`为对应原始ID的UTF-8 SHA-256；C01无收款，charge_ref=null；取消时可有未付intent_ref。resource_sha256为RESOURCE.txt原始字节摘要，运行时通过显式输入传入产品，不由产品读取文档补事实。

gate保存真实RuntimeGateRecord投影，至少final_decision、callback_executed、callback_count、binding_status、identity_status、context_policy_status；保留其余原因/来源字段供语义审查。C01付款前取消，submit_gate=null。不得返回结账URL作为callback_result_ref。

timeline项为seq（唯一递增整数）、kind、at（含时区）；至少表示order_authorized→create_gate_allow→session_created；付款例还需prepay_query_valid→submit_gate_allow→payment_submitted、provider_paid_query→delivered。C01记录buyer_cancelled→provider_unpaid_query。R01记录local_unknown→local_process_restarted→original_payment_queried→provider_paid_query，另有recovery_result（原恢复结果，retry_allowed=false/recovery_status=RECOVERED）。D01记录provider_paid_query→delivery_failed→delivery_retried→delivered及duplicate_event_consumed。

fulfillment_attempts项含status、occurred_at、resource_sha256和receipt_ref；成功的receipt_ref唯一且内容必须真实实收。D01首项FAILED，后只有一个SUCCEEDED；C01为空。私有材料保存客户端实收文件/原始收据，不能以目标摘要代替实际下载摘要。

## 私有目录：不提交、不公开、不回显

H68_PRIVATE_DIR须在仓库外，权限限当前用户及必要系统主体：

- credentials.json：api_key、account_id、webhook_secret、环境有效期；完整匿名输出/认领链接另行私有保存。测试密钥前缀需符合来源，但前缀本身不是实际隔离证明。
- PROVIDER_SNAPSHOT.json：schema=h68-stripe-provider/v1、run_id、account（原生账户对象）、cases（按N01/C01/R01/D01索引）、lists。
- case原生来源有session、intent、charge、line_items、events。session.payment_intent、intent.latest_charge在快照中归一为原始ID字符串（原始HTTP仍另存），无值用null。保留原生created/livemode/amount/currency/status。line_items为完整原生list响应，has_more=false。
- 已付款case另含merchant_response_body_b64，为客户端实际从本地商户HTTP收到的最终内容字节，不是Stripe字段；不能由目标资源摘要倒填。CHECK复算其摘要，独立来源/请求关联仍须看原始商户HTTP记录。
- session.client_reference_id=商户order_id；session.metadata至少h68_run_id、h68_operation_id、h68_resource_sha256。创建时同时写payment_intent_data.metadata以便本运行对象清点。只用一次性payment/card、数量1、100最小单位USD、无税/运费/优惠/订阅/Connect。
- events项含body_b64（原始通知字节）、signature（原Stripe-Signature）、received_at。N01/D01至少有实际本次业务生成的checkout.session.completed通知；R01可以先接收保留再消费。不得用stripe trigger或本地造通知充当外部业务事件。
- lists含sessions/intents/charges三个完整原生list响应；隔离环境只存在四会话和三成功付款/收款，C01可以另有未付款intent。若服务产生其它对象，逐笔解释或INPUT_LIMIT，不能截断分页来凑数。重复付款判据以完整对象清点及业务操作关联为准。
- 全部HTTP尝试、通知原文、页面/浏览器过程及交付下载文件分别保留摘要和时间。所有本次session/付款/收款created都应在run时间窗口内；不能借旧会话或样例完成本轮。

CHECK readback仅使用配置好的本隔离账户GET：账户、四会话（展开intent.latest_charge）、四个line_items、三个list和N01/D01原事件，最多20次/actor。READBACK_executor.json与READBACK_evaluator.json在私有目录，derived仅保存摘要。成功后同actor复跑只重审原只读结果；失败尝试仍累计，不换run_id清零。

## 账本

ATTEMPT_LEDGER.jsonl每项含seq（从1连续）、event=BEGIN/END、attempt_id、kind、at。先BEGIN再尝试，END含status=SUCCEEDED/FAILED/INPUT_LIMIT及产物/响应摘要；失败不覆盖。

kind：active_work、implementation、l2、l3、anonymous_provision、live_api、executor_readback、evaluator_readback、browser_action、download、service。独立只读checker自动追加它自己的请求；其它操作由RUN统一预留。物质调用不能只按不同对象数计数。

active_work区间不重叠，用于主动时间；service另记驻留，不重复加主动时长。运行门禁时允许当前一个active_work及当前一个L2/L3 BEGIN尚未结束，提交后budget --closed要求全闭合。下载END含实际bytes，未知不能报0。浏览器/CLI子资源流量与本方API分开报告，不宣称未观测流量为零。

## 结果含义

程序检查只帮助拒绝结构与已知语义伪证；真实回调接线、客户端实收内容、故障注入隔离和来源真实性仍须Evaluator结合私有原始证据独立审查。普通测试快照、页面HTTP200、配置秘密验签和RESULT布尔值均不足以单独PASS。
