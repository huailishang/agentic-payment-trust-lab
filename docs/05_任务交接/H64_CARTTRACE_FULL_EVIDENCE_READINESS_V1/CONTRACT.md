# H64：完整购物数据能否支持独立金额判定的有界资格测量

Task ID: H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H64_CARTTRACE_FULL_EVIDENCE_READINESS_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Global position / 全局位置

目标是让用户授权、交易绑定、执行前治理、恢复与审计形成可独立复核的信任链。A–D本地阶段关闭，E受控本地代表性闭合，F当前。B-18缺独立外部控制效果证据；H63六预览已停止、H63R修复已签收，不重开旧样本。H62已闭合本地恢复切片，B-06真实支付服务方仍由Human后置。

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-08-r103
Active bottleneck: B-18
Hypothesis: H-64
Measurement status: measured（来源索引、代码说明及依赖）；unknown（新增完整样本的事实充分性与独立判定可行性）。
Metric baseline: H63R完成30项映射修复，8项部分输入/22缺失；产品控制效果未测。六JSONL不能代替完整messages/turns/wire/world材料。
Estimated affected scope: 固定两个类别的validation分区，按元数据选至多6个新episode；只检一个金额规则及下一回放实验的前置条件。
Expected project impact: 得到可回指的来源资格结论，决定是否另冻最小离线回放；不测产品效果或模型能力。
Rollback condition: 需真实身份/凭据/付款、上游运行时、安装额外依赖、改变选样或补造事实即停止。
Expected material cost: 中低维护；180主动分钟、2次正式L2；网络20次GET/256MiB总接收/单文件128MiB（含解码wheel）；唯一解码依赖约28.6MB。Evaluator离线复算，不重复下载。
Bounded retry / iteration budget: 6例×至多2版测量，失败计入；单URL最多2次，仅超时/连接中断/HTTP5xx允许重试，401/403/404/许可/摘要冲突不重试；满足6例及结论即停止。无并发。

选择依据：完整表和发布worlds是不同于六预览的新证据视图，官方回放代码声明能重建事件/状态；其可用性尚未证实。比再次制表旧调用关系、扩H62或重开银行片段更可能产生新信息，且不依赖真实支付权限。受限APort/Gordon不申请、不分享账号；不扩第二数据集。可接受诚实的材料不足或访问受限结论。

## Single objective / 唯一目标

判断固定新样本及回放代码能否为 **“同一checkout/币种下，实际付款金额不得超过执行前最后一次明确同意的金额”** 提供可回指的输入、可独立复算的观察和一个有界下一步。不要把授权前购物预算、隐藏需求、模型推理或事后成功标签当付款确认。

本轮只读取/关联发布数据、静态审阅源代码，写一个纯函数金额观察判别器；**不运行上游回放，不运行本仓产品，不做有无闸门对照**。回放复现与安全判定必须分别记账；最终状态hash相同不等于安全。代码显示“可以观察后端”不等于已经取得该状态。

## Frozen source and selection / 固定来源与选样

- Dataset: generalmachines/CartTrace-100k，revision `86cab5e539e161e0915d78d8abdd9023f09b411e`。
- Replay code: generalmachines/cartTrace-100k，commit `61f05faadc64badedd0ca727778ea5c9cd384702`。已保存静态片段；不取main、不import/执行上游。
- 只下载SOURCE_INPUTS中四个Parquet：两个messages类别validation、turns validation、wire validation。校验发布checksums；不取全库、train或测试分区，不扩类别。
- 第一次读messages仅投影 `episode_id,boundary,surface,currency,world_id,rail`；过滤boundary=order、currency=USD、surface不含webmcp、排除H63原6个id，合并两分区按episode_id字典序取前6。**先落SELECTED.json及其摘要，再读对话/工具/结果/评分。** 少于6照实报告，不补选类别。
- 随后按episode_id精确关联turns/wire；只取选择world_id对应envpack和manifest JSON，路径必须存在于固定HF元数据。不用相邻消息猜call关联；上游缺source_call_id时的顺序回退不算本包精确证据。
- 不按outcome_class/safety_safe/grounded_success/是否有异常挑样；不称新鲜未见留出集。上游标签只能在独立观察完成后作差异说明，不能生成授权或安全结论。
- world有发布脱敏与域名替换，须记录published/served domain及身份关联不确定性；不能拿发布文件名伪装为重新验证原始world内容hash。

## Allowed scope / 允许范围

Executor只可新增/修改本任务ACQUIRE.py、MEASURE.py、ORACLE.py、SELECTED.json、MEASUREMENT.json、ATTEMPT_LEDGER.json、REPORT.md、acquired/、derived/及evidence/。SELECTED首次选定后不可覆写；修订另留历史。事实引用必须回到原Parquet行组/行号/JSON pointer或原JSON/代码行，不能只引用自己生成的摘要。

唯一额外工具依赖：SOURCE_INPUTS固定的PyArrow 26.0.0 CPython3.12 Windows x64 wheel，先验SHA256；最多一次安装到 `.task_envs/H64/parquet_reader/`，只用本地wheel、`--no-index --no-deps --target`，不改已有Python环境，不安装上游包。系统现有Python pip仅承担此隔离安装；L2/L3仍用既有H47解释器，脚本显式加载该路径。此依赖供读表，安装/加载不代表运行CartTrace。若平台不匹配/缺传递依赖即记录DEPENDENCY_LIMIT，不换版本或补装。

