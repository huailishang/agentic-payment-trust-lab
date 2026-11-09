# Agentic Payment Trust Lab 项目瓶颈地图

Map revision: 2026-11-09-r105
Last reviewed: 2026-11-09
Map owner: Evaluator / Human Task Owner
Status: ACTIVE

本版记录H64R开工前显式基线迁移：HEAD已前进，四个保护文档仅行尾空格变化，旧字节已找回并保存；H64拒收与H64R修复语义保持。下载访问限制属实，金额/关联测量尚未有效，不新增产品能力成绩。局部通过不等于真实商户、生产身份、资金网络或监管合规已获证明。

## Project outcome / 项目结果

在本地、可重置的边界内，证明用户授权、Agent动作、订单/支付绑定、执行前治理、异常恢复和审计形成可回放、可解释、可独立复核的信任链。错误放行、漏确认、重扣/重单、低可信来源覆盖确认、错绑、无前置治理的副作用是零容忍风险。

不扩张为通用Agent Runtime（智能体运行时），不以真实资金或生产支付接入为当前目标。客户需求、付费价值与工程能力分别记账。

## Global capability roadmap / 全局能力路线

| 阶段 | 状态 | 声明边界 |
| --- | --- | --- |
| A 评测与治理底座 | 本地阶段关闭 | 固定基线、守护线与独立复核已有代表证据 |
| B 授权、绑定、来源、执行前治理 | 本地阶段关闭 | 明示授权、绑定、确认、来源与受治理执行 |
| C 支付生命周期、恢复、补救证据连续性 | 本地阶段关闭 | 代表性恢复/补救链；H62增加单个商城订单恢复切片 |
| D 责任归因与可消费审计链 | 本地阶段关闭 | Consumer/Read Model/Player（消费器/读取模型/播放器）已有代表覆盖 |
| E 主体真实性、凭证与签署指令 | 受控本地代表性闭合 | 本地凭证/持有证明；真实强认证、凭据治理、签名信任源仍未知 |
| F 外部协议、SDK与消费者适用性 | 当前 | 官方AP2两跳与商城本地副本已有结果；真实主体/PSP/部署/消费者未闭合 |

## End-to-end capability chain / 端到端能力链

用户授权 → 可信来源/主体事实 → 动作与交易绑定 → 副作用前治理 → 支付/订单执行 → 异常处置 → 权威证据 → 可消费审计。

H62使单个本地异常类型从“付款成功而订单缺失，只能查询”前移为“新批准→原生订单事务→唯一收据→重放同结果”；仍不代表真实商户订单、用户身份或履约完成。

## Measurement basis / 测量基础

