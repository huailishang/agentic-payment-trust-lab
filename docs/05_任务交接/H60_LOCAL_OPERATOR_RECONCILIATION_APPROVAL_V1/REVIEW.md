# H60 评估者复核：来源隔离反例成立，拒收并转最小修复

Task ID: H60_LOCAL_OPERATOR_RECONCILIATION_APPROVAL_V1
Task kind: capability_experiment
Reviewed baseline HEAD: 7831d232530c91825bb507a2a6d95b1de6a02c3b
Review date: 2026-11-04
Review boundary: PRE_ACCEPTANCE / NOT_SUBMITTED; no accepted snapshot and no formal L3

## 全局位置

项目最终证明高风险智能体交易的授权、绑定、副作用和恢复证据链。地图 r97：A–D 本地代表完成，E 本地受控闭环，F 当前。B-17 是原 M06 已付款无订单的处置责任链；Human 在 H59 已选择先建设人工批准入口。H60 的能力实验仅登记处置批准，不执行补单或退款。它比 H56 非标准披露支线更接近已观察业务断点，比直接自动补单少副作用；延期的真实 PSP/身份不是本地修复的前提。

## 签收资格与独立证据

原 REPORT 明确不声称正式签收；CURRENT 仍 EXECUTING/Executor。中央结构校验在本轮开始时仍报告执行者状态及 L2 结果/摘要不合格式；不把格式问题改写成已有正式 L2。不接受原包，不启动正式 L3，不补造通过门禁。

所有新证据位于 `evidence/independent_review_20261104/`：

- `AUDIT.py`、`RESULT.json`：独立运行父 CHECK 的 baseline、scope、两角色 materials、selftest，五项退出码均 0；原提交 307 文件复算前后逐字节相同，原两库 hash 不变。两个 materials 只确认既有修复版材料结构，不使其成为独立 L3。
- `HARNESS_V3.diff`：独立比对原冻结与 v3，仅有 closing 导入、嵌套路径定位、关闭连接后摘要、串行子进程相邻时钟允许相等四处差异。
- `C12_PURE_FIXTURE.json`：完全不调用候选，commit 后连接仍开时摘要 `12dd20fb…`，close 后 `76865244…`，独立复现夹具自身的 WAL 检查点漂移。这个历史失败不归因于候选写来源。
- C17 源码使用同步 subprocess.run，返回后才启动第二进程；非递减时钟加三个 PID/退出码保留原实际先后语义。允许相邻采样同 tick 的改动可在新修复包重冻结，不能追溯改变旧计划。
- `PROCESS_ALIAS_PROBE.py`、`PROCESS_ALIAS_RESULT.json`：R05/R06 在一次性副本上为新账本建立交易库/PSP 库的硬链接，候选子进程正常退出且不抛业务拒绝；来源文件新增 approvals、approval_events 两表，hash 实际改变。路径解析不同但 os.path.samefile 为真。交易库 `12dd20fb…→a0b59851…`，PSP 库 `43c40417…→b4756d2d…`。无需 approve 调用，构造器已可写来源，直接违反冻结 AC-01。
- 首批 R03/R04 的进程内读取受 WAL/未关闭连接影响：其中 R03 当时主文件 hash 未变，不把它单独声称为落盘写入证据。R05/R06 的新进程退出后观察消除了这个歧义。

硬链接由受信本地配置/文件准备层建立，不证明远程请求可创建硬链接或真实支付受攻击。但合同明定只有独立新账本可写、不得向任一来源建表；该失败属于已有隔离要求，未新增生产认证或动态文件替换义务。

## AC 逐项裁决

