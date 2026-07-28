# Attack Overlay v1 执行记录

> 日期：2026-07-28

## 1. 目标

第一版不假装已经拥有真实 LLM Agent，也不把“文本里写了攻击指令”直接等同于真实 Prompt Injection 攻击成功。

本次只验证一条最小但关键的信任边界：

```text
可信用户委托 / 支付请求
        +
不可信网页或工具返回文本
        ↓
攻击文本可以被读取和记录
        ↓
但不能直接改写金额、商户、Agent、委托边界等可执行支付字段
        ↓
继续交给原有验证器 + M5 统一评测器
```

## 2. 外部参考核对

参考项目：`ethz-spylab/agentdojo`

- 官方定位：用于评估 LLM Agent 在不可信外部数据中的 Prompt Injection 攻击与防御。
- 本次核对 Release：`v0.1.35`，提交 `a75aba7`。
- License：MIT。
- 访问日期：2026-07-28。
- 本项目只吸收“正常任务 + Injection Overlay + 安全/效用分开评测”的方法，不安装 AgentDojo，不复制其完整运行时。

## 3. TDD 过程

先新增 Attack Overlay 测试，第一轮按预期失败：

```text
ModuleNotFoundError: agentic_payment_experiment.attack_overlay
```

随后实现：

```text
src/agentic_payment_experiment/attack_overlay.py
samples/attacks/attack_overlay_v1.json
scripts/validation/run_attack_overlays.py
```

并增加 CLI 回归测试：

```text
tests/test_attack_overlay.py
tests/test_attack_overlay_entrypoint.py
```

## 4. 第一版场景

基于 `S01_normal.json` 叠加 5 个 Overlay：

```text
A00 普通商品描述                         对照组
A01 恶意抬高 request.amount             攻击
A02 恶意替换 request.merchant           攻击
A03 恶意替换 request.agent_id           攻击
A04 恶意扩大 mandate 金额/商户范围      攻击
```

运行：

```powershell
python scripts/validation/run_attack_overlays.py
```

结果：

```text
total=5
passed=5
failed=0
attack_cases=4
blocked_attack_cases=4
decision_drifts=0
trusted_state_mutations=0
```

报告：

```text
artifacts/attack_overlay_v1_report.json
```

## 5. 全量回归

```text
184/184 PASS
```

Attack Overlay 没有破坏现有 S01—S13、M5、PayBench、AP2、可信执行和交互实验台能力。

## 6. 结论与边界

当前能证明：

> 在本项目当前确定性执行链里，不可信网页/工具内容没有直接修改可信支付输入的权限；已建成可回归的攻击覆盖层骨架，并能交给 M5 判决策漂移和禁止副作用。

当前不能证明：

- 真实 LLM 不会被 Prompt Injection 欺骗。
- 自然语言攻击文本能够被可靠解析成真实攻击动作。
- 已达到 AgentDojo benchmark 水平。
- 已达到生产支付安全或合规要求。

## 7. 下一步

下一步不继续堆更多攻击文本，先把已有模块收进同一个体验入口：

```text
run_experiment.py --serve --open
        ↓
S01—S13
AP2 HP/HNP
PayBench
Attack Overlay
        ↓
统一运行 + M5 统一评测 + UI 展示
```

Attack Overlay 在 UI 第一版只需要展示：攻击文本、试图修改的可信字段、被拦截字段、最终决策、M5 结果。
