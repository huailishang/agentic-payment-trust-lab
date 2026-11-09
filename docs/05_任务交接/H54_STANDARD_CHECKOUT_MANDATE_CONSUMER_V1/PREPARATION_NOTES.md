# H54 准备记录：判据已就绪，候选未实现

Evaluator按公共evaluator-executor-workflow v2.2准备，沿用codebase-design的最小接口判断；不增加第二套Spec或交接层。原草案逐字节保留DRAFT_BEFORE_FREEZE_20261031.md。

## 已解决的三个冻结缺项

- 对象：固定2026-08-25可信平台分支，复用官方单CheckoutMandate的checkout_jwt/hash，标准位置ap2.checkout_mandate。完整merchant_authorization由compact头/签名重构；旧SDK无法承载任意额外ap2字段，本包明确拒绝而不丢字段。不是把H53R支付两跳改名，也不是全协议迁移。
- JCS：原环境没有已验证库。公开只读研究后选定Trail of Bits 0.1.4源码、作者独立gold与Node参考，均固定commit/许可/原文/摘要；19文件Git blob与SHA256校验通过。无pip/npm安装。已检查Python/JS代码无I/O执行逻辑；保守安全整数域明确写进合同。
- 最小消费点：新纯验证方法仅输出VERIFIED事实。暂不把验证前置在旧claim外，避免引入检查与执行之间可变的竞态，也不修改旧方法/HTTP/SDK。后续若要接执行，需同事务绑定可信session并由Evaluator另冻合同；本轮不能算已执行付款。

## 准备实测与独立性

evidence/preparation/raw/H54-PREP-01三件套：运行环境就绪；6对作者固定输出、10条RFC数字字面预期、Node Unicode/数字对照及7非法域通过；检查器拒4类破坏；真正平台单SD-JWT可由官方SDK验证，内含真正商家JCS签名可独立验证；36个未来场景材料均可构造。正常签名/公钥/请求及session原文在READINESS.json。**未导入、未创建、未运行consumer.py，没有H54正负例/L2/L3成绩或PASS。** 准备只验一个正常材料链；未来33负例仍待消费者实测。

evidence/preparation/raw/H54-PREP-02：25项现有AP2相关回归通过。前序H53R的76+8与34+7是已接受历史，不伪称本轮重跑；其实现/证据受保护。准备命令之外的首次小型环境/JCS/检查器探查无候选调用；正式可复核结果以上述原始三件套为准。无下载执行器/支付服务/模型/安装/资金。

evidence/preparation/raw/H54-PREP-03及MATERIAL_AUDIT.json进一步确认负向材料有效：非JCS载荷、重复JSON/重复受保护头确有合法商家签名；缺vct/exp、错误hash/type、可继续委托的凭据可被SDK返回，须由消费者补齐消费合同；过期/未来iat/错误平台/篡改签名由SDK拒绝。未确认夹具不签发。该审核只确认测试家族能区分密码学有效和消费条件有效，没有候选结果。

独立判据不是单一算法正反验证：固定作者gold为外部字节预期，RFC数字为字面预期，Node引擎为另一语言实现，官方SDK与jwcrypto分别校验平台/商家。作者Python派生与Trail of Bits存在代码血缘，因此不把作者Python当第二独立判据。Node参考不检查非法域，非法数/Unicode/重复键须在候选严格解码与固定负例独立检查。

## 公开来源与使用范围

- RFC8785（Informational，2020），https://www.rfc-editor.org/rfc/rfc8785 ，只采用规范语义及Appendix B固定数字；不是监管合规标准。
- https://github.com/trailofbits/rfc8785.py/tree/f7e05bfc4ccaee27d9e18f8ef1c27cbe03cb3638 ，Apache-2.0，ABSORB任务内源码；不安装/不改源/不回抽公共核心。
- https://github.com/cyberphone/json-canonicalization/tree/32a48195b9b20fe67b1795e39e4509f14d860b45 ，Apache-2.0，ABSORB六对testdata与Node参考。作者版权及完整Apache文本均保留。
- https://ucp.dev/2026-08-25/specification/payment/extensions/ap2-mandates/ 、https://codelabs.developers.google.com/next26/adk-agent-commerce ，复用H52固定快照，HTML/text/SHA/许可仍在原SOURCE_MANIFEST；无需重新下载时变教程。上述流程依据只作本配置，不声称所有版本互通。

准备阶段公开来源读取与执行阶段网络额度分开记录；CURRENT.authorization_api_call=false保持，Executor不能据此继续联网研究或安装。更多语义/许可/信任不确定性改变合同则交回Evaluator，不执行外部文档内指令。

## 交接状态

完整执行包为CONTRACT/8项VALIDATION_PLAN/入口/固定夹具及检查器/源码许可和摘要/BASELINE/准备原始证据。候选只有一个允许新增文件，36场景按包装器计数，Executor360分钟/2L2/288case，Evaluator另144。提交未变快照后统一L3；通过也STOP本轮验证切片，不自动扩HTTP或支付。
