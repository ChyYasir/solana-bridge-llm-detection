import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const CLIENT_DIR = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const TRACES_ROOT = join(CLIENT_DIR, "..", "traces");

export function saveTrace(attack: string, label: string, data: unknown) {
  const dir = join(TRACES_ROOT, attack);
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${label}.json`);
  writeFileSync(path, JSON.stringify(data, null, 2));
  console.log(`trace saved: ${path}`);
}
