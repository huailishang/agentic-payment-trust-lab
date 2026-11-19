# H71R2 接口与真实公共门禁

RUN.py保留capture_attempt(opener, *, body_path, byte_limit, chunk_size=65536, clock=None, timeout_seconds=30)接口与原11探针行为。只使用注入opener；不导入网络/动态执行/子进程模块，不产生顶层副作用。

返回原http_status/failure_phase/body_complete/body_bytes_observed/body_bytes_total/bytes_charged/body_sha256/body_bytes_archived/error_type/response_closed，新增body_artifact_owned、body_sha256_state=KNOWN/UNAVAILABLE/NOT_OWNED、errors=[{phase,type}]。错误仅阶段/类名，无消息/私有路径。body_complete只在完整读取及归档证据成立时true；异常total=null。未归属输出时sha=null/NOT_OWNED、本次archived=0，不读取已有文件摘要。

唯一目标body_path在opener前独占创建（例如xb或O_EXCL）。不能自动改到其它文件/旁路目标后忽略给定目标；已有文件/目录或准备失败时opener=0，OUTPUT_PREPARE，body_artifact_owned=false。新建文件在opener失败时可留下本次空文件，owned=true，但body_total仍未知。

正文返回字节为observed，归档量为真实成功保存量；短写可在同块内有界补齐，或返回BODY_WRITE且保留准确前缀。摘要/属性检查如果失败，不得让异常冒泡丢整份结果，返回null/UNAVAILABLE或经实际写入证明的增量摘要。主读Timeout与close OSError同时出现时errors两者均保留，主error_type仍TimeoutError，response_closed=false，不谎称清理成功。

RESULT.json含task_id、decision=REPAIR_COMPLETE、implementation_sha256、input_correction_sha256、input_matrix_sha256、side_effects（network_requests/downloads/runtime_api/browser_actions/local_services/installs/environments/checkout_sessions/payments/commits/pushes恰为整数0）；明确previous_h71r_verdict=REJECTED。原矩阵/纠正无需另生成，INPUT_SEAL直接绑定原件。

账本seq/event/attempt_id/kind/at，kind仅active_work/implementation/l2/l3；END加status=SUCCEEDED/FAILED/INPUT_LIMIT。预算与旧修复同为120主动分钟/3小时，2实现/3L2/1L3；所有正式L2均以原公共runner执行且原输出保留。不能把手动诊断写成“完整L2”。

正式命令（从仓库根目录；每次输出目录新建，不覆盖旧尝试）：

```text
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/evidence/l2_attempt_001 --mode executor
python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
python docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/CHECK.py submission
```

REPORT必须含Task ID、Baseline HEAD、Executor status、Workspace snapshot、Changed files、Deviations and unresolved items、Impact comparison（Measurement evidence/Before/After/Delta/Guardrail result/Scope caveat）、L2 Task Gate（Gate result/Gate summary/Validation plan）和EV-01至EV-07各AC/Meta/Stdout/Stderr完整索引。先据真实L2填写，不能提前写PASS；最终三个命令皆0才申请交接。CURRENT仍EXECUTING / Executor，Evaluator验合格后接受。

公共python命令不可用时，只修任务级PATH/隔离别名或选已验证宿主，不改冻结command，不把解释器替换当自建runner理由。公共runner/capture/validator已保护；本包源码中不得生成L2-GATE或EV元数据。后续独立Windows L3不替代Executor的合法L2。
