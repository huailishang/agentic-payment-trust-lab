# H74R Executor start

全局：B-22未关闭；H74八项L3结构通过但原事实幂等/类型保真及成本完整性未过，最终REJECTED。当前仅修复已知断点，原身份/签名/生产边界不升级。

1. 读CURRENT/r126/CONTRACT/BASELINE/FREEZE及父REVIEW。使用既有Conda agent3.12.13、PYTHONDONTWRITEBYTECODE=1、任务局部PYTHONUSERBASE和ROOT/src、解释器目录置PATH首位。开启新schema=h74r-cost/v1账本，不重置父计数。
2. 只修ledger同原ctx不同有效记账时刻重试、codec真实Enum白名单两处。保留首次payload和时间；未知同名Enum拒绝，合法图可冷载入。不得改HOLDOUT或原测试方法体，仅追加测试。
3. 新增COST_RECONCILIATION.json：parent_ledger_sha256、parent_submission_sha256、parent_review_sha256绑定BASELINE；original_executor_minutes=20.825250133333334、conservative_executor_minutes=25.0192、added_closeout_minutes=4.193949866666666、boundary_utc=2026-11-16T06:24:00+00:00、actual_active_minutes=UNKNOWN、reason说明未证明超预算且旧记录不改。
4. 冻结HOLDOUT是原独立9组+两个同名枚举直接codec对照。先确认已知红基线（可留L1记录），修复后必须全过；原13测试与新增测试、原19/9/74一起验证。
5. 唯一公共L2 --mode executor --out evidence/l2_attempt_001。全部raw保留；失败后不追加第二正式尝试，保留BLOCKED交Evaluator。
6. 完成REPORT/最终源码与diff/账本/全部raw的SUBMISSION，再结束工作窗，计入最终提交序列化上界；不能先关账再继续写报告。提交先有原始meta/摘要，允许最后封存SUBMISSION使用明确短收尾上界并等到该时刻，需披露。
7. CURRENT切READY_FOR_REVIEW/Evaluator，next_artifact本包REVIEW；独立Evaluator另开evidence/l3_review/COST.json，不改Executor接受字节，唯一L3后逐AC验收。

账本windows=[{role:Executor,begin_utc,end_utc:null|UTC}]、implementation_attempts=1、l2_attempts≤1、l3_attempts=0、external_actions网络/API/安装/服务/浏览器/付款/模型均0。Evaluator扩展同schema、role=Evaluator、l2=0、l3=1。预算45执行/15评估/总60，另受累计105/45/150含父包/制包限制。每动作前核剩余，至少留8分钟收尾。旧任务文件、外部平台和Git写入全部禁止。
