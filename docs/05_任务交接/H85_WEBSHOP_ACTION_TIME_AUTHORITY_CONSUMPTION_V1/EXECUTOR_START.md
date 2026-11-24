# H85 执行与复核入口

## 进入条件

本包在 `CONTRACT_FROZEN / Executor` 待交接。执行者核对 `FREEZE.json`、原工作区和开支约束，然后仅将自己的活动路由推进到 `EXECUTING / Executor`。评估者接受未变的成功 L2 快照后才推进到 `READY_FOR_REVIEW / Evaluator`。本包使用现有 WSL、缓存 SPIRE 资产和本地模拟回调。

## 执行顺序

1. 复用 `evidence/BASELINE_PROBE.py` 的桥接输入与已签收 P9 数据，保留固定业务快照和原 H83 门禁。允许修改合同列出的两个 WebShop 调用侧文件。新增候选编排入口 `CANDIDATE.py`，仅在确有需要时使用 `candidate/` 存放作用域内的支持脚本。此编排入口不得承担当次时钟或替消费者选择 Fact。
2. 先实跑本地假来源条件与原守护。只有入口可以独立取得来源响应、证据从属于该动作且原回归无退化时进入正式门禁。使用以下入口运行冻结计划，由它预留当次正式门禁额度并调用公共 runner。执行者与评估者分别使用自己的命令。

```text
wsl.exe -d Ubuntu -- /usr/bin/python3 -B docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/CHECK.py gate --role executor
wsl.exe -d Ubuntu -- /usr/bin/python3 -B docs/05_任务交接/H85_WEBSHOP_ACTION_TIME_AUTHORITY_CONSUMPTION_V1/CHECK.py gate --role evaluator
```

3. VP-04 核对同次 VP-01 至 VP-03 的原始退出码和前置收据，并重新确认角色、候选摘要及资产。全部通过才创建该角色的唯一现场标记，再启动候选。标记一经创建即计费，失败也保留原件。中断后若仍有活动登记，优先核对原运行及清理，不能自动重放或删除登记以续用额度。
4. 执行者提交原始证据、差异、账本和候选摘要清单，成功 L2 和失败尝试均保留。评估者核对同一成功 L2 的 `DISPATCH.json`、候选现存摘要和 L2 三件套，独立写入 `evidence/ACCEPTED_CANDIDATE.json`，字段 `candidate_sha256` 等于接受的 L2 快照，另记接受的 L2 路径及其摘要。然后运行唯一 L3 并按合同逐 AC 复算。

## 候选入口与证据

`CANDIDATE.py offline|live --role executor|evaluator --out <当次运行目录>`。候选将 `OBSERVATIONS.json` 及公开原始证据写入传入的独占目录。offline 只使用离线素材，禁止打开来源服务、启动 SPIRE、切换真实 UID 或发行凭据。live 才能调用隔离来源，须复用 H84 已验证的成员摘要、归属检查、超时和 finally 清理。候选阶段退出非零会保留全部产物并使对应 VP 失败。不得改动验收检查器或模板以让结果通过。

离线文件只包含四个顶层对象 `baseline`、`issued`、`unavailable`、`time_mismatch`。每个含 `assurance / decision / callback_count / business_digest`。baseline 另含 `trace_validation`，unavailable 另含 `source_status`（UNKNOWN），time_mismatch 另含 `fact_supplied`（false）。business_digest 从固定订单、授权、确认与既定输入计算。两角色原回归分别为 42/6/6/6/18/8。

现场文件的 `before` 与 `after` 均记录 `assurance / decision / callback_count / business_digest / action_id / holder_uid / socket_ref / source_status / fact_supplied / use_at_epoch`，before 另含 `observed_at_epoch`。顶层记录 `run_role / network_scope / post_delete_probes / delete_to_denial_monotonic_seconds / registrations_created / registrations_deleted / server_starts / agent_starts / initial_fetch_attempts / holder_signatures / old_leaf_not_after_epoch / cleanup / raw_sha256`。网络范围为 `loopback`，cleanup 为 `owned_processes_alive / private_tmpfs_exists / public_private_key_files`。raw_sha256 引用当次输出目录内公开原始来源命令/响应、实际 UID 和 socket 关联、根和叶、签名/nonce、公有动作引用、订单/授权/确认绑定、调用侧时钟顺序、模拟回调和清理记录。公开索引中的产物必须足够支撑独立复算。验收脚本检验投影与摘要，评估者仍须用原始记录逐项复算，尤其是实际拒绝、签名链、同次动作、归属及清理。

任何预检查失败，记录第一个失败点和已经消耗的额度。若不需要改变合同，且第一次 L2 尚未登记现场，可在剩余额度内修复并直接使用第二次 L2。其余情况按合同停止。
