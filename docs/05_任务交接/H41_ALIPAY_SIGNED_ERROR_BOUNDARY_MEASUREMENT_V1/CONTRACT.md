# H-41 Frozen Measurement Contract

Task ID: `H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1`
Workflow: `evaluator-executor-workflow/v2.2`
Task kind: one_off
Measurement semantics: measurement-only (bounded probe implementation included)
Contract state: `CONTRACT_FROZEN`
Dispatch mode: `SINGLE`
Date: 2026-09-22
Map revision: `2026-09-22-r61`
Baseline HEAD: `0b99f3d1f3db180a37bcb8e6512fb7849711ea72`
Active bottleneck: `B-06`

## Strategic basis / 全局位置、假设与结束点

A–D 完成、E 本地闭环、F 当前。项目目标是可信授权、支付动作及证据连续；第一瓶颈是支付宝实际证据不足。H40 已 PASS，不再扩闸门。Route A 因固定源码的 HTTP 收银等行为不满足现边界暂停，详见 EVALUATOR_DECISION.md。

本包假设：无需创建交易，向已冻结 HTTPS sandbox payment.verify 发一条明确合成的诊断请求，可能取得能在已配置支付宝公钥下验证的响应，从而分离网络、接口处理和响应真实性边界。不得保证它返回特定错误码或签名，也不得假定请求参数形状必被远端接受。

本包不是 H38 成功支付或 proof 篡改负例，没有有效交易正对照；所有付款、买家认证、四维绑定结论保持 NOT_MEASURED。完成一个有界测量即可停止，不围绕错误码不断改请求重试。

## 两个执行阶段与权限

**当前仅派发 P0 离线准备**：新增最小诊断探针、合成测试、报告，真实网络/真实密钥读取预算均为 0。无须 Human 新材料。P0 完成报告 `OFFLINE_READY_FOR_REVIEW`，交 Evaluator L3，Executor 不自行进入 P1。

**P1 是本合同固定的后续测量，尚未放行**：Evaluator 接受 P0 后，记录被批准的代码 hash，在 CURRENT 设置下面唯一组合后才能执行。沿用既有 Sandbox 授权，不重复索取笼统授权；若需要超出本合同的权限则另行处理。

```yaml
workflow: evaluator-executor-workflow/v2.2
task_id: H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1
state: EXECUTING
current_role: Executor
contract_path: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/CONTRACT.md
authorization_api_call: true
execution_phase: H41_SINGLE_DIAGNOSTIC
```

`--execute` 固定读取 ROOT/CURRENT.md；可复用已验收 `parse_current_workflow`，但不修改 H38 的 EXPECTED 或允许任务列表，也不伪装成 H38。H41 探针自己的精确 tuple 包括 phase；literal true、单一状态块和双重读取要求继承 H40。第一次在真实密钥读取/签名前，第二次在 reservation 紧前。不提供 force/skip/env 路径替换。默认 dry-run 只检查合成计划，不读取真实密钥或签名。

## 唯一允许的 P1 请求

- HTTPS POST：`https://openapi-sandbox.dl.alipaydev.com/gateway.do`。
- method：`alipay.aipay.agent.payment.verify`，RSA2，复用 H38 `sign_request`。
- `trade_no` 固定为 32 个 ASCII `0`；`payment_proof` 固定为 64 个 ASCII `0`。二者是有意合成的诊断占位，绝不标记为真实交易或有效 proof，也不保证远端不存在同名记录。
- 省略 `client_session`，不读取买家 UID、不伪造买家身份签名。对会话缺失/参数格式拒绝如实记录，不补参数再试。
- 输入只允许已授权 sandbox APPID 和本地密钥文件路径。不读取 H38 真实 fixture 环境变量，不接受 CLI 覆盖 trade/proof/gateway/method/session。
- 私钥只用于本地签名，不传输私钥；签名请求只发至上面的 HTTPS 地址。正常 TLS 主机/证书验证，不关闭校验、不接受重定向。
- 全包 P1 最多 **1 次 HTTP attempt**，包括超时/异常；无自动或手动重试，无并发多跑。造单、收银、付款、履约、查询恢复、callback、生产、真实资金预算 **0**。
- 请求前以独占创建方式建立固定 `H41_DIAGNOSTIC.reserved`，在本包 evidence 目录持久保留；换 output 文件名也不能绕过。保留失败/超时 reservation，不自动删除。创建失败、已有 reservation、输出已存在或越界均在网络前拒绝。
- timeout=30s；响应最多读取 1,000,001 bytes，超出 1,000,000 拒绝。输出缺失但 reservation 存在也不得补跑。

## 内存验签与结果分类

同次收到的 bytes 在内存中用既有 `signed_response_parts` 取准确签名字节，再执行 RSA2 验签；禁止重序列化后验签、信任响应布尔值或为 L3 重发请求。可只读复用 H38 `response_observer.observe` 形成第二观测；明确共享 parser/同进程的独立性限制。不调用 H38 `verify_response` 时伪造 expected 来冒充绑定证据。

仅在验签通过后读取业务 code/sub_code 作可信分类：

- `SIGNED_BUSINESS_ERROR`：签名成立且 code 为非空字符串、不是 `10000`。记录其错误层级不确定；不推导 proof 篡改被阻断或接口资格已确认。
- `SIGNED_UNEXPECTED_SUCCESS`：签名成立且 code=`10000`。立即 STOP/交 Evaluator；不得认为占位 proof 有效，不触发后续动作。
- `UNVERIFIED_RESPONSE`：缺签名、验签失败、未知 envelope、重复键、缺 code、非法 JSON、超长等。不得显示原始响应或当作签名错误响应成功。
- `TRANSPORT_INCONCLUSIVE`：无可用响应的 TLS/HTTP/网络失败/超时。保留 reservation，停止。
- `LOCAL_BLOCKED`：授权、输入、输出或预留等本地检查阻断；报告调用数 0，不声称观察 Provider。

