<!-- Public display copy; original SHA-256: b6aa1a9ac3c5a8d1693cee795b3349edb78680969e6929385f84187ddf2bf8b2; only trailing whitespace/line endings normalized. -->

# H63 执行报告：六样本来源资格测量及最小验证器兼容修复

Task ID: H63_EXTERNAL_TRACE_QUALIFICATION_V1
Task kind: one_off
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: SUBMITTED_FOR_REVIEW
Authorization: commit=false, push=false, history_rewrite=false, api_call=false

## Global position / 全局位置

H62 已经评估者独立签收并STOP，H63 对B-18做**外部来源能提供哪些有限合同输入**的资料资格测量；不是支付产品改造、真实PSP服务接入、安全提升评测、消费者结算或生产部署。六份固定 CartTrace-100k 仅为已见模拟数据，不能当未见留出集；最终分类保持 **REFERENCE_ONLY / TRANSCRIPT_ONLY**。

本次一次完整六样本观察形成**一个后续只读比较问题**，并且经用户明确授权，自主修复与原始源格式不兼容的冻结验证器小错误。**源事实和原AC不变，但原合同禁止改CHECK/INPUTS；该两文件变更属于单独明示偏差，需要Evaluator独立认可并重冻结，不把自改验证器当作独立验证。**

## Workspace snapshot / 工作区快照

Changed files / 改动文件：
- 合同内正常产物：`EXTRACT.py`（仅Python标准库/仅六冻结JSONL）、`MEASUREMENT.json`（六例七类事实/P1–P5/决策）、`ATTEMPT_LEDGER.json`（每例前持久预留）、`REPORT.md`、`evidence/`（原始运行与审计）。
- 用户明确授权的小范围例外：`CHECK.py` 匹配真实 `toolCalls`，只允许识别明确的支付函数并补正/负自测；`INPUTS.json` 仅同步该一份冻结hash。旧两文件完整保存在 `evidence/executor_harness_compat_20261107/CHECK_BEFORE.py` 和 `INPUTS_BEFORE.json`，差异及 SHA 台账见 `COMPAT_AUDIT.json`，原则/余留见 `REPAIR_DECISION.md`。
- `CURRENT.md` 仅把本任务state/phase设置为EXECUTING，提交给评估者复核；未改H62、其他父任务、地图、冻结六源、BASELINE、合同、SPEC、VALIDATION_PLAN、src/tests/SDK或任何支付产品。
- 本地 `CHECK.py source` 的保护检查：H62文件1154、其它保护1719、冻结23、原始数据库3保持；**注意该检查是在用户授权后修订过的CHECK/manifest上运行**，评估者须检查旧/新hash例外。

Deviations and unresolved items / 偏差与未解决项：
- 原始冻结 `CHECK.py` 第97–98行按 `tool_calls` 取值，但源 JSONL 使用 `toolCalls`；旧检查会误拒S06原第29行 `pay` 的真实付款工具调用。执行者没有通过将其标成ABSENT或改源数据来绕过；保留证据并更正检查字段。
- 更正后的调用限定 `pay`、`request_payment`、`shop_pay_payment_request`；钱包读取 `load_payment_data` 和 `complete_checkout` 不冒充直接钱包支付请求。S02有订单工具结果但无直接付款调用的判定只用于**这份预览的直接调用口径**，不代表真实未付款。
- 该例外与原冻结字节条件冲突，**尚未获得Evaluator独立重冻结**。本次正式L2是“执行者修复后的验证器L2 PASS”，绝不表示原始未改冻结器已通过、Evaluator独立L3已通过，或支付产品获得任何新成熟度。
- 用户身份与授权委托、资金提供方真实状态、实际订单/库存后端状态、完整价税签名、可推广抽样、商业客户价值均缺；只有模拟工具返回。未运行额外网络/Provider/模型/产品，不安装，不提交/推送。

## Impact comparison / 影响对比

Measurement evidence: `MEASUREMENT.json` 原源行号/JSON Pointer/值SHA及 `evidence/l2_executor_01/L2-GATE.json` 的四VP；语义证据参照下表。
Before: 外部购物轨迹的支付/确认/订单字段适用性未知，冻结checker错误拒绝真实 `toolCalls`。
After: 六份固定来源中两份显示可按原生call id与checkout id串起的付款相关**轨迹**，另一份有钱包数据及订单但缺直接付款调用，三份只有购物/结账早期内容。
Delta: 新增六份可回指的来源资格结论和一个有界只读比较问题；**产品控制提升=未测量**，用户/PSP/商家事实均未独立认证。
Guardrail result: 本次 `CHECK.py source/measurement/decision/final` 均PASS；正式四VP 4/4 PASS，零新增外网/支付/模型/产品调用，保护材料未发现漂移；变更原冻结CHECK/INPUTS的治理偏差必须由Evaluator单独接受。
Scope caveat: 只评固定已见六条，非产品攻击评测、外部真实商家、未见测试集或生产安全证明。

## 六样本语义结论

