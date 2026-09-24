# Executor dispatch — H-40

读取 CURRENT.md → CONTRACT.md → VALIDATION_PLAN.yaml → BASELINE.json。只修 H38 探针的 R4，先核对 hash。H39 REVIEW 是最新结论，不重做路线研究，不索要密钥或人工付款。

从实际 probe 入口用临时文件和 fake transport 测试错任务、无授权、伪造正文、重复字段与中途撤销；拒绝必须在 key inspect/signing/reservation/network 前。合法模拟授权保留原护栏，不增加运行时绕过参数。

完成专项/回归后写 REPORT.md（AC 证据、命令/退出码、hash、剩余阻塞），交 Evaluator L3。不得切 CURRENT 回 H38，不 live，不删除 reservation，不 commit/push，不创建任务或委派子 Agent。

下一阶段由 Evaluator 冻结 Route A 最小获取合同；无安全路径时给出 STOP/缩窄测量决定，不再泛泛要求补 fixture。
