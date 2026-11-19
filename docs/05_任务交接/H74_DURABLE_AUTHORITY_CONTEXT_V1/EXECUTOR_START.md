# H74 Executor start

目标与全局：原授权→副作用前治理→恢复审计；A–D本地关闭/E受控本地闭合/F受控Stripe切片关闭。H73 PASS只确认三个有界审计断点，当前H74建设一个本地durable stored路径，不升级真实身份/生产/采用。

1. 读取CURRENT/r125/CONTRACT/SPEC/BASELINE/FREEZE。用既有Conda agent Python3.12.13；环境PYTHONUSERBASE=<本包>/runtime/userbase、PYTHONPATH=<repo>/src、PYTHONDONTWRITEBYTECODE=1，PATH首位为该解释器目录。tests隔离仅当前进程，不改共享site-packages/.pth。
2. 新建ATTEMPT_LEDGER.json开始Executor工作窗，记录初始git status。运行CHECK preservation/baseline及原回归确认前置；初始失败停止，不擅自修旧模块。
3. 按一包完成持久保存/显式codec、load原对象、两个stored消费者及三个命名测试类。数据库只在本任务临时目录；用FakeStripe和计数回调，禁止实例化StripeTestAPI或发HTTP。
4. SAME baseline以锁定原src重建；MEASURE.py只记录固定SPEC三单元，输出MEASUREMENT.json。每单位要有raw证据、原/恢复图摘要、snapshot引用和冷进程/消费者/副作用计数。0/3不支持不能写成旧安全失败；结果不限于漂亮总数。
5. 完成所有拒绝与C01/R01/D01守护，跑八VP公共L2 --mode executor --out evidence/l2_attempt_001；最多第二次l2_attempt_002，失败原件不覆盖。同方法修复预算内自动继续，无需逐步交Human。
6. L2通过后关闭整窗账本，报告原/最终status、diff/源码摘要、每AC证据及影响事实；SUBMISSION.json files覆盖实现/测试/MEASUREMENT/REPORT/账本/所有raw和derived，另记最终L2 gate摘要。不包含自身/CURRENT/未来Evaluator输出。
7. CURRENT切READY_FOR_REVIEW/Evaluator，next_artifact=本包REVIEW.md。不自跑L3。Evaluator使用独立证据与冷进程/损坏对照，唯一L3和逐AC验收。

账本schema=h74-cost/v1，windows=[{role:Executor,begin_utc,end_utc:null或UTC}]，implementation_attempts整数≤2，l2_attempts≤2，l3_attempts=0，external_actions按SPEC全0。每次动作前核剩余；整段墙钟计费，至少留10分钟收尾。Evaluator另写evidence/l3_review/COST.json，不能改Executor接受字节。合并105/45/150分钟及4h/2h墙钟边界，不继承旧预算。

停止条件按合同：零容忍反例/范围外输入或实现/权限/新依赖/预算尽头立即停止；不新增真实付款、网络、浏览器、服务、钱包、提交或推送。
