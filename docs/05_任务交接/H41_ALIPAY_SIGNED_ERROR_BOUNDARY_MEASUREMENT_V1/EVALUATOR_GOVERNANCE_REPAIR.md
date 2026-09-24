# H41 R2 — Evaluator 交接结构修复

Owner: Evaluator。Status: EXECUTOR_EVIDENCE_READY / INDEPENDENT_L3_PENDING。属于同包治理纠正，不重新派发产品实现。

## 2026-09-23 执行者补证记录

Human 要求修复后，原 Executor 完成 amendment 2026-09-23-a2 的合同/计划表示修订和 L2 补证。没有切换为 Evaluator，也没有重新裁决已验收的 R1。CURRENT 与合同类型对齐为 one_off（仍为只测量），原假设/AC/保护边界/请求预算不变。

原七项 VP 均具有真实命令，中央 runner 以 executor 模式生成 evidence/r2_executor_20260923/L2-GATE.json：PASS，7 项全部 exit 0。四组专项共 70 项通过；原独立检查器复跑 7/7，原保护 hash 7/7 以及产品/测试/检查器 hash 均一致。VP-06 额外复跑一项秘密测试。使用已有系统 Python 的 yaml 和 bundled Python 的 cryptography，没有安装包。首次创建证据目录被沙箱拒绝，获得执行授权后完成同一离线计划。

中央 validate_workflow.py --repo . --current CURRENT.md 返回 exit 0：OK，结构无 BLOCKING 或 FIX_IN_PLACE。REPORT 新增执行者补证附注及全部 EV 引用，原观察与 review_20260923 证据保留。当前没有 L3 门禁，不将执行者复跑伪称独立验收。

下一步只需 Evaluator：确认本表示修订、检查范围与证据，使用相同计划在新的独立证据目录运行 --mode evaluator，核对所有 AC 后记录正式 P0 裁决与批准 hash。运行前设置 H41_TEST_PYTHON 指向已有含 cryptography 的测试解释器；入口显式设置测试子进程 PYTHONPATH。不得覆盖 executor 或既有 review 证据。真实网络/密钥/付款/造单/提交/推送均为零；本次不切换 P1。

目标：使 H41 原冻结验证要求可以由 v2.2 runner 执行并可追溯，中央结构检查无 BLOCKING 后才评估 P1 放行。B-06 仍是第一瓶颈；这项修复优于继续扩 AP2/攻击测试，因为一次性外部测量必须有可验证的交接前置条件。

允许范围：CURRENT、H41 合同的元数据/标题与计划文件引用、验证计划命令、评估者检查入口、评估者证据/REVIEW、地图状态。REPORT 若需引用规范化，须以评估者附注区分，不改 Executor 历史观察。合同或计划表示修订明确记为 amendment；不改变 AC、业务语义或授权。无需 Human 新事实或新增权限。

执行步骤：

1. 用 v2.2 已支持的 task kind 表达有界测量（例如 one_off，并保留 measurement-only 语义说明），对齐 CURRENT 与合同；修复必要标题及 Validation plan file 字段。
2. 为 VP-01/06/07 补真实可执行检查，为 VP-02—05 明确可用运行时/PYTHONPATH。保留全部原验收要求，先完成计划表示修订再复跑；不得用固定返回 0 代替审计。
3. 通过中央 runner 生成新的 evaluator L3 原始输出/退出码/摘要，保留此前证据；如缺 Executor L2，明确请求仅补证据，不伪造其角色执行记录。
4. 运行 `python ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md`。全部阻塞关闭后记录最终 P0 裁决与批准 hash；根据原合同独立切换 P1，不额外增加请求预算。

验收：结构校验无 BLOCKING；每个 VP 有真实命令与 evidence；70 项专项和 7 项独立检查保持通过；保护 hash 不变；无真实请求/真实密钥读取；角色和证据归属准确。

排除：产品代码、中央 workflow 实现/schema、H38/H40 保护文件、新依赖、网络、密钥、造单/付款、commit/push。零外部预算、单一治理修复轮；若需要改变 AC/假设/预算或中央协议，STOP 并记录原因，不自行扩张。
