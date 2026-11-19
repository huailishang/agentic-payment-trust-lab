# H76 Executor 执行报告 — Docker P0阻塞及WSL真实发行替代实测

**Task ID**: H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1  
**Executor status**: Docker路径BLOCKED / INPUT_LIMIT_ENV；负责人新授权WSL替代切片已实测成功，待独立评估  
**Submission**: WSL受控替代实验已交执行报告与证据；原冻结Docker H76正式L2仍NOT_RUN  
**Evaluation**: NOT_RUN；没有L2、L3或评估者PASS

## 授权与范围

项目负责人于2026-11-16T11:59:25Z明确要求直接执行H76，实施完成后再由评估者统一独立审查；本次授权已记录在 `AUTHORIZATION.md`。旧 `OWNER_RUNTIME_DECISION.md`（暂不运行）保持原样，时间上较新的本次授权取代其暂停决定。运行范围仅限 `AUTHORIZATION_REQUEST.md`、合同及冻结资产。

一份负责人授权前的 `CURRENT.md` / `CONTRACT.md` / `FREEZE.json` / `REMOTE_HANDOFF.md` 原件已存于 `references/before_owner_run/`；授权后仅作一次性授权元数据收口，`CONTRACT_FROZEN` / `EXECUTING`，技术验收准则、资产、预算与禁止范围不变。

## 已执行及实际观察

1. 通过Windows已安装的conda `agent` Python执行冻结 `CHECK.py preflight`：`protected=1502`，通过。
2. 更新授权与技术冻结摘要后，执行 `CHECK.py preservation`：`protected=1502` 且 `authority_checked=true`，通过。
3. 对指定Windows Docker endpoint `npipe:////./pipe/dockerDesktopLinuxEngine` 检查：Windows Docker客户端29.4.0存在，但Linux Engine管道不存在；原始输出保留于 `evidence/executor_p0/BEFORE_START.json`，首次单独CLI输出在执行会话中。
4. 按负责人批准的P0分支，仅启动已安装Docker Desktop一次。Windows进程启动调用返回 `LAUNCHED`，PID 10072；这不等于daemon已就绪。原始记录 `evidence/executor_p0/DESKTOP_START.json`。
5. 随后复查固定端点仍失败：`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`。原始输出 `evidence/executor_p0/AFTER_START.json`（最后一次复查时间 `2026-11-16T12:10:20.729500+00:00`）。使用Windows `tasklist.exe` 只读查看 `Docker Desktop.exe` 和 `com.docker.backend.exe`，均未返回运行中的匹配进程；原始Windows命令输出保存在 `evidence/executor_p0/tasklist_desktop.stdout.log` 与 `tasklist_backend.stdout.log`（两者SHA-256均为 `cb1256981f7b3ac53e3cfc7c6a13d4b058702bb707431b31e202abfcf6782f07`）。
6. 因合同限定必要时**最多启动Desktop一次**，且不得修复WSL/改backend/设置/换平台，触发 `INPUT_LIMIT_ENV` 停止。没有进行资产下载、容器构建、SPIRE实际签发、工作负载持有证明与正式L2。

**结论：这是P0真实环境失败，不是SPIRE机制失败，不能以本地合成证书补成正例。** 现有Docker Desktop为什么不能持续运行尚未定位；没有把猜测写成故障原因。

## 原始证据与账本

- `evidence/executor_p0/BEFORE_START.json` SHA-256 `d0656cdb61fd970e1a6ae610019b14e37eaa361f56c793e60372f5201536d91a`
- `evidence/executor_p0/DESKTOP_START.json` SHA-256 `2b80e27f4ab294a23e9ef33f79596def3f7356229371dab528c7cd0a7e5ce810`
- `evidence/executor_p0/AFTER_START.json` SHA-256 `016c866d4b7649b37d7845e25a9fc40057aed8715605e215d185681c348f3d8b`
- `evidence/executor_p0/P0_CLOSE.json` 环境分支收口；`ATTEMPT_LEDGER.jsonl` 保存一次启动尝试与其结果。
- 原 `H75` 研究与成本记录、`H74R` 通过结论和旧 `H74` 拒收记录均未改写。

## 冻结AC逐项情况

| AC | Executor证据状态 |
| --- | --- |
| AC-01 基线与权限 | 预检与授权检查通过，但任务未完成，不声明整项通过 |
| AC-02 资产/真实发行 | BLOCKED：Docker Engine不可用 |
| AC-03 UID匹配/不匹配 | NOT_RUN |
| AC-04 同UID签名/原消费 | NOT_RUN |
| AC-05 十项真实来源负例 | NOT_RUN |
| AC-06 必要回归 | 本轮未运行；H75设计阶段回归记录不可冒充本轮L2 |
| AC-07 清理/成本 | 部分证据：一次启动请求；本包未创建容器或密钥，不需删除；整体AC未关闭 |
| AC-08 统一L2及独立L3 | NOT_RUN / NOT_SUBMITTED |

## 成本、权限及仍缺项

本次Docker Desktop启动尝试1次；本包资产文件下载0、镜像pull0、容器启动0、SPIRE Server/Agent启动0、临时测试CA/SVID0、工作负载签名0、真实或测试付款0、正式L2=0/L3=0；没有安装或升级宿主软件，没有提交/推送Git。Docker Engine字节传输未发生，CLI只读元数据调用有可见记录；额外网络/内部进程传输量不可观测时保持UNKNOWN。实际主动分钟UNKNOWN，保留证据时间戳，不伪造用时。

