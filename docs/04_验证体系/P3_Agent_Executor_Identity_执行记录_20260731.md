# P3 Agent / Executor Identity v1 执行者记录

> 日期：2026-07-31  
> 任务：`P3-AGENT-EXECUTOR-IDENTITY-V1`  
> 基线：`dd093ff272f34e4a2e2c9a19ffa2ca4f0dd2b873`  
> 工作流状态：`READY_FOR_REVIEW`  
> 说明：本文是执行者证据摘要，不签发 PASS；最终 verdict 由独立评估者给出。

## 1. 候选实现做了什么

P3 候选实现新增协议中立的身份保证事实：

```text
IdentityAssuranceLevel
    DECLARED
    BOUND
    VERIFIED

verify_agent_executor_identity(...)
    -> IdentityAssuranceFact
       status
       reason_codes
       assurance_level
       authorized / request / execution / identity Agent refs
       provider / executor instance / credential refs
       credential availability
```

当前离线核验器最多产生 `BOUND`。`VERIFIED` 只是为未来显式 credential verifier、provider attestation、workload identity 或同等级验证器保留的封闭枚举值；字符串相等、字段非空或 `credential_ref` 存在都不能升级到 `VERIFIED`。

`execute_with_payment_binding_gate()` 现在同时消费上游决策、P2 和 P3：

```text
上游非 ALLOW
    -> 保持上游结果，不调用 callback
P2 MISSING_EVIDENCE
    -> INDETERMINATE，不调用 callback
P2 INVALID
    -> DENY，不调用 callback
P3 MISSING_EVIDENCE 或低于 BOUND
    -> INDETERMINATE，不调用 callback
P3 INVALID
    -> DENY，不调用 callback
上游 ALLOW + P2 VALID + P3 VALID + 至少 BOUND
    -> callback 恰好调用一次
```

可信执行函数仍只返回事实；`ALLOW / DENY / INDETERMINATE` 映射留在支付域。

## 2. 正式消费路径

正式结果卡使用现有 S10 的完整 Authority → Order → Payment Request → Payment Execution 离线交易链，通过真实支付闸门计算三条 P3 结果：

| case | P2 | P3 | assurance | decision | callback |
|---|---|---|---|---|---:|
| `P3-BOUND` | VALID | VALID | BOUND | ALLOW | 1 |
| `P3-AGENT-SUBSTITUTED` | VALID | INVALID | DECLARED | DENY | 0 |
| `P3-EXECUTOR-MISSING` | VALID | MISSING_EVIDENCE | DECLARED | INDETERMINATE | 0 |

结果稳定暴露 status、assurance level、reason codes、Agent 引用、executor instance、provider 引用和 credential 可用性。界面结果卡明确写明：

> 这里只证明固定离线引用的确定性绑定，最高为 BOUND；不执行真实身份认证、凭证有效性或持有证明。

本轮没有新增 S14，没有修改 `samples/regression/internal_baseline_v1.json`，也没有结构性重构主 UI。

## 3. 验证结果

| VP | 结果 | 摘要 |
|---|---|---|
| VP-01 | exit 0 | P3 身份专项 6 tests / OK |
| VP-02 | exit 0 | P2 闸门、validator、生命周期、恢复 46 tests / OK |
| VP-03 | exit 0 | runner、presentation、interactive lab 44 tests / OK |
| VP-04 | exit 0 | 完整回归 218 tests / OK |
| VP-05 | exit 0 | S01—S13 13/13；内部冻结基线 PASS；M5 13/13、禁止副作用 0 |
| VP-06 | exit 0 | 声明审计命中均为边界、否定性说明、保留枚举或历史研究材料；未发现 P3 夸大声明 |
| VP-07 | exit 0 | 实现文件、直接相关测试、允许文档与交接证据在冻结范围内 |

P3 正向路径不依赖 `VERIFIED`；固定离线路径未产生 `VERIFIED`。

## 4. 原始证据

完整 stdout、stderr、exit code、工作目录和命令保存在：

```text
docs/05_任务交接/P3_AGENT_EXECUTOR_IDENTITY_V1/evidence/
```

主要文件：

```text
EV-01_VP-01_identity_focused.log
EV-04_EV-06_VP-02_gate_regression.log
EV-05_VP-03_integration.log
EV-05_identity_assurance_artifact.json
EV-07_VP-04_full_regression.log
EV-08_VP-05_formal_entrypoint.log
EV-09_VP-06_claim_audit.log
EV-02_EV-09_VP-07_scope.log
EVIDENCE_MANIFEST.json
```

`EVIDENCE_MANIFEST.json` 记录每个原始证据文件的字节数和 SHA-256。

## 5. 明确未证明

本候选实现没有证明或实现：

- 真实 Agent 身份认证、身份核验或认证器验证；
- credential validity、credential possession 或密钥控制；
- provider attestation、workload identity、PKI、OAuth/OIDC、DID 或 federation；
- 生产凭证、生产级记录防篡改、生产支付安全或监管合规；
- 真实付款、退款、重试、资金移动、网络身份服务或外部系统写入。

因此 P3 候选状态保持 `READY_FOR_REVIEW`，不能由本文自行改为 PASS。
