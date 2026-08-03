# Task Contract

Task ID: `P9-WEBSHOP-SMALL-RUNTIME-SMOKE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`  
Amendment: `A1-CHECKSUM-VERIFIED-MIRROR-FALLBACK`（Evaluator，2026-08-02）

## 0. Amendment A1 — checksum-verified mirror fallback

### 0.1 Evaluator decision

`APPROVED`，但仅用于本地实验环境恢复。

EV-17 已证明三个原 Google Drive ID 在当前公开下载路径下均无法由最新版 `gdown` 获取；同一轮诊断从三个不同 Hugging Face 仓库取得的三个 small 文件逐字节 SHA-256 完全一致，其中 `items_human_ins.json` 还与固定 WebShop checkout 中已跟踪的官方副本一致。

本修订只改变 AC-03 的数据取得方式、对应网络授权和停止条件。原合同关于环境隔离、索引范围、真实 smoke、禁止 `click[buy now]`、不修改上游源码、不接支付/LLM/测试网以及不 commit/push 的要求全部保持不变。

### 0.2 Source precedence

执行者必须按以下顺序处理：

1. 已有 EV-17 可作为本轮“官方 Google Drive 公开链接失效”的证据，不要求重复六次失败下载；
2. 运行时数据允许从下列**固定 revision**镜像获取；禁止使用可变的 `main` 地址；
3. 每个文件必须先下载到临时目录，完成大小、SHA-256、JSON 类型和条数校验后再原子移动到 `webshop/data/`；
4. 任一字段不匹配立即停止，不得尝试其他未批准来源、手工浏览器下载或内容修补。

Approved mirrors, in priority order:

```text
Primary
repository: YWZBrandon/webshop-data
revision: ce990fff5aee388db2706f07820c578ab68e0453
base: https://huggingface.co/datasets/YWZBrandon/webshop-data/resolve/ce990fff5aee388db2706f07820c578ab68e0453/

Secondary
repository: HongbangYuan/webshop
revision: 0129d4a81dbdb827e76afd20a1e2c38b61098613
base: https://huggingface.co/datasets/HongbangYuan/webshop/resolve/0129d4a81dbdb827e76afd20a1e2c38b61098613/

Tertiary
repository: Merlin-Hongru/tmp-files
revision: c38999b0787132502fcf85d02ff92ea6347baf87
base: https://huggingface.co/Merlin-Hongru/tmp-files/resolve/c38999b0787132502fcf85d02ff92ea6347baf87/
```

Only these three filenames are allowed:

| Filename | Bytes | SHA-256 | JSON type | Count |
|---|---:|---|---|---:|
| `items_shuffle_1000.json` | 4,467,013 | `30a4765c3a327af72d9a9a95a6b2486d516f0fa1d3ecd83681901ce82a21b269` | list | 1,000 |
| `items_ins_v2_1000.json` | 147,099 | `f88a36314a397b53b3d9c3fa5878e5f7b26d35019a51ec83fbedeca61a948f6f` | dict | 1,000 |
| `items_human_ins.json` | 5,137,548 | `cf78667548a71786e1d9049c24b802e48e1084ad4bb021cae56ce1f6d96954a3` | dict | 10,136 |

### 0.3 Required implementation change

`bootstrap_webshop_small.ps1` must:

- expose an explicit switch such as `-AllowChecksumMirrorFallback`;
- default to fail closed when the switch is absent;
- use revision-pinned URLs only;
- write downloads to a temporary/staging directory;
- verify filename, exact byte length, SHA-256, JSON type and count before promotion;
- record the selected repository, revision and final URL in evidence;
- remove partial staging files after failure;
- never download full data, trajectories, images, model checkpoints or additional files.

The verifier and offline contract tests must cover at least:

1. mutable `main` mirror URL is rejected;
2. unapproved repository/revision is rejected;
3. wrong bytes/hash/type/count is rejected before promotion;
4. no fallback switch means mirror use is rejected;
5. valid pinned mirror metadata passes;
6. `click[buy now]` remains forbidden.

### 0.4 Execution continuation

The existing `webshop38` environment may be reused because it already resolves Python 3.8.13 and the shared `agent` before/after fingerprint matched. The Executor must still capture a fresh `webshop38` inventory and a fresh `agent` after-fingerprint for the resumed run.