| AC | 裁决 | 依据 |
|---|---|---|
| AC-01 来源/旧能力只读 | 不通过 | 旧保护和单模块范围通过，但 R05/R06 通过账本硬链接写入来源副本；路径字符串不同不足以证明文件隔离 |
| AC-02 显式批准与交易绑定 | 不通过（完整复核未完成） | 正常独立控制可批准，既有 20 例材料可解析；未正式签收/独立全量验证，不凭自重放接受整个 AC |
| AC-03 幂等、失效与撤销 | 不通过（完整复核未完成） | 已有修复版材料提供局部支持，非权威 L3；发现零容忍边界失败后不继续消耗完整重跑 |
| AC-04 重启/竞争/事件 | 不通过（完整复核未完成） | 夹具修正理由可接受，实际业务 AC 仍需新合法计划下独立复核 |
| AC-05 完整验证与边界 | 不通过 | 原冻结正式 L2 缺失，v3 为执行者自行版本化验证；同执行者发起 evaluator 模式不能冒充独立签收；费用计数须统一 |

这里的未通过不代表 AC-02/03/04 已发现行为反例。已实证的产品失败为 AC-01；AC-05 为证据资格和计费问题。不因固定修复版 7/7 或二十例通过而接受来源隔离缺陷。

## 费用复核与修复预算

- 父 Executor 已消耗 79/160 案例预留、报告保守 30/240 主动分钟。两原目录 `l2_repair_v2_01`（失败）、`l2_repair_v3_01`（通过）都是实际完整计划尝试，经济/重试计费为 2/2；“原计划正式 L2=0”只描述证据资格，不能用于抹掉两次成本。
- 同一执行者发起 evaluator 模式 20 例不是独立评估，但保守占原 Evaluator 60 例额度。本轮独立六例逐例前耐久预留；共占 26/60，剩余 34。纯夹具诊断无候选调用，单独记录。
- 新 H60R 明确分配新 repair 门禁最多两次，跨父/子总门禁费用上限四次；不是把原包 2/2 清零。Executor 新案例最多 72，累计最多 151/160；新主动分钟最多 120，父子累计上限 150（父原总 240 内）。Evaluator 新包最多 34，父子累计不超过 60。
- 本轮候选对一次性来源副本的实际 schema 写入如实记录，不能再笼统声称“候选来源写入为零”；原两库、业务订单/库存/资金未改变。无 HTTP/网络/Provider/模型/安装/Git 写操作。

## Project-impact verdict

INCONCLUSIVE

已有未验收候选和修复版局部证据，但没有可接受的本地批准能力净提升；也不把仅发生于配置别名副本的缺陷夸大为既有支付能力退化。原 M06 仍付款 1、订单 0。B-17 暴露新的本地隔离断点，优先关闭该零容忍边界，而非扩展身份或自动执行。

## Continuation decision

CONTINUE

Next task: H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1
Next state: CONTRACT_FROZEN / Executor
Next contract: docs/05_任务交接/H60R_SOURCE_LEDGER_ISOLATION_REPAIR_V1/CONTRACT.md

一个产品主变更：仅修新副本 ApprovalInbox.__init__ 的来源/账本文件身份隔离，所有其他业务方法冻结。验证前提由 Evaluator 在新包合法采纳已审查 v3 夹具修正，并固定原二十例加四条别名回归，共 24 例/七 VP。候选原样复制，修复尚未实施；不由 Evaluator 编辑产品。

相比 STOP 放弃已完成候选或 SWITCH 回 H56，一次有界修复有清楚反例、低范围和直接收益。通过后 STOP 扩展登记器，另评批准的实际消费者；预算耗尽或需改其他方法/业务权限则停止回 Evaluator。

## External requirement impact

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/09/10/12/20 CORE：对象=父 CONTRACT 与批准记录/事件；代码=APPROVAL_INBOX.py；Test=父修复版材料及本轮六例；Evidence=本目录。maturity_before=M2 IMPLEMENTED 候选；maturity_after=仍为未接受候选，不能声称有界 M4 EVIDENCED。PCAC-18 业务处置未实现；PCAC-08 现实人工身份/意愿 unknown。无监管合规结论。

## Final verdict

REJECTED

这是未签收交付的有证据拒收，非正式 L3 FAIL；不覆盖父 REPORT/失败/计划/自重放，也不回写 H57R/H58 或更早拒收结论。
