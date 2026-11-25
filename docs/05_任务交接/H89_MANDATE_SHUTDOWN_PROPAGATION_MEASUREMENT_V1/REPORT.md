# H89 Executor report

Task ID: H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Executor status: SUBMITTED_FOR_REVIEW

## Workspace snapshot

2026-11-25，项目地图 r148，原生 Windows Conda agent Python 3.12.13，断言开启。INPUTS.json SHA-256 7b4c4289f87aece8f236cff218b765d44de4d96012173537cad28068c2d6f760，HEAD、source set、325 项锁定输入（含历史 H88 和 r147 归档）均通过。已有 H88 两个产品文件差异与地图差异为执行前继承差异，非 H89 新改动。L1 preserve/inventory/qualification 均通过；所有额外权限 false。

## Changed files

产品/测试/冻结脚本/历史证据/地图新增修改均为 0。仅本任务 REPORT.md、SUBMISSION.json、evidence/attempt-1、evidence/ATTEMPT_LEDGER.jsonl、CURRENT 标准执行与提交元数据。无提交/推送；只读 Git diff --check CURRENT 无空白错误，LF/CRLF 提示不改变冻结文件。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/L2-GATE.json
- Validation plan: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- 正式 L2 1/2：6/6，mandatory failures=0；L3 0/1。Gate SHA-256 94e11c8d2e9b7cba89b1217dfdd5d7458a976f8926c11b93222ad971eae0aa2e。

## EV-01

- AC: AC-01, AC-03, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-01.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-01.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-01.stderr.log
- Result: PASS

## EV-02

- AC: AC-02, AC-05, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-02.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-02.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-02.stderr.log
- Result: PASS

## EV-03

- AC: AC-03, AC-04, AC-05, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-03.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-03.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-03.stderr.log
- Result: PASS

## EV-04

- AC: AC-04, AC-06, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-04.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-04.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-04.stderr.log
- Result: PASS

## EV-05

- AC: AC-06, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-05.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-05.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-05.stderr.log
- Result: PASS

## EV-06

- AC: AC-01, AC-06, AC-07
- Meta: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-06.meta.json
- Stdout: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-06.stdout.log
- Stderr: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-06.stderr.log
- Result: PASS

## S0–S2: Native receiver and qualification

EV-01/02：四业务位置资格及清理 PASS。固定 NOW，A/B/D 先登记并保存原图，B 预先创建成功且绑定会话；A=CREATED、B=SESSION_OPEN，C 尚未登记。同一用户 synthetic-user，A/B/C=(mandate-h89-shared,v1)，D=(mandate-h89-other,v1)；max_count=3，A/B/C sequence_count=1/2/3，D=1。订单、请求、付款、确认、操作 ID 各自独立，合成上下文从 CHECK.py 103–129、132–175 可复算。仅验证逐请求合法性，不证明累计次数或预算。

限定原生接收面人工核验（完整 13 个公开方法及参数在 EV-02 stdout，非全仓扫描结论）：
- models.py:90–102，IntentMandate 为冻结数据对象，字段 mandate_id, user_id, max_amount, allowed_merchants, allowed_categories, expires_at, max_count, confirmation_above, expected_agent_id, currency, authority_version；没有整份委托停止状态或事件入口。
- stripe_checkout_lab.py:117 register（操作、run、case、order、request、payment、resource）；156 get(operation_id)；191 record_authority(operation_id,ctx,*,resource_sha256,recorded_at)；275 load_authority(operation_id,*,expected_sha256)。原图登记/读取与业务状态，不是委托撤销。
- 335 record_confirmation_withdrawal(operation_id,*,expected_sha256,confirmation_id,subject_ref,event_id,received_at)；366 get_confirmation_withdrawal(operation_id,*,expected_sha256)。285–314 校验原图确认、主体、事件、时间；318 按 operation_id 读取；357 按原操作和确认写入。原生事件键是单操作/单确认及原图摘要，不是 user+mandate+version。公开登记是受信任本地控制边界，不证明真实认证。
- 377 bind_session(operation_id,session)；412 mark_unknown(operation_id)；423 observe(operation_id,session,intent,charge)；479 ingest_webhook(*,operation_id,body,signature,test_secret,received_at)；514 recover_original(operation_id,payment,observation)；541 record_client_delivery(operation_id,received,*,inject_failure=False)；576 delivery_history(operation_id)。这些是操作、观察、恢复或履约；observe 441–446 对原会话 expired/unpaid 观察转 CANCELLED，不是整份委托停止登记。身份撤销是主体状态/凭据方向（trusted_execution/execution_facts.py:210 identity_status_revoked），对象不同。
- adapters/stripe_checkout.py:265–274 共享投影，调用 load_authority 与 get_confirmation_withdrawal(operation_id,expected_sha256)，仅对应单次事实转 REVOKED；276 create_stored_session(store,*,operation_id,expected_authority_sha256,success_url,cancel_url,now) 与294 authorize_stored_browser_payment(store,*,operation_id,expected_authority_sha256,now,browser_payment) 共同消费该投影，再检查 CREATED/SESSION_OPEN 与调用原生门禁。