Resume from AC-03 / VP-03, then complete AC-04 through AC-08 and VP-04 through VP-10. Final handoff still requires:

```text
real 1k index query PASS
real WebAgentTextEnv-v0 smoke PASS
click[buy now] not executed
full regression PASS
run_experiment.py PASS
workflow validator: no BLOCKING findings
REPORT.md: executor_state READY_FOR_REVIEW
CURRENT.md: READY_FOR_REVIEW / Evaluator only after atomic package exists
```

### 0.5 Reporting boundary

The final report must describe these files as:

```text
checksum-verified mirror copies of the WebShop small assets
```

It must not describe the mirror download itself as an official Princeton or official Google Drive download. This amendment authorizes the bytes for a local smoke test only; it does not establish canonical dataset provenance for publication, redistribution or production use.

## 1. Context

P9-A1 已由独立评估者判定 `PASS`：

```text
official origin: https://github.com/princeton-nlp/WebShop.git
pinned commit: 64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd
checkout: local_sources/third_party/webshop
state: detached + clean + main-repo ignored
text environment seam: verified
click[buy now] -> SimServer.receive() -> SimServer.done(): verified
```

P9-A1 只验证了官方源码和接入缝隙，没有创建 Conda 环境、安装依赖、下载 small 数据、构建索引或运行 WebShop。

已确认的用户决定：

- 优先接入外部 WebShop，不自建 MiniShop；
- 先分批完成环境、依赖和数据准备，不直接进入 Commerce Adapter 或支付实现；
- 现有 `agent` 环境不满足时，可以创建独立 Conda 环境；
- `agent` 是共享 Python 3.12.13 环境，不允许被 WebShop 旧依赖污染。

P9-A2 使用现有 Windows Conda：

```text
Conda root: <LOCAL_SOFTWARE>\Anaconda\install
planned env: webshop38
target Python: 3.8.13
approved fallback: only another Python 3.8.x patch release, and only after raw solver evidence proves 3.8.13 cannot be resolved
```

上游 `setup.sh -d small` 不能直接无边界执行。它除安装依赖和 small 数据外，还会下载 spaCy 模型、50 条示例轨迹，并构建 100 / 1k / 100k / full 四套索引。当前任务只允许最小的 1,000 商品文本环境，因此必须拆分执行并只保留必需副作用。

Primary references:

- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`
- `docs/05_任务交接/P9_WEBSHOP_UPSTREAM_PREFLIGHT_V1/REVIEW.md`

## 2. Single objective

Create a reproducible, isolated WebShop small runtime that:

1. creates or safely reuses a dedicated Windows Conda environment named `webshop38`;
2. installs only the dependencies required by the official 1,000-product text environment;
3. downloads only the official small product, attribute and human-instruction files;
4. builds only the `resources_1k` / `indexes_1k` search path;
5. runs a deterministic `WebAgentTextEnv-v0` reset → search → product click → pre-Buy-Now smoke test;
6. proves the shared `agent` environment and current project behavior remain unchanged.

This task establishes the external runtime boundary for P9-B. It does not integrate the Trust Control Plane and does not execute `click[buy now]`.

## 3. Acceptance criteria

### AC-01 — isolated Conda environment

The Executor must create or reuse:

```text
name: webshop38
manager: <LOCAL_SOFTWARE>\Anaconda\install\Scripts\conda.exe
```

Required facts:

- `agent` is not modified;
- environment is managed by the existing Windows Conda installation, not WSL Python and not a project `.venv`;
- preferred Python is exactly `3.8.13`;
- if exact `3.8.13` cannot resolve, another `3.8.x` patch release is pre-approved only after the failed/dry-run solver output is captured; Python `3.9+` is not allowed;
- if `webshop38` already exists, record its path, Python version and package inventory before any action;
- an existing environment with unknown provenance, Python outside 3.8.x or conflicting packages must not be deleted or silently repaired; stop and report;
- no global Conda configuration, channel configuration, base environment or system PATH may be changed.

Capture before/after fingerprints for the shared `agent` environment:

```text
python --version
conda list
SHA-256 of normalized conda-list output
```

The before and after fingerprints must match.

### AC-02 — bounded and reproducible dependencies

Install dependencies only inside `webshop38`.

The runtime must provide at least:

```text
Python 3.8.x
Gym 0.24.0
Flask 2.1.2
NumPy 1.22.4
Pandas 1.4.2
Pyserini 0.17.0
spaCy 3.3.0
Torch 1.11.0 or the minimum documented compatible build required for this platform
OpenJDK 11 inside the Conda environment
BeautifulSoup / requests / rich / thefuzz / tqdm and other imported WebShop runtime dependencies
spaCy model en_core_web_sm compatible with the installed spaCy version
```

The pinned upstream source loads `en_core_web_sm`; downloading only `en_core_web_lg` does not satisfy this task.

Dependency rules:

- do not run upstream `setup.sh` as a single opaque command;
- use an explicit local bootstrap script or recorded command sequence;
- every version deviation from `requirements.txt` must list the original pin, resolved version, reason and smoke-test result;
- no unbounded upgrade to current/latest packages;
- no package may be installed into `agent`, base, WSL Python or system Python;
- produce `conda list --explicit`, `conda list` and `pip freeze` evidence;
- rerunning bootstrap must be idempotent or fail closed without duplicating environments/data.

### AC-03 — official small data only

Download only the three official files referenced by the pinned upstream `setup.sh`:

```text
items_shuffle_1000.json
  Google Drive id: 1EgHdxQ_YxqIQlvvq5iKlCrkEKR6-j0Ib

