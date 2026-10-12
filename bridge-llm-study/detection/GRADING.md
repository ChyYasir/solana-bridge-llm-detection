# Grading rubric

Every model answer is free text. Each answer is reduced to two yes/no labels by a
deterministic, rule-based grader (`grade.py`, rules in `rubric.py`). No LLM is used to grade.
Raw answers stay in `results/`; grading is a separate, re-runnable layer on top, so anyone
can inspect or re-score with a different rule.

## The two labels

- **flagged** — did the model answer "yes" to the first question (is this vulnerable / is this
  an attack)? Taken from the first `yes`/`no` token in the answer.
- **localized** — did the model name the *actual planted bug*? Only meaningful where a bug
  exists (the buggy source, the successful-attack trace). On secure code and benign traces
  there is nothing to localize, so this label is left blank (`N/A`) and only `flagged`
  matters there (it is the false-alarm signal).

## How the two labels become the reported metrics

- **True-positive rate (TPR)** = fraction of runs on the *buggy* case where `localized = yes`.
  The headline capability number: how often it actually found the planted bug.
- **False-positive rate (FPR)** = fraction of runs on the *secure / benign* case where
  `flagged = yes`. How often it cried bug on clean input.
- The *blocked-attempt* trace is reported separately (it is neither a clean negative nor a
  successful attack).

## Localization rules (keyword, case-insensitive)

A run is `localized = yes` only if the answer matches every required group for that
attack+track (within a group, any one synonym counts).

### Attack 1 — mint confusion (`v1-mint-confusion`)
- **source:** must mention `lock` **and** the collateral/approved-mint check it dropped
  (`approved`, `collateral`, `deposited token`, `wrong/any/fake/arbitrary mint`,
  `mint confusion`).
- **records:** must describe wrapped tokens being minted **and** that there is no real
  collateral behind them (`no/without collateral`, `real vault … 0`, `fake vault`,
  `fake/worthless mint`, `unbacked`, `nothing`).

### Attack 5 — missing signer check (`v5-missing-signer`)
- **source:** must mention the missing **signer/signature** check **and** the admin/authority
  path it protects (`admin`, `authority`, `set_admin`, `privileged`).
- **records:** must identify an **admin/authority** change **and** that it is an
  unauthorized takeover (`takeover`, `privilege`, `escalation`, `changed`, `transfer`,
  `unauthorized`, `attacker`).

## Validation

`validate.py` samples answers for a human to label by hand, then measures how often the
grader agrees with the human. Report this agreement number alongside the results; it is the
evidence that the keyword rules are faithful. Rules here are approximate by design — the
hand-validation is what certifies them.
