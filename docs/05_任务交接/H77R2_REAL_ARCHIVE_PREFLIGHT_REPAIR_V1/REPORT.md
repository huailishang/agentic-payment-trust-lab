# H77R2 Executor Report / 精确归档成员与真实资产预检统一提交

Task ID: H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1  
Executor status: SUBMITTED_FOR_REVIEW（待评估者接受）  
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e  
Implementation commit: NONE（合同禁止 Git 提交和推送）  
Map revision: 2026-11-17-r131；Active bottleneck: B-15；Hypothesis: H-77R2  
Validation plan: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/VALIDATION_PLAN.yaml`

## 全局位置与本轮结论

项目要形成授权→可信主体→交易治理→支付→恢复→审计的可独立复核链。A–D 本地阶段关闭、E 本地代表闭合、F 受控外部切片关闭。B-15 仍缺真实来源独立复验。原 H77R 已修 Windows 调用路径，但真实官方 SPIRE Server 179,378,008 字节被任意 150 MiB 提取上限误拒；其历史 L3 失败、发行预算、实际 SPIRE 服务启动 0 均保留。

**本轮首次正式 L2 为 PASS，VP-01～06 共 6/6、强制失败 0；实际官方资产预检 PASS，258 MB 级两成员全部经过同一生产提取器逐流核验，执行者新发行 0。** 这只关闭资产资格前置断点，**不构成 B-15 独立来源最终闭合、也不构成整体验收 PASS**；完整新鲜根/nonce、管理登记、UID 与凭据持有仍归 Evaluator 唯一独立 L3。

## 允许范围内的代码与证据

- `WORKLOAD.py`：仅 `extract_binaries(archive, destination, member_profile)` 函数及 `Collector.collect` 唯一生产调用修改。新逻辑验证官方归档 SHA/长度、目标严格路径、唯一普通成员、精确成员长度、流式 SHA 和实际落地文件 SHA；拒绝任意其他版本、链接、特殊成员、逃逸、重复、大小或摘要漂移。保留原调用后其余支付/发证流程、PID/UID、挑战、验证器与清理保护。
- 生产调用固定使用 `read(self.task / "BINARY_MEMBER_LOCK.json")`；不能用 tiny fixture 代替生产资格输入。
- `TASK_TESTS.py`：原 15 项测试名称及非归档测试 AST 不变，仅两个归档测试和 fixture 显式测试 profile 适配，另增一项包含大小/摘要/归档摘要拒绝的测试。L1 首次新增子测试存在临时目录复用错误，按合同内修复后 16/16 通过；没有放宽安全断言。
- `ASSET_PREFLIGHT.py`：本包新增，受控读取现有 Ubuntu 固定 archive，调用同一个 `WORKLOAD.extract_binaries`；只临时提取、逐文件摘要复核和清理。不运行 SPIRE binary，不启动服务，不使用网络、sudo、子进程、签发或密钥。内部 120 秒 watchdog，原 QUALIFY 外层 180 秒。
- `runtime/`：本包实现辅助脚本，仅局部代码转换及 L1 范围自检，不进入交付接受摘要；从未读取或回显原测试中的敏感样例内容。
- 原 `CHECK/QUALIFY/BOOTSTRAP/AUDIT/RUN/SEAM/CONTRACT/VALIDATION_PLAN/BASELINE/FREEZE/BINARY_MEMBER_LOCK/COPY_MANIFEST` 冻结文件、原产品 `src/`、原 `tests/`、上游 H77/H77R 和共享工具均未修改。路由仅 `CURRENT.md` 从 CONTRACT_FROZEN→EXECUTING，权限位不变。

## L1 自检与冻结边界

- 本地 16 项任务防护测试：`python3 -B .../TASK_TESTS.py` 最终 16/16 PASS，`live_issuer_runs=0`、`new_certificates_generated=0`。
- `QUALIFY.scope()`：`production_scope=extractor_and_fixed_profile_call_only`，`original_task_guards_retained=15`。
- `SEAM_CHECK.py`：真实冻结调用方 argv 联调正例 1、路径拒绝 6、WSL 调度 0；历史凭据正例 VALID、十负例 0 VALID，未借用为本次发行证明。
- `CHECK.py preservation`：受保护 1,886 个文件和冻结材料全部保持。

## 真实官方归档资格（Executor 一次预检）

证据：`evidence/asset_preflight/executor_01/START.json`、`COMMAND.json`、`stdout.log`、`stderr.log`、`RESULT.json`，及 `evidence/l2/EV-02.*`。

- Archive: `spire-1.16.0-linux-amd64-musl.tar.gz`，70,187,551 字节；SHA-256 `7bcf5e167151a1fc58293768462b44e155ba8784214582aefa6adf18c633d1d5`。
- `spire-server`：179,378,008 字节；SHA-256 `459983629a053f81901491425f465848f1894d678a4747e8906f6b4eada392d9`。
- `spire-agent`：78,437,656 字节；SHA-256 `b5a35df17f4491c55e5f37d2e34e35bfa81f4199311c9932cd6b174145ced9ce`。
- 总提取 257,815,664 字节；归档成员 SHA 与落地二进制 SHA 对应全部相等；生产提取器 SHA-256 `5dac3489f14a737e324ba5d51be8b7fc87fff6507ca6b19ea30b0c9236331b58`。
- `/dev/shm/h77r2p_zv09ucw6` 为实际临时 tmpfs；记录 uid=1000、mode=0700，`scratch_removed=true`，10.638 秒；`binary_executions=0`、`spire_service_starts=0`、`new_downloads=0`。
- 此预检证据由冻结 `QUALIFY.py` 读取并检查，真实归档不能被离线 tiny fixture 冒充；执行者预检计数 1/2，未耗第 2 次。

## 正式 L2 与原始证据

首个 `BOOTSTRAP.py --mode executor` 在 Windows 现有 conda `agent` Python 3.12.13 运行，公共 Runner 按冻结计划输出：
`evidence/l2/L2-GATE.json` / `L2-GATE.md`，及 `EV-01`～`EV-06` 每项的 `.meta.json/.stdout.log/.stderr.log`。

| 冻结检查 | 执行者实际观察 | 结果 |
| --- | --- | --- |
| VP-01（AC-01） | 原 1,886 项历史/冻结/共享保护 | PASS |
| VP-02（AC-02/03） | 范围/15 原保护、真实 argv 与路径反例、真实固定 archive 预检 | PASS |
| VP-03（AC-04） | 原历史正例、十负例维持 | PASS（只针对历史） |
| VP-04（AC-05） | 原 28+19+9+74=130 项回归全部通过 | PASS |
| VP-05（AC-06） | 执行者新发行 0；原 H76/H77/H77R 历史次数不覆盖 | PASS（执行者阶段） |
| VP-06（AC-01/07） | 回归后历史与冻结快照保持 | PASS |

新 L2 门禁字段：`result=PASS`、`checks_total=6`、`mandatory_failures=0`；正式 L2 计数 1/2，无 retry L2；正式 L3 0/1，Evaluator 预检 0/1，Evaluator 唯一发行 0/1。累计历史不清零。L2 运行窗口 2026-11-17 01:54:59～01:55:33 UTC（约 34 秒）；本次总主动分钟与外部传输字节 UNKNOWN，不能伪造精确数。

## 验收映射与评估者待办

| AC | 执行者已提供证据 | 评估者独立必须完成 |
| --- | --- | --- |
| AC-01 | 冻结范围 AST、保护 1,886、锁定 SHA | 接受报告和全部提交摘要时核对未漂移 |
| AC-02 | 官方归档与同一提取器真实预检 PASS | 接受后独立一次预检，再一次新根/nonce 真发行 |
| AC-03 | 原管理/UID 守护保持、执行者未签发 | 真实管理原件、进程内核 PID/UID、1001/1002、持有签名 |
| AC-04 | 历史 VALID/十负例零 VALID | 本次新鲜证书和挑战签名独立复算及十负例 |
| AC-05 | 原 130 回归、任务 16 自检、路径正负测试 | 独立 L3 复验原断言 |
| AC-06 | 临时提取后清理 PASS、次数/零服务/零新凭据 | 真实发行后的所有退出路径、进程/私钥/tmpfs 残余独立查验 |
| AC-07 | 首次正式 L2 六项 PASS、REPORT/SUBMISSION/原始证据 | 接受不变快照、唯一正式 L3、逐 AC 二元裁决 |

下一步由 Evaluator 核全部 `SUBMISSION.json` 文件哈希，独立创建 `evidence/ACCEPTED.json`（包含 `SUBMISSION.json` 自身与成功 `l2_gate_path`），再将 `CURRENT.md` 路由改为 READY_FOR_REVIEW/Evaluator。只有 **Evaluator 独立真实资产预检 PASS** 才可触发原 `CHECK.live` 的唯一发行。失败应保全/清理并停止，不得修后重跑。Executor 不触碰评估者 REVIEW/地图或进行最终 PASS 裁决。

## Workspace snapshot / 工作区快照

- Baseline: `61414d05521f7c9fe15cf0299b48b25916f5fa0e`；工作区原本已有 AGENTS、地图、REMOTE 与历史证据相关未提交内容，本轮未暂存、提交、推送或改动这些旧内容。
- Initial evidence: 冻结 `BASELINE.json`、`FREEZE.json`、`COPY_MANIFEST.json`、`evidence/readiness/RESULT.json` 及本轮初始 git status 读取；原 1,886 项保护快照未漂移。
- Final evidence: `evidence/l2/L2-GATE.json` 六组 EV 原始输出、`evidence/asset_preflight/executor_01/RESULT.json`、`ATTEMPT_LEDGER.jsonl`、`evidence/executor_closeout/COST.json` 与 `SUBMISSION.json` 逐文件 SHA；最终工作区未做 Git 提交。
- `SUBMISSION.json` 不包含自身的 SHA；Evaluator 接受时另外计算并纳入 `ACCEPTED.json`。可变 `CURRENT.md` 只记观测 SHA，不当不可变实现输入。

## Changed files / 改动文件

| 范围 | 本轮动作 | 证据 |
| --- | --- | --- |
| `WORKLOAD.py` | 精确成员生产提取函数和唯一锁定 profile 绑定 | `QUALIFY.scope()`、真实 preflight |
| `TASK_TESTS.py` | 仅允许的 fixture、两归档测试和新增负例 | 原 15 项 AST 保留；最终 16/16 |
| `ASSET_PREFLIGHT.py` | 新增无服务真实官方资产预检 | `evidence/asset_preflight/executor_01/RESULT.json` |
| `REPORT.md`、`SUBMISSION.json`、`ATTEMPT_LEDGER.jsonl` | 执行者交接、封存、追加式次数账本 | 本目录 |
| `evidence/l2`、`evidence/asset_preflight`、`evidence/executor_closeout` | 新增正式测试、真实预检和成本记录 | 对应原始日志、JSON |
| `CURRENT.md` | 仅由 Executor 将冻结路由切为 EXECUTING | 权限位不变 |
| `runtime/` | 局部临时代码转换/离线检测工具 | 不进入验收摘要 |

## L2 Task Gate

- Gate result: PASS
- Gate summary: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/L2-GATE.json`
- Validation plan: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/VALIDATION_PLAN.yaml`
- Mandatory failures: 0
- Checks: VP-01～VP-06 = 6/6。只有一次正式 L2、一次 Executor 真实资产预检；L3/发行均未启动。

## EV-01

- AC: AC-01
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-01.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-01.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-01.stderr.log`
- Observed result: 1,886 项原保护与冻结文件保持。

