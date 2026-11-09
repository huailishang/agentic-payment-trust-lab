# H41 Evaluator P0 Review

2026-09-30 下一包修订：H41 `PASS / NOT_CONFIRMED / STOP` 不变；地图 r68 已独立复现 Alipay adapter 对合成已签名通用 `error_response` 的 `0/1` 识别盲区，且官方 SDK 存在该外壳的签名原文分支。当前首选 H43 `CONTRACT_FROZEN / SINGLE / OFFLINE_ONLY`，合同为 [H43](../H43_ALIPAY_SIGNED_GATEWAY_ERROR_BOUNDARY_V1/CONTRACT.md)；旧 H42/B-16 草案暂缓。此裁决不声称 H41 原响应实际为通用错误，也不恢复任何外部调用预算。下文 H42“下一可执行候选”为当时判断，现被 r68 决策取代。

2026-09-30 截图补证：同一沙箱控制台截图现完整显示“支付宝公钥”，可见五行与本地指定文件逐段视觉一致；公钥来源疑点从 `NOT_VERIFIED` 收敛为 `CONSOLE_SCREENSHOT_VISUAL_MATCH`，但尚非控制台文本的机器级字节比对。H41 原响应未保留，无法因此倒推 `INVALID_RESPONSE` 原因或恢复一次请求预算。详见 [KEY_PROVENANCE_AUDIT](KEY_PROVENANCE_AUDIT.md)。下方 2026-09-29 结论中的“公钥来源未核对”为当时状态，不再作现行阻塞。

2026-09-29 后续只读核对：Human 指定文件确有可解析的“支付宝公钥”，H41 探针也确实使用了这一段；此前若表述为“没有公钥”应更正为“公钥与当前 Sandbox 应用的对应关系尚未由独立控制台来源核实”。详见 [KEY_PROVENANCE_AUDIT](KEY_PROVENANCE_AUDIT.md)。这不改变下方 H41 最终裁决，也不授权重试。

## 2026-09-29 P1 单次实测最终复核（最新结论）

Task ID: H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Impact verdict: NOT_APPLICABLE

## Final verdict

PASS

## L3 independent gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_evaluator_20260924/L3-GATE.json
- Validation plan: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml

该 L3 是 2026-09-24 对 P0 实现的独立验收，**不是**本次真实 Provider 响应的重放或验签；本次 P1 原始 bytes 按合同未保留，无法进行同响应 L3。下方 AC-06 只依据同次脱敏执行记录和受审代码裁决报告边界。

全局路线：A–D 已完成，E 仅有本地代表性闭环，F 是当前外部验证阶段；最终目标是证明 Agent 授权、交易动作及事后证据连续可信。战略第一缺口仍是 B-06：缺第二 Provider 的有效 Payment-Proof、支付状态及绑定实证。本轮 H41 属 measurement-only，不建设支付能力。相较之下，AP2 已有代表性官方链；B-16 的 Agent-facing 攻击验证虽有安全价值，却不能替代 Provider 证据。完成判据是一次固定诊断、可信分类及无越界；若取得签名错误响应才考虑后续 fixture，若无法验签则 STOP 本路线并重排下一可执行测量。

Task verdict: **PASS（仅有界测量执行与记录）**。Hypothesis: **NOT_CONFIRMED**。Project impact: **NOT_APPLICABLE**（one_off measurement；B-06 未缩小到可信 Provider/Payment-Proof 能力）。Continuation: **STOP H41 / SWITCH 下一可执行测量**。这不是“支付宝接口通过”或“签名失败已独立证实”：已记录的 `signature_verified=false` 来自受审探针；原始响应、签名按合同未落盘，Evaluator **无法复核，建议人工抽查**实际响应的细分原因，且不得为了抽查重发请求或扩张秘密留存。

