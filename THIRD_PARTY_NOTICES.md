# Third-Party Notices

本仓库包含少量经过归一化或固定快照处理的第三方开放资料。它们不因本仓库采用 Apache-2.0 而改变各自原始许可证。

## AP2

- 上游：`google-agentic-commerce/AP2`
- 用途：HP / HNP 最小协议对象快照与适配实验
- 本地位置：`samples/protocol_snapshots/AP2_v020_HP_cards.json`、`samples/protocol_snapshots/AP2_v020_HNP_cards.json`
- 来源版本、提交与许可证信息记录在各快照 `_source` 字段中
- 上游许可证：Apache-2.0

## PayBench / Unsafe Commercial Autonomy

- 上游：`conorplunkett/Unsafe-Commercial-Autonomy`
- 固定提交：`f052ab411f28e79c73f3897029a017f29f5cd4e2`
- 用途：第一批 5 组 × 2 个外部危险案例 / 安全对照
- 本地位置：`samples/external/paybench/phase1_selected_10.json`
- 上游许可证：MIT
- 本仓库保存的是紧凑归一化切片，不是完整 benchmark runtime

## AgentDojo

- 上游：`ethz-spylab/agentdojo`
- 参考版本：`v0.1.35` / `a75aba7`
- 用途：只借鉴“正常任务 + 不可信注入覆盖层 + 同一评测器”的实验方法
- 本地位置：`samples/attacks/attack_overlay_v1.json`
- 上游许可证：MIT
- 本仓库没有复制或集成 AgentDojo runtime

## 第三方 PDF

Sunrate / Mastercard 白皮书及中国银联规范仅作为本地研究资料使用。公开仓库不再分发这些原始 PDF，仅保留：

- 文档名称；
- 来源说明；
- SHA-256；
- 本项目的分析与边界说明。

本地原件存放于 Git 忽略目录 `local_sources/third_party/`，不属于公开仓库内容或运行依赖。
