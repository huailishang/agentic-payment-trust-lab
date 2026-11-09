# H49 S4 — 14 个未来可证伪验收设计



仅是设计，不是运行结果；14 个 executed=false，商家/Provider/ASGI 请求=0。



## 决策词表与计数口径

未来服务接口统一沿用现有 ALLOW/DENY/CONFIRM/WAIT/QUERY/RETRY 六种决策词表。HTTP 200/409/403/202 等仅为未来商家样机的待定映射示例，不声称现有 UCP Merchant/API 已实现本项目码。原报告的 ALLOW_RETURN_CACHED、RETRY_QUERY_ONLY、payment_execution_allowed 都只能作为 trace reason/诊断说明，不是新增核心 decision enum。CALL COUNT 统一标明场景总次数或重放/查询阶段增量。



## T01_NORMAL

准备：新建 checkout v1，用户独立签发仍有效的 confirmation(v1, amount/currency/payee)，库存足够且 PSP fake 只计调用。

步骤：1. 用独立确认提供者签名固定 v1 的所有商品、金额、币种、payee，并存储版本。；2. 服务端 complete 在原子读写区对比当前 v1、授权版本与时效，创建唯一 attempt 后调用 fake PSP 一次。；3. 核查 checkout=COMPLETED、order 内容与确认一致及单笔付款调用。

预期决策：ALLOW（现有决策词，未来商家正常完成）；payment_execution_allowed 只可作为 trace reason，拟定 HTTP 200，不增加核心枚举。

支付调用计数（详见判卷窗口）：1

持久状态：COMPLETED，唯一 order 与 attempt=CONFIRMED，checkout v1 与 frozen snapshot 完全相同。

独立判卷：未来商家样机必须把事务 A 提交的 checkout v1 frozen_snapshot_digest、商品金额及 payee、稳定 payment_request_ref 传给可独立观察的 fake PSP seam；核对 fake PSP 全场景付款调用=1、真实接收的金额/payee/ref 与确认一致、DB order/attempt 唯一。原 _process_payment(payment) 没有这些形参，若未改变观察合同本项不通过。

必需轨迹：confirmation provenance、checkout digest/revision、attempt id、PSP id、commit 与结果。

残余限制：无法证明真实 PSP 结算或生产签名，仅本地模拟正常准入。

已执行：false



## T02_CHANGED_BEFORE

准备：确认在 checkout v1，complete 前合法 update 将商品数量和总额更新为 v2。

步骤：1. 签发并保存 v1 确认，然后调用商家原生 update_checkout 写 v2。；2. 用 v1 confirmation 直接调用服务端 complete，不依赖客户端 wrapper。；3. 独立核查没有发起新付款，v2 保留且要求重新确认。

预期决策：DENY / confirmation_snapshot_mismatch

支付调用计数（详见判卷窗口）：0

持久状态：checkout v2 未完成，无新 order/attempt 扣款结果。

独立判卷：数据库当前 revision 与独立确认 digest 不一致，fake PSP 调用计数 0。

必需轨迹：v1/v2 内容差异、旧签名/版本、服务端拒绝原因、无 PSP 调用。

残余限制：条件写覆盖遗漏或不同价格口径可能造成误判。

已执行：false



## T03_UPDATE_DURING_EXECUTION

准备：两个真正独立的 DB session A/B 与 checkout v1；在 A 读取与确认核对后、事务 A 的 EXECUTION_CLAIM/CAS 前设屏障，B 争抢 update v2；另测 A claim 已提交之后 B 才到达的相反先后，使用真实交错而非串行回放。

步骤：1. A 读取 checkout v1 验证授权，在事务 A 的 checkout revision/CAS 前暂停，记录 frozen digest 和 session id。；2. B 从另一个 DB 连接对同一 checkout 更新 v2：B 若先提交，A 的 claim 必须失败；若 A 先 claim COMMIT，B 必须被拒绝或阻塞至旧支付完成且不得改付款快照。；3. 恢复 A 并观察两个线性化分支：分支1 B赢→A DENY、付款0、checkout v2；分支2 A赢→A ALLOW、付款1且仅为 v1、B 不得在支付前改成 v2。

预期决策：分支 B先 DENY(stale_checkout_revision)；分支 A先 ALLOW(v1)，B 只可 WAIT/DENY。括号为未来 trace reason，均复用既有决策词。

支付调用计数（详见判卷窗口）：UNKNOWN

持久状态：按原子 claim 排序判卷：B先则 checkout v2、0笔支付/0新 order；A先则持久 IN_FLIGHT v1→COMPLETED v1、1笔支付/1新 order，B不能在结算前覆盖同笔冻结快照。

