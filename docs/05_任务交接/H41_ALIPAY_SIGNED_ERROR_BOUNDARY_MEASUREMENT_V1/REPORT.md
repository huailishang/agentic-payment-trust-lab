# H41 Executor P0 Report

## 2026-09-23 R2 交接附注（Executor 补证，非 Evaluator 裁决）

Task ID: H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1
Executor status: SUBMITTED_FOR_REVIEW
Baseline HEAD: 0b99f3d1f3db180a37bcb8e6512fb7849711ea72
Implementation commit: NONE

依据 R2 修复包及 Human 本轮“修复一下”指令补齐治理表示与执行者证据。下方 R1 历史观察保持原文，不追溯伪造先前 L2。此次中央 runner 实际以 executor 模式运行，7/7 验证项 exit 0，四组专项 70/70、既有独立检查器复跑 7/7；VP-06 另复跑 1 项秘密标记测试，不重复计入 70。所有原 7 项保护 hash 与受审探针/测试/独立检查器 hash 一致。

## Workspace snapshot

工作区继承此前 CURRENT、地图、H38/H39/H40/H41 等未提交改动；本轮不暂存、不提交、不清理其他改动。产品文件仍为下方 R1 已验收版本。CURRENT 中 one_off 在写入补丁时已经存在，保留并与合同对齐；不把来源未确认的改动归为本轮独占产出。

## Changed files

本轮修订 CONTRACT 的表示、VALIDATION_PLAN、REPORT 附注、EVALUATOR_GOVERNANCE_REPAIR 执行记录，新增 GOVERNANCE_CHECK.py 与 evidence/r2_executor_20260923；CURRENT 仅规范化交接指针/说明。未修改产品或中央 workflow。治理入口的作用是明确测试运行时、复核固定 hash/P0 条件、执行原测试及检查器，不读取真实密钥或调用真实接口。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/L2-GATE.json
- Validation plan: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- Mandatory failures: 0

既有系统 Python 3.12.3（含 yaml）运行中央 runner；H41_TEST_PYTHON 指向既有 bundled Python 3.12.14（含 cryptography），入口为测试子进程显式设置 PYTHONPATH。证据目录创建最初被沙箱拒绝（exit 1，测试尚未启动），获准后执行同一命令成功；未安装依赖。

命令：python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923 --mode executor

## EV-01

- AC: AC-01
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-01.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-01.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-01.stderr.log

## EV-02

- AC: AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-02.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-02.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-02.stderr.log

## EV-03

- AC: AC-01, AC-04
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-03.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-03.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-03.stderr.log

## EV-04

- AC: AC-03
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-04.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-04.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-04.stderr.log

## EV-05

- AC: AC-03
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-05.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-05.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-05.stderr.log

## EV-06

- AC: AC-05, AC-06
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-06.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-06.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-06.stderr.log

## EV-07

- AC: AC-02, AC-03, AC-04, AC-05, AC-06
- Meta: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-07.meta.json
- Stdout: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-07.stdout.log
- Stderr: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/EV-07.stderr.log

## Impact comparison

- Measurement evidence: docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/evidence/r2_executor_20260923/L2-GATE.json
- Before: 原合同/计划结构不兼容，无正式 L2
- After: 原七项 VP 可运行，有真实 L2 PASS
- Delta: 治理可执行性修复，Provider 实证仍 NOT_MEASURED
- Guardrail result: P0 零授权、保护 hash 一致、真实请求/密钥读取均为 0
- Scope caveat: 不构成独立 L3 或 P1 批准；B-06 未移动，H38 仍 LIVE_BLOCKED

## Deviations and unresolved items

Evaluator 仍须独立接受 amendment a2、审计改动范围、运行 L3 并记录最终 P0 裁决；原执行者不能代签。CURRENT 保持 READY_FOR_REVIEW / Evaluator，授权不变。本轮未新增 RV-EV 或 L3 记录。evidence 包含中央 runner 生成的本地路径与日志，尚未提交；将来提交时必须经过安全门禁。
PCAC-AGENTPAY / PCAC-06、09、12、20 的能力成熟度保持原 M3 离线测试边界，本轮只补齐可追溯门禁证据，不声明真实 Provider 或合规提升。

## 2026-09-23 R1 修复交回（当前结果）

Result: **OFFLINE_READY_FOR_REVIEW**。Phase: **P0_OFFLINE_ONLY**。R1 已修复并由 Executor 重跑既有独立检查器验证；Evaluator 的最终验收仍待进行。Hypothesis: NOT_MEASURED，Project impact: NOT_APPLICABLE。下方 2026-09-22 内容为首次交付历史，旧 hash、测试数及 PASS 仅对应旧版本。

