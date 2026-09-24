# Frozen Capability Contract

Task ID: `H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1`
Task name: Alipay Agent Pay Sandbox First External Verification Slice
Task kind: `capability_experiment`
Contract state: `CONTRACT_FROZEN`
Evaluator amendment: `2026-09-20-a1`（下文补充条款优先；未扩大外部调用权限）
Baseline HEAD: `2b57248af464623402a71d65a2098244819519e3`
Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`
Map revision: `2026-09-19-r55`
Active bottleneck: `B-06`
Hypothesis: `H-38`
Metric baseline: `live external payment-provider verification evidence = ABSENT`
Estimated affected scope: `B-06 first live Sandbox provider slice; no Trust Core expansion`
Expected project impact: `ABSENT → FIRST_LIVE_SANDBOX_PROVIDER_SLICE`
Rollback condition: `any requirement for production endpoint/credential, real funds, new dependency, Trust Core change, or secret-unsafe evidence`
Dispatch mode: `SINGLE`
Validation plan file: `docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/VALIDATION_PLAN.yaml`

## Strategic basis / 战略依据

H-37 已由 Evaluator 独立 L3 `8/8 PASS`，使 AP2 official two-hop cryptographic/delegation runtime verification 从 `ABSENT` 变成 `BOUNDED_EXECUTABLE_SLICE`。

当前 B-06 第一断点已经前移：第二个真实外部 Sandbox/Provider 能否产生 provider-observed(由外部支付方实际返回) 的支付凭证验证证据，并进入现有 Trust / Trace 边界。

继续 AP2 Checkout/Payment typed semantics 或 Receipt 保持 WATCH；本任务优先验证第二个 Provider，判断当前 Trust Control Plane 是否具有协议中立性。

## Human authorization / Human 授权

Human 于 2026-09-19 明确要求“支付宝相关任务布置好，让执行者去执行”。本合同将此解释为仅授权以下边界：

```text
sandbox network/API              true
sandbox-only credential use      true
sandbox simulated transaction    true
payment-proof verification       true
sandbox callback receiver        false
production Alipay                false
production credential / PII      false
real funds                       false
dependency install               false
commit                           false
push                             false
history rewrite                  false
```

授权只适用于支付宝 Agent Pay **Sandbox**。不得自动升级到生产环境。

## Public official contract / 官方公开合同

Evaluator 于 2026-09-19 复核支付宝 Agent Pay 官方资料：

- `https://aipay.alipay.com/products/agent-pay`
- `https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html`
- `https://aipay.alipay.com/docs/ai-receive/api-list/alipay-aipay-agent-payment-verify.html`

冻结外部事实：
- Sandbox gateway: `https://openapi-sandbox.dl.alipaydev.com/gateway.do`
- Sandbox 不使用真实资金；
- Machine Pay 使用 `402 Payment Required` / `Payment-Needed` / `Payment-Proof`；
- 支付凭证验证 API：`alipay.aipay.agent.payment.verify`；
- 请求关键字段：`trade_no`、`payment_proof`、可选 `client_session`；
- 请求签名算法使用 RSA2；
- provider response 必须验签，不能只看 HTTP / code；
- 第一 slice 不包含 callback / fulfillment confirm / refund / production payment。

## Observable objective / 可观察目标

形成第一条支付宝 Sandbox provider verification slice：

```text
sandbox trade_no + Payment-Proof
        ↓
RSA2-signed sandbox request
        ↓
alipay.aipay.agent.payment.verify
        ↓
verified provider response
        ↓
trade/order/resource/amount binding
        ↓
minimal neutral external verification fact
```

只回答一个问题：

> 外部支付宝 Sandbox 能否真实验证支付凭证，并把“有效 / 无效 / 缺证据 / provider error”以最小事实进入本项目，而不把支付宝业务状态复制进 Trust Core。

## Allowed scope / 允许改动范围

允许新增/修改仅限：
- `src/agentic_payment_experiment/adapters/alipay_agent_pay_sandbox.py`；
- `src/agentic_payment_experiment/adapters/__init__.py`：仅追加 H-38 export；
- `tests/test_alipay_agent_pay_sandbox.py`；
- `scripts/h38_alipay_sandbox_probe.py`；
- 本 H-38 task package 下的 Executor-owned REPORT/evidence。

## Exclusions and forbidden side effects / 明确排除

禁止修改 `trusted_execution/**`、既有 AP2 adapter、payment lifecycle、trace、policy、identity core；禁止 production Alipay、production credential/PII、real funds、callback receiver、新依赖安装、commit/push/history rewrite。

## Single principal change / 唯一主要改动

新增极薄 provider adapter：

