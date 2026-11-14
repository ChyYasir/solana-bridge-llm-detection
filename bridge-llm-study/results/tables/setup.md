# Setup

## Models

All through DeepInfra, temperature 0, at most 16,000 output tokens. DeepSeek-V3.2 is run twice, with thinking off and on.

| Model | DeepInfra model | Mode |
|---|---|---|
| gpt-oss-120b | `openai/gpt-oss-120b-Turbo` | reasoning (provider default effort) |
| DeepSeek-V3.2 | `deepseek-ai/DeepSeek-V3.2` | thinking off |
| Llama-3.3-70B | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | no reasoning |
| Nemotron-3-Super | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B` | reasoning |
| Gemma-4-31B | `google/gemma-4-31B-it` | thinking on |
| DeepSeek-V3.2 (thinking) | `deepseek-ai/DeepSeek-V3.2` | thinking on |

## Runs and grading

Answers = 6 models x 4 attacks x inputs per attack x runs. Graded = answers on vulnerable input (the attack session for transactions), each labelled blind by Claude Opus 5.5 and Gemini 3.8 Flash; the author decided every disagreement. Claude, Gemini and Final count the answers labelled as naming the planted bug.

| Experiment | Input | Runs per model and input | Answers | Graded | Claude: correct | Gemini: correct | Graders agree | Decided by author | Final: correct |
|---|---|---|---|---|---|---|---|---|---|
| Source code, no comments | secure and vulnerable program | 100 | 4,800 | 2,400 | 574 | 575 | 2,399 (99.96%) | 1 | 574 |
| Source code, original comments | same, with the code's comments | 100 | 4,800 | 2,400 | 1,433 | 1,420 | 2,385 (99.38%) | 15 | 1,433 |
| Transaction record | attack, normal and blocked-attempt session | 100 | 7,200 | 2,400 | 579 | 636 | 2,335 (97.29%) | 65 | 608 |
| Total | | | 16,800 | 7,200 | | | 7,119 (98.88%) | 81 | |
