# agentic-payment-trust-lab — Agent Rules

<!-- BEGIN localagent-common:codexpro-shell-safety -->
## CodexPro Shell 与文件落盘安全

- Markdown、YAML、JSON 等文本文件优先使用文件 `write/edit` 工具，不使用 `echo`、`printf`、`cat` 或 Here-doc 拼接完整正文。
- 命令中包含反引号、`$()`、复杂正则、多层引号或多行脚本时，先把脚本写入文件，再通过 Bash 执行该脚本。
- Bash 只负责执行命令和检查结果，不承担富文本模板渲染。
- 批量生成或修改文件后，提交前必须检查关键标题、关键标识、文件数量和 `git diff`，防止内容被 Shell 展开或转义破坏。
- Windows 路径调用优先使用项目已验证的命令形式；不要在同一条命令中混合 PowerShell、cmd、WSL Bash 多层转义。
<!-- END localagent-common:codexpro-shell-safety -->