items_ins_v2_1000.json
  Google Drive id: 1IduG0xl544V_A_jv3tHXC0kyFi7PnyBu

items_human_ins.json
  Google Drive id: 14Kb5SPBk_jfdLZ_CDBNitW98QLDlKR5O
```

Destination:

```text
local_sources/third_party/webshop/data/
```

Required validation:

- record exact URL/file ID, final filename, byte size and SHA-256;
- all three files parse as JSON;
- `items_shuffle_1000.json` contains exactly 1,000 top-level products;
- `items_ins_v2_1000.json` is non-empty and covers the small product set sufficiently for runtime initialization;
- `items_human_ins.json` is non-empty and can be consumed by the pinned source;
- no full-dataset IDs, images, reviews, feature tensors, trajectories or other data are downloaded;
- no copied dataset enters the tracked main repository.

Redirects under official Google download infrastructure are allowed only when they resolve one of the three approved file IDs. Any login, quota bypass, mirror or manual browser download is a stop condition.

### AC-04 — 1,000-product search index only

Create only:

```text
local_sources/third_party/webshop/search_engine/resources_1k/
local_sources/third_party/webshop/search_engine/indexes_1k/
```

Required facts:

- index build uses `webshop38` Python, Pyserini 0.17.0 and environment-local OpenJDK 11;
- no system Java replacement or global `JAVA_HOME` mutation;
- no `indexes`, `indexes_100`, `indexes_100k`, `resources`, `resources_100` or `resources_100k` build;
- a `LuceneSearcher` opens `indexes_1k` and returns at least one result for a keyword derived from downloaded product data;
- record source JSON hash, generated `documents.jsonl` hash, index inventory and query result.

The Executor may add a local helper under the allowed tracked script path to generate only `resources_1k`; it must not edit the pinned third-party source.

### AC-05 — deterministic text-environment smoke test

Run a tracked local smoke script against the pinned checkout using `webshop38`.

The smoke must prove:

1. `gym`, `spacy`, `pyserini` and `web_agent_site.envs` import successfully;
2. `WebAgentTextEnv-v0` is registered;
3. environment is created with `observation_mode=text` and `num_products=1000`;
4. `reset` returns a non-empty observation;
5. `get_available_actions()` reports a search bar;
6. a search keyword derived deterministically from downloaded product data is executed;
7. `step(search[...])` returns a non-empty observation, `done == false` and no exception;
8. one valid product result is clicked and a product-detail observation is returned;
9. the environment reaches a state where `buy now` is an available action, selecting a required option first when necessary;
10. `click[buy now]` is **not executed**;
11. a second reset succeeds and does not retain previous purchase state;
12. exact actions, observation summaries, reward/done values and chosen product are written to machine-readable evidence.

No Flask server, browser, ChromeDriver, background process or LLM is required or allowed.

### AC-06 — permanent fail-closed validation

Add deterministic main-repository tests for the new bootstrap/asset/smoke helpers covering at least:

1. missing one of the three small data files fails;
2. product file with a count other than 1,000 fails;
3. missing `indexes_1k` fails before runtime smoke;
4. checkout at a commit other than the pinned SHA fails;
5. an execution plan that includes `click[buy now]` is rejected;
6. valid fixture metadata passes.

These tests must run without network and without requiring `webshop38`. The real environment smoke is separately evidenced by AC-05.

### AC-07 — scope, regression and safety

- no tracked file inside `local_sources/third_party/webshop/` may change;
- only ignored `data/`, `search_engine/resources_1k/` and `search_engine/indexes_1k/` runtime artifacts may be created there;
- no `src/agentic_payment_experiment/` product code changes;
- no Commerce Adapter, Trust Control Plane, payment, fulfillment, evaluator or UI integration;
- no `click[buy now]` execution;
- no WebShop service, browser or background process;
- no LLM/model-provider/API call;
- no x402/testnet, wallet, signing, merchant, customer/card data or funds;
- no commit, push or history rewrite;
- full main-project tests remain green, with at least the existing 288-test baseline;
- `python3 run_experiment.py` remains green.

### AC-08 — roadmap and handoff consistency

The report must state:

```text
P9-A1 official source preflight                 PASS
P9-A2 isolated environment + small runtime      this task
P9-B Commerce Adapter + Buy Now interception    not started
P9-C payment / fulfillment sidecar              not started
```

It must not claim WebShop is integrated with the payment project merely because the external text environment runs.

## 4. Allowed scope

- `scripts/validation/webshop/bootstrap_webshop_small.ps1`
- `scripts/validation/webshop/verify_webshop_small_assets.py`
- `scripts/validation/webshop/smoke_webshop_small.py`
- `tests/test_webshop_small_runtime_contract.py`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`（only factual P9-A2 status/deviation update）
- `docs/02_未来规划/验证体系与后续环境统一路线_20260801.md`（only factual P9-A2 status/deviation update）
- `docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_SMALL_RUNTIME_SMOKE_V1/evidence/EV-*`
- `CURRENT.md` only for atomic handoff after the complete report/evidence package exists

