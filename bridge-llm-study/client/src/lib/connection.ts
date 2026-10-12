import { Connection, Keypair, PublicKey, LAMPORTS_PER_SOL } from "@solana/web3.js";
import { readFileSync } from "fs";
import { homedir } from "os";
import { join } from "path";

export const connection = new Connection("http://127.0.0.1:8899", "confirmed");

export function loadDefaultKeypair(): Keypair {
  const path = join(homedir(), ".config", "solana", "id.json");
  const secret = JSON.parse(readFileSync(path, "utf-8"));
  return Keypair.fromSecretKey(Uint8Array.from(secret));
}

export async function fundWithSol(pubkey: PublicKey, sol: number) {
  const sig = await connection.requestAirdrop(pubkey, sol * LAMPORTS_PER_SOL);
  await connection.confirmTransaction(sig, "confirmed");
}
