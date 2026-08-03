# Task Contract

Task ID: `P9-WEBSHOP-UPSTREAM-PREFLIGHT-V1`  
Workflow: `evaluator-executor-workflow/v2`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`  
State: `CONTRACT_FROZEN`

## 1. Context

P1—P8-A have produced a deterministic trust-control and payment-validation core. The next missing layer is an external multi-step commerce environment.

The user decided to reuse WebShop rather than build a new MiniShop. P8-B public x402 testnet work is deferred and remains separately unauthorized.

Official WebShop facts used by this contract:

```text
repository: princeton-nlp/WebShop
branch: master
observed upstream commit: 64fa2a5
license: MIT
text environment: WebAgentTextEnv-v0
action grammar: search[...] / click[...]
purchase action: click[buy now]
```

The upstream text environment exposes `reset`, `step` and available actions. Its current `click[buy now]` path routes through `SimServer.receive()` to `SimServer.done()`, calculates reward and terminates the session. That is the future purchase-interception seam.

Current local toolchain inventory:

```text
Windows Conda root: D:\SoftWare\Anaconda\install
existing agent env: D:\SoftWare\Anaconda\workspace\.conda\envs\agent
agent Python: 3.12.13
agent available modules: torch, spacy
agent missing modules: gym, flask, pyserini
WSL python3: 3.12.3
Java: 17.0.19
Docker / Podman: absent
uv / micromamba / mamba / pyenv: absent
available disk: about 75 GB
```

The earlier shell probe could not see Windows Conda from `PATH`; direct Windows discovery confirmed Conda and the `agent` environment exist. Because `agent` is Python 3.12 and is already a shared project environment, it must not receive WebShop's Python 3.8-era dependency set.

The user authorized creating a separate environment when `agent` is unsuitable. The planned P9-A2 environment is `webshop38`, targeting Python 3.8.13 or a separately reviewed compatible 3.8.x resolution. This first task still must not create or modify any Conda environment; it freezes the upstream source and proves that the required integration seam exists.

Primary project reference:

- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`

## 2. Single objective

Create a reproducible, bounded WebShop upstream preflight that:

1. acquires the official repository at the pinned commit inside a Git-ignored local third-party directory;
2. verifies the upstream origin, commit, MIT license and required files;
3. deterministically proves the expected text-environment and `click[buy now]` purchase seam are present;
4. records the exact local environment blockers for the next isolated-install task;
5. performs no dependency installation, data download, service startup or product integration.

This task does not yet run WebShop. It establishes a trustworthy external-environment boundary for P9-A2.

## 3. Acceptance criteria

### AC-01 — official bounded acquisition

The Executor must create or reuse:

```text
local_sources/third_party/webshop/
```

The checkout must satisfy all of the following:

- origin URL is exactly the official `princeton-nlp/WebShop` GitHub repository;
- checked-out commit is exactly `64fa2a5` or the full SHA resolving from it;
- checkout is detached or otherwise protected from silently following a moving branch;
- no fork, mirror, archive bundle or copied source is accepted;
- the directory remains ignored by the main repository;
- no third-party source or data appears in the main repository's tracked/untracked scope outside the ignored directory.

A shallow clone/fetch is preferred. If the short SHA cannot be resolved, stop and report rather than selecting another commit.

### AC-02 — upstream integrity manifest

Create a machine-readable manifest containing at least:

- repository origin;
- full pinned commit SHA;
- branch/tag context if available;
- MIT license identification;
- SHA-256 for:
  - `README.md`;
  - `LICENSE.md`;
  - `setup.sh`;
  - `requirements.txt`;
  - `web_agent_site/envs/__init__.py`;
  - `web_agent_site/envs/web_agent_text_env.py`;
  - `web_agent_site/engine/engine.py`;
- required-file existence results;
- acquisition timestamp;
- statement that no dataset, dependency or service was used.

The manifest must be written under this task's evidence directory, not inside the third-party checkout.

### AC-03 — deterministic integration-seam checker

Create a local validation script that accepts a WebShop checkout path and fails closed unless all expected upstream contracts are found.

The checker must verify at least:

