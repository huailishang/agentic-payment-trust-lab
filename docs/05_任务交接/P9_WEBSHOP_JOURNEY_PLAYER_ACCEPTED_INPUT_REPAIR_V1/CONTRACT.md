# Frozen Task Contract

Task ID: `P9-WEBSHOP-JOURNEY-PLAYER-ACCEPTED-INPUT-REPAIR-V1`  
Task name: WebShop Journey Player accepted-input guard repair  
Task kind: repair  
Risk: `L1`  
Contract state: `CONTRACT_FROZEN`  
Branch: `main`  
Baseline HEAD: `a9d02f9dbe3dd1ca580a8c4ac278151081a281be`  
Pre-existing changes: Evaluator-owned P9 review/RV evidence、project-map r16 与 CURRENT routing；以及当前 HEAD 已有的 Platform Validation Adapter 和支付参考资料。Evaluator 复跑代表脚本后，两个既有 EV-03 HTML/JSON 文件可能出现 stat/line-ending modified(状态或换行修改) 标记，但 Git clean-filter hash 与 HEAD blob 完全相同、`git diff` 为空；保留且不得重写或重新归因。

## Strategic basis

Project map: `docs/01_项目现状/PROJECT_BOTTLENECK_MAP.md`  
Map revision: `2026-08-23-r16`  
Active bottleneck: `B-10`  
Hypothesis: `H-10`  
Measurement status: measured  
Metric baseline: accepted-input 反例阻断 `0/2`；合法代表路径 render-ready `1/1`；安全可计量 Journey UI-ready `0/1`；Product Trace `9/12`；GESR `8/12`。  
Estimated affected scope: Journey Player 输入守卫的两个冻结元数据字段；不改变页面、payload、Read Model 或支付链路。  
Expected project impact: `NOT_APPLICABLE` for this repair task；修复只恢复原 H-10 的验收有效性，项目改进 verdict(裁决) 由后续 Evaluator 复评原指标。  
Rollback condition: 合法 accepted Journey 不再渲染、embedded payload 改变、Read Model/Consumer/Trace Player 被修改、来源语义改变，或项目守护指标退化。

## Single objective

让 Journey Player 只接受 `schema_version == JOURNEY_SCHEMA_VERSION` 且 `source_classification_status == SOURCE_CLASSIFICATION_STATUS` 的 `WebShopJourneyReadModel`；任一不匹配必须 fail closed(失败关闭)，合法 Journey 的 HTML 与 exact payload 行为保持不变。

## Frozen defect evidence

```text
docs/05_任务交接/P9_WEBSHOP_JOURNEY_PLAYER_V1/evidence/RV-EV-03.meta.json
docs/05_任务交接/P9_WEBSHOP_JOURNEY_PLAYER_V1/evidence/RV-EV-03.stdout.log
docs/05_任务交接/P9_WEBSHOP_JOURNEY_PLAYER_V1/evidence/RV-EV-03.stderr.log
```

Current hashes:

```text
src/agentic_payment_experiment/webshop_journey_player.py
f86dfae78e1bb94f654b4f44abd7a4f75e18d8d8e8ac97b0710816cce9403e3b

tests/test_webshop_journey_player.py
8722bb4fd44a5f43ded186196e8e78f0a94a0200fc6ec0aed305c9a5dea54e09

src/agentic_payment_experiment/webshop_journey_read_model.py
70d6c19fe7d48d27fc377f943ba53b0db276391f3f48402b66f0a57490d1ba7d
```

## Acceptance criteria

### AC-01 — Exact source-classification acceptance

- Type: mandatory behavior repair。
- Given: exact `WebShopJourneyReadModel` type whose `source_classification_status` was replaced with `UNVERIFIED` or any value other than `SOURCE_CLASSIFICATION_STATUS`。
- When: `build_webshop_journey_player_payload()` or `render_webshop_journey_player()` is called。
- Must observe: `WebShopJourneyPlayerInputError` before a normal payload/player is returned。
- Must not observe: non-empty arbitrary status being accepted。
- Evidence required: focused unit negative test plus frozen Evaluator counterexample。
- Mandatory: yes。

### AC-02 — Exact schema-version acceptance

- Type: mandatory behavior repair。
- Given: exact `WebShopJourneyReadModel` type whose `schema_version` is not `JOURNEY_SCHEMA_VERSION`, including `webshop-journey-read-model/v999`。
- When: payload building or rendering is called。
- Must observe: `WebShopJourneyPlayerInputError` before normal rendering。
- Must not observe: unknown non-empty schema version being accepted。
- Evidence required: focused unit negative test plus frozen Evaluator counterexample。
- Mandatory: yes。

### AC-03 — Accepted-path invariance

