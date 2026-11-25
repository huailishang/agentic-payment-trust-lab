# H90 Executor report

Task ID: H90_STORED_MANDATE_SHUTDOWN_V1
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Executor status: SUBMITTED_FOR_REVIEW

## Workspace snapshot

2026-11-25，r149，Windows Conda agent Python 3.12，S0 PASS。最终 INPUTS.json SHA-256 e6aac1c501306a2b4ef383956ecf15395f18bbb6eddb3a8e2df62a13fac588b7。384保护项通过，HEAD及源集合保持。原首轮报告、检查器和锁文件的字节级备份在 evidence/attempt-1-frozen；首轮原始失败证据在 evidence/attempt-1。

## Changed files

- src/agentic_payment_experiment/stripe_checkout_lab.py：新增 mandate_shutdowns，三元键与全局唯一事件，事务绑定锚快照、用户、委托、版本与时间，幂等及冲突拒绝，读取时校验锚。SHA-256 403dc4054c24636f5e2e742ad1e58123d9926b8e3be309c5841a4aa7f12d2a6e。
- src/agentic_payment_experiment/adapters/stripe_checkout.py：两个 stored 入口共用委托停止事实，首个外部替身动作前 DENY，无匹配复用 H88。SHA-256 d5f7c3306c9adb52caaf692d2509d189722878512f3444f972aef713158e0fb1。
- 负责人授权修订 H90 CHECK.py 的表定位及 INPUTS.json/CURRENT 摘要，不改历史 H88/H89 检查器、不改 AC、验证计划或地图。产品首版在修订期间未再改。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/L2-GATE.json
- Validation plan: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/VALIDATION_PLAN.yaml
- Attempt 1: FAIL 5/6; attempt 2: PASS 6/6, mandatory failures 0. Independent L3 NOT_RUN.

## EV-01

- AC: AC-02, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-01.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-01.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-01.stderr.log
- Result: PASS

## EV-02

- AC: AC-03, AC-04, AC-05, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-02.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-02.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-02.stderr.log
- Result: PASS

## EV-03

- AC: AC-04, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-03.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-03.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-03.stderr.log
- Result: PASS

## EV-04

- AC: AC-05, AC-06, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-04.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-04.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-04.stderr.log
- Result: PASS

## EV-05

- AC: AC-06, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-05.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-05.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-05.stderr.log
- Result: PASS

## EV-06

- AC: AC-01, AC-06, AC-07
- Meta: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-06.meta.json
- Stdout: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-06.stdout.log
- Stderr: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-06.stderr.log
- Result: PASS

## Measurement observations

S0 四位置正常放行，基线 stdout/stderr 为工具返回文本副本（换行规范化，非字节级流采集）。VP-01 七种无效输入及四种冲突全部拒绝，同事件重放同回执，D 无匹配。VP-02 两分支重开、C 后登记，同一 H89 输入，增量为 create/GET/模拟 click：

| 位置 | 原快照 SHA-256 | 无停止 | 有停止 | 事件 |
|---|---|---|---|---|
| A | 8c5c48eed70f4740a148235f1d91a6f309181b190952ce2f86baf8673ba448c9 | ALLOW 1,0,0 | DENY 0,0,0 | event-h90-stop |
| B | 073176f485887cc5946013f9a4f8d823fe506b72c367a46141dc4d82db8dfea2 | ALLOW 0,1,1 | DENY 0,0,0 | event-h90-stop |
| C | e626aa043a9d30c340d5734efe597349f5cbb3187053b77a97e7066f75dbd56b | ALLOW 1,0,0 | DENY 0,0,0 | event-h90-stop |
| D | 4a89870694b70afe5ed139fd2f568ba867fd0a594a6823ecdc9f88a0b2dd1153 | ALLOW 1,0,0 | ALLOW 1,0,0 | 无 |

