# Executor Report

Task ID: `H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1`
Executor status: `SUBMITTED_FOR_REVIEW`
Executor status: SUBMITTED_FOR_REVIEW
Task kind: `evaluator_design`
Baseline HEAD: `e6931273a983459f167b6e72287a6f05d53a8c26`
Project map revision: `2026-09-19-r51`
Active bottleneck: `B-06`
Hypothesis: `H-36`

## 1. Source pin

已从本地 pinned source(固定源码)独立复核：

- repository: `google-agentic-commerce/AP2`
- tag: `v0.2.0`
- commit: `b4587ac1d055888a73b4b21750973cffba961793`
- local source: `local_sources/third_party/ap2-v0.2.0`
- H-36 相对 product baseline `e6931273a983459f167b6e72287a6f05d53a8c26` 不修改 `src/**` / `tests/**`。

静态源码确认的入口链为：

```text
MandateClient.verify
  -> common.parse_token
  -> sdjwt.chain.verify_chain
       -> root: sd_jwt.verify + PublicKeyProvider
       -> later hop: kb_sd_jwt.verify
            -> previous verified cnf.jwk
            -> signature
            -> sd_hash / issuer_jwt_hash binding
            -> terminal aud / nonce
```

详细 10-surface measurement(10 个测量面)见：
`evidence/H36_OFFICIAL_BOUNDARY_MATRIX.json`。

## 2. Boundary matrix summary

10 个冻结 surface(测量面)均已形成单一结论：

1. `mandate_facade_verify`: `OBSERVED`。它是 AP2 facade(门面)和输入合同，不是独立密码学实现。
2. `sdjwt_chain_verify`: `OBSERVED`。root 走 `sd_jwt.verify`，后续 hop(委托跳)走 `kb_sd_jwt.verify`。
3. `root_issuer_signature`: `OBSERVED`。官方使用 `SDJWTVerifier` + JWK，并同时处理 disclosure(选择性披露)。
4. `key_provider_and_cnf_delegation`: `OBSERVED`。root key 由 provider(密钥提供器)解析，后续 key 来自上一跳已经验证并解析出的 `cnf.jwk`。
5. `kb_aud_nonce_holder_proof`: `OBSERVED`。KB-SD-JWT 同时校验签名、上一 token 绑定、`aud` / `nonce` 和 terminal/intermediate `cnf` 规则。
6. `checkout_chain_semantics`: `OBSERVED`。这是 constraint/binding semantics(约束/绑定语义)，不是密码学验签。
7. `payment_chain_semantics`: `OBSERVED`。同样是业务约束与交易绑定语义，不做签名校验。
8. `receipt_verification`: `PARTIAL`。Receipt 走独立 compact-JWS(紧凑 JWS) 路径，再做 receipt model/reference 校验；源码中 `ReceiptClient.verify_receipt` 的 EC key annotation(类型标注)与 `jwt_helper.verify_jwt` 实际要求的 `jwcrypto.JWK` 不一致，因此不能把接口边界写成已闭合。
9. `local_generic_es256_reuse`: `PARTIAL`。现有 generic ES256 verifier(通用 ES256 验签器)只能复用密码学原语和最小 trust-fact(可信事实)表达，不能直接复用 AP2 协议语义。
10. `first_executable_slice`: `BLOCKED_BY_DEPENDENCY`。最小值得执行的是 root SD-JWT + terminal KB-SD-JWT 的两跳链；它能一次覆盖 root signature、`cnf` delegation(委托)、previous-token binding(前序令牌绑定) 和 terminal `aud/nonce`，并明确停在 Checkout/Payment semantics 和 Receipt 之前。

## 3. Minimum dependencies

官方 `pyproject.toml` 的相关固定依赖为：

```text
pydantic==2.12.5
jwcrypto==1.5.6
sd-jwt==0.10.4
cryptography==46.0.5
```

只读观察现有 `.task_envs/f1_ap2_v020`：

