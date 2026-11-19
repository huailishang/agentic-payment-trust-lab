# H77 固定测量接口与原始证据要求

本文件只定义任务测量实现，不改变产品、公共workflow或旧H76验收口径。Executor实现RUN.py，可拆本任务WORKLOAD.py/TASK_TESTS.py；不得更改本文件、CHECK.py或AUDIT.py来适配实现。

## 调用与唯一运行

入口是当前Windows agent Python：`python -B <H77>/RUN.py collect --run-id <Evaluator生成32位hex> --nonce <Evaluator生成32位hex> --out <repo相对专属路径>`。只有CHECK.py live能正式调用；Executor不启动任何实际发行。RUN.py须拒绝错误目录、非本包Evaluator输出、已有运行标记不匹配或非READY_FOR_REVIEW路由。

用wsl.exe显式选择Ubuntu，以argv/任务脚本方式执行；不嵌套拼接shell正文。只启用已安装Ubuntu、现有sudo -n/setpriv/Python/cryptography，不安装包。已知旧实验版本Ubuntu24.04.2/Python3.12.3/cryptography41.0.7只是历史事实；新环境版本与依赖模块文件摘要须记录，不伪装原Docker锁定wheel。缺兼容既有依赖则停止。不得启动docker-desktop或更改WSL设置。

读取旧ASSET_LOCK唯一SPIRE archive。只检查现有WSL用户缓存，不下载。校完整长度及SHA-256后，从archive读取确切两个普通文件成员；拒绝链接、绝对路径、`..`及逃逸路径，不使用不受控extractall。逐个成员SHA与最终执行二进制SHA必须一致。不得直接执行未经本次绑定核对的旧解压缓存。

只创建`/dev/shm/h77w<run_id>`，路径实解和本次创建所有权必须匹配；私有目录0700，密钥只在该tmpfs。使用原h76.test/目标Agent/Provider/Executor，原Server/Agent配置约束：回环随机端口、EC-P256直接根、memory Server key manager、join_token节点引导、唯一unix UID选择器，非dummy/upstream CA。WSL没有Docker网络隔离或只读rootfs，不作等价声明。

步骤：真实Server启动→管理socket导根→本次私有token→真实Agent→管理agent list明确取父ID→创建登记并管理entry show核对→UID1001取证→UID1002接口拒绝→UID1001签名→真实观察时间→公共产物→所有分支清理→独立清理命令。管理列表/entry可按真实结构解析（包括分开的trust_domain/path），不可扫描任意字符串猜ID、手造父ID或从成功日志回退。管理轮询只在单运行内同步，不重启服务生成新根。

三操作进程需提供内核/proc/PID/status观察。可通过任务局部包装进程同UID exec实际CLI/签名进程，在操作前读自身/proc/self/status并输出原始内核字段，同时由父观察器核PID对应命令；不能用仅print预设UID代替。签名私钥在UID1001内读取，目录0700/密钥0600，owner1001。管理员是受信任边界，公开证书/签名可复制，私钥和token不得复制至Windows。

匹配取证最多3次，仅同步重试；不匹配取证1次，须RPC PermissionDenied/no identity issued、非0退出且0 SVID。全部尝试追加账本。每次实际CLI退出/耗时/真实argv保存；涉及私有token的命令或响应保留明确标记的脱敏投影，不写秘密。清理只针对本次拥有PID/进程启动标识及专属路径；异常/信号/超时均执行finally清理。防挂单命令180秒、整次发行20分钟，额外清理时间不限。

## 输出文件与字段

目录内必须包含：RESULT.json、root.pem、leaf.pem、payload.bin、signature.b64、SOURCE.json、PROCESSES.json、ENVIRONMENT.json、server.conf、agent.conf、agent-list.redacted.json、entry.redacted.json、server.redacted.log、agent.redacted.log、matching.stdout.log、matching.stderr.log、nonmatching.stdout.log、nonmatching.stderr.log、COMMANDS.jsonl、CLEANUP.json、PUBLIC_INDEX.json。日志保留所有与原始事实有关的内容；脱敏/截断及原因必须显式记录，不将投影称为秘密原件。禁止PUBLIC_INDEX自包含散列。

RESULT.json至少包含run_id、nonce、issued_at_epoch、observed_at_epoch（采集后真实UTC秒）、status=ISSUER_FETCH_SIGNATURE_CAPTURED、signing_uid=1001，以及原H76相同事实字段。规范payload与H76相同，含nonce、Agent、Provider、Executor、issued_at及末尾换行，不增加金额/用户意愿含义。

SOURCE.json：archive_sha256、archive_size、source=fresh_extraction_from_locked_archive、asset_downloads=0；binaries映射spire-server/spire-agent，各含archive_member、archive_member_sha256、executed_sha256、version=1.16.0；root_source=server_management_socket_before_agent_start、root指纹/实际命令/事件时间、parent_source=server_management_agent_list、parent_id_sha256、entry_id、selector=[unix:uid:1001]、target。字段必须可回查真实命令与管理返回，不由任务自报取代。

agent-list.redacted.json与entry.redacted.json保存CLI返回的完整JSON结构，只将token派生父ID中的秘密片段替为固定占位符，并记录同一原始父ID摘要。Evaluator逐字段核实际管理列表/登记/叶URI/父ID相同、只有一个选择器，不能以非空JSON当作验收。管理者/root受信任，不声明抵御管理员伪造。

PROCESSES.json：matching/nonmatching/signing各含pid、kernel_uid、kernel_euid、proc_status（原内核文本）、argv_public、same_workload_socket=true、socket_path；另含matching_svid_count=1、nonmatching_svid_count=0、private_key_owner_uid=1001、private_directory_mode=0700、private_key_mode=0600及对应观测来源/命令。不可将签名进程误称取证RPC进程；same_workload_socket表示同次凭据来源引用。

ENVIRONMENT.json：distribution=Ubuntu、python_version、cryptography_version、cryptography_files_sha256（既有模块文件路径→SHA）、host_installs=0、package_installs=0、docker_used=false，以及实际用户/kernel/WSL版本和测量方式。证据中的本机路径仅用于本地可复核材料，不提交远程。

CLEANUP.json：owned_processes_alive=[]、private_tmpfs_exists=false、public_private_key_files=0、independent_check_exit_code=0、independent_check_command，列出各被清理进程PID与启动标识、路径所有权核对/退出码及独立检查原始stdout/stderr文件引用。只看本次资源，不删除/停止其它任务。独立检查来自第二条命令，不能只记录finally已被调用。

PUBLIC_INDEX.json结构`files: {relative_filename: sha256}`覆盖上述全部事实文件及嵌套原始证据，禁止逃逸路径、私钥后缀或私钥PEM。成本：本次固定文件新下载0、支付0、模型API0；既有文件核验字节与历史下载/UNKNOWN分别记录。不能把公开私钥扫描无命中扩大解释为管理员不可读取密钥。

## 离线自检义务

可用固定旧公开输入测试路径校验、参数/JSON解析、脱敏、管理响应解析及清理guard（只操作任务自己创建的非敏感临时测试文件）；不能生成本地合成证书作为新实际正例。TASK_TESTS不是新增产品case，不替代冻结十负例/原130测试。L2前Executor必须提交脚本的AST/语法自检及上述关键guard离线检查原始输出；Evaluator接受前人工审实现。
