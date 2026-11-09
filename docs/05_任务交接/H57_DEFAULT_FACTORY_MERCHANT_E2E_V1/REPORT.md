# H57 执行者报告：商城原生工厂接线与证据完整性阻塞

Task ID: H57_DEFAULT_FACTORY_MERCHANT_E2E_V1
Task kind: capability_experiment
Baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Executor status: EXECUTING / FUNCTIONAL_L1_OBSERVED / EVIDENCE_GATE_BLOCKED
Disposition: NOT SUBMITTED FOR REVIEW; no evaluator L3; no Git commit/push

## 全局位置和实际作用

A–D 本地可信支付链已具代表证据，E 仍限本地，F 是外部商城/Provider 研究；B-17 当前第一瓶颈是**正常应用配置→原生服务工厂→既有授权控制→真实商城生命周期**的可执行连接。H51 通过测试替换工厂才成功，原生默认入口完成仍失败；H53R 方法级授权不等于商城实际接入。本轮仅在冻结范围内接通默认工厂，不重启 H56 安全支线，也不扩协议。

## 修改范围与结果

- `merchant/dependencies.py`：仅给 `get_checkout_service` 原函数体增加 `execution_control=getattr(request.app.state, "execution_control", None)`；参数签名、请求级 DB 会话依赖及顶层其他对象不变。
- `merchant/guarded_app.py`：新增 `create_app(execution_control=None)`，保留 `server.app` 原路由和原 `config.lifespan`，原生 DB 初始化后初始化控制；无配置拒绝完成。
- `HTTP_RUNTIME.py`：只用原生 `httpx.ASGITransport`、正式 RFC9421 验签路径、合成离线公开 profile/DNS、独立持久 SQLite 假 PSP；未使用 FastAPI `dependency_overrides`。新增请求预留采用 `HTTP_ATTEMPTS_AFTER_L1.jsonl`，不修改旧受损账本。
- `RUN_JOURNEY.py`：六场景真实 HTTP/SQLite/假 PSP，逐请求及逐场景 JSON、独立签名校验数据、M06 真正第二 Python 进程的 stdout/stderr/退出状态、不同 PID、持久状态查询；每次生成新 `evidence/<role>/run_NNNN` 目录。失败的 `run_0001` 保留，成功的是 `run_0002`。
- 其余36个商家源文件、原始 SDK、H56、旧任务、冻结合同、测试、Checker 未变；本轮 Git 写操作=0，网络/真实支付/Provider/新增安装=0。

## 六条完整原生商城旅程：本地观测校验 6/6

证据：`evidence/executor/run_0002/observations.json`；每条另有对应 `M0*.json`，`evidence/executor/LATEST.json` 指向 `run_0002`。

| Case | 本轮真实 HTTP 结果 | 独立 PSP charge | 订单 / 库存 |
| --- | --- | ---: | --- |
| M01_NORMAL_REPLAY_QUERY | POST创建201；完成200；同键重放200；GET checkout200；GET order200 | 1 | 1单；5→4 |
| M02_CHANGED_AFTER_CONFIRM | 创建201；改数量 PUT200；旧确认完成409/H50_SNAPSHOT_MISMATCH | 0 | 0单；5 |
| M03_MISSING_CONFIRMATION | 创建201；缺确认完成403/H50_CONFIRMATION_MISSING | 0 | 0单；5 |
| M04_INVALID_AUTHORIZATION | 创建201；HTTP签名有效、授权令牌篡改完成403/H53_AUTHORIZATION_DENIED | 0 | 0单；5 |
| M05_UNCONFIGURED_APP | 创建201；无控制完成409/H50_EXECUTION_DENIED | 0 | 0单；5 |
| M06_ORDER_FAILURE_RESTART_QUERY | 创建201；扣款后订单故障500；不同 OS PID 重启GET200；新键重试409；恢复QUERY/SUCCEEDED | 1（累计） | 0单；5 |

完整一轮18个 ASGI HTTP 请求，`RUN_JOURNEY.py --role executor` exit=0；随后任务冻结的 `CHECK.validate(observations)` 对六例顺序、原始 HTTP 方法/签名头/正文、订单与库存、授权哈希/平台公开根、模拟 PSP 次数、两进程恢复和18次请求全部通过。签发只使用创建 HTTP 响应，未从 DB 补造客户端拿不到的授权字段；恢复只查状态，不自动补单。

## 审计日志完整性：阻断正式 L2

