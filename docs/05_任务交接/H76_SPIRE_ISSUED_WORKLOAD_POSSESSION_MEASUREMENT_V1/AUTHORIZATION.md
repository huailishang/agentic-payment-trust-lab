# H76 项目负责人运行授权（2026-11-16）

授权原话（UTC 2026-11-16T11:59:25Z）：“我现在是项目负责人，现在你直接执行H76吧，然后不需要再经过评估者了。你完成之后，我们再统一找评估者进行评估，这一轮的效果”。

本决定晚于 `OWNER_RUNTIME_DECISION.md` 中“先保留执行包，暂不运行”，仅对 H76 执行启动予以更新；原决定原字节保留。本次无需 Evaluator 事前批准，Executor 完成后由 Evaluator 统一独立审查，Executor 不得自行宣布 PASS。

批准范围严格依据本包 `AUTHORIZATION_REQUEST.md`、`CONTRACT.md`、`ASSET_LOCK.json`、`RUNTIME_PROTOCOL.md` 和 `VALIDATION_PLAN.yaml`：如有必要，仅启动已安装的 Docker Desktop 一次及其自身后端；获取锁定的固定版 SPIRE、固定 Python 镜像与三个哈希锁定的依赖；仅在隔离容器内离线安装依赖，生成一次性测试 CA、join token 和 SVID，在 UID1001 内签名，执行受限正负例、回归与安全清理。不自动安装或升级宿主工具、不手动启动其他 WSL 发行版、不改 Docker 配置、不接触生产密钥/账号、不发生真实或沙箱付款、不进行外部付费 API 请求。不得影响其他容器，严格受合同次数、资源和停止条件约束。

权限：authorization_local_service=true；authorization_artifact_download=true；authorization_container_dependency_install=true；authorization_ephemeral_test_credentials=true。其他 authorization_commit/push/history_rewrite/api_call/install/test_payments/browser_test_only 均保持 false；公开参考读取保持 true。

授权不等于环境/性能/身份安全测试已经通过。必须先核定冻结合同、基线及环境；连接失败、摘要不符、不兼容或零容忍反例按原合同立即停下并保存原始证据，不能换平台/扩大范围。

批准时的技术版本：SPIRE 1.16.0；H76 技术草案的 `FREEZE.json`、合同、资产锁、六项验证计划及 `BASELINE.json` 均须在转为 CONTRACT_FROZEN 前独立核对并记录 SHA-256，随后生成正式冻结摘要。若无法运行，本文件只表示授权记录，不是启动或验收证据。
