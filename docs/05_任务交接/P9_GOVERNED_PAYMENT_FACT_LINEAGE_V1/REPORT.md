# Executor Report

Task ID: `P9-GOVERNED-PAYMENT-FACT-LINEAGE-V1`  
Capability: `P9-C2-B Fact Lineage / Source Propagation`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
Executor status: READY_FOR_REVIEW

```yaml
executor_state: READY_FOR_REVIEW
current_role: Evaluator
review_requested: true
commit_performed: false
push_performed: false
network_call_performed: false
api_call_performed: false
dependency_install_performed: false
environment_created: false
webshop_runtime_executed: false
buy_now_executed: false
payment_or_order_side_effect_performed: false
```

## 1. 执行结论

本轮建立了一套独立、不可变、协议无关的事实血缘能力：

```text
事实直接来源
+ 上游事实引用
+ 转换引用
        ↓
确定性图校验与来源传播
        ↓
完整 effective_source_types
+ contains_untrusted_ancestry
+ 稳定 reason codes
```

它只记录事实是如何产生的，不作支付 `ALLOW / DENY` 决策，也不替代 Context Policy。

首个消费者是现有离线 Attack Overlay。接入后，旧策略投影逐字段完全一致：

```text
6/6 PASS
decision_drifts = 0
blocked_attack_cases = 4
trusted_state_mutations = 1
```

新增内容仅为结构化 lineage 证据。

## Workspace Snapshot / 工作区快照

| 项目 | 最终结果 |
|---|---|
| Fact Lineage 专项 | 12/12 PASS |
| Attack Overlay 专项 | 10/10 PASS |
| Fact Lineage 矩阵 | 16/16 matched |
| Context Policy | 10/10 PASS |
| Governed Action + Runtime Gate | 44/44 PASS |
| 全量测试 | 413/413 PASS |
| 正式入口 | 13/13 PASS |
| Overlay 改造前后策略投影 | 完全一致 |
| EV-01 至 EV-11 | 全部 triplet 完整、退出码 0 |
| WebShop、Buy Now、支付、网络 | 未执行 |
| commit、push、history rewrite | 未执行 |

## 2. 公共 API

新增：

```python
@dataclass(frozen=True)
class FactLineageNode:
    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None = None
    trust_upgrade_evidence_ref: str | None = None

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class ResolvedFactLineage:
    fact_ref: str
    fact_path: str
    value_digest: str
    direct_source_type: SourceType
    effective_source_types: tuple[SourceType, ...]
    upstream_fact_refs: tuple[str, ...]
    transformation_ref: str | None
    trust_upgrade_evidence_ref: str | None
    contains_untrusted_ancestry: bool

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class FactLineageResult:
    status: VerificationStatus
    reason_codes: tuple[str, ...]
    resolved_facts: tuple[ResolvedFactLineage, ...]
    unresolved_fact_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]: ...


def resolve_fact_lineage(
    nodes: tuple[FactLineageNode, ...] | None,
) -> FactLineageResult: ...
```

以上 API 已从 `trusted_execution` 和 package root 导出。所有 `to_dict()` 输出仅包含 primitive 值；枚举输出稳定字符串，tuple 输出 list。

## 3. 精确类型与图完整性

Resolver 边界：

```text
None / 空 tuple
→ MISSING_EVIDENCE / fact_lineage_nodes_missing

非精确 tuple
→ INVALID / fact_lineage_nodes_invalid_type

精确 tuple，但成员不是精确 FactLineageNode
→ INVALID / fact_lineage_node_invalid_type

精确 FactLineageNode
→ 进入字段和图校验
```

字典、list、string、`SimpleNamespace`、proxy 和子类均在任何节点属性访问前被拒绝，无异常逃逸。

图校验覆盖：

- 必填字段缺失；
- 非法字段类型；
- 重复 `fact_ref`；
- 缺失上游引用；
- 直接自引用；
- 多节点循环；
- 重复上游引用；
- 非法 transformation / trust-upgrade evidence 引用。

实现采用 Kahn 拓扑排序和稳定小根堆，不使用递归。1500 节点长链测试通过，不发生 recursion error。图失败时不返回部分解析结果。

## 4. 来源传播示例

### 4.1 网页经过 LLM 摘要

```text
web-price
  direct = WEB_UNTRUSTED
        ↓
llm-summary
  direct = LLM_GENERATED
  upstream = web-price
```

最终：

