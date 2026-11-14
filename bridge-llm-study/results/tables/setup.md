# Runs and grading

Six model configurations, all through DeepInfra at temperature 0 with at most 16,000 output tokens. Answers = 6 models x 4 attacks x inputs per attack x runs. Graded = answers on vulnerable input (the attack session for transactions), each labelled blind by Claude Opus 5.5 and Gemini 3.8 Flash; the author decided every disagreement. Claude, Gemini and Final count the answers labelled as naming the planted bug.

| Experiment | Input | Runs per model and input | Answers | Graded | Claude: correct | Gemini: correct | Graders agree | Decided by author | Final: correct |
|---|---|---|---|---|---|---|---|---|---|
| Source code, no comments | secure and vulnerable program | 100 | 4,800 | 2,400 | 574 | 575 | 2,399 (99.96%) | 1 | 574 |
| Source code, original comments | same, with the code's comments | 100 | 4,800 | 2,400 | 1,433 | 1,420 | 2,385 (99.38%) | 15 | 1,433 |
| Transaction record | attack, normal and blocked-attempt session | 100 | 7,200 | 2,400 | 579 | 636 | 2,335 (97.29%) | 65 | 608 |
| Total | | | 16,800 | 7,200 | | | 7,119 (98.88%) | 81 | |