结论：限定接收面 NOT_REPRESENTABLE_IN_FROZEN_NATIVE_SURFACE，没有发现新可用候选。与“提交了整份撤销但被拒绝”不同：整份事件未提交，accepted=false / NOT_SUBMITTED_NO_NATIVE_RECEIVER。未伪造状态、未调用其它入口。

## S3–S4: Measurement observations

EV-03 三套独立临时 SQLite 库、同一输入、FakeStripe 与列表回调。B 每个分支预创建计数 1 单列（不计入表中动作增量），重开后登记 C，随后 A/C/D 创建、B 付款。四位置绑定索引如下，所有分支一致；表中位置可连接完整原生证据。

| 位置 | subject_ref / mandate / version | 确认 / operation | snapshot_sha256 |
|---|---|---|---|
| A | synthetic-user / mandate-h89-shared / v1 | confirmation-h89-A / operation-h89-A | 8c5c48eed70f4740a148235f1d91a6f309181b190952ce2f86baf8673ba448c9 |
| B | synthetic-user / mandate-h89-shared / v1 | confirmation-h89-B / operation-h89-B | 073176f485887cc5946013f9a4f8d823fe506b72c367a46141dc4d82db8dfea2 |
| C | synthetic-user / mandate-h89-shared / v1 | confirmation-h89-C / operation-h89-C | e626aa043a9d30c340d5734efe597349f5cbb3187053b77a97e7066f75dbd56b |
| D | synthetic-user / mandate-h89-other / v1 | confirmation-h89-D / operation-h89-D | 4a89870694b70afe5ed139fd2f568ba867fd0a594a6823ecdc9f88a0b2dd1153 |

| 分支 | 位置 | 门禁 | 回调次数 | create/GET/click 增量 | 单次事件受理回查 | 整份事件 accepted |
|---|---|---|---|---|---|---|
| none | A | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| none | B | ALLOW | 1 | 0/1/1 | 无对应单次事实 | false |
| none | C | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| none | D | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| withdraw_A | A | CONFIRMATION_REQUIRED | 0 | 0/0/0 | event-h89-A | false |
| withdraw_A | B | ALLOW | 1 | 0/1/1 | 无对应单次事实 | false |
| withdraw_A | C | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| withdraw_A | D | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| withdraw_B | A | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| withdraw_B | B | CONFIRMATION_REQUIRED | 0 | 0/0/0 | event-h89-B | false |
| withdraw_B | C | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |
| withdraw_B | D | ALLOW | 1 | 1/0/0 | 无对应单次事实 | false |

A/B 单次受理事实分别 event-h89-A/B，经真实 H88 接收接口登记，回查与提交完全一致，source=LOCAL_USER_CONTROL，received_at=2026-11-12T01:00:00+00:00。C 在事件位置后登记（NOW+1s）；两非空分支只对应目标阻断，重开后仍生效。其它确认和另一委托正常放行。三分支 original_snapshots_unchanged=true，原图 CONFIRMED 不变，temporary_cleanup=PASS。12 行=10 ALLOW+2 CONFIRMATION_REQUIRED，目标已受理单次撤回后副作用为零；整份撤销受理=0，不能宣称发生整份撤销后误付款。

## S5: Causal analysis and mechanism constraints

三种解释：①整份接收缺口：限定公开面无合法接收入口，两个既有消费者共用按单操作读取投影；②单次隔离正确：两合法事件只影响对应目标，A/B互不影响，C未来动作和D另一委托仍放行；③整份撤销后的执行结果仍 NOT_JUDGEABLE，因受理事实不存在。①和②并存，不是H88退化。两业务状态的共同断点是接收对象及查询作用域，不是各自支付执行器的错误。EV-02/03 与上述源码定位支持，未观察到零容忍反例。

