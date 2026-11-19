# H68 Executor 唯一开工说明

1. 先读根CURRENT。只有本包为CONTRACT_FROZEN/Executor且AUTHORIZATION.json已由Evaluator记录明确原话并授予本包精确权限时才能开工。当前DRAFT_CONTRACT必须停止；不得把制包、平台选择或低手工偏好当作运行许可。
2. 读取CONTRACT、SPEC、SOURCE_LOCK、SCHEMA_GUIDE、VALIDATION_PLAN与INPUTS；运行 `python docs/05_任务交接/H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/CHECK.py integrity`。保护不匹配即停止，不更新摘要迎合工作区。
3. 为本轮选唯一run_id。在ATTEMPT_LEDGER.jsonl预留active_work和implementation BEGIN；CURRENT进入EXECUTING。账本定义见SCHEMA_GUIDE，每次物质尝试必须先BEGIN，成功失败均END；init开始24小时墙钟和8主动小时额度。
4. 先完成最薄外部Adapter与隔离启动/脱敏包装，使用现有模型、validate_request与真实付款回调闸门。新本地接缝测试覆盖非ALLOW/错绑时API与浏览器回调0次；不能只构造ALLOW布尔值。先运行廉价离线检查。
5. 创建仓库外专用私有目录并限制访问，H68_PRIVATE_DIR只指向该目录。配置、原始证据和浏览器上下文均隔离；不读默认Stripe配置，不把完整创建/监听输出送入工具或报告。Windows后台辅助进程采用隐藏窗口并记录本任务PID；不关闭用户已有进程。
6. 按SOURCE_LOCK指定URL下载CLI，核字节数及SHA-256后解压，仅用该二进制。已核发布源码支持全局 `--config <private>/stripe.toml`；进程环境去除继承的Stripe密钥/账户选择变量，设置STRIPE_NO_AUTO_UPDATE=1。不要通过改HOME变量隔离，不用--from-git、不用agent setup。
7. 在匿名创建计数预留后，包装运行 `stripe --config <private>/stripe.toml sandbox create --email h68-checkout-lab@example.invalid --non-interactive`；此为逻辑argv说明，实际调用不能把秘密回显。一个创建尝试仅含官方challenge/provision流程；不得跟随正式登录回退。需要真实可收信邮箱即INPUT_LIMIT。
8. 验证返回测试密钥、账户和期限；先GET账户与空的会话/付款/收款清点，确认本轮全新隔离上下文。若权限不足，保留具体失败，不改版本/扩大账号。启动127.0.0.1商户及本地事件监听，仅监听合同事件，不注册公网端点。监听签名秘密仅通过私有配置/内存进入验证器。
9. 最早运行N01资格路径：本仓批准→创建会话→拿到真实checkout.stripe.com页面→付款前核对→用现有受支持浏览器工具填写官方合成测试数据。遵守该工具说明/适用计算机使用Skill。登录/验证码/防自动化挡住就停止，报告INPUT_LIMIT，不能以API直接confirm或伪造浏览器记录替代。不得要求Human例行代点全部流程。
10. N01成立再按C01、R01、D01顺序推进，各只创建一个会话。R01在我方返回和事件消费入口暂缓，原始事件仍保留且不能提前注入产品；记录UNKNOWN及一次本地重启后查询原会话。D01只在我方交付入口故障并恢复；不对Stripe做故障注入。
11. 每次浏览器付款前需已有实际create/pay闸门记录、授权/订单/资源摘要与原生会话金额匹配。取消后expire原会话；未付款的PaymentIntent可以存在，不能当成成功收款。任一未知状态优先查询，不再点付款或新建会话。
12. 原始HTTP、会话/付款/收款/清点、CLI通知、实际页面过程和我方状态保存在私有材料中。生成RESULT与PROVIDER_SNAPSHOT，格式严格按SCHEMA_GUIDE，不把不完整旅程填成成功。若资格失败，写保留失败的REPORT/BLOCKED，不运行一套全绿假证据。
13. 正式L2前预留l2 BEGIN，使用公共runner：`python ../localagent-common/skills/evaluator-executor-workflow/scripts/run_validation.py --repo . --plan docs/05_任务交接/H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/VALIDATION_PLAN.yaml --out docs/05_任务交接/H68_STRIPE_CHECKOUT_SANDBOX_JOURNEY_V1/evidence/l2_01 --mode executor`。最多两次，各用不同输出目录，不能覆盖失败。VP-04是只读回查，不重复付款；同actor已经成功的readback只重审，不重发GET。
14. L2完成后追加END并停止本任务监听/商户进程，保留私有复核材料及未过期只读访问。关闭active_work后运行 `CHECK.py budget --closed`；原始stdout/stderr/失败与L2门禁随REPORT提交。CURRENT仍EXECUTING/Executor，不自行PASS。
15. Evaluator接受未变快照后预留独立L3及active_work，独立生成本轮随机H68_EVALUATOR_NONCE（至少32字符，仅本轮环境/私有目录保留），并以 `--mode evaluator` 跑同计划；只读预算20次，不重跑付款。Evaluator读回不能使用Executor预制的同名文件，CHECK将核随机nonce和自身源码摘要；不一致保留材料并停止。L3除程序检查必须阅读实际副作用接线、故障位置及原始证据。独立复核无法完成则不得PASS。

遇scope、权限、依赖、AC、预算或架构义务需改变时交回Evaluator；已通过N01也不代表可以扩退款、库存、多商户或新攻击。保持H67延期和旧任务证据不变。
