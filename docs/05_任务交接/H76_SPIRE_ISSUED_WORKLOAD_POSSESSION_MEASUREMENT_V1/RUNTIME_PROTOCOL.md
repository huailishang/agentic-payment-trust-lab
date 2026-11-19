# H76 冻结运行与证据协议

此文是合同依赖，不是已运行证据。所有命令由任务RUN.py以argv直接调用，不拼shell正文。具体平台只有linux/amd64；失败不切ARM/Windows或其它发行版。

## 固定构建与容器

Dockerfile从ASSET_LOCK的Python单平台digest开始；仅COPY已核SPIRE包中`bin/spire-server`/`bin/spire-agent`及三个wheel，路径以压缩包实际安全清单确定，禁止路径穿越/符号链接逃逸。先核归属与许可证；无额外镜像、apt、在线pip。`pip install --no-index --find-links /wheels --require-hashes -r /requirements.lock`只在构建层内执行。base/依赖来源许可见ASSET_LOCK；保存安装包METADATA/licenses。基础OS的传递组件未做全面许可证或漏洞审计，不声称生产审计。

容器名`h76-<phase>-<run_uuid>`，标签`agentic-payment-task=H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1`及`run-id=<run_uuid>`。规范选项：`--network none --read-only --cap-drop ALL --cap-add SETUID --cap-add SETGID --cap-add CHOWN --security-opt no-new-privileges --memory 1g --cpus 2 --pids-limit 128 --tmpfs /run:rw,nosuid,nodev,size=256m --tmpfs /tmp:rw,nosuid,nodev,size=32m`。不挂任何宿主目录/卷，不发布端口，PID/IPC不是host。使用docker create/start/inspect/cp/wait/rm（仅本包ID），保持退出容器直到公共证据复制完成，再删除。未授权时连create也不做。

容器内Python PID1负责进程回收；root运行发行者/Agent，`os.umask(0o077)`。各工作负载子进程以`user=1001/1002, group=1001/1002, extra_groups=[]`启动。UID名称非必要；单独私有目录0700、所有权各自匹配。公共socket目录0755、socket可供两UID连接（最终模式需取证），server管理socket和数据0700。root仅为测试管理信任边界，不声称抗宿主/root窃密。

## 最小配置（不得增UpstreamAuthority）

server.conf：server trust_domain=`h76.test`，bind_address=`127.0.0.1`，bind_port=8081，socket_path=`/run/h76/server-private/api.sock`，data_dir=`/run/h76/server-data`，ca_key_type=`ec-p256`，default_x509_svid_ttl=`10m`。plugins为DataStore/sql（sqlite3、/run/h76/server-data/datastore.sqlite3）、NodeAttestor/join_token（空数据）、KeyManager/memory。**无UpstreamAuthority**。

agent.conf：trust_domain=`h76.test`，server_address=`127.0.0.1`，server_port=8081，data_dir=`/run/h76/agent-data`，socket_path=`/run/h76/workload/api.sock`，trust_bundle_path=`/run/h76/bootstrap/root.pem`，workload_x509_svid_key_type=`ec-p256`。plugins为NodeAttestor/join_token、KeyManager/disk（私有agent-data）、WorkloadAttestor/unix（discover_workload_path=false）。配置与运行version必须保存。

先`spire-server run -config ...`；成功后`spire-server bundle show -socketPath ... -format pem`经管理路径保存根；`spire-server token generate -socketPath ... -ttl 300`只在容器私有内存/文件处理。`spire-agent run -config ... -joinToken <private>`。令牌参数/输出/默认Agent ID可能含秘密，公开命令/日志必须有明确字段脱敏记录，不能直接打印完整argv或docker top全部参数。

从本次Agent登记事实取得真实parentID，再`spire-server entry create -socketPath ... -parentID <actual-agent-id> -spiffeID spiffe://h76.test/agent/h76-agent/executor/h76-executor -selector unix:uid:1001 -x509SVIDTTL 600`。若父ID含加入令牌，公开记录不可逆关联摘要及脱敏占位，内部仍用真实值。保存entry ID、选择器、目标URI及Agent关联摘要。

UID1001：`spire-agent api fetch x509 -socketPath /run/h76/workload/api.sock -timeout 5s -write /run/h76/uid1001`，最多3次。v1.16.0实际命名`svid.0.pem`、`svid.0.key`、`bundle.0.pem`（固定官方源码已有归档）。只有恰好一个目标SVID可继续；多证书链如实记录，不截断成伪直接根。UID1002同命令写自己的目录，仅1次；连接成功后PermissionDenied/无匹配身份为有效拒绝，OS权限/超时不算。

## 持有者签名

WORKLOAD.py由UID1001执行，读UID1001目录中的SVID私钥，在容器内用cryptography的`ec.ECDSA(hashes.SHA256())`签名。挑战由host CHECK.py生成新的uuid nonce和实际issued_at_epoch并写入容器；不能让RUN.py复用旧签名。ASCII载荷**包含末尾换行**（与原验证器逐字节一致）：

