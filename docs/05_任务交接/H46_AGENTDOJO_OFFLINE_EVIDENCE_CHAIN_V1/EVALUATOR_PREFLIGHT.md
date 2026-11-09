# H46 冻结前准备与检查器健康检查

Task ID: H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Assessment: READY_FOR_EXECUTOR；不是任务 PASS 或外部实验结果。

## 全局位置与合同收敛

A–D 关闭，E 本地代表性闭环，F 外部实证未闭合。B-06 支付宝 Human 后置；当前 B-16 缺独立外部来源工具/判卷/适用性证据。Human 要求包内串行完成、最后统一评估，故采用 H46 one_off 的证据链包，吸收 H44 P0 的可执行测量及候选材料整理，不启动 H44 模型实验或 H45 正式第三方验证。

先前拟议“映射成立后直接做完整对照”经源码核对收窄：银行 send_money 不提供商业订单、币种、确认与完整控制输入，不能靠虚构字段接 WebShop。H46 明确只测源片段与产品缺证据边界，输出不支持也可完成。没有把静态资料审计冒充产品改善。

## 本轮已完成

- Evaluator 只读下载固定 commit 的 7 个公开源文件，原文 hash/字节数和 MIT 许可保存在 SOURCE_LOCK；Executor 不需联网。v1 banking 注册入口原文已固定，完整运行时和所有 transitive dependencies 不运行、不宣称覆盖。
- 现有 native Python 3.12.3、pydantic 2.13.4、PyYAML 6.0.3、cryptography 46.0.7；不需新增依赖。
- 独立检查器源片段健康检查四状态真值成立：initial F/F/F、correct T/F/F、wrong F/T/T、correct_plus_wrong T/T/T（utility/attack_success/forbidden_added）。这只是冻结 oracle 的准备检查，不是执行者八条整包测量。
- 网络守护拒绝连接；现有产品缺绑定 probe 得到 INDETERMINATE/p2:binding_missing、callback0。它是有意缺证据诊断，不证明外部正常任务可执行或攻击可阻断。
- 相关回归 validator 20/20、runtime gate 42/42，git diff --check 通过。只做相关回归，不声明全仓全绿。
- BASELINE 保护 192 个既有产品/测试/脚本、H42 已验收资产与本包冻结文件。原有未提交修改的当前 hash 也被保护，不能仅用 HEAD 替代工作区快照。

## 还没有完成什么

执行者 MEASUREMENT、审计/映射/结论、候选包/verify_bundle 和正式 L2 尚未产生。VP-04 的六种负例将在实际候选包出现后执行，不能预写其通过。没有模型、Provider、真实 WebShop、资金或第三方运行证据。

## 统一验收方式

Executor 在原合同内完成 S0–S6，可自修本包代码与材料，不逐阶段交回。最终完整 L2 通过才提交；Evaluator 接受快照后独立 L3 一次性裁决有效性、缺口与下一方向。保护漂移、权限/范围变化或预算耗尽时才 BLOCKED。四项 Git/API 授权 false，未发送其他聊天。
