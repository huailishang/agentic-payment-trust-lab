# H50R 修复设计

继承H50原生36文件副本，只有 checkout_service.py 与 execution_control.py 被本轮修改。新增和既有业务流程保持不变，原生创建、库存、订单、幂等及恢复查询继续沿用之前实现。

## 交易竞争修复

complete_checkout 先读取原有幂等结果，保证已成功的同键历史重放可以直接返回；对新增请求，在进入数据库写入/claim前只读检查已有持久占用，存在则发出既有 before_claim 观察事件后立即返回UcpError 409，避免沿着事务B已持有的写锁执行同步 SQLite BEGIN IMMEDIATE。撤销采用SQLite timeout=0的立即锁尝试：空闲时原子更新可信确认，锁争用时明确409 H50_REVOCATION_BUSY（未实施撤销），避免默认10秒同步阻塞事件循环。正常claim和事务A/B及固定子进程故障仍保持原样；没有使用进程全局锁。

## 成功付款路由修复

_process_payment保留原生credential/handler判断，原本mock success_token进入独立模拟付款的路径不变。将google_pay、shop_pay已被原生接受的token成功分支也接到相同 payment_port.charge(payment_ref,snapshot)，并覆盖原生card提前成功返回路径（对象及dict）。失败/未知处理器路径仍拒绝，不生成模拟付款。冻结快照与稳定引用来自此前数据库事务A，不信任客户端提供amount或payee。

## 可测性与限制

H50原始证据不修改、不重写历史L2预算。首次本包局部探针展示R01未到达第二次before_claim、旧回归显示历史重放/先claim后撤销的回归问题；修复后四新增与十五继承局部场景均PASS。独立账本记录charge每一次调用、不是Provider或真实资金。只证明同库SQLite、合成可信引用和方法级入口；不证明HTTP签名、外部身份、跨系统撤销及所有支付通道安全。