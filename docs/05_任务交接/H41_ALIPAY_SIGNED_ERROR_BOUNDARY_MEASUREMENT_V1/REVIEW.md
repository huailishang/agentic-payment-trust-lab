# H41 Evaluator P0 Review

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
