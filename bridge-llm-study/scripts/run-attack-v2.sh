#!/bin/bash
# Attack 2 (Sysvar Spoofing) data collection on a fresh local validator:
#   benign     — an honest release with a real relay signature (true negative)
#   vulnerable — release on the v2 variant driven by a forged attestation in a fake sysvar
#   baseline   — the same forgery against the secure bridge (should be blocked)
# Each run gets its own fresh deployment so no run sees another's state.
#
#   bash scripts/run-attack-v2.sh

set -euo pipefail

source "$HOME/.cargo/env"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEYS_DIR="$(mktemp -d)"
trap 'rm -rf "$KEYS_DIR"' EXIT

SECURE_SO="$ROOT/programs/bridge-secure/target/deploy/bridge_secure.so"
V2_SO="$ROOT/programs/variants/v2-sysvar-spoof/target/deploy/bridge_v2_sysvar_spoof.so"
ORACLE_SO="$ROOT/mock-oracle/target/deploy/mock_oracle.so"
BLOB_SO="$ROOT/blob-writer/target/deploy/blob_writer.so"

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
BLOB_ID=$(deploy_fresh "$BLOB_SO" blob-writer)
BENIGN_ID=$(deploy_fresh "$V2_SO" v2-benign)
VULN_ID=$(deploy_fresh "$V2_SO" v2-vulnerable)
BASELINE_ID=$(deploy_fresh "$SECURE_SO" secure-baseline)
echo "    oracle:          $ORACLE_ID"
echo "    blob writer:     $BLOB_ID"
echo "    v2 (benign):     $BENIGN_ID"
echo "    v2 (vulnerable): $VULN_ID"
echo "    secure (baseline):$BASELINE_ID"

cd "$ROOT/client"
export ORACLE_PROGRAM_ID="$ORACLE_ID"
export BLOB_WRITER_ID="$BLOB_ID"

echo
echo "==> benign release on the v2 variant (real relay signature)"
BRIDGE_PROGRAM_ID="$BENIGN_ID" npx tsx src/exploits/exploit-v2.ts benign

echo
echo "==> sysvar-spoof release against the v2 variant"
BRIDGE_PROGRAM_ID="$VULN_ID" npx tsx src/exploits/exploit-v2.ts vulnerable

echo
echo "==> same forgery against the secure baseline"
BRIDGE_PROGRAM_ID="$BASELINE_ID" npx tsx src/exploits/exploit-v2.ts baseline

echo
echo "==> done. traces in traces/v2-sysvar-spoof/"
