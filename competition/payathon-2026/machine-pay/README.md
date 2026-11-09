# Machine Pay 子作品

## 一句话

让 Agent 为 API / MCP / Skill 按次付费，并证明每次 Payment-Proof 只能解锁正确资源、正确价格和一次履约。

## 协议主链

```text
resource request
 -> HTTP 402
 -> Payment-Needed
 -> payment
 -> Payment-Proof
 -> verify
 -> resource delivery
 -> fulfillment.confirm
```

## 复用主项目

- x402 offline conformance；
- machine resource payment 语义；
- Payment Binding；
- Budget / Policy；
- Idempotency / Replay；
- Finality / Recovery；
- Fulfillment / Remediation；
- Authoritative Trace。

## 比赛专属层

计划只新增：

- Alipay A402 bill adapter；
- Payment-Needed parser/profile；
- Payment-Proof provider verifier adapter；
- fulfillment.confirm adapter；
- 一个最小付费 API/MCP 服务；
- Demo / submission assets。

## 首轮成功判据

1. 无 proof 时稳定返回 402；
2. 账单可稳定关联 resource/order/price/expiry；
3. proof verify 后继续核对业务字段，而非只看 API success；
4. amount/resource/order 任一错绑都不履约；
5. trade_no 重放不能二次交付；
6. Payment Success 与 Service Success 分离；
7. 履约完成后存在明确回执；
8. 全链可回放。
