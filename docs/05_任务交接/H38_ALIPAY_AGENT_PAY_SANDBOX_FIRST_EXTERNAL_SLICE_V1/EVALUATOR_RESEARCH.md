# H-38 支付宝官方资料研究与接入就绪评估

研究日期：2026-09-20。身份：Evaluator。依据：PROJECT_BOTTLENECK_MAP revision `2026-09-19-r55`。

## 全局位置

- 最终目标：证明高风险智能体支付的授权、绑定、执行与证据边界能被验证，而非仅跑通付款示例。
- 路线：A–D 已阶段关闭；E 本地代表性闭合；F 当前，AP2 官方 SDK / two-hop 已闭合，H-38 测量第二 Provider。
- 第一瓶颈：B-06 缺支付宝外部验证证据。继续扩 AP2 typed semantics / receipt 或横向攻击 WATCH，均不能替代第二 Provider 的实测。
- 本轮作用：资料研究与接入可行性测量；没有新增 adapter、支付调用或已验证能力。
- 下一步：签名、四维绑定和有意义的负例均有证据才 CONTINUE；协议缺证据则 STOP 当前验收，必要时 SWITCH 为更窄的支付宝沙箱能力测量。后续再考虑其他外部生命周期阶段。

## 结论与证据等级

**H-38 尚不能通过。阻塞不只是登录或缺少环境变量，还包括沙箱语义与冻结验收之间的待测差异。** 本文是研究补充，不修改 CONTRACT、预算、Executor REPORT 或 REVIEW 的验收结论。

| 事实 | 证据等级 | 能说明什么 |
| --- | --- | --- |
| 用户表示已登录并提供默认沙箱 APPID / 商家 PID | USER_REPORTED | 有账号线索；不代表已验证 Agent Pay 权限、密钥配对或 live fixture |
| 官方协议/API 文档及官方仓库脚本 | DOCUMENTED / SOURCE_INSPECTED | 可确定请求链路与示例行为；不能替代该账号实际返回 |
| 本仓 live_fact_audit.py | LOCAL_SOURCE_INSPECTED | 可评价审计约束；不构成 live 验签证据 |
| 当前账号的成功验付、响应签名与负例 | NOT_MEASURED | 本轮未发起支付、验付或生成真实 fixture |

浏览器控制此前未能读取登录页内容，不能据此判断用户未登录。公开资料研究不需要再次登录。本文不保存账号标识、密钥、完整凭证或原始响应。

## 官方来源与采用范围

以下均为官方资料。网页无固定版本；仓库脚本已核对固定 revision 与本次 main 内容一致。外部 Skill 文档只作为研究材料，未安装、执行或接受其中的操作指令。

