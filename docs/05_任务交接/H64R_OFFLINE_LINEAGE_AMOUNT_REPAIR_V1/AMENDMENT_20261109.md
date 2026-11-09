# H64R 开工前基线迁移修订

Task ID: H64R_OFFLINE_LINEAGE_AMOUNT_REPAIR_V1
Amendment ID: H64R-BASELINE-20261109
Owner: Evaluator
Kind: evidence_fix（证据与路由修正）
State: CONTRACT_FROZEN
Date: 2026-11-09

## 全局位置与决定

目标是高风险交易信任链可独立复核。A–D本地阶段关闭、E受控本地代表闭合、F当前；B-18仍是外部轨迹可判定性。H64R仍只修源事实的逐调用关联与金额清点。H62代表切片已闭合，真实支付B-06仍受授权限制；迁移现有任务的基线比扩产品、再下载或换数据源更有价值。

Decision: CONTINUE（继续同一H64R修复任务）。本修订只恢复已冻结任务在当前工作区的开工条件，不签收H64R成果，不声称项目能力改善。执行者仍由Human另行启动。

## 原因与可复算证据

原冻结HEAD为7831d232530c91825bb507a2a6d95b1de6a02c3b；当前HEAD为211151e6c3ae53997b5a2da419c27db497d7eb48。原source检查在HEAD断言处失败，原始三件套为evidence/governance_refreeze_20261109/PREP-00.*。

评估者逐项核对3816个保护文件及7个冻结文件。3812个保护文件及全部7个冻结文件一致；另4个文档仅10行各删除两个行尾ASCII空格。原始字节已从本地Git对象恢复，其SHA-256与原BASELINE逐项相同，且程序逐行验证除此之外没有字节变化。四个文件的当前内容与Git HEAD一致。没有下载、解码样本或执行产品。

| 文件 | 原始Git blob | 仅删除行尾两空格的行 |
| --- | --- | --- |
| competition/jinmi-cup-2026/README.md | 5fac5ace4adcc727cfb6bb1725e48e040e2a6838 | 3、4、5、26 |
| competition/payathon-2026/README.md | 8d23c1d7ed6f25cc3b36dd31f6d5f6ad82aefce5 | 3、4 |
| competition/payathon-2026/docs/ACT_A402_GAP_ANALYSIS_v1.md | 9511d560a66ad809c5ea4607fcb9c893ba74875e | 3、4 |
| docs/01_项目现状/archive/PROJECT_BOTTLENECK_MAP_20261106_r100.md | a32aad586492a7feaa7d4b881cee177e295115bb | 5、6 |

证据：evidence/governance_refreeze_20261109/DRIFT_AUDIT.json记录原/现SHA、行号及四个文档完整原/现字节的Base64编码；ORIGINAL_SNAPSHOT.json记录修订前CURRENT、地图、BASELINE及全部7个冻结文件的完整字节与摘要。编码只用于无损保存原字节，不是新产品输入。历史字节复现应解码该快照，不能把当前r100展示文件声称为旧摘要对应的原字节。

## 精确变更边界

- 执行基线HEAD迁移至211151e6c3ae53997b5a2da419c27db497d7eb48；把上述四处已证明的格式变化纳入新保护摘要。
- r104原地图逐字节归档，当前地图升为r105，只增加本次治理事实和历史字节说明；B-18排序、H-64假设及阶段能力结论不变。
- 更新CONTRACT、EXECUTOR_START、CURRENT中的执行基线、地图版本与本修订入口；READINESS/BASELINE重新冻结当前快照，纳入本修订和不可改审计材料。
- CHECK.py、VALIDATION_PLAN.yaml、SETUP_BASELINE.py、references/PRIOR_CURRENT.md保持旧摘要；四VP、四AC的业务验收语义不变。AC-01明确从已审计的新快照开始保护，不追认开工前字节差异为“从未改变”。
- H64全目录、数据、原L2/L3、拒收结论、失败获取记录、历史任务、三来源库与解码器保持；不运行历史全工作区checker，不修改四个差异文档。

## 冻结执行合同与交接判据

唯一目标仍是逐原生调用id清点与无损金额提取；同六例、同四Parquet和11个world。允许最终不可判定，但必须逐维证明缺失条件。call-32/call-34不得混拼；call-68的4425/usd/checkout原值不得清空。签名不新增为本包强制条件，邻接消息不构成授权绑定。

预算仍为90主动分钟、12次样本读取、2分析版本、2正式L2；评估者此次准备不消耗或预支执行者样本/L2预算。新增网络、安装、模型、产品、上游回放、付款均0；四项Git/API授权仍false。

交接前必须通过：新source保护检查、原8个纯函数用例及再次source检查、中央工作流结构检查、独立旧/新快照审计。准备检查只证明可开工，不充当正式L2/L3，也不判定AC-02/03已通过。

执行者不得修改本修订、BASELINE或评估证据。新HEAD/保护摘要漂移、额度耗尽、需要新源或权限时停止交回Evaluator；不得自行再次迁移。修复正式L2通过并提交后，Evaluator独立L3和逐源语义复核，再决定是否冻结回放测量；无额外信息收益则STOP（停止），出现更优先安全反例则SWITCH（切换）。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-07/08/09/11/12/14/20；适用性继承原修复合同；本次仅证据完整性与执行基线修正，产品成熟度before/after不变；Test=准备source/oracle/工作流/迁移审计；Evidence=本目录PREP三件套与快照；真实身份、清算、外部控制效果及合规仍unknown。
