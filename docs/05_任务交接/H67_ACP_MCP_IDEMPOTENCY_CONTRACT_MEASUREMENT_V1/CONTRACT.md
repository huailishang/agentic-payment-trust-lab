# H67：ACP交易工具是否弱化了幂等键必填契约

Task ID: H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 23f1505de1991c608aec2644a327b71abd7e76f5
Validation plan file: docs/05_任务交接/H67_ACP_MCP_IDEMPOTENCY_CONTRACT_MEASUREMENT_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-10-r109
Active bottleneck: B-20
Hypothesis: H-67
Metric baseline: H66资格研究PASS，固定视图未找到金融消费者，停止IronClaw接入；本仓A–D本地关闭、E受控本地代表闭合、F当前。ACP官方Issue #295及固定主分支文件提示REST与MCP幂等键要求不一致，尚未形成本包的成对测量结果。
Estimated affected scope: 固定5个官方结账工具，4变更/1读取；只测meta元数据对象的键必填语义。
Expected project impact: 将具体外部绑定风险转成可独立复算的有限矩阵，不声称产品漏洞或实际重扣。
Rollback condition: 需完整域模型、其它规范版本、运行服务器、依赖安装或真实交易才能解释时保持输入受限，不扩大目标。
Expected material cost: init起45分钟墙钟、最多2分析尝试/2正式L2；固定10个成对探针及5个官方示例元数据观察。网络/安装/上游运行/模型服务/产品/钱包/签名/付款0。
Bounded retry / iteration budget: 失败先保留，开始每次分析和L2前预留；最多同一策略内纠正引用/格式/实现，不能借余额加场景或改上游schema。

零容忍风险是交易副作用重复。B-20只测协议转为工具描述时是否丢失该前置要求，优先于继续泛用运行时研究。UCP samples #277报价/履约引用问题是次选，需要更多运行时成本且不是已证明授权越界；H62与真实支付不重开。公开问题单不是客户付费需求证明。

## Single objective / 唯一目标

用同一固定来源，逐工具比较“REST要求带幂等键”与“MCP元数据schema是否接受缺该键”，以仅改变键存在性的成对探针判断绑定契约是否弱化，并用读取工具作对照。

本包既不修产品或上游，也不验证服务端是否会拒绝、补键或稳定重放；不得把元数据schema接受升级为完整RPC请求可执行、实际重扣或生产漏洞。

## Frozen sources and scope / 固定来源与范围

SOURCE_BUNDLE.json由评估者从官方agentic-commerce-protocol/agentic-commerce-protocol提交7fdd78df677a94dce04c770644b0fbbb1401272b制备，源状态为unreleased（未发布）。包含规范相关行、工具映射相关行、完整meta schema、5个meta参数描述和5个示例meta；不含域payload。5份原文的Git blob与正文摘要已核验，许可证Apache-2.0随包保留。原完整来源仅留本地准备证据，公开投影足够执行本任务，无需新下载。

固定工具由BUNDLE.mcp.parameters给出：create/get/update/complete/cancel_checkout_session。每个工具恰做MISSING_KEY和PRESENT_KEY两探针，两者只有meta.idempotency_key存在性不同，api_version相同；PRESENT使用任务内非空测试字符串。官方示例另计5条元数据观察，不计实际调用。

只允许标准库实现并说明封闭的JSON Schema子集（object/type/required/properties/additionalProperties；探针只含无format字段）。不能声称完整JSON Schema/OpenRPC合规；域schema的外部引用不解析、不获取、不验证。遇到影响判断的未支持关键字应INPUT_LIMIT，不默默跳过。

## Allowed scope / 允许范围

仅写本任务ANALYZE.py、RESULT.json、REPORT.md、ATTEMPT_LEDGER.jsonl、versions/、derived/及新evidence/；CURRENT只改本任务状态/阶段。冻结CONTRACT/CHECK/计划/入口/SOURCE_BUNDLE/UPSTREAM_LICENSE/INPUTS只读。产品src/tests、H66报告/来源/失败/L2/L3和全部旧任务禁止改写或重跑。