- Type: mandatory regression guard。
- Given: existing representative accepted Journey。
- When: rendered three times。
- Must observe: exact primitive remains embedded unchanged；existing source labels、instruction/product mismatch、fixed-script limitation、安全文本边界和 deterministic hashes(确定性哈希) remain valid。
- Must not observe: payload mutation、semantic repair(语义修复)、new timestamp/random/local path or autonomous-completion claim。
- Evidence required: Journey Player dedicated suite and related Read Model/Consumer/Trace Player regressions。
- Mandatory: yes。

### AC-04 — Scope and project guardrails

- Type: mandatory scope/regression guard。
- Given: the frozen two-field defect and current project baseline。
- When: repair is implemented and validation runs。
- Must observe: only Player + dedicated test product files change；formal entrypoint `13/13`；project-impact repeat=3 identical；Product Trace `9/12`；GESR `8/12`；callback match `12/12`；duplicate/forbidden side effect `0/12`。
- Must not observe: Read Model、Consumer、Trace Player、Adapter、runner、fixture、network、WebShop runtime、Buy Now or payment/order side effects changing or running。
- Evidence required: changed-file snapshot、formal entrypoint、project-impact result and L2 gate。
- Mandatory: yes。

### AC-05 — v2.2 handoff gate

- Type: mandatory workflow gate。
- Given: frozen contract and `VALIDATION_PLAN.yaml`。
- When: Executor runs `run_validation.py --mode executor` and prepares REPORT。
- Must observe: `L2-GATE.json` result `PASS` and workflow validator `OK` before `SUBMITTED_FOR_REVIEW`。
- Must not observe: report claiming final task/project verdict or ownership transfer by validator。
- Evidence required: L2 gate summary, EV triplets and validator output。
- Mandatory: yes。

## Allowed scope

- May modify: `src/agentic_payment_experiment/webshop_journey_player.py`。
- May modify: `tests/test_webshop_journey_player.py`。
- May add: this task's `REPORT.md`, saved diff, `evidence/EV-*`, `L2-GATE.json/.md` and deterministic metric output。
- Expected implementation: import the two accepted constants from `webshop_journey_read_model` and compare exact values in `_validate_payload()`；add direct negative tests for both mismatches。

## Exclusions and forbidden side effects

- Must not implement: new UI behavior、new Journey schema、autonomous Agent、WebShop replay、browser/network、Buy Now、payment/order execution。
- Must not modify: `webshop_journey_read_model.py`、Consumer、Trace Player、Adapter、runtime gate、runner、fixtures、prior task REPORT/REVIEW/EV、project map、CURRENT。
- Must not weaken: exact payload、four-source separation、origin validation、correlation/source-binding validation、hostile-text boundary or fixed-script limitation。
- Must not call or write externally: API、network、payment、order、wallet、production/testnet；commit、push、reset、clean、history rewrite also remain unauthorized。
- Must not modify frozen evaluator procedure: `docs/05_任务交接/P9_WEBSHOP_JOURNEY_PLAYER_ACCEPTED_INPUT_REPAIR_V1/evaluator_checks/accepted_input_counterexamples.py`。

## Validation plan

Validation plan file: `docs/05_任务交接/P9_WEBSHOP_JOURNEY_PLAYER_ACCEPTED_INPUT_REPAIR_V1/VALIDATION_PLAN.yaml`

| VP | Observable check | Expected result | AC |
|---|---|---|---|
| VP-01 | Journey Player focused suite；Evaluator 用独立冻结反例替代同命令；其成功结果进入 L2/L3 gate | 两个 mismatch fail closed；其余专项全通过 | AC-01..03, AC-05 |
| VP-02 | Read Model / Trace Player / Consumer regressions | 67/67 PASS | AC-03,04 |
| VP-03 | Formal entrypoint | 13/13 PASS | AC-04 |
| VP-04 | Project-impact repeat=3 | identical；Product Trace 9/12；GESR 8/12；side-effect guardrails unchanged | AC-04 |

## Authorization

- commit: false
- push: false
- history_rewrite: false
- api_call: false
- network_call: false
- dependency_install: false
- environment_creation: false
- WebShop_runtime_execution: false
- Buy_Now_execution: false
- payment_or_order_side_effect: false

## Stop conditions

- Baseline focused validation already fails for a reason other than the two frozen counterexamples。
- Work requires an excluded file or behavior。
- Work requires authority whose flag is false。
- Required evidence cannot be produced。
- The objective has materially different interpretations。
- The named map revision, bottleneck, or hypothesis cannot be verified。
- The principal change expands beyond the two accepted constants and their tests。
- The frozen Validation Plan no longer represents the intended acceptance semantics。

## Amendments

None.
