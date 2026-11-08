"""
Blinded localization judging with the prompt in judge_prompt.md.

  python judge.py build                   # judging/<attack>-<track>/{prompt.txt,answers.jsonl}
  python judge.py build timing            # only the timing-shown trace cells
  python judge.py merge claude-opus-5-5   # judging/*/labels-<judge>.jsonl -> results/graded/<judge>/
  PROVIDER=gemini MODEL=gemini-3.8-flash python judge.py grade [per-cell limit]
  JUDGING=judging-gemma python judge.py ...   # same steps for the Gemma answers
  JUDGING=judging-deepseek-thinking python judge.py ...   # and for DeepSeek with thinking on
  JUDGING=judging-fake-comments python judge.py build source   # results/fake-comments/ answers

`build` pools the vulnerable-case answers of every model for one attack and track, shuffles
them under opaque ids and strips the model name; the id -> (file, run) map goes to
judging/keys/ so the judge never sees it. Each judge writes labels-<judge>.jsonl next to
answers.jsonl, one {"id", "reason", "label"} per line; `grade` does this through the API for the
model in MODEL, resuming past ids already labelled and logging unparseable replies to
errors-<judge>.jsonl instead. `merge` copies one judge's labels into
that judge's own graded folder as `localized` with its reason, so judges never overwrite each
other.
"""

import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

from rubric import flagged_yes
from run_study import RESULTS

HERE = Path(__file__).resolve().parent
WORKERS = 8

ATTACKS = ["v1-mint-confusion", "v2-sysvar-spoof", "v5-missing-signer", "v6-arbitrary-cpi"]
MODELS = [
    "gpt-oss-120b-turbo",
    "deepseek-v3.2",
    "llama-3.3-70b-instruct-turbo",
    "nvidia-nemotron-3-super-120b-a12b",
    "gemma-4-31b-it",
    "deepseek-v3.2-thinking",
]
# Gemma and DeepSeek with thinking on were added after judging/ was graded, so each is pooled on
# its own in judging-gemma/ and judging-deepseek-thinking/. The fake-comments pilot
# (make_fake_comments.py) pools all six models' answers per attack in judging-fake-comments/.
JUDGING = HERE / os.environ.get("JUDGING", "judging")
POOLED = {"judging": MODELS[:4], "judging-gemma": MODELS[4:5], "judging-deepseek-thinking": MODELS[5:],
          "judging-fake-comments": MODELS}[JUDGING.name]
FAKE = JUDGING.name == "judging-fake-comments"
ANSWERS = RESULTS / "fake-comments" if FAKE else RESULTS
TRACKS = {
    "source": ("Source Code", "the program's source code", "a security vulnerability"),
    "trace": (
        "Transaction Information",
        "an on-chain transaction trace (program logs and a few balance or account fields)",
        "an attack",
    ),
}
# timing-shown traces are graded against the same Transaction Information rubric
RUBRIC_TRACK = {"source": "source", "trace": "trace", "timing": "trace"}


def load_prompt():
    text = (HERE / "judge_prompt.md").read_text()
    template = re.search(r"## Template\n\n```\n(.*?)```", text, re.S).group(1)
    keys = {}
    for i, section in enumerate(re.split(r"\n### Attack \d+: .*\n", text)[1:]):
        for track, (heading, _, _) in TRACKS.items():
            body = re.search(rf"- \*\*{heading}\.\*\* (.*?)(?=\n- \*\*|\Z)", section, re.S).group(1)
            ref, _, distractors = body.partition("*Distractors:*")
            keys[(ATTACKS[i], track)] = (
                " ".join(ref.split()),
                " ".join(distractors.split()) or "(none listed)",
            )
    return template, keys


def vulnerable_label(attack, track):
    return attack if track == "source" else "vulnerable"


