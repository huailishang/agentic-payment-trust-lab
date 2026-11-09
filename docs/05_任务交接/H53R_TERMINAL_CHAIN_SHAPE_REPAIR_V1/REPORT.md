# H53R Executor Report / 最终签名链形状修复

Task ID: H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: repair
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: SUBMITTED_FOR_REVIEW

## Global position / 全局位置

高风险交易支付项目的最终目标是有证据的身份、授权、交易绑定、执行、恢复和审计链。A–D阶段关闭，E是本地受控验证，F仍需外部授权；当前B-17最前信任缺口是最后一跳授权的角色、终结性质和受众/nonce检查。H51/H52已有STOP判断；父H53固定L2/L3 9/9，但独立S04–S06模拟付款违反合同，最终REJECTED/NOT_APPLICABLE。H53R仅修一处消费者链形状判断，原父拒收事实与56/280case账本保留。修复通过后本地切片STOP，后续真实来源、完整标准/身份/Provider按独立证据新立任务。

## Workspace snapshot / 继承基线与工作区范围

Baseline CHECK.py baseline: HEAD未变；受保护1456份、冻结52份摘要相符；已有Python3.12与6项固定依赖就绪，零安装、零外网。SOURCE_COPY记录37份继承商家文件；CHECK.py scope验证**其余36份保持不变，唯一合法代码变化**为任务副本`merchant/services/ap2_authorization.py`。未改父H53、现有锁/确认/checkout服务/数据库schema/支付端口/SDK、原28/独立6冻结检查器和产品核心。CURRENT仅CONTRACT_FROZEN→EXECUTING和execution_phase提交阶段，任务/权限/地图不变。

## Changed files / 改动文件

- `merchant/services/ap2_authorization.py`：不再递归vct收集两份无序payload，而是**精确两个连续线段**、末段须SDK已知终结`kb+sd-jwt`或`kb-sd-jwt`且不得带后续KB JWT，随后复用`MandateClient.verify`对原完整token验签及委托/交易绑定、`expected_aud`、`expected_nonce`和时钟。其后按返回列表**第1跳OpenPaymentMandate、第2跳PaymentMandate**验证；必须有可信根`cnf.jwk`、终结PaymentMandate绝不能有`cnf`。形状不支持一律403且claim尚未持久化；已验签金额/币种/收款人/完整checkout/确认/执行快照原校验不动。
- `RESULT.json`：报告LOCAL_TERMINAL_CHAIN_REPAIR_OBSERVED且九项过度声明false，保留剩余缺口。
- `ATTEMPT_LEDGER.json`：观察波次和正式L2计数、工时、外部调用预算。
- `REPORT.md`：按AC和EV交接本报告；`evidence/`：每波独立保存原始 signed synthetic token、公钥、SQLite状态、PSP调用及9项门禁meta/stdout/stderr；另`CURRENT.md`仅路由状态/阶段。

## Impact comparison / 前后比较

- Before: 父H53 L2/L3固定9/9、28例一致，但独立S04角色反转、S05/S06仍可委托的末跳且aud/nonce错，均被消费者错误接受，模拟PSP/订单各+1。SDK验证的是可用委托链前缀，不保证消费者最终付款授权场景；不是官方SDK漏洞。
- After: H53R重新由冻结的独立样本生成器实时用内存四角色签名签发S01–S06，**6/6符合合同**：S01合法一次付款一次订单，S02缺可信配置拒绝、S03提交前故障同库回滚；**S04–S06变为类型化拒绝、零占用/授权记录/付款/订单且库存不变**。同时继承T01–T28完整回归**28/28**，4个正向/恢复场景各一笔假付款，24个原负例零付款。
- Delta: 从「无序嵌套字段凑齐即可支付」变为「官方验签+有序根到末跳+终结状态与aud/nonce」的本地消费者拒绝边界，兼容原28执行/并发/同键/恢复；不把修复写成产品级或真实身份/协议能力。
- Measurement evidence: 首轮`evidence/observations_probe01.json`及`evidence/tail_probe01.json`保存28+6原始观测，冻结CHECK独立可核。正式`evidence/observations_l2.json`及`evidence/tail_l2.json`单独生成28+6新签名材料；九步L2原始日志/摘要各EV链接下附。
- Guardrail result: baseline 1456保护+52冻结，scope确认36商家文件不变且仅1代码文件有改，零安装、模型/ASGI/Provider/外部网络/真实付款/Git动作。新签名私钥仅内存，假PSP不等于真实交易。
- Scope caveat: 本切片固定UCP 2026-04-08 + AP2 v0.2.0，旧版compact签名及合成身份/确认；不支持完整JCS/新AP2 checkout extension、真实身份治理、真正外部商家或Provider、跨系统撤销、所有竞态、真实用户需求，亦非监管合规性结论。

