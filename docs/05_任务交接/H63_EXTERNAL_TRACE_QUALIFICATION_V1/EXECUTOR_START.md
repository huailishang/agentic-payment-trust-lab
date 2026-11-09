# H63 Executor入口

先读AGENTS、地图r101、本包CONTRACT、SPEC、SOURCE_DECISION、INPUTS、VALIDATION_PLAN。

本包只是离线外部资料资格测量。冻结六预览已准备，不能扩样、联网、运行上游工具或改产品。测出一个有源依据的后续只读问题或诚实STOP均可；不要求造漏洞。

先把CURRENT本任务state改为EXECUTING、current_role保留Executor。每次完整提取前追加ATTEMPT_LEDGER.json的sample预留；完整一套6条，最多18。每条预留必须有唯一id、sample_id、started_at和terminal_status，失败不删除。MEASUREMENT格式参照SPEC与CHECK；每例有facts、contracts及evidence_level，每个事实有status/citations/reason，每项P1–P5有input_status/fact_keys/reason。顶层decision含candidate_classification/view_decision/candidate_sample_ids/question/reason/limits/missing_inputs，cost含active_minutes及五项调用零值。证据引用原始行对象，不能引用重新编号的消息列表。

运行环境使用已装.task_envs/H47/.venv/Scripts/python.exe。准备检查通过不等于L2。正式提交前按计划运行中央runner：

` .task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01 --mode executor `

L2通过才写SUBMITTED_FOR_REVIEW；REPORT引用四个EV原始三件套和Gate。提交后CURRENT保持EXECUTING/Executor，由Evaluator接受并独立L3。报告与测量须保留实际成本、缺输入、无产品比较和源视图上限。