```text
pydantic      2.12.5   present / exact pin
cryptography  41.0.7   present / pin mismatch
jwcrypto      absent
sd-jwt        absent
```

所以 H-36 没有安装任何东西。下一次如果要真实执行 official crypto/delegation slice(官方密码学/委托切片)，至少需要补齐 `jwcrypto==1.5.6`、`sd-jwt==0.10.4`，并将隔离的下一任务环境对齐 `cryptography==46.0.5`。完整 AP2 sample/demo/ADK 依赖没有被证明是该最小切片的必要条件。

详细依赖证据见：
`evidence/H36_MINIMUM_DEPENDENCIES.json`。

## 4. Crypto vs delegation/constraint boundary

本轮最重要的分层结论是：不能把全部逻辑统称为一个 “AP2 verify”。

```text
Layer 1 — cryptographic/delegation verification(密码学/委托验证)
MandateClient.verify
  -> verify_chain
     -> root issuer signature / disclosures
     -> root key provider
     -> previous cnf.jwk
     -> KB-SD-JWT signature
     -> sd_hash / issuer_jwt_hash
     -> terminal aud / nonce
     -> time claims

Layer 2 — typed business constraint semantics(类型化业务约束语义)
verified payloads
  -> CheckoutMandateChain.parse / verify
     -> checkout constraints / checkout_hash
  -> PaymentMandateChain.parse / verify
     -> payment constraints / checkout reference / transaction_id

Separate path — receipt verification(收据验证)
ReceiptClient.verify_receipt
  -> jwt_helper.verify_jwt (compact JWS)
  -> Receipt model validation
  -> issuer-side reference-store check
```

特别是 `CheckoutMandateChain.extract_parsed_checkout_object` 只解码 `checkout_jwt` payload 并做 schema validation(模式校验)，它本身不验证该 `checkout_jwt` 的签名；因此 Checkout chain semantics 不得被当成密码学验证证据。

## 5. Existing ES256 reuse assessment

现有 `verify_es256_compact_jws_signed_instruction` 已有：

- compact JWS 结构检查；
- `alg=ES256` / `kid` 检查；
- P-256 JWK 转公钥；
- exact signing input(精确签名输入)；
- `ECDSA(SHA-256)` 签名验证；
- caller-owned signer/time binding(调用方提供的签名者/时间绑定)。

但 official AP2 mandate verifier 还要求：

- SD-JWT disclosure resolution(选择性披露解析)；
- root `PublicKeyProvider`；
- verified `cnf.jwk` key transition(密钥迁移)；
- `sd_hash` / `issuer_jwt_hash` previous-token binding；
- AP2 KB-SD-JWT `typ`；
- terminal/intermediate `cnf` 规则；
- terminal `aud` / `nonce`；
- AP2 chain time semantics。

因此复用分类只能是：

`REUSE_PRIMITIVE_ONLY(仅复用密码学原语)`

不能判为 `REUSE_DIRECT(直接复用)`。如果 H-37 获准，应让 AP2-specific glue(AP2 协议特定胶水层)继续拥有上述协议语义，Trust Core(信任核心)仍只接收最小化 verified facts(已验证事实)。

## 6. First executable slice

建议的第一条可执行边界已经收敛为一个，不给多个同优先级方向：

```text
minimal two-hop official mandate verification
root SD-JWT
  -> MandateClient.verify / verify_chain
  -> root key provider + root signature
  -> verified root cnf.jwk
terminal KB-SD-JWT
  -> holder signature
  -> previous-token binding
  -> expected aud / nonce
STOP
  before CheckoutMandateChain semantics
  before PaymentMandateChain semantics
  before Receipt path
```

这条 slice(切片)的最小负例设计应覆盖：

- wrong root key；
- root/terminal signature tamper(签名篡改)；
- broken delegation / `cnf`；
- wrong `aud`；
- wrong `nonce`；
- previous-token binding tamper(`sd_hash` / `issuer_jwt_hash`)。

这些只是下一实验的验证设计，本任务没有实现或运行这些负例。

