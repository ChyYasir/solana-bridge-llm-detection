#!/bin/bash
# Attack 5 (Missing Signer) data collection on a fresh local validator:
#   vulnerable — admin-takeover against the v5 variant
#   baseline   — the same strike against the secure bridge (should be blocked)
# Each run gets its own fresh deployment so no run sees another's state.
#
#   bash scripts/run-attack-v5.sh

set -euo pipefail

source "$HOME/.cargo/env"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEYS_DIR="$(mktemp -d)"
trap 'rm -rf "$KEYS_DIR"' EXIT

SECURE_SO="$ROOT/programs/bridge-secure/target/deploy/bridge_secure.so"
V5_SO="$ROOT/programs/variants/v5-missing-signer/target/deploy/bridge_v5_missing_signer.so"
ORACLE_SO="$ROOT/mock-oracle/target/deploy/mock_oracle.so"

deploy_fresh() {
  local so="$1" name="$2"
  solana-keygen new --no-bip39-passphrase --silent -o "$KEYS_DIR/$name.json" > /dev/null
  solana program deploy "$so" --program-id "$KEYS_DIR/$name.json" > /dev/null 2>&1
  solana address -k "$KEYS_DIR/$name.json"
}

echo "==> fresh validator"
pkill -f solana-test-validator || true
sleep 2
cd "$ROOT"
rm -rf test-ledger
nohup solana-test-validator --reset > /tmp/validator.log 2>&1 &
disown
for i in $(seq 1 30); do
  solana cluster-version --url localhost > /dev/null 2>&1 && break
  sleep 1
done
solana config set --url localhost > /dev/null
solana airdrop 100 > /dev/null

echo "==> deploying"
ORACLE_ID=$(deploy_fresh "$ORACLE_SO" oracle)
VULN_ID=$(deploy_fresh "$V5_SO" v5-vulnerable)
BASELINE_ID=$(deploy_fresh "$SECURE_SO" secure-baseline)
echo "    oracle:          $ORACLE_ID"
echo "    v5 (vulnerable): $VULN_ID"
echo "    secure (baseline):$BASELINE_ID"

cd "$ROOT/client"
export ORACLE_PROGRAM_ID="$ORACLE_ID"

echo
echo "==> admin-takeover against the v5 variant"
BRIDGE_PROGRAM_ID="$VULN_ID" npx tsx src/exploits/exploit-v5.ts vulnerable

echo
echo "==> same strike against the secure baseline"
BRIDGE_PROGRAM_ID="$BASELINE_ID" npx tsx src/exploits/exploit-v5.ts baseline

echo
echo "==> done. traces in traces/v5-missing-signer/"