独立判卷：以独立 DB 两个 session 的事务 A claim/CAS 与 update commit 顺序为分支选择信号，分支 B先=0 PSP调用且无 order；分支 A先=1 PSP调用且金额/payee/quantity 必须匹配冻结 v1，任何第二次调用或用 v1 确认结算 v2 均失败。fake PSP 必须能独立观察 request_ref、冻结金额与收款主体；当前 _process_payment(payment) 不具备，未满足时不能宣称通过。

必需轨迹：两个 DB session transaction ID、屏障、claim 与 update 的 commit 先后、每阶段 checkout revision/hash、外部 fake PSP 实际入参(amount/payee/payment_request_ref)、总调用计数、拒绝理由。

残余限制：事务隔离级别、死锁与多实例数据库实现仍需另外验证。

已执行：false



## T04_MISSING_CONFIRMATION

准备：checkout v1 存在但没有可信确认或 confirmation_ref。

步骤：1. 准备有价目和库存的正常 checkout，但不注入可信确认记录。；2. 绕过客户端直接 POST complete，断言服务端不给任何新 PSP 调用。

预期决策：DENY / missing_confirmation

支付调用计数（详见判卷窗口）：0

持久状态：checkout 仍可编辑，无订单、无付款 attempt。

独立判卷：可信确认存储独立查询缺失并核对 fake PSP=0。

必需轨迹：缺证据字段清单、拒绝来源及无付款轨迹。

残余限制：默认拒绝可能影响未升级客户端兼容性，需明确迁移。

已执行：false



## T05_FORGED_CONFIRMATION

准备：checkout v1 存在，构造伪造签名、错误主体或未受信任 keyid 的确认。

步骤：1. 用不受信任私钥或被修改的签名生成同 checkout 外形的 confirmation。；2. 直调商家 complete，在任何支付前校验密钥来源、签名、主体及绑定。

预期决策：DENY / confirmation_signature_invalid

支付调用计数（详见判卷窗口）：0

持久状态：checkout 不变，无订单、无 PSP attempt。

独立判卷：独立签名验算与受信任公钥集合检查，不依赖被测实现的 pass 标志。

必需轨迹：签名 keyid、验签来源、拒绝码、attempt/PSP 计数。

残余限制：生产密钥轮换、吊销与根信任链尚未验证。

已执行：false



## T06_REVOKED

准备：独立可信授权存储持有单调 authority_version，先签发 confirmation v1，随后可线性化撤销到 v2；相同 checkout 初始未被 execution claim 占用。

步骤：1. 撤销事务写入权威记录 authority_version=v2，确保撤销在服务端事务 A 申请执行占用之前完成。；2. 新 idempotency_key 调用 complete，必须通过与撤销线性化的 claim-and-revoke 协议核对版本；授权源不可达或无法建立一致先后时 fail closed。；3. 核对 DENY、无 PREPARED attempt/无 fake PSP 调用；另注明 claim 在先撤销在后走 QUERY/WAIT 不是自动撤销已发支付。

预期决策：DENY（撤销在 claim 之前）；授权服务断联、版本不可核验亦 DENY；claim 在先撤销在后为 WAIT/QUERY 恢复，不以新决策词覆盖。

支付调用计数（详见判卷窗口）：0

持久状态：撤销在先时 checkout 未完成，无新付款 attempt；如授权源不可用则 fail closed 并记录信任来源不可用，不得继续建 IN_FLIGHT。

独立判卷：由独立授权日志的 revoke commit_seq < merchant claim 请求序号判定撤销在先，必须 DENY 且 fake PSP=0；若协议无法形成跨系统可核先后，样机不能判 PASS，标 SERVICE_CONTRACT_CHANGE_REQUIRED。

必需轨迹：独立授权 revoke/claim 序号、单调 authority_version、事务 A CAS 结果、拒绝码、断联故障标记、fake PSP 计数。

残余限制：实际跨系统可线性化的撤销协议当前不存在；若无法提供即不能证明 race_closed，必须保留服务合同变更前置。

已执行：false



## T07_EXPIRED

准备：有真确认但 expires_at 严格早于注入的固定服务端时间。

步骤：1. 使用可控单调测试时钟签发有效期已结束的可信记录。；2. 服务端立即完成检查并拒绝在付款前执行。

预期决策：DENY / confirmation_expired

支付调用计数（详见判卷窗口）：0

持久状态：checkout 维持可确认状态，没有新付款事实。

独立判卷：独立时钟快照与有效期数值比较，fake PSP=0。

必需轨迹：时间源、有效期、decision reason、PSP counter。

残余限制：多机时钟偏移与时区解释需要单独规范。

已执行：false



## T08_SAME_KEY_REPEAT

准备：checkout v1 已有同 idempotency_key/相同 canonical body 的持久成功 attempt。