以下是给 Evaluator 的候选机制约束，不是实现或新增合同：

| 约束 | 最小要求 |
|---|---|
| 停止键 | 精确绑定 user_id+mandate_id+authority_version；不能按用户全量停止，也不能按 operation_id 代替整份停止。 |
| 信任来源 | 独立可信用户控制入口，验证主体和原委托绑定；不信任 Agent 自报；真实用户认证另议。 |
| 生效排序 | 事务受理提交先于下一次门禁读；时间作证据而非假定生产可信钟；明确重复/冲突和持久化。 |
| 原图保全 | 原授权、单次撤回及历史交易不可覆盖；另存可复核停止事实，保留历史已付恢复。 |
| 失败拒绝 | 状态无法读取、绑定不一致或事实不可信时副作用前拒绝；不能吞错后按原图放行。 |
| 新动作覆盖 | 同键既有 A、B 与未来 C 均消费同一停止事实，D 另一委托不受影响；保留 H88 单次隔离。 |
| 残余边界 | 在途竞态、真实入口/用户认证、跨渠道传播、旧卡凭证失效、累计预算、退款和真实支付均未测。 |

CONTINUE 候选：独立 L3 及逐 AC 确认共同断点与安全守护后，Evaluator 可冻结最小能力建设包。若新证据显示已具完整链/无共同断点或边际价值低，STOP/SWITCH；若仍缺可复核受理或消费者证据，标 NOT_JUDGEABLE，不自行建设。若出现已受理后副作用或漂移，停止保全重新排序。当前不替代评估者作最终判定。

## S6: Guardrails

EV-04 两入口 H88 单次撤回、同事件重放、两冲突拒绝及不可读拒绝全部通过；EV-05 十组 124/124 原回归、0 skip；EV-06 325 项保护保持。全部临时目录清理断言通过。未发外部请求、未真实付款。原有 H88 能力未退化。

## AC observations (Executor only)

| AC | 执行者观察 |
|---|---|
| AC-01 | HEAD/源集合/325 锁定输入零漂移，继承H88和地图归档，产品修改0；EV-01/06。 |
| AC-02 | 13公开方法与11字段枚举，签名和源码回查，控制对象区分，限定面无整份入口；EV-02。 |
| AC-03 | 四位置资格、三同键与一隔离键；正常四行动作及B预创建成功；EV-01/03。 |
| AC-04 | 两事件受理与重开回查一致，仅目标阻断，C后登记仍正常，原图保持；EV-03。 |
| AC-05 | 12行完整绑定/门禁/回调/增量/受理事实；定位共同断点，整份行为NOT_JUDGEABLE；EV-02/03。 |
| AC-06 | H88守护、124/124零跳过、325保护及清理通过；EV-04/05/06。 |
| AC-07 | 一次统一报告、原始L2、账本、机制约束及提交快照；待独立L3与语义回查。 |

## Impact comparison

Measurement evidence: docs/05_任务交接/H89_MANDATE_SHUTDOWN_PROPAGATION_MEASUREMENT_V1/evidence/attempt-1/EV-03.stdout.log
Before: 整份委托停止接收与传播未知，H88仅单次代表切片已关闭。
After: 限定面确认无整份原生接收；实测单次传播仅目标，三分支12行及同键未来动作、异键隔离证据明确。
Delta: 信息增益，产品改动0，capability_gain NOT_APPLICABLE；不计产品成熟度提升（PCAC整份停止 M1→M1，H88单次M4保持）。
Guardrail result: 124/124，325保护，H88两个入口不退化。
Scope caveat: 仅单一既有本地消费者；没有真正整份委托撤销被受理，无生产/外部支付与合规结论。

## Deviations and unresolved items

未遇到需修正冻结方法或环境的阻塞。实际采用已有 Windows agent。L1 preserve 8.634s、inventory 3.955s、qualification 2.935s；正式 L2 工具墙钟 14.337s；这些不是人工主动时间。请求时间约 2026-11-25 10:10+08:00，正式运行后本机时钟观察 10:11:59+08:00；精确角色总墙钟与主动分钟 UNKNOWN。正式 L2 1/2，独立 L3 0/1，产品实现0，外部费用0。无安装、服务、WSL 测试、模型/API、浏览器、凭据、真实支付、Git 提交推送。原始证据保持；下一步 Evaluator 接受提交快照并独立 L3。
