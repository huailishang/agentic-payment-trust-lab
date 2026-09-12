# agentic-payment-trust-lab — Agent Rules

## 当前战略定位

- 本仓是 **高风险交易 / 智能体支付信任验证场，也是当前最严格的 Security（安全）压力测试场**。当前已验证重点是 Identity Binding / Identity Assurance（身份绑定 / 身份保证）、Authorization / Delegation（授权 / 委托）、Binding（绑定）、Policy（策略）、Context / Tool Integrity（上下文 / 工具完整性）、Confirmation（确认）、Idempotency / Replay（幂等 / 重放防护）与 Audit / Recovery（审计 / 恢复）；Strong Authentication（强认证）、Credential / Key Governance（凭据 / 密钥治理）与 Cryptographic Signature Verification（密码学签名验证）仍是待真实证据验证的能力，不得写成已覆盖。
- 支付业务规则和状态机留在本仓；只有跨领域第二消费者已证明重复的安全 / 控制机制，才考虑回抽 Enterprise Agent Control Plane（企业智能体控制平面）。
- Blockchain（区块链）不是项目主线。只有 Wallet / Key / Credential、Signature + Transaction Binding、Nonce / Replay Protection、Verifiable Transaction / Finality、跨主体 Audit / Settlement Evidence 等具体问题有真实消费者和负向测试时才进入候选；普通签名、审计日志、幂等键或现有支付网络足够时默认不用链。
- Token / 发币 / DeFi / 共识 / 智能合约 / 全量上链默认 `REFERENCE_ONLY（只参考）`，除非明确证明它们是解决当前 Trust Contract 的最小必要机制。
- 不扩张为通用 Agent Runtime，也不把生产支付 / 真实资金接入作为当前目标。

## Evaluator 全局视角与回复规范

评估者不能只围绕当前 `H-*` / `P9-*` 任务做局部复核。每次 Evaluator（评估者）对 Human/Task Owner 汇报、复核、布置下一任务时，必须先从项目全局定位当前任务，再进入细节。

每次回复至少先用简短版列清楚下面 5 项：

```text
1. 项目最终目标：这个仓库最终要证明什么
2. 全局能力路线：已经完成哪几个大阶段，当前处在哪一阶段
3. 当前第一瓶颈：具体卡在哪里，为什么它比其他 WATCH / DEFERRED 缺口更优先
4. 本轮任务作用：当前 H-* / task 只是在测量、修复，还是建设这个瓶颈的能力
5. 下一步条件：什么证据会让我们 CONTINUE / STOP / SWITCH，以及后面大概还有哪些阶段
```

默认使用下面这条项目级能力路线作为“地图”，不得只按任务编号顺序理解项目：

```text
A. 评测与治理底座
→ B. 授权、绑定、来源、执行前治理
→ C. 支付生命周期、恢复、补救与证据连续性
→ D. 责任归因、Read Model、Consumer / Player 可消费审计链
→ E. Actor Authenticity / Credential / Signed Instruction 真实性验证
→ F. 外部真实协议 / SDK / 网络 / 钱包 / 测试网接入（有授权时）
```

当前各阶段状态必须从 `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md` 的最新 revision 读取，不得凭历史聊天猜测。

### 第一瓶颈怎么选

评估者选择下一瓶颈时按以下顺序判断，不按“哪个模块好做”或“编号排到哪里”推进：

```text
项目目标与零容忍风险
→ 端到端能力链中尚未被代表性证据闭合的最前/最关键缺口
→ 影响范围与风险严重度
→ 当前证据置信度（measured / estimated / unknown）
→ 修复或测量成本、复杂度、外部授权依赖
→ 与次优瓶颈比较后的 expected project value（预期项目价值）
```

具体规则：

- 已经 `STAGE_CLOSED（阶段关闭）` 的方向默认不继续加 Case、字段或 UI，除非出现新的反例或外部要求改变。
- `WATCH（观察）` 可以是真缺口，但如果只影响少量剩余 Case、已有代表性覆盖，且不是零容忍安全边界，就不能仅因为容易修而抢占第一瓶颈。
- `DEFERRED（延期）` 如果依赖真实网络、生产凭证、钱包、测试网或额外授权，在条件未满足前不能成为执行主线。
- 对“可能是大能力缺口、但还没有系统证据”的方向，先派 `measurement-only（只测量）`；只有测出重复共同断点，才允许形成 capability package（能力建设包）。
- 一个方向即使 `PASS` 或 `IMPROVED`，如果代表性链路已经闭合、边际收益明显下降，也应 `STOP` 或 `SWITCH`，不能因为还能继续加测试就继续做。

