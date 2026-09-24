# H-41 瓶颈决策与来源

Date: 2026-09-22. Map: 2026-09-22-r61. Decision: SWITCH from blocked fixture acquisition to a narrower signed-response measurement.

## 全局位置

项目要证明授权、支付动作与证据连续可信。A–D 完成，E 本地闭环，F 当前。H40 已关闭授权闸门 R4，但 B-06 仍缺支付宝实际响应证据。继续扩授权解析器、AP2 或横向攻击 WATCH 不能补这个缺口。

H39 已证明需要改合同，不应让 Executor 再做一轮笼统“查沙箱资料”。本次 Evaluator 已直接核对固定源码并作决定：当前 Route A 暂停于传输边界；不冻结一份暗含 HTTP 收银许可的 fixture 合同。改测已存在的 HTTPS 验付接口能否提供可验签响应，不创建交易。

## 本轮核实的来源

1. 官方固定源码（2026-09-22 经只读 HTTPS 获取正文，未导入或执行）：
   https://raw.githubusercontent.com/alipay/ai/f3183325f3e4777e53c3483e39954bae000c4778/skills/alipay-aipay/references/integration/modules/scripts/local_402_sandbox_pay.py
   - `PAY_ENDPOINT` 为 `http://aicashier.dl.alipaydev.com/openclawpay/agent/v1/pay`。
   - `build_cashier_payload` 携带 buyer ID 与买家签名字段；默认买家签名为占位值。
   - `request_cashier_with_retry` 有重试路径，`command_run/complete` 将过程信息写入临时文件。
   - `build_payment_proof_header` 在没有传入 proof 时本地构造 SHA-256 值。
   - 结论只针对固定 revision；未证明其他官方安全路线不存在。整体执行 REJECT；字段/流程边界 REFERENCE_ONLY。
2. 官方 payment.verify 文档（2026-09-22 读取，页面标注更新 2026-09-20 12:29:13；网页缓存不等于源站最新版本保证）：
   https://aipay.alipay.com/docs/ai-receive/api-list/alipay-aipay-agent-payment-verify.html
   接口描述为凭证验证；包含带签名的异常响应示例。是否本账号/沙箱也返回可验签错误响应仍 UNKNOWN，正是 H41 假设。网页示例的生产 gateway 禁止采用。
3. 已验收本地依据：H38 adapter 的固定 sandbox gateway 与 RSA2 签验；H39 REVIEW 的路线分离；H40 REVIEW 的离线闸门验收。

## 为什么选择这包

| 选项 | 当前判断 |
|---|---|
| 直接跑 Route A / 人工付款获取 fixture | 当前安全传输路线未闭合；人工付款也未证明能提供所需 Machine Pay proof，暂停 |
| 再做泛化就绪研究 | 重复 H39，信息收益低，不派发 |
| HTTPS 单次错误响应测量 | 不依赖交易/买家，能分离传输、请求处理、响应签名和业务证据，作为最小下一包 |
| AP2 扩展 / 横向攻击 | 不能回答第二 Provider 的真实边界，继续 WATCH |

错误响应验签成功只能说明“该响应在配置公钥下验签通过”，不能证明买家身份、付款成功、四维绑定、该公钥的独立来源或完整接口资格。无签名或网关错误也是有效测量结果，不得反复试到成功。H38 原目标与验收均保留。
