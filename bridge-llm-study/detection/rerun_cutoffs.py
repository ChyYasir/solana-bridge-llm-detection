"""
Re-ask runs whose answer was cut off at MAX_TOKENS (the client then saves raw reasoning
instead of a final answer). Same prompt, model and settings as the original run; the row is
replaced in place and gets a `reruns` count. Originals are copied to results/archive/cutoffs/
before anything changes.

  python rerun_cutoffs.py --attack v1-mint-confusion --track source --model nemotron
"""

import argparse
import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor

from lib.client import ask
from run_study import MODELS, RESULTS, build_track, slug

CUTOFF_CHARS = 20000  # no completed answer from any model has exceeded ~19K chars
MAX_RERUNS = 10


def is_cutoff(answer):
    return len(answer) > CUTOFF_CHARS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attack", required=True)
    ap.add_argument("--track", default="source")
    ap.add_argument("--model", required=True, choices=list(MODELS))
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    model_id = MODELS[args.model]
    out = RESULTS / f"{args.attack}-{args.track}-{slug(model_id)}.json"
    rows = json.loads(out.read_text())
    todo = [r for r in rows if is_cutoff(r["answer"])]
    print(f"{out.name}: {len(todo)} cut-off runs")
    if not todo:
        return

    archive = RESULTS / "archive" / "cutoffs"
    archive.mkdir(parents=True, exist_ok=True)
    if not (archive / out.name).exists():
        shutil.copy(out, archive / out.name)

    sys_prompt, cases = build_track(args.attack, args.track)
    prompts = {(c["label"], c["condition"]): c["prompt"] for c in cases}
    lock = threading.Lock()

    def redo(row):
        prompt = prompts[(row["label"], row.get("condition", ""))]
        for n in range(1, MAX_RERUNS + 1):
            try:
                answer = ask(sys_prompt, prompt, model=model_id)
            except Exception as e:
                print(f"  {row['label']} run {row['run']}: {type(e).__name__}, trying again")
                continue
            if not is_cutoff(answer):
                with lock:
                    row["answer"] = answer
                    row["reruns"] = n
                    out.write_text(json.dumps(rows, indent=2))
                print(f"  {row['label']} run {row['run']}: answered on rerun {n}")
                return
            print(f"  {row['label']} run {row['run']}: cut off again (rerun {n})")
        print(f"  {row['label']} run {row['run']}: still cut off after {MAX_RERUNS} reruns")

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(redo, todo))

    left = sum(is_cutoff(r["answer"]) for r in rows)
    print(f"saved: {out.name} ({left} still cut off)")


if __name__ == "__main__":
    main()
