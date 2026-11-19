# H72R 独立复核 — 门禁全绿但负向证据仍有反例

Task ID: H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1
Reviewed baseline HEAD: c6c617c9e20e227c7bfe967cc86ed9a102034036
Role: Evaluator
Date: 2026-11-15

## Project context before review

目标为授权→绑定→受治理执行→恢复→审计可独立复核。地图r121：A–D本地关闭、E受控本地代表闭合、F当前；B-21已经缩小到复核门禁。H72真实测试四功能事实保留，完整包REJECTED；H72R只修原生查询本地化、角色用例及计量。继续重付、更换平台或重开已关闭本地业务测试的预期价值低于闭合这些明确断点。

## Pre-review checks

接受前独立核对2232保护文件、2393私有证据文件、六个当前源码摘要、全部冻结输入及11份L2原始三件套，无漂移。BASELINE SHA256为fe362ea291a7155c10ee924b8f45c190b0985f086ee9227313a218b7a3518b3f；FROZEN_INPUTS为e2c784c56e3c2b4b8ab535763133a487d471c828f926aa5b3905ea31a18991e6。接受快照包含69个任务文件，见evidence/l3_review_20261115/ACCEPTED_SNAPSHOT.json，摘要2018dce4103a3a732189313ce98d6dad74ba80bddc5655b0b4cd33b34d88e253。

执行者L2 11/11、1次已用、Gate摘要7114b42cde26efa074b68f8823def2f3c6b1dc555f1ce7a4354c582d35f32a5a。公共工作流验证退出0；报告首状态SUBMITTED_FOR_REVIEW，接受后才正常转READY_FOR_REVIEW/Evaluator。旧H72及产品/旧测试/公共工具均只读，全部新增外部权限false。

## L3 Independent Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/gate_001/L3-GATE.json
- Validation plan: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/VALIDATION_PLAN.yaml
- Independent command differences: NONE，原公共runner与原生Windows agent；本包唯一正式L3已执行，11/11。

原安全9、回归74、取证11、生命周期9、URL6实际通过；原生真实节点的标签2684354589、长度20字节、载荷摘要005106ad2d95b593b17fae67256f711e1be28e8c9a23c330d6bb769fa302f940一致。计量正确得到现场35/执行者5/评估者13，共53；额外独立负数/超额/重复序号/断序四个反例均拒绝。13份已有GET、3原始通知和只读数据库离线联结通过；没有新增网络或付款。

## RV-EV-03

- AC: AC-03
- Meta: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/gate_001/RV-EV-03.meta.json
- Stdout: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/gate_001/RV-EV-03.stdout.log
- Stderr: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/gate_001/RV-EV-03.stderr.log
- Observed result: 自报两个上下文各16/16；独立原test14反例证明其语义未完整保留，不能据数量签收。

## RV-CE-01

- AC: AC-03
- Meta: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-01.meta.json
- Stdout: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-01.stdout.log
- Stderr: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-01.stderr.log
- Observed result: 独立程序退出1，隔离实际入口接受单命令test_count从9改99的无效收据；真实原件和69个接受文件不变。

## RV-CE-02

- AC: AC-02
- Meta: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-02.meta.json
- Stdout: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-02.stdout.log
- Stderr: docs/05_任务交接/H72R_OFFLINE_REVIEW_GATE_CLOSURE_V1/evidence/l3_review_20261115/extra/RV-CE-02.stderr.log
- Observed result: 独立程序退出1；相同故意错误字典断言在标准unittest抛AssertionError，在提交的ParserCases正常返回。

## Findings

**F-01：原生测试覆盖了框架的失败入口。** NATIVE_NEGATIVES.ParserCases定义`fail(self,payload)`作为无效解析辅助函数，覆盖unittest.TestCase.fail。故意执行`assertEqual({'tag':1},{'tag':2})`和直接`fail('...')`，标准类均抛AssertionError，提交类均正常返回。原因是字典断言经该辅助函数，把说明字符串送入parse，得到NativeError后被assertRaises视为成功。并非所有断言都失效：标量1与2的不等断言在两类中都会失败，RV-CE-01/02完整保留这个对照。原正例恰好使用字典比较，因此这不是无关方法重名；12/12不能证明所宣称的全部解析验证有效。当前真实节点结构核验仍有正面证据，未发现实际节点被改写或产品错误放行。

最小修复是把辅助函数改为不会覆盖测试框架的方法名，保留12项现有测试，增加独立检查来证明故意错误的字典断言和fail调用确实失败。禁止通过捕获更多异常、重写框架失败机制或删除原正反例来取得绿色输出。

**F-02：原test14的单条命令计数语义被替换。** 原H72/PR_NEGATIVE_TESTS.py的test14将`commands[3].test_count`由9改99，要求真实入口拒绝；H72R的新test14改测顶层`test_counts.safety=99`。新CHECK.receipt_fields不检查单条命令test_count。在同一NON_ADMITTING隔离副本中，真实收据正对照返回0，只有该单条计数改99、顶层汇总保持原值时仍返回0，输出receipt_commands=7。这是明确的原负向测试语义缺失，不因现在顶层计数可拒绝而消失。

