// Builds the normal relay-delay distribution for one bridge: many honest
// lock -> release cycles, D recorded per cycle. The relay waits the same
// base-plus-jitter delay every other script uses (lib/tx.ts relayWait).
//
//   npx tsx src/recon.ts [cycles]
//   RELAY_DELAY_MS=2000 RELAY_JITTER_MS=1000 npx tsx src/recon.ts 40

import { Keypair, SystemProgram, Ed25519Program } from "@solana/web3.js";
import { createMint, getOrCreateAssociatedTokenAccount, mintTo } from "@solana/spl-token";
import { connection, loadDefaultKeypair, fundWithSol } from "./lib/connection.js";
import { ORACLE_PROGRAM_ID, BRIDGE_PROGRAM_ID } from "./lib/programs.js";
import { vaultAuthorityPda, wrappedMintPda, messageAttestationBytes, initializeIx, lockIx, releaseIx } from "./lib/bridge.js";
import { setPriceIx } from "./lib/oracle.js";
import { saveTrace } from "./lib/trace.js";
import { send, relayWait, relayDelay, Step, RELAY_DELAY_MS, RELAY_JITTER_MS } from "./lib/tx.js";
import { summarize } from "./lib/stats.js";

const PRICE_SCALE = 1_000_000n;
const DECIMALS = 6;

async function main() {
  const cycles = Number(process.argv[2] ?? 40);
  const admin = loadDefaultKeypair();
  const relayAuthority = Keypair.generate();
  const user = Keypair.generate();
  const setupSteps: Step[] = [];

  await fundWithSol(user.publicKey, 5);
  const collateralMint = await createMint(connection, admin, admin.publicKey, null, DECIMALS);

  const oracleAccount = Keypair.generate();
  const rent = await connection.getMinimumBalanceForRentExemption(16);
  await send("setup: oracle", setupSteps, admin, [
    SystemProgram.createAccount({
      fromPubkey: admin.publicKey,
      newAccountPubkey: oracleAccount.publicKey,
      lamports: rent,
      space: 16,
      programId: ORACLE_PROGRAM_ID,
    }),
    setPriceIx({ authority: admin.publicKey, priceAccount: oracleAccount.publicKey, price: PRICE_SCALE }),
  ], [oracleAccount]);

  await getOrCreateAssociatedTokenAccount(connection, admin, collateralMint, vaultAuthorityPda(), true);
  await send("setup: initialize", setupSteps, admin, [
    initializeIx({
      admin: admin.publicKey,
      approvedCollateralMint: collateralMint,
      oracleFeed: oracleAccount.publicKey,
      relayAuthority: relayAuthority.publicKey,
      feeBps: 100,
    }),
  ], []);

  const userCollateral = await getOrCreateAssociatedTokenAccount(connection, admin, collateralMint, user.publicKey);
  await mintTo(connection, admin, collateralMint, userCollateral.address, admin, 1_000n * 10n ** BigInt(DECIMALS));
  const userWrapped = await getOrCreateAssociatedTokenAccount(connection, admin, wrappedMintPda(), user.publicKey);

  const amount = 1n * 10n ** BigInt(DECIMALS);
  const samples: number[] = [];

  for (let i = 0; i < cycles; i++) {
    const nonce = BigInt(i);
    const steps: Step[] = [];

    // Keep the price fresh across many cycles, like a live feed. Done before the
    // lock so it isn't counted in D — every script must measure the same interval.
    await send("oracle refresh", steps, admin, [
      setPriceIx({ authority: admin.publicKey, priceAccount: oracleAccount.publicKey, price: PRICE_SCALE }),
    ], []);

    await send("lock", steps, user, [
      lockIx({ user: user.publicKey, userTokenAccount: userCollateral.address, collateralMint, amount, recipient: user.publicKey, nonce }),
    ], []);

    await relayWait();

    const attestation = Ed25519Program.createInstructionWithPrivateKey({
      privateKey: relayAuthority.secretKey,
      message: messageAttestationBytes(nonce, user.publicKey, amount),
    });
    await send("release", steps, admin, [
      attestation,
      releaseIx({ relay: admin.publicKey, oracleFeed: oracleAccount.publicKey, recipientWrappedAccount: userWrapped.address, nonce }),
    ], []);

    const d = relayDelay(steps, "lock", "release");
    if (d !== undefined) samples.push(d);
    console.log(`cycle ${i + 1}/${cycles}: D = ${d} ms`);
  }

  const summary = summarize(samples);
  console.log(summary);

  saveTrace("recon", "baseline-d", {
    programId: BRIDGE_PROGRAM_ID.toBase58(),
    relayPolicy: { baseDelayMs: RELAY_DELAY_MS, jitterMs: RELAY_JITTER_MS },
    summary,
    samples,
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
