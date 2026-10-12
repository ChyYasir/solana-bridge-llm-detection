"""
Trace detection track. Attack selected via ATTACK env var or argv[1]

Gives the model only the captured on-chain evidence (instructions, logs, balances) —
no source code — and asks whether it shows an attack. The exploit script's own
"outcome" verdict is stripped before the model ever sees the trace, so this is a real
test, not an open-book one.
"""

import json
import os
import random
import sys
from pathlib import Path

from lib.client import ask, MODEL, TEMPERATURE, results_path
from lib.gather import read_trace

ROOT = Path(__file__).resolve().parent.parent
RUNS_PER_ITEM = 3
ATTACK = os.environ.get("ATTACK", sys.argv[1] if len(sys.argv) > 1 else "v1-mint-confusion")

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
    traces_dir = ROOT / "traces" / ATTACK
    # Each trace file maps to one condition, with ground truth:
    #   benign    — ordinary user, no attacker at all (true negative), has_bug=False
    #   vulnerable— the exploit succeeding against the variant,        has_bug=True
    #   baseline  — the same strike attempted but blocked by the secure
    #               bridge; labeled "blocked-attempt", NOT a clean negative, has_bug=False
    candidates = [
        ("benign", "benign.json", False),
        ("vulnerable", "vulnerable.json", True),
        ("blocked-attempt", "baseline.json", False),
    ]
    items = [
        {"label": label, "path": traces_dir / fname, "has_bug": has_bug}
        for label, fname, has_bug in candidates
        if (traces_dir / fname).exists()
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

    out_path = results_path(ROOT, ATTACK, "trace")
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
