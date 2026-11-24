# H85 执行者报告 — 单入口按次身份来源消费

## Structural handoff clarification

Task ID: H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1
Baseline HEAD: 69a0512d9b4235b01acec173765a35ab2939f827
Executor status: SUBMITTED_FOR_REVIEW

## Workspace snapshot

本附录由评估者在接受前补齐结构索引，原提交字节保存在 evidence/REPORT.submitted.original.md。既有 H83 产品变动保留，H85 候选六项摘要及 L2 三件套接受前核对一致。

## Changed files

实际实现差异为同旅程调用入口、action_time_authority.py 和本任务候选文件，详见 evidence/EXECUTOR_CANDIDATE_DIFF.patch 与 executor-1/DISPATCH.json。

## Deviations and unresolved items

原提交缺少公共报告结构标记，接受前补索引，原合同、候选和原始证据保持。正式 L3 待独立评估者执行。实际主动耗时 UNKNOWN。

## Impact comparison

Measurement evidence: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/live/OBSERVATIONS.json
Before: 同输入实验关闭为 BOUND / ALLOW / 1。
After: 实验开启、发放有效为 VERIFIED / ALLOW / 1，明确拒绝为 BOUND / ALLOW / 1。
Delta: 一个本地入口完成自身取证、时点与动作关联，实际生产采用 UNKNOWN。
Guardrail result: 原六组 86 项通过，零跳过。
Scope caveat: 受控 SPIRE 发放资格与本地模拟回调，生产可信时钟及用户撤销待证实。

## L2 Task Gate

- Gate result: PASS
- Gate summary: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/L2-GATE.json
- Validation plan: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/VALIDATION_PLAN.yaml

## EV-01

- AC: AC-01, AC-06
- Meta: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-01.meta.json
- Stdout: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-01.stdout.log
- Stderr: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-01.stderr.log
- Result: PASS

## EV-02

- AC: AC-02, AC-03, AC-04, AC-05
- Meta: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-02.meta.json
- Stdout: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-02.stdout.log
- Stderr: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-02.stderr.log
- Result: PASS

## EV-03

- AC: AC-04, AC-05
- Meta: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-03.meta.json
- Stdout: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-03.stdout.log
- Stderr: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-03.stderr.log
- Result: PASS

## EV-04

- AC: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06
- Meta: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-04.meta.json
- Stdout: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-04.stdout.log
- Stderr: docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/evidence/executor-1/EV-04.stderr.log
- Result: PASS

- Task: H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1
- Baseline HEAD: 69a0512d9b4235b01acec173765a35ab2939f827
- Map: 2026-11-24-r143 / B-24
- Executor conclusion: L2 PASS / awaiting Evaluator independent acceptance. No production claim or L3 claim.

## 实现及范围

仅改变约定的 WebShop 集成调用入口 `scripts/validation/webshop/run_same_journey_responsibility.py`，新增同目录 `action_time_authority.py`，及任务内候选文件。入口在原 GovernedPaymentAction、订单、授权版本、请求、付款引用、确认形成后，调用受控来源取得本动作证据，自己生成随机 nonce 并关联业务摘要、读取时钟、调用原验证器及原 WebShop gate。原 P9 默认路径、P2/P3/P4、产品门禁及 H83/H84 冻结原件不变。没有把身份等级升级解释为付款授权升级。H84 现场采集、精确二进制校验、UID 握手与归属清理的复制差异见 candidate/PROVENANCE.md。

## L2 结果及证据

执行命令（已在 Ubuntu WSL2 内）：

```text
/usr/bin/python3 -B docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/CHECK.py gate --role executor
```

正式首次 L2 退出 0，4/4 必选检查 PASS，零失败。六组原测试 42/6/6/6/18/8，86/86 PASS，零跳过。

| AC | 执行者证据 | L2 状态 |
|---|---|---|
| AC-01 | EV-01 / VP-01；冻结保存检查、锁定缓存归档；原 P9 与映射基线复跑、八项相关联、trace VALID；候选摘要 DISPATCH | PASS |
| AC-02 | EV-02 / EV-04；真实 UID 1001 同一隔离 socket；本动作 nonce、签名、证书及原验证器，ISSUED / VERIFIED / ALLOW / 1 | PASS |
| AC-03 | EV-02 来源不可用 UNKNOWN / BOUND；EV-04 删除本次唯一登记后取得明确 PermissionDenied / no identity issued；DENIED / BOUND / ALLOW / 1 | PASS |
| AC-04 | EV-02 跨秒对照不给 Fact；EV-04 两个 action ID 不同，订单、授权、确认、请求、付款引用与业务摘要一致，时点与原资格匹配；动作绑定 VALID | PASS |
| AC-05 | EV-03 六组 86 项零跳过；EV-04 归属清理独立检查退出 0，存活归属进程 0、私有 tmpfs 不存在、公开证据私钥文件 0 | PASS |
| AC-06 | L2-GATE、EV 原始 meta/stdout/stderr、DISPATCH、78 份现场原件摘要复核、完整候选 diff；独立 L3 尚未进行 | L2 PASS / L3 PENDING |

