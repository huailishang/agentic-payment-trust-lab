# H78 单次运行授权申请（完整候选已备齐，当前未授权）

H77R3解析修复已独立签收，完整实际UID/SVID/持有链仍未闭合。当前H78的代码、六项机器验证计划、固定来源、失败分支、预算、提交封存和独立复核清单均已补齐；原始L1与候选摘要见evidence/preparation/READINESS.json和CANDIDATE_MANIFEST.json。这些均不构成正式L2或运行授权。

如Human决定继续，授权范围仅为H78：

- existing_wsl：固定现有Ubuntu，Executor/Evaluator各最多一次无服务真实资产提取/摘要/清理；禁止安装、下载、更改WSL设置或切换发行版。
- local_service：仅Evaluator在正式L3内唯一一次SPIRE 1.16.0来源事件，Server1次、Agent1次。允许127.0.0.1回环和本次Unix socket；禁止主动外部网络请求，不宣称原生WSL有出站强隔离。
- ephemeral_test_credentials：仅本次测试根/节点引导、UID1001/1002工作负载、短期SVID与挑战签名；私钥/join token只在本次有所有权的tmpfs，禁止导出与真实用户/机构凭据。

预算：2次正式L2；双方各1预检；Executor发行0、Evaluator唯一1次正式L3/1次发行；Server/Agent各最多1次。单运行内原匹配取证最多3次仅同步、非匹配1、持有签名1；原十负例/16保护/130回归和独立清理不减。首次资产失败或实际发行失败停止保全，不修后重发，不补发父任务额度。外围Windows监督器等待原发行器1100秒防挂与清理完成；单SPIRE命令180秒，不用外层超时抢断清理。未知主动时间/字节保持UNKNOWN。

无新下载/安装/外部API/浏览器/付款/真实资金/生产接入/提交推送/历史改写。其余权限保持false。

Evaluator应记录Human真实原话/来源到AUTHORIZATION.json，再审定候选、同步唯一项目地图、冻结合同和路由、运行BUNDLE.py seal与公共结构校验。代码不会自行授权或代改CURRENT。随后Executor执行完整L2，统一交付后Evaluator独立L3，不逐步骤Human复核。

本次Human要求“看下现在执行包，是否合理，批判分析，并按照约定制定完整”，授权的是候选制包与已有本地离线检查；没有将该句解释为上述新物理执行许可。

当前状态：NOT_GRANTED；合同DRAFT_CONTRACT；正式L2/L3、WSL、服务、新凭据均未运行。
## 授权已生效（原申请原字节已封存）

Human在紧接上一条明确范围确认后答复“批准”。AUTHORIZATION.json保存原话、前置问题及具体边界；Evaluator现已审定并冻结H78新包。上述“未获批”属于此前申请时点，不再是当前权限状态。仅本包三项许可生效，旧预算与失败不重置。
