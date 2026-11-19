# H76 安全重试与WSL替代环境资格核验（2026-11-16）

结论：`INPUT_LIMIT_ENV` 保持；本次获项目负责人新授权，在不改配置/不升级/不启动系统服务前提下安全再启动已安装Docker Desktop一次，**未成功连通Docker Engine**。Ubuntu WSL2满足SPIRE Linux原生测试的基本系统先决条件，但**与本H76冻结的Docker隔离及验收语义不等价**；本次不自动转路线、不运行SPIRE。

## 新授权
项目负责人新原话及范围：`OWNER_SAFE_RETRY_20261116.md`。前一轮Docker启动尝试及 `evidence/executor_p0/P0_CLOSE.json` 原件保留；本轮是新增、独立、只一次的安全启动授权，不重置旧次数、不修改原冻结合同。

## 实际安全尝试
- 本轮执行前，Docker Windows客户端存在但对应Linux Engine endpoint `npipe:////./pipe/dockerDesktopLinuxEngine` 不可达。
- 使用Windows PowerShell `Start-Process` 启动已有 `C:\Program Files\Docker\Docker\Docker Desktop.exe`：命令 exit=0，打印 PID=29252，**仅表示启动请求成功，并非服务稳定运行**。
- 8秒及约16秒后两次读检查Docker Linux Engine，均失败：不存在 `dockerDesktopLinuxEngine` Windows管道。只读 `tasklist` 没有找到 Docker Desktop / backend 常驻进程。
- 只读查询Windows服务 `com.docker.service`：`STATE=STOPPED`，WIN32_EXIT_CODE=1077；并没有尝试 `sc start` 或修改系统配置。此状态仅为观察事实，不能据此确定真实根因。
- WSL发行版：`Ubuntu Running (2)`，`docker-desktop Stopped (2)`；WSL Ubuntu 24.04.2 LTS，x86_64内核；`sudo -n true` exit=0，`setpriv/openssl/tar/curl` 可用，Ubuntu自身无Docker CLI/socket。没有启动额外WSL发行版或服务。

## 原始证据
- `evidence/executor_p0/safe_retry_20261116/BEFORE.json`、`START.json`、`AFTER_8S.json`、`AFTER_16S.json`
- `evidence/executor_p0/safe_retry_20261116/TASKLIST_DESKTOP.json`、`TASKLIST_BACKEND.json`、`WSL_DISTROS.json`
- `evidence/executor_p0/safe_retry_20261116/SUMMARY.json`（此轮启动1次，合计此前尝试为2次）
- `evidence/executor_p0/safe_retry_20261116/WSL_DIAGNOSTICS.log` SHA-256 `e27274d6cbeed87c4d0695b3d21e70ce51ec29125eab652fd1024429ee992ac4`
- `ATTEMPT_LEDGER.jsonl` 新增本轮事件，旧账本不覆盖。

## WSL原生方案的区别与风险控制
原H76假设是“SPIRE发行+真实UID选择器+持有者签名→现有验证器”，这在Ubuntu WSL2技术上可以实现，**Docker不是SPIRE自身的强制依赖**。如使用已有WSL Ubuntu，SPIRE Server/Agent可以作为独立Linux进程在仅本地地址和任务专属临时目录内运行，两UID的真实Unix身份由`setpriv`和现有sudo控制。需要单独设计只读根、无网络、PID/权限限制、密钥不离开Linux tmpfs、非匹配UID实际RPC拒绝与清理的可审计替代证据。

但是原冻结H76 AC-02/AC-07明确要求`docker inspect`、固定Python容器镜像摘要、无挂载、`--network none`、rootfs只读和本包容器ID清理；WSL原生运行无法满足这些证据项。不得通过修改冻结CHECK、伪造`docker_inspect.json`、把WSL裸跑视为原合同PASS。另需一个经负责人确认的`H76-WSL`替代执行包，沿用现有SPIRE版本/测试假设/十负例，修改隔离与验收定义，并评估WSL共享内核/网络/进程带来的风险。此次只完成环境可行性资格检查，不安装Linux依赖、不签发密钥。

## 消耗与安全边界
额外Docker Desktop启动尝试1次，合计2次（先前1次+当前新授权1次）。未运行Windows系统服务start/stop、WSL其他发行版、Docker daemon、容器、下载或安装；无本包SPIRE证书、临时私钥、付款、L2/L3、Git提交/推送。保持 `EXECUTING / Executor / INPUT_LIMIT_ENV`，未提交验收；Docker Desktop无法稳定运行的具体根因目前未知。
