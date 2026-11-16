# Detection, all four attacks pooled (adjudicated)

400 vulnerable and 400 secure or benign runs per row; blocked attempts (400) are counted separately. Per-attack rows: `metrics-source.md`, `metrics-trace.md`.

| Track | Model | Flagged recall | Flagged F1 | Flagged accuracy | Diagnosed recall | Diagnosed F1 | Diagnosed accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|
| Source code | gpt-oss-120b | 0.79 | 0.65 | 0.58 | 0.55 | 0.50 | 0.46 | -- |
| Source code | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.25 | 0.22 | 0.12 | -- |
| Source code | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 | -- |
| Source code | Nemotron-3-Super | 0.98 | 0.66 | 0.51 | 0.24 | 0.22 | 0.14 | -- |
| Source code | Gemma-4-31B | 1.00 | 0.67 | 0.50 | 0.16 | 0.15 | 0.08 | -- |
| Source code | DeepSeek-V3.2 (thinking) | 0.97 | 0.67 | 0.52 | 0.24 | 0.23 | 0.16 | -- |
| Transaction record | gpt-oss-120b | 0.99 | 0.75 | 0.67 | 0.25 | 0.26 | 0.30 | 115 |
| Transaction record | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.26 | 0.23 | 0.13 | 344 |
| Transaction record | Llama-3.3-70B | 0.25 | 0.36 | 0.55 | 0.00 | 0.00 | 0.42 | 400 |
| Transaction record | Nemotron-3-Super | 0.56 | 0.62 | 0.65 | 0.25 | 0.33 | 0.49 | 385 |
| Transaction record | Gemma-4-31B | 0.87 | 0.62 | 0.47 | 0.28 | 0.25 | 0.17 | 191 |
| Transaction record | DeepSeek-V3.2 (thinking) | 0.94 | 0.73 | 0.66 | 0.48 | 0.45 | 0.42 | 352 |
