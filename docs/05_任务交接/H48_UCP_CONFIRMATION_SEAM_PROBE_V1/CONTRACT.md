# H48 冻结执行包：外部结算快照接入已有用户确认机制

Task ID: H48_UCP_CONFIRMATION_SEAM_PROBE_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: one_off
Risk: L1
Contract state: CONTRACT_FROZEN
Dispatch mode: SINGLE
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Validation plan file: docs/05_任务交接/H48_UCP_CONFIRMATION_SEAM_PROBE_V1/VALIDATION_PLAN.yaml

## Strategic basis / 全局位置

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-10-15-r76
Active bottleneck: B-17
Hypothesis: H-48
Measurement status: H47 九路径/17 项映射已验收；现有确认机制对订单内容变更的单元能力已完成，真实商家快照输入的任务内投影尚未交付。不能把此包说成重新发明确认控制。
Metric baseline: H47 C02 两轮合法更新数量 1→2 后完成，库存 5→3；原生没有本项目确认记录。原生签名、幂等与查询能力不作为本包增量。
Estimated affected scope: 一个固定完整商家；9 条冻结场景各重复两次、12 种投影输入破坏；没有用户规模或市场收益估算。
Expected project impact: 得到一个能复跑的受限输入桥接样例，区分已有确认控制可复用与客户端控制边界；one_off，不预承诺产品能力提高。
Rollback condition: 不能忠实投影即记录缺证据并停止该候选；不能通过新增默认身份、弱化哈希或修改原生商家求通过。

最终目标为授权→绑定→受控执行→恢复→审计。A–D 完成、E 本地代表性闭合、F 当前。H47 已完成通用适用性测量。B-17 现缩小为可信输入与付款前快照如何进入原有机制、检查控制到哪里。优先于继续扩商城名单或重开 A–E；支付宝和比赛仍后置。没有多个消费者证明核心应改，本包只在任务目录做原型。相比直接生产适配，先给出诚实的可运行增量及绕过反例；相比重复 H47 缺字段检查，正常路径必须实际通过既有确认并完成模拟商家动作。

## Single objective / 唯一目标

将真实 UCP checkout（付款前结算会话）与显式合成信任清单忠实投影为已有 Order，复用现有确认记录/检查/回调闸门；完整展示正常、变更、缺证据及客户端控制不足的边界。

唯一主变更：任务内 PROJECTOR.py 的纯输入投影。既有确认机制、原生商家和冻结测试编排均只读。不是完整支付闸门、生产适配器、身份验证器或服务端修复。

## 对象与信任边界

- 内部 Order 是付款前用户可确认的交易，不是“商家已生成最终订单”的证明。内部 ID 固定为 `h48-checkout:` + 原始 checkout.id，另保留 checkout_ref。完成后从原始返回单独读取 order.id；不能提前造最终商家订单 ID。
- TRUST_FIXTURE 全部为 Evaluator 显式合成测试配置：merchant、payee、authority、分类、有效期、履约条件与服务引用。它们不是从 profile URL、临时签名或商家响应推导的生产可信事实。缺任一必要配置必须缺证据，不能回填默认值。
- checkout 只提供 id、line_items[].item.id/title/price、quantity、currency、唯一 total。金额只支持本固定 USD，整数最小单位精确除以 Decimal(100)，拒绝 bool/字符串/浮点/负数；不支持的货币必须拒绝，不默认为 CNY。
- order_version 是该投影确认内容的本地摘要，仅表示观测内容，不是 UCP 协议版本、服务端 CAS（比较版本后原子更新）或防竞态证明。确认仍以现有内容哈希判定；既有测试明确仅版本标签改变不使相同内容失效，本包不修改它。
- 保留所有商品项目，种类 product；分类必须来自清单中该 item 的显式条目。总额读取唯一 total，禁止 subtotal+total 相加。履约字段来自清单只是实验约定，不能声称完整 UCP 履约语义已归一。
- 不生成 PaymentExecutionRecord、Provider proof、真实身份/持有证明或 ProductAuthoritativeTrace。正常完成只是原生模拟处理，不升级为完整支付安全。

## 冻结接口

新增 PROJECTOR.py：`project_checkout(checkout: dict, trust: dict) -> dict`。

