# Frozen Measurement Contract

Task ID: `H39_ALIPAY_SANDBOX_FIXTURE_READINESS_V1`
Task kind: `measurement-only`
Contract state: `CONTRACT_FROZEN`
Workflow: `evaluator-executor-workflow/v2.2`
Dispatch mode: `SINGLE`
Baseline HEAD: `5e7c0c0b78aeec9c241078a37858cf3f2d8a14b3`
Baseline working tree: inherited uncommitted H-38 implementation; see BASELINE.json.
Map revision: `2026-09-20-r56`
Active bottleneck: `B-06`
Parent dependency: H-38, PARTIAL / LIVE_BLOCKED, not accepted.

## Global position

目标：证明智能体支付的授权、绑定和外部证据可验证。路线 A–D CLOSED → E 本地代表性闭合 → F 当前；AP2 官方链已闭合，支付宝 live slice 尚未闭合。

第一瓶颈是有效 sandbox fixture 的获取路径与证据语义未知，不是缺少更多离线 adapter。AP2 typed semantics / Receipt 与 B-16 横向攻击保持 WATCH；WebShop Windows 路径断言失败需保留，不借本任务扩张修复。

本包只测量：账号和接口是否提供满足 H-38 要求的 fixture 路径。文档结论不等于 live 验证，无法获取应输出明确 STOP / HUMAN_REQUIRED / CONTRACT_CHANGE_REQUIRED，不再笼统重复“缺密钥”。

## Hypothesis and observable objective

假设：在既有沙箱账号、零真实资金、秘密不外泄的边界下，可以识别一条官方支持的交易 fixture 获取路径，并明确其最小输入、传输、生命周期与绑定语义。

本包验收的是**路径可执行性判定**，不是创建交易或证明支付安全。

## Known inputs and unknowns

| 输入 | 当前事实 | Executor 动作 |
| --- | --- | --- |
| 沙箱 APPID / 商家 PID | Human 已提供，页面文本曾确认 | 从当前会话/获授权本地材料读取；不要求重复提交、不写值进报告 |
| 应用私钥 / 应用公钥 / 支付宝公钥 | 已解析 RSA-2048、应用密钥配对、本地 RSA2 签验通过 | 使用已有本机配置入口；没有路径上下文时只问路径，不问正文 |
| 支付宝公钥来源 | 用户提供，尚无 live 响应确认 | 区分本地格式正确与 Provider provenance 已验证 |
| 沙箱买家 UID | 未确认 | 优先在官方沙箱测试账号页面读取；商家 PID 不能代替 |
| Agent Pay 权限/入口 | 默认沙箱应用存在，不等于此 API 已可用 | 官方页面/账号提示确认；普通支付开通不能作为替代证据 |
| trade_no / proof / 可信订单、金额、资源 | 未取得 | 不编造、不从待验证响应反填 expected；说明如何得到 |
| 浏览器连接 | ambient 可见页面但控制工具 inventory 空 | 一次绑定现有页面、一次重新连接/开页尝试；仍失败则输出具体人工节点，不推断用户未登录 |

已有私钥文件仅是授权输入位置，不复制进新包。跨任务上下文缺失时允许 Human 只提供本地路径；不得扫描整个桌面或读取浏览器存储/剪贴板来寻找秘密。

## Execution steps

1. 读取 CURRENT、本合同、H-38 EVALUATOR_RESEARCH 和 a1/a2 补充、PCAC 映射。校验 BASELINE.json 中的继承文件 hash，发现漂移停回 Evaluator，不覆盖已有改动。
2. 复用现有官方研究，只针对未决项定向核实：沙箱买家账号、Agent Pay 开通条件、模拟交易入口、proof 来源、返回四维绑定、有效期/是否一次消费。优先官方 API 文档和固定版本官方脚本；记录 URL、日期、版本和结论来源类型。
3. 通过授权浏览器只读检查当前账号。若需登录/验证码，打开确切页面交由 Human；不得让 Human 盲找资料、粘私钥或重复给 APPID。读不到页面就明确工具故障，不宣称账号未登录。
4. 写 ROUTE_ASSESSMENT.md：逐步列出拟调用的方法/端点、输入类别、返回字段、资金是否模拟、秘密传递位置、总调用预算、用户交互、失败/过期处理、H-38 handoff。若只能采用官方 HTTP cashier、临时秘密文件、额外依赖或履约链，逐项标为合同差异，不直接执行。
5. 写 READINESS.json 和 REPORT.md。对每个未知项给已知/未知、证据、最小下一动作。最多一次集中询问 Human 真正无法自行取得的信息；需要人操作的页面应尽量先打开。

