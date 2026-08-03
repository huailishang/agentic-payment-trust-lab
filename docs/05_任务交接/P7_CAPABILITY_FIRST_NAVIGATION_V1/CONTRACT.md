# P7 capability-first navigation v1

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P7-CAPABILITY-FIRST-NAVIGATION-V1
task_name: P7 业务能力优先导航第一切片
contract_state: CONTRACT_FROZEN
freezing_role: Evaluator
baseline_head: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6
roadmap_ref: docs/02_未来规划/整体修正执行计划_20260729.md#21
```

Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## Five-question readiness check

1. First-principles problem: 当前首页把 M2/M3/M4/M5、Attack 和 S 编号当成主角，初学者看到的是研发历史，不是系统解决的支付信任问题。
2. Mature-payment or Agent-new: 页面要同时展示成熟支付能力与 Agent 新增控制能力，但不能继续按内部阶段编号混排。
3. Existing mechanism: 复用现有 scenario presentation、lab overview、PayBench/AP2/Attack 结果和统一评测数据；只重组展示结构，不重写业务判断。
4. Stable capability: 建立稳定的“业务能力 → 测试输入”导航，案例和外部项目继续作为验证题，而不是产品一级功能。
5. Proof: 数据结构测试、HTML 输出检查、交互回归、全量测试、官方入口和范围检查。

## Single objective

把本地实验报告的第一层导航从研发编号和测试来源，改为固定的业务能力导航；M2/M3/M4/M5、S01–S13、PayBench、AP2 和 Attack 仍完整保留，但只作为能力下的验证来源、案例或评测元数据，不修改任何支付、授权、可信执行、状态恢复或统一评测逻辑。

## Acceptance criteria

### AC-01 — fixed capability-first navigation

`build_lab_overview()` 输出新的 `capability_navigation`，一级能力按以下固定顺序出现：

1. `USER_AUTHORIZATION` — 用户授权与确认
2. `AGENT_EXECUTOR_IDENTITY` — Agent 与执行者身份
3. `TRANSACTION_PAYMENT_BINDING` — 交易对象与支付绑定
4. `TRUSTED_CONTEXT_RUNTIME_GATE` — 可信上下文与执行前拦截
5. `PAYMENT_STATE_FINALITY` — 支付状态恢复与最终性
6. `EVIDENCE_REPLAY` — 证据与回放

每个一级能力至少包含稳定 `id`、中文名称、面向初学者的业务问题说明、当前覆盖状态和二级验证项。一级名称不得以 `M`/`S` 编号、PayBench、AP2 或 Attack 作为主标题。

### AC-02 — cases become validation inputs

现有内部场景、PayBench 挑战对、AP2 HP/HNP 样品和 Attack Overlay 案例必须保留，并以 `source_type`、`source_label_zh` 或等价稳定字段标明其验证来源后挂到相应能力下。至少满足：

- 用户授权与确认包含预算、商户、品类、有效期、次数、人工确认和订单变化类内部场景；
- Agent 与执行者身份包含身份不匹配/身份约束相关验证；
- 支付状态恢复与最终性包含 UNKNOWN 查询恢复、终态与冲突相关验证；
- 可信上下文能力包含 Attack Overlay 及对应外部提示注入验证；
- 证据与回放展示统一评测/回放覆盖状态，但不把 M5 当成产品能力。

允许同一个外部验证来源服务多个能力，但不得复制或伪造执行结果。现有 `modules` 聚合数据可作为兼容/开发者数据保留。

### AC-03 — M5 returns to evaluator role

一级导航中不再出现 `M5 统一评测`。统一评测数据继续存在于各能力或二级验证项的评测摘要中，用中文说明其作用是“裁判/评测口径”，不是面向用户的支付功能。错误放行、错误拒绝、漏确认、过度武断和禁止副作用等指标不得丢失或改义。

### AC-04 — HTML homepage uses business language first

生成的 HTML 首页首先展示六个业务能力及其业务问题；进入能力后再看到内部案例、PayBench、AP2、Attack 等来源。页面不得再用“M2 内部回归 / M3 PayBench / M4 AP2 / M5 统一评测 / Attack Overlay”作为第一层主导航。

原始 JSON、reason codes、协议字段和技术证据默认保持折叠或开发者详情，不在首页首屏堆叠。现有场景选择、详情展示和本地交互入口不能因导航重组失效。

### AC-05 — behavior and regression boundaries

只改变 overview/presentation/navigation 结构与对应测试：

- 不改变场景输入、业务决策、统一评测算法、支付状态、授权、身份、绑定、可信上下文或回放逻辑；
- `run_experiment.py` 仍为 S01–S13 `13/13`、内部回归 `PASS`、AP2 `2/2`、Attack Overlay `6/6`；
- 聚焦测试、交互/展示回归、全量发现、官方入口和任务范围检查通过。

## Allowed scope

- `src/agentic_payment_experiment/lab_overview.py`
- `src/agentic_payment_experiment/html_report.py`
- `tests/test_lab_overview.py`
- `tests/test_entrypoint.py`
- `tests/test_interactive_lab.py`（仅在导航重组影响现有本地交互契约时）
- `docs/05_任务交接/P7_CAPABILITY_FIRST_NAVIGATION_V1/REPORT.md`
- `docs/05_任务交接/P7_CAPABILITY_FIRST_NAVIGATION_V1/evidence/EV-*`

## Exclusions

- 不修改模型、场景 JSON、validator/evaluator、runner/result-card 业务结构、payment/authorization/identity/binding/context/replay/finality 实现。
- 不新增 S 场景、Benchmark、协议适配器、外部依赖、前端框架、数据库、网络服务、真实 API、真实支付或回调。
- 不删除 `modules`、现有测试来源数据或开发者详情；不做整站视觉重写，只完成一级信息架构切换和必要渲染调整。
- 不提交、不推送、不改写历史。

## Validation plan

| VP | Command | Expected | AC |
|---|---|---|---|
| VP-01 | `python -m unittest tests.test_lab_overview tests.test_entrypoint -v` | 六个能力顺序、业务语言一级导航、测试来源挂载、M5 非一级功能及 HTML 输出契约通过 | AC-01, AC-02, AC-03, AC-04 |
| VP-02 | `python -m unittest tests.test_interactive_lab tests.test_presentation -v` | 现有场景交互和展示详情未因导航重组失效 | AC-04, AC-05 |
| VP-03 | `python -m unittest discover -s tests -v` | full suite passes | AC-05 |
| VP-04 | `python run_experiment.py` | S01–S13 13/13；内部回归 PASS；AP2 2/2；Attack Overlay 6/6；HTML 正常生成 | AC-04, AC-05 |
| VP-05 | `git diff --check` and scope review | task-attributable changes clean and confined to allowed files | AC-05 |

## Inherited worktree state

P4、P5、P6 及其评估/修复记录仍因授权为 false 而保持未提交。Executor 必须保留这些改动，不得 staging、revert、删除或归因到 P7。本任务只能通过允许文件和新任务包区分自己的改动。

## Authorization and stop conditions

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
```

Stop if implementation requires changing business decisions, scenario data, the unified evaluation algorithm, or the payment flow; adding a frontend framework/external dependency; or deleting existing module data to complete capability-first navigation.

## Atomic handoff requirement

Do not request Evaluator review until all mandatory VPs have readable `EV-*` stdout/stderr plus core metadata, `REPORT.md` maps AC-01 through AC-05, declares `executor_state: READY_FOR_REVIEW`, and the workflow validator has no `BLOCKING` finding. Advisory-only report formatting differences do not delay technical review or create another round.
