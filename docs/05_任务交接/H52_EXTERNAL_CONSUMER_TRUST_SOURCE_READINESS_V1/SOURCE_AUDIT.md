# H52 冻结官方来源与兼容性审计

## 审计范围与结果
仅使用 SOURCE_MANIFEST.json 固定的三份公开原文及本仓已固定 AP2 v0.2.0 SDK 与 H51 商家副本，不请求实时网页、不执行教程命令。PACKET_CHECK baseline 实际通过：HEAD=7831d232530c91825bb507a2a6d95b1de6a02c3b，受保护文件1367、冻结文件21，已有依赖符合预检且新增安装0。SHA-256 对三份原始 HTML 和对应 TXT 由 PACKET_CHECK.mappings 复核，不把已下载文件当当前发布版本。具体 URL、下载时刻、许可与 sha256 见 SOURCE_MANIFEST.json；来源归属见 SOURCE_ATTRIBUTION.md。

## 固定文档
1. `ucp-ap2-extension-20260825`：`sources/ucp-ap2-extension-20260825.txt`，Apache-2.0，定位150–245、260–356行。说明须先通过能力交集协商启用 `dev.ucp.common.payment.ap2_mandate`，商家向 checkout 放 detached JWS `ap2.merchant_authorization`，完整 checkout 经 JCS/RFC8785 规范化，签发 checkout/payment 两类授权，商家不接受缺少 mandate 的完成请求。这是**规范要求**而不是本地商家已实现的证据。
2. `ucp-ap2-relation`：`sources/ucp-ap2-relation.txt`，Apache-2.0，30–68行。UCP 管商城发现/结算，AP2 是授权证据层；双方要协同验签。作为关系解释，不构成可部署 SDK 或业务通过证据。
3. `google-codelab`：`sources/google-codelab.txt`，文本 CC-BY-4.0、示例代码 Apache-2.0，48–62和190–202行。两个模拟影院、代理交互、商家签名、授权的演示有参考价值，但示例角色/本机生成密钥并不能证明真人确认；其中的 ADK/模型/云、动态依赖全部未运行或导入。

## 版本与实现来源
- 固定花店：`docs/05_任务交接/H51_UCP_LOCAL_HTTP_GUARD_SLICE_V1/merchant/routes/discovery_profile.json` 第3–60行标示 UCP 2026-04-08，列出 shopping.checkout/cart/order 等，无 AP2 mandate capability。此商家不因 2026-08-25 规范已有扩展就自动升级。
- 官方 AP2：`local_sources/third_party/ap2-v0.2.0`，固定 commit `b4587ac1d055888a73b4b21750973cffba961793`，Apache-2.0；仅使用其 `MandateClient.create/present/verify`。本轮已有本地环境 cryptography 46.0.7、pydantic 2.13.4、jwcrypto 1.5.6、sd-jwt 0.10.4、ucp-sdk 0.4.6，未更新、未重装。
- 现有产品 `ap2_official_verification.py` 只证明给定预置信任公钥的两跳链、受众/nonce/时钟检查；`ap2_protocol_boundary.py` 明确不验 JWT 签名，仅对紧凑字符串哈希和 transaction_id 做绑定；`validator.py` 为中立离线业务判定。三者目前不构成不可绕过的共同执行路径。
- H51 商家副本 `merchant/services/checkout_service.py` 第735–800行有本地 execution_control 缺失拒绝和 claim→模拟 payment，旧 H51 的 8 个 HTTP 及 23 个方法回归已经被评估者验收；但它没有对 UCP/AP2 完整授权凭证和用户同意进行原生消费。本轮不运行 HTTP、修改商家或外推生产就绪。

## 精确结论
本次可复用已有离线签验和现有商家任务副本的执行占用思路；**不可直接宣称协议兼容、真实签发者可信或商家已实施 AP2 防护**。需要先改商家明确的能力协商/完整 checkout 签名与验签/受信确认来源/付款前强制调用及证据回传责任。若须修改既定源版本、商家合同或授权，另立任务；本包只形成一个证据指向的未来边界。