| 样本 | 用户确认 | 直接付款工具调用 | 付款工具结果 | 独立订单工具结果 | 调用/结账/订单关联 | 主要界限 |
| --- | --- | --- | --- | --- | --- | --- |
| S01 乐器 | 无明确价格确认 | ABSENT | ABSENT | ABSENT | ABSENT | 有checkout工具返回，后续支付未见 |
| S02 汽配 | PRESENT，原40行 | ABSENT | AMBIGUOUS（仅wallet-data），原42行 | PRESENT，原46行 | AMBIGUOUS | `complete_checkout`和订单可见，但未找到独立直接`pay`调用 |
| S03 童装/家居 | PRESENT，原28行 | PRESENT，`shop_pay_payment_request`原29行 | PRESENT（令牌，原30行） | PRESENT，原34行 | PRESENT（仅轨迹） | 钱包令牌不是清算凭证 |
| S04 钱包 | AMBIGUOUS，原17行仅同意商品 | ABSENT | ABSENT | ABSENT | ABSENT | 仅建购物车，不是付款确认 |
| S05 图书 | ABSENT，选书不等于下单授权 | ABSENT | ABSENT | ABSENT | ABSENT | 仅购物车，没有付款 |
| S06 服饰 | PRESENT，原26行`$25.42` | PRESENT，`request_payment`原23行及`pay`原29行 | PRESENT（模拟收据，原30行） | PRESENT，原32行 | PRESENT（仅轨迹） | 用户确认发生在支付请求/挑战之后、实际pay之前；不能外推真实授权强度 |

上述每项 `PRESENT` 均在 `MEASUREMENT.json` 记录实际源**行号+JSON pointer+值SHA256**；工具调用与结果逐一按源的 `id/toolCallId` 关联，不借相邻消息猜测。数据集的`grounded_success`、assistant解释、隐藏任务信息不作为用户授权。

P1–P5分别按局部可观察输入处理：P1只观察用户原文，不代表强身份；P2区分下单确认与选品意愿；P3检查checkout/支付调用的轨迹绑定；P4检查付款工具调用及其回复而非真PSP付款；P5观察订单工具结果而非独立订单库。对应每样本完整映射及缺失原因已落 `MEASUREMENT.json`，不存在宣称所有P项完全证实的情况。

## 唯一建议下轮问题 / 决策

**`BOUNDED_READONLY_COMPARISON_CANDIDATE`**，源级 **`REFERENCE_ONLY`**。下轮如由Evaluator另冻，建议只问：

> 对 S03/S06，能否不使用助手自然语言成功声明，而仅用用户原文价格确认、checkout ID/金额、明确付款工具调用及其精确关联的结果、get_order身份构建可复算的只读链？对 S02仅出现wallet-data/complete_checkout的路径应如何保守降级？

这是待测试的有限比较问题，不声称有安全漏洞、模型表现提升或商业可推广结论。备选STOP：若Evalu-ator认为S03/S06链仍不足以支持这个窄问题，则停止此预览视图，不新增来源/适配器。

## 预算与保护边界

- 六个样本提取预留均由 `EXTRACT.py` 在读该样本**之前**写入 `ATTEMPT_LEDGER.json` 并在完成后标 `SUCCEEDED`；**6/18**，失败不删除、未回滚重复计数。
- 正式L2 **1/2**，四项强制检查全部PASS；主动时长按消息开始至最后更新的连续墙钟保守计（当前读 `ATTEMPT_LEDGER.active_minutes` 与 `MEASUREMENT.cost.active_minutes`，均不超过120），包括修检查器、读取、实验、报告；不是纯键盘耗时。
- 本次新增network_calls、model_calls、payment_calls、installation_calls、product_calls均0；没有外部服务请求、商品支付、真实PSP及SDK调用；此前来源准备阶段10个公开GET/727832字节已独立记在 `PREPARATION.json`，不可混淆为执行时零网络。
- Git写入/提交/推送0。保护的其它旧工作区改动未触碰，旧合同材料可与新hash审计比对。

## L2 Task Gate / 正式执行者门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/L2-GATE.json
- Validation plan: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/VALIDATION_PLAN.yaml
- Formal L2: 1/2, VP01–VP04 PASS 4/4, mandatory_failures=0; original checker compatibility deviation must be independently accepted.

## EV-01 — 原冻结范围与来源保护（VP-01）

- AC: AC-01
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-01.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-01.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-01.stderr.log
- Observed result: 0，H62 1154 / 其它1719 / 修订清单23 / 三源库3；原始修订例外另审。

## EV-02 — 六条原源引用与合同映射（VP-02）

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-02.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-02.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-02.stderr.log
- Observed result: 0；六样本各七类事实+P1–P5通过结构检查，**Evaluator独立语义检查仍必要**。

## EV-03 — 单一后续问题与成本预留（VP-03）

- AC: AC-03, AC-04
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-03.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-03.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-03.stderr.log
- Observed result: 0；候选 `BOUNDED_READONLY_COMPARISON_CANDIDATE`，6预留，费用在界。

## EV-04 — 七项负例与最终保护复查（VP-04）

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-04.meta.json
- Stdout: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-04.stdout.log
- Stderr: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/evidence/l2_executor_01/EV-04.stderr.log
- Observed result: 0；坏引用/越界/超预算/假后端证据拒绝，冻结保护仍保持。

## 执行者交接

**Executor status: SUBMITTED_FOR_REVIEW，L3 NOT_RUN。** Evaluator下一步先核对用户授权的两份冻结例外（旧/新SHA与原始源正负例），明确是否接受这次偏差/独立重冻结，再使用独立L3逐条语义审查六份来源。仅可接受为来源资格测量，不可把本轮L2当真实支付能力提升或签收产品。若新旧哈希/来源/界限不成立，直接REJECTED/修复或STOP；不自动H64。