不用本次请求来证明反重放/负例安全性质；单次错误响应即使验签通过也不改变 H38 LIVE_BLOCKED。

## 输出与秘密边界

原始响应、签名、账号、proof、client_session、完整请求和密钥永不落盘或输出；禁用 requests/curl 等 debug 回显，不把秘密放命令行。仅 allowlist 脱敏 evidence：schema/task/UTC 时间、实现 hash、gateway 固定标识、attempt_count、HTTP status（可空）、response SHA256（可空）、signature_verified、classification、reason enum、共享 parser 观测范围、synthetic_input=true、payment_success_proven=false、binding_proven=false。

业务 code/sub_code 只能映射到固定枚举：`10000 / 20000 / 40004 / OTHER`；sub_code 为 `INVALID_PARAMETER / CLIENT_SESSION_IS_EMPTY / PAYMENT_PROOF_INVALID / PAYMENT_PROOF_NOT_FOUND / TRADE_NOT_FOUND / TRADE_NO_INVALID / OTHER / ABSENT`，所有未知值只记 OTHER；不输出 msg/sub_msg 或异常正文。hash 是标识而不是独立验签证据。

只在同次响应内产生产品结果和观测结果。无法安全保存 evidence 就报告不完整并停止，不扩大秘密持久化范围。Python 内存清理不宣称可验证擦除。

## Allowed scope / 写入范围与交付

允许新增：`scripts/h41_alipay_signed_error_probe.py`、`tests/test_h41_alipay_signed_error_probe.py`、本包 `REPORT.md` 与脱敏 evidence。可在同一探针文件内实现 H41 tuple 验证和诊断分类；不为这一消费者抽取通用控制平面。

## Exclusions / 明确排除

保护：Trust Core、Alipay adapter、H38/H40 产品/测试/检查器、H39 资料与既有 reservation。BASELINE 漂移先停回 Evaluator。Executor 不改 CURRENT/地图/本合同/验证计划（本轮 R2 治理修订范围见 amendment）。不装依赖，不运行官方脚本或 Skill，不创建线程、不委派、不 commit/push。

## 验收条件

- AC-01：保护 hash 不变；代码仅在上述范围；诊断输入/方法/地址不可替换，默认不读取真实密钥、不联网。
- AC-02：从实际 main 入口用 fake inspect/signer/transport 证明：P0、wrong task、false/quoted true、wrong phase/state/contract、歧义状态块均在密钥/签名/预留/网络前拒绝；中途撤销在预留前拒绝；合法合成执行仅一次 fake 调用。
- AC-03：使用临时合成 RSA 密钥对真实签名 bytes 做正/负测试：签名业务错误、意外成功、篡改 payload、错误公钥、缺签名、重复键、未知 envelope、缺 code、过大响应；禁止全 mock 验签后宣称密码学覆盖。
- AC-04：重定向、超时、已有 reservation、换 output 重试、越界/已有输出、授权二次撤销、密钥异常均有零额外调用证据；超时保持 reservation。不弱化 H40。
- AC-05：嵌套响应、未知 code、错误信息和异常中注入合成秘密标记，检查 stdout/stderr/evidence 无标记；证据严格 allowlist，未知 code 不原样落盘。完整原始 bytes 不持久化。
- AC-06：P0 REPORT 给测试命令/退出码/hash/逐项结果，结论只能 OFFLINE_READY_FOR_REVIEW；P1 单次观测后报告实际分类与 attempt 数。measurement task 完整可审计即可验收；假设是否成立必须单列，不能把 INCONCLUSIVE 写成验签 PASS。

## Stop conditions / 下一步条件

P0 PASS → Evaluator L3 接受代码并单独切换 P1；不再增加新研究包。P1 获 SIGNED_BUSINESS_ERROR → 只关闭响应签名/错误分类这一层，停止本包，重新评估官方安全 fixture 路线。若是权限/参数错误则只描述已观察层级，不保证业务接口 ready。

P1 无签名、意外成功或网络不确定 → STOP 该次实测，按实证原因选择继续/换路线；不补第二次尝试，不开启 production，不要求 Human 先人工付款。没有安全 fixture 路线时保持 H38 未通过并 SWITCH 其他项目瓶颈，不无限循环造本地案例。

## Validation plan

Validation plan file: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml

## Amendments

2026-09-23-a2：按 EVALUATOR_GOVERNANCE_REPAIR.md 与 Human 修复指令，规范化类型、标题、计划引用和原 VP 的执行命令。只修订治理文件和新增本包离线验证入口、证据及报告附注；不改变原假设、AC、产品、保护文件、P0 零预算或 P1 单次上限，不修改中央 workflow。测试入口通过 H41_TEST_PYTHON 指定已有测试运行时，显式设置子进程 PYTHONPATH；该变量不属于产品或 live 开关。本轮由原 Executor 补 L2，旧报告事实保留。Evaluator 仍须独立确认修订并运行 L3 后才能批准 P1，Executor 不代签。

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_scope: sandbox signed-error observation only
  maturity_before: M1 MODELLED
  maturity_after_target_P0: M3 TESTED
  maturity_after_P1: evidence-dependent; no automatic upgrade
  Test: fake transport entry gates and real synthetic RSA response tests
  Evidence: BASELINE.json, REPORT.md, sanitized same-call observation, Evaluator review
  residual_risk: no valid fixture, buyer authenticity, payment binding or production assurance
```
