#!/usr/bin/env bash
set -euo pipefail
printf 'HEAD='
git rev-parse HEAD
printf 'HASHES\n'
sha256sum   src/agentic_payment_experiment/webshop_runtime_gate.py   tests/test_webshop_runtime_gate.py   samples/external/webshop/checkout_snapshot_anomalies_v1.json   scripts/validation/webshop/run_checkout_snapshot_anomalies.py
printf 'PROTECTED_TRACKED_DIFFS\n'
git diff --exit-code --   src/agentic_payment_experiment/order_validation.py   src/agentic_payment_experiment/validator.py
printf 'STATIC_REUSE\n'
grep -n 'authorized_order=authorized_snapshot.order\|final_order=adaptation.order'   src/agentic_payment_experiment/webshop_runtime_gate.py
if grep -n 'from \.order_validation import\|validate_order('   src/agentic_payment_experiment/webshop_runtime_gate.py; then
  echo 'duplicate order state machine detected' >&2
  exit 1
fi
printf 'AUTHORIZATIONS\n'
printf '%s\n' 'network=false api=false dependency_install=false create_environment=false webshop_runtime=false buy_now=false payment_side_effect=false commit=false push=false history_rewrite=false'