def build(tracks=("source", "trace")):
    template, keys = load_prompt()
    rng = random.Random(20261027)
    (JUDGING / "keys").mkdir(parents=True, exist_ok=True)
    for attack in ATTACKS:
        for track in tracks:
            _, input_kind, target = TRACKS[RUBRIC_TRACK[track]]
            pool = []
            if FAKE:
                names = sorted(p.name for p in ANSWERS.glob(f"{attack}-*.json"))
            else:
                names = [f"{attack}-{track}-{model}.json" for model in POOLED]
            for name in names:
                for row in json.loads((ANSWERS / name).read_text()):
                    if FAKE or row["label"] == vulnerable_label(attack, track):
                        pool.append((name, row["run"], row["answer"]))
            rng.shuffle(pool)

            cell = JUDGING / f"{attack}-{track}"
            cell.mkdir(parents=True, exist_ok=True)
            reference, distractors = keys[(attack, RUBRIC_TRACK[track])]
            prompt = (template.replace("{INPUT_KIND}", input_kind).replace("{TARGET}", target)
                      .replace("{REFERENCE}", reference).replace("{DISTRACTORS}", distractors))
            (cell / "prompt.txt").write_text(prompt)
            with open(cell / "answers.jsonl", "w") as f:
                for i, (_, _, answer) in enumerate(pool):
                    f.write(json.dumps({"id": f"{cell.name}-{i:03d}", "answer": answer}) + "\n")
            key = {f"{cell.name}-{i:03d}": [name, run] for i, (name, run, _) in enumerate(pool)}
            (JUDGING / "keys" / f"{cell.name}.json").write_text(json.dumps(key, indent=1))
            print(f"{cell.name}: {len(pool)} answers")


def graded_rows(graded, name):
    path = graded / name
    if path.exists():
        return json.loads(path.read_text())
    rows = json.loads((ANSWERS / name).read_text())
    for row in rows:
        row["flagged"] = flagged_yes(row["answer"])
        row["localized"] = None
    return rows


def merge(judge):
    graded = ANSWERS / "graded" / judge
    graded.mkdir(parents=True, exist_ok=True)
    files = {}
    for labels in sorted(JUDGING.glob(f"*/labels-{judge}.jsonl")):
        key = json.loads((JUDGING / "keys" / f"{labels.parent.name}.json").read_text())
        for line in labels.read_text().splitlines():
            if not line.strip():
                continue
            judged = json.loads(line)
            name, run = key[judged["id"]]
            rows = files.setdefault(name, graded_rows(graded, name))
            row = next(r for r in rows if r["run"] == run and r["ground_truth_has_bug"])
            row["localized"] = judged["label"] == "correct"
            row["judge"] = judge
            row["judge_reason"] = judged["reason"]
    for name, rows in files.items():
        (graded / name).write_text(json.dumps(rows, indent=2))
        print(f"merged {judge}/{name}")


def parse_label(reply):
    try:
        judged = json.loads(reply[reply.index("{"):reply.rindex("}") + 1])
    except ValueError:
        return None
    if judged.get("label") not in ("correct", "incorrect") or not judged.get("reason"):
        return None
    return judged


def grade(limit=None):
    from openai import BadRequestError
    from lib.client import ask, MODEL_SLUG

    jobs = []
    for cell in sorted(p.parent for p in JUDGING.glob("*/prompt.txt")):
        labels = cell / f"labels-{MODEL_SLUG}.jsonl"
        done = {json.loads(l)["id"] for l in labels.read_text().splitlines() if l.strip()} if labels.exists() else set()
        template = (cell / "prompt.txt").read_text()
        answers = [json.loads(l) for l in (cell / "answers.jsonl").read_text().splitlines()][:limit]
        jobs += [(cell, template, a) for a in answers if a["id"] not in done]
    print(f"{len(jobs)} answers to grade with {MODEL_SLUG}")

    lock = Lock()

    def run(job):
        cell, template, answer = job
        try:
            reply = ask("", template.replace("{ANSWER}", answer["answer"]))
        except BadRequestError as e:
            reply = f"{type(e).__name__}: {e}"
        judged = parse_label(reply)
        name = f"labels-{MODEL_SLUG}.jsonl" if judged else f"errors-{MODEL_SLUG}.jsonl"
        line = {"id": answer["id"], "reason": judged["reason"], "label": judged["label"]} if judged \
            else {"id": answer["id"], "reply": reply}
        with lock, open(cell / name, "a") as f:
            f.write(json.dumps(line) + "\n")
        return judged is not None

    with ThreadPoolExecutor(WORKERS) as pool:
        ok = 0
        for i, parsed in enumerate(pool.map(run, jobs), 1):
            ok += parsed
            if i % 50 == 0 or i == len(jobs):
                print(f"{i}/{len(jobs)} graded, {i - ok} unparseable", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2:] or ("source", "trace"))
    elif sys.argv[1] == "grade":
        grade(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    else:
        merge(sys.argv[2])
