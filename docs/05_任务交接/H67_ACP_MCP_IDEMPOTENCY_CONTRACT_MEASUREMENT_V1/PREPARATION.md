# H67来源准备与选择理由

日期：2026-11-10；责任人：Evaluator（评估者）。本文件是冻结前准备，不是执行者测量结果。

H66资格研究通过但未证明具体金融消费者，因此停止IronClaw接入。评估者比较既有代表证据与公开线索，选定ACP官方[#295](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol/issues/295)：工具绑定是否把REST必填幂等键变成可选。该问题在本次观察时open，2026-08-10创建；问题单是线索，不是服务器重复扣款证明。

评估者通过只读git ls-remote取得官方HEAD `7fdd78df677a94dce04c770644b0fbbb1401272b`，再用GitHub连接器读取5个固定完整文件：规范、MCP说明、OpenRPC、示例和LICENSE。全部正文Git blob复算与官方值一致；SOURCE_BUNDLE记录来源链接、blob及全文SHA-256，冻结必要行/JSON投影；原完整副本保留本地准备evidence，Apache-2.0许可证随包保存。原文未修改，公开投影不含域payload或支付数据。

规范第236–253行限定所有POST结账变更请求的幂等键；MCP映射表给出5工具及HTTP操作，meta表与机器meta schema另列其要求。准备只定位和冻结这些输入，未生成正式10探针/5示例测量结果，也未执行上游或产品。机器描述标记unreleased，不能当已发布生产服务行为。

次选[UCP samples #277](https://github.com/Universal-Commerce-Protocol/samples/issues/277)报告悬空履约行引用造成不同运费/总价，并附样例复现；本轮未独立运行。其问题更偏业务引用/报价正确性，且需要运行环境；ACP键要求关系更直接对应零容忍重扣风险，先做低成本离线契约测量。两类公开线索都不等于已证明客户需求或付费价值。

本次Evaluator外部准备与H66 Executor预算分开；H67 Executor新GET/安装0，只使用公开冻结包。既有H65R拒收与H66原始提交/L2/L3不回写。后续只按SOURCE_BUNDLE固定版本作矩阵，不因另有版本更新而替换输入。