## EV-02

- AC: AC-02 AC-03
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-02.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-02.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-02.stderr.log`
- Observed result: 原范围/路径自检和真实官方资产预检通过，落地提取总 257,815,664 字节并完整清理；无服务、无签发。

## EV-03

- AC: AC-04
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-03.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-03.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-03.stderr.log`
- Observed result: 历史凭据正例 VALID、十负例零 VALID；不冒称新鲜发行。

## EV-04

- AC: AC-05
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-04.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-04.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-04.stderr.log`
- Observed result: 原 28+19+9+74 = 130 项回归通过，原测试文件未改。

## EV-05

- AC: AC-06
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-05.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-05.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-05.stderr.log`
- Observed result: 执行者发行 0、服务 0；历史 H76/H77/H77R 次数不覆盖。

## EV-06

- AC: AC-01 AC-07
- Meta: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-06.meta.json`
- Stdout: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-06.stdout.log`
- Stderr: `docs/05_任务交接/H77R2_REAL_ARCHIVE_PREFLIGHT_REPAIR_V1/evidence/l2/EV-06.stderr.log`
- Observed result: 正式 L2 后原保护和冻结文件再次保持。

## Impact comparison / 项目影响对比

- Measurement evidence: `evidence/asset_preflight/executor_01/RESULT.json`、`evidence/l2/EV-02.stdout.log`、`EV-04.stderr.log`、H77R REVIEW/ARCHIVE_CATALOG 与旧 L3 FAIL。
- Before: H77R 的 150 MiB 任意边界误拒 179,378,008 字节的官方 Server，实际服务 0，来源真实性独立结论 UNKNOWN。
- After: 真实两个已锁定官方成员提取、长度和 SHA 严格相等；首轮 L2 六项通过、原 130 回归和 15 防护保留。
- Delta: 可复核的真实资产资格阻塞已消除；独立来源闭环结果仍 UNKNOWN，修复本身不增加产品成熟度。
- Guardrail result: 1,886 历史保护未漂移；链接/逃逸/重复/长度/哈希拒绝；0 外部下载、0 支付、0 新发行、0 提交推送；预检非敏感 tmpfs 清理已验证。
- Scope caveat: 受信管理员、UID 不等于组织/用户强认证；新根/nonce/实际凭据持有和独立清理由 Evaluator 新鲜 L3 决定；不能称作监管合规或真实资金可用。

