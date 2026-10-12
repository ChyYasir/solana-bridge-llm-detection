import "dotenv/config";
import { PublicKey } from "@solana/web3.js";

// Override with env vars after a fresh `solana program deploy` if the ids differ
// from a previous local-validator session.
export const BRIDGE_PROGRAM_ID = new PublicKey(
  process.env.BRIDGE_PROGRAM_ID ?? "ZJiL1rw3eXwNWFW5iMnTGy9Wu87Ab64pQigEzNnjDUW",
);
export const ORACLE_PROGRAM_ID = new PublicKey(
  process.env.ORACLE_PROGRAM_ID ?? "2RDdcMcpTV6h1C8rGABbsGuBScUU3XJoHxagoTgnrx7N",
);
