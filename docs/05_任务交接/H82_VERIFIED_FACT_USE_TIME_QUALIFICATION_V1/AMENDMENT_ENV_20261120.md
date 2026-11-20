# H82 A1：执行环境资格修订（Evaluator 冻结，2026-11-20）

## 来源与权限

负责人在2026-11-20本轮明确指示：「继续评估，可以不用限制验证环境，以conda agent 环境为主，只要功能可实现即可。需要将项目瓶颈向后推进」。

本修订仅修改**本地离线验证的解释器/启动环境限制**。保留 H82 原任务 ID、B-24/H-82-CANDIDATE、原本五项 AC 的行为语义、原15项原件 SHA、正式 L2 最多2次/独立 L3 最多1次、原历史证据和旧支出。不得将本修订解释为授权真实支付、API、私钥、发行服务、安装软件、Git提交/推送或产品代码修改。

## 环境修订：覆盖原合同第3、4、6、7节的环境专属条款

1. **优先**使用已有 Windows Conda `agent`（有可靠且可执行的入口时）；不要为等待 Windows 原生命令通道而停止任务。
2. 若当前工具不能直接执行 Conda `agent`，允许使用**现有 WSL/Linux Python3.11+** 及其已有依赖执行本地只读验证；也可使用已有 WSL→Windows 解释器传输，只要记录实际可执行的解释器身份与父进程来源。本权限明确属于 H82，不靠继承 H81。
3. `CHECK.py` 对平台类型的硬性拒绝应经本修订公开调整为**平台中立**，不动原 5 类行为断言；`VALIDATION_PLAN.yaml` 的命令可以匹配现有可执行解释器。修改前/后 SHA 必须记录在本修订结尾，旧版本仍由 Git 提交和本修订旧 SHA 保留，不能说它从未存在。
4. 实际验证前打印 Python 版本、`sys.executable`、`os.name`、`cryptography` 与 `yaml` 可用性，记录 L2 日志来源。评估者 L3 要独立重跑，不能复用执行者的 L2 输出。
5. 如 WSL 中 Python3 可用且必要测试已通过轻量预检，直接使用当前已存在环境进行 H82；不为追求 Windows 字样新装 Docker/Conda 或新建服务。只有源锁或实质检查失败才停止/交回评估者。

## 冻结语义及不能松动的边界

- 保留全部15个保护对象的原始 SHA；新增/修改的治理脚本、计划不能被宣称是旧冻结版。原旧：CHECK SHA-256=`2ba0801715263b681ba25ac61498c0a2e0b76d8ce5013447302aef43256f38e0`，PLAN SHA-256=`38f509761447365d39f3bf74ca90a9e83ed8ff79d80cca51382a003264ab356e`。
- 继续只测合成事实，不能把模拟身份状态变化当作真实发行方撤销、轮换或支付漏洞。
- 原支付 P3 `BOUND/VERIFIED` 两级准入策略不变；H82 不修产品源码，不重开发过期、Nonce或已存在身份撤销逻辑。
- 不改写 H82 已有的 S0 BLOCKED 报告及之前预算，之后只能新增事实与证据；已发生 0 次正式 L2，不能因修订伪称已通过。
- 本修订不对产品能力签发 PASS，不允许绕过 H82 原 SOURCE_LOCK、五项 VP 或历史 H81 接受快照。
- `CURRENT.md` 的 `authorization_existing_wsl` 可根据本修订从 false 更新至 true；其它外部副作用授权仍 false。

## 项目价值 / 后续门槛

H82 的目的是得到 B-24 的接口使用时点对照，不是继续扩写环境报告。完成同输入对照及独立 L3 后，评估者再决定是否冻结后续**使用时点资格与权威状态输入**能力包。该能力包应以“不合格历史事实不得维持 VERIFIED”为可测试目标，区分 `BOUND` 与 `VERIFIED`、保持付款授权/策略原样，并把真实生产撤销/轮换来源保留 UNKNOWN，直至有来源实证。

## 修订冻结校验

- 原件 SOURCE_LOCK: 仍采用原 `SOURCE_LOCK.json` 的15项 SHA，禁止重算或追认原件漂移。
- 原 H82 任务基线：`61414d05521f7c9fe15cf0299b48b25916f5fa0e`；当前已知 HEAD：`cf5fe507f79a517a2be0a0e8fe1867934748b94d`。此差异不等于15个已锁原件漂移。
- 修订前 `CHECK.py` SHA：`2ba0801715263b681ba25ac61498c0a2e0b76d8ce5013447302aef43256f38e0`。
- 修订前 `VALIDATION_PLAN.yaml` SHA：`38f509761447365d39f3bf74ca90a9e83ed8ff79d80cca51382a003264ab356e`。
- 修订后两个 SHA 与解释器预检结果：见本文末尾冻结回填；在该回填完成前不得开始正式 L2。

## 修订后 SHA 与启动预检（Evaluator 回填并冻结）

- `CHECK.py` 新 SHA-256：`fd20a33968cdadb368bd08b6d7ba0ecb49215efc69a4b3128be7f066077998ea`。唯一功能变化：将原平台硬拦截 `check_native()` 改为要求 Python≥3.11 的 `check_runtime()`；保留 `preservation/inventory/probe/regressions/qualification` 原测量语义。
- `VALIDATION_PLAN.yaml` 仍采用原 SHA-256：`38f509761447365d39f3bf74ca90a9e83ed8ff79d80cca51382a003264ab356e`；原命令 `python -B` 不改。Conda `agent` 下直接用 `python`；WSL无 `python` 命令时，可以在忽略提交的本任务 `evidence/runtime_bin/python` 建立到本机 `python3` 的透明符号链接，并预置 `PATH`，逐项记录 `command -v python` 与 `python -c ...` 的真实解释器信息。不要更改测量用例或伪造 Windows 平台。
- 当前有界环境预检（非正式L2）：WSL `/usr/bin/python3`，Python `3.12.3`，`cryptography=41.0.7`，PyYAML 可导入；一次 `unittest discover -s tests/trusted_execution -p test_credential_context_consumption.py -q` 6/6 PASS。原生 Conda `agent` 文件存在，但本工具不能直接执行其Windows解释器，故现有WSL回退已经满足 A1。
- 新正式 L2 只由下一角色 Executor 执行并保存新 `EV-*` 三件套；本修订没有产生L2或L3。修订权限 `authorization_existing_wsl=true`，提交/推送/支付/安装/API 等仍为 false。