## Deviations and unresolved items / 偏差与遗留

- L1 新增拒绝子测试曾有临时目录重复创建的 fixture 错误，已在正式 L2 之前修复；正式 L2 仅一次且 6/6 PASS，没有动原安全案例。
- 在报告编写后的首次 workflow 静态校验发现缺少固定报告栏目，已在本报告补齐；这属于报告格式闭环，不触碰实现、原始 EV 或次数预算。修正后的 `SUBMISSION.json` 需以最终 REPORT SHA 重封存。
- 不运行属于 Evaluator 的真实服务、持有证明、签发或独立清理。评估者仍需接受快照后运行唯一 L3；失败不可修后重跑。

## 项目影响与外部指标

Before：H77R Windows 路径已修复，但官方 Server 的精确成员被任意 150 MiB 上限拒绝，导致真实服务 0、独立来源仍 UNKNOWN。After：本轮真实锁定 archive 的两个官方二进制通过同生产提取器/逐流摘要及 tmpfs 清理，路径联调、原 130、原 15 防护、L2 6/6 未回退。**Delta 仅为资产资格断点修复；B-15 真实身份来源结果仍需独立发行观察，不宣称新产品能力或监管合规。**

外部要求：profile=PCAC-AGENTPAY；PCAC-03/05/06/12/15/20 关联来源、凭据、审计证据；PCAC-07/08/09/10 保留原授权门禁。Before/After 的既有产品 M2 不因本修复升级。风险仍包括受信管理员、UID 并非组织/硬件/用户真实性、无长期轮换/真实撤销/金额支付意愿证明。本轮支付、API、下载、安装、Git commit/push 均 0。
