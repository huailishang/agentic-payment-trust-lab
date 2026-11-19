# H71R3 显式合同修订01（2026-11-14）

Role: Evaluator
Task ID: H71R3_CONDA_AGENT_TEST_IMPORT_ISOLATION_V1
State: CONTRACT_FROZEN / Executor
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Project map: 2026-11-14-r118 / B-21 / H-71R3

本次为冻结合同的可执行性修订，不是Executor提交验收。原合同/计划/路由/地图原字节见`references/before_amendment_01/`及`evidence/reassessment_20261114/ORIGINAL_SNAPSHOT.json`；旧H71R2拒收不追认。H71R3无REPORT、无L2、未执行正式L3，不作PASS/REJECTED的执行成绩裁决。

## 为什么必须修订

1. 旧`CHECK.py integrity`从BASE_CHECK读取旧BASELINE并要求路由含H71R2、只准旧包新增文件；当前路由和新增范围为H71R3。DA-01独立核1701保护输入，唯一漂移是已切换的REMOTE_HANDOFF；13冻结输入全部保持。DA-03原完整性命令退出1，随后仍存在旧路由及新增范围冲突。不能把正常治理切换伪装成产品回归，也不能恢复旧路由骗过检查。
2. H68R原`regressions()`构建`env=dict(os.environ, PYTHONPATH=str(ROOT/'src'))`。外层PYTHONPATH隔离不能传给真实测试进程。DA-02用相同重设方式实测：只对进程树设置任务局部PYTHONUSERBASE，Windows用户包入口仍能将原测试模块定位到本仓；测试断言和正式门禁执行数均为0。
3. 原VP-08只检查H71R2账本，其限额是2实现/3L2/120主动分钟/180墙钟，不能核H71R3的1实现/2L2/60/90。原VP-09零副作用自声明也不替代本包范围和预算审计。

## 唯一修订包

- 原六项产物/探针/安全/回归/历史预算命令保持；把旧完整性命令替换为当前任务CHECK preservation，逐字节保护历史、当前源码和冻结输入，并对新增范围/权限重新检查。旧检查文件及旧失败证据一字不改。
- 隔离承载从仅外层PYTHONPATH改为任务局部PYTHONUSERBASE，禁止启动钩子/.pth/猴子补丁；原安全9项、原回归74项入口及断言不变。
- 增加本包预算命令；计划由9项变为10项。当前范围/预算检查须有局部复制fixture拒绝自测，原文件不被变异。
- 仍限1版实现、2次正式L2、1次独立L3；此前正式消耗均0。原预算不是自动续期；首次Executor BEGIN后按合同累计，外部/安装/提交推送权限全false。

本轮只冻结可执行的接续设计；Executor随后自行完成合同内实现及L2，再交Evaluator统一L3。不是把设计探针当作支付能力增益。NOT_APPLICABLE（不评价产品能力增量）；CONTINUE（继续此有界修复）。通过即STOP（停止同类本地扩例），回到外部授权/资格决策。