```text
WebAgentTextEnv class exists
step(action) exists
reset(...) exists
search[...] and click[...] action grammar is present
WebAgentTextEnv-v0 is registered
END_BUTTON resolves to Buy Now
SimServer.receive routes the Buy Now action to done()
SimServer.done records purchase, reward and terminal state
small / 1000-product setup path is documented
```

The checker must use source inspection or AST/text contracts only. It must not import WebShop, install dependencies, start Flask, load products, build a Lucene index or access data files.

Failure messages must identify the missing contract and file path.

### AC-04 — permanent checker tests

Add deterministic tests for the checker covering:

1. valid minimal source fixture passes;
2. missing `WebAgentTextEnv` fails;
3. missing `WebAgentTextEnv-v0` registration fails;
4. changed `END_BUTTON` fails;
5. missing Buy Now → `done()` route fails;
6. missing required upstream file fails;
7. wrong origin or commit fails;
8. actual pinned checkout passes when available.

Tests must not require network. The actual-checkout test may skip with an explicit reason only when the ignored checkout is absent; after AC-01 acquisition it must execute and pass.

### AC-05 — toolchain and next-stage blocker report

The report must record raw evidence for:

- Windows Conda root and `conda env list`;
- the `agent` environment path, Python version and presence/absence of Gym, Flask, Torch, spaCy and Pyserini;
- WSL Python executables and versions;
- Java version;
- Docker / Podman / uv / micromamba / mamba / pyenv availability;
- available disk space;
- whether Python 3.8.13 is already available in any existing environment;
- why the existing `agent` Python 3.12 environment must not receive WebShop's old dependency set;
- the planned dedicated environment name `webshop38` and the user's authorization to create it in P9-A2.

It must conclude with a bounded P9-A2 prerequisite list. It must not create, modify or install into any Conda environment in P9-A1.

### AC-06 — scope and safety

The task must preserve all current project behavior.

- No `src/agentic_payment_experiment/` product file changes.
- No current business-rule, payment, trust, evaluator or UI changes.
- No run of `setup.sh`.
- No `pip install`, `conda install`, package-manager bootstrap or system installation.
- No Google Drive dataset, spaCy model, trajectory or image download.
- No Lucene/Pyserini index build.
- No WebShop server or background process.
- No ChromeDriver or browser automation.
- No LLM/model/API call.
- No x402 network/testnet action.
- No real merchant, card, customer, wallet or funds.
- No commit, push or history rewrite.

### AC-07 — roadmap and handoff consistency

The execution report must identify this task as P9-A1 and state that:

```text
P9-A1 upstream preflight
    -> P9-A2 create dedicated webshop38 Conda environment + small dataset smoke test
    -> P9-B Commerce Adapter and purchase interception
    -> P9-C payment / fulfillment sidecar
```

It must not claim WebShop is installed, runnable or integrated merely because source checks pass.

## 4. Allowed scope

Tracked project paths:

- `scripts/validation/webshop/check_webshop_upstream.py`
- `tests/test_webshop_upstream_contract.py`
- `docs/reference/WebShop外部商城接入分析与分批执行路线_20260801.md`（only factual status correction if needed）
- `docs/05_任务交接/P9_WEBSHOP_UPSTREAM_PREFLIGHT_V1/REPORT.md`
- `docs/05_任务交接/P9_WEBSHOP_UPSTREAM_PREFLIGHT_V1/evidence/EV-*`

Ignored local path:

- `local_sources/third_party/webshop/`

Router after the atomic handoff:

- `CURRENT.md`

No other path is allowed without stopping and reporting.

## 5. Exclusions

- No run of `setup.sh` or any WebShop installation command.
- No `pip install`, `conda install`, package-manager bootstrap or system installation.
- No Google Drive product dataset, spaCy model, trajectory, image or search-index download.
- No WebShop import, runtime execution, Flask service, background process, browser or ChromeDriver.
- No Lucene / Pyserini index build.
- No modification of the ignored third-party WebShop checkout.
- No copied or tracked WebShop source/data outside `local_sources/third_party/webshop/`.
- No change under `src/agentic_payment_experiment/` or to existing payment, trust, evaluator or UI behavior.
- No LLM/model/API provider call.
- No x402 testnet, wallet, signing, faucet, blockchain, real merchant, customer/card data or funds.
- No commit, push or history rewrite.

