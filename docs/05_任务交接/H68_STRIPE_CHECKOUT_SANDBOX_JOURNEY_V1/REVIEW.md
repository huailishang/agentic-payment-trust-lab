# H68 受阻交付复核：不具备签收条件，退回本地修复

Task ID: H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1
Reviewed baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Review date: 2026-11-12
Review disposition: NOT_ACCEPTED_FOR_L3 / RETURN_FOR_REPAIR
Executor status at review: BLOCKED

## 全局位置

目标是证明授权→交易绑定→执行前治理→支付/恢复→审计的信任链。地图r111：A–D本地阶段关闭，E仅受控本地代表闭合，F当前。B-21仍缺合格的外部支付旅程，比已延期H67和追加本地攻击更优先。H68为外部适配能力实验；本次是受阻交付审计，不是外部能力签收。

本次复核又定位了候选接缝的确认时效、原会话恢复及通知关联错误。它们是进入外部试验前的安全前提，优先于继续试浏览器或换支付平台。修复通过后才继续环境资格，再考虑四旅程；不能用本地通过替代外部证据。

## Pre-review checks / 评估前检查

- r111、CONTRACT、SPEC、来源锁、授权、计划、PCAC映射均已读。仓库授权记录为GRANTED；复核未创建沙箱、读取密钥、查询Stripe或付款。
- 在任何治理变更前，57个提交/路由文件形成只写一次快照：`evidence/blocked_review/SNAPSHOT.json`，SHA-256=`686c4a5f7335487161d76689bfab00aca212542923f72f280bac67bfba8f2410`。
- 独立核对六份L2原始输出的字节数/摘要，全部相符；VP-03/04确实失败。原L2、REPORT、RESULT、ATTEMPT_LEDGER和冻结合同/检查器没有回写。
- 独立完整性、预算关闭、工作流结构、判别器自测通过。它们都不代表外部旅程或候选产品正确。
- 新五个产品/测试/脚本文件在原允许范围；当前尚没有完整四旅程现场编排，REPORT已坦承这一点。

## L3 eligibility / 独立验收资格

Formal L3: NOT_RUN

公共技能规定：`A failed L2 stays with Executor.` 本提交L2为FAIL、状态BLOCKED，不能伪造SUBMITTED_FOR_REVIEW或READY_FOR_REVIEW。本次保存独立离线审计，不生成一份冒充完整L3的门禁；也不消耗Stripe只读额度。Review disposition是退回修复，不是已完成正式L3后的产品终态裁决。

技能来源：`../localagent-common/skills/evaluator-executor-workflow/SKILL.md`，Use L1–L3 validation gates、submission与acceptance边界。本约束仅限制签收，不妨碍已授权的本地审计、准备最小修复合同或现有隔离浏览器空白页探测。

## 独立证据

证据均在 `evidence/blocked_review/`：

| 检查 | 结果 | 原始证据 |
| --- | --- | --- |
| 提交快照及L2六份摘要复算 | 通过 | AUDIT.meta.json / stdout.log / stderr.log |
| 冻结完整性 | 通过 | INTEGRITY三件套 |
| Windows Python 3.12.3 原命令回归 | 不通过，74项中6项ERROR | REGRESSIONS三件套 |
| 判别器2对照/15损坏自测 | 通过，仅判别器 | SELFTEST三件套 |
| 关闭预算、工作流结构 | 通过 | BUDGET、WORKFLOW三件套 |
| 三个独立合成反例 | 三个均复现 | COUNTEREXAMPLES_V2三件套，REVIEW_AUDIT.py |
| 现有浏览器隔离页面打开/点击/读取 | 通过 | BROWSER_PROBE.json、三份页面快照 |

首版反例脚本也被产品数据库连接泄漏阻断，原脚本和失败COUNTEREXAMPLES三件套保留。V2只在审计脚本清理阶段执行gc.collect，使其能完成临时目录清理；没有修改产品或把Windows原回归改为通过。反例验证使用合成测试夹具，Stripe API与付款均为0。

## Findings / 发现

