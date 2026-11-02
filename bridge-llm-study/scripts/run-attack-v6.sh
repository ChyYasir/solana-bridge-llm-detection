#!/bin/bash
# Attack 6 (Arbitrary CPI) data collection on a fresh local validator:
#   benign     — an honest user redeems through the real SPL Token program (true negative)
#   vulnerable — redeem on the v6 variant with the attacker's program substituted for the
#                token program; the vault is drained
#   baseline   — the same substitution against the secure bridge (should be blocked)
# Each run gets its own fresh deployment so no run sees another's state.
#
#   bash scripts/run-attack-v6.sh

set -euo pipefail

source "$HOME/.cargo/env"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEYS_DIR="$(mktemp -d)"
trap 'rm -rf "$KEYS_DIR"' EXIT

SECURE_SO="$ROOT/programs/bridge-secure/target/deploy/bridge_secure.so"
V6_SO="$ROOT/programs/variants/v6-arbitrary-cpi/target/deploy/bridge_v6_arbitrary_cpi.so"
ORACLE_SO="$ROOT/mock-oracle/target/deploy/mock_oracle.so"
EVIL_SO="$ROOT/attacker-program/target/deploy/evil_cpi.so"

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
EVIL_ID=$(deploy_fresh "$EVIL_SO" evil-cpi)
BENIGN_ID=$(deploy_fresh "$V6_SO" v6-benign)
VULN_ID=$(deploy_fresh "$V6_SO" v6-vulnerable)
BASELINE_ID=$(deploy_fresh "$SECURE_SO" secure-baseline)
echo "    oracle:          $ORACLE_ID"
echo "    evil program:    $EVIL_ID"
echo "    v6 (benign):     $BENIGN_ID"
echo "    v6 (vulnerable): $VULN_ID"
echo "    secure (baseline):$BASELINE_ID"

cd "$ROOT/client"
export ORACLE_PROGRAM_ID="$ORACLE_ID"
export EVIL_PROGRAM_ID="$EVIL_ID"

echo
echo "==> benign redeem on the v6 variant (real token program)"
BRIDGE_PROGRAM_ID="$BENIGN_ID" npx tsx src/exploits/exploit-v6.ts benign

echo
echo "==> arbitrary-CPI drain against the v6 variant"
BRIDGE_PROGRAM_ID="$VULN_ID" npx tsx src/exploits/exploit-v6.ts vulnerable

echo
echo "==> same substitution against the secure baseline"
BRIDGE_PROGRAM_ID="$BASELINE_ID" npx tsx src/exploits/exploit-v6.ts baseline

echo
echo "==> done. traces in traces/v6-arbitrary-cpi/"
