# Grading

Every model answer is free text. Each answer is reduced to two yes/no labels. Raw answers stay
in `results/`; grading is a separate, re-runnable layer on top, written to
`results/graded/<grader>/`.

## The two labels

- **flagged** — did the model answer "yes" to the first question (is this vulnerable / is this
  an attack)? Taken from the first `yes`/`no` token in the answer (`flagged_yes` in
  `rubric.py`). No grader is involved.
- **localized** — did the model name the *actual planted bug*? Only scored where a bug exists:
  the vulnerable source and the successful-attack trace. On secure code, benign traces and the
  blocked attempt there is nothing to localize, so it is left blank and only `flagged` matters.
  This label is decided by an LLM grader, as below.

## How `localized` is graded

The rubric is `judge_prompt.md`: one template plus, per attack and track, a reference
description of the planted flaw and a list of common wrong diagnoses. Its rules, in short:
the answer's main diagnosis (the first-named or clearly singled-out issue) must name the
reference mechanism; saying something is wrong is not enough; on source code the flaw must be
placed in the right function.

1. **Blinding.** `python judge.py build` pools the vulnerable-case answers of all four models
   for each attack and track (400 per cell, 3,200 in total), shuffles them with a fixed seed,
   strips the model name and writes `judging/<attack>-<track>/{prompt.txt,answers.jsonl}`. The
   id-to-run map goes to `judging/keys/` and is not shown to the graders.
2. **Two independent graders.** Each grader sees only `prompt.txt` and the anonymous answers,
   and writes `judging/<cell>/labels-<grader>.jsonl` (one `{"id", "reason", "label"}` per
   answer).
   - **Claude Opus 5.5** (`claude-opus-5-5`) read and labelled every answer.
   - **Gemini 3.8 Flash** (`gemini-3.8-flash`), through the API at temperature 0, with the
     filled `prompt.txt` as the only message:
     `PROVIDER=gemini MODEL=gemini-3.8-flash python judge.py grade`. Replies that cannot be
     parsed, or requests the API rejects, go to `errors-<grader>.jsonl` and are retried on the
     next run.
3. **Merge.** `python judge.py merge <grader>` maps the labels back to their runs and writes
   `results/graded/<grader>/`, setting `localized`, `judge` and `judge_reason` on each
   vulnerable-case row. Each grader has its own folder, so graders never overwrite each other.

## Agreement

The two graders agree on 3,180 of 3,200 answers (99.4%, Cohen's kappa 0.987). Per cell, and
the effect on each reported count, is in the attack docs (`docs/attack-*.md`), which show one
results table per grader. Where almost every answer is "incorrect", a single disagreement pulls
kappa down sharply, so raw agreement is reported next to it. The 20 disagreements are listed in
`judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`.

**Adjudication.** I decided every disagreement under `judge_prompt.md`; each decision is in the
Decision column of the disagreement files. The final labels (agreed labels plus these decisions)
are in `judging/<cell>/labels-adjudicated.jsonl` and merged with `python judge.py merge
adjudicated` into `results/graded/adjudicated/`. On the main tracks every decision matched the
Claude label, so the adjudicated counts equal the Claude tables.

As a stability check, two cells (A1 Source, A6 Trace) were graded a second time by Claude from
scratch; 799 of 800 labels matched.

The timing ablation (`run_study.py --tracks timing`: the same traces with step times shown) is
graded the same way: `python judge.py build timing` builds four more cells, graded against the
Transaction Information rubric. On those 1,600 answers the graders agree on 1,534 (95.9%); all 66
disagreements are A1 answers that cite the empty approved vault but explain it as a missing
approval step, listed in `judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`.
Adjudication kept 10 of them as correct (those that also say the mint has no backing).

## How the labels become the reported metrics

- **Detected** = runs on the vulnerable case where `localized` is true, out of 100.
- **False alarm** = runs on the secure source or the benign trace where `flagged` is true.
- **Blocked attempt** = runs on the rejected-attack trace where `flagged` is true, reported
  separately (it is neither a clean negative nor a successful attack).

## Earlier keyword grader

The first results were graded by keyword rules (`grade.py`, `LOCALIZE` in `rubric.py`): an
answer counted as localized if it contained the listed terms. This proved too loose, crediting
answers that mentioned the right words without making the right diagnosis, and was replaced by
the graders above. Files graded that way are the ones directly in `results/graded/` (not in a
grader folder); none of them are used in the attack docs.