- measured（已测）：H62 REVIEW、L2/L3各8/8；独立16恢复/24批准/6商城旅程/25AP2。同类新M06付款1/订单0/库存5→付款仍1/订单1/库存4，恢复新增付款0；原2638保护文件及3来源库保持。
- measured（已测）：H63准备核对H62目录1154文件和原2638保护文件；CartTrace源固定revision `86cab5e539e161e0915d78d8abdd9023f09b411e`，按路径规则取得6份JSONL预览，未按结果挑选。
- measured（已测）：六预览只有session/message记录。**预览缺独立后端状态表是已知边界，不作为待重新发现的假设**；整个数据集的支付/订单/事件表充分性不由预览推断。
- measured（已测）：H63独立L3结构4/4，但AC-03合同语义错位，REJECTED（拒收）；原件保留。H63R已独立L3 3/3、30映射语义审阅和4个原错误变异通过，PASS（通过）/NOT_APPLICABLE（修复不评价能力增量）/STOP（停止该视图）。30映射为8项部分输入、22项缺失、0项完整可观察，不是产品通过/失败率。
- measured（已测）：S01/S02/S03/S06仅有P1/P2零散输入，S04/S05对应输入缺失；六例均无完整P3执行身份、P4来源/上下文策略、P5治理回放输入。S03/S06调用关系可读，但重复同一六例的新增信息收益低。
- measured（已测，仅准备）：H64固定数据revision及GitHub回放实现commit `61f05faadc64badedd0ca727778ea5c9cd384702`，校验14份静态代码/文档的Git blob归属，取得完整数据索引和校验和；未查看新episode、未安装解码器或运行回放。代码存在缺call id按顺序回退及域名替换，已知边界不充作下一轮发现。
- estimated（估计）：H64 180主动分钟/2L2、6个固定规则新样本、20GET/256MiB，唯一隔离PyArrow解码依赖约28.6MB；不安装上游，不调用产品/模型/支付。准备获取与执行预算分开，实际见H64 PREPARATION/READINESS。
- measured（已测）：H64选定6新例、4 Parquet及11/12 world材料，18 GET/88,710,515字节、两次同envpack失败，1次解码安装；独立L3结构4/4、8纯函数例通过，但AC-02/03语义不通过，REJECTED/INCONCLUSIVE。第4例关联值32/32/34混拼；第6例协议total=4425、currency=usd、checkout可见而被统一payment=None丢弃。
- measured（已测）：缺失envpack属于INPUT_LIMIT（输入获取受限），不是源文件不存在；5例world对完整。原始付款观察、单位/授权绑定、实际后端状态必须逐维清点，不能由通用空输入推断全部源不可用。
- estimated（估计）：H64R仅复用原六例与现有材料，90主动分钟/2L2/至多12次sample读取，网络/安装/产品/回放/模型/付款0。先修离线关联/金额清点比重试下载更有直接信息收益。
- measured（已测，仅开工准备）：评估者核对H64R原3816保护/7冻结文件；3812保护及7冻结一致，另4文档共10行各去除两个行尾ASCII空格，原Git blob字节均匹配旧摘要。已保留原BASELINE/合同/路由/地图及差异文件原字节，显式迁移至HEAD 211151e；CHECK/计划和测量范围/预算不变。未读取样本、未执行正式L2/L3，不增加产品能力成绩。
- unknown（未知）：本仓控制效果、独立未见样本泛化及新来源可用性；真实商户/PSP/客户价值。不能由六预览缺本仓内部对象推断整个数据集不可用。
- estimated（估计）：H63测量120主动分钟/2L2、中低维护成本，运行时/模型/支付/安装0。准备匿名公开读取10文件/727832字节；公开网页研究另计，不写成零网络。

## Bottleneck register / 瓶颈登记表

| ID | 范围 | 当前证据与缺口 | 状态 |
| --- | --- | --- | --- |
| B-01/03/07/08/09/10/11/12/13/14 | 评测、重扣、轨迹、责任与消费 | 继承r100代表性结果，无新反例不重开 | LOCAL_STAGE_CLOSED |
| B-05 | 数据最小化 | 字段名级本地闭合；真实PII/完整隐私治理未证实 | LOCAL_STAGE_CLOSED |
| B-15 | 主体真实性 | 受控本地代表闭合；真实发行者/凭证/认证未证实 | CLOSED_WITH_LOCAL_BOUNDARY |
| B-02/04 | 血缘收益与Agent行为长尾 | 无新共同失败 | WATCH |
| B-16 | 横向外部攻击 | H46源片段停止，不重测既知完整入口语义缺口 | WATCH / SOURCE_SLICE_STOPPED |
| B-06 | 真实身份/外部支付服务方 | 支付宝有效Payment-Proof及绑定仍缺；Human后置，权限不恢复 | DEFERRED / HUMAN_DEFERRED |
| B-17 | 商城批准与业务恢复 | H62本地代表性已付无单改善；真实采用/履约未知 | LOCAL_SLICE_CLOSED / REAL_ADOPTION_UNKNOWN |
| B-18 | 独立外部轨迹可判定性 | 完整材料已部分取得，测量有混拼id/丢弃金额缺陷；独立可判定性未闭合 | ACTIVE / H64R_OFFLINE_MEASUREMENT_REPAIR |

## Active bottleneck / 当前第一瓶颈