步骤：1. 先按 T01 完成一次并持久化商家/PSP 关联结果。；2. 重复提交同 key/同正文；从持久幂等缓存读既有结果，不再调用 PSP。

预期决策：ALLOW（返回历史成功结果，trace reason=cached_original_result；可为 HTTP 200）而非新增 ALLOW_RETURN_CACHED 核心决策；不发起新付款。

支付调用计数（详见判卷窗口）：0

持久状态：原 completed 与单一 order/attempt 保持不变；本次新支付计数0。

独立判卷：以重复请求阶段为观察窗口：新 PSP 调用增量=0；包含最初 T01 的全场景累计调用仍为1，attempt/order id 均不变，原交易成功记录可查询。

必需轨迹：请求规范化 hash、缓存命中和旧 receipt/revision。 重放窗口起止标记、原成功调用与新增调用计数必须区分。

残余限制：缓存持久期限及真实 PSP 幂等保留窗口仍未知。

已执行：false



## T09_SAME_KEY_DIFFERENT_BODY

准备：checkout 已缓存一次 attempt，同 idempotency_key 但商品/金额/支付凭据正文变化。

步骤：1. 持久化历史 key 和 canonical body hash。；2. 同 key 使用改过正文请求 complete，服务端在新付款前比较 hash。

预期决策：DENY / idempotency_conflict_409

支付调用计数（详见判卷窗口）：0

持久状态：历史已完成 order 保留，不新增执行记录或新款项。

独立判卷：独立 hash 比较与 fake PSP 新调用计数0。 计数指冲突重放阶段增量0；包含原成功场景累计1，不改变旧订单。

必需轨迹：key、两个 hash、冲突来源与旧记录索引。

残余限制：跨语种字段/浮点金额规范化规则需统一。

已执行：false



## T10_NEW_KEY_AFTER_COMPLETE

准备：checkout 已成功 complete，持久状态 COMPLETED，新 key 即新的意图。

步骤：1. 使用 T01 的完整结果快照、设置新的请求幂等键。；2. 直调原生商家 complete 并核对终态拒绝而不是创建第二笔。

预期决策：DENY / checkout_not_modifiable

支付调用计数（详见判卷窗口）：0

持久状态：checkout 保持 COMPLETED，只有第一条 order/attempt。

独立判卷：独立订单计数/PSP 计数保持1，确认旧意图不可复用为新付款。 此0是第二个新 key 尝试阶段的增量，包含原成功尝试的全场景累计仍为1。

必需轨迹：checkout status、new key、拒绝及历史 attempt。

残余限制：跨商家重复下单的全局幂等不属于本样机。

已执行：false



## T11_UNKNOWN_THEN_QUERY

准备：事务 A 已在独立 DB commit 中保存 unique attempt=IN_FLIGHT、frozen snapshot 与稳定 payment_request_ref；fake PSP 按此引用接受一笔付款，但调用方响应丢失。

步骤：1. 执行事务 A COMMIT 并以稳定 payment_request_ref 调用 fake PSP，PSP ledger 记录本场景首次付款恰好1次；丢弃响应、进程可能在记录 UNKNOWN 之前崩溃。；2. 恢复器从已提交的 IN_FLIGHT/ref 查 fake PSP，查询接口不增加任何新支付调用；防止换新 key 重收。；3. 确定单笔成功则补齐原订单/状态，结果仍不明则保持 QUERY/WAIT 与人工对账，不假造付款结果。

预期决策：QUERY/WAIT（在途恢复）；查实已完成时可 ALLOW 返回旧事实，不等于新付款授权。

支付调用计数（详见判卷窗口）：1

持久状态：事务 A IN_FLIGHT/ref 已持久；其后从 QUERY 结果补齐单一 order 或保留恢复待办；不得因响应丢失再次发款。

独立判卷：本场景原付款阶段 fake PSP 总计1次，恢复查询阶段新增支付=0；独立 fake PSP ledger 可按付款前持久化 request_ref 返回事实，DB 即使尚无 UNKNOWN 字样也必须有可恢复的 IN_FLIGHT/ref。

必需轨迹：事务 A commit 成功、稳定 payment_request_ref、PSP 原始调用计数1、响应遗失点、重启后查询计数与新增支付0、补齐或人工待办。

残余限制：真实 Provider 状态一致性/查询终局性不能从 fake 推断。

已执行：false



## T12_CONCURRENT_COMPLETE

准备：两个独立 session/process A/B 同 checkout v1；屏障让双方读取同一初态再竞争执行 CAS/行锁。

步骤：1. A/B 在两个真实独立数据库连接并行提交同一 checkout，设置确定性启动屏障。；2. 分别以各自 idempotency key 抢占执行唯一 attempt，注入调度交错。；3. 断言最多一笔 fake PSP 付款，另一方 DENY/WAIT/QUERY，核对持久订单唯一。

