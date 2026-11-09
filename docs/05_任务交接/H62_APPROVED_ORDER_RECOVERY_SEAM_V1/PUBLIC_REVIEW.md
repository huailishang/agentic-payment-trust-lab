<!-- Public display copy; original SHA-256: 2669b9fd300f38c60dd84a0fc3771b25154a09f2c83d6a3b717239cafccc650d; only trailing whitespace/line endings normalized. -->

# H62 评估者独立复核：本地已付款无订单的受批准恢复切片通过，停止本切片扩张

Task ID: H62_APPROVED_ORDER_RECOVERY_SEAM_V1
Task kind: capability_experiment
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review date: 2026-11-07
Reviewer: Evaluator
Task verdict: **PASS**
Impact verdict: IMPROVED
Continuation decision: **STOP**

## 全局位置

最终项目目标是让高风险智能体交易中的身份/授权/绑定/决策/资金副作用/履约恢复和审计形成可检验的信任链。冻结地图 r100：A–D 已有本地代表性结果，E 仅受控本地验证，F 当前商户与协议接缝；第一瓶颈 B-17 是已经成功付款、商户原订单提交失败后，批准能否成为一次**不会重新付款**的订单恢复事实。本包为单个、局部、隔离来源的能力实验，优先于重复读取 H58/H61、泛化 SDK、第二商城和未经授权的真实 PSP 接入。

## Pre-review checks / 签收提交快照

- 执行者 REPORT 标注 SUBMITTED_FOR_REVIEW，正式 L2-GATE.json 为 **PASS 8/8，mandatory_failures=0**；原旧 L1 验证器命名失败 `run_0001`、修复重冻结 hash 和真实耗费保留。
- 评估者在路由接受前，独立读取合同、map r100、冻结计划和 L2 Gate，生成 `evidence/independent_review_20261107/PRE_ACCEPTANCE.json`：14 个关键文件 SHA-256、两角色 L2/L3 门禁哈希、同源独立成功/失败材料、HEAD 和原错误文件 SHA。
- 将 `CURRENT.md` 从 EXECUTING/Executor 交接为 READY_FOR_REVIEW/Evaluator，中央 workflow validator 返回 `OK`。这一变更没有扩大本地或 Git/网络权限，业务候选与冻结验证器未修改。
- 对 H62 原件的冻结 VP01/02/08，L3 重复核验 **2638 保护文件、3 来源数据库、HEAD 和冻结 validator**；只在隔离任务副本写合成订单与批准记录。原 L2 证据和失败原件保留。
- 当前四个业务副本：`merchant/services/checkout_service.py`、`merchant/db.py`、`APPROVAL_INBOX.py`、`ORDER_RECOVERY.py`。没有扩改 src/tests/SDK/父任务或真实外部系统。

## L3 Independent Gate / 独立回放门禁

- Gate result: PASS
- Gate summary: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/L3-GATE.json
- Validation plan: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/VALIDATION_PLAN.yaml
- Checks total: **8**
- Mandatory failures: **0**
- 原始证据：`evidence/l3_evaluator_01/RV-EV-01..08.{meta.json,stdout.log,stderr.log}`；没有复用执行者 `EV-*` 充数。
- 16 个恢复例在 `evidence/recovery_evaluator/run_0001/OBSERVATIONS.json`，独立的批准 24 例与原生 6 旅程分别位于 evaluator 独立目录；原生 18 个 ASGI 请求，原 25 项 AP2 回归检查通过。

## Acceptance matrix / AC 逐项裁决