1. **P1：付款时沿用历史请求时间，过期确认仍放行。** `adapters/stripe_checkout.py:114`调用validate_request，后者按request.occurred_at验证确认，而本接缝的真实动作时间是now。令确认在NOW+1分钟过期，在NOW+2分钟调用authorize_browser_payment，订单和mandate仍有效，实际付款回调数为1、决定ALLOW，预期应为0。需在适配层复用既有确认验证器按当前动作时间再核验，创建会话和点击付款两个入口都覆盖，不改旧验证器语义。
2. **P1：恢复没有绑定数据库保存的原始会话。** `stripe_checkout_lab.py:263–270`只核payment_id/order_id；payment和observation的provider_ref相互相等、但同为另一cs_test会话时，底层规则仍返回RECOVERED。本例数据库原会话未变、状态仍UNKNOWN，却另存成功恢复结果。不能声称已造成真实付款或自动交付，但原交易恢复/审计结论已错绑。需先校验持久payment/request/order/session关联，再调用现有恢复规则。
3. **P2：付款对象通知可关联到任意业务操作。** `stripe_checkout_lab.py:243`仅对checkout.session.*校验session；payment_intent.succeeded即使指向外部pi_foreign_fixture，只要HMAC有效就被存为当前operation的通知。本例返回True；未自动把状态改为已付，这一保护有效，但事实血缘已污染。需将该事件绑定到原会话已验证的intent；尚未知时应拒绝或独立暂存，不接受调用者自报operation作为绑定依据。
4. **P2：SQLite上下文没有关闭连接，Windows回归不通过。** `_open():77`返回sqlite3.Connection，`with self._open()`仅完成事务提交/回滚，不负责close。独立在本机重跑原CHECK regressions，六项SQLite测试全部在临时文件清理时发生WinError32。原执行证据路径为/mnt/d，属于WSL结果；74/74只能保留为原运行环境成绩。需在成功/异常路径显式关闭连接，再在原生Windows复跑；不能靠gc.collect、忽略清理异常或换宿主掩盖。
5. **诊断边界：两种自写探针失败不等于现有浏览器不可用。** 浏览器脚本硬编码/mnt/c路径，且测试的是自建Chrome通道。当前Evaluator通过已有mcp__Playwright隔离上下文打开自写data页、点击按钮、读取到`Clicked`，随后关闭仅本次标签。没有访问Stripe，也不能据此反推Executor当时拥有相同工具，更不能证明Stripe接受自动化。但现已不应继续把“无可用浏览器”当作已证事实。下一资格测量应先复用这个现成通道。

## Acceptance matrix / AC 逐条判断

这里“通过”仅指该项已有足够本地/审计证据，不构成整包签收。

| AC | 判断 | 依据 |
| --- | --- | --- |
| AC-01 | 不通过 | 无外部沙箱/来源/对象资格，现成浏览器只证本地交互 |
| AC-02 | 不通过 | 过期确认仍触发付款回调，且没有现场链 |
| AC-03 | 不通过 | N01/C01未执行 |
| AC-04 | 不通过 | 外部R01未执行，另复现错误原会话恢复 |
| AC-05 | 不通过 | 外部D01未执行，只有离线夹具 |
| AC-06 | 不通过 | 无真实通知，另复现错绑付款通知 |
| AC-07 | 不通过 | 无外部原文与独立回查；本地关联还存在反例 |
| AC-08 | 通过（停止审计边界） | 账本闭合、112分钟左右计费主动时间；无已记录Stripe请求/付款，未见公开凭据；不声称穷尽所有宿主网络活动 |
| AC-09 | 不通过 | 冻结历史保持，但原生Windows指定回归失败 |

## Project impact verdict / 项目影响裁决

Impact verdict: INCONCLUSIVE

外部合格旅程仍0，四例均未进入可测阶段，不能换算为0%产品成功率或证明Stripe路线失败。已有代码也不签收为可复用安全适配器。原停止保护和如实保存L2失败值得保留；B-21未缩小，候选实现暴露了更前置的本地安全缺口。PCAC-06/07/08/09/11/12/18/20外部成熟度不提升，真实主体认证、密钥治理、签名信任源、资金安全与合规均不作新结论。

## Iteration decision / 下一步

Continuation decision: CONTINUE，仅指本地有界修复；STOP原H68外部运行。

新包：`H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/CONTRACT.md`，task_kind=repair。修四项已复现缺陷，标准库/本地测试、0网络/0付款/0安装，90主动分钟、2实现尝试/2L2/1L3。原H68保持BLOCKED、未接受L3的历史事实；新CURRENT显式路由修复，不把旧报告升级为通过，不重置原外部额度。

新包独立门禁通过后，Evaluator再冻结环境资格测量；只有现成浏览器、匿名资格与事件来源可用才考虑重开四旅程。若Stripe出现登录/验证码/真实资料/反自动化限制则停止；在有比较证据和权限时才SWITCH，不自动换PayPal。相比直接重试浏览器，本地修复解决已测零容忍风险；相比H67/新增本地攻击，它是下一次外部试验的必要前提。