独立核对：脱敏 JSON 与 REPORT 均记录 `attempt_count=1`、HTTP `200`、响应摘要 `e33d76604d9d1d9a32fddd71f8d9e79c911c7192d3812ae87cb4551979b28e17`、`UNVERIFIED_RESPONSE / INVALID_RESPONSE`、code/sub_code 均 null；固定 reservation 存在。REPORT 记载请求前本地 RSA-2048 配对及 RSA2 签验通过，但支付宝公钥来源为 `NOT_VERIFIED`，所以不能从本地密钥检查推断远端验签可信。受审探针/测试/独立检查器 SHA-256 与 P0 签收版本一致，7/7 保护 hash 一致，baseline HEAD 仍为 `7831d23`。中央 workflow 结构校验返回 OK，`git diff --check` 通过。`INVALID_RESPONSE` 是多种解析/验签异常的共同出口；证据不能区分缺签名、错误公钥、envelope 不符、重复键等。共享 parser/同进程观测不是独立第二验签者。未重新执行 live，也不把旧 P0 L3 记作本次远端响应的独立复现。

AC-01—05：沿用已独立签收的 P0 实现与守护线，本轮 hash 未漂移，**通过（继承）**。AC-06：实际分类、次数、脱敏证据与 STOP 报告齐备，**通过（仅报告/执行边界）**；其验收本来不要求响应验签成功。Provider 签名真实性、错误业务语义、支付成功、买家真实性、四维绑定均 **NOT_PROVEN**。H38 保持 `PARTIAL / LIVE_BLOCKED`；PCAC-AGENTPAY / PCAC-06、09、12、20 成熟度不升级。H41 的一次 HTTP 预算已消耗，固定 reservation 必须保留，`authorization_api_call=false`；不得换文件名、删预留、补参数、再试、造单或付款。

逐项裁决：AC-01 通过（保护 hash/范围）；AC-02 通过（既有 P0 独立入口门禁）；AC-03 通过（既有合成 RSA 正负例，不外推真实响应）；AC-04 通过（固定 reservation/单次预算）；AC-05 通过（脱敏 allowlist 与 P0 秘密标记检查）；AC-06 通过（P1 报告完整、假设单列）。

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_evaluator_20260924/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_evaluator_20260924/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_evaluator_20260924/RV-EV-01.stderr.log

此节仅索引既有 P0 独立证据；P1 独立复核以固定脱敏 evidence、reservation、hash、源码分类分支及当前授权路由的只读核对为限。

下一步预算判断：继续同类 Sandbox 盲探的边际信息价值低，且已触及单次授权边界；B-06 继续是战略缺口，但没有可直接执行的有效 fixture 与公钥来源证据，保持 `LIVE_BLOCKED`。选 B-16/X1 **Evaluator-owned measurement-only 设计**为下一可执行候选：先审计真实 Agent observation → action → governed gate 的接缝，确认现有 Attack Overlay `6/6` 仅为预声明字段覆盖，不等于面向 Agent 的提示/工具污染对抗证明。只测量接缝、可判定的未授权副作用及负对照；若发现重复共同断点才冻结能力包，若无可观测接缝则 STOP，不为比赛包装新模块。其 DRAFT 见 `docs/05_任务交接/H42_AGENT_FACING_ATTACK_SEAM_MEASUREMENT_V1/CONTRACT.md`；在设计和验证计划完成前不派 Executor，不新增网络/支付授权。若将来 Human 提供可核对的官方公钥来源与安全 fixture/新授权，再由 Evaluator 单独重评 B-06，而不是复活 H41 请求。

---

## 2026-09-29 P1 治理修复独立复核（当前结论）

全局位置：A–D 已关闭、E 有本地代表性闭环、F 正在验证外部 Provider；B-06 缺支付宝实际响应与后续有效 Payment-Proof 证据。H41 只测一次合成 HTTPS signed-error(已签名错误响应) 边界，不能证明支付成功或交易绑定。比赛规划与 B-16 攻击轨均不能替代当前 Provider 观测。

