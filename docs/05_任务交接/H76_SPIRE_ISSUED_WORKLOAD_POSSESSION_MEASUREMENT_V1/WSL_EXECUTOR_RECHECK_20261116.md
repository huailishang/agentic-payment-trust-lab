# H76 WSL 实验执行者复核记录（2026-11-16）

**性质：对已留存真实 SPIRE 实验进行独立的执行者复算及回归复跑。不是新增身份签发，也不是评估者 L3 签收。**

## 复核对象

- 原实测 Run ID：`d446ee01ee70`
- 入口：`evidence/wsl_experiment/d446ee01ee70/`
- 原实验报告：`WSL_EXECUTION_REPORT_20261116.md`
- 本次追加证据：`evidence/wsl_executor_recheck_20261116/RECHECK.json`、`identity.stderr.log`、`stripe_guard.stderr.log`、`preservation.log`。
- 负责人授权：`OWNER_WSL_AUTHORIZATION_20261116.md`。原 Docker 合同、冻结 CHECK、验证计划保持原样。

## 已实际执行的复查

1. 对 `EVIDENCE_INDEX.json` 列出的 **20 个公共证据文件**逐项重新计算 SHA-256：全部一致，差异 0。
2. 用未改动的 `WSL_VERIFY.py` 再次解析**原本真实发行的SPIRE根和叶证书**、对公开挑战/签名做ECDSA验签，并调用项目的 `verify_x509_svid_credential_possession`。返回 `VALID`，credential/subject/possession/freshness 四项 `true`；同一实际正例派生的 **10/10 负例全部拒绝**。复算前后 `WSL_VERIFICATION.json` 的 SHA-256 相同（`59e5aebec9ac5d4e41059a66b5ea2d0aad7c3b8cc8f9cc7a89ffdd88ffe2f28a`）。
3. 再次逐字节校验WSL缓存官方 `spire-1.16.0-linux-amd64-musl.tar.gz`：SHA-256 `7bcf5e167151a1fc58293768462b44e155ba8784214582aefa6adf18c633d1d5` 与原锁定值一致。
4. 单独重跑原项目回归：凭据/身份/Stripe上下文 **28/28**，H74受控Stripe **19/19**、安全守护 **9/9**、业务守护 **74/74**，合计 **130/130 PASS**。由WSL Python运行，未修改项目源码或原测试。
5. 用Windows Conda `agent` Python运行冻结 `CHECK.py preservation`：1502个基线受保护文件以及任务授权与冻结一致，PASS；原路由文件的 `git diff --check` 返回0。
6. 对公开实验目录扫描无 `PRIVATE KEY-----` 私钥标记，并复查无活动 `spire-server` / `spire-agent` 进程或本任务 `/dev/shm/h76w*` 临时目录。

## 独立观察与来源边界

- 原 `matching.stdout.log` 表明UID1001真实获得唯一目标SVID；`nonmatching.stderr.log` 明确出现 `rpc error: code = PermissionDenied desc = no identity issued`。这不是单纯文件读取失败。
- 证书/签名/原验证器/负例测试的密码学事实可从公开材料独立复算；SPIRE issuer、Agent接入、UID与临时密钥边界本身仍需评估者检查实现和原始日志，并用**新鲜根/nonce**独立重演。
- 原 H76 冻结的Docker镜像digest、独立命名空间、`docker inspect`、容器回收等AC并未通过WSL实测满足，不得将这次复核冒充原合同正式L2或Evaluator L3。
- 原实验包含2次技术失败和1次成功发行，失败证据保留。本次**没有再启动SPIRE、生成新测试密钥、付款、安装软件或Git提交/推送**。

## 结论与交接

**执行者结果：WSL实际发行身份 + UID1001私钥持有签名 + UID1002身份拒绝 + 原支付验证器VALID + 十个负例 + 130项回归，复核通过。**

**仍未完成：原Docker H76正式L2、评估者独立新根/nonce L3以及评估者对WSL替代验收口径的书面决定。** 当前仓库路由保留 `EXECUTING / Executor`，不擅自改 `PASS` 或 `READY_FOR_REVIEW`。建议评估者评估时先核认可比较的WSL技术事实与Docker隔离要求间的差异，再在新鲜环境里独立复演，不借用本次私钥。
