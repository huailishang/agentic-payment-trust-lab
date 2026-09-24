# H-40 Frozen Repair Contract

Task ID: `H40_ALIPAY_LIVE_AUTHORIZATION_GATE_REPAIR_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: `repair`
Contract state: `CONTRACT_FROZEN`
Dispatch mode: `SINGLE`
Date: 2026-09-21
Map revision: `2026-09-21-r57`
Baseline HEAD: `5e7c0c0b78aeec9c241078a37858cf3f2d8a14b3`
Active bottleneck: `B-06`
Parent: H39 PASS / CONTRACT_CHANGE_REQUIRED; H38 PARTIAL / LIVE_BLOCKED.

## 全局位置与目标

最终目标是授权、支付副作用与 Provider 证据连续可验证。A–D 已关闭，E 本地代表性闭环，F 当前。第一业务瓶颈仍是支付宝 fixture/证据能力；零容忍前置缺陷是 H38 探针网络入口未检查 CURRENT 授权。本包只关闭 H39 REVIEW 的 R4，不重复 R1–R3 研究。AP2 细节、VI、B16 均不能替代此修复。

假设：在密钥读取/签名和 reservation 前检查当前任务授权，并在 reservation 紧前重读，可以阻止旧任务或失效授权发起请求。完成只表示入口受控，不表示支付宝 live PASS。

## 范围与授权

允许修改：`scripts/h38_alipay_sandbox_probe.py`；可选新增 `scripts/h38_authorization_gate.py`；新增 `tests/test_h38_authorization_gate.py`；本包 REPORT.md 与脱敏 evidence。

保护对象：Trust Core、Alipay adapter、密钥检查器、H38 evaluator 检查器、H39 已验收资料和既有 reservation。CURRENT/地图由 Evaluator 管理。不得更改冻结合同/检查器降低标准。

真实交易、验付、网络请求、开通/注册、真实密钥读取预算全部为 **0**。只用临时目录、合成输入、fake signer/transport。无新依赖、commit/push、历史改写；不运行官方 Skill。

## 授权判定合同

`--execute` 固定读取 ROOT/CURRENT.md，不提供 CLI/env 替代路径、force 或 skip 开关。仅解析唯一 fenced yaml 工作流状态块的顶层字段，不能搜索整篇 Markdown 子串。可用标准库实现严格最小解析；重复字段、多状态块、嵌套伪字段、格式损坏、缺失或读取失败都 fail closed。

未来 H38 在线执行仅接受以下组合（本轮只在测试夹具模拟）：

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1
state: EXECUTING
current_role: Executor
authorization_api_call: true
contract_path: docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/CONTRACT.md
```

true 只接受未加引号布尔字面量；字符串可支持普通标量与成对引号，写入测试。其他正常元数据可保留，但不能覆盖安全字段。PASS/REVIEW/CONTRACT_FROZEN 等状态不能替代 EXECUTING。H40 即使误设 true 也拒绝。这是必要门，不能替代人工授权、后续 fixture 合同和原预算。

在参数解析后、inspect/sign_request 前检查一次；reservation 紧前重新读取，禁止 import 时缓存。二次检查失败必须零 reservation、零网络。任意并发篡改的原子事务保证不属于本包，不宣称完全消除竞态。

缺省 dry-run 不预留、不联网，不扩其业务语义。保持原 HTTPS sandbox、禁止重定向、一次调用、输出目录、脱敏及 reservation 不可自动清除的护栏。

## 验收条件

- AC-01：集成测试从实际 probe 入口证明拒绝发生在 inspect/sign_request/reservation/opener 前；非零退出且上述调用均为零，不只单测 parser。
- AC-02：合法模拟状态与完整合成 fixture 通过原 probe，只调用 fake transport 一次；不带 --execute 时零调用，不使用真实密钥。
- AC-03：wrong task（含 H39/H40）、false/缺失/带引号 true、错误 role/state/contract/workflow、缺失或损坏 CURRENT、重复字段/状态块、正文注释伪授权与嵌套伪字段均拒绝。
- AC-04：第一次允许后临时状态切为 false/wrong task，第二次检查拒绝且不预留；已有 reservation 的重复执行不再次调用。
- AC-05：非 sandbox gateway、非法输出路径、缺 fixture 等护栏不回归；保护文件 hash 不变，无 live 调用、秘密与新依赖。
- AC-06：REPORT 给出逐项证据、测试命令/退出码、变更后 hash 与剩余阻塞。R4 修复后 H38 仍 LIVE_BLOCKED，交 Evaluator L3。

## 验证与停止

先核对 BASELINE.json；漂移停回 Evaluator，不覆盖他人改动。只运行本包专项、已有 adapter 和 evaluator 测试；不修改支付核心则不重复全量/项目 baseline。继承的 Windows WebShop 失败保留登记。

需要扩 endpoint、放松绑定、安装依赖或真实调用即停止。一次报告集中列出结果，不继续泛搜资料。Executor 不自行声明 L3 通过、不开启 live、不删除 reservation。

## 下一阶段及 Human 输入

R4 PASS 后，Evaluator 使用 H39 已固定官方来源冻结 Route A 最小方案：method/endpoint/transport、输入和秘密流向、内存 proof 捕获、调用预算和退出点。完整脚本不可直接执行；HTTP cashier、自动重试、临时敏感文件和履约必须逐项处理，不能猜改 HTTPS。

若官方路线无法满足秘密传输或严格绑定，明确 STOP / UNSUPPORTED 或提交更窄证据测量合同；保留 H38 未通过，不无限重复要求补 fixture。

本包 Human 无需新材料。后续确需交互时只请求对应页面登录/验证码；已有密钥位置丢失只问路径；买家 UID 仅在选定源码证明必需后取得。禁止要求先人工付款、重发 APPID/私钥正文或生产信息。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-07, PCAC-09, PCAC-20]
  applicability: CORE
  maturity_scope: H38 live probe workflow authorization gate only
  maturity_before: M0 MISSING
  maturity_after_target: M3 TESTED
  Test: fake transport integration and negative authorization cases
  Evidence: BASELINE.json, REPORT.md, test outputs and independent L3
  residual_risk: no live Provider evidence or production assurance
```