Allowed ignored runtime paths:

- `local_sources/third_party/webshop/data/`
- `local_sources/third_party/webshop/search_engine/resources_1k/`
- `local_sources/third_party/webshop/search_engine/indexes_1k/`
- Windows Conda environment `webshop38`
- Conda/Pip package caches produced by the approved install

No other path is allowed without stopping and reporting.

## 4.1 Exclusions

- 不修改 `src/agentic_payment_experiment/` 产品代码、正式 UI、P1—P6 或 M5；
- 不修改固定 WebShop checkout 的任何 tracked 文件，不切换 commit、branch 或 fork；
- 不下载 full 数据、图片、reviews、feature tensors、轨迹、额外模型或其他未列名文件；
- 不运行浏览器、ChromeDriver、Flask 服务、后台进程或 LLM；
- 不执行 `click[buy now]`，不创建模拟或真实订单、付款、钱包、签名或测试网交易；
- 不修改 `agent`、base、WSL Python、系统 Java、系统 PATH 或全局 Conda 配置；
- 不使用可变镜像分支、未批准镜像、手工修补数据、登录绕过或非固定哈希文件；
- 不 commit、不 push、不 rewrite history。

## 5. Explicit network and side-effect authorization

```yaml
create_conda_environment: true
environment_name: webshop38
dependency_install: true
data_download: true
network_call: true
api_call: false
background_process: false
system_package_install: false
real_payment_or_order: false
commit: false
push: false
history_rewrite: false
```

Approved network purposes:

1. resolve Python 3.8.x and approved dependencies through existing Conda configuration and official Anaconda/PyTorch/conda-forge channels;
2. obtain pinned Python packages from official PyPI infrastructure when Conda does not provide them;
3. download only the three approved Google Drive file IDs in AC-03;
4. obtain the compatible official `en_core_web_sm` model from official spaCy/explosion distribution infrastructure.

Not authorized:

- full WebShop dataset IDs;
- human trajectory folder download;
- images, reviews, feature tensors or model checkpoints;
- mirrors, unofficial package indexes or account/login flows;
- GitHub source updates or checkout movement away from the pinned commit;
- model-provider APIs, public WebShop demo, payment, wallet, blockchain, testnet or real commerce endpoints.

