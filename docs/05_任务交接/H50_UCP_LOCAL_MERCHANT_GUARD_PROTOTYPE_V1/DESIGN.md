# H50 本地商家原生方法级执行占用样机设计

## 保留的原生行为
保留创建商品、履约选择、库存预留、订单写入、原生支付凭据校验、终态持久化和已有幂等记录。不修改上游UCP副本其余33个文件、不修改主产品源码。仅在固定副本指定方法加入本地执行占用；本模型不提供HTTP入口。

## 合成可信来源与事务协调
由Evaluator冻结夹具注入 merchant/payee、可信确认颁发器、受控时间、持久模拟账本。确认引用只用于查询本地可信确认行，不能由请求payload自行定义付款快照。
同一个transactions.db增加 h50_confirmations 和 h50_attempts。事务A通过 SQLite BEGIN IMMEDIATE 核对原生checkout状态、引用、过期和撤销，比较 line_items、totals、currency、fulfillment 及 merchant/payee 的完整规范化JSON，唯一checkout占用及唯一payment_ref与 IN_FLIGHT 在发款前COMMIT。before_claim在写锁外，before_claim_commit在事务内部，after_claim_commit在独立可读提交以后。
update/cancel在原生同一事务连接上获取 BEGIN IMMEDIATE，检查占用后才操作；claim先赢则拒绝后续写入，update先提交则claim快照不匹配。原生订单/库存/幂等在事务B提交，B失败不影响A与独立付款账本。原生付款入口经execution对象取稳定引用与快照；模拟端每次charge都会单独记录，不靠PSP去重掩盖重复调用。

## 故障与恢复
after_payment允许子进程直接退出；before_order_commit模拟事务B失败，库存/订单回滚。恢复按A的payment_ref在独立账本查询，不能根据本地UNKNOWN标识臆造退款或盲目再次charge。查询为成功仍保留人工对账/补单责任，查询未见付款也只WAIT/QUERY，不自动重发。

## 最强反对理由及限制
局部SQLite写锁和同库合成可信授权不是跨系统一致性协议；控制仅覆盖明确接线的原生方法，无法证明HTTP/签名/真实用户身份/商户团队接入或跨服务撤销。原生付款验证中并非所有分支有amount/payee参数，原生金额绑定基线 NOT_OBSERVABLE；现有样机只能证明冻结的mock token付款分支观察到快照，不能宣称全凭据分支已达生产安全。无真实Provider/消费者/资金。