预期决策：ALLOW one / WAIT or DENY other

支付调用计数（详见判卷窗口）：1

持久状态：一个 completed checkout，一个 order，一个 authoritative attempt；另一请求无第二次付款。

独立判卷：独立 fake PSP 总计=1，数据库唯一约束/事务事件证明非串行调用。 1 次是两个会话全场景总付款数，而不是每会话各 1；另一会话增量0。fake PSP 的唯一引用需与数据库 winner attempt 对应。

必需轨迹：会话 ID、竞争屏障、CAS 胜负、锁、attempt ids 与提交顺序。

残余限制：SQLite 局限及生产多实例/分布式网络依旧未证明。

已执行：false



## T13_PAYMENT_BEFORE_COMMIT_FAILURE

准备：商家新增事务 A 在 PSP 调用前独立 COMMIT，保存 checkout frozen_snapshot、唯一 IN_FLIGHT attempt 和预生成稳定 payment_request_ref；模拟 PSP 依此引用成功1笔，再在事务 B（库存/订单/checkout 完成提交）注入故障。

步骤：1. 确保事务 A 已 COMMIT 后，以相同稳定引用调用 fake PSP 1次；观察真实 fake PSP 入参中的金额/payee/币种/快照哈希，而非从原 _process_payment(payment) 虚构。；2. 在单独的事务 B commit 处强制失败并回滚库存/订单变更，模拟 crash 可发生于尚未来得及持久写 UNKNOWN 前。；3. 恢复器从未回滚的事务 A 读 IN_FLIGHT/payment_request_ref，用 fake PSP 查询付款事实，保持阻断新付款；核对人工补救或可幂等补记完成状态。

预期决策：QUERY/WAIT（支付结果与订单状态待核对，不能以 RETRY_QUERY_ONLY 创造新核心决策，也不得新发付款）。

支付调用计数（详见判卷窗口）：1

持久状态：事务 B 回滚后 order 可能不存在，但事务 A 的 frozen attempt=IN_FLIGHT 与 payment_request_ref 必须仍存在；恢复时标记 UNKNOWN/RECONCILIATION_REQUIRED 是补写动作，不要求 crash 前已经落盘 UNKNOWN。

独立判卷：两个分离事务的 DB 审计证明 A COMMIT、B ROLLBACK；fake PSP ledger 付款总次数=1、恢复 QUERY 新付款增量=0；按事务 A 预生成稳定引用找回 PSP 成功事实。不满足时 fail，不能将数据库 rollback 解释为已退款。

必需轨迹：DB 事务 A commit 与 B rollback 事实、付款前 durable request_ref、fake PSP 实际收取 amount/payee/ref、ledger total1、crash/restart/QUERY 轨迹、是否退款/补记及其来源。

残余限制：固定源码付款方法没有 amount/snapshot/ref 或真实 Provider 查询能力；未来必须改商家与 fake PSP 可观察接口，否则此场景没有独立判卷条件，不能冻结为已可实施安全控制。

已执行：false



## T14_DIRECT_ENTRY

准备：可信确认 v1 后服务端 checkout 被直接合法更新 v2；客户端 wrapper 完全不参与。

步骤：1. 准备有效旧确认，直接使用服务端 update_checkout 将数量改为 v2。；2. 直接调用 routes/ucp_implementation.complete_checkout，不经过 H48 客户端确认函数。；3. 读取商家服务端拒绝并确认 fake PSP 未扣款。

预期决策：DENY / service_snapshot_mismatch

支付调用计数（详见判卷窗口）：0

持久状态：checkout v2 保留未完成；无新 PSP 及最终订单。

独立判卷：调用轨迹证明未执行客户端 wrapper；独立 fake PSP=0 与 DB revision mismatch。 从实际商家入口观察付款时 frozen snapshot/ref，不依赖 H48 客户端的决策输出；如果未来适配器未暴露金额绑定不能判定安全通过。

必需轨迹：原生 REST 路由、签名请求、确认 v1、checkout v2、拒绝与计数。

残余限制：只测固定服务端入口，不代表全部外部商户实现均防旁路。

已执行：false



## 重要门禁

T03 明确 A/B 的 CAS 与更新先后两个分支：B先=0次付款，A先=1次 v1 付款；UNKNOWN 字段只表示总数依分支而定，绝不能当不可判卷。T08 的0是重复请求阶段增量，原成功1次仍存在；T11/T13 的1是全场景中首次付款的总数，后续 QUERY 的新增支付都为0。

现有 `_process_payment(payment)` 无 checkout 金额/收款人/快照参数，未来样机必须先实现能独立验证冻结执行快照与实际模拟付款输入相同的可观察接缝；未满足就不能以门禁检查通过冒充付款绑定。
