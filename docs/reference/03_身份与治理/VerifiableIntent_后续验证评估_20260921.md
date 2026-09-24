# Verifiable Intent：支付宝之后的第三个外部验证对象

日期：2026-09-21。用户已确定顺序：AP2 → 支付宝 Agent Pay / APASS → Verifiable Intent（VI）。
状态：`QUEUED / MEASUREMENT_FIRST`，尚未冻结执行合同，不代表产品接入已完成。

## 官方依据与边界

[官方仓库](https://github.com/agent-intent/verifiable-intent) 当前标识为 Mastercard 维护、Draft v0.1，提供分层 SD-JWT 授权规范、Python 参考实现、Examples 和 Tests；涵盖委托、密钥绑定、约束、选择性披露及 checkout/payment 关联。

[pyproject.toml](https://github.com/agent-intent/verifiable-intent/blob/main/pyproject.toml) 标识 Apache-2.0、Python >=3.10、cryptography >=42.0。本轮只读核验公开页面，未安装或运行；main 为浮动来源，正式测量前必须固定 commit、规范文件 hash、依赖与许可证。

VI 是授权证据验证对象，不代表已接入 Mastercard 支付网络。密钥供应、生产身份、真实扣款和争议处理不能由本次验证自动覆盖。

## 为什么排在支付宝之后

支付宝提供真实 Provider 的观察证据；VI 用于检验另一种外部授权表达能否复用现有核心。两者互补。AP2 已有代表性官方 SDK / crypto 切片，不宣称完整协议覆盖。

启动门：支付宝当前约定的代表性切片经 Evaluator 验收，且剩余缺口显式登记。若支付宝仍 BLOCKED，不能以 VI 通过冒充其完成；如需调序，显式记录 SWITCH 决策。

## 第一包：只测量

1. 固定官方来源、版本、验证入口、最小依赖与可用正负样例。
2. 分别测量用户在场和自主委托模式，不能预设两种模式有相同层数或 key binding 语义。
3. 对照 Authority、交易绑定、身份/持有证明、披露与审计事实；每项标记 SUPPORTED / PARTIAL / UNSUPPORTED / NOT_APPLICABLE。
4. 冻结 AP2 与 VI 的共同可表达语义：金额/币种、商户/收款方、委托范围、时效及交易对象。对合法授权、超限、错绑、签名篡改、错误密钥、过期/重放与缺失必要披露建立比较计划。
5. 区分官方 checker 结果、Adapter 映射与 Trust Core 决策，避免两边共同丢字段却误判为一致。

第一包不修改产品核心；不以同为 SD-JWT 推定现有 verifier 可以直接复用。不提前复制外部敏感样本或密钥。

## 映射注意事项

- 委托约束 → Authority；金额、币种、merchant/payee → Authorization / Binding。
- cnf / key binding → 身份与持有证明的候选输入；仍需可信根、实际签名和完整链验证，不能见到 cnf 就给 VERIFIED。
- Selective Disclosure → 优先检查数据最小化及必要字段可见性；不直接等同 P4 可信来源。隐藏必要授权字段时不得默认允许。
- 防篡改授权证据 → 审计链输入；不自动证明支付已执行、可恢复或证据可独立回放。
- 产品名称等描述字段不能未经规范依据就当成机器可验证购买约束。

## 完成与停止条件

第一包完成：产出固定来源、兼容矩阵、可复核差距和一个明确后续决定。

- 无新缺口：保留为外部验证证据，STOP 产品扩展。
- 重复 Adapter 断点：CONTINUE 最小适配包，随后做 AP2/VI 等价语义比较。
- 核心语义缺口：交 Evaluator 单独设计，不在测量中顺手改 Core。
- 来源/环境不足：BLOCKED；协议差异明确归因，不强行比较或抹平。

跨协议通过仅证明冻结的共同语义与案例范围可复用，不证明所有协议、所有 Provider 或生产安全。

## 外部要求影响

external_requirement_impact：profile=`PCAC-AGENTPAY`；关联 PCAC-03/07/09/11/12/15；适用性为 CORE / ADAPTER（逐项在合同中确定）。本次仅规划，maturity_before / maturity_after 保持不变，具体等级待合同核实；Test / Evidence 尚无新增。残余风险：草案变化、信任根、必要披露、重放状态及生产凭据边界。
