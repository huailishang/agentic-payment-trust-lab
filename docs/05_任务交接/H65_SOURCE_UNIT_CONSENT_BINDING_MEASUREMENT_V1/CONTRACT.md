# H65：现有源能否补齐金额单位与确认绑定

Task ID: H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 211151e6c3ae53997b5a2da419c27db497d7eb48
Validation plan file: docs/05_任务交接/H65_SOURCE_UNIT_CONSENT_BINDING_MEASUREMENT_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-09-r106
Active bottleneck: B-18
Hypothesis: H-65
Metric baseline: H64R独立L3四VP通过、六源语义通过；5原生调用分链、6响应金额/4请求额度观察、4条用户金额确认；6/6来源判定仍不可判定。
Estimated affected scope: 原六episode、已下载材料和已锁定静态代码，不新增样本或来源。
Expected project impact: 区分已有源桥接事实未提取与源材料确实不足，不声称产品控制效果提升。
Rollback condition: 需要新文件、网络、依赖、回放、真实身份/签名或人为补造关联时停止并保留未知。
Expected material cost: 75主动分钟，最多12次完整episode源读取、1版分析、2次正式L2；网络/安装/模型/产品/回放/付款0。
Bounded retry / iteration budget: 仅允许同一假设内修正引用/格式；不得扩样、增加第二版策略或超2L2。足够判断即停。

目标仍是高风险交易信任链可独立复核。A–D本地关闭、E受控本地代表闭合、F当前。H62代表切片已闭合，真实支付受授权限制；现有wallet的Consent/checkout/amount结构是值得静态核查的具体线索，比直接回放或继续扩旧切片成本更低。该代码说明不是实际episode授权事实。

## Single objective / 唯一目标

只判断现有锁定材料能否为至少一例建立可回指的“执行前用户确认金额 → 特定checkout → 金额单位 → 协议报告结果”证据链。逐例区分PROVEN/PARTIAL/UNKNOWN/INPUT_LIMIT；不得把自然语言没有字面checkout id或签名直接当作证据不存在，也不得把相邻、同额、metadata标签或代码意图当作真实绑定。

这不是回放、产品对照或新能力建设。没有至少一例完整直接证据时，停止当前六例静态来源视图；不再围绕同一未知字段无限修补。

## Allowed scope / 允许范围

只写本任务ANALYZE.py、RESULT.json、ATTEMPT_LEDGER.json、REPORT.md、derived/与新evidence/；CURRENT只改本任务执行状态/阶段。INPUTS/CHECK/CONTRACT/计划/入口/FREEZE及已有准备证据只读。

INPUTS.json锁定H64R提交快照、H64 SELECTED/ORACLE、四Parquet/11个已获world、已存静态代码/文档与产品文件摘要。只读这些输入；不import/执行上游、H64/H64R提取器或产品。允许标准库和原固定PyArrow解码器；不得重新安装或下载。H64/H64R合同、报告、测量、账本、L2/L3和src/tests不得改。

## Acceptance criteria

### AC-01 — 输入和产品边界

Given INPUTS；When VP01/04；Must observe冻结任务文件、全部输入和产品摘要保持；只在本任务允许路径落盘，网络/安装/模型/产品/回放/付款0。发布提交只改变治理元数据，不以HEAD自引用判定输入是否相同；精确输入摘要是本任务保护依据。Mandatory: yes。

### AC-02 — 单位与适用范围

Given同六例及原源；When VP02和独立语义审阅；Must observe每例原始amount/currency/checkout与单位的定义、适用字段和连接路径，或具体缺失。PROVEN必须引用原源字段或类型定义及其适用链；不能由数值相似、美元常识或隐藏评分推算。源规范说明与运行结果分开。Mandatory: yes。

### AC-03 — 用户确认到checkout的显式桥

Given确认原话、序列、challenge/call/checkout和已存钱包静态说明；When VP02及独立逐边复核；Must observe每边来自SOURCE_OBSERVATION/CODE_INTENT/INFERENCE中的哪一种及原源引用。PROVEN须包含同episode直接源观察，不能只由代码存在、metadata seq、顺序或同额推出；缺环保持未知。缺签名不新增为本包拒收条件。Mandatory: yes。

### AC-04 — 有界决策与防过度声明

Given四VP和账本；When VP03/04；Must observe代码意图冒充绑定、无引用的单位、伪称回放执行、无完整例却CONTINUE四类损坏被拒。最终只作CONTINUE_TO_REPLAY_BASELINE/STOP_SOURCE_VIEW/INPUT_LIMIT之一；CONTINUE需要至少一例单位与绑定均PROVEN，但也只允许另冻回放基线，不执行回放。账本≤75分钟/12源读取/1版/2L2，失败保留。Mandatory: yes。

## Validation plan

四个VP依次核source、analysis、guards、final；正式L2/L3使用公共runner，机器参数见冻结YAML。Evaluator必须独立核原源及每条连接，结构通过不自动签收。

## Publication and baseline / 发布与基线

本任务在发布前观察到的代码基线为上述HEAD；本合同、地图和摘要清单随下一次正常提交发布，发布本身不授权改变输入。CHECK.py package只验证可公开任务元数据，不需要私有原始输入；CHECK.py source才验证全部本地输入并允许业务开工。远端仅package通过不能声称L2或源测量通过。没有本地输入时明确INPUT_LIMIT，不按旧任务HEAD失败误判为需要改门禁。

## Authorization / Exclusions

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

上述为Executor权限。Human本轮另行授权Evaluator按中央数据安全门禁统一提交推送可公开任务包；不转授Executor，不上传原始日志、凭据、解码器或原始数据，不允许新GET/付款/服务写入。禁止发布、本地快照外取数、受限申请和联系他人。

## Stop conditions

任一预算耗尽、缺输入、需新依赖/授权/运行时、引用无法复算即停止新增操作。若完整证据仍不足，最终STOP_SOURCE_VIEW；若仅环境缺已锁定文件则INPUT_LIMIT。不得另开同六例的第三轮静态修补；存在直接完整链才可建议另冻回放基线。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；适用性CORE/ADAPTER/EVIDENCE_ONLY沿原源测量；对象=单位与确认桥测量合同；代码=任务内只读分析；Test=四VP+四反例+独立逐源审阅；Evidence=新L2/L3；产品成熟度before/after不变，真实身份/清算/控制效果/合规unknown。