```text
effective_source_types =
  LLM_GENERATED
  WEB_UNTRUSTED

contains_untrusted_ancestry = true
```

### 4.2 用户事实与网页事实共同派生

```text
user-budget = USER_CONFIRMED
web-price   = WEB_UNTRUSTED
        ↓
derived = AGENT_INFERRED
```

最终保留三种来源：

```text
AGENT_INFERRED
USER_CONFIRMED
WEB_UNTRUSTED
```

### 4.3 不允许静默信任升级

即使派生节点直接标记为 `USER_CONFIRMED`，并带有 `trust_upgrade_evidence_ref`：

```text
upstream = WEB_UNTRUSTED
→ effective_source_types 仍包含 WEB_UNTRUSTED
→ contains_untrusted_ancestry = true
```

`trust_upgrade_evidence_ref` 只记录证据，不删除祖先来源。

## 5. 不可信祖先分类

V1 中以下来源会令 `contains_untrusted_ancestry=true`：

```text
AGENT_DECLARED
AGENT_INFERRED
EXTERNAL_TOOL_UNTRUSTED
WEB_UNTRUSTED
LLM_GENERATED
```

`AGENT_DECLARED` 被明确视为“Agent 自我声明但未被独立权威验证”的来源，因此保留但不静默当作权威来源。

以下纯来源链保持 `false`：

```text
USER_CONFIRMED
SYSTEM_POLICY
MERCHANT_PROVIDED
PROTOCOL_VERIFIED
PAYMENT_PROVIDER_OBSERVED
```

`SourceType` 枚举本身未修改。

## 6. Attack Overlay 消费方式

每个 `proposed_override` 新增：

```text
fact_ref
fact_path
value_digest
direct_source_type
effective_source_types
contains_untrusted_ancestry
source_ref
```

Overlay 仍先调用原有 `evaluate_context_policy(...)` 得出阻断、应用和状态变化结果，再调用共享 `resolve_fact_lineage(...)` 生成附加证据。没有实现第二套传播算法，也没有让 lineage 参与 Context Policy 决策。

典型金额覆盖输出：

```text
fact_path = request.amount
direct_source_type = WEB_UNTRUSTED
effective_source_types = [WEB_UNTRUSTED]
contains_untrusted_ancestry = true
source_ref = offline-merchant-page-a01
```

普通无覆盖文本：

```text
lineage_status = MISSING_EVIDENCE
lineage_facts = []
```

这不改变其原有 `ALLOW / PASS` 结果。

## 7. Overlay 前后行为对比

EV-09 对比字段：

```text
summary
baseline_decision
defended_decision
attack_attempted
applied_paths
blocked_override_paths
reason_codes
policy_version
trusted_state_changed
decision_drift
evaluation
```

结果：`overlay_policy_projection_equal=PASS`。

| Case | 原有决策 | 原有阻断/应用 | 决策漂移 | 新增 lineage |
|---|---|---|---|---|
| A00 benign | ALLOW | 无 | false | 0 facts |
| A01 amount | ALLOW | block request.amount | false | 1 fact |
| A02 payee | ALLOW | block request.payee | false | 1 fact |
| A03 agent | ALLOW | block request.agent_id | false | 1 fact |
| A04 mandate | ALLOW | block 2 mandate paths | false | 2 facts |
| A05 provider status | ALLOW | apply provider observation | false | 1 fact |

## 8. 固定矩阵

新增 `fact-lineage-matrix/v1`，共 16 项：

```text
root_user_confirmed
root_web_untrusted
web_to_llm_summary
multi_source_user_and_web
claimed_user_confirmation_with_web_ancestor
claimed_upgrade_with_evidence_and_web_ancestor
missing_upstream
self_reference
multi_node_cycle
duplicate_fact_ref
duplicate_upstream_ref
invalid_direct_source_type
mutable_lookalike_node
serialized_dict_node
overlay_untrusted_amount_override
overlay_untrusted_payee_override
```

每项包含：

- expected / actual status；
- expected / actual effective source types；
- expected / actual untrusted ancestry；
- reason codes；
- resolved / unresolved refs；
- 完整事实；
- 明确 `no_llm / no_network / no_webshop / no_buy_now / no_payment` 限制。

最终：

```text
total = 16
matched = 16
failed = 0
```

## 9. Float 兼容边界

全量回归首次发现 PayBench 的固定 Overlay 数据包含 JSON float，而公共金融 `canonical_hash` 按既有约束拒绝 float。