取证文件：`evidence/executor/LEDGER_INTEGRITY_FINDING.json`。

- 原 L1 `HTTP_ATTEMPTS.jsonl`：原始 SHA-256=`e0950438ff219c16ee539de623405951b6efb21c837bf2e244b679f2a8f9208f`。包含25条实际预留记录，但物理换行符为0、以字面量反斜杠+n拼接；仅2个不同请求 ID，其中 `h57-2` 被使用24次。字节原样保留，没有伪造/重新编号。
- 新追加的 `HTTP_ATTEMPTS_AFTER_L1.jsonl`：32条预留，32个不同 ID；失败证据波次 `run_0001` 14条、通过波次 `run_0002` 18条，均未覆盖。连同旧日志共57条已记录请求，仍在 Executor 160 次上限内，但当前**不能直接满足冻结 Checker 指定的唯一追加账本路径与唯一 ID 要求**。
- `CHECK.py materials executor` 已独立执行，exit=1：`json.decoder.JSONDecodeError: Extra data: line 1 column 135`，在读取历史 `HTTP_ATTEMPTS.jsonl` 时失败，未进入后续结果/预算断言。
- 这个缺陷属于本轮执行记录格式错误，不是商城付款被重复执行的实证。原请求 IDs 不能事后替换成新的 ID 伪装原始预留，也不能删掉旧失败以让判别器通过。
- 需 Evaluator 正式冻结**证据专属**修复方式：保留旧 raw 的精确哈希和25次计数，允许独立追加的新 HTTP 账本作为当前规范材料，修订判别器/核算规则以包含所有57次历史预算，不能修改商家业务、放宽验签或扩权限。

## 按 AC 和 VP 交付状态

| 冻结判据 | 执行者状态 | 可复核事实 |
| --- | --- | --- |
| AC-01 / VP-01/02/07 | L1 实现及静态校验通过 | 1680保护文件、52冻结文件；36只读商家文件；工厂唯一原函数体改动 |
| AC-02 / VP-03 | 完整本地观测通过，正式 L2 待补 | M01创建/付款/重放/查询以及证据的独立对象绑定 |
| AC-03 / VP-03 | 完整本地观测通过，正式 L2 待补 | M02–M05各拒绝与零 side effects |
| AC-04 / VP-03 | 完整本地观测通过，正式 L2 待补 | M06不同 PID，新进程查到已付、再付被拒 |
| AC-05 / VP-05/06 | 回归通过，正式 L2 待补 | 25个 AP2 单测 + 6个反例自测全部 exit=0 |
| VP-04 | BLOCKED | 旧请求日志既非合法 JSONL又有重复 ID；材料检查 exit=1 |

没有创建通过分类的 `RESULT.json`，没有把非正式验证冒充 L2/L3。正式 `l2_executor_01` 和 `_02` 均未消费，当前仍 `CONTRACT_FROZEN / Executor`，不提交 `SUBMITTED_FOR_REVIEW`。

## 成本、影响和下一动作

- 已知 ASGI 预留57次（旧25 + 新32；本轮正式 6 例18）；完整波次18≤28，累计57≤160。完整波次模拟付款2次（M01和M06各1），M06查询1次，真实支付0。
- 人工活跃分钟缺少连续实时计量，不能将不可靠估算写作精确用时；正式 L2 尝试数0/2。
- Before：原生默认工厂正常完成未接入安全控制；After：六类商城本地完整 HTTP 旅程均可运行并通过冻结的观测语义校验。B-17 接线子断点有进展，但证据提交门禁仍阻塞，不能升级为正式项目 PASS。
- 下一步归 Evaluator 裁定最小 evidence-only 合同修订或 STOP；Executor 不得自行改写冻结 `CHECK.py` / `VALIDATION_PLAN.yaml` 或历史 HTTP 记录来消除失败。若准许更正证据契约，Executor 可继续完成预算记录、RESULT、正式完整 L2，之后交独立 L3。

## 外部要求及剩余风险

profile=PCAC-AGENTPAY。PCAC-07/09（授权消费）达到本地原生入口观察；PCAC-08（主体/签名）仍只有合成根和离线公开 profile；PCAC-12/20（证据审计）因账本不规范而阻塞；PCAC-18（恢复）仅证明查询和不重复扣款，不是自动补单。真实商户、真实授权身份、真实支付服务、标准 CheckoutMandate 完整互通、客户需求、监管合规与生产就绪均未验证。H56仍为未执行的安全支线，不更改其结论或合同。
