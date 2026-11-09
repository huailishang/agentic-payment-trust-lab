# H63：外部购物轨迹的有限合同观察资格测量

Task ID: H63_EXTERNAL_TRACE_QUALIFICATION_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H63_EXTERNAL_TRACE_QUALIFICATION_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE
Attempt execution mode: SEQUENTIAL

## Strategic basis / 战略依据

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-07-r101
Active bottleneck: B-18
Hypothesis: H-63
Measurement status: measured（六份源预览及其结构）；unknown（有限合同观察是否可用）。
Metric baseline: 已有本地治理/恢复代表证据，缺本外部源的逐条可回指观察；没有本仓控制对照成绩。
Estimated affected scope: 六条已公开模拟购物预览，只测源适用性，不是外部真实商户或留出集。
Expected project impact: 收敛一个可判定的后续只读比较问题，或有证据地停止此预览视图；不声明能力提升。
Rollback condition: 来源漂移、范围外写入/执行/网络、伪造缺失事实、需要新增数据或预算时停止。
Expected material cost: 中低估计；120主动分钟/2L2，最多3次完整六例提取，Evaluator独立6例复算及最多6条附加只读诊断；网络/安装/模型/付款0。
Bounded retry / iteration budget: 18个sample提取预留、2次L2；失败同计，足够提交即停。语法/结构L1不反复读取源，不计新sample但计工时。准备公开读取与测量分开，准备10 GET/727832字节已发生，不写成零网络。

全局A–D本地闭合、E受控本地代表闭合、F当前。H62已签收并停止；B-06真实服务方后置。比继续加M06案例或重开AgentDojo，本包以新的独立购物来源收敛可测问题；比真实身份/付款接入少权限和维护负担。

## Single objective / 唯一目标

从固定六JSONL预览提取可回指的用户授权、确认、结账对象、付款调用/响应和订单响应观察，映射现有P1–P5所需输入，决定是否存在**一个**值得另冻的有限只读比较问题。允许诚实STOP结论；不要求找到漏洞，不开发适配器。

预览缺独立后端状态表是已知边界，不以再次发现该事实作为新成果；只测实际会话内可用观察。工具返回成功只可称TRANSCRIPT_ONLY（仅轨迹记录）。不把助手解释、上游outcome/grounded_success或隐藏需求当用户确认/真实身份/独立付款事实。

## Allowed scope / 允许范围

仅可新增/修改本任务EXTRACT.py、MEASUREMENT.json、ATTEMPT_LEDGER.json、REPORT.md及evidence/。EXTRACT仅标准库、输入只限六JSONL与冻结说明，不import/调用本仓产品、上游代码或外部工具；可读取本包冻结CHECK帮助函数解释格式，不借其生成观察代替源读取。

CURRENT只可改本任务state/phase至EXECUTING/Executor，提交时保持EXECUTING/Executor。合同、INPUTS、BASELINE、SPEC、CHECK、计划、入口、准备记录、全部references与地图/历史不可改。已有其他工作区改动保持。

## Acceptance criteria

### AC-01 — 保护与来源边界

Given BASELINE/INPUTS；When VP01/04；Must observe H62全部1154文件、三源库、其他工作区不变；r100归档hash匹配，r101只作为新基线。固定revision/六选择/许可/NOTICE保持；允许范围以外不写。Mandatory: yes。

### AC-02 — 六条源事实可回指

Given SPEC和固定六预览；When VP02及Evaluator逐源审阅；Must observe每例七类事实分别PRESENT/ABSENT/AMBIGUOUS，带原始行号、JSON pointer及所指值摘要；存在性与角色正确，缺失不补造。调用/响应按实际call id或显式业务id关联，不能靠相邻顺序猜测。Mandatory: yes。

### AC-03 — 合同映射与下一问题

Given逐例事实；When VP02/03及独立语义审阅；Must observe每例P1–P5输入OBSERVABLE/PARTIAL/MISSING，区分缺输入与产品失败；给出至多一个有源依据的后续只读问题，或STOP_PREVIEW_VIEW。缺身份/后端/完整用户策略明确保留，不推断整个数据集缺失或真实消费者需求成立。候选分类仍REFERENCE_ONLY。Mandatory: yes。

### AC-04 — 证据、成本与声明

Given预留账本、四VP和判别器自测；When VP03/04与L2/L3；Must observe调用前追加sample预留、失败原始流保留、预算闭合；新网络/模型/支付/安装/产品调用均0；只测源资格、不报告控制提升、泛化、生产安全或监管合规。Mandatory: yes。

## Validation plan / 验证计划

VP01 source：检查固定源、保护/归档/新地图及范围；VP02 measurement：六例引用、角色和映射结构；VP03 decision：决策/预算/预留；VP04 selftest及保护复查：坏引用、假后端证据、超预算等必须拒绝。exact argv在冻结YAML。L2/L3的结构通过不能代替Evaluator对六源逐条语义复核；L3只重算文件，不运行商家/模型/付款。

## Authorization / 授权

仅本任务离线测量产物可写。准备阶段公开只读研究已结束；Executor不得联网、下载新表、申请受限数据、分享账号或联系发布者。

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

## Exclusions / 明确排除

不改src/tests/SDK/商家/批准/订单恢复；不启动上游replay kit、调用工具或安装依赖；不重跑H62/H46业务；不建第二商城、通知/退款平台或通用运行时；不训练/消费外部CoT为授权依据，不读取凭据、不操作真实资金或链、不发消息、不Git写。

## Stop conditions / 停止条件

120分钟、18样本、2L2任一耗尽即停；来源漂移、真实敏感数据疑点、范围外权限/文件/新数据需要即停。一次完整有效测量即提交，不用余额堆样本。只剩已知缺表/评分陈述、无新观察时结论STOP，不用适配器制造可测性。后续需独立重冻结，不能自动实施。

## External requirement impact / 外部要求

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20 CORE/ADAPTER。对象=源资格合同和证据等级；代码=本任务测量器/判别器，非产品；Test=四VP和独立六源语义核查；Evidence=源行号/原值摘要/正式L2/L3。成熟度before=本地代表能力已有、此外部源未知；after=只收敛外部资料适用性，不升级产品M级。真实身份、PSP、确认来源、客户价值及监管合规仍unknown。