### Evaluator 汇报固定开头

以后 Evaluator 回复默认先给一段不超过约 10 行的“全局位置”，格式可简化，但信息必须齐全：

```text
全局路线：A[完成] → B[完成] → C[完成] → D[完成] → E[当前] → F[未来/受授权约束]
当前瓶颈：B-xx ...
为什么是它：...（同时说明为什么不是最强的 1-2 个备选瓶颈）
本轮任务：H-xx，属于 measurement / capability / repair 中哪一种
完成判据：...
下一步：如果结果 A → CONTINUE；如果结果 B → SWITCH/STOP
```

然后再展开 L2/L3、AC、hash、测试数等局部证据。禁止让任务编号和验证细节淹没项目全局位置。

<!-- BEGIN localagent-common:codexpro-shell-safety -->
## CodexPro Shell 与文件落盘安全

- Markdown、YAML、JSON 等文本文件优先使用文件 `write/edit` 工具，不使用 `echo`、`printf`、`cat` 或 Here-doc 拼接完整正文。
- 命令中包含反引号、`$()`、复杂正则、多层引号或多行脚本时，先把脚本写入文件，再通过 Bash 执行该脚本。
- Bash 只负责执行命令和检查结果，不承担富文本模板渲染。
- 批量生成或修改文件后，提交前必须检查关键标题、关键标识、文件数量和 `git diff`，防止内容被 Shell 展开或转义破坏。
- Windows 路径调用优先使用项目已验证的命令形式；不要在同一条命令中混合 PowerShell、cmd、WSL Bash 多层转义。
<!-- END localagent-common:codexpro-shell-safety -->

## 外部 Benchmark / Trace Dataset 规则

- 只有当当前 Trust / Security 瓶颈缺独立评测样本、缺真实攻击 / 失败 Trace（轨迹）、新方向没有明确实现依据，或需要证明修复能跨 Case 泛化时，才主动检查 Hugging Face / ModelScope 上的 Benchmark（基准集）或 Trace Dataset（轨迹数据集）。已有固定场景和 Checker 可直接验证的普通小修不触发额外数据调研。
- 优先关注 agent/tool security、authorization misuse、prompt/context tampering、transaction/intent binding、policy violation、tool-call trace、fraud/anomaly 与 adversarial agent 数据；但“信用卡欺诈数据集”只有在能验证本项目 Trust Contract（信任合同）时才可吸收，不能因为同属支付领域就直接采用。
- 候选统一标记 `ABSORB（吸收） / REFERENCE_ONLY（只参考） / REJECT（不采用）`，检查许可证、是否含真实敏感支付数据、攻击样本真实性、Gold/Checker、trace 完整度、是否能映射到 ALLOW/DENY/WAIT/CONFIRM/QUERY/RETRY 与现有 P1-P5 / Fact Lineage。
- 模型生成 CoT（思维链）、无来源支付样本、只有 fraud score（欺诈分数）但缺少授权/绑定/执行证据的数据默认只作参考或拒绝；优先采用可回放、可判定、可形成 attack overlay / regression case（攻击覆盖层 / 回归案例）的数据。

## 智能体支付外部要求基线

- 涉及 Agent 身份、授权、支付执行、风险控制、证据、回放、安全评测的新增任务，必须先检查 `docs/reference/05_产业与机构资料/pcac/智能体支付应用自律公约_开发指标映射_v1.md`。
- 任务包应记录 `external_requirement_impact`：`profile=PCAC-AGENTPAY`、关联 `PCAC-*`、适用性、成熟度 before/after、Test、Evidence、残余风险。
- 只有 `CORE` 项进入强制开发 / 回归指标；机构级 `REFERENCE_ONLY` / `ADAPTER` 要求不得机械实现成同名模块。
- 任一 `CORE` 能力声称已覆盖时，必须同时能指出对象 / Contract、代码、Test 和 Evidence；不得把项目能力表述成监管合规结论。
- 《公约》是重要外部验收基线之一，不替代项目瓶颈优先级，也不替代 AP2 / ACP / UCP / x402 / APOP / ACT 等协议与产业参考。
