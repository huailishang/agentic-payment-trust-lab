# H93 持久动作控制证据与生命周期统一收尾

Task ID: H93_STORED_ACTION_EVIDENCE_CLOSURE_V1
Task kind: capability_experiment
Contract state: CONTRACT_FROZEN
Workflow: evaluator-executor-workflow/v2.2
Baseline HEAD: df4073d95f718f06216c94d39046de6025ea33ad
Dispatch mode: SINGLE

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-25-r154
Active bottleneck: B-27
Hypothesis: H-93-STORED-ACTION-EVIDENCE-CLOSURE
Metric baseline: H91六族13行/124原回归已独立签收；H92候选1局部L1通过，但原回归独立107通过/2失败/15未运行，正式L2/L3=0。独立已发生create且返回丢失、终结写入失败→ADMITTED→停止PENDING→裸NO_EFFECT被接受→LOCAL_QUIESCENT，effect_counts=[1,0,0]。H92拒收，不追认局部能力改善。
Estimated affected scope: 现有本地SQLite、两stored入口及其原生状态视图，无真实支付或身份消费者。
Expected project impact: 保留一个持久控制机制，闭合原H92全部生命周期目标，同时消除兼容失败和无证据终结；用H91同输入前后整表而非加无关Case证明净收益。
Rollback condition: 任一零容忍、必要回归/清理失败、预算/范围/权限变更立即保全停止，交Evaluator；不自行撤掉控制机制或放宽门禁。

A/C/D本地阶段关闭；B的局部撤回/整份停止切片关闭，B-27共同控制与证据仍第一。E实际采用/真实主体与F未来接入依赖材料或权限；重复关闭切片、重做测量、引入钱包均不优于当前确定反例的有界闭合。不是新机制实验：主变化仍是H92的同一持久控制事实机制，本包合并其中实现缺陷。新ID用于保全零容忍拒收和显式修正冻结checker，累计预算不重置。

## Objective, inherited contract and single principal change

唯一目标：两个stored入口通过一个控制表建立可信准入/停用顺序、未知不重放、原交易恢复关联和不虚报静止的原生视图，并保持全部原接口兼容和安全门禁。

H92/CONTRACT.md的Frozen stop/admission semantics、Native interface、Native recovery/history、两文件/单表及排除范围完整继承。以下是仅有的实现修正和验证澄清；不改变原准入、停止优先级、O7在途承诺或支付状态机：

1. 原已取消/已付等业务状态不再接受新动作时，保持原受控StripeCheckoutError语义。停止与撤回优先返回原生DENY/CONFIRMATION_REQUIRED；已有ADMITTED/UNKNOWN无停止时INDETERMINATE/0，停止后DENY/0。不要靠删断言、绕过begin或隐藏DENIED事实修兼容。原取消/已付后的create与pay都须无provider动作；原124回归保持不变。
2. NO_EFFECT必须携带受控原生gate最小证据，decision为有效非ALLOW枚举、callback_count严格整数0、reason为合法原因列表；缺失/畸形/ALLOW或矛盾证据受控拒绝且不追加终结事实。COMPLETED仍须ALLOW/1和非空result_ref，UNKNOWN不得假造gate。摘要读取须校验同样的终结结构/引用，防单字段损坏被视作可信；摘要不等于签名。
3. 真正既有门禁的拒绝必须能写NO_EFFECT；没有可信gate的异常保持UNKNOWN或ADMITTED。已发生动作又丢返回、终结写失败时，重开不重放，停止后保持PENDING。即使provider动作尚不知结果，也不能以裸NO_EFFECT变LOCAL_QUIESCENT。信任边界是本地受信任调用者的受控记录，不声称防恶意调用者伪造整份gate或抗全库改写。
4. 保持H92全部六族13行及原生序号/关联、R1–R5、未知和仅准入重开、坏事实fail closed、可信旧库LEGACY_UNRECORDED、getter只读、原八字段回执、原图/已付事实及清理要求。O5/O6 DENY/[0,0,0]，O7 ALLOW/[0,1,1]但pending且不称真实取消。

## Allowed scope and exclusions

产品仅src/agentic_payment_experiment/stripe_checkout_lab.py和src/agentic_payment_experiment/adapters/stripe_checkout.py；沿用stored_action_control_events一个表及原索引。保留候选1为实现起点。禁止改tests、历史任务、依赖、其他产品文件、通用门禁/模型、真实支付策略或新增表。

本目录CONTRACT/CHECK/SUPPLEMENT/VALIDATION_PLAN/INPUTS为Evaluator冻结只读。Executor仅新增REPORT/SUBMISSION/evidence/只增账本和CURRENT标准执行元数据。CHECK.py从H92原checker逐字复制，仅protocol两次NO_EFFECT正控制增加明确gate_record；其余场景和124断言不变。SUPPLEMENT.py固定核查无证据/矛盾终结四负例及真实既有gate拒绝正对照；不改变旧历史成绩。发现checker问题交Evaluator，不能自行修改。

## Authorization / 授权边界

网络/API/模型/下载/安装/服务/浏览器/WSL/凭据/真实资金/Git提交推送和历史改写全部false。无新研究/数据集：已有固定反例、明确机制和checker足够。真实身份、可信生产时钟、真实渠道取消、退款/履约、旧凭证失效、恶意回滚不在范围。