Verdict: **PASS / REPAIR_ACCEPTED / RESTORE_P1**，仅针对本轮 REPORT 治理修复；H41 P1 假设仍 **NOT_MEASURED**，项目影响 **NOT_APPLICABLE**。Executor 报告已把当前 Task ID 与 baseline `7831d232530c91825bb507a2a6d95b1de6a02c3b` 置于历史旧 baseline 之前，保留历史事实。Evaluator 使用已有含 PyYAML 的运行时独立执行中央 `validate_workflow.py --repo . --current CURRENT.md`，结果 `OK: v2.2 routing and required artifacts are structurally valid`。`git diff --check` 通过；H41 探针、测试、独立检查器 SHA-256 分别为 `09733850937776f5d286454504e01d54bdfebd0b4915e3189104b68583a19b69`、`b2d8bb9f546a2f421d6a895e5b86e57c2efba0193c60619b1a8061aa711323e5`、`46090bf1cc42b885bf26785adfb95e7be2167c83093680ed389e010d0242f2ca`，与此前批准值一致；固定 reservation 不存在。此次没有重跑 P0 L3，因为受审实现与检查器未改，本轮验收对象仅为报告当前标识。

Evaluator 恢复 `CURRENT.md` 的精确 `EXECUTING / Executor / H41_SINGLE_DIAGNOSTIC / authorization_api_call=true` tuple。该恢复只对应原已批准且未消耗的一次合成 Sandbox HTTPS 请求；无新密钥、造单、付款、重试、生产或提交推送授权。Executor 在真实密钥读取前重新执行合同前置检查，固定输出路径与预留约束必须通过；任何分类结果立即停止并更新 REPORT 回交。一次 signed business error(已签名业务错误) 也只关闭响应签名窄层，不改变 H38 `PARTIAL / LIVE_BLOCKED`。PCAC-AGENTPAY / PCAC-06、09、12、20 成熟度不升级。

下一步条件：若请求得到可验签错误响应，Evaluator 再测量其实际信息价值并决定是否继续安全 fixture(测试交易输入) 路线；若无签名、网络不确定或意外成功，则按原合同 STOP，不补第二次调用。B-16/X1 与比赛映射继续作为备选，不抢占这次已批准的低成本测量。

---

## 2026-09-29 P1 输入恢复后的结构阻塞（非最终验收）

Human 已提供既有 Sandbox APPID 与此前指定的本地密钥文件路径。Evaluator 只核对路径存在、是文件及大小，未读取密钥、签名或联网；不把本会话的输入提供视作 Provider 证据。现有 reservation 仍不存在，真实 HTTP attempt=0，原一次预算未消耗。

中央 `validate_workflow.py` 用已有 PyYAML 运行时执行后返回 `BLOCKING`：REPORT 首次可识别的 `Baseline HEAD` 仍是历史 `0b99f3d1f3db180a37bcb8e6512fb7849711ea72`，与 CURRENT 的 `7831d232530c91825bb507a2a6d95b1de6a02c3b` 不一致。这是报告当前快照标识/解析问题，未观察到产品实现或保护文件漂移；不能把校验失败当作 Provider 或密码学失败。此前两个 Python 运行时因缺 `yaml` 未能启动校验，不计为结构裁决。

Evaluator decision: **P1 暂停 / 治理修复交回 Executor**。`CURRENT.md` 的 `authorization_api_call` 暂设 false，精确 P1 授权 tuple 失效；不增加或消耗预算。Executor 在原 H41 报告顶部补当前 P1 的 Task ID 与 Baseline HEAD，保留 2026-09-23 历史记录，运行中央 validator 至 `OK`，更新报告本次检查结果，并交 Evaluator 复核。不得改产品、合同请求形状、密钥边界或用新任务绕过报告修复。Evaluator 复核通过后才恢复原一次调用授权；真实请求仍由 Executor 执行，并在任一分类结果后停止回交。

项目判断不变：A–D 已完成、E 本地闭环、F 当前；B-06 仍是第一瓶颈。比赛项目不改变优先级，B-16/X1 保持下一独立测量候选。PCAC-AGENTPAY / PCAC-06、09、12、20 在此轮无成熟度变化。

---

## 2026-09-29 P1 输入阻塞评估（非最终验收）

