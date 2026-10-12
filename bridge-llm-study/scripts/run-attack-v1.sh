#!/bin/bash
# Resets the local validator, deploys bridge-secure + v1-mint-confusion + mock-oracle,
# then runs the v1 exploit against both (vulnerable, then baseline) exactly once each.
# Safe to re-run any time — it always starts from a fresh chain.

set -euo pipefail

source "$HOME/.cargo/env"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> stopping any running validator"
pkill -f solana-test-validator || true
sleep 2

echo "==> wiping old chain data"
cd "$ROOT"
rm -rf test-ledger

echo "==> starting a fresh validator"
nohup solana-test-validator --reset > /tmp/validator.log 2>&1 &
disown

echo "==> waiting for it to come up"
for i in $(seq 1 30); do
  if solana cluster-version --url localhost > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

solana config set --url localhost > /dev/null
solana airdrop 50 > /dev/null

echo "==> deploying programs"
BRIDGE_ID=$(solana program deploy "$ROOT/programs/bridge-secure/target/deploy/bridge_secure.so" \
  | grep "Program Id" | awk '{print $3}')
V1_ID=$(solana program deploy "$ROOT/programs/variants/v1-mint-confusion/target/deploy/bridge_v1_mint_confusion.so" \
  | grep "Program Id" | awk '{print $3}')
ORACLE_ID=$(solana program deploy "$ROOT/mock-oracle/target/deploy/mock_oracle.so" \
  | grep "Program Id" | awk '{print $3}')

echo "    bridge-secure:      $BRIDGE_ID"
echo "    v1-mint-confusion:  $V1_ID"
echo "    mock-oracle:        $ORACLE_ID"

echo "==> writing client/.env (baseline = bridge-secure)"
cat > "$ROOT/client/.env" <<EOF
BRIDGE_PROGRAM_ID=$BRIDGE_ID
ORACLE_PROGRAM_ID=$ORACLE_ID
EOF

cd "$ROOT/client"

echo
echo "==> running exploit against the VULNERABLE variant"
BRIDGE_PROGRAM_ID="$V1_ID" npx tsx src/exploits/exploit-v1.ts vulnerable

echo
echo "==> running exploit against the SECURE BASELINE (negative control)"
BRIDGE_PROGRAM_ID="$BRIDGE_ID" npx tsx src/exploits/exploit-v1.ts baseline

echo
echo "==> done. traces saved under traces/v1-mint-confusion/"
