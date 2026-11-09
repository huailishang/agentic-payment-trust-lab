# H52 四角色可信来源与签验/执行边界

本次全部主体都是本地合成，不存在真实客户、真实商户、支付服务方或银行密钥。PROBES.py 使用四把不同的内存 EC P-256 私钥，公钥和 kid 分别以 `h52-trusted_user`、`h52-delegate_agent`、`h52-merchant`、`h52-attacker` 记录。私钥不写入文件，公开签名凭据仅供离线复算。可信根 `trusted_user` 通过试验外部预置注册表选择，而不是接受请求自称 root；此处的“用户”只表示被试验设为可信的模拟签发者，不是现实世界个人身份。

- **trusted_user（合成可信用户）**：用内存根签发 OpenPaymentMandate，授权 delegate_agent 公钥；所谓确认 `consent_present` 也是独立合成事件，当前三 API 均没有消费它。缺失即不应获得端到端授权通过，不能让模型生成一个布尔值替代确认来源。
- **delegate_agent（合成代理）**：持与 OpenPaymentMandate 中 `cnf.jwk` 对应的私钥签发 PaymentMandate，绑定收款方、金额、币种和原 checkout 紧凑 JWS 的 SHA-256。其有签名能力不等于用户进行了此次确定性同意。
- **merchant（合成商家）**：用独立 ES256 JWS 签署固定 ASCII/整数小 checkout；本次是普通紧凑 JWS，**不是** 2026-08-25 UCP 规范要求的完整 checkout JCS + detached JWS，也没有在真实商家 checkout 入口签发/校验。
- **attacker（合成攻击者）**：Q07 另签一条本身数学上有效的两跳链。用预置信任的 `trusted_user` 公钥验时 INVALID；把验证入参切到请求自带 attacker 公钥则 VALID，准确展示必须将信任锚与输入分离。

## 两层证据之外仍有断口
`verify_ap2_v020_official_two_hop_chain` 是真实官方 SDK 验证后的加密事实；`adapt_verified_ap2_v020_snapshot` 是只看 JSON 对象身份、checkout_jwt 字符串 hash 与 PaymentMandate transaction_id 的边界投影；`validate_request` 仅基于投影执行本地业务规则。它们没有一个“前一道信任失败就禁止后一层支付”的共同商家执行消费者。这是待衔接责任，不能因为三段各能返回 VALID/ALLOW 就声称整条交易授权成立。

观察 Q01：官方链 VALID、商家 JWS VALID、边界 VALID、业务 ALLOW、解码投影与已验签 payload 一致；它仅支持局部证据。Q02 改 checkout 签名正文后商家验签失败，另有 checkout hash 断裂。Q03 正常重签新 checkout 但旧 PaymentMandate 的 transaction_id 仍引用原 hash，绑定拒绝。Q04–Q06 仅改 decoded 投影的金额/收款方/币种，官方链仍可能 VALID，但投影血缘 `projection_matches_verified_payload=false`，不允许拿仅局部业务判断作放款依据。Q08 无合成用户确认但既有三函数不检查确认；Q09 过期、Q10 错误受众、Q11 显式已见 ID、Q12 上下文缺失分别揭示时效/去重/字段依赖；Q07 对比前述根的替换。

## 本包绝不宣称
不构成完整 UCP/JCS/RFC9421 会话，不观测真实确认签发者、客户身份、撤销事件顺序、商家付款副作用、支付机构回执、稳定交易查询引用、真实网络重试或跨系统竞争。业务返回 ALLOW 只是本地 `validate_request` 的输出，不是“已付款”；crypto VALID 不能替代确认、授权来源、已签原文投影血缘与真正的执行前强制合并验证。