Active bottleneck ID: B-18

当前第一证据缺口仍是外部轨迹能否支撑合同有效的独立判定。眼前阻塞是正确清点已经下载的事实：逐个call id关联、保留已报告金额，再独立判断单位/授权/后台状态。H64R不建设支付控制，也不要求最终必须可判定。固定旧六预览停止保持；不继续扩M06或提前声称泛化。

离线修复预算优于先补缺失world：补齐下载不会修复已经存在的混合id及恒空金额输入。四Parquet和5组完整world已足以定位测量错误，无需网络。H62和B-16已知片段不重开，B-06真实支付仍Human后置。原H64 INPUT_LIMIT事实保留，不授权第三次GET；外部源不必包含本仓内部同名对象，原始观察和缺失维度分别记账。客户需求仍未知。

## Active hypothesis / 当前假设

Hypothesis ID: H-64
Hypothesis status: inherited measurement-only / H64 rejected / H64R CONTRACT_FROZEN / SINGLE / Executor

继承命题不变，但先纠正测量：同六例逐call关联，分别保留请求/令牌额度/协议报告完成的金额，说明确认到checkout/单位/后台状态哪些可证、哪些仍未知。只修源测量，不运行上游或本仓；修复通过后再决定是否另冻回放基线，不能用八个合成纯函数例替代实际源输入清点。

当前合同：`docs/05_任务交接/H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1/CONTRACT.md`，开工前基线修订见同目录`AMENDMENT_20261109.md`；H64拒收证据见其REVIEW及RV-EV-06。H63R既有签收/停止、H63原拒收不改。原六例不是已证实未见留出集；确认文字不是强身份，协议成功不是独立PSP记录，缺签名也不等于源金额字段不存在。

## Candidate experiments / 候选与比较

| 方向 | 分类与动作 |
| --- | --- |
| CartTrace固定六预览 | REFERENCE_ONLY（只参考）；来源资格测量完成，STOP_PREVIEW_VIEW，不升级ABSORB（吸收）或导入产品；不外推整个源 |
| CartTrace完整表/world/静态回放实现 | REFERENCE_ONLY（只参考）；H64测量拒收，H64R只离线修源事实关联/金额，不启动回放/产品对照或新下载 |
| APort Vault | REFERENCE_ONLY（只参考）；文件访问需申请且分享账号信息，不申请/下载 |
| Gordon AgentCommerceBench | REFERENCE_ONLY（只参考）；受限且含生产来源，不申请、不接链/服务 |
| ModelScope ACEBench线索 | REFERENCE_ONLY（只参考）；工具能力资料不足替代授权/支付状态证据，不展开 |
| E本地再扩、通知平台、第二商城、H56 | 不派发；缺新消费者需求或反例；H56仍未执行，无新成败结论 |

## Reassessment triggers / 继续、停止与切换

- CONTINUE（继续）：先通过H64R的逐源语义复核，恢复测量有效性；再按各例关联/单位/后台证据决定是否另冻回放基线，不自动进入对照或付款。
- INPUT_LIMIT（输入受限）：下载/解码/预算不足与数据本身无证据区分；保留失败和限额记录，后续授权/资源取舍再评估，不无限重试。
- STOP（停止）：仅有评分/助手陈述，缺明确绑定或新增信息；停止该预览视图，不无限下载/适配。
- SWITCH（切换）：独立反例显示另一个零容忍边界更优先，或取得经许可、脱敏且可判定的新消费者轨迹。
- 真实身份/网络/资金/凭证/数据分享仍需相应授权；本轮不改变四项Git/API旗标。

## Historical preservation / 历史保护与新基线