| AC | 裁决 | 独立证据与限制 |
| --- | --- | --- |
| AC-01 保护与最小变更 | **通过** | RV-EV-01/02/08、PRE_ACCEPTANCE.json；2638 保护文件、3 原库和冻结范围检查 PASS；四个产品副本限定范围 |
| AC-02 一次订单、零恢复付款 | **通过** | RV-EV-03/04；R01/R02、过期重放与单据/库存/唯一收据逐值核验；同一类独立 M06 来源付款1/订单0/库存5 → 付款仍1/订单1/库存4，恢复额外付款0 |
| AC-03 不合格批准和输入失败关闭 | **通过** | RV-EV-03/04/06；R03–R10/R15/R16 均 DENIED、交易库无副作用，批准原回归 24/24 |
| AC-04 崩溃、竞争和撤销 | **通过** | RV-EV-03/04/06；R11–R14 提交前终止回滚、提交后终止复读同收据、双独立进程最多一次订单与扣库、撤销持锁忙拒绝和消费后 CONSUMED，进程 PID/nonce 与退出证据成立 |
| AC-05 商城共享实现及回归 | **通过** | RV-EV-05 加独立源码审查；普通 complete 与订单恢复共用 `prepare_order`；M01 正常 fake PSP 1/订单1，M02–M05 零付零单，M06 旧的查询/拒绝且不重扣；6 条旅程、18 ASGI、25 AP2 保持 |
| AC-06 证据/预算/声明边界 | **通过** | RV-EV-04/07/08；6 个判别器损坏自测拒绝；审计预留、真实 worker PID/nonce、提交前/后进程退出、原始 stdout/stderr/meta 和所有失败已存；不虚报真实身份、资金或客户收益 |

## Independent semantic review / 源码语义复核

1. **批准与实际提交的锁序**：`ORDER_RECOVERY.py:154–166` 先建立批准库 `BEGIN IMMEDIATE`，在 `_recover:59–61` 取得真实交易库连接并 `BEGIN IMMEDIATE`。两锁的持有范围跨越 `transactions.commit()`；撤销 `APPROVAL_INBOX.py:415–456` 采用同一顺序（批准锁 → 交易锁），包含 CLI `main():468–505` 复用的 `revoke()`。忙锁以 0 timeout 失败关闭，不用无限等待。
2. **订单、库存和消费权威单事务**：`ORDER_RECOVERY.py:93–123` 使用原生 `CheckoutService.prepare_order`；`checkout_service.py:816–990` 在同一 `transactions` session 预备库存、订单、checkout、成功幂等结果和购物车状态；`db.py:594–610` 定义具有 approval_id / checkout_id / payment_ref 唯一约束的 `h62_consumptions` 并在该 session flush；最终一次 `transactions.commit()`。批准库只持锁，不额外写第二份消费权威；**没有跨两库原子提交的声明**。
3. **授权重新校验与收据优先**：`ORDER_RECOVERY.py:29–43,69–106` 明确绑定批准/checkout/payment 与受信操作员/策略/上下文。首次消费要求批准未撤销、未过期、当前来源全量摘要未改变，旧确认仍有效；在写前读取真实事务视图，既有消费收据可按固定 owner/binding 重放，避免因结果丢失再执行。来自 `APPROVAL_INBOX._consumption` 的收据还验证订单/checkout 一致性，不把普通查询伪装成再次授权。
4. **撤销与崩溃边界**：撤销先拿到锁并提交，首次消费失败；消费提交先完成，后撤销读取持久消费收据，返回 `APPROVAL_CONSUMED` 而不追加 `REVOKED`。观察 hook 分别在持锁、事务提交前、提交后；冻结进程边界已重冻结真实 PID/nonce/退出检查。L3 在独立副本分别复现提交前回滚和提交后复用，未发现双订单/重扣。
5. **不扩张的真实边界**：恢复不触发 `_process_payment` / `complete_checkout` / 旧执行 claim/recover，冻监测器对这几个入口及外网调用失败关闭。恢复成功仅返回 `notification_status=PENDING_NOT_SENT`。人工操作者仅为 `LOCAL_OPERATOR_ASSUMED` 的合成信任配置；产品目录、本地 SQLite、fake PSP、标准 `CheckoutMandate` 全链路和真实客户使用均不构成生产证明。

## 业务增量、成本及剩余风险

