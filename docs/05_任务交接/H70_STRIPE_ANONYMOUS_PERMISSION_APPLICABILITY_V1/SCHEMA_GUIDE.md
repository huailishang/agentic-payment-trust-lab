# H70 输出结构

CHECK只离线读文件，不做网络请求；通过仍须Evaluator审来源语义。JSON使用UTF-8、禁止重复key。

SOURCE_MANIFEST.json为sources数组，每项含id/url/file/sha256/bytes/started_at/finished_at/status。file位于sources/；成功status=200，存实际响应字节。失败请求只进入账本，不伪造来源正文。每条来源引用为{source_id,quote}，quote必须是归档UTF-8正文中的实际连续片段，不用模型改写冒充原句。

PERMISSION_MATRIX.json为rows数组，四项id见SOURCE_LOCK；每项含operation/key_family/observed/documented/unknown/refs。后三个事实维度均为字符串，refs为引用数组。无资料可refs=[]，documented明确UNKNOWN。观察只限H69实测，不把Account403外推其它操作。

RESULT.json含task_id/decision/rationale/matrix_sha256/side_effects；decision见SOURCE_LOCK；side_effects恰含runtime_api/credential_requests/cli_downloads/installs/browser_actions/local_services/checkout_sessions/payments/commits/pushes，全部整数0。REPORT用原生中文解释引用和残余未知，不粘贴H69私有消息。

ATTEMPT_LEDGER.jsonl为seq/event/attempt_id/kind/at，BEGIN动作前预留，END动作后追加status=SUCCEEDED/FAILED/INPUT_LIMIT。kind为active_work/implementation/source_http/l2/l3；source_http BEGIN含url，END含status_code/body_bytes，实际失败也计；若读取达到总预算前中止，保存实际读取字节数。每跳重定向独立BEGIN/END，下一跳重新审允许域。一个source_http同时只一个，禁止先并发再补账。主动工作BEGIN/END总长不超过35分钟，全部工作墙钟不超60分钟；未结束的L2/L3在门禁期间允许，提交前关闭。

RUN.py只用于来源获取/账本，须在每次请求前核URL、剩余额度与源域边界，不读取CLI配置/凭据；引用H69私有材料仅原位审阅，原错误正文不得写sources。SOURCE_LOCK的预算不授权任何Stripe运行请求。
