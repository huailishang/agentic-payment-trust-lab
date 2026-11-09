# H64R：离线修复逐调用关联与已报告金额清点

Task ID: H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 211151e6c3ae53997b5a2da419c27db497d7eb48
Baseline amendment: AMENDMENT_20261109.md（评估者开工前基线迁移；原合同字节已保存）
Validation plan file: docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-09-r105
Active bottleneck: B-18
Hypothesis: H-64（继承；只修正源事实测量）
Metric baseline: H64 L3结构4/4，但AC-02混合call-32/34、AC-03统一清空payment而拒收；固定envpack两次失败属实。
Estimated affected scope: 原六episode、原四Parquet及11个已下载world；不选新样本、不取缺文件。
Expected project impact: 恢复来源资格测量的有效性，不能声明产品安全改善。
Rollback condition: 需要新材料/GET/安装、上游或产品执行、签名/真实身份才能完成本修复时停并回Evaluator。
Expected material cost: 90主动分钟、2L2、最多2版六例分析；复用已安装的PyArrow；网络/安装/模型/产品/回放/付款0。
Bounded retry / iteration budget: 每版六例，每例完整读取前记预留；最多12次sample读取，失败同计；迭代/正式L2失败原件保留，足够提交即停。

全局A–D本地闭合、E受控本地代表闭合、F当前。眼前阻塞是已下载事实的正确测量；补一个缺失world不会修复已存在的关联/金额丢失，故先离线修复，优先于扩H62、更换数据源或恢复真实支付权限。

## Single objective / 唯一目标

另产本目录MEASUREMENT.json，按**逐个原生call id**清点调用/响应/wire，保留源协议/工具实际报告的金额、币种、checkout和阶段，再逐维说明授权绑定/单位/后台状态仍缺什么。允许最终NOT_JUDGEABLE（不可判定），不允许通过统一清空已知字段预设结论。

失败AC-02反例：ep-09bafc6d1c7e旧引用call-32/call-32/call-34不能声称同一个id，须分链；如要论证显式父子关系，另列原生父子证据，不能把父子当相等。
失败AC-03反例：ep-172fbb8cce5b的wire行组1/行2632，seq69/source_call_id=call-68，响应total=4425/currency=usd/checkout-3766021cd113/status=completed，必须按“协议报告的完成”保留。它不自动证明真实清算。用户seq64确认44.25美元，原文不带签名或字面checkout id不等于金额字段不存在；同样禁止仅凭邻接把授权绑定设为真。

## Allowed scope / 允许范围

仅写本任务EXTRACT.py、MEASUREMENT.json、ATTEMPT_LEDGER.json、REPORT.md、derived/及新执行证据；CURRENT只改本任务state/phase至EXECUTING/Executor并保持该角色提交。冻结CHECK/CONTRACT/入口/计划/SETUP_BASELINE/READINESS/references/BASELINE/AMENDMENT不可改；既有evidence/governance_refreeze_20261109/及原准备证据只读。

H64全部原件和获取材料只读，包括拒收报告/证据/失败GET/预算；四Parquet、SELECTED名单和原先安装的 `.task_envs/H64/parquet_reader` 仅可读，不能重装/更改。只允许标准库和该固定PyArrow解码器。可以只读加载已审阅的H64 ORACLE.evaluate纯函数及冻结8用例；不得运行其ACQUIRE/MEASURE/CHECK或上游代码。不得改本仓src/tests/SDK、历史任务、三源库、地图或无关工作区。

## Acceptance criteria

### AC-01 — 原件与零外部副作用

Given经AMENDMENT_20261109审计的新BASELINE；When VP01/04；Must observe完整H64/历史工作区/原三库/解码器和HEAD保持，新文件限本任务，网络/GET/安装/模型/产品/上游回放/付款均0。开工前四个文档的纯行尾空格差异及地图治理更新已逐项记账；原摘要/字节保留，不把新快照冒充历史字节未变。Mandatory: yes。

### AC-02 — 逐个原生id的关联

Given原六例turns/wire；When VP02及独立审阅；Must observe所有H64已使用的支付相关工具call逐条清点（pay/send_payment_mandate/delegate_payment/shop_pay_payment_request）；同链call/result/wire引用都来自同episode且值相等，结果或wire缺失时PARTIAL，不合并第一元素。call-32/call-34分别处理，不声称32=34。父子关系若无直接证据则保留未知。Mandatory: yes。

### AC-03 — 先保留原始金额，再说明不可判定

Given源返回和确认原文；When VP02/03及独立语义审阅；Must observe已有金额/currency/checkout逐字段原源引用，区分请求/令牌额度/报告完成与真实后台。单位有依据才写amount_minor，否则保留raw_amount及UNKNOWN；不得把授权绑定不充分写成付款字段不存在。已知call-68的4425/usd/checkout原值必须出现，不可只运行8个虚构用例替代源清点。所有source_verdict由已审阅纯函数复算；缺绑定可NOT_JUDGEABLE，但missing_dimensions具体，签名不作为本包新增强制条件。Mandatory: yes。

### AC-04 — 反例、成本与保守声明

Given提交材料；When VP03/04和独立L3；Must observe误拼call id、删除已知金额、改金额不改引用、伪称回放已运行四类损坏被拒；原8用例保持；预算/预留/失败保留。访问限制单独继承，不能再次下载；修复结论不自动变成回放就绪、外部控制有效性或生产能力。Mandatory: yes。

## Validation plan

冻结YAML四VP：source保护；measurement复算关联/金额/缺失；regression内存破坏；oracle复跑原8纯函数例并复查保护。L2由公共runner --mode executor，L3为 --mode evaluator；都离线，Evaluator另核逐源语义。执行者报告SUBMITTED_FOR_REVIEW不等于签收。

## Authorization / Exclusions

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

本包网络/新下载/安装/执行上游/本仓产品/真实或模拟支付副作用全部禁止。不得对缺失world进行第三次或其它新尝试；不申请受限材料、不发消息、不发布、不扩数据集或更换名单。只读静态源和解码数据不赋予资金/主体真实性。

## Stop conditions

90分钟、12样本读取、2分析版本、2L2任一耗尽即停止新增尝试并如实提交；需改假设/AC/范围/依赖/权限或补源事实即回Evaluator。可以保留全部不可判定，但必须完成字段清点和逐维证据判断；不能用人为填空保证结果。修复通过后再决定下一测量，不直接接回放/产品对照。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；对象=源事实关联/金额修复合同；代码=任务内提取器/判别器；Test=4VP+冻结源反例/8纯函数例；Evidence=新L2/L3及原Parquet；产品成熟度before/after不变；真实身份/清算/控制效果/商业/合规unknown。