r100原SHA-256=`ec6bb8f8895a6e8dfb9c284ba37c5fb5c530c6966f030378280f38bc19633328`。当前展示归档 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261106_r100.md` 在第5/6行各去除两个行尾空格，当前SHA-256=`7960dd28efa9a7ec50d98171ff33254e380fbc06151f970267d892063abd6109`；2026-11-09已从本地Git blob a32aad586492a7feaa7d4b881cee177e295115bb找回旧字节并匹配原摘要，完整原字节编码保存在H64R `evidence/governance_refreeze_20261109/DRIFT_AUDIT.json`。历史字节复现用该旧快照，不声称当前展示文件仍有原摘要。H62合同、报告、计划、判别器、INPUTS与全部证据不回写。

当前地图与CURRENT为H62签收后的显式治理变更。H63 BASELINE记录旧路径→归档路径及H62/其他工作区摘要。H62冻结checker要求原路径/工作区集合，不能在新增任务后的当前工作区直接重跑并把预期治理差异当产品回归；历史复现须在隔离原基线中进行。H63只核历史保持与新范围，不重跑H62业务。

H63R完成L3及终态结构校验后，r101逐字节归档为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261107_r101.md`，SHA-256=`24edf9d63cbbb1812816bc048893b668366faec6247bf5ef87c2e7b8c4b19935`。r102是验收后治理更新，不重写H63/H63R冻结BASELINE、合同、报告、数据或L2/L3；保护检查历史复现使用原地图与工作区快照。更新审计见H63R `evidence/GOVERNANCE_UPDATE_20261108.json`。

r102原字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r102.md`，SHA-256=`c0a1617e9b94ed1399886faa3e18344912d8be90a50ed43910d5d37f8ba4206a`；H64 BASELINE将r103作为新保护输入，并保护H63R/H63/历史工作区和原三库。旧CURRENT完整副本见H64 references/PRIOR_CURRENT.md；不在新路由下重跑历史全工作区checker。

H64完成独立L3与拒收结构检查后，r103归档为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r103.md`，SHA-256=`0fd46544e823738b164210264a21c2e220e24c4324f06b0e187c55c2a311ad9d`；r104为新修复治理基线。H64R保护完整H64提交/原证据/已获材料、原三库及既有解码器，不回写旧预算或重跑旧全工作区checker。

r104原字节保存为 `docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261108_r104.md`，SHA-256=`c22c10c5c6e89623d66cbfbfceef122b7aa3e1ba4c2ec3f7d0be3199420e2020`。r105仅修正执行基线和历史字节声明；B-18排序与H64R任务范围不变。旧CURRENT、合同、BASELINE及全部7冻结文件的字节另存H64R `evidence/governance_refreeze_20261109/ORIGINAL_SNAPSHOT.json`；不覆盖旧L2/L3或失败准备证据。

## Revision log / 修订记录

| Revision | 证据与决策 |
| --- | --- |
| 2026-11-09-r105 | 评估者核清HEAD漂移和四文档10行尾空格差异，找回全部旧字节并保存审计；同一H64R显式迁移执行基线，CHECK/计划/预算/授权不变。r104逐字节归档；仅恢复可开工条件，无新测量或产品通过结论。 |
| 2026-11-08-r104 | H64独立L3结构4/4、语义AC-02/03不通过；原调用id混拼/已报告金额被丢弃，REJECTED/INCONCLUSIVE。冻结H64R离线最小修复，0网络/安装；下载限制保留，不能据此否定源或声称产品漏洞。归档r103。 |
| 2026-11-08-r103 | Human要求制定新包；固定完整表/world与代码来源、规则/选择/预算/依赖，H64 CONTRACT_FROZEN，尚未执行。B-18测量主线，不恢复真实支付权限；归档r102，原H63/H63R不改。 |
| 2026-11-08-r102 | H63R PASS，独立L3 3/3及30映射语义复核；原H63拒收保留；停止六预览资格研究。B-18独立控制效果证据仍缺，新来源未就绪，无下一执行包；E/F和支付权限不升级。归档r101。 |
| 2026-11-07-r101 | H62既有PASS/IMPROVED/STOP；归档r100，B-17本地切片关闭，B-18有界外部资料资格测量。非新产品成绩。 |
| 2026-11-06-r100及更早 | 完整原文见归档，不改历史合同/结论。 |
