# H43 Frozen Contract — Signed Alipay Gateway Error Boundary

Task ID: `H43_ALIPAY_SIGNED_GATEWAY_ERROR_BOUNDARY_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: `capability_experiment`
Risk: `L2`（离线安全解析边界；无外部调用）
Contract state: `CONTRACT_FROZEN`
Dispatch mode: `SINGLE`
Date: 2026-09-30
Baseline HEAD: `7831d232530c91825bb507a2a6d95b1de6a02c3b`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-30-r69`（关闭后治理元数据同步；执行时冻结地图为 r68，AC 与预算未变）
Active bottleneck: `B-06`
Hypothesis: `H-43`
Validation plan file: `docs/05_任务交接/H43_ALIPAY_SIGNED_GATEWAY_ERROR_BOUNDARY_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 为什么此刻做

项目要证明 Agent 授权、交易动作和 Provider(外部支付方)证据连续可信。A–D 已完成、E 本地代表性闭环、F 当前；B-06 的首个支付宝 Sandbox(沙箱)有效 Payment-Proof(支付凭证)与四维绑定仍缺。H41 单次合成请求已消耗，HTTP 200 被统一归为 `INVALID_RESPONSE`；没有原始响应，**不得声称 H41 实际返回 `error_response`**，也不得重试。控制台截图已使本地支付宝公钥与该 Sandbox 应用形成强视觉对应证据，公钥来源不再是本包主问题。

Evaluator 独立构造临时 RSA-2048 已签名 `error_response`，当前 `verify_response` 返回 `INVALID`、未验签事实，代表性基线 **0/1**。代码的 `signed_response_parts` 只允许接口专属 `alipay_aipay_agent_payment_verify_response`；支付宝官方 `payment.verify` 文档给出接口专属异常示例，官方 SDK 的 `parserJSONSignSource` 则分别提取接口专属外壳和通用 `error_response` 的原始签名内容。来源：

- [官方 payment.verify 接口文档](https://aipay.alipay.com/docs/ai-receive/api-list/alipay-aipay-agent-payment-verify.html)，2026-09-30 只读观察；页面标注更新 2026-09-27。
- [支付宝官方 PHP SDK 的响应签名来源提取](https://github.com/alipay/alipay-sdk-php-all/blob/master/v2/aop/AopCertClient.php)，2026-09-30 只读观察，`parserJSONSignSource` 对 `error_response` 有独立分支；这是外部语义参考，不能把动态 master 当不可变执行依赖。本包验收由冻结的本地合成检查器确定。

第一备选 B-16/X1 Agent-facing(面向智能体)攻击测量值得做，但不能消除当前 B-06 的外部响应盲区；继续同类 live 盲探既违反 H41 单次预算又难解释结果。此包用零外部调用、低成本的最小解析扩展先关掉已证实的本地盲区，完成后重新评估安全 fixture(有效测试交易输入) 路线，而不是自动再请求 Sandbox。

## One hypothesis and one principal change

假设：在保留现有接口专属响应验签语义的前提下，仅为 Alipay adapter(适配器)增加严格的、已签名通用 `error_response` 识别，能将合法错误从 `INVALID` 改为“**只可信为 Provider 错误**”，并使错钥、篡改、无签名、重复键、双外壳等继续 fail closed(失败即关闭)。

唯一 principal change(主要改动)：`verify_response` 的离线通用错误外壳解析/验签分支及其直接测试。不得把通用错误变成 `VALID`、`active=true`、绑定通过或支付成功；不得扩张 H41 已冻结的 `signed_response_parts` 方法专属语义。

## Measured boundary and budget

- Measurement status: `measured`（合成 RSA 反例）；真实 H41 原响应类型 `unknown`。
- Metric baseline: 同一合成已签名通用网关错误可安全识别 `0/1`；目标 `1/1`。
- Primary metric: 同一冻结合成 signed generic gateway error(已签名通用网关错误)由 `verify_response` 安全识别，before `0/1`，target `1/1`。
- Negative guardrails: 5 类坏错误外壳全部 `INVALID` 且签名事实 false；接口专属已签名错误原行为保留；通用 `code=10000` 不能成为有效支付；H41 解析入口仍拒绝通用外壳。
- Estimated affected scope: 所有进入当前 adapter 的通用网关错误；真实发生率 unknown，不把 H41 归因于此。
- Expected project impact: 本地 B-06 响应证据分类盲区缩小；不声称 live Provider、Payment-Proof 或绑定改善。
- Cost: 零网络/沙箱额度、零真实密钥、低计算与小范围代码审查；最多两次正式 L2 提交门禁，L1 本地修复可在同一合同内进行。不能以失败为由改变边界或追加 live。
- Attempt mode: `SEQUENTIAL`；并发波次、外部 attempt ledger 均 `NOT_APPLICABLE`。
- Rollback condition: 任一无效/未签名响应被记录为已验签，通用错误触发 `VALID`/绑定/副作用，旧接口专属正负例回退，或保护 hash/授权越界。
- Next-round value: 若通过，仅评估一次安全 fixture 获取路线；如果无安全路径，B-06 继续 `LIVE_BLOCKED` 并可切 B-16/X1，不连续堆本地解析 Case。

## Acceptance criteria

### AC-01 — 冻结基线、授权和范围

HEAD 必须等于冻结 baseline；`BASELINE.json` 中 H41 探针、H38 探针/观察器与独立检查器 hash 不变；仅修改下面允许的 adapter、直接产品测试和 REPORT/evidence。`CURRENT.md` 的 API、commit、push、history rewrite 授权全部为 false。L2/L3 `VP-01` 必须 exit 0，Evaluator 另审 live diff。

### AC-02 — 正例只形成可信错误事实

临时 RSA-2048 私钥对原始 `error_response` JSON 子串做 RSA2 签名；同一公钥调用 `verify_response`，须得到 `status=PROVIDER_ERROR`、`provider_response_signature_verified=true`、`reason_codes=[SIGNED_GATEWAY_ERROR]`、`active=null`、`binding_checks_passed=[]`。不得出现 `VALID`、支付成功、可信绑定或原始错误信息泄漏。`VP-02/03` 必须 exit 0。

### AC-03 — 保留接口专属语义

现有接口专属签名成功/业务错误、金额与绑定正负例保持；接口专属签名错误仍 `PROVIDER_ERROR` 且旧 `reason_codes=[PROVIDER_ERROR]`。不修改 `signed_response_parts` 对通用外壳的拒绝语义，也不改 H41 探针。`VP-02/03` 必须 exit 0。

### AC-04 — 通用外壳负例 fail closed

错公钥、签名后篡改、无签名、重复 JSON 键、同时含接口专属与通用外壳，都须 `INVALID`、签名事实 false、无绑定；已签名通用外壳中 `code=10000` 也不得成为 `VALID`。合成敏感标记不得进入 fact。`VP-03` 必须 exit 0。

### AC-05 — 回归与秘密边界

H41 探针测试、H38 response observer(响应观察器)测试与 adapter 专项通过；无真实密钥读取、HTTP、造单、付款或生产切换。`VP-03/04` 必须 exit 0；任何回归先在原范围修复，不能改 H38/H41 代码绕过。

### AC-06 — 可审计交付、不外推

REPORT 给出逐项命令/退出码、前后 `0/1→1/1`、保护/受审 hash、变更 diff 与残余风险；明确“不能证明 H41 实际响应外壳或真实支付能力”。L2 `PASS` 才可 `SUBMITTED_FOR_REVIEW`，之后由 Evaluator 另跑 L3；不得由 Executor 宣布项目 `IMPROVED` 或放行 live。

## Allowed scope

- May modify: `src/agentic_payment_experiment/adapters/alipay_agent_pay_sandbox.py`、`tests/test_alipay_agent_pay_sandbox.py`、本包 `REPORT.md`。
- May add: 本包 `evidence/` 中的 L2 原始证据和任务差异快照；不新增通用安全模块或生产依赖。
- Frozen Evaluator files: `CONTRACT.md`、`VALIDATION_PLAN.yaml`、`BASELINE.json`、`EVALUATOR_CHECK.py`、`GOVERNANCE_CHECK.py`、`REVIEW.md`、项目地图、`CURRENT.md` 不由 Executor 修改。
- Inherited dirty worktree: CURRENT、地图、H41 治理文件及 `competition/` 已有或并行改动均属非本任务；保持原样且 unstaged。

## Exclusions / 禁止事项

API/沙箱调用、重复 H41、读取本地真实密钥文件、账户/私钥截图处理、造单/付款/退款/履约、生产网关、安装 SDK/依赖、执行官方支付脚本、修改 H38/H40/H41 代码或证据、提交/推送/改写历史，预算全部为 0。禁止持久化原始真实响应、签名或秘密。只允许临时合成 RSA 测试材料。

## Validation plan and entry

冻结计划：`docs/05_任务交接/H43_ALIPAY_SIGNED_GATEWAY_ERROR_BOUNDARY_V1/VALIDATION_PLAN.yaml`。`VP-01` 审 baseline/hash，`VP-02` 跑 adapter 测试，`VP-03` 跑预置独立反例，`VP-04` 跑 H41/H38 观察器回归及 diff check。Executor 在运行 L2 前以 `H43_TEST_PYTHON` 指向**现有**含 cryptography 的测试运行时；中央 runner 用已有含 PyYAML 的 Python 执行，不安装依赖。Evaluator L3 用同一冻结计划另存 `RV-EV-*`，并人工核实代码、范围和授权。预置 checker 的 `before` 已在原基线独立运行 exit 0；`after` 必须由 Executor 修复后通过。

## Stop conditions

若源代码证明 `error_response` 无法在此协议边界安全验签、反例无法实现而不改旧 parser 语义、正式 L2 两次仍有 mandatory failure、需改保护文件/合同/AC/预算、或出现任何外部调用需求，立即 STOP 回 Evaluator。通过后也 STOP，不自动进入 H38 live；下一步由 Evaluator 比较安全 fixture 路线和 B-16/X1 的预期价值。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_before: M3 TESTED for method-specific offline response only
  maturity_after_target: M3 TESTED for bounded generic signed gateway-error classification
  Test: VP-02, VP-03, VP-04
  Evidence: L2/L3 EV and RV-EV triplets, synthetic RSA checker, adapter tests
  residual_risk: H41 raw response unavailable; valid payment proof, buyer authenticity, live provider and four-way binding not proven
```
