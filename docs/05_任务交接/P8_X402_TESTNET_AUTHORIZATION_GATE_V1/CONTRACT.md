# Task Contract

Task ID: `P8-X402-TESTNET-AUTHORIZATION-GATE-V1`  
Workflow: `evaluator-executor-workflow/v2`  
State: `DRAFT_CONTRACT`  
Baseline HEAD: `8acaa9e4319240d258f14d8a23b1f15cc71d09b6`

## 1. Context

P8-A offline x402 conformance has passed. The next logical stage is a bounded interaction with a public x402 testnet environment.

That stage is not authorized by the current router because it may require:

```text
external HTTP/API calls
public facilitator interaction
creation or use of a dedicated test wallet
local signing with a test key
faucet or test-token handling
testnet transaction submission
```

No real/mainnet funds are needed or permitted.

## 2. Single objective

Obtain and record the exact human authorization boundary required to decide whether a separate minimal public-testnet smoke-test implementation contract may be frozen. This package performs no network, API, wallet, signing, faucet or transaction action.

## 3. Missing human decisions

### Decision A — external interaction

Choose one:

```text
AUTHORIZE_TESTNET_NETWORK_CALLS
DO_NOT_AUTHORIZE_TESTNET_NETWORK_CALLS
```

Authorization would be limited to official/public x402 documentation and a public testnet facilitator endpoint. It would not authorize production APIs, customer systems or mainnet.

### Decision B — test network

Choose one, only if Decision A is authorized:

```text
BASE_SEPOLIA
SOLANA_DEVNET
EVALUATOR_SELECTS_LOWEST_COMPLEXITY_OPTION
```

### Decision C — wallet and signing boundary

Choose one, only if Decision A is authorized:

```text
AUTHORIZE_EPHEMERAL_TEST_WALLET_AND_TEST_SIGNING
USE_USER_PROVIDED_DEDICATED_TEST_WALLET
DO_NOT_AUTHORIZE_WALLET_OR_SIGNING
```

An ephemeral test wallet would contain no real assets and would be used only for the bounded testnet run. Private material must not be committed, printed in reports or pushed remotely.

### Decision D — faucet and test tokens

Choose one, only if wallet/signing is authorized:

```text
AUTHORIZE_PUBLIC_FAUCET_AND_TEST_TOKEN_USE
USER_PROVIDES_TEST_TOKEN_BALANCE
DO_NOT_AUTHORIZE_FAUCET_OR_TEST_TOKENS
```

## 4. Acceptance criteria

### AC-01 — explicit network decision

The user explicitly authorizes or denies bounded public-testnet network/API calls. General permission to continue the project does not satisfy this criterion.

### AC-02 — exact network selection

If network calls are authorized, the decision records Base Sepolia, Solana Devnet, or delegated lowest-complexity selection.

### AC-03 — exact wallet/signing boundary

If network calls are authorized, the decision explicitly authorizes an ephemeral test wallet/signing, identifies a user-provided dedicated test wallet, or denies wallet/signing.

### AC-04 — exact test-token boundary

If wallet/signing is authorized, the decision explicitly authorizes a public faucet/test tokens, identifies a user-provided test balance, or denies faucet/test-token use.

### AC-05 — hard prohibitions preserved

The recorded decision preserves these prohibitions unless a future contract separately changes them:

```text
real funds
mainnet transaction
production merchant or facilitator credentials
customer or card data
long-lived wallet or unlimited approval
commit or push of secrets
background or recurring network activity
```

## 5. Allowed scope

- `docs/05_任务交接/P8_X402_TESTNET_AUTHORIZATION_GATE_V1/CONTRACT.md`
- `docs/05_任务交接/P8_X402_TESTNET_AUTHORIZATION_GATE_V1/HUMAN_DECISION.md`
- `CURRENT.md`
- `docs/02_未来规划/整体修正执行计划_20260729.md`（仅状态同步）

No product source, test, fixture, wallet or network file is in scope.

## 6. Exclusions

- No external HTTP/API call.
- No facilitator call.
- No wallet creation or use.
- No signing or private-key handling.
- No faucet or test-token request.
- No testnet/mainnet transaction.
- No real funds.
- No product implementation.
- No dependency installation.
- No commit, push or history rewrite.

## 7. Validation plan

| VP | Validation | Expected | AC |
|---|---|---|---|
| VP-01 | Review the user's explicit authorization statement | Decision A is unambiguous | AC-01 |
| VP-02 | If authorized, verify network selection is explicit | One allowed network choice is recorded | AC-02 |
| VP-03 | If authorized, verify wallet/signing boundary is explicit | One allowed wallet/signing choice is recorded | AC-03 |
| VP-04 | If applicable, verify faucet/test-token boundary is explicit | One allowed token choice is recorded | AC-04 |
| VP-05 | Verify hard prohibitions remain in the recorded decision | No real/mainnet/production/secret/background authority is implied | AC-05 |
| VP-06 | Workflow validator | No `BLOCKING` finding after routing the next state | handoff |

## 8. Expected continuation

If all required decisions authorize a viable testnet path, the Evaluator may create and freeze a separate task such as:

```text
P8-X402-PUBLIC-TESTNET-SMOKE-V1
```

Its first version should contain only:

```text
one network
one public facilitator
one local seller endpoint or official sample
one dedicated buyer wallet
one successful low-value testnet flow
binding and evidence capture
no production claim
```

If network calls or wallet/signing are denied, record the decision and close P8 at the accepted offline harness.

## 9. Stop conditions

Stop without creating an Executor task if:

- Decision A is absent or ambiguous;
- network calls are authorized but network choice is absent;
- wallet/signing is required but not explicitly authorized;
- faucet/test tokens are required but not explicitly authorized;
- any wording could be interpreted as authorizing real funds, mainnet, production credentials or secret publication;
- the requested scope exceeds one bounded smoke test.

## 10. Current authorization

```yaml
authorization_commit: false
authorization_push: false
authorization_history_rewrite: false
authorization_api_call: false
authorization_network_call: false
authorization_wallet_creation: false
authorization_signing: false
authorization_faucet: false
authorization_testnet_funds: false
authorization_mainnet: false
authorization_real_funds: false
```

## 11. Why the contract remains draft

The exact decisions in AC-01 through AC-04 are missing. Until the user supplies them, this package remains `DRAFT_CONTRACT / Evaluator`; it must not route to an Executor or perform any external action.
