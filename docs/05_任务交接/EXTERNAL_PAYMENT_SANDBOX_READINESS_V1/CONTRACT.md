# 外部支付沙箱最小接入草案

Task ID: EXTERNAL_PAYMENT_SANDBOX_READINESS_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: evaluator_design
Contract state: DRAFT_CONTRACT
Owner: Evaluator
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-11-r110
Active bottleneck: B-21
Hypothesis: SANDBOX-01

## 唯一目标与当前结果

形成一份可授权、可判定的外部支付沙箱接入合同，优先验证本仓执行前治理及响应丢失后的原付款恢复。首轮公开研究已完成，见 `docs/02_未来规划/外部沙箱与测试网络首轮筛选_20261111.md`。优先候选为 Stripe 匿名隔离沙箱；本草案不派发新的静态协议侦查任务。

H67 按 Human 决定延期且未执行，不是验收通过/失败；六类攻击及批量案例扩展暂停派发。本包不得恢复 H67 或旧测试网、支付宝权限。

## 为什么暂不冻结

仍缺三个具体条件：

1. Human 是否允许一次隔离沙箱创建、取得并本地保存临时测试密钥，以及后续有界测试 API 调用。
2. 匿名创建使用哪个经 Human 指定的邮箱；不得读取或外传 Git 邮箱/姓名作为默认答案。
3. 是否允许下载/使用指定 CLI、隔离配置与本地接线；尚无固定可执行 Validation Plan（验证计划），不能把本草案交给 Executor。

本轮“搜索一轮”已被授权并完成，不因上述缺项继续搜索或实施。下一产物为 `AUTHORIZATION_DECISION.md`，仅在收到新决定后填写；不预填同意，不创建空白报告或伪造 L2/L3。

## 候选执行边界，待授权与冻结

- 一份隔离测试环境、一个固定商户上下文、一个本地数字资源；正常与付款响应丢失恢复两个功能情形。
- 官方 Stripe CLI v1.55.10 候选；Windows x86_64 发行包及摘要已在研究中定位，但未下载/执行。实际宿主匹配及依赖版本必须写入最终计划。
- 外部创建候选仅 `https://ai.stripe.com/keys/challenge`、`/keys/provision`；付款侧候选仅 `https://api.stripe.com/v1/payment_intents` 的创建、确认、按 ID 查询及隔离环境内付款/收款清点。端点来源已核，不是当前调用许可。
- 创建失败停止，不跟随正式登录/认领回退，不自动换平台，不安装 Agent 插件或修改全局工具设置。
- 独立 CLI 配置，测试密钥、认领链接及邮箱不进入仓库/公开日志；完整创建输出不得由工具回显。只保存最小去敏证据和必要本地凭据，不接触已有正式账户配置。
- 建议60分钟、一次创建、最多20次 API 请求、至多两笔不同业务操作的测试付款；每笔合成 USD 1.00、总计 USD 2.00，为沙箱账面值；真实资金0。失败也计数。
- 原付款未知时先查询；持久保存业务操作到原付款对象与幂等键的关联，不以新对象绕过恢复。发现同业务第二笔付款即停止并记失败。
- 同一官方组件、同一保护配置下比较接入前后；官方机制已解决问题时不宣称本仓新增安全能力。

## 后续冻结时必须明确的验收

- AC-01：所有对象属于隔离测试环境，真实模式关闭；无真实卡、真实资金、已有账户或跨商户操作。
- AC-02：本仓批准的金额/币种/商户上下文/资源与实际外部请求相符；裁决发生在创建或确认副作用之前，外部对象可回查。
- AC-03：付款响应丢失后查询原付款和收款对象，同一业务操作无第二笔付款；对象清点范围、时间与读取限额可复核。
- AC-04：实收内容与预先固定的内容判据对应；付款、交付和任务完成分别判定；自有服务不算第三方采用。
- AC-05：保留成功与失败、API 消耗及官方原有保护对照；公开证据无凭据；没有观测到的维度保持未知。

这些是冻结前设计要求，未形成已执行 AC 或可运行门禁。允许文件当前仅本草案、研究说明、人工决定与治理记录；产品实现及正式测试计划在新权限明确前不变。

## 当前权限与停止条件

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

公开资料阅读不等于沙箱 API 操作授权。无明确邮箱或运行权限、需正式登录/生产配置、需扩大端点/金额/预算、凭据无法安全隔离时均不执行。PayPal/x402 仅候选，切换须重新说明资格及权限；钱包/签名/领币权限仍无。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/07/09/11/12/18/20；适用性=环境资格与未来CORE/ADAPTER接缝；本轮产品成熟度不变，代码/Test/运行Evidence未新增；真实身份、强认证、资金和合规未证明。

## 历史保持

原 CURRENT 完整字节保存在 `references/PRIOR_CURRENT.md`，SHA-256=`0052f76e7932d1342cd137004c985d5fd75eb2f324493909012102f48b553606`。原 r109 逐字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261110_r109.md`，SHA-256=`da842128dfa0d897891934dd736ac57382b64de194fdba36b669a1f5474ead1c`。H67 原九份文件不改写；不在新路由重跑其全工作区保护检查器。

## 本轮治理核验

2026-11-11运行公共 `scripts/validate_workflow.py --repo . --current CURRENT.md`，exit=0，输出 `OK: v2.2 routing and required artifacts are structurally valid`。`git diff --check`无空白错误；H67九文件与归档前摘要相同，r109及原CURRENT归档摘要复核一致。实际已跟踪差异仅CURRENT、REMOTE_HANDOFF和地图，新增文件为研究、草案及历史归档；产品src/tests未改。此为治理结构检查，不是L2/L3或产品通过；未提交推送。