```text
agentic-payment-possession/v1
nonce=<fresh_nonce>
agent=h76-agent
provider=h76-provider
executor=h76-executor
issued_at=<issued_at_epoch>
```

max_age_seconds=300，observed_at由采样时host实际UTC epoch取得，正例必须在窗口内。私钥不得写stdout、环境证据、镜像层、公开目录或host；只复制public/白名单文件，不能docker cp整个/run。此证明范围是被选择器覆盖的UID持有者，而非取证CLI与Python为同一PID。

## RUN.py接口与公开产物（冻结）

`RUN.py collect --phase executor|evaluator|l1 --run-id <uuid> --nonce <uuid> --issued-at <epoch> --out <repo-relative-output>`。输出路径是仓库相对路径，解析后必须严格在本任务evidence内。Executor实现其内部下载/构建/运行/清理，在phase=evaluator时不得修改已提交L2目录，只读必要的资产和脚本。必须先检查授权；所有相对路径解析后检查归属。

公开目录必含：PUBLIC.json、root.pem、leaf.pem、signature.b64、payload.bin、server.conf、agent.conf、entry.json、versions.json、docker_inspect.json、COMMANDS.jsonl、CLEANUP.json、server.redacted.log、agent.redacted.log、matching_fetch.stdout.log、matching_fetch.stderr.log、nonmatching_fetch.stdout.log、nonmatching_fetch.stderr.log、NONMATCHING.json。root.pem必须由管理CLI取得，leaf.pem保留完整实际链。

PUBLIC.json字段：schema=`h76-public/v1`、run_id、phase、nonce、issued_at_epoch、observed_at_epoch、trust_domain=`h76.test`、agent_ref=`h76-agent`、provider_ref=`h76-provider`、executor_ref=`h76-executor`、matching_uid=1001、signing_uid=1001、nonmatching_uid=1002、matching_pid、signing_pid、nonmatching_pid（正整数）、matching_svid_count=1、management_root_sha256（DER根指纹）、management_bundle_captured_before_fetch=true、root_export_command_ref、entry_id、agent_parent_ref_sha256、private_key_export_count=0、payment_callback_count=0、files（各公开文件SHA256，PUBLIC本身除外）。

versions.json字段：spire_server/spire_agent均为实际`-version`解析出的`1.16.0`，python=`3.12.13`，cryptography/cffi/pycparser为实际导入版本；base_reference为ASSET_LOCK.image_reference，built_image_id为实际docker inspect Image；downloaded_files为已获取4文件的filename→SHA256。原version命令、资产下载/校验原始日志仍须可回查，不能仅填期望值。依赖安装只来自这三个已核wheel。

NONMATCHING.json必须包含uid=1002、socket_connected=true、write_directory_accessible=true、rpc_status=`PermissionDenied`、svid_count=0及原始stderr/Agent日志引用；若实际RPC状态不同，不改成此值，判定INPUT_LIMIT/不通过后交Evaluator。CLEANUP.json含container_id、ownership_labels、container_removed、private_tmpfs_removed、host_private_key_files=0；冻结CHECK另用docker inspect对ID回查，不能只信布尔。

所有COMMANDS.jsonl行包含step、start/end、argv_redacted、exit_code或timeout、stdout/stderr相对路径与摘要、secret_redaction_fields；密钥/令牌相关stdout先在容器私有内存脱敏，公开材料标redacted。保留失败行，不覆盖原文件。下载账本逐块计数，对未取得状态的字段UNKNOWN。

Executor的ATTEMPT_LEDGER.jsonl保存asset/file attempt、image_pull、build、actual_container、matching_fetch、nonmatching_fetch、formal_l2等事件的唯一event_id、run_id、result与消耗。接受后此账本只读；Evaluator新增事件（含formal_l3）只写evidence/evaluator_ATTEMPT_LEDGER.jsonl。累计边界合并两本复算，不能重置。每次动作前追加STARTED事件，结果以kind=result及ref_event_id引用原事件另行追加，不重复计尝试。失败也计数，不得只在成功后记账。L3复用已核资产，不重新下载或修改已提交脚本/缓存；环境不支持则停止。

## 独立L3

Evaluator先固定接受快照，再检查全部任务脚本，不只信JSON。CHECK用新uuid根本不同的容器流程；新根指纹/nonce/证书签名须与已提交L2不同。单次L3不改任何接受文件，仅写evidence/l3及派生新目录。另从公开证书独立检查密码学签名、URI、有效期、BasicConstraints/KeyUsage，并通过原验证器构造10反例。不能因旧向量通过就把实际来源记通过。

官方依据：固定release及源码见ASSET_LOCK；[Server配置/CLI](https://spiffe.io/docs/latest/deploying/spire_server/)、[Agent配置/CLI](https://spiffe.io/docs/latest/deploying/spire_agent/)。官方配置语义是方案依据，兼容性必须由实际产物证明。