A/B/C 同键 synthetic-user / mandate-h89-shared / v1，D 为同用户不同委托。停止事实锚 operation-h89-A 与 A 摘要，UTC 2026-11-12T01:00:00+00:00，LOCAL_USER_CONTROL。A/B/C 回调0，D回调1，B预创建不计增量，原图、原批准及业务状态保持，清理 PASS。VP-03 不可读与损坏锚两入口均无副作用。责任链：账本负责受理与持久化，两个执行入口负责消费与拦截，事件回执与原快照摘要关联。VP-05 124/124零跳过，VP-06 384保护通过。

## Authorized checker correction and failed attempt

首轮 VP-04 因 H88 CHECK.py:280 的 len(current - expected)==1 断言与 H90 新增 mandate_shutdowns 冲突。原 H88 定位函数的五张基础表之外现有 confirmation_withdrawals、mandate_shutdowns 两张表。失败发生于实际不可读动作前。负责人 2026-11-25 15:05 +08 明确授权执行者修正 H90 的兼容检查。仅 H90 CHECK.py 添加 schema-aware locator：明确确认撤回表，保留额外表集合约束与 event_id 唯一索引断言，局部 patch.object 替换定位函数，原 H88/H89 行为断言仍执行，退出恢复原函数。首轮 CHECK SHA ea46ef158ea3cff636349f73208f0a5bd872bf69f0421c9411c240cf0a3b4a53，新 SHA 4f9fcebfeb8dc42eb99258f442c26e0b10fbe10544dfba6dbfc928310a327656；旧 INPUTS SHA 6088a489a25f1c74051d97424d3756d1092e34b50dc8aa07df455c87c54fb12a，新 SHA 如上。未改变验收目标或历史文件。首轮原件保留。评估者须独立复核修订等价性。

第二轮 VP-04：H88 两入口 CONFIRMATION_REQUIRED，create/GET/click 增量0；不可读双入口 fail closed；旧库初始化后创建 ALLOW 1,0,0、付款 ALLOW 0,1,1；已付恢复 RECOVERED_NO_RETRY_NO_NEW_EFFECT，临时库清理 PASS。

## AC observations (Executor only)

| AC | 观察 |
|---|---|
| AC-01 | 384保护、HEAD、源集合通过，两个指定产品文件可变。 |
| AC-02 | VP-01 PASS，11项拒绝、幂等与隔离。 |
| AC-03 | VP-02 PASS，A/B/C同事件DENY/0，D正常。 |
| AC-04 | VP-02/03 PASS，无停止正常、D隔离、损坏拒绝。 |
| AC-05 | VP-04 第二轮 PASS，原图、H88、旧库及已付恢复保持。 |
| AC-06 | VP-05/06 PASS，124/124零跳过、384保护、临时库清理。 |
| AC-07 | 两轮证据、授权修订、账本及候选快照供独立复核。 |

## Impact comparison

Measurement evidence: docs/05_任务交接/H90_STORED_MANDATE_SHUTDOWN_V1/evidence/attempt-2/EV-02.stdout.log
Before: H89 限定接收面无整份停止表示。
After: 本地合成代表切片 0→1 停止事实、3/3 同键拒绝，D正常；第二轮 L2 6/6 PASS。M4 仍待独立 L3。
Delta: 本地整份委托停止表示 0→1；同键三个位置受理停止后 3/3 DENY、0 副作用，独立委托保持 ALLOW；不是已签发凭证失效的证据。
Guardrail result: 124/124、384保护与历史兼容通过。
Scope caveat: 本地受信任控制方及两个 stored 入口；不证明真实用户认证、在途竞态、旧凭证失效、渠道撤销、真实支付或累计预算。整表删除后重开与旧库迁移的区分尚未验证。

## Deviations and unresolved items

实现1/2（首版产品未再改），L2 2/2，L3 0/1。基线15.781s，L1 ingress 6.146s，L2 attempt1 16.100s，备份8.918s，兼容性自检11.114s，L2 attempt2 18.418s。主动分钟与总角色墙钟 UNKNOWN，多次 MCP 中断重连。收尾脚本首次调用因 Conda 不支持多行 -c 参数失败，未运行脚本、未发送诊断报告；不计 L2。外部成本0，未安装、服务、外部支付接口、凭据、真实支付、Git提交推送。只提交执行者候选，不代替独立评估。L2额度用尽，不重复测试。
