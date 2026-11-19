# H80：已验证凭据事实的消费上下文最小修复

Task ID: H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1
Task kind: repair
Workflow: evaluator-executor-workflow/v2.2
Risk: L1
Contract state: CONTRACT_FROZEN
Baseline HEAD: 61414d05521f7c9fe15cf0299b48b25916f5fa0e
Project map: docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md
Map revision: 2026-11-17-r135
Active bottleneck: B-23
Hypothesis: H-80
Parent: H79_VERIFIED_FACT_CONTEXT_CONSUMER_MEASUREMENT_V1
Dispatch mode: SINGLE
Validation plan file: docs/05_任务交接/H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1/VALIDATION_PLAN.yaml

## Strategic basis / 战略依据

目标为授权→可信主体→交易治理→支付→恢复→审计。A–D本地阶段关闭，E受控来源代表切片已签收，F受控外部切片关闭。H79只测量任务PASS/NOT_APPLICABLE/CONTINUE：L2/L3各4/4，2395接受项不变；同一真实H78证明在跨Agent自洽消费上下文中错误晋级VERIFIED（凭据已验证）。原验证器已核规范签名payload，事实却没有携带并在消费者核对三元上下文。

Metric baseline: H79 M01同上下文VERIFIED；M02跨Agent仍VERIFIED；M03–M06未执行，不预报其结果。
Hypothesis: 只传递原验证器成功验签的Agent/Provider/Executor三元上下文，并在消费晋级前精确核对，可消除跨上下文错误保证等级，不改变现有支付政策。
Principal change: 凭据事实的已验证上下文传递与消费核对，作为同一个接缝修复。
Expected impact: 修复具体归因反例并封住三维同类晋级路径；不声称真实身份生命周期、监管合规或资金安全闭合。
Estimated affected scope: 一个共享身份消费者、一个验证事实类型；支付门禁通过既有调用直接消费，不增模块。
Why first: 已有独立正反例、机制明确且成本低，优先于真实轮换/撤销和第二平台；不需要外部研究或新增领域设计。

## Single objective / 唯一目标

保全父证据→实现一个上下文接缝修复→必要回归→完整L2与原始提交→不变快照接受→唯一独立L3。Evaluator只制包和复核，不在本轮实现产品。

## Frozen behavior / 冻结行为

1. 在现有frozen dataclass CredentialPossessionVerificationFact尾部追加三个可选字段，默认None，保持旧构造器兼容：verified_agent_ref、verified_provider_ref、verified_executor_instance_ref。不引入第二种身份事实/容器/序列化系统。
2. verify_x509_svid_credential_possession只有全部原检查成功返回VALID时，才将原规范签名payload已绑定的expected Agent/Provider/Executor精确值写入三字段；任何INVALID/MISSING_EVIDENCE返回均为None。可调整同文件_fact帮助函数，原证书/信任域/SAN/签名/新鲜度/重放检查和原因不削弱。
3. verify_agent_executor_identity原base绑定无效/缺失立即返回；credential_ref规则及其原原因优先保持。只有原status/四布尔/非replay条件成立、三个已验证字段非空且与authorized_agent_ref/current_provider_ref/current_executor_instance_ref精确相等，才可VERIFIED。禁止从当前消费者输入补造证明字段，禁止只解析subject替代Provider签名上下文。
4. 满足原晋级条件但上下文缺失，返回VALID/BOUND（确定性引用绑定）并加credential_possession_context_missing；三字段齐全但不符，加credential_possession_context_mismatch。旧鸭子类型对象没有字段时用安全缺省，不能抛AttributeError或晋级。空白字段视为缺失，实际引用相等保持精确比较，不因strip而将不同标识认作同一。
5. 原无证明/错误证明/不匹配credential_ref的BOUND策略不变，原身份inactive/revoked、授权/请求/执行冲突继续阻止callback。BOUND/VERIFIED采用同一支付策略是既有合同；不改payment_execution，不强制VERIFIED，不新增DENY。
6. tests/trusted_execution/test_payment_binding.py只允许在已有test_verified_identity_uses_same_payment_policy_as_bound_identity的手写事实构造器中追加三项与原fixture一致的关键字；所有原断言/测试方法/fixture业务逻辑保持。增加一个独立回归测试文件，不改原credential/identity/Stripe测试。

## Acceptance criteria / 验收标准

### AC-01 范围、兼容与历史

HEAD不变，只有Allowed scope所列两产品文件、一个限定fixture调整及一个新回归测试可变。父H79全部接受项、L2/L3/REVIEW与H78真实来源和历史失败保持；允许改的父源码/测试以旧字节别名保全，不声称修复后父原路径不变。旧dataclass构造器可用，三字段None；原支付fixture除三kwargs外AST相同，共享工具和冻结checker不变。

### AC-02 原反例及三元上下文

从SOURCE锁定的H78公开证明按原observed复算，不制造VALID；成功事实三字段与原签名payload相等。完成H79原六槽：M01为VALID/VERIFIED、P2/P4有效、callback1；M02/M03/M04为VALID/BOUND且明确context_mismatch；M05保留原ref_mismatch/BOUND；M06为INVALID/DECLARED、callback0。每项保留精确输入、源主体、三字段、原因与结果。ALLOW和本地callback不是实际付款。

### AC-03 缺失及失效不能晋级

同一成功事实去掉全部/逐个三元字段、以及旧鸭子类型对象无三字段，都BOUND且context_missing；不抛异常。无证明保持BOUND。inactive和原base请求主体冲突均INVALID/DECLARED且callback0。原十个密码学负例全部按原原因拒绝、上下文字段None，送入自洽消费者不得VERIFIED。额外将已验证事实的status/四布尔/重放条件逐项置为不满足（明确合成守护单测，不称新实际来源证据），均不得晋级。

