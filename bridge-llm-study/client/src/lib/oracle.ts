import { PublicKey, TransactionInstruction } from "@solana/web3.js";
import { ORACLE_PROGRAM_ID } from "./programs.js";

export function setPriceIx(params: {
  authority: PublicKey;
  priceAccount: PublicKey;
  price: bigint;
}): TransactionInstruction {
  const data = Buffer.alloc(8);
  data.writeBigUInt64LE(params.price, 0);

  return new TransactionInstruction({
    programId: ORACLE_PROGRAM_ID,
    data,
    keys: [
      { pubkey: params.authority, isSigner: true, isWritable: false },
      { pubkey: params.priceAccount, isSigner: false, isWritable: true },
    ],
  });
}