全局位置：项目要证明 Agent 交易在授权、身份、对象、来源、副作用与事后证据上连续可信。A–D 已关闭，E 只有本地代表性闭环；F 的 B-06 仍缺第二 Provider 的实际证据。H41 是 B-06 的窄层测量，不能替代有效 Payment-Proof、支付结果或四维绑定。B-16 横向攻击验证有独立价值，但现有固定负例已有基础，当前尚不能提供缺失的 Provider 观测。

Evaluator decision: **P1 未执行 / LOCAL_BLOCKED / 保持原一次预算**。这不是新的 `PASS`、`REJECTED` 或 Provider 实证。Executor 的 REPORT 记录 baseline gate 与 dry-run 均 exit 0；真实密钥读取、HTTP attempt、reservation 均为 0。2026-09-29 在当前会话仅检查变量是否存在：`AIPAY_APP_ID` 及三个既有 AIPAY 密钥变量均未设置；固定 reservation 路径不存在。未读取变量值、密钥文件或远端接口。本次独立检查支持“本会话仍缺执行输入”，不证明别的会话也缺失。H41 假设保持 `NOT_MEASURED`，H38 保持 `PARTIAL / LIVE_BLOCKED`；PCAC-AGENTPAY / PCAC-06、09、12、20 不升级 Provider 成熟度。

恢复条件：Human 将既有 Sandbox APPID 与此前指定的本地密钥文件绝对路径交给受控执行会话，不发送私钥正文。Executor 在原合同内重新完成输入/授权/保护 hash 预检；若通过，最多执行原预算中的一条固定合成 HTTPS 请求。任一分类结果均停止、更新 REPORT 并交 Evaluator；不得补第二次请求。若现有输入无法恢复，由 Evaluator 显式终止本次 P1 路由并重排瓶颈，首个离线候选是 B-16 的 X1 agent-facing(面向智能体) 攻击测量，而非直接建设新安全模块。

优先级判断：恢复既有输入的成本低，且一次请求能直接降低 B-06 的关键不确定性，因此暂不把比赛映射或 X1 提升为当前执行任务。此判断只保留已有预算，不新增网络、凭据或实现授权；`CURRENT.md` 仍处于 `EXECUTING / Executor`，等待输入或后续显式路由决策。两场比赛是独立消费者，赛题进度不改变主项目瓶颈。

---

## 2026-09-27 P1 基线漂移复核（当前结论）

Verdict: **PASS / BASELINE_REANCHORED / CONTINUE_P1**。Executor 的 `LOCAL_BLOCKED / BASELINE_HEAD_DRIFT` 符合冻结合同：真实 HTTP attempt、真实密钥读取、reservation 和一次预算消耗均为 0。

Evaluator 审核 `0b99f3d→7831d23`：该提交固化此前 H38–H41 已验收工作区，未改变 7 个保护文件、H41 探针、产品测试或独立检查器的受审 hash；Git hooksPath 指向中央 security-hooks，commit `git show --check` 与 security `audit-head` 通过。新 HEAD 上 H38 gate `12/12`、Alipay adapter `16/16`、observer `14/14`、独立反例 `7/7` 通过。H41 专项 `27/28`；唯一失败 `test_actual_current_p0_blocked` 明确要求实际 CURRENT 仍为 P0，在已批准 P1 后属于阶段性预期不适用，不是授权、安全或产品回归。旧 P0 的 28/28 证据仍只归属于当时 P0 状态。

接受 amendment `2026-09-27-a3`，把 CURRENT、CONTRACT、BASELINE 重新锚定到 `7831d232530c91825bb507a2a6d95b1de6a02c3b`。不重置或增加一次请求预算，不改变输入、地址、方法、秘密边界、分类或停止条件；P1 原授权继续有效。B-06、H38 `PARTIAL / LIVE_BLOCKED` 与 PCAC 成熟度均不变。

---

## 2026-09-24 最终 P0 签收与 P1 放行（当前结论）

Verdict: **PASS / RELEASE_P1**。Hypothesis: **NOT_MEASURED**。Project impact: **NOT_APPLICABLE**。H38 保持 **PARTIAL / LIVE_BLOCKED**。

