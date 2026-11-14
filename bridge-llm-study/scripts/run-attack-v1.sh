#!/bin/bash
# Full Attack 1 data collection on a fresh local validator:
#   1. benign  — one ordinary user session on the v1 variant (true negative)
#   2. vulnerable — the exploit against the v1 variant
#   3. baseline   — the same exploit against the secure baseline (blocked attempt)
# Each run gets its own fresh deployment of the program, so no run sees another's state.
#
#   bash scripts/run-attack-v1.sh

set -euo pipefail

source "$HOME/.cargo/env"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEYS_DIR="$(mktemp -d)"
trap 'rm -rf "$KEYS_DIR"' EXIT

SECURE_SO="$ROOT/programs/bridge-secure/target/deploy/bridge_secure.so"
V1_SO="$ROOT/programs/variants/v1-mint-confusion/target/deploy/bridge_v1_mint_confusion.so"
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
BENIGN_ID=$(deploy_fresh "$V1_SO" v1-benign)
VULN_ID=$(deploy_fresh "$V1_SO" v1-vulnerable)
BASELINE_ID=$(deploy_fresh "$SECURE_SO" secure-baseline)
echo "    oracle:          $ORACLE_ID"
echo "    v1 (benign):     $BENIGN_ID"
echo "    v1 (vulnerable): $VULN_ID"
echo "    secure (exploit):$BASELINE_ID"

cd "$ROOT/client"
export ORACLE_PROGRAM_ID="$ORACLE_ID"

echo
echo "==> benign session on the v1 variant"
BRIDGE_PROGRAM_ID="$BENIGN_ID" npx tsx src/happy-path.ts benign

echo
echo "==> exploit against the v1 variant"
BRIDGE_PROGRAM_ID="$VULN_ID" npx tsx src/exploits/exploit-v1.ts vulnerable

echo
echo "==> exploit against the secure baseline"
BRIDGE_PROGRAM_ID="$BASELINE_ID" npx tsx src/exploits/exploit-v1.ts baseline

echo
echo "==> done. traces in traces/v1-mint-confusion/"
