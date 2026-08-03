# WebShop 购买轨迹可视化 UI 规划

> 日期：2026-08-02  
> 阶段：未来任务，不进入当前 P9-B1 执行范围  
> 任务编号：`P9-E-WEBSHOP-TRAJECTORY-UI-V1`

## 1. 核心结论

先完成 WebShop 的基础运行、商务对象适配、购买前可信闸门、支付与履约状态、对比评测，再开发 UI。

UI 的定位不是重新执行或编造购买过程，而是：

> **读取真实运行生成的结构化轨迹，把“用户想买什么、Agent 做了什么、商城返回什么、可信系统检查了什么、最终为什么继续或停止”按步骤展示出来。**

执行顺序：

```text
P9-A  WebShop 运行环境与真实轨迹
  ↓
P9-B  Commerce Adapter + Buy Now 前可信闸门
  ↓
P9-C  支付、状态查询、履约与补救
  ↓
P9-D  外部任务与 M5 对比评测
  ↓
P9-E  购买轨迹可视化 UI
```

当前不修改 UI，不打断正在执行和复核的基础能力任务。

## 2. UI 展示的完整购买链路

```text
用户购物需求
  ↓
Agent 读取任务
  ↓
搜索商品
  ↓
查看候选商品
  ↓
点击商品与选择规格
  ↓
Commerce Adapter
  ↓
Order + TransactionRequest
  ↓
授权 / 订单绑定 / Agent 身份 / 来源可信检查
  ↓
ALLOW / DENY / CONFIRMATION_REQUIRED / INDETERMINATE
  ↓
模拟支付状态
  ↓
履约 / 查询 / 补救
  ↓
最终任务结果
```

UI 必须同时展示“商城动作”和“可信支付动作”，不能只展示最终结论。

## 3. UI 页面结构

### 3.1 用户任务区

直接展示：

- 原始购物指令；
- 预算、品类、颜色、用途、数量等可提取条件；
- 哪些内容只是自然语言要求；
- 哪些内容已经形成正式授权；
- 哪些内容仍未确认。

不得把自然语言购物指令直接显示成已授权 `IntentMandate`。

### 3.2 商城环境区

按轨迹步骤展示：

- 当前页面或文本 observation 摘要；
- 搜索词；
- 搜索结果数量；
- 候选商品编号、名称、价格与选项；
- 实际点击的商品；
- 当前可执行动作；
- `reward`、`done`、购买计数等环境返回值。

第一版使用文本商品卡片，不依赖图片或浏览器自动化。

### 3.3 Agent 轨迹区

提供：

```text
上一步 / 下一步 / 自动播放 / 暂停 / 回到起点
```

每一步固定展示：

- 步骤编号；
- 执行主体；
- 输入事实；
- 执行动作；
- 输出事实；
- 环境反馈；
- 证据来源；
- 本步骤明确没有做什么。

只展示结构化行动记录和选择依据摘要，不展示或伪造隐藏思维链。

### 3.4 可信支付区

按层展示：

```text
Adapter
→ Facts
→ Trust / Binding
→ State
→ Policy
→ Action
```

具体显示：

- WebShop 字段如何映射成 `Order`；
- 如何形成 `TransactionRequest`；
- 商品、金额、商户、收款方、授权引用是否一致；
- Agent 声明身份是否匹配；
- 页面和上下文来源是否可信；
- 最终决策及原因；
- 是否要求人工确认；
- 是否产生了购买、支付或履约副作用。

### 3.5 结果与异常区

直接显示：

- 用户需求与选中商品是否匹配；
- 是否发生涨价、换商品、换商户或换收款方；
- 是否错误放行、错误拒绝或漏确认；
- 支付与履约状态；
- 最终任务成功、失败、等待或需要人工处理；
- M5 评测结果。

## 4. 轨迹数据契约

UI 只读取机器生成的轨迹文件，不从日志文字猜测过程。

统一轨迹至少包含：

```text
run_id
scenario_id
source_commit
source_asset_hashes
user_instruction
normalized_constraints
steps[]
selected_product
order
transaction_request
checks[]
decision
payment_state
fulfillment_state
final_task_state
side_effects
limitations
evidence_refs
```

