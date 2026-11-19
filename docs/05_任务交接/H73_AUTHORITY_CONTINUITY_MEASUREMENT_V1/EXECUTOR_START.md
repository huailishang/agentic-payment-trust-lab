# H73 Executor start

全局位置：A–D本地关闭；E受控本地代表闭合；F受控Stripe切片关闭。B-22为外部交易的原授权/明确续授事实能否连续回查，尚不是已证实漏洞。本包measurement-only，不继承旧支付/运行权限。

1. 读CURRENT、r124地图、CONTRACT、SPEC、INPUTS、FREEZE及PREPARATION。先运行CHECK.py preservation，记录git status并开启ATTEMPT_LEDGER.json工作窗；不运行H72产品/旧checker。
2. 在PATH选择既有Conda agent Python 3.12.13，设置PYTHONDONTWRITEBYTECODE=1。公共runner需要现有PyYAML；缺依赖则INPUT_LIMIT，不安装。无需tests导入隔离，也不运行产品测试。
3. 创建ANALYZE.py，只读冻结公共sources与两白名单私有材料。逐项产出MATRIX.json和RESULT.json；引用格式与必填结构见SPEC/CHECK。从PRIVATE_REF取目录仅供内存访问，不公开该路径。SQLite使用只读URI及query_only。
4. 一次完成四旅程/三个边界/全部字段；运行许可、合成确认与真实外部付款分开，保留UNKNOWN。特别回查N01原创建与续行、C01无付款、R01只读恢复、D01记账恢复。不要把工厂重建当原事实或真实身份。
5. 按四分支提交决策及其依据。若推荐最小能力，给出最小接缝与同基线对照设计，仍不实现。普通脚本/引用修正可在预算内自主完成，不逐步请求Human。
6. 用公共run_validation.py运行六项计划，out=evidence/l2_attempt_001，mode=executor；第二次只能用l2_attempt_002。公共工具路径为../localagent-common/skills/evaluator-executor-workflow/scripts/。全部原始meta/stdout/stderr保留。
7. L2通过后完成REPORT、关闭工作窗并保存最终成本；生成SUBMISSION.json的files映射，覆盖ANALYZE/MATRIX/RESULT/账本/REPORT、全部derived及全部L2原始文件。SUBMISSION不含自身、CURRENT、Evaluator未来输出；l2_gate={path:最终通过的L2-GATE.json相对本包路径,sha256:该文件摘要}，该gate也必须列入files。
8. 只切CURRENT到READY_FOR_REVIEW / Evaluator，next_artifact=本包REVIEW.md。保持冻结控制字段及全false权限。Evaluator须先验证SUBMISSION，再依L3_PROCEDURE独立逐源回查和唯一L3；评估成本另写evidence/l3_review/COST.json，绝不回写已接受的Executor账本/快照。

账本最小结构：schema=h73-cost/v1；windows=[{role:Executor|Evaluator,begin_utc,end_utc:null|UTC}]；l2_attempts整数；l3_attempts整数；external_actions={api:0,network:0,install:0,service:0,browser:0,payment:0,model:0}。BEGIN/END与失败不可删，整窗墙钟入账。开启正式L2/L3前先增加对应计数；不能在检查后再补造次数。公共runner从repo根调用，当前解释器的python须为已验证agent。

缺源/漂移/预算耗尽或六项不能通过：保留BLOCKED报告和全部证据，不标READY_FOR_REVIEW，不增加L2或新来源。不要提交、推送、启服务、调用Stripe或下载任何东西。