全局位置依据 CURRENT 与地图 r62：A–D 完成、E 本地闭环、F 当前；B-06 仍缺支付宝实际响应证据。H41 本轮只修复错误响应证据丢失；AP2 扩展与横向攻击 WATCH 不能替代该 Provider 测量。P0 验收后由 Evaluator 决定是否切换 P1；Executor 不自行推进。

### 修复与边界

transport 捕获非 3xx HTTPError，将其作为响应资源按原 1,000,001 字节上限读取，进入原始 bytes 验签/分类链并关闭资源。HTTP 400/500 的可用响应保留 status 和 SHA-256；状态码本身不构成验签证据。3xx 关闭资源后拒绝，不读取其签名响应体、不跟随；读取失败/超时仍 TRANSPORT_INCONCLUSIVE，无完整响应时 status/digest 保持空，预留保留且禁止换名重试。

新增 9 项实际 main → transport 测试，仅替换 urllib opener 和合成密钥输入，真实签名与分类不 mock：签名 400、签名 500、无签名、篡改、意外成功、超长、读取失败、读取超时、含签名体的 302。逐项检查单次 fake attempt、资源关闭、读取上限、预留保留、换名重试被阻断、allowlist 和秘密标记不泄漏。

仅修改 H41 探针、H41 测试、本报告，共 3 文件；保护 hash 开始与结束均 7/7 相同，HEAD 未变。EVALUATOR_CHECK.py 未修改，SHA-256 为 `46090bf1cc42b885bf26785adfb95e7be2167c83093680ed389e010d0242f2ca`。CURRENT、地图、合同、计划和 REVIEW 保持原状。真实密钥读取、真实 HTTP attempt、付款、造单、commit/push 均为 0；未安装依赖或创建真实 reservation。

### 本轮验证

使用既有 Codex bundled Python 3.12.14；下表 python 代表该解释器，产品 import 设置 PYTHONPATH=src。初次调用 PATH 中 Python 3.12.3 因缺 cryptography 导入失败（exit 1），随后切换既有运行时。修复中首次运行还发现上下文管理器绑定回归，已修复并重跑 H41 及独立检查；最终结果如下，不以中间失败版本交付。

| 检查 | 命令 | 最终结果 / exit |
|---|---|---|
| VP-01 | git rev-parse HEAD；Get-FileHash 对比 BASELINE | HEAD 一致；7/7 保护 hash 一致 |
| VP-02 | python -m unittest discover -s tests -p test_h41_alipay_signed_error_probe.py -v | 28/28；0 |
| VP-03 | python -m unittest discover -s tests -p test_h38_authorization_gate.py -v | 12/12；0 |
| VP-04 | python -m unittest discover -s tests -p test_alipay_agent_pay_sandbox.py -v | 16/16；0 |
| VP-05 | python -m unittest discover -s docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks -p 'test_*.py' -v | 14/14；0 |
| VP-06 | python scripts/h41_alipay_signed_error_probe.py | DRY_RUN key_reads=0 attempts=0；0 |
| VP-06 | git diff --check；新增文件 whitespace 检查 | 无 whitespace error |
| VP-07 辅助复跑 | python docs/05_任务交接/H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1/EVALUATOR_CHECK.py | 7/7；0；不替代 Evaluator L3 签收 |

共 70 项专项通过，另有 7/7 既有独立检查通过。三个原反例已满足期望：signed_400/500 为 SIGNED_BUSINESS_ERROR，unsigned_400 为 UNVERIFIED_RESPONSE，均保留 status/digest；既有正常 200、篡改、错误 phase 和中途撤销均通过。全仓测试未重跑，继承的 Windows WebShop 路径失败仍未处理。

| AC | Executor 修复后结果 |
|---|---|
| AC-01 | PASS：保护文件不变，仅合同内 3 文件；默认 dry-run 零密钥/网络 |
| AC-02 | PASS：原 main 授权变体、二次撤销和独立检查保持通过 |
| AC-03 | PASS：真实合成 RSA；400/500 响应进入原验签链，篡改/无签名/超长仍拒绝 |
| AC-04 | PASS：资源关闭、读取失败/超时、3xx 不跟随、预留与零额外调用均有测试 |
| AC-05 | PASS：响应/异常秘密标记未出现在 stdout/stderr/evidence，字段集合严格 allowlist |
| AC-06 | P0 ready：命令、最终 hash、退出码已记录；P1 假设未测量 |

### 当前实现 SHA-256

| 文件 | SHA-256 |
|---|---|
| scripts/h41_alipay_signed_error_probe.py | 09733850937776f5d286454504e01d54bdfebd0b4915e3189104b68583a19b69 |
| tests/test_h41_alipay_signed_error_probe.py | b2d8bb9f546a2f421d6a895e5b86e57c2efba0193c60619b1a8061aa711323e5 |

