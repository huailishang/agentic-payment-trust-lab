# AgentEmulator：低优先级实验环境参考

日期：2026-09-21。分类：`REFERENCE_ONLY`。用户决定：仅收录参考，不列入首批外部验证对象。

## 作用与证据

把预先编写的 join / pay / leave 行为编译为交易，在 BlockEmulator-X 中回放并输出结果图表，主要服务 Agent × 区块链机制实验。

本轮静态审查版本：`db6b0c1130ddc1befd9f368a122edc9b27c21f4c`；GitHub API 标识许可证为 MIT。未安装、未运行，未做完整依赖或数据审计。

- [官方 README](https://github.com/HuangLab-SYSU/agent-emulator/blob/db6b0c1130ddc1befd9f368a122edc9b27c21f4c/README.md)：FAQ 说明身份合约尚未部署，记录调用不等于实际身份合约状态管理；确定性输出不包括不受运行条件影响的打包时序。
- [registry.go](https://github.com/HuangLab-SYSU/agent-emulator/blob/db6b0c1130ddc1befd9f368a122edc9b27c21f4c/agentsupervisor/registry.go)：seed 与 agent_id 派生 DID，不构成主体真实性或密钥持有证明。
- [trace.go](https://github.com/HuangLab-SYSU/agent-emulator/blob/db6b0c1130ddc1befd9f368a122edc9b27c21f4c/agentsupervisor/trace.go)：按 ts 排序，相同 ts 保留行序。
- [agentsupervisor.go](https://github.com/HuangLab-SYSU/agent-emulator/blob/db6b0c1130ddc1befd9f368a122edc9b27c21f4c/agentsupervisor/agentsupervisor.go)：支付编译路径检查双方 active 并生成交易，未按 request_id 去重；递增 nonce 不等于业务幂等。支持 raw_tx，未来适配需要防止绕过治理入口。

## 为什么当前不接入

当前 B-06 / H-39 需要支付宝真实 Provider 观察证据，仿真账本无法替代。已有 runner、Trace Consumer / Player 覆盖相近实验组织需求；引入新运行环境尚无已测量的项目收益。

可借鉴固定输入、动作到交易关联、实验输出展示的方法；不新增产品模块，不重新建设已关闭能力，不把仿真 DID 升为 VERIFIED，不引入发币或全量上链。

重新评估条件：出现现有环境无法表达的跨主体结算、时序或证据问题，而且可冻结独立 checker 与负例。仅重复正常支付或增加图表则 STOP。

未来试验需明确合成数据来源、初始状态、版本和依赖；外部源码不自动构成独立攻击基准。所有仿真结果必须与真实 Provider 证据分开。

首批验证顺序见 [F 阶段路线](../../02_未来规划/F阶段公开验证路线_20260917.md)。
