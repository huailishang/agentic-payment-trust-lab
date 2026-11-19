# H71R2：归档全生命周期与公共门禁修复长包

Task ID: H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Contract state: CONTRACT_FROZEN
Baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Validation plan file: docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/VALIDATION_PLAN.yaml
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-13-r117
Active bottleneck: B-21
Hypothesis: H-71R2
Dispatch mode: SINGLE

## Strategic basis / 战略依据

项目验证授权→绑定→执行/恢复→审计的信任链；A–D本地关闭、E受控本地闭合、F当前。H71R矩阵、正文引用、历史UNKNOWN与原部分读取问题已修好；原生Windows独立六检查、11探针/9安全/74回归通过。但原合同第4项的归档摘要读取故障仍使函数抛出、整个结果丢失，第5项的公共L2被自建门禁替代，整包REJECTED。

本包继承B-21取证方向，只完成候选采集器从输出准备到归档收尾的失败保真，并真实走既有公共门禁；不修改公共工作流或再设计验证器。先修这两项，比重新生成已正确矩阵、增加支付Case或重开H67更有收益。原H68运行授权已于2026-11-13T00:59:06Z过期，无运行API/下载/监听权限可继承。

Metric baseline: 摘要rb读取PermissionError可复现无返回元数据；已有目标+opener失败会混入旧文件摘要；原公共L2不存在。正向成果和11/9/74保留。
Expected project impact: 修复取证闭环和交接资格，impact=NOT_APPLICABLE，不增加外部成熟度。
Expected material cost: 120主动分钟/3小时墙钟、2实现版本/3正式L2/1独立L3；零新增网络/下载/API/安装/服务/浏览器/环境/会话/付款/提交推送。
Rollback condition: 保持H71/H71R及正确投影原件；若不能可靠返回收尾失败结果或不能生成标准公共门禁，停止并报告BLOCKED，不补造旧输出。

## Single objective / 唯一目标

在一个离线包中闭合归档采集的全生命周期，并以合法公共L2/L3验收：旧文件不能误归本次尝试，准备/读/写/摘要/属性/关闭故障均不抹去已观察事实。唯一主要实现变化是归档失败保真；公共门禁直接使用原工具，不新建代码替代。

## Execution steps / 六步连续执行

1. 读H71R REVIEW/候选快照分类、独立文件反例和INPUT_SEAL。复用已正确EVIDENCE_CORRECTION/CORRECTED_MATRIX及三GET，不重新生成、修改或测量；核原件与冻结保护。
2. 仅将原H71R纯采集原语作为新RUN.py的起点。在调用opener前独占创建本次输出（例如xb/O_EXCL）；已存在目标或不可归档时不发起opener，不覆盖旧字节。声明所有权；不得通过摘要把既有文件带入本次。
3. 统一保护流关闭和归档收尾。摘要/属性读取失败时返回保留的HTTP状态、观察/计费字节、明确UNKNOWN摘要状态和错误类别；禁止异常携带私有路径向外抛出。允许增量摘要避免收尾重读，但必须对实际归档字节负责。主错误和关闭错误分别保留，不能因清理覆盖主错误或误报已关闭。
4. 连续运行原11冻结探针和9个归档生命周期探针，覆盖已有目标、输出准备、短写/flush、摘要/属性故障、单/双关闭故障；保留9安全/原生Windows74守护。不修改驱动/旧产品。预算内修新RUN并保留失败证据，不逐步交Human。
5. 用唯一公共runner执行完整VALIDATION_PLAN，原始三件套与标准Gate真实落盘。精确命令见SCHEMA_GUIDE。若WSL没有python，仅在该命令环境修正PATH/隔离别名，或使用已有原生Python；不改冻结argv，不复制/自建runner，不手写/转换元数据。公共runner或capture失败就保留失败，按同一预算修环境，不声称L2通过。
6. 原样完成REPORT标准字段和EV索引，运行公共validate_workflow及CHECK submission均退出0，再以SUBMITTED_FOR_REVIEW申请一次独立L3。Executor保持EXECUTING / Executor，由Evaluator确认资格后更新READY_FOR_REVIEW；不能自转角色。独立验收只复现离线测试，不新增外部动作。

## Acceptance criteria

### AC-01 — 原件与已通过成果保持