最小修复是恢复原单命令9→99变异并通过实际同一收据检查拒绝，同时保留顶层计数、原始元数据/源码/保护正面证据；不能只把变异改到当前实现恰好检查的字段。没有对真实P0或原证据做变异。

## Acceptance matrix

| AC | 决策 | 独立依据 |
| --- | --- | --- |
| AC-01 | 通过 | RV-EV-01；2232/2393保护、1843父保护继承、治理归档和原H72 FAIL保持，源码/原件无漂移 |
| AC-02 | 不通过 | RV-EV-02真实节点通过，但RV-CE-02证明原生测试类吞掉所用的错误字典断言；严格正反验证证据未完整成立 |
| AC-03 | 不通过 | RV-EV-03数量32通过，角色构造缺陷已修；RV-CE-01原test14语义仍被误收 |
| AC-04 | 通过 | RV-EV-04准确计为53/13；RV-CE-03实际计量函数拒绝负数/超额/重复序号/断序，D01声明边界保持 |
| AC-05 | 通过 | L2与L3均11/11；原9/74/11/9及URL6实际通过，原H72 FAIL不改判 |
| AC-06 | 通过 | RV-EV-10只读复算13GET、4/3/3对象、R01原付款恢复、D01唯一收据及3通知/9签名反例 |
| AC-07 | 通过 | 原件/秘密边界及零外部动作保持，执行者23.223主动分钟上界；截至本轮复核累计仍远低于480，实际L2/独立L3各1；本次评估时间另记，不清零 |

## Final verdict

REJECTED

- Failed AC: AC-02、AC-03。
- Specific fact: 正式L3 11/11，独立RV-CE-01/02仍确认错误断言被吞、原单命令计数反例被接受；L3通过不足以签收。
- Minimum repair task: H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1。
- Required rerun: 最小辅助函数更名、收据逐命令计数语义恢复；原12解析/两个角色各16/原9/74/11/9/URL6与两项冻结独立反例，统一新包L2/L3。
- Missing human fact or authorization: 本地可逆修复无新增外部权限需求；不在旧H72R中追加第二次L3。

## Project impact verdict

Impact verdict: NOT_APPLICABLE

本包是repair，不声称新产品增量。原生本地化误报及计量报零已取得独立修复证据，角色构造的旧失败也消失；负向证据自身的可靠性仍未闭合，B-21不关闭。H72四条外部功能事实及其REJECTED历史都保持；不增加已合格支付旅程、强认证、凭据治理、真实清算或商户采用声明。D01仍仅为交付记账/收据失败恢复。

## Iteration value and continuation decision

Continuation decision: CONTINUE

三处旧复核缺口已有净推进；剩余两项均为可独立复现的小范围验证代码缺陷，不是支付平台不可用。一次30主动分钟/90分钟墙钟的离线最小修复优于再付一轮、换平台或扩建验证框架；不为凑长度加业务Case。原H72与本包的L2/L3及成本保留，新包仅明确分配本地门禁额度并累计于主线480分钟和原绝对截止。若预算内无法拒绝相同反例或出现新产品风险则停止并交Evaluator，不自动扩张。

## Bottleneck movement after review

第一瓶颈进一步收窄为负向检查是否真正拒绝其声称拒绝的错误输入。原生结构比较、角色组合及真实计量已有正面证据；可信断言和原负向语义仍是签收前必要条件。最小修复闭合后停止同类扩例，再依据全局地图选择方向；真实身份、生产支付等缺口不由本包升级。

## Next execution package

- Dispatch mode: SINGLE
- Continuation action: bounded offline repair
- Next task ID: H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1
- Next contract path: docs/05_任务交接/H72R2_ASSERTION_AND_RECEIPT_PARITY_REPAIR_V1/CONTRACT.md
- Initial state and role: CONTRACT_FROZEN / Executor
- Scope: 本包只读原件基础上在新目录复制必要任务局部检查/测试实现，修两项缺陷及最小任务命名/成本适配；原H72R报告/实现/证据均只读，不改旧结论。
- Bounded budget: 30主动分钟/90分钟墙钟、1方案/2本包L2/1本包L3，主线累计480分钟及2026-11-16T04:08:37Z不延长；外部动作/安装/服务/付款/Git写入全0。
- Executor-ready check: 单目标、精确范围、排除、继承保护、7个AC、12项冻结计划、独立HOLDOUT及停止线均见新包，无缺失人类事实。

## External requirement impact

profile=PCAC-AGENTPAY；PCAC-12/20，兼顾PCAC-15，CORE/EVIDENCE_ONLY。门禁修复after仍未闭合，不改H72复合M0或声称M4。Test为冻结11项及独立RV-CE-01/02/03，Evidence为原始三件套和不变对象/通知；残余风险为负向证明缺口及真实身份/生产支付/传输级交付未测，不构成合规结论。
