# H72 执行者唯一交接入口

先读根CURRENT.md。目标为一个合并包连续完成：本地验证收尾→外部资格→正常/取消/付款未知恢复/交付恢复→对账→最终完整L2；Evaluator末尾统一一次独立L3。

## 当前启动条件

当前是CONTRACT_FROZEN / Executor，Human已授权H72及主线内自主调整，权限/起止时间已登记AUTHORIZATION.json。读取冻结输入后可直接开始，不再询问相同范围许可。按AUTONOMY自主选择等价现有工具/线路、调整互不依赖的步骤、修补普通脚本问题和进行暂态网络重试；所有调整/失败照常留证。只在真正改变主线/AC/范围/预算/权限或触发安全停止线时交Evaluator。

## 阅读顺序与历史

1. CONTRACT.md（步骤依赖、12条AC、范围、停止线）。
2. SPEC.json、AUTHORIZATION.json/md、AUTONOMY.md（累计额度、分角色额度、精确许可及自主空间）。
3. BASELINE.json、SUPERSESSION.json和references（原件保护和已有未提交工作）。
4. SOURCE_LOCK.json、VALIDATION_PLAN.yaml。

H71R3由本包承接且原件只读；不要在旧H71R3/H71R2里执行、写报告或覆写Gate。不要把旧完整性命令绑定旧路由的失败当产品回归，也不能忽略保护检查；本包CHECK必须按新BASELINE重新保护历史和当前范围。

## 授权冻结后的执行顺序

- 事前校验HEAD、冻结文件/授权有效期，记录工作区、实现版本和BEGIN。
- P0只用原生Windows Conda agent，在本包runtime建立进程级用户包入口；原安全9项、回归74项、取证11项、生命周期9项须实际通过。用公共capture_evidence保存命令三件套，生成绑定环境/代码摘要及原始证据路径的P0_RECEIPT。
- P0通过且新权限有效后，按CONTRACT逐阶段自动继续。先建立通知/浏览器资格，N01第一会话同时承担必要写入/托管页资格测量；不浪费额外资格会话。资格失败诚实停止。
- 默认N01→C01→R01→D01；N01成立后，可按无依赖步骤/服务状态调整后三例顺序，保持各例身份、真实注入点和R01重启要求。普通脚本修补不按每次编辑另算一个主要方案，在剩余时间/范围内自主修补继续，不逐步骤发起人工复核。
- 网络暂态同一只读/下载单元最多4次总尝试，按2/5/10秒退避并遵守Retry-After；固定下载最多4次传输/12 HTTP/64MiB，成功足够即停。付款/创建结果未知先查原对象，禁止盲目重付/重建。不得占用Evaluator独立20次额度或重置累计成本。
- 原始秘密/HTTP/通知保存在仓库外任务私有目录，只用去敏引用和摘要入仓；不把结账URL或key打印到日志。
- 整包末尾才运行公共L2，提交一份REPORT、RESULT、阶段证据索引、闭合账本和完整EV；不替自己写PASS。L2失败可在总2次内同包修复，所有失败证据保留。

## 机器命令边界

目标解释器固定为CONTRACT所列Windows agent Python。设置进程级PATH/PYTHONUSERBASE/PYTHONDONTWRITEBYTECODE，不改变系统变量。严禁WSL替代或为导入冲突卸载/升级共享依赖。

Executor需在本包实现以下入口，不能改公共工具：

```text
python <H72>/CHECK.py environment
python <H72>/CHECK.py preservation
python <H72>/RUN.py --phase local-closeout
python <H72>/RUN.py --phase external-journeys
python <H72>/CHECK.py submission
```

`<H72>`代表`docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1`。RUN不自动触发正式L2/L3，也不把诊断当正式Gate；每次运行须读取持久账本/已完成阶段，只恢复必要未完成步骤，禁止重跑已完成付款。

PREPARE.py仅保留历史草案制包逻辑，不是当前运行前置；FREEZE.py verify用于Evaluator冻结时的无执行快照核验。Executor实现的CHECK应核当前BASELINE及正常任务流转，不能机械要求旧DRAFT/旧未授权状态或“尚无实现文件”。

正式L2使用目标解释器执行：

```text
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H72_LOCAL_CLOSEOUT_AND_STRIPE_JOURNEY_V1/evidence/l2_attempt_001 --mode executor
```

第二次如有必要使用全新l2_attempt_002；原目录不覆盖。L2通过后关闭Executor账本，CHECK submission及公共validate_workflow均0，REPORT标SUBMITTED_FOR_REVIEW，CURRENT保持EXECUTING / Executor。Evaluator接受快照后再改READY_FOR_REVIEW并用相同计划mode=evaluator落盘独立新目录。

## 最后一次性提交

REPORT须包含：初末工作区/实际diff和摘要、P0全部原始证据、版本/下载及资格证据、每旅程授权到交付逐引用链、所有失败和停止原因、外部清点、前后0/4→实际结果、累计及角色预算、合法L2-GATE和每份EV。独立20次只读额度不得由Executor消费。没有Report/L2不得让Evaluator先跑正式L3。

COMPLETE才报告四旅程完成；QUALIFICATION_LIMIT的未执行案例全部标缺测，收益不成立。制包、工具可用、通知模拟或本地测试成功均不等于实际外部支付链已验证。
