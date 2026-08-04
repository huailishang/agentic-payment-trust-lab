# Frozen Task Contract

Task ID: `P9-PRODUCT-AUTHORITATIVE-TRACE-MINIMUM-CONTRACT-V1`  
Task name: 产品权威轨迹最小合同与覆盖映射 v1  
Task kind: `evaluator_design`  
Risk: `L0`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `71a3acbbd9622b68a8064381b9034e07c1f4d700`

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-04-r5`  
Active bottleneck: `B-03`  
Hypothesis: `H-03`  
Current measured baseline: product-observed authoritative trace `0/12`; GESR `0/12`; duplicate or forbidden side effect `0/12`; callback match `12/12`.

B-07 已完成并独立确认 `PASS / IMPROVED`。当前第一瓶颈已切换为 B-03：产品内部虽然存在 Authority、Order、Request、Decision、Payment、Policy、Lineage 等局部事实，但固定 12 项任务的产品公开输出无法提供统一、可验证、可归因的权威轨迹。评测器自行拼装 ReplayEvent 只能作为诊断，不得计为产品轨迹。

本任务只冻结设计合同、覆盖映射和首个 capability slice，不修改产品代码，也不宣称项目指标改善。

## Single objective

基于现有产品 outcome、RuntimeGateRecord、PaymentExecutionRecord、Policy / Fact Lineage 等真实公开对象，冻结一份最小统一产品轨迹合同，并完成 12 项固定任务的“已有真实事件—缺失事件—来源对象”覆盖映射；选择一个最小代表性纵向切片，冻结后续 capability experiment 的 before/after target。

## Acceptance criteria

### AC-01 — 明确产品轨迹与评测器 Replay 边界

必须给出不可混淆的定义：

```text
product-observed authoritative trace
= 产品实际运行过程中产生
+ 由产品公开 outcome / record 直接携带
+ 事件引用可追溯到真实 Authority / Order / Request / Decision / Payment / Policy / Lineage 对象

evaluator-synthesized replay
= runner 或测试根据 fixture / outcome 事后拼装
+ 只能用于诊断和校验 Replay API
+ 不得满足 product trace 指标
```

必须列出至少 3 个禁止伪装情形，例如 runner 补事件、自由文本 reason 转事件、缺产品来源却标记 `VALID`。

### AC-02 — 冻结最小 trace schema

设计文档必须冻结最小字段：

- trace id / schema version；
- source=`PRODUCT_OBSERVED`；
- ordered immutable events；
- event type；
- occurred_at 或稳定顺序号；
- authority/order/request/action/payment/policy/lineage/result refs；
- producer component；
- decision / status / reason codes；
- completeness status：`VALID / INDETERMINATE / INVALID / NOT_AVAILABLE`；
- limitations。

所有序列化字段必须是 primitive-only；不得依赖自由文本完成引用和一致性校验。

### AC-03 — 冻结事件类型和顺序规则

至少定义：

```text
AUTHORITY_RECORDED
ORDER_RECORDED
REQUEST_RECORDED
ACTION_RECORDED
POLICY_DECISION_RECORDED 或 RUNTIME_DECISION_RECORDED
PAYMENT_ATTEMPT_RECORDED / PAYMENT_OUTCOME_RECORDED（适用任务）
FULFILMENT / RECOVERY / REFUND / CONFLICT 事件（适用任务）
RESULT_RECORDED
```

必须明确：

- 哪些事件是所有任务必需；
- 哪些事件按任务条件必需；
- 顺序和引用不一致时如何失败关闭；
- 不允许 evaluator 在缺失时补齐后计为 `VALID`。

### AC-04 — 12 项产品输出覆盖映射

必须逐项列出 T01—T12：

- 当前产品入口 / outcome 类型；
- 产品现在真实暴露的 record / fact；
- 可直接形成的事件；
- 缺失事件；
- 当前 product trace 状态；
- 最小补齐位置；
- 是否涉及副作用路径；
- 是否需要新增业务规则。

预期当前汇总仍为 `0/12 VALID`，不得为了让映射变绿而将 evaluator replay 计入产品输出。

### AC-05 — 复用现有事实，不复制规则

必须证明方案复用现有：

- Authority / Order / TransactionRequest；
- Governed Action；
- RuntimeGateRecord / gate outcome；
- PaymentExecutionRecord；
- Policy / Source / Fact Lineage；
- Lifecycle / Recovery / Conflict records。

不得新增第二套金额、币种、payee、authority、agent、order、request 或 payment binding 规则。轨迹层只引用与封装现有事实，不重新判断业务正确性。

### AC-06 — 选择首个最小 capability slice

只能选择一个代表性 slice，必须说明选择理由、影响范围和排除项。优先选择已有公开 outcome 和真实 observed record 最完整、无需改动业务决策的路径。

必须冻结：

- slice 名称和入口；
- 原始 BEFORE；
- target fixture；
- 必需事件；
- 预期 AFTER；
- 主要变量；
- 守护指标；
- rollback conditions。

首个 slice 的合理目标为：

```text
product trace：NOT_AVAILABLE → VALID
决策 / callback / 状态 / binding projection：完全不变
```

不得在本任务直接实现该 slice。

### AC-07 — 项目影响和阶段边界

本任务项目影响裁决固定为 `NOT_APPLICABLE`。

必须明确后续阶段：

```text
本任务：设计与冻结合同
→ 下一任务：一个最小 slice capability experiment
→ 独立确认改善后，再扩展到其他任务
```

不得直接制定“一次覆盖全部 12 项”的实现包。

### AC-08 — 完整证据与可执行交接

REPORT 必须包含：

- 初始和最终 git status；
- 阅读和审计的现有代码 / 文档入口；
- trace schema；
- event taxonomy；
- T01—T12 覆盖矩阵；
- 首个 slice 冻结 target；
- 逐 AC 证据；
- changed files 和完整 diff；
- 未运行项、限制与授权；
- workflow validator `OK`。

## Required outputs

必须形成：

1. `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
2. `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
3. `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
4. 当前任务 `REPORT.md` 和 `evidence/EV-*`

