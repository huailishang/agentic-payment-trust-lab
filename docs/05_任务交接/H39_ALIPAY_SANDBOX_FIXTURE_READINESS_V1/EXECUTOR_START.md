# Executor dispatch — H-39

按 CURRENT.md → CONTRACT.md → VALIDATION_PLAN.yaml 顺序执行。你处理的是 B-06 沙箱 fixture 获取路径测量，不是继续写 adapter，也不是要求 Human 重发密钥。

已有 APPID 与已验证的本地沙箱密钥材料；原 H-38 产品实现和测试保持原样。执行第一步校验 BASELINE.json，然后优先解决 Agent Pay 入口/资格、沙箱买家 UID、可信订单与 proof 获取方式。公开资料可独立研究，不因浏览器失败停止所有工作。

本包禁止创建交易和调用 payment.verify。需要登录或确切账号操作时直接显示对应官方页面；只要求 Human 完成必要操作。无法访问浏览器时明确报告工具问题，给出一个具体操作节点。若仅能走 HTTP cashier / 履约 / 新依赖路径，提交最小合同差异，不执行。

提交 ROUTE_ASSESSMENT.md、READINESS.json、REPORT.md，完成验证计划，然后交 Evaluator。不得 claim H-38 PASS、重跑 live、删除 reservation、提交或推送。不要另建任务或委派子 Agent。
