# H49 S2 — 三机制工程比较



已接受基线：H48 CLIENT_GUARD_ONLY；L01/L02 直接/穿插更新都可完成两件。此表是源码推导而不是实测提升。



## CLIENT_RECHECK — REJECT

现有：H48 客户端纯投影与 P1 确认记录可以在 wrapper 自身入口比较快照，挡住核验前的变更、缺字段与过期。

可覆盖：H48 G02–G06 检查前变更/缺证据/过期会拒绝，G01 正常可放行。

不能覆盖：L01 核验后更新穿插以及 L02 绕过客户端直接 complete；两者仍可完成修改后的两件，无法约束多实例和后台入口。

可信输入：客户端模拟确认和当前 merchant checkout 快照；真实用户权限、payee 来源未核实。

需商家控制：没有商家控制权便不能覆盖直接调用服务端；客户端先查后调不能提供原子保证。

改动点：只修改 H48 wrapper，不能作为消除 B-17 的主变更。

成本：局部开发成本低但每新增客户端入口都可能遗漏检查，维护成本随消费者增长。

最强反对：非安全演示场景这是最便宜选项；但已观察 L01/L02 绕过，无法解决当前首要瓶颈。


## MERCHANT_ATOMIC_GUARD — ABSORB

现有：原生同键同正文缓存、不同正文冲突、完成后新键拒绝及库存条件减量已有源码证据。

可覆盖：如果商家掌握真实确认和所有 checkout 写事务，执行前版本/CAS 加信任事实可设计性地阻断 L01/L02。

不能覆盖：当前无持久 checkout_revision、CAS、确认验签、真实 payee、PSP 付款结果；单进程 mutex 无法覆盖多实例；DB commit 不会回滚外部付款。

可信输入：由独立用户认证确认服务提供的授权、签名/撤销版本，以及 checkout/items/total/currency/merchant/payee 有来源的完整快照。

需商家控制：须修改 CheckoutService.complete_checkout、update_checkout、cancel_checkout 与共享数据库条件事务，落 durable attempt/outbox；直写数据库权限另审计。

改动点：服务端 complete idempotency miss 后、_process_payment 前，以及所有同一 checkout 修改入口。

成本：需要数据库 schema 变更与两会话竞态测试、故障注入、恢复与审计，维护/运维成本中高。

最强反对：当前可信确认和 Provider receipt 缺失，商家可能无法授权改全部写路径；无这些前置条件，样机只能模拟不能验证生产安全。


## EXTERNAL_AUTHORITY_GATE — REFERENCE_ONLY

现有：ServiceNow AI Passport 官方公告宣称运行时授权、签名权限凭据、委托收窄/撤销及审计，预计 2026 Q4 可用。

可覆盖：有可能提供可核实用户/agent 权限、版本和撤销事实，减少自建通用身份治理成本。

不能覆盖：没有证明它在固定 UCP merchant 内做 checkout/amount/payee CAS，或解决数据库提交与外部支付不原子的恢复；未取得 SDK、凭据、测试。

可信输入：官方可校验签名/授权服务、授权版本和与 checkout 关联的标准化凭据；现均未准备。

需商家控制：仍需商家端落可靠执行点并协调 update/cancel/complete，外部 authorize API 不能替代数据库条件写。

改动点：未来可替换信任事实来源，不替换支付执行事务；当前不调用、不安装。

成本：费用/延迟/可用性/锁定成本未知，服务端协调和恢复成本仍在。

最强反对：平台可能成熟且便宜；没有证据表明本项目另造通用认证或审计有优越性，故优先参考并保留实测条件。


## 收敛机制及竞争事实

下一样机仅选择 MERCHANT_ATOMIC_GUARD 为主变量：服务端要阻断直接付款，仍需商家自己控制读写快照的原子性。外部权限服务若有真实合约可作为可信授权来源，但无法仅凭远端权限判定确保本地 checkout 不被随后修改。

2026-10-15 ServiceNow 官方公告是产品发布（EXTERNAL_BASELINE.json），不是可执行 API/真实支付绑定测试，分类 REFERENCE_ONLY；可用性预计 Q4 2026。未来若其提供同场景可靠能力且总成本更低，应复用/停止重复产品。

本包不修改源码、安装 SDK、建立新平台、测试商家或者对外联系。