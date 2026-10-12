import { Keypair, SystemProgram, Ed25519Program } from "@solana/web3.js";
import {
  createMint,
  getOrCreateAssociatedTokenAccount,
  mintTo,
  getAccount,
} from "@solana/spl-token";
import { connection, loadDefaultKeypair, fundWithSol } from "./lib/connection.js";
import { ORACLE_PROGRAM_ID, BRIDGE_PROGRAM_ID } from "./lib/programs.js";
import {
  vaultAta,
  vaultAuthorityPda,
  wrappedMintPda,
  messageAttestationBytes,
  initializeIx,
  lockIx,
  releaseIx,
  redeemIx,
} from "./lib/bridge.js";
import { setPriceIx } from "./lib/oracle.js";
import { saveTrace } from "./lib/trace.js";
import { send, relayWait, relayDelay, Step } from "./lib/tx.js";

const PRICE_SCALE = 1_000_000n;
const DECIMALS = 6;

async function main() {
  const traceLabel = process.argv[2]; // optional: save a trace under this label if provided
  const steps: Step[] = [];
  const admin = loadDefaultKeypair();
  const relayAuthority = Keypair.generate();
  const user = Keypair.generate();

  console.log("funding user wallet...");
  await fundWithSol(user.publicKey, 5);

  console.log("creating collateral mint...");
  const collateralMint = await createMint(connection, admin, admin.publicKey, null, DECIMALS);

  console.log("creating oracle price account...");
  const oracleAccount = Keypair.generate();
  const rent = await connection.getMinimumBalanceForRentExemption(16);
  await send(
    "setup: create oracle price account",
    steps,
    admin,
    [
      SystemProgram.createAccount({
        fromPubkey: admin.publicKey,
        newAccountPubkey: oracleAccount.publicKey,
        lamports: rent,
        space: 16,
        programId: ORACLE_PROGRAM_ID,
      }),
      setPriceIx({ authority: admin.publicKey, priceAccount: oracleAccount.publicKey, price: PRICE_SCALE }),
    ],
    [oracleAccount],
  );

  console.log("creating vault for the approved collateral mint...");
  await getOrCreateAssociatedTokenAccount(connection, admin, collateralMint, vaultAuthorityPda(), true);

  console.log("initializing bridge...");
  await send(
    "setup: initialize bridge",
    steps,
    admin,
    [
      initializeIx({
        admin: admin.publicKey,
        approvedCollateralMint: collateralMint,
        oracleFeed: oracleAccount.publicKey,
        relayAuthority: relayAuthority.publicKey,
        feeBps: 100,
      }),
    ],
    [],
  );

  const userCollateralAccount = await getOrCreateAssociatedTokenAccount(connection, admin, collateralMint, user.publicKey);
  await mintTo(connection, admin, collateralMint, userCollateralAccount.address, admin, 1_000n * 10n ** BigInt(DECIMALS));

  const userWrappedAccount = await getOrCreateAssociatedTokenAccount(connection, admin, wrappedMintPda(), user.publicKey);
  const adminFeeAccount = await getOrCreateAssociatedTokenAccount(connection, admin, collateralMint, admin.publicKey);

  const lockAmount = 100n * 10n ** BigInt(DECIMALS);
  const nonce = 0n;

  console.log("locking collateral...");
  await send(
    "honest user: lock",
    steps,
    user,
    [
      lockIx({
        user: user.publicKey,
        userTokenAccount: userCollateralAccount.address,
        collateralMint,
        amount: lockAmount,
        recipient: user.publicKey,
        nonce,
      }),
    ],
    [],
  );

  await relayWait();

  console.log("relay: attesting and releasing...");
  const attestationMessage = messageAttestationBytes(nonce, user.publicKey, lockAmount);
  const attestationIx = Ed25519Program.createInstructionWithPrivateKey({
    privateKey: relayAuthority.secretKey,
    message: attestationMessage,
  });
  await send(
    "relay: release",
    steps,
    admin,
    [
      attestationIx,
      releaseIx({
        relay: admin.publicKey,
        oracleFeed: oracleAccount.publicKey,
        recipientWrappedAccount: userWrappedAccount.address,
        nonce,
      }),
    ],
    [],
  );

  const wrappedBalance = (await getAccount(connection, userWrappedAccount.address)).amount;
  console.log(`wrapped tokens received: ${wrappedBalance}`);

  console.log("redeeming...");
  await send(
    "honest user: redeem",
    steps,
    user,
    [
      redeemIx({
        user: user.publicKey,
        userWrappedAccount: userWrappedAccount.address,
        approvedCollateralMint: collateralMint,
        userCollateralAccount: userCollateralAccount.address,
        feeRecipient: adminFeeAccount.address,
        amount: wrappedBalance,
      }),
    ],
    [],
  );

  const finalUserCollateral = (await getAccount(connection, userCollateralAccount.address)).amount;
  const finalAdminFee = (await getAccount(connection, adminFeeAccount.address)).amount;
  const finalUserWrapped = (await getAccount(connection, userWrappedAccount.address)).amount;
  const finalVault = (await getAccount(connection, vaultAta(collateralMint))).amount;

  console.log({
    finalUserCollateral: finalUserCollateral.toString(),
    finalAdminFee: finalAdminFee.toString(),
    finalUserWrapped: finalUserWrapped.toString(),
    finalVault: finalVault.toString(),
  });

  const expectedUserCollateral = 1_000n * 10n ** BigInt(DECIMALS) - lockAmount + (lockAmount - lockAmount / 100n);
  const expectedAdminFee = lockAmount / 100n;

  if (finalUserCollateral !== expectedUserCollateral || finalAdminFee !== expectedAdminFee || finalUserWrapped !== 0n || finalVault !== 0n) {
    throw new Error("happy path did not reconcile — see values above");
  }

  console.log("OK: happy path reconciled 1:1 (minus fee, accounted for)");

  if (traceLabel) {
    saveTrace("v1-mint-confusion", traceLabel, {
      programId: BRIDGE_PROGRAM_ID.toBase58(),
      relayDelayMs: relayDelay(steps, "honest user: lock", "relay: release"),
      balances: {
        finalUserCollateral: finalUserCollateral.toString(),
        finalAdminFee: finalAdminFee.toString(),
        finalUserWrapped: finalUserWrapped.toString(),
        finalVault: finalVault.toString(),
      },
      steps,
    });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