## 6. Explicit network authorization

The user authorized proceeding with the existing external simulated shopping application. For this first task, network authority is narrowly limited to:

```text
git clone / git fetch
https://github.com/princeton-nlp/WebShop.git
```

Allowed purpose:

- resolve and acquire commit `64fa2a5`;
- no other repository or endpoint.

Not authorized in this task:

- GitHub API use beyond normal Git transport;
- Google Drive;
- PyPI / Conda channels;
- spaCy model servers;
- model providers;
- public WebShop demo;
- any payment, wallet, blockchain or testnet endpoint.

If Git transport requires credentials, redirects to a nonofficial origin or cannot resolve the pinned commit, stop and report.

## 7. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | origin / full SHA / ignored-path evidence for `local_sources/third_party/webshop/` | Official origin, pinned commit, ignored checkout | AC-01 |
| VP-02 | run `check_webshop_upstream.py` against the actual checkout | All required contracts pass | AC-02, AC-03 |
| VP-03 | `python3 -m unittest tests.test_webshop_upstream_contract -v` | Checker positive and negative tests pass | AC-03, AC-04 |
| VP-04 | local toolchain inventory commands | Exact environment and blockers recorded | AC-05 |
| VP-05 | `env PYTHONPATH=src python3 -m unittest discover -s tests -v` | Existing full suite remains green | AC-06 |
| VP-06 | `python3 run_experiment.py` | Existing official entrypoint baseline remains unchanged | AC-06 |
| VP-07 | task-scoped `git diff --check`, path inventory and ignored-checkout proof | No scope creep or tracked third-party source/data | AC-01, AC-06 |
| VP-08 | workflow validator | No `BLOCKING` finding | AC-07 |

If the inherited worktree causes a full-suite failure unrelated to P9-A1, capture the raw failure and prove the same failure exists without the task-scoped files; do not modify product code.

## 8. Required report evidence

`REPORT.md` must include:

- `executor_state: READY_FOR_REVIEW`;
- exact changed tracked files and SHA-256 hashes;
- exact ignored checkout path;
- official origin and full pinned commit;
- integrity manifest path and contents summary;
- checker contract matrix;
- positive/negative test results;
- local toolchain inventory;
- P9-A2 blockers and prerequisites;
- explicit statement that no dependency, data, service, browser, model, payment or testnet action occurred;
- AC-01 through AC-07 mapping to EV identifiers;
- raw EV meta/stdout/stderr triplets;
- any deviation or unresolved upstream drift.

## 9. Stop conditions

Stop and report instead of broadening scope if:

- official commit `64fa2a5` cannot be resolved;
- origin is not the official Princeton repository;
- MIT license is absent or materially changed;
- source no longer exposes the expected text environment or Buy Now path;
- validating the seam requires importing or running WebShop;
- any dependency/data download is required;
- checker implementation would require modifying project product code;
- another external runtime appears necessary;
- a network endpoint outside the exact official Git remote is required.

## 10. Inherited worktree state

P4—P8 product changes, tests, task packets, evidence and current documentation edits remain uncommitted because commit/push authorization is false. The Executor must preserve all inherited changes and attribute only the allowed P9-A1 files to this task.

The ignored WebShop checkout is not a tracked deliverable. Its exact source identity must be evidenced from outside that directory.

## 11. Authorization

```yaml
commit: false
push: false
history_rewrite: false
api_call: false
network_call: true
network_scope: https://github.com/princeton-nlp/WebShop.git
dependency_install: false
data_download: false
background_process: false
real_funds: false
```

## 12. Atomic handoff

Do not request Evaluator review until VP-01 through VP-08 have readable raw evidence, every AC is mapped in `REPORT.md`, `executor_state: READY_FOR_REVIEW` is declared, the actual checkout passes the checker, and the workflow validator reports no `BLOCKING` finding.
