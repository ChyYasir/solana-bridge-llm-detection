# Grader counts

Answers each grader labelled as naming the planted bug, out of the graded answers (vulnerable input only). Same label: answers both graders labelled the same way. Final: after the author decided the disagreements.

| Experiment | Graded | Claude | Gemini | Same label | Final |
|---|---|---|---|---|---|
| Source code, no comments | 2,400 | 574 | 575 | 2,399 | 574 |
| Source code, original comments | 2,400 | 1,433 | 1,420 | 2,385 | 1,433 |
| Transaction record | 2,400 | 579 | 636 | 2,335 | 608 |
| Total | 7,200 | | | 7,119 (98.9%) | 81 decided |

## Per model

Out of 400 graded answers per model and experiment (100 per attack).

| Experiment | Model | Claude | Gemini | Final |
|---|---|---|---|---|
| Source code, no comments | gpt-oss-120b | 218 | 218 | 218 |
|  | DeepSeek-V3.2 | 99 | 99 | 99 |
|  | Llama-3.3-70B | 1 | 1 | 1 |
|  | Nemotron-3-Super | 95 | 96 | 95 |
|  | Gemma-4-31B | 63 | 63 | 63 |
|  | DeepSeek-V3.2 (thinking) | 98 | 98 | 98 |
| Source code, original comments | gpt-oss-120b | 306 | 306 | 306 |
|  | DeepSeek-V3.2 | 202 | 202 | 202 |
|  | Llama-3.3-70B | 188 | 175 | 188 |
|  | Nemotron-3-Super | 214 | 214 | 214 |
|  | Gemma-4-31B | 269 | 269 | 269 |
|  | DeepSeek-V3.2 (thinking) | 254 | 254 | 254 |
| Transaction record | gpt-oss-120b | 100 | 100 | 100 |
|  | DeepSeek-V3.2 | 104 | 106 | 104 |
|  | Llama-3.3-70B | 0 | 0 | 0 |
|  | Nemotron-3-Super | 100 | 97 | 100 |
|  | Gemma-4-31B | 107 | 113 | 113 |
|  | DeepSeek-V3.2 (thinking) | 168 | 220 | 191 |
