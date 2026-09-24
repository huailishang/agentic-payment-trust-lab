# Evaluator Review

Task: `H39_ALIPAY_SANDBOX_FIXTURE_READINESS_V1`
State: **REVIEWED / PASS**
Task verdict: **PASS**
Measurement decision: **CONTRACT_CHANGE_REQUIRED**
Project-impact verdict: **NOT_APPLICABLE**
Continuation: **CONTINUE B-06; STOP_LIVE until H-38 authorization gate repair and a new frozen fixture-acquisition contract exist**
Reviewed: 2026-09-21

## Global position

项目最终目标仍是证明智能体在支付场景中能够把 Authorization(授权)、Binding(绑定)、Provider Evidence(外部支付方证据) 和 Side-effect Gate(副作用闸门) 串成一条可独立复核的可信链。

全局路线：A–D 已关闭 → E 本地代表性闭环已关闭 → F 外部真实协议 / SDK / Sandbox 当前。当前第一瓶颈仍是 `B-06`：支付宝 Sandbox 能否产生可归属、可验证、可安全进入现有 Trust / Trace 边界的 Provider-observed evidence(支付方实际观测证据)。

H-39 是 measurement-only(只测量) 任务，不创建交易、不调用 `payment.verify`。它的作用是判定 fixture(测试交易夹具) 获取路线是否足够清楚，可以进入下一份执行合同。

本轮只复核 Executor 对 R1–R3 的修订；R4 仍是 H-38 的独立 repair(修复) 前置条件，不能借 H-39 修改产品代码。

## Independent re-review

### Baseline integrity

`BASELINE.json` 中四个继承 H-38 文件的 SHA256 已重新计算，全部与冻结值一致：

- `src/agentic_payment_experiment/adapters/alipay_agent_pay_sandbox.py`
- `scripts/h38_alipay_sandbox_probe.py`
- `scripts/h38_inspect_local_keys.py`
- `tests/test_alipay_agent_pay_sandbox.py`

因此本轮 R1–R3 文档修订没有改动这四个继承实现文件。

### R1 — PASS

原问题：把 Manual Sandbox APP Payment(人工沙箱付款体验) 与 Machine Pay Automated Integration(Machine Pay 自动联调) 混成一条必经链。

独立复核固定官方源码 revision `f3183325f3e4777e53c3483e39954bae000c4778` 的 `a2m-sandbox-test.md`：

- 标准联调使用 `run --auto-complete`；
- 同一命令内获取 `Payment-Needed`、调用沙箱收银、构建 `Payment-Proof` 并重试服务；
- “付款体验”在测试结论之后作为 optional(可选) 体验入口，不是自动联调的强制前置步骤。

Executor 现已在 `ROUTE_ASSESSMENT.md` / `READINESS.json` 中明确拆分：

- Route A：Machine Pay 自动联调；
- Route B：可选的人工 Sandbox APP 支付体验。

并且对两条路线分别记录 proof production(凭证产生位置)、proof capture(凭证获取位置) 与 provenance(来源属性)；无法证明的地方保持 `UNKNOWN`。不再要求 Human 先做一次人工付款，也没有把 sample-constructed proof(样例流程构造的凭证) 提升成 Provider-signed proof(支付方签发凭证)。

**R1 关闭。**

### R2 — PASS

原问题：就绪等级超过证据强度。

现有 `READINESS.json` 已修正为：

- `buyer_account = UNKNOWN`，仅保留“沙箱账号导航入口已观察”；
- `binding_fields = UNKNOWN`；
- `documented_schema = CONFIRMED`；
- `live_returned_fields = UNKNOWN`；
- `account_access = CONFIRMED` 仅表示 Executor-reported read-only page reachability(执行者报告的只读页面可达)，明确不等于 Agent Pay eligibility(产品资格/开通状态)。

三个 Browser observation(浏览器观察) 均补充了 method / visible evidence / scope / limitation，且未保存身份、买家账号、密码或秘密值。

这与原 R2 修复要求一致。

**R2 关闭。**

### R3 — PASS, with source-drift note

原问题：把页面更新时间、API 参数最大长度和 H-38 本地负例形状混写。

Executor 已完成语义分离：

- `observed_at` 与 `page_updated_at` 分开；
- 参数表的 `payment_proof` 记录为 **maximum length 64**；
- H-38 篡改负例“保持 64-character shape(64 字符形状)”明确标记为本项目测试设计，不再表述成“参数表规定必须恰好 64”。

本次 2026-09-21 独立复核时，支付宝官方 `payment.verify` 页面已经再次更新，当前页面显示更新时间为 **2026-09-20 12:29:13**，而 Executor 在 2026-09-20 的测量记录保存的是 `page_updated_at=2026-09-17 16:23:08`。这是一个 **source drift(外部来源漂移)**：当前页面不能再直接复现昨日页面元数据。

这不推翻 R3 的核心修复，因为当前官方页面仍明确把业务请求参数表中的 `payment_proof` 标为最大长度 64；同时当前错误码说明还出现“支付凭证需要为64位”。因此后续如果继续引用“exact 64”，必须分别注明它来自错误码语义还是本地负例设计，不能再只靠字段表推导。

本轮不因外部页面在提交后继续变化而退回 Executor；但下一份合同若依赖动态官方页面，必须同时记录精确观察时间，并优先保存固定版本/快照依据，避免只记录可变页面的更新时间。

**R3 关闭。**

## R4 remains open and blocks live execution

R4 不属于本轮 R1–R3 修订，但仍是零容忍前置缺陷：

`scripts/h38_alipay_sandbox_probe.py` 在 `--execute` 路径进入 reservation(调用预留) 和网络调用前，没有读取 `CURRENT.md` 的 `task_id` / `authorization_api_call`。

当前 `CURRENT.md` 已不是 H-38 live 执行态，因此在恢复任何 live Sandbox 调用前，必须单独冻结并完成 H-38 Live Authorization Gate(在线调用授权闸门) repair。该 repair 只能使用 fake transport(假网络传输) / 本地测试验证，不得发起真实支付或验付请求。

## Final verdict

R1：**PASS**
R2：**PASS**
R3：**PASS**（记录 source drift，不退回）

H-39 Task：**PASS**
H-39 Measurement decision：**CONTRACT_CHANGE_REQUIRED**

这里的 `CONTRACT_CHANGE_REQUIRED` 不是任务失败，而是 H-39 成功测量出的路线结论：现有 H-38 合同不能直接拿来执行 fixture acquisition(夹具获取)。下一步必须先修 H-38 的 live 授权闸门，再由 Evaluator 冻结一份更窄的 Route A fixture-acquisition 执行合同；在这两件事完成前，继续保持：

```text
transaction_create = 0
payment_verify = 0
production = forbidden
real_funds = forbidden
```

PCAC-AGENTPAY [06,07,09,12,20] 仍为 M1 MODELLED；本轮不产生 Strong Authentication(强认证)、Production Security(生产安全) 或 Compliance(合规) 结论。