## Allowed scope

May add or modify only:

- `docs/03_架构设计/产品权威轨迹最小合同_v1.md`
- `docs/04_验证体系/产品权威轨迹12项覆盖映射_v1.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/NEXT_SLICE.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/REPORT.md`
- `docs/05_任务交接/P9_PRODUCT_AUTHORITATIVE_TRACE_MINIMUM_CONTRACT_V1/evidence/EV-*`
- `CURRENT.md`（仅原子路由）

允许只读审计 `src/`、`tests/`、`scripts/`、`samples/` 和既有任务文档。

## Exclusions

- 不修改任何 `src/`、`tests/`、`scripts/`、`samples/`；
- 不修改现有 runner、fixture、指标定义或既有 evidence；
- 不实现 trace envelope 或任何产品功能；
- 不把 evaluator replay 重新命名为产品轨迹；
- 不新增业务绑定、支付状态机或副作用逻辑；
- 不执行真实 WebShop、Buy Now、网络、LLM、支付、钱包、退款或外部 API；
- 不安装依赖、不创建环境；
- 不 commit、不 push、不 rewrite history；
- 不清理、reset 或回退继承工作区。

## Validation plan

| VP | Exact action | Expected |
|---|---|---|
| VP-01 | 审计现有 outcome、records、replay、project runner 和 12 项 fixture | 列出真实产品输出与 evaluator 合成边界 |
| VP-02 | 静态检查 schema 和 event taxonomy | primitive-only、引用闭合、顺序和 fail-closed 规则明确 |
| VP-03 | 逐项核对 T01—T12 覆盖矩阵 | 12/12 均有来源对象、已有事件、缺失事件和最小补齐位置 |
| VP-04 | 检查现有 binding / policy / lineage 复用关系 | 无第二套业务校验规则 |
| VP-05 | 审核 NEXT_SLICE | 单一 slice、同基线 before/after、守护线和回滚条件冻结 |
| VP-06 | scope 和 diff audit | 无产品、测试、runner、fixture 或既有 evidence 改动 |
| VP-07 | workflow validator | `OK` |

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

- 无法区分产品真实事件与 evaluator 合成 Replay；
- 设计需要复制现有业务绑定规则；
- 无法为 12 项任务建立来源对象和缺失事件映射；
- 首个 slice 需要同时修改多个产品路径，无法归因；
- 需要修改产品代码、runner、fixture 或指标才能完成本设计包；
- 需要网络、新依赖或外部副作用；
- 需要新的业务风险容忍度决定。

## Amendments

None.
