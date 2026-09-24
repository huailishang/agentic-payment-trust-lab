# H-41 Executor 入口

读取 CURRENT → EVALUATOR_DECISION → CONTRACT → VALIDATION_PLAN → BASELINE；先验证保护 hash。

本包大白话：先做好一个安全的小探针，之后最多问支付宝沙箱一次“这组明确合成的交易号/凭证能不能验证”，观察错误响应能否验签。没有造单，没有人工付款，也不证明支付成功。

**现在只执行 P0 离线准备。** 新增合同限定探针与测试，用 fake transport 和合成 RSA 密钥证明授权、单次预留、错误分类和脱敏。不要运行官方脚本、拿真实密钥、联网试接口、恢复 H38、泛搜其他路线或扩通用框架。

提交 REPORT.md，逐项列 AC、命令/退出码、实现 hash、结果与限制，状态 OFFLINE_READY_FOR_REVIEW。既有 H40/H38 代码与独立检查器保持不动。不改 CURRENT、地图或合同，不 commit/push，不委派。

Evaluator L3 通过且切换 CURRENT 后才进入本合同 P1，最多一次请求，不因报错再跑。届时复用既有授权密钥位置；上下文缺失只问路径、不索要正文。P0 不需要 Human 提供任何新材料。