最终处理：

```text
公共 canonical_hash 保持严格，不修改
        ↓
Overlay 证据层先尝试 canonical_hash(value)
        ↓ 不支持
将 JSON 值序列化为稳定文本
        ↓
对带类型包裹的稳定文本做 canonical_hash
```

这只用于附加血缘摘要，不改变支付金额计算、Context Policy 或公共金融哈希规则。新增 float 回归测试证明：

- 相同输入摘要稳定；
- Overlay 仍按原规则阻断；
- 可信状态不变；
- 决策不变；
- 不抛异常。

## Changed files / 改动文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/trusted_execution/fact_lineage.py` | `7608b0f9997eb357a7ca733343eb359183f29bcc52eae6d941c3c83efb9737b5` |
| `src/agentic_payment_experiment/trusted_execution/__init__.py` | `feb23392d6382c471af951519fb7c09558d8caa93c9bf1698b9b2eadd0f4ea96` |
| `src/agentic_payment_experiment/__init__.py` | `bcd378e3d9e35995d2cb308f8e6a56b2825663c8854996367dbf4dda6b85d9d5` |
| `src/agentic_payment_experiment/attack_overlay.py` | `2f14925231f4c59368b096fdcc2398bba8c8c4e6f774d7bcb430487ca65f25d7` |
| `tests/trusted_execution/test_fact_lineage.py` | `bb5cdecc54b08857104243ee73437c3bdc26a5e04a195cd25a6c12445561073f` |
| `tests/test_attack_overlay.py` | `afc977542e4d53abfefa42892a62b3a64df0a8cc4cecbcf7e3d662328a23dd27` |
| `samples/attacks/fact_lineage_matrix_v1.json` | `238391eb288abd0226ea72ad385268806afd2a01d907487f7b5ce1331070c14c` |
| `scripts/validation/run_fact_lineage_matrix.py` | `e1316c306090e4a436183abfa7d08981cb63ac6fb9079f9471b1a7d0961bdc7f` |

受保护文件哈希未变：

| 文件 | SHA-256 |
|---|---|
| `context_policy.py` | `be5a343ac0f48967b4b861f9b0a0c041d3f87406e6d82df1c366cb6ca810ac56` |
| `governed_action.py` | `115df903ff7ba4090438c7a5b89132882e43bc97830672899837165d05058c7e` |
| `webshop_runtime_gate.py` | `53cf905867905ae73f2886c4612a6d19cc839420677afe4f0eb4f655c87c1dd2` |
| `hashing.py` | `20a3ccbe372d48b4239aafde41dd09ac53446761d95e8e4d7f4686cb118b2931` |
| `models.py` | `d38d49fb026e2887198f00292b0ecf9c9a58ea1b9af8fbefd243f79e3b558b65` |
| `validator.py` | `9c001311c36a00d33959fffbf50784ff42928100d622a4d645b79ec8e395cbcb` |
| `payment_execution.py` | `25113d7c067a6ba43bcae7a182c60ec77404a50229987b0314805b1c10e0ce71` |

## 11. AC 映射

| AC | 执行结果 | 证据 |
|---|---|---|
| AC-01 | frozen dataclass、精确外层/节点类型、primitive-only serialization | EV-02、EV-10 |
| AC-02 | 必填字段、SourceType、tuple、唯一非空上游引用均有稳定分类 | EV-02、EV-04 |
| AC-03 | duplicate、missing ref、self-ref、cycle、duplicate upstream 均确定性失败且无部分解析 | EV-02、EV-04 |
| AC-04 | root、WEB→LLM、多来源传播均保留所有祖先 | EV-02、EV-04 |
| AC-05 | 有无 upgrade evidence 均不删除 WEB_UNTRUSTED | EV-02、EV-04 |
| AC-06 | 10 个 SourceType 全部显式测试；AGENT_DECLARED 定义为非权威祖先 | EV-02、EV-10 |
| AC-07 | Overlay 调用共享 resolver；旧策略投影完全一致 | EV-03、EV-09、EV-10 |
| AC-08 | 固定 16-case 矩阵全部 matched，字段和限制完整 | EV-04 |
| AC-09 | resolver 无 I/O、网络、进程、环境和业务决策；保护模块哈希不变 | EV-10 |
| AC-10 | 12、10、16、10、44、413、13/13 全部通过；EV triplet 完整 | EV-01 至 EV-11 |

