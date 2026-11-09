<!-- Public display copy; original SHA-256: 7386e0c2ddb00d6fa318cb088a6590e156694bcfe4f274584aaa1c6c33e708bd; only trailing whitespace/line endings normalized. -->

# H64 执行报告：CartTrace 完整材料的有界金额证据资格测量

Task ID: H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1
Task kind: one_off
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: SUBMITTED_FOR_REVIEW
Authorization: commit=false, push=false, history_rewrite=false, api_call=false

## Global position / 全局位置

本项目要在可重置测试环境中独立验证智能体授权、交易绑定、执行前控制、支付与订单异常恢复和审计链。地图r103：A–D本地阶段闭合、E受控本地代表闭合、F外部协议/独立证据仍在进行。第一可执行瓶颈B-18是**独立外部轨迹能否提供可判定的授权、付款金额与后台状态事实**。H63R已签收并停止六预览；B-06真实支付主体及PSP仍需另行Human授权。H64只做完整表/world/静态代码的来源资格检查，不运行上游或本仓产品、不测安全控制效果。

## Workspace snapshot / 工作区快照

Changed files / 改动文件：
- 本任务新增 `ACQUIRE.py`（冻结白名单公开GET、严格接收预算、下载前预留与SHA校验）、`MEASURE.py`（固定投影选样、原表行组/行索引证据与测量账本）、`ORACLE.py`（金额观察纯函数）、`SELECTED.json`（首次锁定不可覆写）、`MEASUREMENT.json`、`ATTEMPT_LEDGER.json`、`REPORT.md`。
- 本任务 `acquired/` 保存获取的公开材料；`derived/INSPECT.json` 仅用于人工只读审阅，正式引用回到原Parquet/JSON/源码；`evidence/l2_executor_01/` 存原始L2三件套和Gate；`evidence/FAILED_GET_CAPTURE_20261108.md` 保留失败终端输出副本；`evidence/INSTALL-01.stdout.log` 和 `INSTALL-01.stderr.log` 记录隔离安装。
- `.task_envs/H64/parquet_reader/`：仅将指定PyArrow 26.0.0 wheel进行一次本地 `--no-index --no-deps --target` 隔离安装，未更改旧环境。只下载和读表，无上游运行时导入。
- `CURRENT.md` 只改H64状态/阶段为 `EXECUTING/Executor`；保持其余旧任务、源码、测试、冻结合同/判别器/验证计划/地图、原三库和用户既有脏工作区不变。

Deviations and unresolved items / 偏差与未解决项：
- 固定 `env-bd45a7e9be19` envpack 的两次公开GET（G-08 RemoteDisconnected、G-09 URLError）均零接收并失败，已到该URL的冻结上限；**不得第三次、改源或换镜像**。其manifest取得成功，但envpack缺失，不能声明六组world完整可用。
- 其他下载成功不等于此world缺失或数据自身无交易证据；属于INPUT_LIMIT。固定提供的发布world存在脱敏和域名替换，未证明发布文件名等于其原始内容SHA。
- 当前金额观察有执行前明确价格确认与原生payment call id的来源片段，但尚未构造可独立证实的**相同checkout、单位、付款状态**的完整链。用户说“place order for $X”不自带签署的checkout ID，不通过邻近消息猜测授权；工具结果不充作PSP清算或后端账本。
- `ORACLE.evaluate` 是纯金额规则，不是对发布轨迹的支付安全裁决；样本上全部NOT_JUDGEABLE指**此测量输入不充分**，不能推断六例确实越额或不越额。

## Fixed selection / 固定样本与来源

- Dataset: `generalmachines/CartTrace-100k` @ `86cab5e539e161e0915d78d8abdd9023f09b411e`；code: `generalmachines/cartTrace-100k` @ `61f05faadc64badedd0ca727778ea5c9cd384702`。
- 两个固定类别 `arts-crafts-music`、`automotive-parts` 的validation messages第一次仅投影 `episode_id,boundary,surface,currency,world_id,rail`，排除旧H63六例，过滤order/USD/非webmcp；候选141条，按episode_id字典序固定前6，随后才读取turns/wire、完整messages和world。源SHA/名单SHA见 `SELECTED.json`；非随机抽样、非未见留出集。
- 六例：`ep-03a80be98c66`、`ep-0646e4cec480`、`ep-08fb1a04f29a`、`ep-09bafc6d1c7e`、`ep-1375d00dacdb`、`ep-172fbb8cce5b`。四个Parquet发布SHA全部验证通过；六组world所需12个JSON取得11个，缺第2例envpack。
- 在 `MEASUREMENT.json` 的36项事实中，执行前**明确标价下单确认、支付工具调用、工具返回和精确call id级别关联**在第1、2、4、6例均可观察；第3、5例只有初期购物/其他行为，不能把预算/选品升级为下单确认。六例均有最终state摘要，但**摘要≠独立后台事件**；world输入5例完整、1例不完整。
- 每项 `confirmation/payment_call/payment_result/business_state/correlation/replay_inputs` 均带PRESENT/ABSENT/AMBIGUOUS、源文件、Parquet row_group/row_index/JSON pointer和值SHA256或JSON/代码原引用。调用/响应仅按原生 `call_id/tool_call_id/source_call_id` 精确关联，未使用上游缺ID时的顺序回退。
- 6个观察结论均为 `NOT_JUDGEABLE`（不可判定）。第1、2、4、6例有可解析的USD下单文本，却尚不能将其与唯一checkout ID及独立付款单位/结果完全绑定；第3、5例没有明确下单价格确认。不能把 `final_state`、`grounded_success`、模型陈述、钱包令牌或工具成功当真实支付凭证。

