# H51 离线 HTTP 接线与证据边界

Task ID: H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b

地图 r82：目标为授权、绑定、受控执行、恢复与审计可信；A–D 完成，E 本地代表性闭环，F 当前。B-17 的最前未知点是 HTTP 路由如何连接已有控制。H50R2 方法锁修复已经接受并停止，支付宝与比赛延期，商业需求未知。本切片只测这一接缝。

## 原生入口与唯一覆盖

HTTP_RUNTIME.py 从任务内冻结 merchant/server.py 导入完整应用，使用原生 lifespan（应用启停生命周期）初始化和关闭数据库。httpx.ASGITransport（进程内应用传输）将请求直接交给该应用；不启动 uvicorn、不监听 TCP 端口。原生 generated_routes、routes/ucp_implementation、common_headers、verify_signature、请求模型、CheckoutService、ExecutionControl 和付款方法保持原样。

默认 dependencies.get_checkout_service 不传 execution_control。C07 不设依赖覆盖，实际 complete 返回 409/H50_EXECUTION_DENIED，付款账本和订单均为空。其他场景仅以 app.dependency_overrides[dependencies.get_checkout_service] 覆盖服务工厂，构造原生 CheckoutService 并传入既有 execution_control。工厂参数保留原生 get_products_db、get_transactions_db 和 get_fulfillment_service；数据库会话仍由原生依赖为每个请求创建和关闭。没有共享 CheckoutService 实例、全局锁或强制串行完成请求。

## 签名、确认与离线边界

require_signatures=true。每个场景生成只在内存存在的 EC P-256 私钥，通过原生 sign_request 签署实际正文。原生 fetch_signing_keys 从 respx（离线 HTTP 返回夹具）读取本地合成 profile（签名公钥资料）；DNS 仅返回固定合成地址，socket.connect/create_connection 拒绝应用外连，未知 HTTP 返回请求也被拒绝。日志中的 HTTPS profile 请求由离线夹具返回，并非真实网络。仅沿用 H47 对 Windows 标准库事件循环唤醒 socketpair 的例外，不开放业务 socket 或端口。观察保留请求头、正文、原始正文字符串、响应及公开 JWK（公钥表示）；不导出私钥。

确认由本地 fixture（夹具）在 HTTP 创建之后，使用真实返回的 checkout 完整快照调用既有 control.issue 签发。它是合成信任假设，不是用户身份认证或新的签发端点。C02 的数量更新走真实 PUT，付款仍携带旧确认；C03 无确认，C04 使用未签发引用。C05 不签署 complete，C06 在签署后改变正文，由原生验签路径拒绝。

## 付款、并发和继承边界

独立 PaymentPort 沿用冻结 FROZEN_TESTS 的 SQLite 假 PSP：每次 charge 调用都落库，不用幂等回执掩盖重复调用。付款快照与确认逐字结构比较；订单、库存、持久占用及幂等记录由独立 SQLite 连接读取，不从 HTTP 成功码推断付款。

C08 首笔 HTTP 请求停在已有 before_order_commit 钩子，真实付款已经发生、订单事务尚未提交。独立读者核对一次 charge/零可见订单，再发不同键的第二个 HTTP 请求；第二笔返回 409 后释放第一笔。钩子没有移动，事务、控制和业务代码没有修改。工厂记录并保留两个真实 AsyncSession 和底层数据库连接引用，避免 Python 对象释放后的 ID 重用；心跳与两个请求在同一事件循环运行。结束后核对一次付款、一单、库存 4。该调度只证明本固定竞争，不宣称全局竞态关闭。

原 2+15+4+2 方法回归由冻结脚本独立执行，不作为 HTTP 场景。冻结继承脚本保留其既有临时目录约定；新 HTTP 临时数据库只位于 .task_envs/H51/runs，并在关闭生命周期后清理。恢复仍仅继承方法级证据，不新增 HTTP 恢复端点。

## 交接与后续限制

每次 HTTP 调度前递增预算账本，失败调用同样计数；一次完整观察 19 请求，单次上限 40，执行者总上限 160。L3（评估者独立验证）将预算写到 evidence/evaluator_http_attempt_ledger.json，保持接受后的执行者账本不变；评估者上限 80。ARCHIVE_AND_RUN 在同名观察覆盖前按内容哈希归档。无新依赖、模型、外部 Provider（支付服务提供方）、客户联系或 Git 写操作。

LOCAL_HTTP_SLICE_OBSERVED 只表明人工依赖接线可测且固定拒绝路径成立；默认工厂仍未接线。实际部署、可信确认来源、真实主体、跨系统撤销、真实支付服务与客户需求全部未知。按冻结合同，本 HTTP 切片提交后停止，后续方向由评估者决定。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY；before=方法级证据、HTTP 接线未知；after=任务内 HTTP 证据可复核，未提升产品或生产身份成熟度；Test=VP-01..08；Evidence=http_l2.json 与 L2 原始流；残余=合成确认、跨系统撤销/真实服务/部署/需求未知。没有监管合规结论。