- **已测改善**：原 M06 的固定异常类型只有付款与失败 claim，无订单；使用单次新批准的本地受控恢复，在隔离的新副本将订单0→1、库存5→4，原付款引用保持一次；旧 M06 原生重试继续 query-only，不被放松。
- **Executor 费用**：恢复 case 18/48，worker 70/320，批准 24/72，ASGI 18/80，L2 1/2；保守主动时间累计 21/360 分钟；旧失败及裸 `python` 命令 127 都计入原账。未重置。
- **Evaluator 费用**：正式独立 L3 1 次，恢复 16/32，批准 24/24，ASGI 18/40，worker 总 65/160（逐 case 操作数求和）；预接受签名/代码只读检查不计业务案例，也不回写 Executor 预算。
- **限制**：真实人身份/授权发行、真实 PSP 清算确认、跨真实商家联通、生产安装、订单通知/履约最终到达、客户收益与监管合规 **unknown**。已验证切片只覆盖一个合成商家的局部订单恢复，不代表真实自动补单可启用。本地批准被保存，不等于用户可主动签署可信商家指令。

## Project impact verdict / 项目影响

Impact verdict: IMPROVED

B-17 在**代表性的本地已付无单—人工批准—原生订单恢复**切片上形成可独立重放的能力增量，不再停留 H58/H61 的材料和设计；仍不能说 B-17 的真实商业化端到端已关闭。此前 A–D 的本地成果与 E/F 的真实性和外部集成边界保持原样。没有发现需要在 H62 内继续增加案例/添加泛化平台的正收益。

## Iteration value and continuation decision / 下一步

Continuation decision: **STOP**

**正式签收并关闭 H62 本地能力切片；不自动启动 H63、第二商城、通知平台、退款、生产 PSP 或更大 SDK 变更。** 继续给同一个合成 M06 多加场景的边际价值低于获取真正使用方/身份/PSP/商家对接证据。下一步是 Evaluator 根据可取得的真实验证条件，重新比较 E 的 Actor Authenticity（主体身份真实性）和 F 的真实商户/外部协议消费者，或保留当前 local-only；缺少授权和商家/客户证据时，不冻结外部执行包。这比擅自把本地通过扩称成生产接入更有价值。当前没有新的可授权执行任务包，下一阶段仍需新的有界评估决策，不默许额外权限。

地图 `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` 仍为冻结 H62 的 r100 保护输入；本 REVIEW 和 CURRENT 记录 H62 已改善的事实，但不在本次原验证范围内热改保护的 map 并破坏已独立验收的原件。后续重排序须在新 map revision 中显式记录新的保护基线/任务路由，不复写 H62 合同、旧证据或预算。

## External requirement impact / 外部要求

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/18/20 CORE/ADAPTER。before=本地合成批准记录可测、实际订单消费者缺失；after=在一个 local-only UCP 商家副本可通过受信配置与人工假定批准把原成功付款转为一次原生订单，具备 L2/L3 实验、代码及追溯证据。真实身份/PSP/标准互通、真实交付和监管合规仍未知。对象=H62 CONTRACT；代码=四个允许产品副本；Test=正式 VP01–VP08 两角色；Evidence=L2/L3 两套原始流、原受保护数据及恢复目录。

## Final verdict

**PASS / IMPROVED / STOP**

## L3 raw-evidence index

## RV-EV-01 — VP-01

- AC: AC-01
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-01.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-02 — VP-02

- AC: AC-01
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-02.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-03 — VP-03

- AC: AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-03.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-04 — VP-04

- AC: AC-02, AC-03, AC-04, AC-06
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-04.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-05 — VP-05

- AC: AC-05
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-05.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-05.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-05.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-06 — VP-06

- AC: AC-01, AC-03, AC-04
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-06.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-06.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-06.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-07 — VP-07

- AC: AC-06
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-07.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-07.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-07.stderr.log
- Observed result: PASS / exit_code=0.

## RV-EV-08 — VP-08

- AC: AC-01
- Meta: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-08.meta.json
- Stdout: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-08.stdout.log
- Stderr: docs/05_任务交接/H62_APPROVED_ORDER_RECOVERY_SEAM_V1/evidence/l3_evaluator_01/RV-EV-08.stderr.log
- Observed result: PASS / exit_code=0.