Overall classification: `DEPENDENCY_BLOCKED`

Next action: Human 明确授权 Evaluator 冻结一个新的 H-37 task-local isolated environment(任务级隔离环境)，只安装/对齐 official AP2 v0.2.0 所需的 `jwcrypto==1.5.6`、`sd-jwt==0.10.4`、`cryptography==46.0.5`（保留 `pydantic==2.12.5`），然后才允许执行上面的两跳 official verification slice；在获得该授权前不进入 H-37。

## 7. L2 evidence

Executor 在提交前按冻结 `VALIDATION_PLAN.yaml` 执行 L2 task gate(L2 任务门禁)。权威机器证据由 runner 写入本任务 `evidence/**`：

- `VP-01` → `evidence/EV-01.meta.json` / `EV-01.stdout.log` / `EV-01.stderr.log`: source pin + product scope audit；
- `VP-02` → `evidence/EV-02.meta.json` / `EV-02.stdout.log` / `EV-02.stderr.log`: official boundary inventory；
- `VP-03` → `evidence/EV-03.meta.json` / `EV-03.stdout.log` / `EV-03.stderr.log`: matrix/dependency/report contract check；
- `VP-04` → `evidence/EV-04.meta.json` / `EV-04.stdout.log` / `EV-04.stderr.log`: existing project baseline smoke；
- `VP-05` → `evidence/EV-05.meta.json` / `EV-05.stdout.log` / `EV-05.stderr.log`: existing experiment smoke；
- gate summary: `evidence/L2-GATE.json` / `evidence/L2-GATE.md`。

本报告不把 runner 的结构校验等同于 Evaluator verdict(评估者结论)；Executor 只提交证据，不签发 `PASS`。

## 8. Limitations

- H-36 是 measurement-only(仅测量)；没有新增产品能力。
- 未修改 `src/**`、`tests/**` 或 pinned AP2 source。
- 未安装/升级依赖，未创建新环境。
- 未调用 public network、external API、Sandbox/testnet、Provider、wallet。
- 未使用生产 credential、PII、银行卡或真实资金。
- 未运行 official SD-JWT/delegation verifier，因为当前环境缺少 `jwcrypto` / `sd-jwt` 且 `cryptography` 与官方 pin 不一致，同时本任务合同明确禁止安装或升级。
- Receipt 路径只完成源码边界测量；其 key type contract(密钥类型合同)存在官方源码内部不一致，需要下一独立切片才能形成运行证据。
- 本任务的 `SUBMITTED_FOR_REVIEW(已提交复核)` 只表示 Executor 已完成冻结测量输出并交给 Evaluator；最终验收由 Evaluator 独立 L3 决定。

## 9. Workspace snapshot / 工作区快照

- HEAD 仍为冻结 baseline `e6931273a983459f167b6e72287a6f05d53a8c26`。
- Official AP2 local source 仍固定为 `v0.2.0 / b4587ac1d055888a73b4b21750973cffba961793`。
- `EV-01` 独立记录 `src_tests_changed=0`；H-36 未修改 `src/**` / `tests/**`。
- 现有 `.task_envs/f1_ap2_v020/` 仅只读观察；H-36 未安装、升级或扩装依赖。
- 未调用网络 API、Sandbox/testnet、Provider、wallet；未使用生产 credential、PII 或真实资金。
- 未 commit、未 push、未 history rewrite。

## 10. Changed files / 改动文件

H-36 Executor 仅产生 task-owned measurement artifacts(任务内测量产物)：

- `docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/REPORT.md`
- `docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/**`

产品实现、产品测试与 pinned AP2 source 均冻结不变。

## L2 Task Gate

- Validation plan: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/VALIDATION_PLAN.yaml
- Gate summary: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/L2-GATE.json
- Gate result: PASS