## Allowed actions and scope

- 公共官方资料读取、授权账号页面只读检查、本地既有非回显密钥检查均可进行。
- 只修改本 H39 task package 内报告/来源/测量证据。CURRENT 和地图由 Evaluator 管理。
- 无新依赖；使用已有 Python runtime。不得改 H-38 产品文件、冻结检查器或 Trust Core。
- 本包交易创建预算 **0**、payment.verify 调用预算 **0**。既有 Human 沙箱授权继续有效，本次 measurement 不消耗 H-38 的交易/验付预算。
- 不重置/生成/更换密钥、不改权限、不注册生产服务、不向第三方发消息；不运行完整官方 Skill、不调用 HTTP cashier、不猜测 HTTPS 替代地址。
- 不提交、推送、改写历史；不因 CURRENT 切换而删除任何 H-38 reservation。

## Route decision and completion criteria

- AC-01：继承文件 hash 相同，无产品/秘密改动、无交易调用。
- AC-02：七项就绪维度均记录 `CONFIRMED / UNKNOWN / UNAVAILABLE`：account_access、agent_pay_eligibility、buyer_account、fixture_route、proof_provenance、binding_fields、transport_and_budget。每项都关联官方/本地/用户报告等证据类别，不能自报 true 替代来源。
- AC-03：有具体端点/方法/人工页面链路及 fixture handoff 设计；trade_no 与 out_trade_no、买家 UID 与商家 PID、本地 proof 与 Provider 签发严格区分。
- AC-04：明确四维绑定缺失、proof 篡改不敏感、一次性消费/过期造成负例歧义时如何 STOP/INCONCLUSIVE；不能削弱 H-38 验收。
- AC-05：输出唯一判定及最小后续动作：
  - `READY_FOR_EVALUATOR_FREEZE`：路径与全部必要输入类别有依据，需 Evaluator 冻结最小上游执行合同后才能创建 fixture；不等于 live-ready。
  - `HUMAN_REQUIRED`：仅具体账号交互/买家信息无法自行取得；指明页面及操作，禁止泛泛“请补沙箱信息”。
  - `CONTRACT_CHANGE_REQUIRED`：路径依赖当前禁止的方法/传输/履约，提供差异与最小修订建议。
  - `UNSUPPORTED`：官方证据表明无法满足该路径；说明是沙箱能力边界，不外推生产漏洞。
- AC-06：沿用 PCAC 基线，不声称强认证、生产安全或监管合规。

完整、可证的 BLOCKED/UNSUPPORTED 测量也可结束本包；不能因预算用完写 PASS。测出重复共同断点才考虑 capability package。

## Next-stage conditions

READY → Evaluator 冻结最小 fixture acquisition 执行合同，继承 H-38 最多一笔交易及验付预算，随后恢复 H-38；不能直接运行旧 preflight，因为它要求 CURRENT.task_id=H38。
HUMAN_REQUIRED → 保持精确交互待办，完成后只复核受影响项。
CONTRACT_CHANGE_REQUIRED / UNSUPPORTED → STOP 现路径，评估更窄支付宝测量或官方替代；不自动切生产、其他支付平台或降低绑定要求。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-07, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_scope: Alipay live external verification slice
  maturity_before: M1 MODELLED
  maturity_after_target: M1 MODELLED
  Test: baseline integrity and source-supported route assessment
  Evidence: BASELINE.json, ROUTE_ASSESSMENT.md, READINESS.json, REPORT.md
  residual_risk: no live response or buyer authenticity evidence; no compliance claim
```
