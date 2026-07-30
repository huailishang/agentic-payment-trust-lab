# Agentic Payment Trust Lab

**智能体支付可信实验室**：一个本地、离线、可重复的智能体支付安全与可信执行实验项目。

> 仓库名与公开项目名统一为 `agentic-payment-trust-lab`。项目面向通用智能体支付授权、安全、可信执行与评测，不局限于信用卡。

本项目不教智能体“怎样更快付款”，而是重点研究：

```text
Agent 凭什么可以付？
        ↓
授权边界有没有被越过？
        ↓
订单、商户、金额和执行对象有没有变化？
        ↓
什么时候必须拒绝 / 询问用户 / 暂停判断？
        ↓
支付状态不确定时怎样避免重复扣款？
        ↓
外部网页或工具内容能不能篡改可信支付输入？
        ↓
事后能不能用确定性证据解释当时为什么这样判断？
```

本项目只用于学习、研究、回放和开发者验证，不接生产支付、真实银行卡、真实客户数据、真实资金、生产私钥或清算网络。实验通过不等于生产安全、业务合法或监管合规。

## 当前能力

### 1. 交互式支付风险实验

S01—S13 固定场景覆盖：

- 委托边界、预算、商户、品类、次数和有效期；
- 重复请求与人工确认；
- 订单价格 / 商品变化与重新确认；
- 支付成功但履约失败；
- 退款、部分退款与争议；
- 支付状态 `UNKNOWN` 后查询原交易并防止盲目重复扣款；
- 声明 Agent 标识与委托预期标识不一致。
- P1：用户确认的具体订单摘要、确认有效期与付款前 fail-closed 核验；关键交易内容或授权版本变化时不复用旧确认。

启动交互实验台：

```powershell
python run_experiment.py --serve --open
```

页面主线保持简单：

```text
选择 M2 / M3 / M4 / M5 / Attack Overlay
    ↓
选择对应场景 / 流程
    ↓
查看当前模块与场景结果
    ↓
M2 时继续展开 S01—S13 交互实验、生命周期矩阵和关键环节
```

### 2. 一仓两域

```text
支付域
  委托、订单、支付、履约、退款、争议、恢复、协议适配、UI
        |
        | 单向调用
        v
可信执行域
  规范化、Hash、Binding、Execution Facts
```

核心边界：

> **可信执行负责证明“发生了什么”，支付域负责决定“应该怎么办”。**

例如：

```text
Binding INVALID
!= 自动 DENY

Idempotency VALID
!= 自动允许再次扣款

声明标识 VALID
!= 真实身份认证已经成立
```

当前已实现：

- TE01：哈希（Hash）；
- TE02：规范化（Canonicalization）；
- TE03：对象绑定（Binding）；
- TE04：执行身份、状态观察与幂等事实（Execution Facts）。
- P1：确认记录与确认—订单绑定事实（Confirmation Binding），已接入 S09 与主验证路径。

### 3. 外部协议与外部挑战

当前接入的最小外部验证切片：

- **AP2**：HP / HNP 两个官方最小流程快照；
- **PayBench**：第一批 5 组 × 2 个危险案例 / 安全对照；
- **Attack Overlay v1**：不可信网页 / 工具文本尝试越权改写可信支付字段。

当前基线：

| 模块 | 当前结果 | 作用 |
|---|---:|---|
| S01—S13 内部回归 | 13/13 | 防止已有能力回归 |
| AP2 HP/HNP | 2/2 | 验证外部协议对象能映射到中立模型 |
| Attack Overlay v1 | 5/5 | 验证不可信内容不能直接改写可信支付输入 |
| PayBench | 8/10 可执行 | E1 已接入 Attack Overlay；当前只剩 D1 隐私披露 2 个未覆盖挑战 |

PayBench 的 `PARTIAL` 是刻意保留的真实缺口，不用“已支持部分全过”冒充完整覆盖。

### 4. M5 统一评测

评测不只看最终枚举是否一致，还检查：

```text
决策是否正确
错误放行
错误拒绝
漏人工确认
在证据不足时是否过度武断
是否产生禁止副作用
```