## Deviations and unresolved items / 偏差与未解决项

修复严格一文件，原H53最终REJECTED、S04–S06原始失败、父H53已接受证据原样留存；不覆盖旧文件，也不以改冻结测试隐藏根因。独立反例由原Evaluator复制的生成器重新签发，每次SDK仍可识别可委托链，**消费者拒绝才是本包修复结果**。准备的6+28测试通过，不替代正式L2或Evaluator独立L3。下一步Evaluator核对源码终结语义、三条攻击家族、正式34原始观测与强制保护，不做自动H53R2。

## Acceptance criteria

- **AC-01 / VP-01..02**：HEAD/保护/冻结摘要，36份商家源不变、唯一模块改动合法；环境固定、调用0。
- **AC-02 / VP-04..05**：S04反向类型、S05末跳中间型错误aud、S06末跳中间型错误nonce拒绝且全零副作用；SDK签名验真、完整序列/终结角色检查并未放宽expected_aud/nonce；S01合法仍可执行。
- **AC-03 / VP-03..05**：原28/28保持，S01正向、S02缺配置、S03提交前故障回滚；直接claim、变价/变币种、并发两连接、重放、一次付款及订单失败恢复原冻结证明不变。
- **AC-04 / VP-06..09**：76产品相关回归、H37八例保持，34材料复算、完整9步门禁、九项过度声明false；预算与原始失败透明，最终PASS保留Evaluator决策权。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/L2-GATE.json
- Validation plan: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/VALIDATION_PLAN.yaml
- Formal L2 attempt: **1/2，实际VP-01..09共9/9 PASS，mandatory failures=0，全部退出码0**。其中VP-03独立跑原28例、VP-04使用冻结的六例对照和反例全部符合合同、VP-05两类原始材料复算通过；VP-06相关76例回归、VP-07 H37八例通过，VP-09检查器自测与父反例判别通过。所有EV原始三件套和L2-GATE.json已落盘。
- Material case budget: probe 6+28、formal 28+6，**实际68/272**；formal L2 1/2，active_work_minutes=50/120（Executor账本），所有模型、外部网络、Provider、ASGI、真实付款、安装计数0。首轮和正式波次分别保存原始材料与独立复核结果。
- Executor只提交材料等待L3。CURRENT维持EXECUTING/Executor、next_artifact=REPORT，**不自授PASS或推送**。

## EV-01
- AC: AC-01
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-01.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-01.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-01.stderr.log

## EV-02
- AC: AC-01
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-02.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-02.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-02.stderr.log

## EV-03
- AC: AC-03
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-03.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-03.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-03.stderr.log

## EV-04
- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-04.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-04.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-04.stderr.log

## EV-05
- AC: AC-02, AC-03
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-05.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-05.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-05.stderr.log

## EV-06
- AC: AC-04
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-06.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-06.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-06.stderr.log

## EV-07
- AC: AC-04
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-07.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-07.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-07.stderr.log

## EV-08
- AC: AC-01, AC-02, AC-03, AC-04
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-08.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-08.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-08.stderr.log

## EV-09
- AC: AC-04
- Meta: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-09.meta.json
- Stdout: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-09.stdout.log
- Stderr: docs/05_任务交接/H53R_TERMINAL_CHAIN_SHAPE_REPAIR_V1/evidence/l2_executor_01/EV-09.stderr.log

## External requirement impact / 外部要求影响

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/10/12/18/20；CORE/ADAPTER/EVIDENCE_ONLY。before=父H53原28固定通过但独立S04–S06违反最终授权，REJECTED；after=H53R任务内末跳有序及终结授权拒绝/零副作用可复核，产品/生产身份成熟度不升级。Test=VP-01..09，Evidence=真实签名合成样本/SQLite/假PSP/L2与Evaluator L3；remaining=真实身份/确认、JCS/新标准、Provider、部署与跨系统撤销/客户未知，不作监管合规结论。