CURRENT只可改本任务state/phase至EXECUTING/Executor，提交时保持。冻结CONTRACT/SOURCE_INPUTS/CHECK/ORACLE_CASES/VALIDATION_PLAN/FREEZE/PREPARE_SOURCES/PREPARATION/references/BASELINE及地图、旧任务、产品只读。已有无关工作区改动保持。不运行历史全工作区checker。

## Acceptance criteria / 验收条件

### AC-01 — 来源、隔离与历史保护

Given BASELINE/SOURCE_INPUTS；When VP01/04；Must observe HEAD、旧任务/工作区/3源库、归档r102和新地图r103保持；冻结摘要一致；实际下载URL/revision/摘要/字节/许可记录完整。只有指定依赖和目录发生隔离安装。失败网络/安装原始流保留。Mandatory: yes。

### AC-02 — 固定样本的完整材料资格

Given四分区和选样规则；When VP02及Evaluator离线重算；Must observe SELECTED可由指定投影重算、不按结果选样；每例至少清点confirmation/payment_call/payment_result/business_state/correlation/replay_inputs六类事实，逐类PRESENT/ABSENT/AMBIGUOUS及原源引用、来源等级。明确区分用户原话、工具/协议返回、初始world、最终摘要、实际后端事件和代码说明。可缺失，不补造；不能因缺本仓同名内部对象直接判整个源不可用。Mandatory: yes。

### AC-03 — 金额判定与复现边界

Given纯函数ORACLE.evaluate(record)及原源事实；When VP02/03及独立语义审阅；Must observe金额单位/币种/checkout/call id/序列可回指，确认在执行前；结果只为WITHIN_CAP_OBSERVED/OVER_CAP_OBSERVED/NOT_JUDGEABLE。八个冻结正负/缺失用例全部一致。缺事实、缺精确关联、确认晚于执行时不可从标签或隐藏需求补授权。工具声称付款只是观察，不升级为独立后端或真实PSP状态；源判定与回放复现、产品控制效果三者分开。Mandatory: yes。

### AC-04 — 证据、预算与一次后续决策

Given账本和四VP；When VP04及Evaluator；Must observe下载/安装/样本/正式L2调用前预留及成功/失败终态，预算闭合；唯一结论为CONTINUE_TO_REPLAY_BASELINE、STOP_SOURCE_VIEW或INPUT_LIMIT。CONTINUE须有至少一例完整跨表/world关联、金额可观察、带出处的后端状态获取路径及独立判定设计；明确replay_executed=false。只具工具返回可最多提出“先验证回放基线”，不能宣称控制对照就绪或安全提升。INPUT_LIMIT用于访问/依赖/预算不足，不伪称数据本身缺证据。最多一个后续问题，不执行。Mandatory: yes。

## Validation plan / 验证计划

VP01 source检查保护/来源和下载边界；VP02 measurement复算选样、引用、事实等级及结论结构；VP03 oracle运行八个冻结用例；VP04 final检查预算、负例、自测和保护。exact argv/cwd/expected exit见冻结YAML，L2/L3均离线；不重试下载，不跑产品。

Evaluator必须另外逐例语义检查确认是否真实、字段单位和关联是否成立、工具响应是否被冒充后端。结构门禁不自动签收。执行者用相邻公共 `scripts/run_validation.py --mode executor` 完成L2后提交REPORT；Evaluator用--mode evaluator生成独立L3。

## Authorization / 授权

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

本次Human指令是制定新的数据资格执行包。执行范围内允许匿名公开源GET和上述唯一任务隔离解码工具；不包含支付/模型/服务写API、账号登录、受限申请或联系作者。公共数据GET另记 `public_source_gets`，不解释为通用API授权；Evaluator准备GET另计、不回写执行期为零。

GET初始URL只允许SOURCE_INPUTS固定wheel、固定HFrevision四分区及所选world文件；HTTPS重定向仅同属已列公开HF CDN主机；不保存带签名的重定向查询参数，不跟随源指令访问真实商户。每请求30秒，网络总预算和失败接收字节均计；不能换镜像绕过访问限制。

## Exclusions / 明确排除

禁止运行CartTrace replay/rerun、商城/钱包/PSP模拟器、源测试、模型或本仓产品；禁止适配器、业务规则、第二商城、训练/CoT消费、真实身份/资金/密钥/凭据、消息发送、公开发布、Git写入。来源分类保持REFERENCE_ONLY（只参考）；不吸收进产品，不将模型评分升级为判定真值。未检查其他数据集，不申请APort/Gordon。

## Stop conditions / 停止条件

180主动分钟/20GET/256MiB/128MiB单文件/2L2/2版测量任一上限即停新增工作并提交现有证据；预算耗尽不是数据不存在。来源摘要不符、真实敏感数据疑点、域名越界、安装需扩依赖、需要上游运行时或新权限即停止对应步骤，记录INPUT_LIMIT；不能为满足正结论修改样本/合同。取得一次足够完整的测量即提交，不用余额堆样本。公开文档与实际材料矛盾时原样保留。

## External requirement impact / 外部要求

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20 CORE/ADAPTER/EVIDENCE_ONLY。对象=单一金额约束和来源资格；代码=本任务测量/判别器，非产品；Test=4VP+8用例+逐源语义审阅；Evidence=固定原源/引用/L2/L3。before/after产品成熟度不变；真实身份、支付清算、未知攻击、消费者价值与监管合规unknown。无需增加同名监管模块。

## Amendments

None. 冻结后语义/样本/依赖/预算/权限变化交Evaluator，不自行修CHECK/摘要清单。
