# Executor Report

Task ID: `P9-WEBSHOP-SMALL-RUNTIME-SMOKE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
Contract amendment: `A1-CHECKSUM-VERIFIED-MIRROR-FALLBACK`  
Executor status: `READY_FOR_REVIEW`  

```yaml
executor_state: READY_FOR_REVIEW
current_role: Evaluator
review_requested: true
commit_performed: false
push_performed: false
history_rewrite_performed: false
buy_now_executed: false
```

## 1. 执行结论

P9-A2 的功能与安全验收已经完成：

```text
固定 WebShop checkout
→ 独立 webshop38 / Python 3.8.13 / OpenJDK 11
→ 固定 revision 镜像下载到 staging
→ 大小 / SHA-256 / JSON 类型 / 条数全量校验
→ 原子迁入三份 small 数据
→ resources_1k / indexes_1k
→ Lucene 真实查询
→ reset → search → 商品点击 → Buy Now 前停止 → reset
```

真实运行结果：

- Lucene 查询返回 10 条结果；
- `WebAgentTextEnv-v0` 两次 reset 均成功；
- 执行了 `search[vhomes lights reclaimed]`；
- 点击商品 `b06y3vldfb`；
- 到达 `Buy Now` 可用状态；
- 没有执行 `click[buy now]`；
- 购买计数为 0，第二次 reset 没有保留购买状态。

工作流预验证已无 `BLOCKING`，当前候选包已进入 `READY_FOR_REVIEW`；尚未开始 P9-B。

## 2. 工作区快照

| 项目 | 结果 | 证据 |
|---|---|---|
| 主仓 HEAD | `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`，与基线一致 | EV-34 |
| WebShop checkout | `64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`，detached 且 clean | EV-34 |
| `webshop38` | `<LOCAL_SOFTWARE>\Anaconda\workspace\.conda\envs\webshop38` | EV-19、EV-34 |
| Python | 3.8.13 | EV-19、EV-31、EV-34 |
| Java | OpenJDK 11.0.30，环境内安装 | EV-19、EV-34 |
| 共享 `agent` 指纹 | 前后均为 `4539e11540ef6bdae7d4ce8adc6e9cc9c1b45891a36a5218ece046db3ad1622c` | EV-19、EV-34 |
| WebShop 数据/索引 | 主仓 Git 忽略，嵌套上游状态仍为 clean | EV-34 |
| 根目录临时 venv 外壳 | 不存在 | EV-34 |

主仓工作树原本已包含 P4—P9 和产品代码的继承改动；本任务没有回滚、覆盖或据为本轮产出。

## 3. 改动文件

本轮实现和状态文档：

| 文件 | SHA-256 | 作用 |
|---|---|---|
| `scripts/validation/webshop/bootstrap_webshop_small.ps1` | `164d16b44d30714c790fa0097a00466e3e76f8ad628ac98836adfc950d779169` | 隔离环境、固定依赖、显式镜像 fallback、staging 校验、1k 索引和 smoke 入口 |
| `scripts/validation/webshop/verify_webshop_small_assets.py` | `c8e8d49de928c87710317cc88f77d253f1411cd6389e019f855813a82feff571` | 固定来源/哈希/结构门禁、原子 promotion、资源构建、索引查询 |
| `scripts/validation/webshop/smoke_webshop_small.py` | `8628023cbee0c131ff496f0810090d6cc1fb8509cda0333b9474a19aa47d953d` | 真实文本环境 smoke，禁止 Buy Now |
| `tests/test_webshop_small_runtime_contract.py` | `e3617c9a0f8e30b1c7f92848c4c8d6b05a5a07f7826bbe1adeabd37a072f6f13` | 14 项 fail-closed 合同测试 |
| `docs/reference/04_商城与外部环境/WebShop外部商城接入分析与分批执行路线_20260801.md` | `e5dbed07c0c6f6204f3b78d0a16d4a46b4eb4a110741a7377b86295de968a12c` | 更新 P9-A2 事实状态和 P9-B 边界 |
| `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md` | `9da59f0ebca51a180e3be623814eeb666f4cc8d42cd9eba237616552359ad808` | 更新验证路线状态 |

评估者修改并冻结的合同：

| 文件 | SHA-256 |
|---|---|
| `docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/CONTRACT.md` | `cf00f3174a070c816d2ad5678ad743f3d967afc7a357a4730e1531c92a2b98ff` |

`REPORT.md`、`CURRENT.md` 和 `evidence/` 属于工作流状态与证据产物，不纳入自引用文件哈希表。

## 4. 隔离环境与依赖

最终关键版本：

| 组件 | 版本 |
|---|---:|
| Python | 3.8.13 |
| OpenJDK | 11.0.30 |
| Gym | 0.24.0 |
| Flask / Werkzeug | 2.1.2 / 2.1.2 |
| spaCy / `en_core_web_sm` | 3.3.0 / 3.3.0 |
| Pyserini | 0.17.0 |
| Torch | 1.11.0 CPU |
| Faiss CPU | 1.7.4 |
| NumPy | 1.23.5 |
| Pandas | 1.4.2 |
| MKL / Intel OpenMP | 2021.4.0 / 2021.4.0 |
| Transformers | 4.19.2 |
| ONNX Runtime | 1.12.1 |
| PyYAML | 6.0 |

完整 `conda list`、`conda list --explicit` 和 `pip freeze` 保存在 EV-34。

## 5. 数据恢复与来源边界

本轮数据必须表述为：

> checksum-verified mirror copies of the WebShop small assets

实际来源：

```text
repository: YWZBrandon/webshop-data
revision: ce990fff5aee388db2706f07820c578ab68e0453
```

三个文件只在 staging 校验全部通过后迁入：

| 文件 | 字节数 | SHA-256 | JSON 类型 / 条数 |
|---|---:|---|---|
| `items_shuffle_1000.json` | 4,467,013 | `30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269` | list / 1,000 |
| `items_ins_v2_1000.json` | 147,099 | `f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f` | dict / 1,000 |
| `items_human_ins.json` | 5,137,548 | `cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3` | dict / 10,136 |

机器可读结果：`evidence/webshop_small_mirror_assets.json`，SHA-256 为 `8e9208f962f8061d42e5146545443a465427e0098d705cae4f75e950c87f3548`。

该授权只用于本地 smoke，不证明 Princeton 或 Google Drive 的当前官方分发来源，也不授权发布、再分发或生产使用。

## 6. 1k 资源、索引与查询

仅生成：

```text
search_engine/resources_1k/
search_engine/indexes_1k/
```

结果：

- `documents.jsonl`：1,000 条，SHA-256 `2014b89a9cd72b3790632e488cc6b8a5bc6c7484af5073e95df5308bac59c275`；
- `indexes_1k`：19 个文件；
- 禁止的 full / 100 / 100k 资源和索引目录均不存在；
- 查询词：`vhomes lights reclaimed`；
- 返回 10 条结果；
- 第一条：`B06Y3VLDFB`，分数约 `10.5262`。

机器可读查询结果：`evidence/webshop_small_index_query.json`，SHA-256 为 `e5f0d26246e2d063c6106f61068c3cce9f97d67589c97da7ee0bf945291fcc78`。

## 7. 真实 WebShop smoke

实际动作：

```text
reset
→ search[vhomes lights reclaimed]
→ click[b06y3vldfb]
→ Buy Now 可用
→ 不执行 click[buy now]
→ reset
```

验证结果：

- `gym`、`spacy`、`pyserini`、`web_agent_site.envs` 导入成功；
- `WebAgentTextEnv-v0` 注册成功；
- `observation_mode=text`、`num_products=1000`；
- 两次 reset 均返回非空 observation，session 不同；
- search 后 `done == false`；
- 商品详情页返回成功；
- 无需选择额外 option 即出现 `Buy Now`；
- `buy_now_executed == false`；
- purchase count 始终为 0；
- 第二次 reset 的 asin 为空、options 为空。

机器可读结果：`evidence/webshop_small_smoke.json`，SHA-256 为 `e1cf270fe8612ace744b70a01809293a7c3005a215b222a926a559d2bd7e0c57`。

## 8. 测试与回归

| 验证 | 结果 | 证据 |
|---|---|---|
| Python 编译 | PASS | EV-31 |
| PowerShell bootstrap 解析 | PASS，stdout 仅 `POWERSHELL_PARSE_OK`，stderr 为空 | EV-31 |
| P9 专项 fail-closed 测试 | 14/14 PASS | EV-31 |
| 最终依赖导入和版本自检 | PASS | EV-31 |
| 主仓完整 unittest | 302/302 PASS | EV-32 |
| `run_experiment.py` | 13/13 PASS | EV-33 |
| 最终环境/范围/指纹审计 | PASS | EV-34 |

Gym 0.24 输出已知版本警告，但真实 reset、step 和第二次 reset 均已通过；该警告未被当作失败或隐藏。

## 9. 偏差与未解决项

### 9.1 已接受的兼容偏差

| 上游/初始值 | 最终值 | 原因 | 验证 |
|---|---|---|---|
| NumPy 1.22.4 | 1.23.5 | 官方 Windows Faiss 1.7.4 扩展需要更高 NumPy C-API | EV-28、EV-29、EV-30、EV-31 |
| 上游仅写 `faiss-cpu` | Faiss 1.7.4 + MKL 2021.4 | `faiss.dll` 依赖 `mkl_rt.1.dll` | EV-24、EV-26、EV-29 |
| Pyserini 元数据依赖未完整落地 | Transformers 4.19.2 + ONNX Runtime 1.12.1 及固定 wheel 依赖 | Pyserini 0.17 在导入 LuceneSearcher 时预加载编码模块 | EV-26、EV-29 |

所有偏差只存在于 `webshop38`，没有进入主项目依赖或共享 `agent`。

### 9.2 失败尝试及处理

- EV-20—EV-22：从 WSL 启动 Windows PowerShell 时，外部 `git.exe` / `conda.exe` 调用链不能可靠返回；均在下载前失败。最终使用相同参数的直接 `conda.exe run` 命令完成执行，bootstrap 本身通过 PowerShell 解析和离线合同测试。
- EV-23：数据、资源和索引成功，首次查询发现缺 Faiss。
- EV-24：安装 Faiss 1.7.4 后发现 MKL DLL 版本不匹配。
- EV-25：工具传输超时留下本轮自己的 Conda 子进程；只终止该次 P9 自有 PID，没有影响其他进程。
- EV-27：Faiss 1.7.2 降级求解超时且未改变环境；因其要求 MKL `<2021`，未采用更大范围降级。

### 9.3 未解决项

当前没有阻断 P9-A2 验收的未解决项。P9-B Commerce Adapter、购买动作授权拦截、支付和履约是后续独立合同，不属于本任务。

## 10. AC 映射

| AC | 状态 | 证据 |
|---|---|---|
| AC-01 isolated Conda environment | PASS | EV-19、EV-34 |
| AC-02 bounded and reproducible dependencies | PASS | EV-19、EV-26、EV-28、EV-29、EV-31、EV-34 |
| AC-03 official small data only / Amendment A1 | PASS | EV-17、EV-18、EV-23、EV-34 |
| AC-04 1,000-product search index only | PASS | EV-23、EV-30、EV-34 |
| AC-05 deterministic text-environment smoke | PASS | EV-30、EV-34 |
| AC-06 permanent fail-closed validation | PASS | EV-31 |
| AC-07 scope, regression and safety | PASS | EV-32、EV-33、EV-34 |
| AC-08 roadmap and handoff consistency | PASS，路线文档已更新，两轮交接前验证均无 `BLOCKING` | EV-34、EV-35、EV-36 |

## 11. VP 映射

| VP | 状态 | 证据 |
|---|---|---|
| VP-01 | PASS | EV-19、EV-34 |
| VP-02 | PASS | EV-19、EV-26、EV-28、EV-29、EV-31、EV-34 |
| VP-03 | PASS | EV-17、EV-18、EV-23、EV-34 |
| VP-04 | PASS | EV-23、EV-30、EV-34 |
| VP-05 | PASS | EV-30、EV-34 |
| VP-06 | PASS | EV-31 |
| VP-07 | PASS | EV-32 |
| VP-08 | PASS | EV-33 |
| VP-09 | PASS | EV-34 |
| VP-10 | PASS，两轮交接前 validator 均无 `BLOCKING` | EV-35、EV-36 |

## 12. 证据链

- EV-01—EV-08：初始隔离环境、依赖安装与清单；
- EV-09—EV-10：原 Google Drive 链接失效；
- EV-11—EV-16：初始脚本、测试、回归与阻断收口；
- EV-17—EV-18：最新版 gdown 复测和三镜像逐字节共识；
- EV-19：修订合同恢复执行前的新鲜环境/指纹；
- EV-20—EV-22：Windows PowerShell 宿主调用失败，未进入数据阶段；
- EV-23：固定 revision 数据校验迁入、资源和索引构建；
- EV-24—EV-29：Pyserini/Faiss 兼容链诊断与固定依赖修复；
- EV-30：Lucene 真实查询和真实 WebShop smoke；
- EV-31：编译、PowerShell 解析、14 项专项测试和运行时自检；
- EV-32：302 项完整回归；
- EV-33：官方入口 13/13；
- EV-34：最终工作区、环境、范围、哈希和安全边界审计；
- EV-35：`EXECUTING / Executor` 状态下的工作流预验证，无 `BLOCKING`；
- EV-36：`READY_FOR_REVIEW` 报告候选的交接前验证，无 `BLOCKING`。

## 13. 明确未发生事项

本轮没有：

- 修改固定 WebShop 上游源码；
- 创建 full / 100 / 100k 数据或索引；
- 启动 Flask、浏览器、ChromeDriver 或后台服务；
- 执行 `click[buy now]`；
- 创建真实或模拟订单；
- 接入 Commerce Adapter、Trust Control Plane、支付或履约；
- 调用 LLM/API、测试网、钱包、签名或资金；
- 修改 base、系统 Python、系统 Java、系统 PATH 或共享 `agent`；
- commit、push 或 history rewrite。