`src/agentic_payment_experiment/adapters/alipay_agent_pay_sandbox.py`

允许附带：
- `src/agentic_payment_experiment/adapters/__init__.py`：只追加 export；
- `tests/test_alipay_agent_pay_sandbox.py`：offline boundary tests；
- `scripts/h38_alipay_sandbox_probe.py`：仅任务级 Sandbox probe，读取 env secret，不把 secret 写日志/文件。

不得修改 `trusted_execution/**`、既有 AP2 adapter、payment lifecycle、trace、policy、identity core。

## Frozen public behavior / 冻结行为

产品 adapter 应输出最小事实，至少包含：

```text
status: VALID | INVALID | MISSING_EVIDENCE | PROVIDER_ERROR
provider: ALIPAY_AGENT_PAY_SANDBOX
method: alipay.aipay.agent.payment.verify
trade_no_sha256
active
binding_checks_requested
binding_checks_passed
provider_response_signature_verified
reason_codes
```

不得落盘：
- merchant private key；
- Alipay private material；
- raw password；
- full Payment-Proof；
- raw client_session；
- raw provider signed response if it contains sensitive material。

允许仅保存不可逆 digest / sanitized fields。

## Credential boundary / 凭据边界

Executor 只可从 environment / secret store 读取。推荐变量名：

```text
AIPAY_APP_ID
AIPAY_PRIVATE_PKCS_KEY
AIPAY_ALIPAY_PUBLIC_KEY

H38_TRADE_NO
H38_PAYMENT_PROOF
H38_CLIENT_SESSION
H38_EXPECTED_OUT_TRADE_NO
H38_EXPECTED_AMOUNT
H38_EXPECTED_RESOURCE_ID
```

checker 只判断“存在/不存在”，不得打印 value。

如果前三个 Sandbox credential 或 live fixture 缺失：
- 不得编造；
- 不得切 production endpoint；
- 不得把密钥写到文件；
- Executor 立即以 `BLOCKED` 报告缺少哪一类输入，保留已完成的 offline 实现/测试。

允许使用支付宝官方 Sandbox App / Sandbox test account 创建模拟交易来取得 fixture；如果必须 Human 交互完成 Sandbox App 支付，Executor 停在该交互点，不得绕过。

## Dependency boundary / 依赖边界

本任务**不批准安装新依赖**。

当前系统 `cryptography==41.0.7` 可用于 RSA2 request signing / provider response signature verification。若实现必须安装 Alipay SDK、npm Skill 或其他包，立即停回 Evaluator，不得自动安装。

## Acceptance criteria

- AC-01：Sandbox-only credential boundary；secret 不进 Git/log/evidence。
- AC-02：只能调用冻结 Sandbox gateway + `alipay.aipay.agent.payment.verify`。
- AC-03：至少 1 个 provider-observed valid proof，且 provider response signature verified。
- AC-04：至少 1 个保持 64-char 形状但篡改的 Payment-Proof，由 provider/adapter fail closed。
- AC-05：expected trade/order/resource/amount binding 不允许静默跳过。
- AC-06：RSA2 request signing 与 provider response verification 均实际执行。
- AC-07：只输出 minimal neutral fact；不把 Alipay-specific enum 写入 Trust Core。
- AC-08：无 production endpoint / production credential / PII / real funds。
- AC-09：既有 project baseline / run_experiment / full unittest 不退化。
- AC-10：范围声明诚实：只证明 first live Sandbox payment-proof verification slice；callback/finality/recovery/fulfillment/production 均未证明。

## Live-call budget / 外部调用预算

支付类外部操作不允许并发重试波次。

冻结预算：
- sandbox simulated transaction：最多 1 条有效 fixture；
- valid `payment.verify` live call：最多 2 次，仅用于一次执行 + 一次明确 retryable network failure；
- tampered-proof live call：最多 1 次；
- 不允许 L3 再次发起 live transaction 或再次消费 Payment-Proof。

L3 对 live evidence 采用 evaluator-owned audit，不重复 live side effect。

## Validation

L2 运行冻结 `VALIDATION_PLAN.yaml`。

Live run 生成 secret-safe evidence：
- `evidence/H38_LIVE_VALID_FACT.json`
- `evidence/H38_LIVE_NEGATIVE_FACT.json`

L3 对这两个事实做独立审计，不重复 live call。

## Stop conditions

任一触发立即停回 Evaluator：
- 只能用 production endpoint/credential 才能继续；
- Sandbox 要求真实资金；
- secret 无法做到不出现在日志/evidence；
- provider response 无法验证签名；
- 第一 slice 必须同时实现 callback/finality/recovery；
- 需要修改 Trust Core；
- 需要安装新依赖；
- live API 文档与冻结官方合同发生不兼容变化。

