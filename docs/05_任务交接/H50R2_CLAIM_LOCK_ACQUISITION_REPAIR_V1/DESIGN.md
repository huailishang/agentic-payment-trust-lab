# H50R2 写锁竞争修复设计

## 实现范围
唯一修改本包 merchant/services/execution_control.py 中 claim() 的实际数据库写锁获取及异常归类；继承的 checkout_service.py、db.py、其他商家文件和旧任务全部只读。默认 sqlite3.connect(timeout=10) 的同步 BEGIN IMMEDIATE 在两个请求均通过空占用预读后仍可能阻塞事件循环约11秒。修复改用独立 SQLite 连接 timeout=0，立即争抢事务A写锁。锁忙时直接UcpError 409/H50_CLAIM_BUSY，不再裸OperationalError、不调用PSP、不修改确认或占用。读取checkout、确认、原子占用及提交仍在获取成功的同一SQLite事务内，钩子before_claim仍在锁外、before_claim_commit和after_claim_commit位置保持。

## 数据正确性
先持有SQLite写锁才能检查checkout状态、撤销/超时、全部快照并生成唯一支付引用；避免先查空的非原子竞态。事务提交前出错rollback；成功后才触发after_claim_commit与模拟付款。S01相同checkout和S02不同checkout在共享写锁竞争时都允许明确409，不允许同步长等待。旧15场景中的原生订单、幂等、两阶段事务、崩溃恢复、撤销与付款分支无需改动。

## 观测及边界
L1 S01/S02 均PASS，心跳约2ms，业务仍首笔正常完成、第二笔可分类拒绝；L1继承15/15通过。没有全域并发消除、生产性能、HTTP接口、Provider调用或真实用户身份证明。H50、H50R既有拒收历史不复写，需后续独立L3源码核查。