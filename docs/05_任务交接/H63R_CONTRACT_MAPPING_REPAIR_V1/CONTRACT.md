# H63R：恢复既有P1–P5语义的最小测量映射修复

Task ID: H63R_CONTRACT_MAPPING_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H63R_CONTRACT_MAPPING_REPAIR_V1/VALIDATION_PLAN.yaml
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-07-r101
Active bottleneck: B-18
Hypothesis: H-63（继承，只修复测量合同语义）
Metric baseline: H63 L3结构4/4；AC-03语义失败，六例合同编号误映射。H63 REVIEW为权威拒收证据。
Estimated affected scope: 6×5映射；不改源事实，不扩大来源、能力、权限或资金范围。
Expected project impact: 修复测量有效性，产品控制效果仍未测；比直接比较错位合同或扩H62更优先。
Rollback condition: 需要新事实、数据、产品代码或权限，停止并回交Evaluator。
Expected material cost: 60主动分钟、2L2、一次六例映射及至多一次修订；Evaluator一次30映射独立审阅。
Bounded retry / iteration budget: 六例不重新运行EXTRACT，不刷新旧成本；新账本记录时间/正式L2次数/修订次数，失败原始流保留。网络、安装、模型、产品、付款均0。

## Single objective

在本目录新增MAPPING.json，把H63固定六例七类事实按产品既有P1–P5定义重新清点可用及缺失输入，保留一个后续只读问题或STOP。本轮不做该比较，不将模拟轨迹导入产品。

失败AC-03：原P1仅user_request即OBSERVABLE；P3错写交易关联、P4错写付款响应、P5错写订单结果。既有定义及固定代码引用以SPEC.json为准。OBSERVABLE指合同所需输入齐全可观察；部分字段存在只能PARTIAL，不能因自然语言说明缺身份却将整个合同标为OBSERVABLE。六例均缺完整权威输入，不得宣称任何P已满足/产品PASS。

## Allowed scope

Executor只可写本目录MAP.py、MAPPING.json、ATTEMPT_LEDGER.json、REPORT.md、evidence/，CURRENT仅可更新本任务state/phase；保留EXECUTING/Executor提交。MAP只标准库，读取H63 MEASUREMENT及固定事实、既有P定义；不import产品、H63 EXTRACT或CHECK，不执行工具。

H63全目录、原src/tests、历史工作区、冻结CONTRACT/SPEC/CHECK/VALIDATION_PLAN/BASELINE/SETUP_BASELINE与地图只读。原不相关未提交工作保持，BASELINE记本任务冻结时全部已有文件hash；CURRENT是显式新路由例外。新产物不覆盖原拒收证据。

## Acceptance criteria

### AC-01 — 保护和来源连续性

Given BASELINE；When VP01；Must observe原H63全部文件、旧保护材料/三源库、已有工作区hash不变，HEAD不变；新增文件仅本任务，冻结自文件保持。Mandatory: yes。

### AC-02 — 30个既有合同映射

Given SPEC及H63固定facts；When VP02和Evaluator逐项代码语义审阅；Must observe六例每项contract_name、contract_ref、input_status、fact_keys、missing_inputs、reason完整；引用事实确实PRESENT/AMBIGUOUS，缺失不造。P1=确认/订单绑定，P2=连续支付绑定，P3=执行身份，P4=来源/上下文策略，P5=收据/治理回放；明确缺权威输入，不用订单/支付响应替代P3/P4/P5。本任务不运行现有验证器对源作产品判定。Mandatory: yes。

### AC-03 — 保守结论与成本

Given MAPPING和账本；When VP02/03；Must observe至多一个有源依据的后续问题或STOP，REFERENCE_ONLY/TRANSCRIPT_ONLY，六个原限制保持；预算闭合、执行期五类外部调用均0；不升级产品/真实性/合规成熟度。Mandatory: yes。

### AC-04 — 判别器拒绝原错误

Given判别器及内存变异；When VP03；Must reject错误contract_ref、S01的P1 OBSERVABLE、P3以付款关联替代身份、删除缺失输入；原正常映射检查通过。自测不能替代Evaluator对30映射的语义审阅。Mandatory: yes。

## Validation plan

VP01保护；VP02映射/结论/预算；VP03变异自测。exact argv见冻结YAML。Executor用中央run_validation.py --mode executor产正式L2，Evaluator用--mode evaluator产L3，复核代码定义与30映射。结构validator在提交/接受/终态前运行。

## Authorization / Exclusions / Stop conditions

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

无网络、下载、模型、依赖安装、真实/模拟产品执行、支付、第二商城、适配器或外部消息。不得重跑H63样本提取或历史全工作区checker。60分钟/2L2/2映射版本任一耗尽即停；需要改事实、权威P语义、AC、范围、预算或权限即回Evaluator。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/14/20 CORE/ADAPTER；对象=映射修复合同；代码=MAP/CHECK与只读既有定义；Test=三VP+独立30映射语义核查；Evidence=新L2/L3与原源引用；before/after产品成熟度不变，身份/PSP/客户价值/合规unknown。
