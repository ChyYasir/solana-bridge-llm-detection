"""
Blinded localization judging with the prompt in judge_prompt.md.

  python judge.py build                   # judging/<attack>-<track>/{prompt.txt,answers.jsonl}
  python judge.py merge claude-opus-5-5   # judging/*/labels-<judge>.jsonl -> results/graded/<judge>/

`build` pools the vulnerable-case answers of every model for one attack and track, shuffles
them under opaque ids and strips the model name; the id -> (file, run) map goes to
judging/keys/ so the judge never sees it. Each judge writes labels-<judge>.jsonl next to
answers.jsonl, one {"id", "reason", "label"} per line. `merge` copies one judge's labels into
that judge's own graded folder as `localized` with its reason, so judges never overwrite each
other.
"""

import json
import random
import re
import sys
from pathlib import Path

from rubric import flagged_yes
from run_study import RESULTS

HERE = Path(__file__).resolve().parent
JUDGING = HERE / "judging"

ATTACKS = ["v1-mint-confusion", "v2-sysvar-spoof", "v5-missing-signer", "v6-arbitrary-cpi"]
MODELS = [
    "gpt-oss-120b-turbo",
    "deepseek-v3.2",
    "llama-3.3-70b-instruct-turbo",
    "nvidia-nemotron-3-super-120b-a12b",
]
TRACKS = {
    "source": ("Source Code", "the program's source code", "a security vulnerability"),
    "trace": (
        "Transaction Information",
        "an on-chain transaction trace (program logs and a few balance or account fields)",
        "an attack",
    ),
}


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


def build():
    template, keys = load_prompt()
    rng = random.Random(20261027)
    (JUDGING / "keys").mkdir(parents=True, exist_ok=True)
    for attack in ATTACKS:
        for track, (_, input_kind, target) in TRACKS.items():
            pool = []
            for model in MODELS:
                name = f"{attack}-{track}-{model}.json"
                for row in json.loads((RESULTS / name).read_text()):
                    if row["label"] == vulnerable_label(attack, track):
                        pool.append((name, row["run"], row["answer"]))
            rng.shuffle(pool)

            cell = JUDGING / f"{attack}-{track}"
            cell.mkdir(parents=True, exist_ok=True)
            reference, distractors = keys[(attack, track)]
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
    rows = json.loads((RESULTS / name).read_text())
    for row in rows:
        row["flagged"] = flagged_yes(row["answer"])
        row["localized"] = None
    return rows


def merge(judge):
    graded = RESULTS / "graded" / judge
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


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    else:
        merge(sys.argv[2])