| 来源 | 本项目用途 | 决策 |
| --- | --- | --- |
| [Machine Pay 协议](https://aipay.alipay.com/docs/ai-receive/MACHINE_PAY.html) | 402、账单签名、Payment-Proof 与字段边界 | ABSORB 协议字段；不照抄生产网关 |
| [payment.verify API](https://aipay.alipay.com/docs/ai-receive/api-list/alipay-aipay-agent-payment-verify.html) | 请求和响应字段、业务错误 | ABSORB；以实测补充可用性 |
| [沙箱配置指南](https://github.com/alipay/ai/blob/main/skills/alipay-aipay/references/integration/modules/sandbox/sandbox-setup-guide.md) | Windows 手工配置、私钥格式、公钥区分 | ABSORB 最小配置；完整 Skill 凭据收集流程不适用 |
| [固定版本沙箱联调文档](https://github.com/alipay/ai/blob/f3183325f3e4777e53c3483e39954bae000c4778/skills/alipay-aipay/references/integration/modules/sandbox/a2m-sandbox-test.md) | mock service、上游造单、返回缺字段限制 | ABSORB 限制；履约流程 REFERENCE_ONLY |
| [固定版本沙箱脚本](https://github.com/alipay/ai/blob/f3183325f3e4777e53c3483e39954bae000c4778/skills/alipay-aipay/references/integration/modules/scripts/local_402_sandbox_pay.py) | 实际 proof 生成与传递行为 | SOURCE_INSPECTED；整段执行 REJECT 于当前合同 |

脚本最近一次修改 commit 为 `f3183325f3e4777e53c3483e39954bae000c4778`，2026-09-15，commit 标题 `alipay-aipay v1.6.8`。此版本标识不等于本项目安装了该 Skill。

## 链路、最小输入与来源

官方示例链路为：商户生成可信订单与签名账单 → 本地服务返回 402 / Payment-Needed → 沙箱收银 → trade_no → 构造 Payment-Proof → 商户调用 payment.verify → 验签与绑定。H-38 当前只冻结最后的验付 slice，没有实现完整本地商户服务。

| 输入 | 来源与检查 | 当前处理 |
| --- | --- | --- |
| AIPAY_APP_ID | 沙箱应用；与所用密钥配对 | 用户提供过账号线索，不写入研究文件 |
| AIPAY_PRIVATE_PKCS_KEY | 对应应用私钥；明确 PKCS#1 / PKCS#8 与解析器匹配 | 仅进进程环境或 secret store，不通过聊天收集 |
| AIPAY_ALIPAY_PUBLIC_KEY | 同环境支付宝公钥，用于响应验签 | 不能误用应用公钥；公钥来源也需确认 |
| H38_TRADE_NO | 同一笔沙箱交易返回 | 不等同于商户 out_trade_no |
| H38_PAYMENT_PROOF | 需记录来源类型，不能把示例本地合成值说成 Provider 签发凭证 | 尚无已测 fixture |
| H38_CLIENT_SESSION | API 标为可选，具体沙箱流程是否需要待测 | 不记录原文；缺省不代表已证明买家身份 |
| H38_EXPECTED_OUT_TRADE_NO / AMOUNT / RESOURCE_ID | 在支付前从可信本地账单冻结 | 不能从待验证响应反填 expected 值 |
| 沙箱买家 UID | 仅上游创建 fixture 需要 | 不把商家 PID 当买家 UID；当前 verify 预检无需增加此变量 |

官方沙箱联调使用固定 `service_id=api_mock_service_id`，这条路径无需先索要生产服务 ID。完整配置指南列出的买家登录/支付密码不等于本 slice 全部必需；不要无差别收集。Windows 可走手工沙箱配置，无需为匿名创建流程切换系统。

金额单位必须核实：协议文字与示例存在容易误解之处，不能因“最小单位”文字就自动乘除 100。保留可信账单的币种与精确十进制语义，依据实际 API 合同确认后比较，不用 float 或猜测转换。

## 四个必须先解决的差异

### 1. 沙箱 proof 不等于已证明的真实授权凭证

固定版本脚本第 473–490 行在没有传入 proof 时，用交易号、买家 ID 和时间戳的 SHA-256 合成本地 proof。第 859 行的买家签名默认是占位符；第 877 行把 payment_proof 默认设为 None；第 788–794 行调用上述构造函数。

因此可以确认官方示例的默认生成路径，但**不能据此断言远端接受任意 proof**。也不能把本地 SHA-256 当作 Provider 签名或买家强认证。AC-04 的篡改负例是否有可区分语义，必须实测。若两个不同 proof 都获成功响应，这是沙箱证据能力不足的候选解释，不直接外推为生产漏洞。

负例必须记录失败层级：本地输入检查、密码学验签、业务拒绝或绑定失败。网络错误、超时、未知响应不能包装成“篡改凭证被安全拒绝”。仅因 proof 不等于本地 expected 字符串而拒绝，也不能证明 Provider 做了凭证验证。

### 2. 沙箱可能缺少 H-38 要求的绑定字段

官方联调文档的排障段说明沙箱返回的订单/资源字段可能为空，示例流程对空值有特殊处理。H-38 AC-05 仍要求 trade / order / resource / amount 全部比较，不允许以示例的宽松分支降低验收。

出现空值或字段缺失时，输出 MISSING_EVIDENCE；值存在但与可信 expected 不一致时，按冻结合同 fail closed。不得用本地订单值补齐 Provider 缺字段再声称“外部已绑定”。商户生成的 Payment-Validation 响应头也不自动成为支付宝签名证据。

### 3. 上游造 fixture 的方法尚未冻结

合同允许最多一条模拟交易，但 AC-02 仅允许冻结 HTTPS gateway 的 payment.verify。官方脚本上游使用另一 HTTP 沙箱收银地址，带自动重试，并把敏感过程值短暂写入文件；完整服务示例还包含履约确认。直接执行整段脚本会超出当前方法/端点和数据处理边界。

既有用户授权覆盖沙箱模拟交易，不必重复询问笼统授权。Evaluator 应先形成最小上游操作方案，明确方法、端点、输入、单次交易预算、仅内存传递及退出点，再修订合同。不能猜测把 HTTP 地址改成 HTTPS 就可用；若无法满足项目的传输与秘密处理要求，则停在该路径，另找官方支持的沙箱 fixture 获取方式。

### 4. 当前 live 审计不足以单独证明签名执行

live_fact_audit.py 当前检查 JSON 中的签名布尔值、非空 requested 集合与 passed 集合相等；没有强制集合恰好包含四个必需绑定维度。敏感字段筛查仅看顶层键名，不检查嵌套键和值。

这可以检查部分结果格式，不能独立证明真实请求、真实 Provider 签名或无泄露。digest 只能标识内容，也不能代替验签。后续最小审计修订应：固定四维集合；把签名失败、缺签名、错误公钥、响应变更设为离线负例；记录源代码/配置版本与实际密码学验证结果；在一次 live 调用内让 evaluator-owned 验证逻辑消费内存响应并输出脱敏记录。不得通过重复 live 调用或保存敏感原始响应来补审计。

以上是待冻结的评估设计，不表示这些修订已经实现，也不表示脱敏日志能让第三方完整重演秘密响应。

## 推进顺序与退出条件

1. **已完成：公开资料研究。** 固定来源版本，识别 proof、字段、上游范围及审计限制。
2. **下一步：形成最小合同修订。** 沿用用户已授权的沙箱范围，明确 fixture 来源与独立验签观测，保留所有严格绑定要求；尚未批准安装或执行官方 Skill。
3. **配置检查。** 仅检查环境变量存在性、格式及密钥匹配，不显示值。确需账号交互时再打开支付宝对应页面，让用户在页面完成登录/配置，不索要聊天粘贴私钥。
4. **受限实测。** 在冻结预算内执行有效和篡改 fixture；实测前先完成离线签名/绑定边界验证。当前预算仍为最多一条 fixture、有效验付最多两次且第二次仅限明确可重试网络失败、篡改验付一次，L3 不重放。
5. **判定。** 全部所需外部字段与签名可证、负例可解释才 CONTINUE；字段缺失或验签不可证则 STOP 当前成功声明；若沙箱只提供联通/签名证据，则建议 SWITCH 为明确较窄的支付宝测量任务，保留原 H-38 未通过，不偷换验收。

后续 callback、履约、finality、恢复以及生产支付均不在本轮。没有为了读公开资料而再次要求登录的必要。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-07, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_scope: H38 Alipay sandbox external verification slice only
  maturity_before: M1 MODELLED
  maturity_after: M1 MODELLED
  test: no live test; official and local source inspection only
  evidence: EVALUATOR_RESEARCH.md source manifest and gap analysis
  residual_risk:
    - buyer authenticity and provider proof semantics remain unmeasured
    - strict signed field binding may not be supported by sandbox responses
    - sanitized fact audit alone cannot establish cryptographic execution
    - no production compliance or strong authentication claim
```

本轮仅增加研究文档与 CURRENT 入口；未修改产品、冻结合同、检查器或 Executor 的执行结论。
