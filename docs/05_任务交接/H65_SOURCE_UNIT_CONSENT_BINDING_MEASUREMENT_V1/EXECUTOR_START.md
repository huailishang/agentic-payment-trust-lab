# H65 执行入口

先读仓库根CURRENT、本目录CONTRACT/INPUTS/CHECK/VALIDATION_PLAN及PUBLICATION_READINESS。状态CONTRACT_FROZEN/Executor，尚未执行。H64R已PASS，不再执行或修改其修复包。

1. 远端可先用标准Python运行本目录CHECK.py package核对公开包。此项通过不证明本地数据齐备。真正开工前必须运行CHECK.py source；缺输入时报告INPUT_LIMIT，不下载、不改门禁。
2. source通过后才把CURRENT改EXECUTING/Executor。每次完整episode读取/正式L2先持久记账；75主动分钟/12源读取/1分析版/2L2，网络/安装/模型/产品/回放/付款0。
3. 只读原六例和锁定静态材料，写ANALYZE.py及RESULT.json。每例unit、binding包含status、citations、reason；binding另列edges，每边有origin=SOURCE_OBSERVATION/CODE_INTENT/INFERENCE及citation。原金额、币种、checkout和用户确认原文分别保留，不以代码意图或缺字面id预设结论。
4. 引用格式：file为INPUTS.readonly内仓库相对路径；静态文本用line_start/line_end/text_sha256（对所选完整行含原换行的UTF-8字节摘要）；Parquet用row_group/row_index/pointer/value_sha256，可加embedded_pointer/decoded_value_sha256。引用中的episode_id必须与样本相同。不能只引用自己生成的总结。
5. RESULT顶层含task_id、samples（六例按INPUTS顺序）、verdict、reason（至少40字符）、replay_executed=false、product_effect_measured=false。unit/binding的status仅PROVEN/PARTIAL/UNKNOWN/INPUT_LIMIT；PROVEN至少有原源引用，binding还须有同episode直接源观察边。每例unit/binding各有≥40字符说明。
6. ATTEMPT_LEDGER含task_id、active_minutes、measurement_versions、formal_l2_attempts、sample_reads、network_calls/installation_calls/model_calls/product_calls/upstream_replay_calls/payment_calls全部0；attempts记每次预留及SUCCEEDED/FAILED终态。所有失败保留。
7. 无完整直接证据就STOP_SOURCE_VIEW，缺已锁定环境输入才INPUT_LIMIT；至少一例单位/绑定均有直接证明才CONTINUE_TO_REPLAY_BASELINE，仍不执行回放。不要提出第二个同六例静态修复包。

公开元数据检查（仓库根目录）：

```text
python docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/CHECK.py package
```

本地开工检查：

```text
.task_envs/H47/.venv/Scripts/python.exe -B docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/CHECK.py source
```

正式L2（每次out唯一，先预留L2预算）：

```text
.task_envs/H47/.venv/Scripts/python.exe -B ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/evidence/l2_executor_01 --mode executor
```

强制VP全通过才提交REPORT及证据；CURRENT保持EXECUTING/Executor。提交前运行公共validate_workflow.py --repo . --current CURRENT.md。Evaluator独立L3和逐源语义复核，执行者不签发PASS。Executor无commit/push/API权限。
