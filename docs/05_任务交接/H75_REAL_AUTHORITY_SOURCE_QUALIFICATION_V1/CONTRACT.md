# H75：真实签发来源资格设计

后续状态：负责人已明确“不用自设时间，继续完成”，本设计按CONTINUATION_AUTHORITY.md续行并完成制包；权威收口见CLOSEOUT.md及H76完整合同。下列25分钟/6调用和DRAFT为前一窗口的原约束，原字节另存references/before_owner_completion，不再作为续行停止条件；不追改旧超限记录。

Task ID: H75_REAL_AUTHORITY_SOURCE_QUALIFICATION_V1
Workflow: evaluator-executor-workflow/v2.2
Task kind: evaluator_design
Contract state: DRAFT_CONTRACT
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-16-r127
Active bottleneck: B-15
Hypothesis: H-75

## Current design objective

H74R签收后停止B-22本地stored切片。复用已有X.509-SVID消费者与旧参考中优先候选SPIFFE/SPIRE，核实能否以一个实际运行的发行者/工作负载来源提供下一代表性证据；不重复本地合成凭据实验。真实签发进程不等同真实企业主体、真实用户同意或付款授权。

## Exact unresolved inputs

尚未核实际SPIRE运行环境、可用本机隔离方式、下载/安装/服务/测试凭据与工作负载证明的最小权限。先查已存参考和官方公开资料、只读本机命令可用性，形成单一候选的可审阅运行方案；缺可执行环境或所需权限时保持DRAFT，不能派Executor。

本轮不再要求Human先在笼统身份分支中选题：已有参考明确SPIRE是既有X.509-SVID的第一资格候选，先用有界资格核验消除环境/证据不确定性。后续若仍有多条重要且证据无法收敛的来源分支，再建议Human显式/wayfinder；不机械增加讨论。

## Evaluator preparation envelope

Human在H74R复核期间明确“继续”，本阶段仅推进后继设计。制包/资格设计整窗从H74R评估END保守起算，上限25分钟，最多6次公开网页工具调用；没有额外模型服务。可读取PCAC映射、既有ATI/SPIFFE/BSN/AP2参考和本仓X.509-SVID消费者；可用Get-Command读命令存在性，追加docker version及docker compose version两项本地只读客户端/daemon元数据检查。不得自动启动Docker Desktop/daemon、WSL、容器或服务，失败保留INPUT_LIMIT。

授权公开只读参考研究：官方SPIFFE/SPIRE文档、规范和仓库优先。保存URL/观察日期/声明边界，不把网页可见当运行就绪。输出QUALIFICATION.md、来源/成本记录、后续运行边界草案；不计产品能力或正式L2/L3。

authorization_reference_read: true
authorization_api_call: false
authorization_install: false
authorization_local_service: false
authorization_browser_test_only: false
authorization_test_payments: false
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false

不下载二进制/镜像、不启动Docker/WSL/发行者/Agent、不签发凭据、不生成密钥、不请求私有账号/生产凭证、不付款、不读旧支付私有原件。本任务全部实际运行权限仍缺，公开研究不授予后继运行权限。

## Freeze / stop conditions

找到具体隔离环境、最小命令与依赖、真实证据/负例、成本/回滚和权限范围后，形成可供最终授权审阅的运行方案；未获运行权限不将DRAFT改为CONTRACT_FROZEN。若方案只复现本地合成密钥、无实际发行者/工作负载或没有既有消费者，STOP当前候选；不自动换其它平台或扩身份体系。预算/工具调用限额耗尽即形成INPUT_LIMIT，不续期。

external_requirement_impact: profile=PCAC-AGENTPAY；PCAC-03/05/06/07/08/12/15/20；本轮为CORE/ADAPTER资格设计，成熟度before/after不变。对象为发行者/工作负载事实到既有身份验证器，不把凭据存在等同支付授权，不构成合规结论。