全局路线仍为 A–D 完成、E 本地代表性闭环、F 当前；第一瓶颈仍是 B-06 缺支付宝第二 Provider 的实际证据。本轮 H41 是 measurement-only：只证明单次 signed-error 测量工具已准备好，不证明付款、有效 Payment-Proof、买家真实性、四维绑定或生产安全。AP2 扩展和 B-16 横向攻击保持 WATCH，因为它们不能替代当前 Provider 证据。

Evaluator 接受 amendment `2026-09-23-a2`。中央 `validate_workflow.py` 对当前任务包返回 `OK`；正式 evaluator-mode L3 为 **7/7 PASS**、mandatory failures=`0`，证据入口为 `evidence/r2_evaluator_20260924/L3-GATE.json` 与 `RV-EV-01`—`RV-EV-07`。本轮独立复核实际覆盖 H41 `28/28`、H38 授权闸门 `12/12`、Alipay adapter `16/16`、observer `14/14`、独立反例 `7/7`；保护文件及探针、测试、独立检查器 hash 全部一致，R1 HTTPError 响应丢失与 R2 v2.2 治理结构阻塞均关闭。复核期间真实网络、真实密钥读取、造单、付款、提交和推送均为 0。

AC-01—AC-06：P0 全部通过。PCAC-AGENTPAY / PCAC-06、09、12、20 仅在离线 signed-error 探针范围维持 M3 TESTED；Provider 实测、公钥来源、买家真实性、支付与绑定成熟度不升级。

按冻结合同单独放行 P1：CURRENT 必须且现已精确设置为 `EXECUTING / Executor / H41_SINGLE_DIAGNOSTIC / authorization_api_call: true`。Executor 最多执行一次固定合成 Sandbox HTTPS 请求；不得重试、补参数、创建交易、付款、读取 H38 fixture、扩大秘密输出、切换生产或真实资金。commit、push、history rewrite 继续禁止。

停止与回交条件：`SIGNED_BUSINESS_ERROR` 只关闭响应签名与可信错误分类这一窄层；`UNVERIFIED_RESPONSE`、`SIGNED_UNEXPECTED_SUCCESS`、`TRANSPORT_INCONCLUSIVE` 或 `LOCAL_BLOCKED` 均立即停止，不补第二次请求。任一结果都必须更新 REPORT 并交回 Evaluator，不能自行把 H38 标为 PASS。

---

## 2026-09-23 二次复核（当前结论）

R1: **CLOSED / REPAIR_ACCEPTED**。整体 P0 签收：**暂缓，任务包治理校验未通过**。P1 NOT RELEASED；Hypothesis: NOT_MEASURED。下文 2026-09-22 为首次复核历史。

项目目标仍是授权、支付动作及证据连续可信。地图 r62 的 A–D 完成、E 本地闭环、F 当前；B-06 缺支付宝实际响应证据。此次只修复测量工具，未取得 Provider 实证。AP2 扩展与横向攻击仍不能替代该证据；下一步先纠正本包交接结构，再决定单次 P1，禁止增加产品能力或继续堆离线案例。

### 评估前检查与 AC 逐条裁决

受审 HEAD 为 `0b99f3d1f3db180a37bcb8e6512fb7849711ea72`；7/7 保护 hash 一致。探针 `09733850937776f5d286454504e01d54bdfebd0b4915e3189104b68583a19b69`、测试 `b2d8bb9f546a2f421d6a895e5b86e57c2efba0193c60619b1a8061aa711323e5` 与 REPORT 相符；独立检查器 `46090bf1cc42b885bf26785adfb95e7be2167c83093680ed389e010d0242f2ca` 未变。以上为受审标识，尚非 P1 放行。

Evaluator 独立运行 H41 28、H38 授权 12、Alipay adapter 16、H38 evaluator 14，共 **70/70 通过**；原独立检查 **7/7 通过**。HTTPError 400/500 签名响应正确分类，unsigned 400 正确拒绝，状态码和摘要保留。新增测试覆盖资源关闭、读上限、读取失败/超时、篡改、意外成功、302 不读取不跟随及换名重试阻断。源码检查确认非 3xx 错误对象进入原 bytes 验签路径，没有把 HTTP status 当成签名成立。

