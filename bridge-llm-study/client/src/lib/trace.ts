import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const CLIENT_DIR = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const TRACES_ROOT = join(CLIENT_DIR, "..", "traces");

// A trace stands in for what a chain monitor would see, so it must not carry our own editorial
// labels. Reduce each step name to the plain instruction it ran (identical whether the session
// is honest or an attack) and drop the authored "outcome" summary. The on-chain facts — program
// ids, logs, amounts, errors — are what remain.
function neutralOp(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("release")) return "release";
  if (n.includes("redeem")) return "redeem";
  if (n.includes("set_admin")) return "set_admin";
  if (n.includes("withdraw")) return "withdraw_fees";
  if (n.includes("lock")) return "lock";
  if (n.includes("initialize")) return "initialize";
  if (n.includes("oracle")) return "set_price";
  return "instruction";
}

function sanitize(data: any): any {
  const clone = JSON.parse(JSON.stringify(data));
  if (Array.isArray(clone?.steps)) {
    for (const step of clone.steps) {
      if (typeof step?.name === "string") step.name = neutralOp(step.name);
    }
  }
  delete clone.outcome;
  return clone;
}

export function saveTrace(attack: string, label: string, data: unknown) {
  const dir = join(TRACES_ROOT, attack);
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${label}.json`);
  writeFileSync(path, JSON.stringify(sanitize(data), null, 2));
  console.log(`trace saved: ${path}`);
}
