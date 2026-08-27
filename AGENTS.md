# agentic-payment-trust-lab — Agent Rules

## 当前战略定位

- 本仓是 **高风险交易 / 智能体支付信任验证场，也是当前最严格的 Security（安全）压力测试场**。当前已验证重点是 Identity Binding / Identity Assurance（身份绑定 / 身份保证）、Authorization / Delegation（授权 / 委托）、Binding（绑定）、Policy（策略）、Context / Tool Integrity（上下文 / 工具完整性）、Confirmation（确认）、Idempotency / Replay（幂等 / 重放防护）与 Audit / Recovery（审计 / 恢复）；Strong Authentication（强认证）、Credential / Key Governance（凭据 / 密钥治理）与 Cryptographic Signature Verification（密码学签名验证）仍是待真实证据验证的能力，不得写成已覆盖。
- 支付业务规则和状态机留在本仓；只有跨领域第二消费者已证明重复的安全 / 控制机制，才考虑回抽 Enterprise Agent Control Plane（企业智能体控制平面）。
- Blockchain（区块链）不是项目主线。只有 Wallet / Key / Credential、Signature + Transaction Binding、Nonce / Replay Protection、Verifiable Transaction / Finality、跨主体 Audit / Settlement Evidence 等具体问题有真实消费者和负向测试时才进入候选；普通签名、审计日志、幂等键或现有支付网络足够时默认不用链。
- Token / 发币 / DeFi / 共识 / 智能合约 / 全量上链默认 `REFERENCE_ONLY（只参考）`，除非明确证明它们是解决当前 Trust Contract 的最小必要机制。
- 不扩张为通用 Agent Runtime，也不把生产支付 / 真实资金接入作为当前目标。

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