AC-01/02/03/04/05：本轮离线实现证据通过；AC-06：报告准确区分 P0 与未测量 P1，但正式交接结构尚需下述 R2 修正。默认 dry-run 为 key_reads=0、attempts=0，git diff --check 通过。未跑全仓，继承 Windows WebShop 路径失败不宣称已修复。实际密钥读取/网络/付款/造单/提交/推送均为零。

### R2 / P2 — 评估者任务包不符合所声明 v2.2，阻止正式签收

这是既有治理文件的问题，不是 Executor 本轮 R1 引入。结构校验器真实执行 exit 1：CURRENT 使用未支持的 `CHANGES_REQUIRED`、`measurement-only`；合同缺可识别的 allowed scope / exclusions / stop conditions / strategic basis，Task kind 行还因附带说明不被字段解析器识别，缺具体 Validation plan file。进一步检查计划可见 VP-01/06/07 只有 kind/expected，没有 runner 必需的 command；不能把本次手工复跑包装成自动 L3 Gate PASS。

归属 **Evaluator**，禁止退回 Executor 改已通过的探针。补齐机器可读结构与证据引用应保留原假设、AC、请求形状、预算、保护文件、零 live 授权；详见 `EVALUATOR_GOVERNANCE_REPAIR.md`。不得为通过校验修改中央 validator 或伪造 L2/L3。流程通过后才可单独批准 hash 并切换 P1。

### 独立证据

- `evidence/review_20260923/RV-EV-01.*`：未修改的 EVALUATOR_CHECK.py，exit 0，7/7 与保护 hash。
- `evidence/review_20260923/RV-EV-02.*`：中央 validate_workflow.py 对复核前 CURRENT 的原始输出，exit 1。
- 四组专项命令同 VALIDATION_PLAN 的 VP-02—05，使用既有 bundled Python 3.12.14、PYTHONPATH=src，各 exit 0；本次终端独立复跑，未伪称已生成 runner 门禁。
- bundled Python 缺 yaml、PATH 中 conda 不可用；最终用既有系统 Python 运行中央校验器，未安装依赖。证据目录初次创建被沙箱拒绝，获准后保存上述输出。

## 项目影响裁决

Impact verdict: NOT_APPLICABLE

R1 测量准备缺陷已关闭，B-06 实证瓶颈尚未移动；治理交接阻塞明确化。PCAC-AGENTPAY / PCAC-06、09、12、20：仅本轮离线探针范围达到 M3 TESTED 的独立测试证据；不升级 Provider 实测、公钥来源、买家真实性、付款或绑定结论。下一行动为同包 Evaluator 治理修复，完成后 CONTINUE 单次 P1；P1 无签名、意外成功、网络不确定均 STOP、不重试。H38 保持 PARTIAL / LIVE_BLOCKED。

---

Date: 2026-09-22
Verdict: **CHANGES_REQUIRED**
Phase: **P0_OFFLINE_ONLY**; P1 NOT RELEASED
Hypothesis: NOT_MEASURED; H38 remains PARTIAL / LIVE_BLOCKED.

## 全局位置

目标是授权、支付动作和证据连续可信。A–D 完成、E 本地闭环、F 当前。第一瓶颈 B-06 是支付宝实际响应证据不足；AP2 扩展与攻击 WATCH 无法替代该测量。本轮检查 H41 离线探针能否可靠支撑一次受限请求。修复以下证据丢失后再验收 P0；本轮不切换 P1、不增加调用预算。

## R1 / P2 — HTTP 错误响应体被丢弃，错误归为网络不确定

位置：`scripts/h41_alipay_signed_error_probe.py:48` 和 `:141`。

`urllib` opener 对 HTTP 400/500 等错误状态抛出 `HTTPError`，其中可以携带完整响应体。当前 transport 没有读取该响应，main 的统一异常分支直接写 `TRANSPORT_INCONCLUSIVE`，使 http_status、response_sha256 丢失，且从未执行验签。