成功返回 `{"order": Order, "checkout_ref": 原始id, "final_order_ref": None, "missing": []}`。Order 字段逐项精确来源见上文与 EVALUATOR_CHECK.expected_order。service_id 必填，candidate_rails=()，authority_version_ref 来自清单；quote_expires_at 为带时区 datetime。

无法表达时返回 `order=None`、非空 missing 列表、保留可得 checkout_ref、final_order_ref=None。不伪造字段使投影成功。非法输入不是未捕获异常。不得修改输入、文件、全局类/函数或上下文；函数无网络/数据库/回调能力。只导入标准库和现有项目类型/哈希辅助；不安装包。

主编排由 Evaluator 冻结：真实 Merchant 创建→保留原始快照→投影→create_confirmation_record→按场景变更/查当前快照→verify_confirmation_binding→execute_with_confirmation_gate→可选调用真实 mock complete。记录完整调用、持久状态、确认事实与实际模拟处理次数。Executor 不拥有预期答案或运行编排。

## 串行阶段

| 阶段 | 工作 | 一次性交付 |
|---|---|---|
| S0 | baseline、来源、隔离环境与 H47 历史保护检查 | 初始状态/保护结果 |
| S1 | 读对象/信任合同与现有确认代码，写来源表 | INPUT_LINEAGE.md，明确哪些是商家事实、哪些是合成配置 |
| S2 | 实现纯投影、处理非法/缺失输入 | PROJECTOR.py；不改核心或商家 |
| S3 | 运行冻结的原生/确认前置对照 | 正常能完成；已变数量/金额需重确认；缺输入不调用 complete |
| S4 | 完成核验后穿插更新、绕过客户端直接 complete 反例 | 如实暴露客户端限制，不能为了“安全”删去反例 |
| S5 | 写可读演示与结论，比较原生/任务内投影/未来服务端控制 | ANALYSIS.md、DEMO.md、RESULT.json；明确客户/Provider 未验证 |
| S6 | 完整 L2、成本/原始证据及中央校验 | REPORT、账本；整包后一次 L3 |

阶段间不等评估者签字。普通缺证据结果属于有效观察；保护、权限、冻结语义或环境需变化才硬停止。冻结接口无法实现则保留最小失败输入，不自行改合同。

## 冻结场景与可证伪边界

每条两轮独立 Merchant：N01 原生确认后合法改为 2 并完成；G01 投影确认后不变正常完成；G02 完成前已变为 2，现有确认失效、零 complete；G03/G04 缺可信 payee/authority，缺证据、零 complete；G05 确认过期阻断；G06 当前投影缺 currency 阻断（只对复制响应做显式输入破坏，不冒充商家原生输出）；L01 已通过确认检查后、执行回调前合法改为 2，展示客户端时间窗口；L02 绕过确认客户端直接原生 complete，同样展示控制范围。

N01 是原生基线；G01/G02 对照说明桥接既有确认的局部效果；L01 是确定性穿插次序，不是并发压力测试。其实际状态如与预期不同，保存原始观察、分析原因，不改原生代码。只有真实原生版本/环境与冻结前提不一致才 BLOCKED。按冻结代码本版本预期 L01/L02 均可完成改变后的数量；这不是新发现的官方漏洞，也不能声称所有服务端接法都不可行。

另外 12 种离线输入破坏要求投影拒绝：payee/authority 缺失、currency 缺失/不支持、总额字符串/bool/负数、重复 total、缺 quantity/非正 quantity、缺商品分类、缺商品 title。还检查入参未改、精确金额、商品及内部引用保留，协议版本绝不冒充订单版本。

## Acceptance criteria

### AC-01 — 冻结资产、权限与环境保持

Given 固定 HEAD、H47 历史和既有隔离环境；When VP-01/05；Must observe 保护/来源/环境一致、只改本包白名单、四项授权 false；Must not observe 安装、联网、源代码改动、改 H47 历史；Evidence=VP-01/05。Mandatory: yes。

### AC-02 — 忠实的付款前投影

Given 真实快照与显式清单；When 运行投影及 12 种输入破坏；Must observe 逐字段精确、Decimal USD、引用分开、成功正常输入与非法输入拒绝、输入不变；Must not observe 默认身份、生成支付证明、忽略商品或改输入；Evidence=VP-02/03、INPUT_LINEAGE。Mandatory: yes。

### AC-03 — 复用现有确认且实际控制回调