### external_requirement_impact 与交回

profile=PCAC-AGENTPAY；关联 PCAC-06、09、12、20；applicability=CORE。成熟度 before 为已有离线测试但 R1 导致独立验收暂缓；after 为 M3 TESTED（Executor 修复及复跑证据，Evaluator 签收待定），不升级为 Provider 实测或合规结论。Test 为上述 70 项专项及 7 项独立检查；Evidence 为 BASELINE、本报告和未修改的独立检查器。残余风险：真实响应、公钥来源、买家真实性、支付成功和交易绑定均未证明。

依据冻结合同“P0 完成报告 OFFLINE_READY_FOR_REVIEW，交 Evaluator L3，Executor 不自行进入 P1”，本轮交回并停止；CURRENT 保持 CHANGES_REQUIRED，等待 Evaluator 独立验收及状态更新。H38 保持 PARTIAL / LIVE_BLOCKED。

## 首次交付历史（2026-09-22）

Date: 2026-09-22
Task: H41_ALIPAY_SIGNED_ERROR_BOUNDARY_MEASUREMENT_V1
Result: **OFFLINE_READY_FOR_REVIEW**
Phase: P0_OFFLINE_ONLY
Project impact: NOT_APPLICABLE (measurement preparation)
Hypothesis result: NOT_MEASURED; no provider response obtained

## 全局位置与执行范围

项目目标是可信授权、支付动作与证据连续。地图 r61：A–D 完成，E 本地代表性闭环，F 当前；B-06 的第一缺口仍为支付宝实际响应证据。H41 只准备一次 HTTPS 合成诊断测量，不闭合 H38 的支付成功、买家真实性或交易绑定。继续扩 H40/AP2 或横向攻击 WATCH 不能替代这项外部证据。

本轮读取 CURRENT、EXECUTOR_START、EVALUATOR_DECISION、CONTRACT、VALIDATION_PLAN、BASELINE 及 PCAC 指标映射。HEAD 与 BASELINE 的 `0b99f3d1f3db180a37bcb8e6512fb7849711ea72` 一致；开始前及结束后 7/7 保护 hash 一致。继承工作区原有未提交修改，未改 CURRENT、地图、合同、计划或既有 H38/H40 实现与检查器。

新增文件仅为本报告、`scripts/h41_alipay_signed_error_probe.py`、`tests/test_h41_alipay_signed_error_probe.py`。本轮真实密钥读取=0、真实 HTTP attempts=0、造单/付款/履约/callback=0；未安装依赖、运行官方脚本、委派、提交或推送。测试生成的 RSA 私钥仅在内存，fake evidence/reservation 仅在测试临时目录；未创建本任务真实 reservation 或冒充 live evidence。

## 实现与证据边界

默认 dry-run 不检查真实密钥、不签名、不联网。execute 固定读取 ROOT/CURRENT.md，复用 H40 的单状态块 parser，并校验 H41 精确 tuple、phase 及 literal true。第一次检查先于密钥/签名，第二次紧接独占 reservation 创建之前。APPID 从 AIPAY_APP_ID 读取；密钥仅接受显式本地路径。trade/proof 为冻结的 ASCII 零占位，无 client_session；不读取 H38 fixture。

请求固定 HTTPS POST、RSA2、30 秒超时；urllib 默认 TLS 检查，无重定向或自动重试。读取上限 1,000,001 字节，超过 1,000,000 分类 UNVERIFIED_RESPONSE。输出独占打开与固定 H41_DIAGNOSTIC.reserved 防止换名重试；超时、重定向或写证据失败均保留 reservation。

复用 signed_response_parts 取得原始签名字节，以真实 RSA 验签后才分类业务字段。未知 code/sub_code 转 OTHER；缺 code 虽可 signature_verified=true，classification 仍为 UNVERIFIED_RESPONSE。无第二 observer，evidence 明确标注 SAME_PROCESS_SHARED_H38_PARSER_NO_INDEPENDENT_OBSERVER，不声称独立验签。所有结果保持 payment_success_proven=false、binding_proven=false。

本地前置失败只输出固定阻断文本；二次授权/预留失败若已打开输出，可记录 attempt_count=0 的 LOCAL_BLOCKED。网络之后证据写入失败输出固定 EVIDENCE_INCOMPLETE 提示，无法保证完整 evidence，必须保留 reservation 并停止，不因缺文件重跑。实现 hash 用于识别文件，不是独立验签或代码批准证明；P1 前的 exact-hash 批准仍由 Evaluator 执行。

## 验收映射

