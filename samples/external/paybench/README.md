# PayBench 外部挑战集本地快照

> 更新时间：2026-07-27

## 1. 来源

本目录只保存 PayBench Phase 1 的第一批最小挑战快照，不引入完整 PayBench 运行时。

```text
上游仓库：conorplunkett/Unsafe-Commercial-Autonomy
固定提交：f052ab411f28e79c73f3897029a017f29f5cd4e2
许可证：MIT
访问日期：2026-07-27
```

上游固定来源文件：

```text
data/scenario_sets/v1_50_scenarios.md
data/answer_keys/v1_constraints.json
```

本地文件：

```text
phase1_selected_10.json
```

## 2. 为什么只取 10 题

第一阶段按 PayBench Phase 1 的五个方向各取一组危险案例（Trap）和安全对照（Lookalike）：

```text
A1 预算 / 总成本
B1 商户授权范围
C1 人工审批阈值
D1 隐私披露
E1 提示注入

5 组 × 2 = 10 题
```

目的不是追求题量，而是先验证本项目能否正确承接外部题目合同和评分方式。

## 3. 本地做了什么归一化

PayBench 的动作语义被映射到本项目统一决策：

```text
purchase     -> ALLOW
ask_approval -> CONFIRMATION_REQUIRED
refuse       -> DENY
```

部分挑战允许多个安全答案。例如 A1 Trap 同时允许：

```text
ask_approval
refuse
```

因此 M5 已增加 `acceptable_decisions`，避免强行把外部题压成唯一正确枚举。

同时增加本项目用于 M5 副作用检查的归一化标签，例如：

```text
payment_over_budget
unapproved_merchant_purchase
approval_evasion_split
optional_personal_data_disclosure
prompt_injection_compliance
```

这些 `local_*` 字段属于本项目适配层，不应表述为 PayBench 官方字段。

## 4. 当前边界

当前已经完成两种运行方式。

外部 Agent / Runtime 提交 attempts：

```text
PayBench 固定 10 题
    -> 外部 attempts.json
    -> M5 统一评测
    -> 独立 external report
```

运行：

```text
python run_paybench_challenges.py --attempts <attempts.json>
```

当前规则覆盖审计：

```text
python run_paybench_challenges.py --current-rules
```

当前协议中立规则可以直接表达 A1 / B1 / C1，并已通过 Attack Overlay 接入 E1，共 8 题可执行且 8/8 通过；当前仅 D1 隐私披露 2 题标记为 `UNSUPPORTED`，报告整体状态仍为 `PARTIAL`。

因此“参考答案输入后 10/10 PASS”只能证明适配器和评测器合同正确，不能作为当前系统的 PayBench 实际成绩；当前规则的真实覆盖结果是 **8 题可执行、2 题能力缺口**。

## 5. 更新规则

不得自动跟随上游 `main`。

上游题目或约束变化时，应先：

```text
核对新提交 / Release
    -> 比较题目与答案键变化
    -> 审查本地映射
    -> 新建明确版本
    -> 再更新测试
```

避免外部基准变化后，本项目结果在没有审查的情况下悄悄漂移。
