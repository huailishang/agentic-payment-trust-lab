# H76 冻结独立审阅要求

自动CHECK不能单独证明外部来源真实性。Evaluator必须检查RUN/WORKLOAD/Dockerfile实际实现与容器命令、发行者/Agent日志和公共产物一致；不能仅复算任务自行填写的JSON。

1. 接受前核原公共L2各三件套、plan/报告/源文件/全部引用摘要、原基线、冻结文件及授权原话。`python -B ../localagent-common/skills/evaluator-executor-workflow/scripts/validate_workflow.py --repo . --current CURRENT.md`只做结构检查。用git status/diff及BASELINE确认src/tests与旧任务保持，任务新文件白名单匹配。记录SUBMISSION及所有原提交文件的接受快照，接受后不可修改。
2. 在运行前读任务脚本：正例只来自锁定SPIRE二进制Workload API；无本地签CA/叶、旧证书替换、伪造日志/UID、导出SVID私钥或隐式外网。核实际资产SHA与版本、安装METADATA/licenses、base digest/image ID与Dockerfile；若SPIRE musl发行包在该base不能运行，记录具体不兼容并STOP，不换新资产。
3. 用本任务BOOTSTRAP `--mode evaluator`跑冻结计划，新的实际运行在evidence/evaluator_runs内。Evaluator亲自回查Docker inspect（运行期间的容器ID、image ID、PID/隔离/能力/资源）、管理bundle取得顺序、实际entry/父Agent关联和UID1002接口拒绝日志。必要只读Docker CLI核对不额外启动容器；不可把旧L2 JSON直接复制为L3。Docker Desktop本来已运行则结束不关。
4. 对AC-02逐项人工核：一Server/Agent实际进程启动、根新鲜/管理socket来源、配置没有UpstreamAuthority/dummy、rootfs/tmpfs/无挂载/无外网/权限最小化、至少与L2根和nonce不同。AC-03核取证与签名PID/UID、选择器及负例真实PermissionDenied/0SVID；文件权限或超时不得替代。
5. 对AC-04/05用CHECK公开证书/签名复算及原验证器10个单量变异，核目标原因被触发；独立读原代码确认没有把凭据直接升级为授权。错误Provider/nonce必须挑战绑定失败；过期观察要在根有效区间内，明确模拟时间。若实际证书链不兼容，只按测得缺口写结论，不放宽Checker。
6. 对AC-06保留原身份/上下文28项（6+6+16）及Stripe19/安全9/业务74原始输出；数字仅为冻结前已知预期，**验收以原完整测试集和全部断言成功为准**。异常减少测试数/跳过/测试继承变更均失败。普通任务脚本修复不能替代原回归。
7. 对AC-07核完整追加attempt ledger，失败计入、每文件/运行单位上限、确切可得字节和Docker隐藏网络UNKNOWN分开；独立确认本包容器/私有tmpfs清除且其它容器不动。检查公开输出及task runtime无SVID私钥，密钥相关日志明确脱敏，不将脱敏投影谎称完整原件；主机设置无变化。无工作时长硬上限，成本实际/估计/UNKNOWN分别记。
8. L3后再次复算接受快照保持；逐AC通过/不通过，PASS/REJECTED/HUMAN_REQUIRED与IMPROVED/NO_MEASURABLE_GAIN/REGRESSED/INCONCLUSIVE分别给结论。仅完整实测通过才可说受控实际发行来源切片前进；企业身份/强认证/生产能力不升级。协议/环境不兼容有信息价值但不得将强制AC失败判PASS。

L2重试仅在两版/两次范围内，首轮保留evidence/l2，第二轮BOOTSTRAP `--mode executor --attempt 2`写evidence/l2_retry_02，不覆盖旧三件套。每次正式门禁由BOOTSTRAP在启动前追加唯一ledger事件；L3只一次。新实际运行nonce/根自然变化不算合同变更。零容忍反例、原回归失败或缺授权立即停止，不进入常规脚本重试。