Given 真实 Merchant 与冻结场景；When 比较 N01/G01/G02/G03–G06；Must observe 正常实际完成一次，已变更要求重确认，缺证据/过期零 complete/零模拟处理，并留存真实状态；Must not observe 全阻断或自填返回冒充改善；Evidence=VP-02。Mandatory: yes。

### AC-04 — 客户端不足必须暴露

Given L01/L02；When 运行确定性穿插/直接调用；Must observe 原始状态与确认检查前后位置，区分控制内与外，说明非原子绑定；Must not observe 以先读后写称竞态已解决、掩盖旁路或宣称 UCP 漏洞；Evidence=VP-02/04、ANALYSIS。Mandatory: yes。

### AC-05 — 边界、成本与统一结论

Given 所有结果；When 完整 L2 后提交；Must observe 一份 CLIENT_GUARD_ONLY 的有限结论或有据差异、正常/异常/限制演示、成本账、公开团队后续问题仅引用 H47、需求仍 UNKNOWN；Must not observe 生产适配、完整支付闸门、客户/Provider/第三方认证声明；Evidence=VP-04/05、REPORT。Mandatory: yes。

## Allowed scope / Exclusions

可写 PROJECTOR.py、INPUT_LINEAGE.md、ANALYSIS.md、DEMO.md、RESULT.json、ATTEMPT_LEDGER.json、REPORT.md 与本包 evidence/。
CURRENT 只准 CONTRACT_FROZEN→EXECUTING/Executor，更新 phase/next_artifact_path；交付仍保留 Executor，Evaluator 接受后转 READY_FOR_REVIEW。不能更改任务/地图/授权或历史叙述。
合同、清单、EVALUATOR_CHECK、FREEZE、BASELINE、计划、EXECUTOR_START、REVIEW 冻结。src/tests/scripts、H47 全目录、其他任务/规划/商业材料、公共工作流只读。禁止修改服务端、事务、Middleware、源码/环境、生产适配、UI、模型、对外消息或新仓库下载。

## Validation plan / 预算

VP-01 baseline；VP-02 新商家原始场景观测；VP-03 投影畸形/缺字段检查；VP-04 材料/声明/预算；VP-05 现有 confirmation 和 WebShop gate 相关回归、diff、保护复验。具体 argv 和 L2/L3 输出分离在 VALIDATION_PLAN.yaml。

主动执行上限 8 小时，预计半天至一天为估计。正式 L2 最多 3 次；同一失败连续两次无新依据即停止。包内 ASGI 请求上限 600，单次完整正式矩阵上限 80 次，Evaluator 独立 L3 一次上限 80；廉价纯函数检查不耗网络预算。并发度 1，串行；不重复已足够结果。ATTEMPT_LEDGER 记录 formal_l2_attempts、asgi_requests、active_work_minutes、external_runtime_calls/model_calls/provider_calls 均 0 及每次目录/原因；工时自报与客观 meta 分开。

- commit: false
- push: false
- history_rewrite: false
- api_call: false

不需要新的 Human 输入；合成配置只用于演示假定“可信外部输入已给定”时的局部边界，不代替未来真实认证。已有 `.task_envs/H47/.venv` 缺失即停止，不重装。付款始终 mock_payment_handler，无真实卡/钱、支付宝、钱包/测试网、比赛、上传或对外联系。

## Stop conditions / 后续条件

保护漂移、环境/来源缺失、需改冻结接口/核心/商家/权限或预算耗尽即 BLOCKED；保留最小事实，不改检查器。
投影与正常/变化对照成立、穿插/旁路仍可完成 → 仅证明 CLIENT_GUARD_ONLY（只控制此客户端路径），下一轮评估服务端原子绑定的最小可行性，不能直接发布安全适配器。
投影不忠实或已有原生足够、无新增信息 → STOP/SWITCH。出现两个独立消费者共同需要相同机制才考虑核心回抽。任何结果不自动恢复支付宝、比赛、H44/H45 或客户联系。

## External requirement impact

已读 PCAC 开发指标映射。external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/12/20；CORE/ADAPTER/EVIDENCE_ONLY；maturity_before=已有本地确认控制、外部输入桥接未交付；maturity_after_target=固定完整商家/合成信任输入的可复跑局部证据，不改变生产能力成熟度；Test=VP-01..05；Evidence=原生状态/投影/确认事实/L2/L3；残余=合成身份和收款人、客户端可绕过、无原子/并发保证、无真实 Provider/客户。不是监管合规结论。