当前完整自动化回归为 **200 tests OK**；P1 核心、验证器与主结果专项为 **32 passed（含 4 个 subtests）**。正式入口中 S01—S13 为 **13/13 PASS**，内部冻结基线和 M5 均通过。它证明当前离线实现和固定证据契约一致，但不等于生产支付安全。

## 本地运行

推荐 Python 3.10+。Windows 下可使用 Conda 环境。

生成静态实验结果：

```powershell
python run_experiment.py
```

日常使用只需要启动统一交互实验台：

```powershell
python run_experiment.py --serve --open
```

下面三个脚本是开发 / 排查时使用的专项验证入口，不是普通用户的启动入口：

```powershell
python scripts/validation/run_paybench_challenges.py --current-rules
python scripts/validation/run_ap2_protocol_samples.py
python scripts/validation/run_attack_overlays.py
```

运行全量测试：

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## 项目结构

```text
.
├── run_experiment.py              # 唯一正式入口
├── scripts/validation/            # 开发 / 排查专项验证工具
│   ├── run_paybench_challenges.py
│   ├── run_ap2_protocol_samples.py
│   └── run_attack_overlays.py
├── src/agentic_payment_experiment/
│   ├── adapters/                 # 外部协议 -> 中立模型
│   ├── trusted_execution/        # 确定性可信事实
│   ├── validator.py              # 付款前业务规则
│   ├── lifecycle.py              # 支付生命周期
│   ├── payment_recovery.py       # UNKNOWN / PENDING 恢复
│   ├── evaluator.py              # M5 统一评测
│   └── interactive_server.py     # 本地交互实验服务
├── samples/
│   ├── scenarios/                # S01—S13
│   ├── regression/               # 内部冻结基线
│   ├── protocol_snapshots/       # 固定协议样品
│   ├── external/paybench/        # PayBench 最小归一化挑战
│   └── attacks/                  # Attack Overlay
├── tests/
└── docs/
```

## 第三方资料处理

公开仓库只保留来源、版本、许可证、摘要、哈希和本项目分析；**不再分发第三方原始 PDF**。

本地研究原件统一放在被 Git 忽略的：

```text
local_sources/third_party/
```

历史开发执行包、复评过程和早期规划**不随本公开仓库分发**。公开仓只保留当前架构、验证方法、可运行样品和仍有效的研究结论。

## 设计原则

1. 协议先映射到中立模型，Adapter 不修改核心业务语义。
2. 可信执行域只返回确定性验证事实，不定义支付业务裁决。
3. 每新增一个可信能力，必须由真实场景或外部失败证明其必要性。
4. 外部 benchmark 用来暴露缺口，不为追求分数反向污染业务边界。
5. 固定外部协议 / benchmark 版本，避免上游变化悄悄改变实验结果。
6. 默认使用合成数据、本地离线环境和测试密钥。

## 下一步

```text
PayBench 当前 8/10 可执行
        ↓
M3-C1：E1 提示注入 × Attack Overlay【已完成】
    ↓
P1 Delegated Authority v1【已完成】
    ↓
P2：把 Authority → Order 的绑定继续延伸到 Payment Request / Payment Execution
    ↓
仍不直接跳去 S14 / D1，也不重构主 UI
```

## 文档

- [项目中控](docs/01_项目现状/项目中控.md)
- [总体架构](docs/03_架构设计/总体架构.md)
- [模块化实验与评测路线](docs/02_未来规划/模块化实验与评测路线.md)
- [支付生命周期异常矩阵](docs/03_架构设计/支付生命周期异常矩阵.md)
- [支付与可信执行模块边界](docs/03_架构设计/支付与可信执行模块边界.md)
- [P1 授权绑定与执行前核验执行记录](docs/04_验证体系/P1授权绑定与执行前核验执行记录_20260730.md)
- [外部项目与开源参考台账](docs/reference/开源项目台账.md)

## License

本项目代码以 [Apache License 2.0](LICENSE) 发布。第三方协议样品、benchmark 归一化数据和参考资料遵循其各自来源许可证与使用条款；来源信息保留在对应目录或资料台账中。
