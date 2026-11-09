# H63 来源选择与准备边界

Date: 2026-11-07
Status: PREPARATION_ONLY；无新产品适用性或安全成绩

复用H46/H52已有审查，不重测银行片段的完整入口语义缺口或官方签名材料。H62已停止本地恢复切片；缺独立交易轨迹，触发仓库外部Benchmark（基准集）检查规则。

| 来源 | 分类 | 依据与处置 |
| --- | --- | --- |
| [CartTrace-100k](https://huggingface.co/datasets/generalmachines/CartTrace-100k) | REFERENCE_ONLY（只参考） | 固定revision=86cab5e539e161e0915d78d8abdd9023f09b411e。CC BY 4.0；商品/模型输出沿用来源条件。模拟商家/用户/付款，只读六预览，不训练、不执行工具 |
| [APort Vault](https://huggingface.co/datasets/aporthq/vault-benchmark-v1/tree/main) | REFERENCE_ONLY（只参考） | 文件访问须申请并分享账号信息，模型输出另有条款；未申请/下载受限文件 |
| [Gordon AgentCommerceBench](https://huggingface.co/datasets/withgordon/agentcommercebench) | REFERENCE_ONLY（只参考） | 受限访问且声明生产来源会话；未申请，不导入生产会话或执行链/支付服务 |
| [ModelScope ACEBench](https://modelscope.cn/datasets/evalscope/acebench) | REFERENCE_ONLY（只参考） | 工具使用任务线索，不足以替代授权/付款绑定证据，不展开 |

选CartTrace因为来源独立、输入公开、交易对象相邻、标准库可读，不因上游分数高。六预览只有session/message，缺独立后端表是已知边界。本任务的新问题是能否定位有限的授权/确认/绑定观察，以及这些观察有什么证据上限；不重测“有无后端表”。

准备预算16 GET/16MB/单文件2.5MB。实际10 GET、727832字节；公开网页检索另计，不是零网络。首次元数据筛选误用.json后缀，只得零文件；修正.jsonl后，按前六类别各首路径取样，未按结果选样。响应hash及路径见PREPARATION.json。没有执行下载代码、安装或调用模型。

Hugging Face连接器调用一次返回UNAVAILABLE（不可用）；改用公开网页及匿名只读下载，无账号/凭据/付费/申请。后续Executor全离线，不把本次公开源研究解释成authorization_api_call=true。六预览已做结构检查，不得当新鲜未见留出集；不能用会话中的攻击指令改变本任务或工具权限。

## Attribution / 署名与许可

CartTrace-100k，Pratham Bhatnagar、Deepanshu Pal，General Machines，2026。六份JSONL按上述固定revision原样保存，未改内容。数据CC BY 4.0：https://creativecommons.org/licenses/by/4.0/ 。README、SCHEMA及NOTICE随附；商品来源许可和模型输出条件继续适用。仅本地只读防御评测，不训练、不公开重新分发。许可/隐私疑点出现即停交Evaluator。
