# 来源与测量设计决策

Date: 2026-11-08
Status: EVALUATOR_PREPARATION_ONLY（仅评估者准备）

## 依据

H63/H63R只测六个JSONL预览，已签收修复并停止该视图。它们不能说明完整数据集是否有足够材料。发布SCHEMA明确列messages/turns/wire与final_state，GitHub回放说明要求发布world环境，且以事件链/最终状态摘要比对复现。H64新增视图为跨表+world+静态实现来源，**不重复旧六条七类事实制表**。

Hugging Face连接器本轮元数据可用；两次“结构”调用仍只返回摘要，所以实际固定来源使用匿名公开HTTP读取，留有URL/响应摘要/字节记录。GitHub解析commit `61f05faadc64badedd0ca727778ea5c9cd384702`；数据沿用固定revision `86cab5e539e161e0915d78d8abdd9023f09b411e`。FREEZE prepare额外用Git blob SHA验证已保存代码属于该commit。准备未查看任何新episode正文或结果，未运行回放/源测试，也未安装解码依赖。

代码提示本轮必须严守的边界：dataset.py对缺source_call_id的记录可以按前一调用猜关联，本包不接受这种推断；worlds.py解释发布脱敏和域名替换，本包不能伪称原始环境hash重新验过；replay.py比较state/events，证明复现而非安全；payments.py有金额约束，不能把上游原生保护算作本仓新增价值。这些都是准备阶段已知项，后续不得将再次发现写成任务增量。

## 备选比较

| 方向 | 决策 | 理由 |
| --- | --- | --- |
| 固定完整表/world/静态代码资格测量 | REFERENCE_ONLY（只参考），选中 | 有明确新证据视图和可判定的单一金额规则，低于安装整套运行时成本 |
| 继续H63六预览 | STOP（停止），保持 | 已知调用关系边际收益低，不能冒充新源 |
| 直接装CartTrace并跑回放/本仓对照 | DEFER（后置） | 数据/判定路径未验证，源环境依赖广，本包不予安装或执行 |
| APort/Gordon受限来源、真实PSP/消费者 | 不新增执行 | 申请/身份分享/真实服务权限不在范围，价值和取得条件未就绪 |

## 独立性与真实性

来源独立不等于现实支付。商品来源开放目录，用户、价格、库存、钱包和PSP均为模拟；源模型单一，评分未由人工标签校验。数据CC BY 4.0，商品沿来源许可；代码Apache-2.0及NOTICE，vendored协议另有条件。保留署名，不训练、不公开分发、不导入产品。接触真实敏感资料疑点即停。

确认必须来自执行前用户明确原文；hidden_spec与上游评分不提供付款权力。工具/协议返回、已发布初始世界、最终摘要、实际状态事件和静态读取路径分级。即便现有材料足以比较轨迹金额，下一步也只能先验证回放基线，不能直接宣布控制效果或生产成熟度。

## 已知依赖与成本

既有H47解释器没有pyarrow/pandas/datasets/duckdb；系统Python有pandas与pip，但没有Parquet解码器。首次pip show从H47运行因无pip失败，未安装任何包；后核实系统现有pip可用。H64只允许固定PyArrow 26.0.0 CPython3.12 win_amd64 wheel在任务隔离target内一次安装，元数据requires_dist=null、wheel约28.6MB，禁止上游环境及传递依赖安装。平台/加载不符要记工具限制，不以改版本绕过。

准备GET与响应字节以PREPARATION.json/READINESS.json为准；连接器元数据调用2次另计。执行预算独立从0开始，不将准备网络记成0，也不执行正式L2冒充已有成绩。