## Impact comparison / 影响对比

Measurement evidence: `SELECTED.json`、`MEASUREMENT.json`、`ATTEMPT_LEDGER.json`、`acquired/`四Parquet/固定11world JSON、冻结源码 `references/` 及 `evidence/l2_executor_01/L2-GATE.json`。
Before: H63/H63R只验六JSONL预览的可观察性，不知道完整表/world对单一金额判定是否提供独立证据。
After: 新增固定六例的原生跨表call ID追溯、11份world发布材料、源限制与一项纯金额观察器；明确指出单一world获取失败，后端真实状态和checkout绑定仍不可证明。
Delta: **来源资格与数据访问边界得到实测，产品控制效果=未测量**；没有增加外部支付真实性、生产安全或监管成熟度。
Guardrail result: 已验证4个原Parquet SHA、唯一wheel SHA，PyArrow仅一次隔离安装；正式L2 4/4 PASS、八个固定ORACLE用例PASS、7项负边界自测PASS；保护2944旧文件/34冻结文件/原三库未漂移。
Scope caveat: 仅所选validation中6条合成记录；world脱敏/域名转换，工具/协议结果是模拟，不是独立资金清算；没有运行任何上游回放、产品、模型、钱包或支付副作用。

## Cost / 预算与停止条件

- 公开GET **18/20**，其中成功16次、失败2次（G-08/G-09）；所有初始URL及重定向host和实际接收字节保存于 `ATTEMPT_LEDGER.json`。四Parquet与指定wheel有发布hash；world JSON以实际sha记录，未伪称原始未脱敏hash一致。
- 仅1次工具依赖安装，模型/付款/产品/上游回放调用均0；原六条样本各读取2次，共12次sample读取，测量版本1/2；正式L2 1/2。
- 保守活动时间截至正式L2结束由账本计算为20/180分钟；执行期公开GET与准备阶段 `PREPARATION.json` 中的GET严格分开。没有Git提交或推送，授权旗标维持false。

## Decision / 本次唯一决策

**INPUT_LIMIT（输入获取受限） / REFERENCE_ONLY（仅参考） / SOURCE_READINESS_ONLY（仅资格材料）**。

H64合同正向的 `CONTINUE_TO_REPLAY_BASELINE` 要求所选六world均取得，且有可比较金额和带出处的后端观测路径；因固定envpack访问失败、严守每URL两次尝试及不补造金额绑定，本轮不能达成。**不以这次失败推断CartTrace整体无用，也不把缺失材料误报为支付安全漏洞。** 下一步由Evaluator独立L3审阅并权衡是否停止此source slice、另取得明确授权/网络条件后重冻访问修复，或切换另一有独立证据的消费者；本包不自动H65、不运行回放。

## L2 Task Gate / 正式执行者门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/L2-GATE.json
- Validation plan: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/VALIDATION_PLAN.yaml
- L2尝试1/2，全部必选VP 4/4，mandatory_failures=0，独立Evaluator L3 NOT_RUN。执行者未宣布最终任务PASS。

## EV-01 — VP-01 来源与保护

- AC: AC-01
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-01.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-01.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-01.stderr.log
- Observed result: exit 0 / PASS；protected=2944、frozen=34。

## EV-02 — VP-02 六例来源与金额证据测量

- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-02.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-02.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-02.stderr.log
- Observed result: exit 0 / PASS；样本6，INPUT_LIMIT，需独立语义审查。

## EV-03 — VP-03 金额规则纯函数

- AC: AC-03
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-03.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-03.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-03.stderr.log
- Observed result: exit 0 / PASS；冻结ORACLE 8/8，通过/超额/确认晚/错checkout/缺币种/隐藏需求/助手代确认/缺精确链接均按合同返回。

## EV-04 — VP-04 边界负例、预算、历史保护

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-04.meta.json
- Stdout: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-04.stdout.log
- Stderr: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/evidence/l2_executor_01/EV-04.stderr.log
- Observed result: exit 0 / PASS；7项基础负例、来源保护与预算检查通过。

## Executor handoff / 执行者交接

**Executor status: SUBMITTED_FOR_REVIEW，L2 PASS 4/4，L3 NOT_RUN。** Evaluator应独立接受提交快照、离线运行原冻结L3，并逐个检查六例真实原行引用、金额单位、确认时序、工具call ID与checkout链接；尤其审查“用户确认金额但checkout授权绑定不充分”的保守判断及INPUT_LIMIT分类。冻结规则不允许用模型/上游标签补授权，也不能把发布world状态和静态回放路径升级为已观测后端付款。若验证结论不一致，应REJECT或另行冻结修复，不直接改本包CHECK迎合结果。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；before/after产品成熟度不变；身份/真实PSP/合规/客户价值unknown。证据对象=本包合同、MAP/ORACLE与原始来源；本任务不宣称监管符合。