每个 `steps[]` 至少包含：

```text
sequence
stage
actor
action
input_facts
output_facts
observation_summary
available_actions
reward
done
timestamp_or_sequence_marker
evidence_hash
```

轨迹必须区分：

- WebShop 原始事实；
- Agent 生成的动作；
- 实验上下文补充字段；
- Commerce Adapter 输出；
- Trust Control Plane 检查结果；
- 模拟支付和履约结果。

不同来源不得在 UI 中混成一个“已验证事实”。

## 5. 当前已有的输入基础

P9-A2 已经生成真实 WebShop 轨迹，包括：

```text
reset
→ search
→ product click
→ pre-Buy-Now
→ reset
```

已有字段包括：

- session；
- 用户指令；
- 实际动作；
- 搜索结果；
- 点击商品；
- observation 摘要和 SHA-256；
- reward / done；
- Buy Now 是否出现；
- Buy Now 是否执行；
- purchase count；
- 第二次 reset 状态。

P9-B1 已开始补充：

```text
instruction_text
+ 当前商品 / 选项 / 价格
+ 显式实验上下文
→ Order + TransactionRequest
```

这些内容以后都作为 P9-E 的真实输入，不需要重新手工编一套 UI 演示数据。

## 6. 验证方式

UI 展示正确性通过四层验证：

### 6.1 轨迹真实性

```text
真实环境运行
→ 生成轨迹 JSON
→ 保存源码提交、数据哈希和动作序列
```

### 6.2 数据一致性

UI 展示的每个关键字段必须能回指：

- 原始轨迹字段；
- Adapter 输出；
- 规则检查证据；
- 支付或履约状态记录。

### 6.3 回放一致性

相同轨迹文件重复打开时：

- 步骤数量一致；
- 动作顺序一致；
- 商品、金额和决策一致；
- 不产生新的购买或支付副作用。

### 6.4 独立评估

评估者从原始 JSON 与 UI 导出结果分别读取关键字段，验证：

```text
UI 展示值 == 原始证据值
```

UI 不作为事实源，也不参与计算最终决策。

## 7. 第一版验收目标

P9-E V1 只要求：

1. 从一份真实轨迹 JSON 生成 WebShop 专属页面；
2. 支持逐步、自动播放和回到起点；
3. 展示用户任务、搜索、候选、点击商品和 Buy Now 前状态；
4. 展示 Commerce Adapter 的 `Order + TransactionRequest`；
5. 展示购买前可信检查和最终四态决策；
6. 每个页面字段可以回指原始证据；
7. UI 回放不运行 WebShop、不执行 Buy Now、不支付；
8. 明确标记“固定脚本轨迹”或“自主 Agent 轨迹”，不得混淆。

## 8. 明确排除

P9-E V1 不做：

- 让 UI 直接控制 WebShop；
- 浏览器自动化；
- 真实支付、钱包或测试网；
- 在前端重新计算授权决策；
- 从自然语言自动补造缺失证据；
- 展示隐藏思维链；
- 把固定 smoke 脚本标成自主智能体；
- 为了 UI 修改第三方 WebShop 源码。

## 9. 自主智能体购物的后续边界

“轨迹可视化 UI”和“自主购物 Agent”是两个不同能力：

```text
P9-E UI
= 读取并展示已有真实轨迹

后续自主 Agent
= 根据用户任务自己生成搜索词、比较商品、选择商品和选项
```

只有当 Agent 决策层真正接入后，UI 才能把轨迹类型标记为：

```text
AUTONOMOUS_AGENT
```

在此之前必须标记为：

```text
DETERMINISTIC_SMOKE
或
FIXED_REPLAY
```

## 10. 最终定位

```text
轨迹 JSON = 原始证据
可信系统 = 决策与状态来源
UI = 可验证的证据播放器
```

UI 的价值是让普通用户看懂一次购买经过了哪些环节、系统在哪里发现问题、为什么允许或阻止，而不是用漂亮页面代替真实能力和真实证据。
