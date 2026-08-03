# Executor Report

Task ID: `P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1`
Executor status: `READY_FOR_REVIEW`
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`
Implementation commit: `NONE`

```yaml
workflow: evaluator-executor-workflow/v2
task_id: P8-X402-OFFLINE-CONFORMANCE-HARNESS-V1
executor_state: READY_FOR_REVIEW
commit_created: false
push_performed: false
api_call_performed: false
```

## Workspace snapshot

- Baseline and final HEAD remain `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`.
- Inherited P4–P7 code, tests, task packets and evidence remain uncommitted and were not staged, reverted, deleted or attributed to P8.
- P8 product changes remain within the contract allowlist; P7 UI and existing payment/trust algorithms were not modified.
- No network, API, wallet, signing, payment, commit, push or history rewrite was performed.

## Authorization record

```yaml
implementation_commit: NONE
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
network_call_performed: false
wallet_created: false
signature_created: false
payment_executed: false
real_or_testnet_funds_used: false
```

## 1. 执行结果

新增了一个仅使用本地合成 fixture 的 x402 离线一致性验证工具。它把有限的 x402 请求、付款要求、付款证明、facilitator 验证/结算和资源交付观察转换为项目已有的协议中立事实，并复用现有：

```text
Payment Binding
Idempotency
Original Transaction Binding
Payment Query Finality
Payment Status Conflict
Replay
```

未修改现有授权、支付、身份、绑定、可信上下文、重放、最终性或统一评测算法；未修改 P7 UI；未增加外部依赖。

六个确定性案例均由实际适配与事实函数推导，结果为：

```text
正常绑定                         → ALLOW
偷换收款方                       → BLOCK
修改金额 / 资产 / 网络            → BLOCK
跨资源复用付款证明                → BLOCK
重复 / 并发使用同一证明           → BLOCK
结算成功、异步失败、资源交付失败   → CONFLICT
```

## 2. 改动文件与 SHA-256

### 2.1 产品、测试、fixture 与说明

| 文件 | SHA-256 |
|---|---|
| `src/agentic_payment_experiment/adapters/x402.py` | `d863aa463cb0dce6b3c1bd262d68179b8bb4ec907e3d7e4f5247cd919a4d2812` |
| `src/agentic_payment_experiment/x402_conformance.py` | `5240369a4620b5339538f62a294564fe2d4cda06c11b5a4aefb00fdb16cc9b2e` |
| `src/agentic_payment_experiment/adapters/__init__.py` | `d6ea7127d18c791b51e15e603966ca03e8ed90f3ec7af21ae19ce1f9074e6754` |
| `tests/test_x402_adapter.py` | `521e604a05809f69b2aa8ff8e2aeefa0f4dc1b6cfdec9470c5c5bc5cf85e257f` |
| `tests/test_x402_conformance.py` | `78f952ec07d6b3a8a90296a001bbaeaef8de96c3ebec34744d115fc72d001526` |
| `samples/protocols/x402/x402_offline_cases_v1.json` | `5e34d70667faf7c2d91e0bf7b70086a7bb106bb552a85989f6f6f12915292153` |
| `docs/04_验证体系/x402离线一致性验证方案_v1.md` | `5edd674080d1526aca16bd8370d2bee83123dbcaec68c04cebdc2e271653a9d6` |

### 2.2 证据辅助脚本

| 文件 | SHA-256 |
|---|---|
| `evidence/EV-05_scope_check.py` | `b9ccf4dbd77745e14b01a92b5d0cbe6e581d1116c209fe208006549ff964750f` |
| `evidence/EV-07_case_matrix.py` | `7a8c1d2322bb24440dbd76fc2e911cdf4761b7fc5acabdf442ce1ef07a0cb722` |

`REPORT.md` 是自引用清单，不在正文内固定自身哈希；最终范围证据 `EV-05.stdout.log` 会记录执行时的报告文件哈希。每个 EV 的 `.meta.json` 记录对应 stdout/stderr 文件名、字节数和 SHA-256。

## 3. Fixture 清单与合成数据声明

Fixture：

```text
samples/protocols/x402/x402_offline_cases_v1.json
fixture_version = x402-offline-fixture-v1
synthetic = true
case_count = 6
```

案例清单：

| Case ID | 合成变化 | 预期 |
|---|---|---|
| `X402-C01-BINDING-MATCH` | 要求、证明、资源、结算和交付一致 | `ALLOW` |
| `X402-C02-PAYEE-CHANGED` | 证明中的收款方被替换 | `BLOCK` |
| `X402-C03-VALUE-RAIL-CHANGED` | 证明中的金额、资产和网络被替换 | `BLOCK` |
| `X402-C04-CROSS-RESOURCE-REUSE` | 东京资源的证明被用于大阪资源 | `BLOCK` |
| `X402-C05-DUPLICATE-CONCURRENT-REUSE` | 同一 proof 形成两个并发交付尝试 | `BLOCK` |
| `X402-C06-SETTLEMENT-DELIVERY-CONFLICT` | 结算成功、异步失败、交付失败 | `CONFLICT` |

所有标识均为 `synthetic-*` 或固定测试路径。Fixture 不包含真实秘密、私钥、助记词、客户身份、卡数据、生产凭据或真实资金交易。`project_context` 被明确标注为项目本地授权桥接字段，不宣称属于 x402 线上报文。

## 4. x402 字段到协议中立事实的映射

| 外部/fixture 字段 | 协议中立事实 | 使用方式 |
|---|---|---|
| HTTP method、resource ref | `Order.service_id` + 资源证据 | 检查证明是否跨资源使用 |
| requirement id | `Order.order_id`、原交易引用 | 稳定交易对象引用 |
| amount | `Order.total_amount`、`TransactionRequest.amount`、`PaymentExecutionRecord.amount` | 复用现有连续绑定 |
| asset | 中立模型的 `currency` | 复用现有连续绑定 |
| payee | 订单、请求和支付执行收款方 | 复用现有连续绑定 |
| scheme、network | `Order.candidate_rails` + adapter 边界事实 | 不向支付核心引入 x402 专用字段 |
| request ref | `TransactionRequest.request_id`、执行对象引用 | 绑定请求与付款证明 |
| proof ref | `PaymentExecutionRecord.payment_id`、`idempotency_key` | 检查重复/并发使用 |
| facilitator settlement | `PaymentStatusObservation` | 只表示支付状态观察 |
| facilitator async observation | `PaymentStatusObservation` | 与主动观察形成冲突事实 |
| resource delivery | `FulfillmentRecord` | 与支付结算状态分离 |
| project authorization context | `IntentMandate` | 项目本地桥接，不是 x402 wire claim |

付款要求摘要使用已有 `canonical_hash`，覆盖资源、请求、要求标识、方案、网络、资产、金额和收款方。该摘要仅用于本项目确定性离线验证，不声称符合官方签名标准。

## 5. 六案例实际结果矩阵

原始完整矩阵：`EV-07.stdout.log`。

| Case | Status | Expected | Actual | 主要实际原因码 | 业务成功确认 |
|---|---|---|---|---|---|
| C01 | `PASS` | `ALLOW` | `ALLOW` | `x402_conformance_allow` | `true` |
| C02 | `PASS` | `BLOCK` | `BLOCK` | `payment_request_payee_mismatch`, `x402_payee_mismatch`, `x402_binding_blocked` | `false` |
| C03 | `PASS` | `BLOCK` | `BLOCK` | `payment_request_amount_mismatch`, `payment_request_currency_mismatch`, `x402_network_mismatch` | `false` |
| C04 | `PASS` | `BLOCK` | `BLOCK` | `x402_proof_resource_mismatch`, `x402_cross_resource_reuse` | `false` |
| C05 | `PASS` | `BLOCK` | `BLOCK` | `x402_duplicate_proof_reuse_blocked` | `false` |
| C06 | `PASS` | `CONFLICT` | `CONFLICT` | `payment_status_opposite_terminal_claims`, `x402_settlement_succeeded_delivery_failed` | `false` |

关键证据：

- C05 的同一 proof/idempotency key 有两个交付尝试，但成功交付观察数为 `1`，第二个尝试被作为重复使用阻断；
- C06 的 facilitator settlement 为 `SUCCEEDED`，异步观察为 `FAILED`，资源交付为 `FAILED`；现有冲突事实返回 `CONFLICT`，`business_success_confirmed=false`；
- 测试会把 fixture 的 `expected` 改成错误值，确认实际事实不变时案例状态变为 `FAIL`，证明 PASS 不是展示元数据写死；
- 每个案例均生成资源、付款要求、付款证明、验证、结算、异步观察、交付、绑定、幂等、最终性、冲突和回放证据。

## 6. 无外部副作用证明

实现没有导入网络、钱包、链上或外部 SDK 依赖。测试使用 mock 将 `socket.socket` 和 `urllib.request.urlopen` 设置为一旦调用就抛错；新增测试仍全部通过。

`EV-07` 的报告级副作用记录：

```json
{
  "network_called": false,
  "wallet_created": false,
  "signature_created": false,
  "payment_executed": false
}
```

本任务实际未发生：

```text
外部 HTTP/API 调用
Coinbase/CDP 账户或 API Key 使用
x402.org facilitator 调用
钱包创建
签名生成
faucet / token / gas 操作
测试网或主网交易
真实或测试资金付款
回调或资源交付副作用
```

## 7. 验收证据

每个证据均包含：

```text
EV-xx.meta.json
EV-xx.stdout.log
EV-xx.stderr.log
```

| EV | 命令/用途 | 原始结果 |
|---|---|---|
| `EV-01` | P8 adapter + conformance tests | exit `0`; `Ran 14 tests`; `OK` |
| `EV-02` | P4–P6 focused regressions | exit `0`; `Ran 35 tests`; `OK` |
| `EV-03` | full unittest discovery | exit `0`; `Ran 275 tests`; `OK` |
| `EV-04` | `run_experiment.py` | exit `0`; S01–S13 `13/13`; internal baseline `PASS`; AP2 `2/2`; Attack `6/6` |
| `EV-05` | baseline、允许路径、空白、哈希、禁止导入和范围检查 | exit `0`; task scope `PASS` |
| `EV-06` | workflow validator | exit `0`; `OK: v2 routing and required artifacts are structurally valid` |
| `EV-07` | 六案例完整结果与证据矩阵 | exit `0`; `case_count=6`; `all_pass=true`; side effects all false |

已生成证据元数据中的输出摘要哈希：

| EV | stdout SHA-256 | stderr SHA-256 |
|---|---|---|
| EV-01 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `e7ab500ddf08bf23c09129076a98ffc0f8e4eb259011b0a4d969ec7e632b5034` |
| EV-02 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `82b279faff2c204dd75493a8359328f86276b9d0f05d6c80e7b00809b0994092` |
| EV-03 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `ae4780966aa38f9fe9d52b5775104f74e4d1c372c6a70033db26294be2ce9d49` |
| EV-04 | `82fb3f51147e6ef6f5a4952db9e94ca4ac0eec9ab149524e4ab97353bcd0d81b` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| EV-07 | `fdba8bfc5bda97e921727e627c248f8bf87ee6875d88a5fd029a9a8eda7ff649` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

EV-05、EV-06 的 stdout/stderr 精确哈希由各自最终 `.meta.json` 保存。

## 8. AC 映射

| AC | 实现/事实 | 证据 |
|---|---|---|
| AC-01 bounded fixture model | 版本化 JSON；覆盖 method/resource、scheme/network/asset/amount/payee、requirement digest、proof、verify/settle/delivery、引用和时间 | EV-01、EV-07 |
| AC-02 neutral adapter boundary | 映射到既有 neutral models；缺失、类型、枚举、标识、摘要和不支持语义 fail-closed；无外部动作 | EV-01、EV-05、EV-07 |
| AC-03 six deterministic cases | 六案例实际结果由 binding/idempotency/finality/conflict/replay 推导，全部 PASS | EV-01、EV-07 |
| AC-04 evidence and limitations | 输出资源、要求、证明、重复使用、facilitator、交付、原因和回放；文档声明离线边界 | EV-07、`x402离线一致性验证方案_v1.md` |
| AC-05 regression and scope | focused 35、full 275、原入口 13/13，baseline/AP2/Attack 保持；范围检查通过 | EV-02、EV-03、EV-04、EV-05 |

## 9. 偏差与不支持语义

### 9.1 命令偏差

合同使用 `python` 示例；当前环境未暴露 `python`，因此按合同允许方式使用：

```bash
env PYTHONPATH=src python3 ...
```

### 9.2 支持边界

当前仅接受：

```text
fixture version: x402-offline-fixture-v1
scheme: exact
network: base-sepolia / solana-devnet
```

下列能力未实现并被明确标注为限制：

```text
官方 SDK 兼容性
真实 wire-format 完整解析
密码学签名或持钥证明
facilitator 生产安全
商户实现正确性
法规合规
测试网/主网就绪
链上重组、Gas、nonce、确认深度
真实网络并发语义
```

## 10. 范围与继承状态

P4–P7 的产品修改、测试、任务包和证据原本就处于未提交状态，本任务未清理、覆盖或归属这些继承内容。全局 `git diff --check` 若仍显示历史证据文件空白问题，由 EV-05 标为继承且超出 P8 范围；P8 任务文件自身的空白和 task-scoped diff 检查为通过。

HEAD 保持：

```text
8acaa9e4319240d258f14d8a23b1f15cc71d09b6
```

未 commit，未 push，未改写历史，未调用外部 API/网络。