`git diff --check` 综合调用超过30秒被执行通道终止，未取得完整通过结论；已获取的文件SHA与冻结 `CHECK.py preservation` 成功不等于此命令成功。

**确切缺件**：原合同指定的Docker Desktop Linux Engine处于可连接状态。该条件未满足前无法正当地启动P1到P4，更不能进行正式L2或给出能力增益。本轮已耗用允许的Desktop启动尝试；恢复服务需要另一次明确的运行决定/合同处置，不能由Executor私自重复启动或更换平台。项目负责人所要求的独立评估仍留在后续，并未由Executor替代。

## 结构门禁与工作区差异（不冒充提交通过）

追加执行公共 `validate_workflow.py` 返回1：冻结合同被判缺少格式化的 `exclusions`、`stop conditions` 段落（实际合同已有中文范围/停止语义，但结构校验不识别）；本报告还被列出标准化章节/字段 `FIX_IN_PLACE` 提示。本次仍在 `EXECUTING / BLOCKED`，未发L2提交，不以报告文字修补冒充正式门禁成功。合同已经冻结，执行者不擅自改冻结标准或伪造评估者判定。`git diff --check -- CURRENT.md REMOTE_HANDOFF.md` 首轮返回2，提示路由Markdown为CRLF导致整行trailing whitespace；仅规范这两个路由文件的行尾为LF后，独立重跑返回0，未改正文语义。首轮失败与第二次修正结果都如实保留，提交/推送均未执行。

## 追加负责人授权的Docker安全重试与WSL核查（2026-11-16）

在先前INPUT_LIMIT_ENV后，负责人再次明确允许安全地尝试启动已有Docker，并询问WSL是否能充当运行环境。新增授权独立记录为`OWNER_SAFE_RETRY_20261116.md`；原`P0_CLOSE.json`、第一次启动账本与冻结合同均保留。

执行Windows PowerShell `Start-Process` 安全启动原有Docker Desktop **一次**，返回PID 29252 / exit=0；约8秒、16秒后Docker Engine均仍不可达，Windows进程检查也无Desktop/backend。只读诊断发现 `com.docker.service` 为STOPPED、`docker-desktop` WSL发行版Stopped；未尝试系统服务启动、配置变更、WSL发行版启动或安装。累计两次桌面启动请求（每次均有独立负责人授权），容器和SPIRE执行仍0。

现有WSL Ubuntu 24.04.2 LTS（WSL2、x86_64）运行中，`sudo -n`、`setpriv`、OpenSSL、tar、curl基本条件可用，因此**WSL原生SPIRE技术上可行**；但冻结H76要求`docker inspect`、固定镜像、隔离与容器清理，WSL原生不等价，未进行安装或身份签发。完整结果见`SAFE_RETRY_RESULT_20261116.md`与`evidence/executor_p0/safe_retry_20261116/`；该路径包含Windows启动/失败原始命令和WSL服务状态日志。本轮同样保持`INPUT_LIMIT_ENV`，没有新增L2或L3成绩。

**原Docker分支交付**：保留真实环境失败证据和停止点，不追认Docker H76 PASS。

## 后续负责人授权WSL并完成真实签发实验（最新结果）

负责人于2026-11-16T12:45:03Z明确授权使用已有WSL Ubuntu完成真实SPIRE签发及签名认证，并要求把结果写回项目、稍后统一交评估者独立复核。授权原文见`OWNER_WSL_AUTHORIZATION_20261116.md`。本补充实验未更改原Docker合同、冻结验证器或原产品源码/测试。

**WSL替代切片实测结果：成功。** 经官方SHA锁定的SPIRE 1.16.0在WSL2真实启动、生成新根并完成Agent节点身份认证；UID1001按`unix:uid:1001`取得真实X.509-SVID和私钥并在同UID内签名；UID1002连接同一Workload API后真实被`PermissionDenied`拒绝（0 SVID）。既有`verify_x509_svid_credential_possession`直接验证本轮真实证书与签名，得到`VALID`且四项有效性字段为true，所有10项原冻结负例均非VALID；必要回归28+19+9+74=**130项全部通过**。私有tmpfs密钥和本轮SPIRE进程已经清理；原1502文件保护检查再次通过。

完整执行报告：`WSL_EXECUTION_REPORT_20261116.md`；证据Run ID：`d446ee01ee70`，入口：`evidence/wsl_experiment/d446ee01ee70/EVIDENCE_INDEX.json`。两次早期脚本受阻也原样保留，不能覆盖或当成正例。没有金额篡改、生产机构身份或真实支付验证；绝不将“持有凭据”当作“获得支付授权”。

**验收区分**：WSL下的真实发行与原验证器效果已经执行者实测，但没有原合同指定的Docker image/inspect/隔离证据，也没有其正式L2和Evaluator独立L3，因此`CURRENT.md`维持`EXECUTING / Executor`，阶段改为WSL结果就绪、等待评估者决定补充验收口径，**不宣告原H76 PASS**。无需为此重跑已失败的Docker环境分支。