不运行上游、JSON-RPC/MCP/HTTP服务或客户端；不运行示例，不发任何工具/支付调用，不安装验证器，不扩协议、工具或字段。只解析冻结文本/JSON与构造本地字典。

## Acceptance criteria

### AC-01 — 来源和历史保持

Given INPUTS/BUNDLE；When VP-01/04；Must observe冻结文件、公开历史与产品摘要保持，5来源归属/许可和unreleased边界明确；保留投影范围，不伪造完整RPC或运行结果。无需原始CartTrace或IronClaw缓存。Mandatory: yes。

### AC-02 — 五工具与十个单变量探针

Given 官方工具映射和meta schema；When VP-02与独立语义审阅；Must observe精确5工具/10探针：verb、REST键要求、meta容器required与内部键required分别记账；同对api_version相同且仅多/少幂等键。逐探针保留输入、meta子集接受结果、规范要求是否满足、契约差异和原bundle引用。GET不因缺幂等键误报，不能把容器必填当作内部键必填。Mandatory: yes。

### AC-03 — 官方示例与结果边界

Given 官方5例meta；When VP-02；Must observe每例幂等键存在性、schema子集接受、对应REST规则及来源引用；不把例子缺键视为成功付款。总体只为CONTRACT_WEAKENING_CONFIRMED/NO_WEAKENING_IN_FROZEN_VIEW/INPUT_LIMIT之一。backend_rejects_missing_key与backend_synthesizes_stable_key均UNKNOWN，production_duplication_observed=NOT_MEASURED；产品成熟度不变。Mandatory: yes。

### AC-04 — 有界执行与防误报

Given 事前预留追加账本及VP-03/04；Must observe修改源schema、误拒GET、破坏单变量对照、隐去缺键接受、例子键存在性造假、宣称实际付款六类错误被拒；保留每次分析/L2起止、成功失败及产物摘要。≤45分钟/2分析/2L2；旧版本或失败不得覆盖，各副作用为0。Mandatory: yes。

## Outputs and validation / 输出与验证

RESULT顶层task_id、ref、scope=META_ONLY、decision、probes（10条）、examples（5条）、backend_rejects_missing_key=UNKNOWN、backend_synthesizes_stable_key=UNKNOWN、production_duplication_observed=NOT_MEASURED、runtime_executed=false、product_effect_measured=false、payment_executed=false。每探针id/method/case/meta/rest_verb/rest_contract_requires_key/meta_container_required/meta_internal_key_required/mcp_meta_schema_accepts/rest_rule_satisfied/mismatch/citations；示例method/key_present/mcp_meta_schema_accepts/rest_rule_satisfied/mismatch/citations。

引用格式为pointer（SOURCE_BUNDLE内JSON Pointer）及value_sha256（排序/紧凑/UTF-8规范JSON值摘要），不可改成网络取数。按EXECUTOR_START先source再init与EXECUTING；分析/L2均begin→执行→finish，分析结果先保存在versions/A编号/RESULT.json，再复制最终版本为RESULT.json；失败保留。公共runner执行四VP，L2成功后报告仍EXECUTING/Executor，Evaluator独立L3及来源复核。

## Authorization / Exclusions

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

Evaluator既有安全发布授权不转授Executor；本任务也不继承H66公开GET权限。禁止联系作者、修上游、安装、运行服务、访问外部模型或付款。发现共同契约断点也只提交证据，下一能力包须重新评估具体消费者与边界。

## Stop conditions

达到预算、缺冻结文件或出现未支持schema语义即停并记录受限；不为了正结论修改源或扩字段。十探针/五例足够即提交；若弱化确认，只有下一具体消费者及可判定控制目标成立才另冻有界控制测量；若未确认则停止此假设。不能把纯规范结果当成服务端行为。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-09/11/12/14/18/20；适用性=CORE/EVIDENCE_ONLY的契约保真测量；对象=幂等键要求；代码=任务内分析；Test=四VP/六损坏/独立矩阵；Evidence=冻结官方来源及新L2/L3；before/after产品成熟度不变，真实重扣/身份/签名/部署/客户价值/合规unknown。