旧H71R/H71、候选快照分类、错误/自建门禁、旧矩阵/纠正投影、产品/旧测试保持；INPUT_SEAL绑定已通过投影与旧实现。不追认旧任务通过，不补旧L2，三GET与历史UNKNOWN不丢失。

### AC-02 — 输出归属与准备

opener前已证明能独占保存本次数据；已有目标保持字节不变且opener调用0。输出无法准备时返回OUTPUT_PREPARE，仅归属本次的观察/归档为0、摘要null且NOT_OWNED；不把已有文件摘要归当前。独占创建是原子动作，不仅exists后再wb覆盖。

### AC-03 — 全生命周期失败保真

正文/flush/关闭/摘要/属性故障均返回结构化结果，不丢已获HTTP状态/已观察与计费字节。摘要无法证明时为null/UNAVAILABLE，不能伪造空SHA或完整正文；主错误与清理错误分别列出。关闭失败如实response_closed=false。可完全避开事后摘要重读，但必须正确处理写失败与实际归档量。只返回错误类别/阶段，不包含异常消息或私有路径。

### AC-04 — 原传输边界与独立驱动

原11探针及本包9生命周期探针全部通过；继续保留EOF、读取上限、失败read保守计费、HTTP状态和单次opener/不跟随重定向。不得为修文件状态削弱原保护。独立Evaluator原生Windows验证原9安全/74回归；无法复核就不能PASS。

### AC-05 — 合法公共门禁与统一交接

最终正式L2必须由原run_validation.py/capture_evidence.py生成，标准schema/AC映射/argv/cwd/摘要可由原结构验证器接受；本包不产生另一套runner。L2 PASS与提交时validate_workflow=0、CHECK submission=0同时满足才申请Evaluator；不得以L3诊断代替缺失L2、不得先接受后修结构。保留失败/原始输出，预算内三次正式L2。

### AC-06 — 范围、成本与授权

120主动分钟/3小时墙钟、2实现/3L2/1L3，追加账本失败照计；全部外部动作和提交推送0。只修新包采集实现/结果/报告/证据，原工具与冻结输入不变。原运行截止已过，不自动恢复任何下载/凭据权限。

## Allowed scope / 允许范围

只新增本包RUN.py、RESULT.json、REPORT.md、ATTEMPT_LEDGER.jsonl、evidence/、versions/；CURRENT仅正常执行与申请交接字段。CHECK/BASE_CHECK/PROBES_LEGACY/PROBES_LIFECYCLE/INPUT_SEAL/SCHEMA_GUIDE/合同/计划/基线不可改。只读旧投影与旧源码，不复制私有密钥。

## Exclusions / 排除

不修改产品/旧测试/旧报告/旧门禁或架构；不新建/转换Gate和元数据，不执行旧自建run_l2.py；不研究新框架、下载CLI、启服务、调用API、重取样或补建沙箱，不再修改已正确矩阵。不把归档修复写成外部支付/真实身份保证。

## Validation plan / 验证计划

七项完整计划：保护/封存输入与RESULT、原11探针、新9生命周期探针、原9安全、原74回归、预算。门禁完成后另行CHECK submission和公共validate_workflow，避免在Gate尚未生成时循环验证。Evaluator先结构验资格、再保留不可变快照、再一次独立L3与逐AC审阅；不重演H71R接受顺序错误。

## Authorization / 权限

authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false

安装/服务/浏览器/测试付款全部false。只读已有材料与临时离线故障注入有充分授权，无待补Human事实。

## Stop conditions / 停止条件

任何新网络/权限、原件漂移、预算用尽、需改冻结AC/驱动/公共工具或不能生成公共门禁即停止；不得用自建证据绕过。普通本包实现/报告/环境解析修复在预算内连续完成，不逐步骤询问Human。

## Project impact and continuation / 后续

impact=NOT_APPLICABLE。闭合后STOP同类取证扩例；下一方向回到外部入口，但原截止过期、历史下载余额未知，须先形成明确的新运行条件/授权决定，不自动执行或换平台。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-06/12/15/20；单取证链CORE/ADAPTER/EVIDENCE_ONLY；before=收尾信息丢失/门禁不合格，after仅Test/Evidence修复；不提升支付/强认证/密钥治理/签名信任源或合规成熟度。