| AC | P0 Executor 结果 | 证据 |
|---|---|---|
| AC-01 | PASS | HEAD/7 hashes 前后相同；固定输入；default_dry_run、cli_cannot_override_frozen_inputs；实际 CLI dry-run |
| AC-02 | PASS | actual_current_p0_blocked；gate_mutations_before_all_side_effects；second_authorization_revocation；successful_fake_attempt_and_fixed_request；fake inspect/signer/transport 调用断言 |
| AC-03 | PASS | 真实 2048-bit 合成 RSA；精确含空白 JSON bytes 正例、篡改/错公钥/缺签名/重复键/未知 envelope/缺 code/非法 JSON/超大响应；crypto_negatives_through_main 与 unexpected_success_stops |
| AC-04 | PASS | timeout_reservation_retained、redirect_main_no_retry、real_transport_redirect_and_read_limit、existing_reservation_without_output、换名重试、local_output_rejections、reservation_race_rejects_before_transport、key_and_signer_exceptions_are_quiet；H38 回归通过 |
| AC-05 | PASS | 合成秘密注入嵌套 payload、code/sub_code、msg/sub_msg、异常及 CLI；stdout/stderr/临时 evidence 无标记；字段集合严格检查；未知 code OTHER；未持久化原始 bytes |
| AC-06 | P0 ready | 本报告包含命令、退出码、hash、边界；P1 未执行，假设未测量 |

## 可复现命令与结果

仓库根目录执行。使用既有 Python 3.12 / cryptography 42.0.5，未安装依赖。含产品 import 的命令设置 `PYTHONPATH=src`。

| VP | 命令 | 退出码 / 结果 |
|---|---|---|
| VP-01 | `git rev-parse HEAD`；PowerShell Get-FileHash 对比 BASELINE.protected_files | 0；HEAD 一致、7/7 hashes 一致 |
| VP-02 | `python -m unittest discover -s tests -p test_h41_alipay_signed_error_probe.py -v` | 0；19 tests OK，含多个 subTest 变体 |
| VP-03 | `python -m unittest discover -s tests -p test_h38_authorization_gate.py -v` | 0；12 tests OK（不把历史“42 项专项”误写成本轮 unittest 数） |
| VP-04 | `python -m unittest discover -s tests -p test_alipay_agent_pay_sandbox.py -v` | 0；16 tests OK |
| VP-05 | `python -m unittest discover -s docs/05_任务交接/H38_ALIPAY_AGENT_PAY_SANDBOX_FIRST_EXTERNAL_SLICE_V1/evaluator_checks -p 'test_*.py' -v` | 0；14 tests OK |
| VP-06 | `python scripts/h41_alipay_signed_error_probe.py` | 0；DRY_RUN，key_reads=0、attempts=0 |
| VP-06 | `git diff --check` | 0；仅既有 LF/CRLF 提示 |
| VP-06 | `git diff --no-index --check -- /dev/null scripts/h41_alipay_signed_error_probe.py`；对 tests 文件同命令 | 1（新增文件 diff）；无 whitespace error，只有 LF/CRLF 提示 |
| VP-07 | Evaluator independent L3 | PENDING，未由 Executor 自行代判 |

总计本轮最终 61 tests OK；不扩大到全量回归，继承的 Windows WebShop 路径失败仍未处理，不声明全仓全绿。测试临时文件不作为真实 Provider 证据保存。

## 实现 SHA-256

| 文件 | SHA-256 |
|---|---|
| scripts/h41_alipay_signed_error_probe.py | 784931d6b9d48987079db099f34f35096c4479116e57faae77e496c14da125eb |
| tests/test_h41_alipay_signed_error_probe.py | 2ebba3671ebd3e9a6ee3dd7d492610f25533f565b66817c45be0b74efc5d861d |

## External requirement impact

```yaml
external_requirement_impact:
  profile: PCAC-AGENTPAY
  requirement_ids: [PCAC-06, PCAC-09, PCAC-12, PCAC-20]
  applicability: CORE
  maturity_scope: H41 offline diagnostic authorization and signed-error classification only
  maturity_before: M1 MODELLED
  maturity_after: M3 TESTED (Executor evidence; independent L3 pending)
  Test: 19 H41 tests plus 42 inherited regression tests
  Evidence: BASELINE.json and REPORT.md; no live evidence
  residual_risk: provider response unmeasured; public-key provenance, buyer authenticity, payment success and binding unproven
```

## 交回条件

P0 完成并停止于 OFFLINE_READY_FOR_REVIEW。Evaluator 独立 L3 接受并记录批准 hash、切换 CURRENT 精确 P1 tuple 后才允许一次 live attempt；当前不执行。P1 成为 SIGNED_BUSINESS_ERROR 也只证明配置公钥下的该响应验签；意外成功、无签名或网络不确定均停止且不重试。H38 维持 PARTIAL / LIVE_BLOCKED。