### 实测投影

| 模式 | 可信等级 | 决策 | 模拟回调 |
|---|---|---|---:|
| 离线基线 | BOUND | ALLOW | 1 |
| 离线有效凭据 | VERIFIED | ALLOW | 1 |
| 离线来源不可用 | BOUND | ALLOW | 1 |
| 离线时点不一致 | BOUND | ALLOW | 1 |
| 现场登记有效 | VERIFIED | ALLOW | 1 |
| 现场删除登记后 | BOUND | ALLOW | 1 |

现场正例使用 epoch 1795506210，负例使用 epoch 1795506216；旧叶证书有效至 epoch 1795506808，失去发放资格并不等于证书全局吊销。正例 Fact supplied=true，负例 false。后置探测共 2 次，删除至明确拒绝 6.293496971999957 秒。两个现场动作均由原门禁执行模拟回调；没有改变 BOUND 准入，不能声称撤销身份就拒付。业务摘要 11372f23cdbb8befbf287da7fc798b75f87a4bd8f644cd9c62bf53c26fe11f4f。

## 预算及边界

- 正式 L2 1/2，现场 executor 1/1 已用完；禁止再执行 executor live。Evaluator 0/1，尚未授权进入独立复核状态前不得调用。
- 初始取证 2/3，持有签名 1/1，Server/Agent 各启动 1 次，登记创建/删除各 1 次；删除后探测 2/12，6.2935/90 秒。
- 正式 L2 命令墙钟 173.301 秒，EV-04 现场检查 86.273247 秒（meta UTC 07:42:33.658063 至 07:43:59.931310）；主动开发耗时未独立计量，记 UNKNOWN，不虚构总主动时间。
- 现场 COMMANDS.jsonl 26 条命令记录；初始读取独立 baseline 命令因缺正式 gate reservation 被拒绝，不计 L2 或现场额度；WSL 入口直接运行，先前 wsl.exe 127 和超时均未启动服务。实际首个 L2 全过，不重试。
- 仅本地 loopback 测试凭据、缓存资产；真实支付、外部网络/下载/安装、Git commit/push 为零。生产采用 UNKNOWN。

## 交接入口

- `evidence/executor-1/L2-GATE.json` SHA256 50c9d12785a9e97e7ebfff6e861f42a0eb1b59056bdaf23b9863e022cea1ea82
- `evidence/executor-1/L2-GATE.md`
- `evidence/executor-1/DISPATCH.json` SHA256 8c1fef54eb8afa97ade3e5516018d56c070b41abcdbc4a7fba91478af91a92cc，包含六文件候选摘要。
- `evidence/executor-1/live/OBSERVATIONS.json` SHA256 2b193c84354c8e9f27f5de6cd04f7f4b3941b8cc308a9f2ae4ee775bb52659c1
- `evidence/executor-1/live/PUBLIC_INDEX.json` 与 OBSERVATIONS.raw_sha256：78 份原始证据，执行者重算无不一致。
- `evidence/EXECUTOR_CANDIDATE_DIFF.patch` SHA256 7a94eb0cb58359f4b76f8976f4a7c2e3270667df87eef5e7d126e1cc3a87d051。
- `evidence/executor_LIVE.json` 唯一现场标记仍保留；FORMAL_ACTIVE.json 已不存在。
- `evidence/executor_preflight_01/` 非正式离线预检原件，先于现场候选完成。

## External requirement impact

PCAC-AGENTPAY：PCAC-03/05/06 对应本地按次来源、时点及动作证据；PCAC-09/12/20 保留原守护及证据标准。现阶段只取得受控单入口 L2 证据，目标成熟度由 Evaluator 独立 L3 后确认；真实用户认证、授权撤销、生产授时与采用范围仍 UNKNOWN。

## 下一角色

Evaluator 核对成功 L2 与现存候选摘要，按 EXECUTOR_START.md 独立接受快照、维护 CURRENT 并运行唯一 L3，逐 AC 复算原始签名、动作关联、实际拒绝、时点及清理。执行者不代写 ACCEPTED_CANDIDATE.json，不代行 L3。若 L3 失败，按合同停止，不自动重开现场额度。

大白话：原先测试程序告知付款入口身份可信不可信；本轮让付款入口自己取得本次身份凭据并验证。真实 SPIRE 登记删除后，同一入口确实由 VERIFIED 降为 BOUND，业务订单和付款规则未改。下一步不是继续加同类用例，而是交独立评估者复核。
