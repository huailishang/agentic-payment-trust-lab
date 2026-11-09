# H64执行入口：先取完整材料，再判断是否值得回放

本包为CONTRACT_FROZEN（合同已冻结）/Executor（执行者），尚未执行。先读CONTRACT、SOURCE_INPUTS、CHECK和VALIDATION_PLAN。不要复用H63/H63R旧全工作区检查器。

## 顺序

1. 运行冻结CHECK.py source，确认新保护基线；仅把CURRENT本任务state/phase改为EXECUTING。建立ATTEMPT_LEDGER，任何GET/安装/样本读取/正式L2前先落预留，结束后补终态；失败不删。准备阶段PREPARATION不是执行期账本。
2. 需要解码时，只下载SOURCE_INPUTS指定wheel并验SHA；用现有系统Python的pip从本地wheel装到 `.task_envs/H64/parquet_reader/`。示例参数：`python -m pip --isolated --disable-pip-version-check install --no-index --no-deps --no-compile --target .task_envs/H64/parquet_reader <本包已验hash的wheel路径>`。不得调用pip在线索引、升级包、修改全局或既有venv。
3. 编写任务内ACQUIRE，只允许SOURCE_INPUTS白名单公开GET，逐块限字节、30秒超时、严格处理重定向与预算；仅保存初始固定URL和跳转host，不存预签名查询参数。四Parquet必须符合固定checksums。读messages时先投影选择字段并落SELECTED，再看剩余字段。允许安装一次是执行包内的专用解码工具范围，不代表允许安装整个回放环境。
4. 按固定id读取messages/turns/wire，以及所选world的envpack/manifest；不额外挑成功/失败样本。原文件保留，输出可以裁剪到所选行的derived摘要，但引用回原始行组/行索引/字段。单份大分区可能含未选episode，分析范围只限选定6例。
5. 编写MEASURE和纯函数ORACLE.evaluate。确认、执行、金额单位、顺序、id关联和代码可见性分别审阅。最终hash或标签不是实际付款记录；静态后端读取路径不是实际回放结果。缺输入允许NOT_JUDGEABLE（不可判定）。
6. 输出MEASUREMENT和单一结论；CONTINUE_TO_REPLAY_BASELINE（仅建议先验回放基线）、STOP_SOURCE_VIEW（停止该完整视图）、INPUT_LIMIT（访问/依赖/预算限制）三选一。原始材料不足时不要靠编造Internal Record（内部记录）补齐；不要求整个P1–P5都可用，也不宣布对照或产品已通过。
7. L1先用CHECK各子命令。正式L2调用前记预算，然后按以下准确入口执行；REPORT引用全部EV，CURRENT保持EXECUTING/Executor交评估者。首次L2失败时若未超过两次且不改合同，可合同内修复；改冻结CHECK/范围/样本/依赖要回交。

正式L2（在仓库根目录，out目录每次唯一）：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01 --mode executor
```

交接前结构校验：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

评估者以同一计划 `--mode evaluator` 写新的L3目录，离线读取已固定材料，不重复GET/安装、不调用上游。结构成功不自动签收。

## 机器格式（键名以CHECK.py为准）

- SELECTED.json：`samples=[{episode_id,world_id},...]`，必须符合固定投影和排序；先写再读结果。另存选择时间、选择规则、来源文件sha和名单sha作审计。
- ATTEMPT_LEDGER：task_id、active_minutes、formal_l2_attempts、measurement_versions、installation_calls、model_calls/payment_calls/product_calls/upstream_replay_calls（均0）；attempts和materials数组。
- 每attempt：id、kind（public_get/install/sample/l2等）、started_at、finished_at、status（SUCCEEDED/FAILED/LIMIT）；GET另含初始url、bytes_received（失败也计）和redirect_hosts（即使为空也必须有）。成功材料另入materials `{file,url,sha256}`，file必须在本包acquired下；安装stdout/stderr单独保留。
- MEASUREMENT顶层：task_id、dataset_revision、code_revision、replay_executed=false、product_effect_measured=false、candidate_classification=REFERENCE_ONLY、evidence_level=SOURCE_READINESS_ONLY、samples、backend_access_citations、decision。
- samples每项：episode_id、world_id；facts六键 confirmation/payment_call/payment_result/business_state/correlation/replay_inputs，每项 `{status,reason,citations}`；oracle_input、observed_verdict、business_state_level、unit_and_link_reason、unit_citations。
- observed_verdict：WITHIN_CAP_OBSERVED（观察到未超额）/OVER_CAP_OBSERVED（观察到超额）/NOT_JUDGEABLE（不可判定）；前两者仍需注明数据层级，绝不自动等于独立PSP事实或产品控制成绩。
- business_state_level：MISSING/REPORTED_TOOL_STATE/PUBLISHED_INITIAL_STATE/FINAL_STATE_DIGEST/OBSERVED_BACKEND_EVENT/CODE_PATH_ONLY。按实际源选择，不能把协议响应冒充独立事件库。
- 引用：`{file,kind,value_sha256,...}`；Parquet用kind=parquet、row_group、row_index（均从0）、pointer（原行对象RFC6901）；JSON用kind=json、pointer；源码用kind=text、line（从1）。摘要为UTF-8规范JSON值的SHA256，参数 `ensure_ascii=False,sort_keys=True,separators=(',',':')`。
- confirmation引用turns的用户/购物者行；缺失事实无正引用。需要说明消息文本内部字段时引用原字段整体，不篡改源增加结构。
- oracle_input：接口及八冻结例见ORACLE_CASES。金额为USD整数最小单位，非负且不接受bool；同checkout/币种、明确精确关联、来源user_message、确认seq严格小于执行seq才可比较。没有这些条件返回NOT_JUDGEABLE，不使用隐藏任务或标签。
- decision：kind、reason、next_question。仅CONTINUE可给一个next_question；该结论须有金额可比较样本、全部选择world材料、完整跨表关联和backend_access_citations。其它next_question=null。

## 成本与边界

180分钟、20GET、256MiB总接收、128MiB单文件、6样本×2版、1次隔离解码安装、2L2。程序或材料问题导致无法读表，可完成可核验的INPUT_LIMIT报告；不得把它叫“数据集没有合适轨迹”。不启动上游，不写产品，不取受限数据，不Git提交或推送。