这与合同把 TRANSPORT_INCONCLUSIVE 限定为“无可用响应”的边界不符。H41 的任务恰好是测量错误响应；一次预算如果遇到这种返回，就会丢失已经拿到的可验证证据，且不能重试。本发现不声称支付宝必然以 HTTP 400/500 返回业务错误，只证明探针对允许出现的 HTTP 结果不能正确分类。

### 独立复现

`EVALUATOR_CHECK.py` 使用独立生成的临时 RSA-2048 密钥、真实签名字节和独立 CURRENT 夹具；实际调用 main、transport、分类器，只替换 urllib opener 与密钥检查输入。没有替换密码学验签或分类函数。

| 输入 | 期望 | 实测 |
|---|---|---|
| 签名错误响应，HTTP 200 | SIGNED_BUSINESS_ERROR / 验签 true | PASS |
| 同类签名响应，HTTPError 400 | SIGNED_BUSINESS_ERROR / status=400 / 有摘要 | TRANSPORT_INCONCLUSIVE / status=null / 无摘要 / 未验签 |
| 同类签名响应，HTTPError 500 | SIGNED_BUSINESS_ERROR / status=500 / 有摘要 | 同上 |
| 无签名 JSON，HTTPError 400 | UNVERIFIED_RESPONSE / status=400 / 有摘要 | 同上 |

三项反例各仅一次 fake attempt，reservation 均保留；未发生真实请求或秘密泄漏。

### 最小修复要求

在 transport 边界区分“收到 HTTP 错误响应”和“无可用响应”。对可读取的非重定向 HTTPError 响应体，按同样的 1,000,001 字节读取上限进入既有内存分类链，保留 HTTP status 和摘要，并正确关闭响应资源。不得直接把 HTTP 错误状态当作签名成立；无签名/篡改/超长仍 UNVERIFIED_RESPONSE，读取失败/超时仍停止。

保持拒绝重定向、零重试和固定 reservation；不要通过改为无限读取或增加网络调用来补证据。扩展实际 main/transport 测试覆盖签名/无签名 HTTPError、响应体读取失败/超长及 3xx 不跟随。修改只限原合同的 H41 探针、产品测试与 REPORT，保护 EVALUATOR_CHECK.py。

## 本轮验证

Evaluator 使用既有 Python 3.12.14，设置 PYTHONPATH=src；未安装依赖。

| 检查 | 结果 |
|---|---|
| H41 产品专项 | 19/19 PASS，exit 0 |
| H38 授权专项 | 12/12 PASS，exit 0 |
| Alipay adapter 专项 | 16/16 PASS，exit 0 |
| H38 evaluator 专项 | 14/14 PASS，exit 0 |
| `python docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/EVALUATOR_CHECK.py` | 4/7 PASS，exit 1；3 项上述反例 |
| BASELINE 保护 hash | 7/7 一致 |
| `git diff --check` | PASS |

独立检查中 wrong phase 在 inspect/sign/reservation/network 前拒绝；签名后撤销在 reservation/network 前拒绝；篡改响应不通过；所有用例 stdout/stderr/evidence 无合成秘密标记。

受审探针 hash：`784931d6b9d48987079db099f34f35096c4479116e57faae77e496c14da125eb`。
受审产品测试 hash：`2ebba3671ebd3e9a6ee3dd7d492610f25533f565b66817c45be0b74efc5d861d`。
两者均与 REPORT 一致。以上 hash 仅标识受审版本，不是 P1 批准。

AC-01/02：已有边界证据通过。AC-03/06：HTTP 错误响应证据分类不完整，验收暂不通过。AC-04/05：已验证的单次调用、预留、脱敏路径通过，修复不得回退。无全仓测试声明；继承 Windows WebShop 失败保持登记。

PCAC-AGENTPAY / PCAC-06、09、12、20：P0 实现及测试存在，但 M3 独立验收暂缓；无 Provider 实测、付款成功、买家真实性或绑定结论。

## 交回

Executor 在原 H41 P0 合同内修复 R1，跑四组专项及独立检查，更新 REPORT/hash 后交回。P1 仍未放行；真实调用、真实密钥读取、commit/push 均为零。不得另开研究包或恢复 H38 live。