### AC-04 必要回归与独立证据

原28+19+9+74=130回归通过，另运行原18支付绑定测试及新增回归文件，不skip、不删断言。原16/4正21负/8门禁按原离线命令复跑、历史材料保持；原十实际来源负例在本包离线重算。全部四项L2通过后一次提交REPORT/SUBMISSION/完整EV、行为原文、实现diff/源码摘要和成本；接受后唯一L3。L3不接受Executor结果自报作为独立事实。不执行父物理来源或修改其证据。

## Allowed scope / 允许范围

- src/agentic_payment_experiment/trusted_execution/credential_possession.py，仅CredentialPossessionVerificationFact追加三字段、verify_x509_svid_credential_possession及_fact；其余顶层AST和原dataclass字段保持
- src/agentic_payment_experiment/trusted_execution/execution_facts.py，仅_CredentialPossessionFactLike与verify_agent_executor_identity，其余顶层AST保持
- tests/trusted_execution/test_payment_binding.py，仅上文三kwargs
- tests/trusted_execution/test_credential_context_consumption.py，新文件
- 本包REPORT/SUBMISSION、ATTEMPT_LEDGER、evidence/executor_*、l2/l2_retry_02与runtime。实现cycle标记由BOOTSTRAP创建。

本包CONTRACT/PLAN/CHECK/BOOTSTRAP/SEAL/PREPARE/SOURCE/BASELINE/FREEZE和references只读。Executor只可更新CURRENT的执行状态/阶段及报告路由，任务/AC/权限不变；Evaluator拥有ACCEPTED/REVIEW/独立L3及后续治理。已有无关未提交改动原样保持，禁止暂存/提交/推送。

## Exclusions / 排除

不变更支付策略、强制保证等级、授权生命周期、轮换/撤销服务、信任根、真实外部身份或平台；不重开H78。无WSL/服务/生成或读取私钥/新凭据/网络/安装/下载/API/浏览器/真实付款/Git。验证器产出的事实仍是进程内可信对象；本包不证明抵抗任意调用者伪造dataclass、持久化篡改、用户强认证或真实当前有效性。

## Steps, branches and repair envelope / 步骤分支

Executor读冻结包、父REVIEW和SOURCE；先BOOTSTRAP --mode implementation --attempt 1登记，再进行合同内实现与廉价L1。运行BOOTSTRAP --mode executor --attempt 1完成全部L2。PASS即停止实现与重跑并统一提交；FAIL保全原输出，仅无范围/AC/权限变化的本接缝修复可登记attempt2并执行第二L2。第二失败或新共同断点需要扩大范围即停止交Evaluator。父H79反例是修复输入，修复后仍错误VERIFIED则本次L2失败，可在剩余同一修复额度内纠正；其它零容忍新反例立即停止。不得为加时/续权或“多跑几轮”改checker。

## Validation plan / 验证计划

VP-01范围/历史/fixture兼容，AC-01；VP-02独立冻结消费者与密码学守护，AC-02/03；VP-03原130+18与新增测试，AC-04；VP-04最终范围/接受保持，AC-01/04。正式命令见VALIDATION_PLAN.yaml。H80 CHECK不运行H79严格保护命令，因为本包明确修改了父源码；历史通过旧字节别名保护。

## Cost and bounded budget / 预算

Expected material cost: low，纯本地验签/模拟消费者/回归，付费及外部调用0。
Bounded retry / iteration budget: 最多2实现cycle、2正式L2、1独立离线L3，顺序执行。每cycle廉价目标L1至多2次；初版实现加一次合同内修复，不改冻结验证器。正式成功后不续跑。单个回归子进程原有240秒超时保留；无自设总墙钟上限。主动分钟UNKNOWN则如实写，编排窗/工具次数另记，不借未知成本重置父失败。
Attempt execution mode: SEQUENTIAL
Evidence sufficiency target: 所有AC及冻结原文、必要回归、快照接受和一次独立L3
Max total attempts: 2 implementation, 2 L2, 1 L3, 0 issuer
Max parallelism: 1
Stop-on-sufficiency: true
Attempt ledger: docs/05_任务交接/H80_VERIFIED_FACT_CONTEXT_BINDING_REPAIR_V1/ATTEMPT_LEDGER.jsonl

## Authorization / 授权

仅现有Windows agent Python、本地文件/进程内fixture；reference_read=true。api_call/install/download/local_service/existing_wsl/ephemeral_test_credentials/browser/test_payments/commit/push/history_rewrite全部false；继承“评估后制包”及本地可逆修复范围，不继承H78物理运行许可。无缺失Human事实/授权。

## Stop conditions / 停止与下一步

源/冻结输入漂移、预算用尽、新权限、范围/AC/机制变化、新零容忍反例→STOP交Evaluator。全部AC独立成立→关闭B-23本地代表消费切片、停止同类扩例，再比较真实生命周期与其它端到端未知；不得从此自动启动外部源、钱包或付款。结果不足→只保留已测范围，不造产品改善。

## External requirement impact / 外部指标

external_requirement_impact：profile=PCAC-AGENTPAY；requirement_ids=PCAC-03/05/06/09/12/20。03/05/09/12为CORE，06为CORE/ADAPTER，20为CORE/EVIDENCE_ONLY；仅已验证上下文传播窄对象适用。maturity_before=M2（实现有已证反例）；maturity_after=待验收，不预填整体升级。对象/Contract=CredentialPossessionVerificationFact与消费晋级合同；代码=上述两产品文件；Test=冻结CHECK、原回归与新测试；Evidence=H79反例/H78公开源及本包L2/L3。残余为进程内事实可信边界、历史重放非当前认证、未测真实撤销/轮换、组织用户身份和生产采用。无监管合规结论，机构级项不机械实现。
