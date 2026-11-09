# H50R2 执行入口

Task ID: H50R2_CLAIM_LOCK_ACQUISITION_REPAIR_V1
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
State: CONTRACT_FROZEN / Executor / repair / SINGLE

先读CURRENT、地图r81、CONTRACT、父H50R最终REVIEW、VALIDATION_PLAN与INHERITED_COPY。项目A–D完成、E本地闭环、F当前，B-17只剩本次可修的写锁获取残余；不能把H50R的6/6当最终验收。

继承36实现文件，Evaluator没有实现修复。原4修复有实证通过；两个请求先查空再争写锁仍裸异常并卡事件循环，新两例在继承实现的准备运行中失败。只改本目录merchant/services/execution_control.py；checkout_service.py与其他34实现冻结。优先在真正写锁获取点处理忙时语义/调度，不再以预检替代原子边界，不改钩子位置或断言。

串行完成：检查继承/原始失败 → 实现最小机制 → L1包括两新调度及原修复 → 解释事务/撤销/付款恢复不退化 → REPORT/DESIGN/RESULT/预算 → 冻结计划完整L2七项 → 一次交Evaluator。直接使用冻结公共runner，不修改计划；正式命令不带--diagnostic。

预算90主动分钟/2次正式L2，旧H50的2/2与H50R的1/2保留。零代理、零外部调用/真实付款/安装/Git。只有合同内低成本修复；超范围或无新依据立即停回Evaluator，不自动追加第三包。最终通过还需独立L3与源码审阅，不能扩成生产/HTTP/客户成绩。
