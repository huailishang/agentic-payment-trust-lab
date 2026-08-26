# agentic-payment-trust-lab — Agent Rules

<!-- BEGIN localagent-common:codexpro-shell-safety -->
## CodexPro Shell 与文件落盘安全

- Markdown、YAML、JSON 等文本文件优先使用文件 `write/edit` 工具，不使用 `echo`、`printf`、`cat` 或 Here-doc 拼接完整正文。
- 命令中包含反引号、`$()`、复杂正则、多层引号或多行脚本时，先把脚本写入文件，再通过 Bash 执行该脚本。
- Bash 只负责执行命令和检查结果，不承担富文本模板渲染。
- 批量生成或修改文件后，提交前必须检查关键标题、关键标识、文件数量和 `git diff`，防止内容被 Shell 展开或转义破坏。
- Windows 路径调用优先使用项目已验证的命令形式；不要在同一条命令中混合 PowerShell、cmd、WSL Bash 多层转义。
<!-- END localagent-common:codexpro-shell-safety -->

## 智能体支付外部要求基线

- 涉及 Agent 身份、授权、支付执行、风险控制、证据、回放、安全评测的新增任务，必须先检查 `docs/reference/05_产业与机构资料/pcac/智能体支付应用自律公约_开发指标映射_v1.md`。
- 任务包应记录 `external_requirement_impact`：`profile=PCAC-AGENTPAY`、关联 `PCAC-*`、适用性、成熟度 before/after、Test、Evidence、残余风险。
- 只有 `CORE` 项进入强制开发 / 回归指标；机构级 `REFERENCE_ONLY` / `ADAPTER` 要求不得机械实现成同名模块。
- 任一 `CORE` 能力声称已覆盖时，必须同时能指出对象 / Contract、代码、Test 和 Evidence；不得把项目能力表述成监管合规结论。
- 《公约》是重要外部验收基线之一，不替代项目瓶颈优先级，也不替代 AP2 / ACP / UCP / x402 / APOP / ACT 等协议与产业参考。
