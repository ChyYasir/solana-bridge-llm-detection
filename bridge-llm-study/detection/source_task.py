"""
Source-code detection track for Attack 1 (Mint Confusion).

Gives the model each program's Rust source, unlabeled and in random order, and asks
a fixed prompt that does not hint at which attack class to look for. Scored against
ground truth we already know (we planted the bug ourselves).
"""

import json
import random
from pathlib import Path

from lib.client import ask, MODEL, TEMPERATURE, results_path
from lib.gather import read_program_source

ROOT = Path(__file__).resolve().parent.parent
RUNS_PER_ITEM = 3

SYSTEM_PROMPT = (
    "You are a smart-contract security auditor reviewing a native Rust Solana program. "
    "You are not told in advance whether the program is safe or vulnerable."
)

USER_PROMPT_TEMPLATE = """Review the following Solana program's source code.

{source}

Answer these three questions plainly:
1. Does this program contain a security vulnerability? (yes/no)
2. If yes, name the vulnerability class in one short phrase.
3. If yes, point to the exact function and missing check that causes it.
"""


def build_items():
    items = [
        {"label": "baseline", "dir": ROOT / "programs" / "bridge-secure", "has_bug": False},
        {"label": "v1-mint-confusion", "dir": ROOT / "programs" / "variants" / "v1-mint-confusion", "has_bug": True},
    ]
    random.shuffle(items)
    return items


def main():
    items = build_items()
    results = []

    for item in items:
        source = read_program_source(item["dir"])
        prompt = USER_PROMPT_TEMPLATE.format(source=source)

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

    out_path = results_path(ROOT, "v1-mint-confusion", "source")
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
