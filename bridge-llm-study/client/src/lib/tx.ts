import { Keypair, Transaction, TransactionInstruction } from "@solana/web3.js";
import { connection } from "./connection.js";

export type Step = {
  name: string;
  signature?: string;
  slot?: number;
  submittedAt: number;
  confirmedAt?: number;
  error?: string;
  logs?: string[];
};

export async function send(
  label: string,
  steps: Step[],
  payer: Keypair,
  ixs: TransactionInstruction[],
  signers: Keypair[],
) {
  const tx = new Transaction().add(...ixs);
  const submittedAt = Date.now();
  try {
    const sig = await connection.sendTransaction(tx, [payer, ...signers]);
    await connection.confirmTransaction(sig, "confirmed");
    const confirmedAt = Date.now();
    const parsed = await connection.getParsedTransaction(sig, { commitment: "confirmed", maxSupportedTransactionVersion: 0 });
    steps.push({
      name: label,
      signature: sig,
      slot: parsed?.slot,
      submittedAt,
      confirmedAt,
      logs: parsed?.meta?.logMessages ?? [],
    });
    return sig;
  } catch (err: any) {
    steps.push({
      name: label,
      submittedAt,
      error: err.message ?? String(err),
      logs: err.logs ?? err.transactionLogs ?? [],
    });
    throw err;
  }
}

export function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/// The honest relay's wait before releasing: a base delay plus random jitter,
/// standing in for observation/finality time. Shared by every script so benign
/// and exploit runs all see the same relay behaviour.
export const RELAY_DELAY_MS = Number(process.env.RELAY_DELAY_MS ?? 2000);
export const RELAY_JITTER_MS = Number(process.env.RELAY_JITTER_MS ?? 1000);

export function relayWait() {
  return sleep(RELAY_DELAY_MS + Math.random() * RELAY_JITTER_MS);
}

/// D = T_release - T_lock, measured from lock confirmation to release confirmation.
export function relayDelay(steps: Step[], lockName: string, releaseName: string) {
  const lock = steps.find((s) => s.name === lockName);
  const release = steps.find((s) => s.name === releaseName);
  if (!lock?.confirmedAt || !release?.confirmedAt) return undefined;
  return release.confirmedAt - lock.confirmedAt;
}