## Inherited uncommitted snapshot / 继承快照

H-38 baseline HEAD 仍为 `2b57248...`，工作区继承已通过 H-37 L3 的未提交 product snapshot：

- `src/agentic_payment_experiment/adapters/ap2_official_verification.py` sha256 `7a094c9d...270a`
- `src/agentic_payment_experiment/adapters/__init__.py` H-37 snapshot sha256 `1a7aafae...872c`
- `tests/test_ap2_official_verification.py` sha256 `4321882e...c780`

Executor 不得改动 H-37 行为；对 `adapters/__init__.py` 只允许机械追加 H-38 export。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-07, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_scope: H38 Alipay Agent Pay Sandbox first external verification slice only
  maturity_before: M1 MODELLED
  maturity_after_target: M4 EVIDENCED
  residual_risk:
    - sandbox evidence is not production compliance
    - no production credential or real funds
    - callback/finality/recovery remain out of scope
```

## Evaluator amendment 2026-09-20-a1

依据本包 EVALUATOR_RESEARCH.md 的固定版本官方源码研究，冻结以下补充要求：

1. `binding_checks_requested` 必须恰好包含 `trade_no`、`out_trade_no`、`resource_id`、`amount`，不得重复。VALID 时 passed 同样包含全部四项；缺字段不能补值后通过。
2. 成功事实 reason_codes 仅为 `VERIFIED`。篡改负例只有经验签的 Provider 拒绝可进入通过候选，reason_codes 为 `PROVIDER_REJECTED_PROOF` 或 `PROVIDER_INACTIVE`，active=false。网络失败、缺字段、本地 proof 字符串比较、验签失败、绑定失败均不得充当 AC-04 的外部证明。它们仍须 fail closed，但不等于本任务通过。
3. 有效/篡改记录必须属于同一交易 digest，除 proof 外保持相同输入；先取得有效对照。若 inactive 可能来自过期、一次性消费或交易状态变化，则负例 INCONCLUSIVE，不授予 PASS。不得超预算追加试验。
4. live_fact_audit.py 仅检查脱敏事实结构与语义，不能独立证明 live origin 或验签执行。L3 还必须复核实际验签代码、离线错误公钥/缺签名/篡改响应测试及单次 live 执行内的 evaluator-owned 内存验签观测。原始响应不落盘；缺少此观测则 AC-06 仍未闭合。该观测尚待实现，不能用布尔值替代。
5. fixture 输入须在内存中区分 Provider 返回与本地合成来源。官方示例本地合成 proof、买家签名占位符，不得被标为 Provider 签发或真实买家认证。
6. 外部方法白名单仍只有原冻结 HTTPS gateway 的 payment.verify。官方脚本的 HTTP 收银、自动重试、临时凭证文件和履约调用不在白名单内，不直接执行。使用已有沙箱 fixture 或官方交互取得 fixture；如该路径不可行，先形成独立最小上游方案并重新冻结方法/传输/预算，而非绕过 AC-02。
7. 执行顺序：检查器自测 → 薄适配器离线签名/绑定测试 → secret-safe preflight → 有效 live → 篡改 live → L3。缺凭据不妨碍已授权离线实现，但不得伪造 live evidence。

本次只完成评估侧修订和检查器自测，未实现产品适配器或独立内存验签观测。PCAC-AGENTPAY 的 [PCAC-06, PCAC-07, PCAC-09, PCAC-12, PCAC-20] 保持本 slice 的 M1 MODELLED；12 项合成检查器测试不升级为 M4 外部证据。

## Iteration budget (unchanged)

### Implementation checkpoint 2026-09-20-a2

- 用户明确授权读取本地沙箱密钥文件，允许任务脚本读取该指定文件至内存。不得复制正文或将本机路径写进共享证据。新增 scripts/h38_inspect_local_keys.py 纳入范围。
- 已实现离线 adapter、probe 和 evaluator-owned response_observer。observer 在同次响应内单独调用验签，共用 envelope parser；不是独立网络来源证明。a1 的“尚待实现”状态由本条更新。
- probe 默认只预检；live 必须显式 --execute 并指定 --key-file。无重定向、无自动重试；每个 case 固定 reservation 文件，在调用前独占创建，失败保留，不得删除以重试。
- 另存脱敏 observation（响应 digest、验签结论和观测范围）。不得将合成测试当作 live evidence。
- fixture 尚未取得；未批准 HTTP 收银或完整 Skill 执行；未发生外部支付调用。

最多 2 个 implementation → L2 cycles。

若第二轮仍因真实产品缺陷失败，停止交回 Evaluator；不得无限修。
