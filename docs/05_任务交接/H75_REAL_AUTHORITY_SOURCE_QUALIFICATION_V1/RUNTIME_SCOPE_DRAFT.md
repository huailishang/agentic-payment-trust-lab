# 后继运行方案待锁定项

已被H76_SPIRE_ISSUED_WORKLOAD_POSSESSION_MEASUREMENT_V1/CONTRACT.md、RUNTIME_PROTOCOL.md、ASSET_LOCK.json和VALIDATION_PLAN.yaml取代。下文仅为历史草案；完整内容已制定，运行权限仍待负责人最终同意。

状态：DRAFT / NOT_EXECUTABLE。此文使下一次授权与制包讨论具体，不是运行许可，也不是第二套路由。

拟验证范围：一个新鲜测试信任域、一套实际SPIRE Server/Agent、一个选择器匹配的工作负载、一个不匹配对照；已有EC/direct-root SVID验证器。身份事实不得直接当付款授权，所有支付回调保持本地fake。

建议有界依赖链：

1. P0环境：确认现有Docker Linux engine可用；当前未连通。明确是否允许启动既有Docker Desktop，禁止自动安装/升级Docker或启动任意WSL发行版。准备前先固定发行资产/镜像版本、摘要、许可和隔离启动/清理方式。
2. P1发行：新测试CA、join token、工作负载登记与UID/选择器证据。禁用示例dummy CA；不挂生产凭据、Docker host socket或用户目录，不给privileged/host-network，不部署云服务。
3. P2持有与消费：匹配工作负载取实际SVID，内部私钥对已有规范nonce载荷签名；host侧只收公共证书/签名/事实验证。必须说明究竟证明UID、容器还是具体进程，不能超出选择器证据。
4. P3反例：不匹配选择器拒绝签发，错误信任根/Agent/Executor/nonce/签名/过期观测拒绝，nonce重放拒绝；合法控制保留。自动续期/轮换和撤销不在首个代表切片。
5. P4收尾：既有身份/持有证明必要回归，公共L2、独立L3、原始日志/证书指纹/注册配置/进程归属/成本；清除本包容器和私有临时密钥，原项目/其它容器不动。

预算草案：单方案，预计2–3小时量级；必须在环境/资产锁定后给出Executor/Evaluator、下载字节、API/CLI次数、服务最大存活时长、2实现/2L2/1L3及停止条件。当前不发放该预算。

冻结前必须闭合：

- 现有Docker engine启动的明确权限与所选本地endpoint；失败则INPUT_LIMIT，不自动换云或其它平台。
- 发行包/容器镜像及签名工具链可复核的固定来源/摘要/许可；不允许执行floating latest或在线脚本。
- 新鲜根与bundle的固定来源、实际证书profile、private key不出持有者边界的具体签名步骤。
- 六项以上原始可观察证据、独立负例与cleanup路径，以及完整Validation Plan。

在上述内容可审阅且获得实际运行权限前，CURRENT保持Evaluator/DRAFT。无需再做一轮本地合成身份或泛化框架研究来填补这些前置。
