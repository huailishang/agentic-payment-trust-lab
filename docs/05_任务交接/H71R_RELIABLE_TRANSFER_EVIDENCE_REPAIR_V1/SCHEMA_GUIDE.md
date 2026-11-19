# H71R 离线接口与派生结构

RUN.py不含网络客户端/子进程启动，允许Python标准库文件/JSON/hash/时间；顶层导入不得有副作用。冻结驱动先检查危险导入，再在socket/子进程拒绝的隔离测试上下文内导入、调用。所有外部响应仅通过驱动注入的opener获取。

必须提供capture_attempt(opener, *, body_path, byte_limit, chunk_size=65536, clock=None, timeout_seconds=30) -> dict。opener为无参数函数，返回带status/headers/read(n)/close()的流；可能在打开或read时抛异常。body_path是驱动给定的临时文件路径。只调用一次opener，不自动重试/跟重定向。clock可注入单调时钟，执行前及块间检查期限，真实底层read超时由调用者的流提供，本包不声称具备强制中断任意阻塞流的能力。

返回至少http_status/failure_phase/body_complete/body_bytes_observed/body_bytes_total/bytes_charged/body_sha256/error_type/response_closed。failure_phase为COMPLETE/OPEN/HEADERS/BODY_READ/BODY_WRITE/LIMIT/TIMEOUT；异常只保留类名，不回显完整异常消息。HTTP404等状态仍可完整读取，传输成功与业务HTTP成功分开，不将状态改为None。

文件保存每个成功返回的完整块。body_bytes_observed为成功read返回的字节数，body_sha256必须等于实际文件摘要（写失败例另外保留observed与archived的差异，驱动不制造写失败）；只有收到EOF且前序无异常时body_complete=true、body_bytes_total=observed，否则total=null。bytes_charged在成功块后取实际观察量，read异常时计先前观察量加本次请求的最大可能字节数；不能超过byte_limit。读到上限但未证明EOF就LIMIT，不额外读越界字节。空流成功可完整0，异常/未知不得伪装成完整0。

EVIDENCE_CORRECTION.json字段：original_snapshot_sha256；gets（三项url/status=200/body_sha256/empty=true/has_more=false）；failed_sources（两项attempt_id/http_status=200/archived_bytes=0/received_bytes=null/failure_phase=BODY_READ）；download（http_status=null/http_status_certainty=UNKNOWN/failure_phase=UNKNOWN/archived_bytes=0/received_bytes=null/guaranteed_remaining_download_bytes=0）；uncertainty_note与no_historical_backfill=true。保守上下界可另加，但必须可由原read大小推导，不声称已证明超额。

CORRECTED_MATRIX.json含rows四项id/observed/documented/unknown/observations；id见EVIDENCE_GOLD。checkout_required_endpoints.observations恰等于纠正投影的三个GET，observed明确200，不能含NOT_MEASURED。其它未测维度保留；source_notes至少两项{claim,source_id,quote}，source_id来自金标两份既有文档，quote为原始文件连续正文片段（20～1200字符），禁止导航标签，claim由Evaluator独立审支持关系。

RESULT.json含task_id/decision=REPAIR_COMPLETE/original_h71_verdict=REJECTED/correction_sha256/matrix_sha256/side_effects。side_effects恰为network_requests/downloads/runtime_api/browser_actions/local_services/installs/environments/checkout_sessions/payments/commits/pushes，全部整数0。REPORT逐AC引用证据并区分修复、历史事实与外部未测能力。

账本seq/event/attempt_id/kind/at；kind仅active_work/implementation/l2/l3。END含status=SUCCEEDED/FAILED/INPUT_LIMIT。主动区间不重叠，120分钟累计/3小时墙钟；实现2/L2三/L3一。最终提交前均关闭；门禁期间允许当前active_work/L2/L3尚开。任何失败或版本不删除，所有原件只读。
