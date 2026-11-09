# Agent Pay 主作品

## 一句话

在用户授权范围内，让 Agent 完成真实商品/服务购买，同时用现有 Trust Core 证明“谁授权、买了什么、为何允许、是否越权、支付与履约是否闭环”。

## 首发 Profile

`SPECIFIED / 定向委托`。

首发不追求全自主；先把用户意图、授权、订单、支付和履约的一条真实 Provider 链跑通。

## 复用主项目

- Delegated Authority；
- Confirmation Binding；
- Order/Payment Binding；
- Agent Identity；
- Runtime Gate；
- Payment Lifecycle / Recovery；
- Authoritative Trace / Player；
- WebShop / Commerce Adapter；
- AP2 外部协议验证经验。

## 比赛专属层

计划只新增：

- ACT ADD/CID/PSD adapter/profile；
- Agent Pay provider seam；
- Demo merchant / product fixture；
- 产品入口与 UI；
- submission evidence。

## 首轮成功判据

1. 一条合法购买成功；
2. 超预算被拒绝；
3. 商户/订单/金额变化导致原确认失效或重新确认；
4. 过期/撤销授权不可继续支付；
5. 重复请求不会重复付款；
6. UNKNOWN 不盲目重试；
7. 支付后履约状态单独可见；
8. 完整 Trace 可回放。
