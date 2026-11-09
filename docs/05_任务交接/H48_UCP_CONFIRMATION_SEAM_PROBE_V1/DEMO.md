# H48 可读离线演示

这是用被冻结的完整 UCP 商家应用和实验信任配置进行的离线进程内测试，不需要真实钱包、银行卡、买家、密钥或支付网络。每次实验都重新开一个 Merchant，create 得到真实 checkout，并在原始响应上读取 checkout.id、line_items、currency、唯一 total；merchant/payee/authority/item category/expiry/service 等必填信任信息来自明确标记为 synthetic 的 TRUST_FIXTURE。

**正常交易 G01**：用户确认一件商品 → 取得 confirmation record → 再查询当前 checkout → 内容摘要一致，核验 VALID → 通过 execute_with_confirmation_gate → 实际模拟商家 complete 一次，mock payment 一次，库存 5→4，取得完成后商家订单编号。

**内容变化 G02**：先确认数量 1 → 商家更新到数量 2 → 重新查询并投影 → hash 不一致，结果 INVALID / CONFIRMATION_REQUIRED → 不调用 complete，不发生 mock payment，不建完成订单，库存保持 5。

**缺证据 G03/G04/G06**：缺显式合成收款人、授权或把当前快照币种从复制响应中删除 → 投影返回 order=None、非空 missing → 确认事实 MISSING_EVIDENCE → INDETERMINATE，complete=0。G06 是人为输入破坏，不代表原商家正常输出缺币种。

**确认过期 G05**：已创建确认但在过期时间后验证 → INVALID / confirmation_expired → complete=0，不自动续期。

**时间窗口 L01**：核验时数量仍为 1、fact VALID；核验之后模拟合法更新到 2 → 继续使用之前 fact 调用客户端 callback → 商家仍完成 2 件。该案例展示一次确定性的检查-执行穿插，不是并发竞态已解决。

**旁路 L02**：数量更新到 2，完全跳过本项目客户端 gate，直接调用原生 complete → 能完成 2 件。原生 N01 修改订单后完成同样是可观察的行为基线，而不是正式生产商城漏洞。

检查器将 9 个案例分别重复两轮并保存原始每步调用、状态、确认事实、HTTP 模拟返回、库存、订单和 mock payment 调用数；正式 L2/L3 有各自证据。