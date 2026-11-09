# H64R执行入口

状态CONTRACT_FROZEN（合同已冻结），尚未执行。先读CONTRACT、CHECK、父H64 REVIEW和RV-EV-06反例。只复用原SELECTED六例、已获四Parquet/11个world以及现有解码器，禁止对缺失文件重新GET。

1. 初始CHECK.py source通过后，把CURRENT本任务改EXECUTING/Executor。建立本任务新账本；每个sample读取、版本和L2前预留，失败保留，最多90分钟/12样本读取/2版本/2L2。
2. 新写EXTRACT.py；不要import/执行H64 MEASURE/ACQUIRE/CHECK。按call_id分组，同一结果用tool_call_id，wire用source_call_id；每个父子调用分别列出，不从池中分别取第一个元素。原source里出现的四类支付工具都清点，不能省略坏链。
3. 保留协议/工具已有原始金额、币种、checkout与阶段。call-68响应4425/usd必须出现；若最小单位尚无充分依据，保留raw_amount并把amount_minor置null/单位UNKNOWN（未知），不得因此删除原始观察。用户确认的44.25美元与执行字段能否绑定要另作证明，不能因为缺签名一律清空，亦不能凭邻接补造。
4. 原H64 ORACLE纯函数和8个冻结例可只读复用，不能改。最终不可判定允许保留，但说明missing_dimensions；这不是说付款未发生，更不是控制失效。
5. 写本任务MEASUREMENT/REPORT及原始证据，通过新计划L2后提交；CURRENT保持EXECUTING/Executor。Evaluator独立L3并逐源语义复核。

## 输出格式

- MEASUREMENT顶层：task_id、classification=REFERENCE_ONLY、replay_executed=false、product_effect_measured=false、samples、access_limit、assessment（至少40字符）。
- samples按旧SELECTED顺序6例：episode_id、world_id、call_chains、raw_payment_observations、binding_status（PROVEN/AMBIGUOUS/MISSING）、binding_citations、missing_dimensions、reason、oracle_input、source_verdict。
- 每条call_chains：call_id、call_citation、result_citations、wire_citations、status。引用值必须是同一标量id，同episode；有结果与wire为COMPLETE，否则PARTIAL。父子关系额外解释，不能混合id。
- 每个raw_payment_observations：call_id、seq、origin（tool_response/protocol_response/backend_event）、phase（REQUEST/TOKEN_ALLOWANCE/REPORTED_COMPLETION/UNKNOWN）、raw_amount、currency_raw、checkout_id及amount_citation/currency_citation/checkout_citation/call_id_citation；unit_status（PROVEN/UNKNOWN）、amount_minor、unit_citations。phase是源报告的阶段，不能升级成真实清算。
- 原始源引用：file为**仓库相对路径，必须指向H64 acquired或references**；kind=parquet时row_group/row_index从0、pointer=原行对象RFC6901、value_sha256为UTF-8规范JSON值的SHA256（ensure_ascii=False,sort_keys=True,separators=(',',':')）。JSON/text引用支持pointer/原行号。
- 若response_body原值是JSON文本，用pointer=/response_body与该原字符串摘要，再加embedded_pointer=/total、decoded_value_sha256（内部字段值摘要）；币种/checkout同理。不要把解析出的对象回写原Parquet。
- access_limit.missing_world_ids固定为 `["env-bd45a7e9be19"]`，保留原访问限制。assessment区分已修复测量、未证实绑定、实际后端未知和回放未执行；最多提出一个后续测量问题，不执行。
- ATTEMPT_LEDGER：task_id、active_minutes、measurement_versions、formal_l2_attempts；network_calls/installation_calls/model_calls/payment_calls/product_calls/upstream_replay_calls全部0；attempts各项id/kind/started_at/finished_at/status（SUCCEEDED/FAILED），其中sample条目6–12条。先持久预留再读样本，正式L2也须预留。

## 正式命令

在仓库根目录用以下入口，每次out唯一；先记L2预算：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/evidence/l2_executor_01 --mode executor
```

提交前：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

本包不能通过修改冻结CHECK、旧数据、旧报告或原预算来“修复”；只有新提取产物可以修订。额度耗尽或需新数据/权限就停止并交Evaluator，不启动源运行时、产品或真实资金。