## 6. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | Conda inventory, `agent` before fingerprint, environment create/reuse, Python version | `webshop38` isolated on Python 3.8.x; `agent` untouched | AC-01 |
| VP-02 | module/version imports, env-local Java, explicit/freeze inventories | Required runtime resolves only inside `webshop38` | AC-02 |
| VP-03 | approved-ID data download plus verifier | Three files only; JSON valid; product count exactly 1,000 | AC-03 |
| VP-04 | 1k resource/index build and direct Lucene query | Only `resources_1k` / `indexes_1k`; at least one result | AC-04 |
| VP-05 | `smoke_webshop_small.py` in `webshop38` | reset → search → product click → pre-Buy-Now → reset passes | AC-05 |
| VP-06 | `python3 -m unittest tests.test_webshop_small_runtime_contract -v` | All offline helper contract tests pass | AC-06 |
| VP-07 | `env PYTHONPATH=src python3 -m unittest discover -s tests -v` | Full suite green; test count at least 288 | AC-07 |
| VP-08 | `python3 run_experiment.py` | Existing official entrypoint green | AC-07 |
| VP-09 | nested WebShop Git status, main Git scope, `agent` after fingerprint, task-scoped `git diff --check` | No upstream tracked change, no agent drift, no scope creep | AC-01, AC-07 |
| VP-10 | workflow package validation | No `BLOCKING` finding before review handoff | AC-08 |

Windows-side validation must preserve the exact PowerShell/`conda.exe run` command and exit code rather than replacing it with prose.

## 7. Required execution evidence

For every VP, save:

```text
EV-xx.meta.json
EV-xx.stdout.log
EV-xx.stderr.log
```

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact environment path and Python version;
- 3.8.13 resolution result and any approved 3.8.x fallback evidence;
- `agent` before/after inventory hashes;
- package/version table and all deviations;
- environment-local Java version;
- exact three data file IDs, names, sizes and SHA-256;
- 1k resource/index inventory and direct query result;
- machine-readable smoke result and exact action sequence;
- statement that `click[buy now]` was not executed;
- exact changed tracked files and SHA-256;
- nested WebShop Git status and main-repository scope result;
- AC-01 through AC-08 mapped to EV identifiers;
- all failures, retries, skipped checks and environment limits;
- explicit statement that no Commerce Adapter, payment, LLM, testnet, real order, commit or push occurred.

## 8. Stop conditions

Stop and report without broadening scope if:

- `webshop38` already exists with unknown/conflicting state;
- neither Python 3.8.13 nor another 3.8.x patch can resolve;
- installation requires changing `agent`, base, WSL Python, system Java, global Conda config or system PATH;
- required runtime needs Python 3.9+;
- a package requires an unofficial index, account, credential or unapproved network host;
- small data cannot be fetched using the three approved IDs or fails JSON/count validation;
- runtime requires full data, trajectories, browser, Flask server, image features or additional model downloads;
- Pyserini cannot build/open `indexes_1k` with environment-local Java 11;
- pinned WebShop source must be edited to make smoke pass;
- any action would execute `click[buy now]` or create a simulated/real purchase;
- any product-code change under `src/agentic_payment_experiment/` appears necessary;
- main-project regression fails due to P9-A2 tracked changes.

Do not delete an existing environment, rewrite source history, switch the checkout commit or substitute a different WebShop fork.

## 9. Inherited worktree state

The main repository contains uncommitted P4—P9-A1 product, test, documentation and evidence files because commit/push authorization remains false. Preserve all inherited changes.

The Executor must attribute only the P9-A2 allowed tracked files and ignored runtime artifacts to this task. Global worktree dirtiness is not permission to edit unrelated files.

## 10. Atomic handoff

Do not request Evaluator review until:

1. VP-01 through VP-10 have readable raw evidence;
2. every AC is mapped in `REPORT.md`;
3. `executor_state: READY_FOR_REVIEW` is declared;
4. the real small text-environment smoke passes;
5. `agent` before/after fingerprints match;
6. workflow validation reports no `BLOCKING` finding.

Until then, `CURRENT.md` remains Executor-owned in `CONTRACT_FROZEN` or `EXECUTING` state.