| VP | Result | Observed |
|---|---|---|
| VP-01 | PASS | AP2 source pin 正确；`src/**` / `tests/**` 相对 baseline 无 H-36 修改 |
| VP-02 | PASS | official verifier/helper 与 local ES256 verifier 边界符号均可复核 |
| VP-03 | PASS | 10-surface matrix、4 项最小依赖与单一总体分类满足冻结合同 |
| VP-04 | PASS | project baseline smoke = 12/12 matched |
| VP-05 | PASS | existing experiment smoke 正常 |

## 11. Acceptance-criterion evidence map

| AC | Executor result | Evidence |
|---|---|---|
| AC-01 Source pin | PASS | EV-01, EV-02 |
| AC-02 Boundary matrix complete | PASS | EV-03, H36_OFFICIAL_BOUNDARY_MATRIX.json |
| AC-03 Crypto vs semantics separated | PASS | EV-02, EV-03, REPORT §4 |
| AC-04 Reuse claim bounded | PASS | EV-02, EV-03, REPORT §5 |
| AC-05 Dependency set bounded | PASS | EV-03, H36_MINIMUM_DEPENDENCIES.json |
| AC-06 First slice explicit | PASS | EV-03, REPORT §6 |
| AC-07 Product frozen | PASS | EV-01, EV-04, EV-05 |
| AC-08 Honest report | PASS | EV-03, EV-05, REPORT §8 |

## EV-01 — Source pin and product scope audit
- AC: AC-01, AC-07
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-01.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-01.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-01.stderr.log

## EV-02 — Official boundary inventory
- AC: AC-01, AC-03, AC-04
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-02.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-02.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-02.stderr.log

## EV-03 — Measurement contract check
- AC: AC-02, AC-03, AC-04, AC-05, AC-06, AC-08
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-03.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-03.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-03.stderr.log

## EV-04 — Project baseline smoke
- AC: AC-07
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-04.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-04.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-04.stderr.log

## EV-05 — Existing experiment smoke
- AC: AC-07, AC-08
- Meta: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-05.meta.json
- Stdout: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-05.stdout.log
- Stderr: docs/05_任务交接/H36_AP2_OFFICIAL_CRYPTO_DELEGATION_BOUNDARY_MEASUREMENT_V1/evidence/EV-05.stderr.log

## Impact comparison

- Measurement evidence: EV-01..EV-05, H36_OFFICIAL_BOUNDARY_MATRIX.json, H36_MINIMUM_DEPENDENCIES.json, H36_PROJECT_BASELINE.json, L2-GATE.json
- Before: F1 已证明 official generated types → Bridge → H-34 → Canonical 可执行，但 official cryptographic/delegation verification 的第一可执行边界、最小依赖和复用边界仍未知。
- After: H-36 将第一可执行边界收敛为 root SD-JWT + terminal KB-SD-JWT 两跳链；generic ES256 复用降界为 `REUSE_PRIMITIVE_ONLY`；最小依赖与 AP2-specific glue 边界已定位。
- Delta: 从“官方密码学/委托验证边界未知”前移到“具体两跳 slice 已定位，但因缺 pinned crypto dependencies 尚未形成运行能力”。
- Guardrail result: `src/**` / `tests/**` 无 H-36 修改；project baseline 12/12 matched；existing experiment smoke PASS；无外部副作用。
- Scope caveat: H-36 是 measurement-only，不构成完整 AP2 conformance、SD-JWT/delegation、Receipt、Sandbox/provider/wallet、生产凭证或真实支付验证。

## Deviations and unresolved items / 偏差与未解决项

- Contract deviation: NONE。
- H-36 未安装任何依赖，符合 dependency authority=false。
- `jwcrypto==1.5.6`、`sd-jwt==0.10.4` 缺失，`cryptography` 现有版本与官方 pin 不一致，因此 official two-hop verifier 未执行。
- Receipt key type contract(密钥类型合同)存在官方源码内部类型标注/实际 helper 输入不一致，本任务只记录为独立后续风险，不混入 mandate slice。
- Complete measurement→L2 cycles consumed: `1/2`。
- Authorization respected: commit=false, push=false, history_rewrite=false, api_call=false。