## 12. Evidence

每个 EV 均有：

```text
EV-XX.meta.json
EV-XX.stdout.log
EV-XX.stderr.log
```

### EV-01 — Overlay 改造前基线

命令：`python3 scripts/validation/run_attack_overlays.py --output .../overlay_before.json`  
结果：6/6 PASS，冻结 `overlay_before_projection.json`。

### EV-02 — Fact Lineage 专项

命令：`python3 -m unittest tests.trusted_execution.test_fact_lineage -v`  
结果：12/12 PASS。

### EV-03 — Attack Overlay 专项

命令：`python3 -m unittest tests.test_attack_overlay -v`  
结果：10/10 PASS。

### EV-04 — Lineage Matrix

命令：`PYTHONPATH=src python3 scripts/validation/run_fact_lineage_matrix.py`  
结果：16/16 matched。

### EV-05 — Context Policy 回归

命令：`python3 -m unittest tests.trusted_execution.test_context_policy -v`  
结果：10/10 PASS。

### EV-06 — Governed Action / Runtime Gate 回归

命令：`python3 -m unittest tests.trusted_execution.test_governed_action tests.test_webshop_runtime_gate -v`  
结果：44/44 PASS。

### EV-07 — 全量回归

命令：`PYTHONPATH=src python3 -m unittest discover -s tests -v`  
结果：413/413 PASS。

### EV-08 — 正式入口

命令：`python3 run_experiment.py`  
结果：13/13 PASS。

### EV-09 — Overlay 前后策略投影

结果：旧策略字段逐项完全一致，lineage 仅为附加证据。

### EV-10 — 范围、哈希与静态审计

结果：精确类型、拓扑解析、无业务决策、无 I/O/网络/进程/环境、共享 resolver、保护文件哈希和禁止动作全部通过。

### EV-11 — 工作流验证

最终 handoff 后运行 workflow validator，要求无 `BLOCKING` finding。

## Deviations and unresolved items / 偏差与未解决项

1. 首次采集 EV-01 前的批处理命令使用 shell 变量时发生路径展开失败，未执行任何业务代码；随后用完整字面路径覆盖并成功采集 EV-01。
2. 首次正式 EV 批处理同样因 shell 变量传参兼容问题未执行测试；随后以完整字面路径覆盖 EV-02 至 EV-08，全部退出码 0。
3. 全量回归首次发现 PayBench float 与公共金融哈希严格边界冲突。未放宽 `canonical_hash`，而是在 Overlay 附加证据层增加稳定 JSON 文本摘要，并新增回归测试。最终全量 413/413。
4. 一次直接模块回归因未设置 `PYTHONPATH=src` 导致导入失败；以合同正式环境重新运行后通过，不涉及代码问题。
5. 未修改 Context Policy、SourceType、Governed Action、Runtime Gate、P1—P6、订单规则或支付生命周期。
6. 未实现提示注入组合、隐私最小化、UI、真实 WebShop、Buy Now 或支付执行。
7. 未执行网络、API、依赖安装、环境创建、commit、push 或 history rewrite。


## EV-01 — Overlay baseline

- AC: AC-07, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-01.stderr.log

## EV-02 — Fact lineage tests

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08, AC-09, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-02.stderr.log

## EV-03 — Attack Overlay tests

- AC: AC-07, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-03.stderr.log

## EV-04 — Lineage matrix

- AC: AC-02, AC-03, AC-04, AC-05, AC-06, AC-08, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-04.stderr.log

## EV-05 — Context Policy regression

- AC: AC-07, AC-09, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-05.stderr.log

## EV-06 — Governed Action and Runtime Gate regression

- AC: AC-09, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-06.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-06.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-06.stderr.log

## EV-07 — Full suite

- AC: AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-07.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-07.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-07.stderr.log

## EV-08 — Formal entrypoint

- AC: AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-08.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-08.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-08.stderr.log

## EV-09 — Overlay projection audit

- AC: AC-07, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-09.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-09.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-09.stderr.log

## EV-10 — Scope and hash audit

- AC: AC-01, AC-06, AC-07, AC-09, AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-10.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-10.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-10.stderr.log

## EV-11 — Workflow validation

- AC: AC-10
- Meta: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-11.meta.json
- Stdout: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-11.stdout.log
- Stderr: docs/05_任务交接/P9_GOVERNED_PAYMENT_FACT_LINEAGE_V1/evidence/EV-11.stderr.log
