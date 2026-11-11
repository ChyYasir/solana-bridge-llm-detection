# Transaction information: recall, F1, accuracy (adjudicated)

| Attack | Model | Flagged recall | Flagged F1 | Flagged accuracy | Diagnosed recall | Diagnosed F1 | Diagnosed accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|
| A1 mint confusion | gpt-oss-120b | 0.99 | 0.99 | 0.99 | 0.00 | 0.00 | 0.49 | 0 |
| A1 mint confusion | DeepSeek-V3.2 | 1.00 | 0.67 | 0.51 | 0.03 | 0.03 | 0.02 | 66 |
| A1 mint confusion | Llama-3.3-70B | 0.00 | 0.00 | 0.50 | 0.00 | 0.00 | 0.50 | 100 |
| A1 mint confusion | Nemotron-3-Super | 0.29 | 0.45 | 0.64 | 0.03 | 0.06 | 0.51 | 100 |
| A1 mint confusion | Gemma-4-31B | 0.48 | 0.43 | 0.36 | 0.08 | 0.09 | 0.17 | 18 |
| A1 mint confusion | DeepSeek-V3.2 (thinking) | 0.82 | 0.82 | 0.81 | 0.28 | 0.38 | 0.55 | 58 |
| A2 sysvar spoof | gpt-oss-120b | 0.98 | 0.69 | 0.56 | 0.00 | 0.00 | 0.07 | 92 |
| A2 sysvar spoof | DeepSeek-V3.2 | 1.00 | 0.67 | 0.51 | 0.00 | 0.00 | 0.01 | 100 |
| A2 sysvar spoof | Llama-3.3-70B | 0.00 | 0.00 | 0.50 | 0.00 | 0.00 | 0.50 | 100 |
| A2 sysvar spoof | Nemotron-3-Super | 0.02 | 0.03 | 0.44 | 0.00 | 0.00 | 0.43 | 99 |
| A2 sysvar spoof | Gemma-4-31B | 1.00 | 0.67 | 0.51 | 0.01 | 0.01 | 0.01 | 100 |
| A2 sysvar spoof | DeepSeek-V3.2 (thinking) | 0.94 | 0.83 | 0.81 | 0.30 | 0.37 | 0.48 | 100 |
| A5 missing signer | gpt-oss-120b | 1.00 | 0.67 | 0.50 | 1.00 | 0.67 | 0.50 | 0 |
| A5 missing signer | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 1.00 | 0.67 | 0.50 | 78 |
| A5 missing signer | Llama-3.3-70B | 0.00 | 0.00 | 0.21 | 0.00 | 0.00 | 0.21 | 100 |
| A5 missing signer | Nemotron-3-Super | 0.96 | 0.69 | 0.57 | 0.96 | 0.69 | 0.57 | 99 |
| A5 missing signer | Gemma-4-31B | 1.00 | 0.67 | 0.50 | 1.00 | 0.67 | 0.50 | 6 |
| A5 missing signer | DeepSeek-V3.2 (thinking) | 1.00 | 0.67 | 0.50 | 1.00 | 0.67 | 0.50 | 94 |
| A6 arbitrary CPI | gpt-oss-120b | 0.99 | 0.72 | 0.61 | 0.00 | 0.00 | 0.12 | 23 |
| A6 arbitrary CPI | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.01 | 0.01 | 0.01 | 100 |
| A6 arbitrary CPI | Llama-3.3-70B | 1.00 | 0.98 | 0.98 | 0.00 | 0.00 | 0.48 | 100 |
| A6 arbitrary CPI | Nemotron-3-Super | 0.99 | 0.94 | 0.94 | 0.01 | 0.02 | 0.45 | 87 |
| A6 arbitrary CPI | Gemma-4-31B | 1.00 | 0.67 | 0.50 | 0.04 | 0.04 | 0.02 | 67 |
| A6 arbitrary CPI | DeepSeek-V3.2 (thinking) | 1.00 | 0.67 | 0.51 | 0.33 | 0.28 | 0.17 | 100 |
| All pooled | gpt-oss-120b | 0.99 | 0.75 | 0.67 | 0.25 | 0.26 | 0.30 | 115 |
| All pooled | DeepSeek-V3.2 | 1.00 | 0.67 | 0.50 | 0.26 | 0.23 | 0.13 | 344 |
| All pooled | Llama-3.3-70B | 0.25 | 0.36 | 0.55 | 0.00 | 0.00 | 0.42 | 400 |
| All pooled | Nemotron-3-Super | 0.56 | 0.62 | 0.65 | 0.25 | 0.33 | 0.49 | 385 |
| All pooled | Gemma-4-31B | 0.87 | 0.62 | 0.47 | 0.28 | 0.25 | 0.17 | 191 |
| All pooled | DeepSeek-V3.2 (thinking) | 0.94 | 0.73 | 0.66 | 0.48 | 0.45 | 0.42 | 352 |
