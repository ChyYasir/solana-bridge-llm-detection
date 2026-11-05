"""
Scaled detection study: run the source / trace / ablation tracks for an attack across
one or more models, N runs each, with checkpointing so a throttle or crash resumes
instead of starting over.

  # one model (standalone)
  python run_study.py --attack v1-mint-confusion --models deepseek --runs 100

  # all four models
  python run_study.py --attack v1-mint-confusion --models all --runs 100

  # pick tracks (ablation only applies to timing-gated attacks)
  python run_study.py --attack v1-mint-confusion --models all --runs 100 --tracks source,trace,ablation

  # timing shown only; the timing-hidden side is the trace track itself
  python run_study.py --attack v2-sysvar-spoof --models gpt --runs 100 --tracks timing

Results land in results/<attack>-<track>-<model_slug>.json, one row per run. Re-running the
same command tops each file up to --runs rather than redoing finished runs. Grade with
grade.py afterwards.
"""

import argparse
import json
from pathlib import Path

from lib.client import ask, TEMPERATURE
from lib.gather import read_program_source, read_trace, load_baseline
from source_task import SYSTEM_PROMPT as SRC_SYS, USER_PROMPT_TEMPLATE as SRC_USER
from trace_task import SYSTEM_PROMPT as TRC_SYS, USER_PROMPT_TEMPLATE as TRC_USER

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "detection" / "results"
WRITE_EVERY = 5  # checkpoint to disk this often

MODELS = {
    "gpt": "openai/gpt-oss-120b-Turbo",
    "deepseek": "deepseek-ai/DeepSeek-V3.2",
    "qwen": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "llama": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "glm": "zai-org/GLM-5.3",
    "kimi": "moonshotai/Kimi-K3",
    "nemotron": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
    "gemma": "google/gemma-4-31B-it",
}


def slug(model_id):
    return model_id.split("/")[-1].lower()


def source_cases(attack):
    dirs = [
        ("baseline", ROOT / "programs" / "bridge-secure", False),
        (attack, ROOT / "programs" / "variants" / attack, True),
    ]
    cases = []
    for label, d, has_bug in dirs:
        prompt = SRC_USER.format(source=read_program_source(d))
        cases.append({"label": label, "condition": "", "has_bug": has_bug, "prompt": prompt})
    return SRC_SYS, cases


def trace_cases(attack, baseline=None, include_timing=None):
    traces_dir = ROOT / "traces" / attack
    candidates = [
        ("benign", "benign.json", False),
        ("vulnerable", "vulnerable.json", True),
        ("blocked-attempt", "baseline.json", False),
    ]
    cases = []
    for label, fname, has_bug in candidates:
        path = traces_dir / fname
        if not path.exists():
            continue
        if include_timing is None:
            trace = read_trace(path)
            cond = ""
        else:
            trace = read_trace(path, include_timing=include_timing, baseline=baseline)
            cond = "with-timing" if include_timing else "without-timing"
        prompt = TRC_USER.format(trace=json.dumps(trace, indent=2))
        cases.append({"label": label, "condition": cond, "has_bug": has_bug, "prompt": prompt})
    return TRC_SYS, cases


def build_track(attack, track):
    if track == "source":
        return source_cases(attack)
    if track == "trace":
        return trace_cases(attack)
    if track == "ablation":
        baseline = load_baseline(ROOT)
        sys_prompt, cases = TRC_SYS, []
        for include_timing in (True, False):
            _, part = trace_cases(attack, baseline=baseline, include_timing=include_timing)
            cases.extend(part)
        return sys_prompt, cases
    if track == "timing":
        # the normal-delay baseline only means something next to a trace's own relay delay
        has_delay = "relayDelayMs" in (ROOT / "traces" / attack / "vulnerable.json").read_text()
        return trace_cases(attack, baseline=load_baseline(ROOT) if has_delay else None, include_timing=True)
    raise ValueError(track)


def completed_counts(rows):
    counts = {}
    for r in rows:
        key = (r["label"], r.get("condition", ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def run_track(attack, track, model_id, runs):
    sys_prompt, cases = build_track(attack, track)
    out = RESULTS / f"{attack}-{track}-{slug(model_id)}.json"
    rows = json.loads(out.read_text()) if out.exists() else []
    done = completed_counts(rows)
    out.parent.mkdir(parents=True, exist_ok=True)

    for case in cases:
        key = (case["label"], case["condition"])
        have = done.get(key, 0)
        tag = case["label"] + (f"/{case['condition']}" if case["condition"] else "")
        if have >= runs:
            print(f"  [{slug(model_id)}] {track} {tag}: {have}/{runs} (done)")
            continue
        print(f"  [{slug(model_id)}] {track} {tag}: {have}/{runs}, running...")
        for run_idx in range(have + 1, runs + 1):
            answer = ask(sys_prompt, case["prompt"], model=model_id)
            rows.append({
                "label": case["label"],
                "condition": case["condition"],
                "ground_truth_has_bug": case["has_bug"],
                "run": run_idx,
                "model": model_id,
                "temperature": TEMPERATURE,
                "answer": answer,
            })
            if run_idx % WRITE_EVERY == 0 or run_idx == runs:
                out.write_text(json.dumps(rows, indent=2))
        out.write_text(json.dumps(rows, indent=2))
    print(f"  saved: {out.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attack", required=True)
    ap.add_argument("--models", default="all", help="comma list of " + ",".join(MODELS) + " or 'all'")
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--tracks", default="source,trace")
    args = ap.parse_args()

    names = list(MODELS) if args.models == "all" else args.models.split(",")
    tracks = args.tracks.split(",")
    for name in names:
        if name not in MODELS:
            raise SystemExit(f"unknown model '{name}'; choose from {list(MODELS)} or 'all'")
        print(f"\n=== model: {name} ({MODELS[name]}) ===")
        for track in tracks:
            run_track(args.attack, track, MODELS[name], args.runs)


if __name__ == "__main__":
    main()
