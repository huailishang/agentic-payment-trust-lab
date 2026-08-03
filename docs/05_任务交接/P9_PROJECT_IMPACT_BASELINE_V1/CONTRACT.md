# Frozen Task Contract

Task ID: P9-PROJECT-IMPACT-BASELINE-V1  
Task name: 固定端到端项目影响基线 v1  
Task kind: evaluator_design  
Risk: L0  
Contract state: CONTRACT_FROZEN  
Branch: main  
Baseline HEAD: 8acaa9e4319240d258f14d8a23b1f15cc71d09b6  
Pre-existing changes: 工作区包含 P4-P9 历史与当前任务的继承未提交改动；执行者必须在 EV-01 保存完整初始 git status，不得清理、覆盖或顺带修改合同允许范围之外的文件。

## Strategic basis

Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md  
Map revision: 2026-08-03-r2  
Active bottleneck: B-01  
Hypothesis: H-01  
Measurement status: unknown  
Metric baseline: Governed End-to-End Task Success Rate 尚未测量；当前组件守护基线为全量 413/413、正式入口 13/13、Fact Lineage 16/16 矩阵。  
Estimated affected scope: 所有后续 capability_experiment 的项目影响裁决，估计覆盖 100%。  
Expected project impact: 本任务只把项目级指标从 unknown 变为可重复测量，不声明支付能力改善；最终项目影响裁决必须为 NOT_APPLICABLE。  
Rollback condition: 任何产品决策变化、P1-P6/Runtime Gate/Fact Lineage 修改、根据实际输出反改目标答案、结果不确定或既有回归退化，均停止并回滚本任务改动。

## Single objective

建立一个完全离线、可重复、机器可读的项目级端到端评测基线：固定至少 12 个任务、统一运行命令、统一主指标与守护指标，并证明相同代码和 fixture 连续三次产生相同规范化结果。

本任务测量当前系统，不修复测出的能力缺口。当前任务出现失败项可以被如实记录，不能为了让基线全绿而修改产品代码或目标答案。

## Acceptance criteria

### AC-01 — 固定任务集与不可反向改写的目标

- Type: evaluator-owned measurement fixture
- Given: `docs/04_验证体系/项目级能力评测基线_v1.md` 已冻结 T01-T12 的业务语义。
- When: 创建项目级 fixture。
- Must observe:
  - 至少包含 T01-T12，ID 唯一且顺序稳定；
  - 覆盖 ALLOW、DENY、CONFIRMATION_REQUIRED、INDETERMINATE 四态；
  - 覆盖正常支付、订单变化、身份错绑、缺证据、不可信来源、UNKNOWN 查询、重复防护、履约失败和状态冲突；
  - 每项显式定义初始状态、步骤、目标 decision、callback/retry 次数、最终状态、必要 reason code 子集和必要证据阶段；
  - fixture 带 schema/version/limitations，且 SHA-256 写入报告。
- Must not observe:
  - 从本轮 actual 输出自动生成 expected；
  - 删除失败任务、修改任务目标或只保留通过样本。
- Evidence required: EV fixture audit + SHA-256。
- Mandatory: yes

### AC-02 — 单一离线运行器

- Type: deterministic evaluation runner
- Given: 固定 fixture 和现有公开 API。
- When: 执行一个命令运行全部任务。
- Must observe:
  - 输出机器可读 JSON；
  - 每项包含 expected、actual、matched dimensions、能力缺口和 limitations；
  - 输出 project summary、task results、metric definitions、fixture hash 和 runner hash；
  - 退出码只反映运行器/fixture 是否有效，不因当前项目能力尚有缺口而伪装执行失败。
- Must not observe:
  - 网络、LLM、WebShop runtime、真实 Buy Now、支付、钱包、环境变量写入或随机外部状态；
  - 在 runner 中复制第二套 P1-P6、Context Policy、Binding、Lineage 或 Sidecar 业务算法。
- Evidence required: EV runner command、stdout/stderr、输出 JSON。
- Mandatory: yes

### AC-03 — 项目主指标与守护指标

- Type: measurement semantics
- Given: T01-T12 实际结果。
- When: 计算项目指标。
- Must observe:
  - Governed End-to-End Task Success Rate；
  - unsafe allow、false refusal、missed confirmation、overconfident decision；
  - duplicate/forbidden side effect、callback/retry count；
  - binding completeness、source-lineage completeness、evidence-stage completeness、decision-reason consistency；
  - 正式入口和全量回归作为外部守护线单独记录。
- Must not observe:
  - 用单元测试通过率替代项目主指标；
  - 把“与当前输出一致”当作“达到目标结果”。
- Evidence required: EV metric audit with hand-calculated spot checks for at least four tasks。
- Mandatory: yes

### AC-04 — 三次确定性复现

- Type: reproducibility
- Given: 同一 HEAD、fixture、runner 和本地环境。
- When: 连续运行三次。
- Must observe:
  - 规范化 task results 和 metrics 的 SHA-256 三次完全一致；
  - 任务顺序、reason codes、数值和缺口列表稳定；
  - 非确定性运行元数据不得进入规范化比较对象。
- Must not observe: 随机种子、当前时间、临时路径或字典遍历顺序导致结果漂移。
- Evidence required: EV repeat-3 output and three identical digests。
- Mandatory: yes

### AC-05 — 只编排现有能力，不修改产品

- Type: scope boundary
- Given: 当前 P1-P6、Governed Action、Fact Lineage、Attack Overlay、Runtime Gate、Payment/Sidecar/Recovery 能力。
- When: 构造 T01-T12。
- Must observe: runner 通过现有公开函数和固定对象组合获取实际结果；产品模块哈希保持不变。
- Must not observe:
  - 修改 `src/`；
  - 新增业务 allow/deny 规则；
  - 通过 monkeypatch 改变产品行为；
  - 为了满足 fixture 修改现有测试期望。