## Acceptance criteria

| AC | 必须可观察的验收结果 |
| --- | --- |
| AC-01 | HEAD、历史冻结/运行/接受证据与H92拒收候选快照保持；仅两产品差异，一个控制表；原图、回执八字段及已付事实不变。 |
| AC-02 | H92三原生接口/事务/唯一准入/终结幂等及序号成立；无证据、矛盾NO_EFFECT拒绝且不改历史，真实gate拒绝可写NO_EFFECT；读取核对摘要与引用。 |
| AC-03 | 同H91六族13行及两入口真实gate/原生关联一致，O5/O6拒绝且零动作，O7先准入在途保持允许及pending，不假取消。 |
| AC-04 | 两入口丢返回、仅准入重开及新增终结写失败原反例保留UNKNOWN/ADMITTED，重开不重放，停止后DENY/0且pending。 |
| AC-05 | 原R1–R5的原引用恢复、20次新入口拒绝、10查询及单recoveries记录保持；原生RECOVERY_OBSERVED/状态解释可消费、无新付款/退款。 |
| AC-06 | 不可读/摘要坏事实fail closed、可信旧库和H88/H90守护通过；原124回归零失败零跳过、取消和已付兼容恢复、临时清理通过。 |
| AC-07 | 原生五类事件/准入及停止序号独立可回查，getter只读一致；无证据终结不使pending变静止，不以测试拼接冒充产品事实。 |
| AC-08 | 完整统一报告、前后13行整表/差异/失败成本、七组三件套、PASS L2及SUBMISSION；Evaluator接受后唯一L3及源码语义逐AC验收。 |

## Steps, dependencies and branches

S0→S1→S2→S3→S4→S5，满足前置自动继续，最终一次性交完整包，不逐步等Human。

| 步骤 | 继续条件 | 失败处理 |
| --- | --- | --- |
| S0 | 原生Windows Conda agent Python3.12，断言开启；CHECK preserve_pre核候选1、继承锁和所有历史证据 | 仅PATH/编码可恢复；漂移停 |
| S1 | 在剩余候选内一起修原生终结证据/读取与adapter兼容；保留提交先于provider、停止优先与未知不重放 | 超两文件/一表/语义范围停 |
| S2 | SUPPLEMENT及两原失败测试先验证，再跑原protocol/matrix/uncertain/guards | 零容忍立即保全停；非零容忍合同内L1定位与修正计同候选，不能新增第三候选 |
| S3 | 原124回归完整零跳过、原生引用/序号/getter只读及diff自检 | 回归/清理失败保全停；不改历史断言 |
| S4 | 公共七VP统一正式L2，目录attempt-1；仅普通非零容忍实现/启动缺陷且仍同候选可用attempt-2 | 额度耗尽或零容忍停；不得覆写输出 |
| S5 | REPORT/SUBMISSION/只增成本账本、validator后一次提交；仍EXECUTING/Executor | L2失败不能SUBMITTED_FOR_REVIEW；Evaluator接受后才L3 |

## Validation plan

Validation plan file: docs/05_任务交接/H93_STORED_ACTION_EVIDENCE_CLOSURE_V1/VALIDATION_PLAN.yaml

七VP包含原六VP和终结证据反例；机器argv/cwd/expected_exit_code在计划。L3同计划、新进程/新临时库，仅一次；不能用本轮checkpoint代替。Evaluator另外独立核事务提交点、不跨provider锁、唯一索引、原生payload摘要/引用、NO_EFFECT/COMPLETED/UNKNOWN证据、getter只读和legacy解释。共享checker通过只是必要条件。

## Cost and stop conditions

继承H92成本：1/2候选、0/2正式L2、0/1正式L3已用；H93额外上限1候选、2正式L2、1正式独立L3，H92+H93累计仍2/2/1。不以新ID、重连或修脚本重置。候选指一次完整修复实施，正常L1定位修改逐项计账；若完整送验后仍要第三版或改机制，停止重评。所有失败/环境/脚本成本追加记录；实际主动分钟、角色墙钟无法证实写UNKNOWN，外部成本0，不设虚构时间硬限。

停止后新准入、无可信准入provider动作、重复或UNKNOWN重放、历史/paid漂移、无证据终结/虚报静止、回归/清理失败、预算耗尽、变假设/范围/AC/权限均停交Evaluator。全部通过则STOP同类扩例并重排地图；若共同机制无净收益则SWITCH/STOP，不自动续包。

## external_requirement_impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-10, PCAC-12, PCAC-18, PCAC-22]
  applicability: CORE
  maturity_before: M2
  maturity_after: M4
  maturity_scope: H92候选只到实现与部分L1，M4是本地持久准入和停用生命周期切片的验收目标，须本包独立证据，不是实际成熟度或合规结论
  test_evidence: [AC-02, AC-03, AC-04, AC-05, AC-06, AC-07]
  trace_evidence: [VP-01, VP-02, VP-03, VP-04, VP-05, VP-06, VP-07]
  residual_risk: [真实控制主体, 真实渠道取消, 生产可信时钟, 实际采用, 恶意存储回滚, 退款履约补偿]
```
