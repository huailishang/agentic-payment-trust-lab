# H46 执行入口：整包串行，完成后统一评估

先读根 CURRENT.md，确认 H46 / CONTRACT_FROZEN / Executor / H46_OFFLINE_SERIAL_EVIDENCE_CHAIN。再读本包 CONTRACT、VALIDATION_PLAN、FIXTURE、SOURCE_LOCK、BASELINE。冻结资产由 Evaluator 持有，不改。

本包大白话目标：核实外部题目和判卷 → 真正调用固定转账源码测四种状态 → 看现有完整付款闸门缺什么输入 → 把真实发现装成别人能核对的候选材料。不是跑模型攻击或接支付宝。

## 串行完成，无需逐阶段等待评估

1. 运行 `python docs/05_任务交接/H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1/EVALUATOR_CHECK.py baseline`。无新依赖、无网络。
2. 完成来源/授权审计，按 CONTRACT 接口实现 MEASUREMENT.py；源码调用与状态/评分由冻结检查器注入并复核。可用 measurement 子命令做 L1。
3. 写清三类判定：完成正常目标、达到攻击目标、产生禁止交易不是同一回事。必须保留“正确+错误”反例。
4. 跑真实缺证据产品诊断，交字段映射与单一 DECISION。不支持可以完成测量；不为通过造订单或补确认，不改产品。
5. 形成 candidate_bundle，标 UNREVIEWED_CANDIDATE。verify_bundle.py 提供 verify(path)，成功时重算八条源状态/评分；产品两条仅完整性核对，不宣称重跑产品。干净复制与冻结负例必须过。
6. 审查许可/秘密/机器路径/依赖与声明，写 REPORT、L2 EV 索引、包内迭代和剩余缺口。
7. 最后运行一次完整 L2 与中央结构校验；3 次正式 L2 总上限内可自修本包，完成后一次提交等待统一评估。

完整 L2（在仓库根）：

```powershell
python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H46_AGENTDOJO_OFFLINE_EVIDENCE_CHAIN_V1/evidence/l2_executor --mode executor
python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md
```

保存每次正式 L2，失败记录不能覆盖后消失；最终 REPORT 指向最后一组门禁，并登记前两次（若存在）。只有 L2 全通过才 SUBMITTED_FOR_REVIEW；执行者不签 PASS、不改 CURRENT。

## 关键边界

MEASUREMENT / 工具源码片段 / 上游评分 / 产品诊断分别标来源。使用独立合成授权信封，不能用 Gold 建授权；币种是实验 profile 补充。没有模型在环和真实攻击轨迹，不报告模型攻击成功率。

候选包文件全登记 hash；verify_bundle 不从原工作区、用户目录或网络读资料。仅用现有 Python/pydantic；不复制 raw EV 的本机路径/命令日志、真实凭据、思维链或整个 dirty worktree。候选材料尚未验收，不能写成第三方背书或 H45 已完成。

需要改产品、冻结范围/来源、模型/网络/依赖或预算时 BLOCKED，写清原因。普通本包编码/文档/打包错误在原范围内自修，不逐阶段交回评估。既有工作区改动原样保留；不暂存、不提交、不推送、不通知其他聊天。
