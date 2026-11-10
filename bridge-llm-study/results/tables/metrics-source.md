# Source code: recall, F1, accuracy (adjudicated)

| Attack | Model | Flagged recall | Flagged F1 | Flagged accuracy | Diagnosed recall | Diagnosed F1 | Diagnosed accuracy |
|---|---|---|---|---|---|---|---|
| A1 mint confusion | gpt-oss-120b | 1.00 | 0.78 | 0.72 | 0.94 | 0.75 | 0.69 |
| A1 mint confusion | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 |
| A1 mint confusion | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 |
| A1 mint confusion | Nemotron-3-Super | 1.00 | 0.67 | 0.51 | 0.30 | 0.26 | 0.16 |
| A1 mint confusion | Gemma-4-31B | 1.00 | 0.67 | 0.51 | 0.05 | 0.05 | 0.03 |
| A1 mint confusion | DeepSeek-V3.2 (thinking) | 0.97 | 0.66 | 0.49 | 0.32 | 0.28 | 0.17 |
| A2 sysvar spoof | gpt-oss-120b | 0.91 | 0.71 | 0.62 | 0.51 | 0.47 | 0.42 |
| A2 sysvar spoof | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.73 | 0.53 | 0.36 |
| A2 sysvar spoof | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.01 | 0.01 | 0.01 |
| A2 sysvar spoof | Nemotron-3-Super | 1.00 | 0.68 | 0.53 | 0.49 | 0.40 | 0.27 |
| A2 sysvar spoof | Gemma-4-31B | 1.00 | 0.67 | 0.51 | 0.56 | 0.44 | 0.28 |
| A2 sysvar spoof | DeepSeek-V3.2 (thinking) | 0.97 | 0.68 | 0.54 | 0.45 | 0.38 | 0.28 |
| A5 missing signer | gpt-oss-120b | 0.31 | 0.31 | 0.32 | 0.15 | 0.16 | 0.23 |
| A5 missing signer | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.01 | 0.01 | 0.01 |
| A5 missing signer | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 |
| A5 missing signer | Nemotron-3-Super | 0.96 | 0.66 | 0.49 | 0.10 | 0.10 | 0.07 |
| A5 missing signer | Gemma-4-31B | 1.00 | 0.67 | 0.51 | 0.00 | 0.00 | 0.01 |
| A5 missing signer | DeepSeek-V3.2 (thinking) | 0.98 | 0.67 | 0.52 | 0.04 | 0.04 | 0.05 |
| A6 arbitrary CPI | gpt-oss-120b | 0.94 | 0.73 | 0.66 | 0.58 | 0.53 | 0.48 |
| A6 arbitrary CPI | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.25 | 0.22 | 0.12 |
| A6 arbitrary CPI | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 |
| A6 arbitrary CPI | Nemotron-3-Super | 0.95 | 0.65 | 0.49 | 0.06 | 0.06 | 0.04 |
| A6 arbitrary CPI | Gemma-4-31B | 0.99 | 0.66 | 0.49 | 0.02 | 0.02 | 0.01 |
| A6 arbitrary CPI | DeepSeek-V3.2 (thinking) | 0.95 | 0.66 | 0.52 | 0.17 | 0.16 | 0.12 |
| All pooled | gpt-oss-120b | 0.79 | 0.65 | 0.58 | 0.55 | 0.50 | 0.46 |
| All pooled | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.25 | 0.22 | 0.12 |
| All pooled | Llama-3.3-70B | 1.00 | 0.67 | 0.50 | 0.00 | 0.00 | 0.00 |
| All pooled | Nemotron-3-Super | 0.98 | 0.66 | 0.51 | 0.24 | 0.22 | 0.14 |
| All pooled | Gemma-4-31B | 1.00 | 0.67 | 0.50 | 0.16 | 0.15 | 0.08 |
| All pooled | DeepSeek-V3.2 (thinking) | 0.97 | 0.67 | 0.52 | 0.24 | 0.23 | 0.16 |
