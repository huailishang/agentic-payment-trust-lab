# H84 独立复核

Task ID: H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1
Baseline HEAD: 69a0512d9b4235b01acec173765a35ab2939f827

## 全局位置

项目验证高风险智能体从用户授权、动作与交易绑定到受治理支付、恢复及审计的信任链。冻结地图为 2026-11-24-r141。A–D 本地代表阶段关闭，E 当前优先 B-24，F 的受控代表切片关闭且进一步接入受授权约束。B-24 的第一瓶颈是付款动作的调用方能否承担当次凭据状态与时钟责任。新增支付渠道和延期的工具幂等均无法回答该问题。H84 测量实际本地发放资格变化，下一包才处理消费者的调用责任。

## Pre-review checks

公共结构校验在接受前和切换至 `READY_FOR_REVIEW / Evaluator` 后均通过。L2 四项原始三件套可复算。确认提交 118 项、冻结 9 项、保护 232 项及提交路由原字节一致。冻结清单摘要为 `da624566566163b0cf0fa9bc50fa241f7f7439eedd16e742f9648cec51c155b6`。实查产品差异属于已验收的 H83 WebShop 接缝。签收输入见 [ACCEPTANCE.json](evidence/ACCEPTANCE.json)。

公共 runner 按顺序执行检查且会继续运行后续条目。为落实合同的“前置失败不进入现场”，先在既有 WSL Python 3.12.3 独立执行 VP-01 至 VP-03，三项通过后才接受快照和启动唯一正式 L3。该预检未启动发行者。H85 将现场前置阻断放入现场入口本身。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/L3-GATE.json
- Validation plan: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/VALIDATION_PLAN.yaml

四项强制检查均退出 0。现场 RV-EV-04 为 22.049 秒。两轮来源各有 83 份公开索引，postcheck 独立核对三件套摘要、固定 SPIRE 资产、证书链与挑战签名，并核对清理与提交原件。L3 门禁摘要为 `3f620913ec84691bc752cb81aeacd316f6905964809ec7d3008d7b1f3b831c51`。见 [独立复算](evidence/POSTCHECK.json)。

## Acceptance matrix

| AC | 裁决 | 独立依据 |
| --- | --- | --- |
| AC-01 | 通过 | RV-EV-01/04，接受前后 118/9/232 项零漂移。授权、现有 WSL、70,187,551 字节归档和两个成员摘要相符。 |
| AC-02 | 通过 | RV-EV-04，独立新根与 nonce，UID1001 取得唯一 SVID 并持有签名。另用密码库从原始根、叶及挑战复算；原验证器为 VALID。驱动将本次 Fact 关联至模拟付款，WebShop 为 VERIFIED / ALLOW / 1。 |
| AC-03 | 通过 | RV-EV-04，删除唯一新登记一次，原始删除响应成功。同 UID 同专属 socket 第二次探针返回 PermissionDenied / no identity issued。独立轮次从删除到探针完成约 5.206 秒。叶仍在证书有效期内。相同订单摘要，不同模拟动作，驱动省略旧 Fact 后为 BOUND / ALLOW / 1。 |
| AC-04 | 通过 | RV-EV-02/03/04，历史样本是离线接线对照，原六组 42/6/6/6/18/8 共 86 项、零跳过。每轮正负动作各一个模拟回调。原始清理及评估者追加只读检查均显示本轮私有目录和归属进程已清理，公开私钥文件为零。 |
| AC-05 | 通过 | 正式 L2/L3 各 4/4，各一次现场。两轮根、nonce、现场 ID 各异，原始三件套完整。评估者在独立复算后确认已接受原件零漂移。 |

## RV-EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-01.meta.json
- Stdout: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-01.stdout.log
- Stderr: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-01.stderr.log
- Result: PASS

## RV-EV-02

- AC: AC-02, AC-04
- Meta: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-02.meta.json
- Stdout: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-02.stdout.log
- Stderr: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-02.stderr.log
- Result: PASS

## RV-EV-03

- AC: AC-04
- Meta: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-03.stderr.log
- Result: PASS

## RV-EV-04

- AC: AC-01, AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-04.meta.json
- Stdout: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-04.stdout.log
- Stderr: docs/05_任务交接/H84_B24_AUTHORITY_EVIDENCE_QUALIFICATION_V1/evidence/l3/RV-EV-04.stderr.log
- Result: PASS

## Final verdict

PASS

每角色各一次 Server/Agent 启动，一次登记创建和删除、三次初始取证、一次签名、两次删除后探针。首个删除后探针仍成功，明确拒绝以第二次为准。两轮分别约 5.242 和 5.206 秒，仅描述本次观测。安装、下载、外部 API、真实或外部测试支付、Git 提交推送均为零。实际主动时长和底层传输总字节 UNKNOWN。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

H84 为 evaluator_design 测量，产品代码零改动。证据推进到同一受控工作负载的实际发放资格变化，以及驱动据此选择是否提供 Fact 时的身份等级差异。两轮受控对照的付款决策均为 ALLOW。挑战签名覆盖工作负载身份、nonce 和挑战签发时点，动作关联由实验驱动记录。当前证据范围包括本地发放资格和来源传播，生产可信授时、实际调用责任、轮换、用户撤销和证书全局吊销保持 UNKNOWN。PCAC-03/05/06 增加受控观测证据，PCAC-09/12/20 原守护通过，PCAC-10 的用户授权撤销成熟度维持原判。

## Iteration value and continuation decision

Continuation decision: CONTINUE

B-24 继续，H84 相同驱动的发行例和状态扩例停止。当前驱动在 `MEASURE.py` 根据探针结果手动切换传参。静态回查发现，仓内 `gate_webshop_buy_now` 的生产代码定义、验证脚本及测试调用均未展示一个可独立证明逐次取状态的生产消费者。现有 WebShop 同旅程 `integration_phase` 连接 `GovernedPaymentAction`、确认、真实门禁函数及模拟回调，适合用作单个本地代表入口。扩大来源例、切换 Stripe 或叠加轮换的成本更高且无法补当前调用责任。永远多收一条来源记录也无法替代动作绑定。

## Next execution package

下一任务为 `H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1`，状态 `DRAFT_CONTRACT / Evaluator`。SINGLE 能力实验以同一个受治理 WebShop 入口承担按次取证、时钟和动作绑定为唯一变量，并要求守住既有准入和回归。H85 尚缺针对两角色各一次本地隔离现场的授权。H84 的授权限定本轮，已按角色用完。r141 地图和 H84 终态路由归档后进入 r142。见 [H85 合同草案](../H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/CONTRACT.md)。
