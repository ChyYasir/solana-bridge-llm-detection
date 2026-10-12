"""
Trace detection track for Attack 1 (Mint Confusion).

Gives the model only the captured on-chain evidence (instructions, logs, balances) —
no source code — and asks whether it shows an attack. The exploit script's own
"outcome" verdict is stripped before the model ever sees the trace, so this is a real
test, not an open-book one.
"""

import json
import random
from pathlib import Path

from lib.client import ask, MODEL, TEMPERATURE, results_path
from lib.gather import read_trace

ROOT = Path(__file__).resolve().parent.parent
RUNS_PER_ITEM = 3

SYSTEM_PROMPT = (
    "You are monitoring a Solana token bridge for suspicious activity. You are given "
    "the accounts, instructions, logs, and balances from one user's session. You are "
    "not told in advance whether anything is wrong."
)

USER_PROMPT_TEMPLATE = """Here is a captured transaction trace from the bridge:

{trace}

Answer these three questions plainly:
1. Does this trace show an attack? (yes/no)
2. If yes, what is suspicious about it, specifically?
3. If yes, name the likely vulnerability class being exploited.
"""


def build_items():
    traces_dir = ROOT / "traces" / "v1-mint-confusion"
    items = [
        # True negative control: an ordinary user, no attacker involved at all.
        {"label": "benign", "path": traces_dir / "benign.json", "has_bug": False},
        # The actual exploit succeeding against the vulnerable variant.
        {"label": "vulnerable", "path": traces_dir / "vulnerable.json", "has_bug": True},
        # Secondary data point: an attacker attempts the same strike, but it's
        # blocked by the secure baseline's check. Not a clean negative (an attack
        # really was attempted here) — kept separate from "benign" on purpose.
        {"label": "blocked-attempt", "path": traces_dir / "baseline.json", "has_bug": False},
    ]
    random.shuffle(items)
    return items


def main():
    items = build_items()
    results = []

    for item in items:
        trace = read_trace(item["path"])
        prompt = USER_PROMPT_TEMPLATE.format(trace=json.dumps(trace, indent=2))

        print(f"testing item (ground truth hidden from model): {item['label']}")
        for run_idx in range(RUNS_PER_ITEM):
            answer = ask(SYSTEM_PROMPT, prompt)
            print(f"  run {run_idx + 1}/{RUNS_PER_ITEM} done")
            results.append(
                {
                    "label": item["label"],
                    "ground_truth_has_bug": item["has_bug"],
                    "run": run_idx + 1,
                    "model": MODEL,
                    "temperature": TEMPERATURE,
                    "answer": answer,
                }
            )

    out_path = results_path(ROOT, "v1-mint-confusion", "trace")
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
