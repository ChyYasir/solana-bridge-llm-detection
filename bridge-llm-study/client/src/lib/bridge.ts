import {
  PublicKey,
  TransactionInstruction,
  SYSVAR_INSTRUCTIONS_PUBKEY,
  SystemProgram,
} from "@solana/web3.js";
import { TOKEN_PROGRAM_ID } from "@solana/spl-token";
import { BRIDGE_PROGRAM_ID } from "./programs.js";

export function configPda() {
  return PublicKey.findProgramAddressSync([Buffer.from("config")], BRIDGE_PROGRAM_ID)[0];
}

export function vaultPda() {
  return PublicKey.findProgramAddressSync([Buffer.from("vault")], BRIDGE_PROGRAM_ID)[0];
}

export function wrappedMintPda() {
  return PublicKey.findProgramAddressSync([Buffer.from("wrapped_mint")], BRIDGE_PROGRAM_ID)[0];
}

export function messagePda(nonce: bigint) {
  const nonceBuf = Buffer.alloc(8);
  nonceBuf.writeBigUInt64LE(nonce);
  return PublicKey.findProgramAddressSync([Buffer.from("message"), nonceBuf], BRIDGE_PROGRAM_ID)[0];
}

export function messageAttestationBytes(nonce: bigint, recipient: PublicKey, amount: bigint): Buffer {
  const buf = Buffer.alloc(8 + 32 + 8);
  buf.writeBigUInt64LE(nonce, 0);
  recipient.toBuffer().copy(buf, 8);
  buf.writeBigUInt64LE(amount, 40);
  return buf;
}

export function initializeIx(params: {
  admin: PublicKey;
  approvedCollateralMint: PublicKey;
  oracleFeed: PublicKey;
  relayAuthority: PublicKey;
  feeBps: number;
}): TransactionInstruction {
  const data = Buffer.alloc(3);
  data.writeUInt8(0, 0);
  data.writeUInt16LE(params.feeBps, 1);

  return new TransactionInstruction({
    programId: BRIDGE_PROGRAM_ID,
    data,
    keys: [
      { pubkey: params.admin, isSigner: true, isWritable: true },
      { pubkey: configPda(), isSigner: false, isWritable: true },
      { pubkey: vaultPda(), isSigner: false, isWritable: true },
      { pubkey: wrappedMintPda(), isSigner: false, isWritable: true },
      { pubkey: params.approvedCollateralMint, isSigner: false, isWritable: false },
      { pubkey: params.oracleFeed, isSigner: false, isWritable: false },
      { pubkey: params.relayAuthority, isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
    ],
  });
}

export function lockIx(params: {
  user: PublicKey;
  userTokenAccount: PublicKey;
  amount: bigint;
  recipient: PublicKey;
  nonce: bigint;
}): TransactionInstruction {
  const data = Buffer.alloc(1 + 8 + 32);
  data.writeUInt8(1, 0);
  data.writeBigUInt64LE(params.amount, 1);
  params.recipient.toBuffer().copy(data, 9);

  return new TransactionInstruction({
    programId: BRIDGE_PROGRAM_ID,
    data,
    keys: [
      { pubkey: params.user, isSigner: true, isWritable: false },
      { pubkey: params.userTokenAccount, isSigner: false, isWritable: true },
      { pubkey: vaultPda(), isSigner: false, isWritable: true },
      { pubkey: configPda(), isSigner: false, isWritable: true },
      { pubkey: messagePda(params.nonce), isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
    ],
  });
}

export function releaseIx(params: {
  relay: PublicKey;
  oracleFeed: PublicKey;
  recipientWrappedAccount: PublicKey;
  nonce: bigint;
}): TransactionInstruction {
  const data = Buffer.alloc(1 + 8);
  data.writeUInt8(2, 0);
  data.writeBigUInt64LE(params.nonce, 1);

  return new TransactionInstruction({
    programId: BRIDGE_PROGRAM_ID,
    data,
    keys: [
      { pubkey: params.relay, isSigner: true, isWritable: false },
      { pubkey: configPda(), isSigner: false, isWritable: true },
      { pubkey: messagePda(params.nonce), isSigner: false, isWritable: true },
      { pubkey: SYSVAR_INSTRUCTIONS_PUBKEY, isSigner: false, isWritable: false },
      { pubkey: params.oracleFeed, isSigner: false, isWritable: false },
      { pubkey: wrappedMintPda(), isSigner: false, isWritable: true },
      { pubkey: params.recipientWrappedAccount, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
  });
}

export function redeemIx(params: {
  user: PublicKey;
  userWrappedAccount: PublicKey;
  userCollateralAccount: PublicKey;
  feeRecipient: PublicKey;
  amount: bigint;
}): TransactionInstruction {
  const data = Buffer.alloc(1 + 8);
  data.writeUInt8(3, 0);
  data.writeBigUInt64LE(params.amount, 1);

  return new TransactionInstruction({
    programId: BRIDGE_PROGRAM_ID,
    data,
    keys: [
      { pubkey: params.user, isSigner: true, isWritable: false },
      { pubkey: params.userWrappedAccount, isSigner: false, isWritable: true },
      { pubkey: wrappedMintPda(), isSigner: false, isWritable: true },
      { pubkey: vaultPda(), isSigner: false, isWritable: true },
      { pubkey: params.userCollateralAccount, isSigner: false, isWritable: true },
      { pubkey: params.feeRecipient, isSigner: false, isWritable: true },
      { pubkey: configPda(), isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
  });
}