- Evidence required: protected hash audit and live diff audit。
- Mandatory: yes

### AC-06 — 真实记录当前缺口

- Type: baseline honesty
- Given: 当前项目可能没有统一权威轨迹或某些证据阶段。
- When: 某任务未达到目标。
- Must observe:
  - 任务被标记为 project capability gap；
  - 明确缺失维度和实际证据；
  - 主指标按真实结果计算。
- Must not observe:
  - 因任务可稳定复现就把能力缺口判为成功；
  - 将 unknown 强制转为更乐观状态；
  - 在 evaluator_design 任务中修复该缺口。
- Evidence required: 至少一个失败或不足维度的展示；若 12 项全部达到目标，必须给出逐项完整证据并说明为什么不是测试过弱。
- Mandatory: yes

### AC-07 — 回归守护

- Type: regression
- Given: 本任务只新增评测基础设施。
- When: 运行强制回归。
- Must observe:
  - Fact Lineage、Runtime Gate、Attack Overlay、Payment Sidecar、Recovery 和 Status Conflict 专项全部通过；
  - 全量测试不少于 413 且全部通过；
  - 正式入口 13/13 PASS。
- Must not observe: 既有测试删除、跳过或阈值降低。
- Evidence required: 完整 EV triplets。
- Mandatory: yes

### AC-08 — 报告、快照和影响边界

- Type: governance evidence
- Given: 工作区无实现 commit 且存在继承改动。
- When: 完成报告。
- Must observe:
  - 初始/最终 git status、保存 diff 和 SHA-256；
  - 改动文件清单与 SHA-256；
  - AC-01 至 AC-08 对应 EV triplets；
  - 项目指标 before=unknown、after=measured 的事实描述；
  - Impact comparison 明确 `NOT_APPLICABLE`，不得写 IMPROVED；
  - deviations、未运行项、已知盲区和外部依赖。
- Must not observe: commit、push、history rewrite、网络或支付副作用。
- Evidence required: REPORT.md + workflow validator。
- Mandatory: yes

## Allowed scope

May add or modify only:

- `samples/evaluation/project_impact_baseline_v1.json`
- `scripts/validation/run_project_impact_baseline.py`
- `scripts/validation/project_impact_baseline_*.py`（如确需拆分纯评测辅助代码）
- `tests/test_project_impact_baseline.py`
- `docs/04_验证体系/项目级能力评测基线_v1.md`（仅补充已实现命令、schema 和实测基线）
- `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/REPORT.md`
- `docs/05_任务交接/P9_PROJECT_IMPACT_BASELINE_V1/evidence/EV-*`
- `CURRENT.md`（仅原子交接）

No `src/` file is allowed to change.

## Exclusions and forbidden side effects

- 不修改 P1-P6、Fact Lineage、Governed Action、Context Policy、Runtime Gate、支付生命周期、Sidecar、Recovery 或 UI；
- 不新增真实 Agent、LLM、浏览器自动化、Prompt Injection 组合测试、P9-E UI、UCP/ACP 或银行沙箱；
- 不执行 WebShop runtime、Buy Now、支付、查询、履约、退款、钱包、测试网或网络；
- 不安装依赖、不创建环境、不启动后台进程；
- 不修改现有任务期望以适应 actual；
- 不 commit、不 push、不 rewrite history；
- 不清理继承工作区改动。

## Validation plan

| VP | Exact command or steps | Expected result | AC |
|---|---|---|---|
| VP-01 | `PYTHONPATH=src python3 scripts/validation/run_project_impact_baseline.py --spec samples/evaluation/project_impact_baseline_v1.json --repeat 3 --output <evidence>/project_impact_baseline.json` | 至少 12 项；三次规范化 digest 相同；输出完整 metrics/gaps | AC-01, AC-02, AC-03, AC-04, AC-06 |
| VP-02 | `python3 -m unittest tests.test_project_impact_baseline -v` | 所有 runner、fixture、指标和抗反向改写测试通过 | AC-01 至 AC-06 |
| VP-03 | `python3 -m unittest tests.trusted_execution.test_fact_lineage tests.test_attack_overlay tests.test_webshop_runtime_gate tests.test_webshop_payment_sidecar tests.test_payment_recovery tests.test_payment_status_conflict -v` | 全部通过 | AC-05, AC-07 |
| VP-04 | `PYTHONPATH=src python3 -m unittest discover -s tests -v` | 测试数不少于 413，全部通过 | AC-07 |
| VP-05 | `python3 run_experiment.py` | 13/13 PASS | AC-07 |
| VP-06 | 保护文件与范围审计 | `src/` 哈希不变，只有允许文件变化 | AC-05, AC-08 |
| VP-07 | `python3 <workflow-skill>/scripts/validate_workflow.py --repo . --current CURRENT.md` | 无 BLOCKING；交接前修复全部 FIX_IN_PLACE | AC-08 |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- data_download: false
- dependency_install: false
- create_environment: false
- webshop_runtime_execution: false
- buy_now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- 任一所需任务无法通过现有公开 API 编排，必须修改 `src/`；
- fixture 的目标结果存在两个实质不同解释；
- 需要外部网络、真实 WebShop、LLM、支付或新依赖；
- 无法区分“运行器正确”与“项目能力达到目标”；
- 三次结果不稳定且原因无法在评测基础设施范围内修复；
- 既有回归在本任务改动前已失败；
- 命名地图 revision、B-01 或 H-01 无法核验；
- 需要用户提供新的业务目标、风险容忍度或外部授权。

## Amendments

None.
