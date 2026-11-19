# H75：实际SPIRE签发来源资格核验

续行收口：负责人取消自设制包时间限制后，固定资产/签名依赖/运行方案/完整验收计划已补齐，见CLOSEOUT.md与H76合同；当前只缺明确运行授权。本文件下文保留前一准备窗口当时结论，不再作为最新制包状态。旧CLOSE.json不改。

状态：MECHANISM_CANDIDATE_SELECTED / INPUT_LIMIT_RUNTIME_ENV_AND_AUTHORIZATION；不是正式L2/L3或产品能力验收。

预算收尾：准备保守整窗超过自设25分钟，已STOP且未签收；实际数和超出数见evidence/preparation/CLOSE.json。不得把候选资料足够或文档结构有效写成此轮预算通过，也不静默续期。H74R原签收保持。

## 全局位置与结论

H74R已PASS/NOT_APPLICABLE/STOP，本地stored代表切片关闭，原H74拒收及外部采用未知保持。下一关键缺口是原先标作“本地合成”的身份/持有证明能否获得实际发行者和工作负载来源证据。已有SVID消费者与旧参考优先级使SPIRE成为单一资格候选，不必先增加一轮笼统选题讨论。

选择SPIRE作**实际签发/工作负载证明的测量候选**；目前不具备运行就绪条件。Docker/WSL命令存在，Docker客户端29.4.0、Compose5.1.1可读取，但本机Docker Desktop Linux engine管道连接失败，Server版本/OS/架构未取得。不能由命令存在推成daemon/容器可运行；也不能推成整台主机没有其它Linux环境。未启动任何daemon、WSL、容器或服务。

## 现有消费者与真正新增的信息

src/agentic_payment_experiment/trusted_execution/credential_possession.py已有verify_x509_svid_credential_possession：检查直接信任根、SPIFFE URI到Agent/Executor、ECDSA持有证明、时间/nonce防重放；tests/trusted_execution/test_credential_possession.py为既有消费者。当前实现只接受自签的EC信任根直接签叶证书，持有证明用ECDSA-SHA256；不支持任意中间链/RSA持有证明。此次只静态核代码，未运行新产品测试。

SPIRE实际进程可按节点/工作负载选择器签发身份文档，现有模块能成为证据消费端。这是运行机制线索，尚不是本项目的实测结果。[SPIRE Concepts](https://spiffe.io/docs/latest/spire-about/spire-concepts/)

按官方说明，不配置UpstreamAuthority时，SPIRE可自行产生CA并签发SVID。结合EC配置，可作为保持既有direct-root消费边界的候选；**兼容性是推断，必须用实际产物核验，不能预判通过**。[SPIRE Concepts](https://spiffe.io/docs/latest/spire-about/spire-concepts/)、[Server配置](https://spiffe.io/docs/latest/deploying/spire_server/)

## 不能直接照搬官方演示

Docker walkthrough需要构建开发环境，并以UID选择器演示工作负载；示例含disk UpstreamAuthority和公开dummy CA。其角色/命令流程可REFERENCE_ONLY，但不能把示例密钥作为本项目的新鲜信任根，也不能把UID选择器写成精确应用/PID身份认证。[Docker walkthrough](https://spiffe.io/docs/latest/try/spire101/)

本项目若运行，必须新建隔离测试信任域，实际发行者生成新鲜密钥，选择与既有消费者一致的EC/直接根配置；信任bundle须从已明确的本地发行者管理通道固定指纹，不能盲信请求者自带的根。若实测出现中间链或不符profile，记INPUT_LIMIT/不兼容并交Evaluator，不顺手放宽verifier。

Agent官方文档确有Windows服务选项，故不能写成“SPIRE完全不支持Windows”。本轮选择Docker Linux只是最小候选运行路线，Windows原生路线未测。[Agent配置](https://spiffe.io/docs/latest/deploying/spire_agent/)

## 候选来源、许可及版本

- ABSORB：既有消费者、SPIRE实际签发/内核选择器/Workload API的有界实验方法；不引入全套运行时、策略引擎或跨域联合。
- REFERENCE_ONLY：官方quickstart/dummy key/宽泛UID示范；后继应明确其证据上限。
- DEFER：BSN/ATI真实机构身份、真实用户确认、生产PSP、云CA、跨域信任与在线轮换；这些不由一次本地SPIRE运行验证。
- 候选发行版本：v1.16.0，对应提交872c1d55b4d5ac7fc1bf05f0760f2ca740ab37aa，页面变更记录日期2026-11-05。本轮只核版本/源码归属，未下载发行包、镜像、校验和或执行文件；运行前仍须固定所用二进制/镜像digest。[release](https://github.com/spiffe/spire/releases/tag/v1.16.0)、[固定提交](https://github.com/spiffe/spire/commit/872c1d55b4d5ac7fc1bf05f0760f2ca740ab37aa)
- 已核仓库主分支LICENSE标为Apache-2.0；所选发行资产/依赖许可与摘要仍须在运行包准备中逐项锁定，不能假称所有依赖审查已完成。[LICENSE](https://github.com/spiffe/spire/blob/main/LICENSE)

## 下一长包建议边界（尚未冻结）

唯一目标：一套实际SPIRE Server/Agent和一个受控工作负载签发SVID，证书及由持有者生成的挑战签名进入已有验证器；另一个不匹配选择器的工作负载必须取不到同一身份。

建议把环境资格→发行/持有证明→消费与负例→原回归→清理/原始证据放入同一有界包。不得用本地Python再造证书替代SPIRE产物。原始私钥/一次性join token留在隔离私有目录或容器，公开输出只含证书、签名、选择器、指纹和必要进程证据；签名要发生在声明的持有者边界内，不把复制到其它进程的私钥当原进程持有证明。

具体依赖/下载摘要、现有Docker engine启动方式、Linux运行镜像及签名工具链、UID/进程证据边界、服务时长/自动签发观测和清理命令仍未锁定。它们决定是否能安全且可复核地运行，故保持DRAFT。详见RUNTIME_SCOPE_DRAFT.md；不能派Executor或由“继续”推成启动/安装授权。

## 成本与证据

本轮公开网页工具共5次（两次检索/打开组合及来源跟进，非HTTP请求总数），没有额外模型服务；没有下载二进制/镜像。Get-Command与两种Docker只读检查，后者各补抓一次原始返回码，共4次本地CLI元数据调用。Docker version失败、Compose version成功，不能用组合shell最终退出码0代替前一项成功；ENVIRONMENT.json分别记录。

实际主动时间UNKNOWN，整窗保守费用见evidence/preparation/CLOSE.json，与已终态H74/H74R主线分开，不重置其71.862797分钟。正式L2/L3、新产品执行与真实发行均0。

external_requirement_impact: PCAC-AGENTPAY；PCAC-03/05/06及07/08/12/15/20，成熟度不变。真实发行者工作负载事实≠用户付款意愿或真实企业身份；本轮没有强认证、密码学真实来源或监管合规的通过结论。
