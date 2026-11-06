# Final Accuracy (adjudicated labels)

Generated from `detection/results/graded/adjudicated/` with the counting in `detection/metrics.py`.
Positives: 100 vulnerable runs per cell. Negatives: 100 secure-source or benign-trace runs per
cell. The blocked attempt is excluded from the matrix; its flag count is shown separately.
**Flagged** = the model said yes. **Diagnosed** = the model also named the planted bug (graded);
false positives are the same at both levels. The main study has timing hidden; the timing
ablation (timing shown) follows in its own section.

## Flagged

### Source Code

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 56 | 44 | 0.64 | 1.00 | 0.78 | 0.72 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 100 | 0 | 98 | 2 | 0.51 | 1.00 | 0.67 | 0.51 |
| Gemma-4-31B | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 |
| DeepSeek-V3.2 (thinking) | 97 | 3 | 98 | 2 | 0.50 | 0.97 | 0.66 | 0.49 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 91 | 9 | 66 | 34 | 0.58 | 0.91 | 0.71 | 0.62 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 100 | 0 | 95 | 5 | 0.51 | 1.00 | 0.68 | 0.53 |
| Gemma-4-31B | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 |
| DeepSeek-V3.2 (thinking) | 97 | 3 | 89 | 11 | 0.52 | 0.97 | 0.68 | 0.54 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 31 | 69 | 68 | 32 | 0.31 | 0.31 | 0.31 | 0.32 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 96 | 4 | 97 | 3 | 0.50 | 0.96 | 0.66 | 0.49 |
| Gemma-4-31B | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 |
| DeepSeek-V3.2 (thinking) | 98 | 2 | 94 | 6 | 0.51 | 0.98 | 0.67 | 0.52 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 94 | 6 | 62 | 38 | 0.60 | 0.94 | 0.73 | 0.66 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 95 | 5 | 97 | 3 | 0.49 | 0.95 | 0.65 | 0.49 |
| Gemma-4-31B | 99 | 1 | 100 | 0 | 0.50 | 0.99 | 0.66 | 0.49 |
| DeepSeek-V3.2 (thinking) | 95 | 5 | 92 | 8 | 0.51 | 0.95 | 0.66 | 0.52 |

#### All four attacks pooled (Source Code)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 316 | 84 | 252 | 148 | 0.56 | 0.79 | 0.65 | 0.58 |
| DeepSeek-V3.2 | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 391 | 9 | 387 | 13 | 0.50 | 0.98 | 0.66 | 0.51 |
| Gemma-4-31B | 399 | 1 | 397 | 3 | 0.50 | 1.00 | 0.67 | 0.50 |
| DeepSeek-V3.2 (thinking) | 387 | 13 | 373 | 27 | 0.51 | 0.97 | 0.67 | 0.52 |

### Transaction Information

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 99 | 1 | 1 | 99 | 0.99 | 0.99 | 0.99 | 0.99 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 66 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 29 | 71 | 1 | 99 | 0.97 | 0.29 | 0.45 | 0.64 | 100 |
| Gemma-4-31B | 47 | 53 | 75 | 25 | 0.39 | 0.47 | 0.42 | 0.36 | 20 |
| DeepSeek-V3.2 (thinking) | 82 | 18 | 19 | 81 | 0.81 | 0.82 | 0.82 | 0.81 | 58 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 98 | 2 | 85 | 15 | 0.54 | 0.98 | 0.69 | 0.56 | 92 |
| DeepSeek-V3.2 | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 2 | 98 | 14 | 86 | 0.12 | 0.02 | 0.03 | 0.44 | 99 |
| Gemma-4-31B | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 100 |
| DeepSeek-V3.2 (thinking) | 94 | 6 | 33 | 67 | 0.74 | 0.94 | 0.83 | 0.81 | 100 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 78 |
| Llama-3.3-70B | 0 | 100 | 57 | 43 | 0.00 | 0.00 | 0.00 | 0.21 | 100 |
| Nemotron-3-Super | 96 | 4 | 81 | 19 | 0.54 | 0.96 | 0.69 | 0.57 | 99 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 11 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 94 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 99 | 1 | 76 | 24 | 0.57 | 0.99 | 0.72 | 0.61 | 23 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 100 | 0 | 4 | 96 | 0.96 | 1.00 | 0.98 | 0.98 | 100 |
| Nemotron-3-Super | 99 | 1 | 12 | 88 | 0.89 | 0.99 | 0.94 | 0.94 | 87 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 70 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 100 |

#### All four attacks pooled (Transaction Information)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 396 | 4 | 262 | 138 | 0.60 | 0.99 | 0.75 | 0.67 | 115 |
| DeepSeek-V3.2 | 400 | 0 | 398 | 2 | 0.50 | 1.00 | 0.67 | 0.50 | 344 |
| Llama-3.3-70B | 100 | 300 | 61 | 339 | 0.62 | 0.25 | 0.36 | 0.55 | 400 |
| Nemotron-3-Super | 226 | 174 | 108 | 292 | 0.68 | 0.56 | 0.62 | 0.65 | 385 |
| Gemma-4-31B | 347 | 53 | 374 | 26 | 0.48 | 0.87 | 0.62 | 0.47 | 201 |
| DeepSeek-V3.2 (thinking) | 376 | 24 | 251 | 149 | 0.60 | 0.94 | 0.73 | 0.66 | 352 |

## Diagnosed

### Source Code

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 94 | 6 | 56 | 44 | 0.63 | 0.94 | 0.75 | 0.69 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nemotron-3-Super | 30 | 70 | 98 | 2 | 0.23 | 0.30 | 0.26 | 0.16 |
| Gemma-4-31B | 5 | 95 | 99 | 1 | 0.05 | 0.05 | 0.05 | 0.03 |
| DeepSeek-V3.2 (thinking) | 32 | 68 | 98 | 2 | 0.25 | 0.32 | 0.28 | 0.17 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 51 | 49 | 66 | 34 | 0.44 | 0.51 | 0.47 | 0.42 |
| DeepSeek-V3.2 | 73 | 27 | 100 | 0 | 0.42 | 0.73 | 0.53 | 0.36 |
| Llama-3.3-70B | 1 | 99 | 100 | 0 | 0.01 | 0.01 | 0.01 | 0.01 |
| Nemotron-3-Super | 49 | 51 | 95 | 5 | 0.34 | 0.49 | 0.40 | 0.27 |
| Gemma-4-31B | 56 | 44 | 99 | 1 | 0.36 | 0.56 | 0.44 | 0.28 |
| DeepSeek-V3.2 (thinking) | 45 | 55 | 89 | 11 | 0.34 | 0.45 | 0.38 | 0.28 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 15 | 85 | 68 | 32 | 0.18 | 0.15 | 0.16 | 0.23 |
| DeepSeek-V3.2 | 1 | 99 | 100 | 0 | 0.01 | 0.01 | 0.01 | 0.01 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nemotron-3-Super | 10 | 90 | 97 | 3 | 0.09 | 0.10 | 0.10 | 0.07 |
| Gemma-4-31B | 0 | 100 | 99 | 1 | 0.00 | 0.00 | 0.00 | 0.01 |
| DeepSeek-V3.2 (thinking) | 4 | 96 | 94 | 6 | 0.04 | 0.04 | 0.04 | 0.05 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 58 | 42 | 62 | 38 | 0.48 | 0.58 | 0.53 | 0.48 |
| DeepSeek-V3.2 | 25 | 75 | 100 | 0 | 0.20 | 0.25 | 0.22 | 0.12 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nemotron-3-Super | 6 | 94 | 97 | 3 | 0.06 | 0.06 | 0.06 | 0.04 |
| Gemma-4-31B | 2 | 98 | 100 | 0 | 0.02 | 0.02 | 0.02 | 0.01 |
| DeepSeek-V3.2 (thinking) | 17 | 83 | 92 | 8 | 0.16 | 0.17 | 0.16 | 0.12 |

#### All four attacks pooled (Source Code)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 218 | 182 | 252 | 148 | 0.46 | 0.55 | 0.50 | 0.46 |
| DeepSeek-V3.2 | 99 | 301 | 400 | 0 | 0.20 | 0.25 | 0.22 | 0.12 |
| Llama-3.3-70B | 1 | 399 | 400 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nemotron-3-Super | 95 | 305 | 387 | 13 | 0.20 | 0.24 | 0.22 | 0.14 |
| Gemma-4-31B | 63 | 337 | 397 | 3 | 0.14 | 0.16 | 0.15 | 0.08 |
| DeepSeek-V3.2 (thinking) | 98 | 302 | 373 | 27 | 0.21 | 0.24 | 0.23 | 0.16 |

### Transaction Information

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 1 | 99 | 0.00 | 0.00 | 0.00 | 0.49 | 0 |
| DeepSeek-V3.2 | 3 | 97 | 99 | 1 | 0.03 | 0.03 | 0.03 | 0.02 | 66 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 3 | 97 | 1 | 99 | 0.75 | 0.03 | 0.06 | 0.51 | 100 |
| Gemma-4-31B | 7 | 93 | 75 | 25 | 0.09 | 0.07 | 0.08 | 0.16 | 20 |
| DeepSeek-V3.2 (thinking) | 28 | 72 | 19 | 81 | 0.60 | 0.28 | 0.38 | 0.55 | 58 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 85 | 15 | 0.00 | 0.00 | 0.00 | 0.07 | 92 |
| DeepSeek-V3.2 | 0 | 100 | 99 | 1 | 0.00 | 0.00 | 0.00 | 0.01 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 0 | 100 | 14 | 86 | 0.00 | 0.00 | 0.00 | 0.43 | 99 |
| Gemma-4-31B | 1 | 99 | 99 | 1 | 0.01 | 0.01 | 0.01 | 0.01 | 100 |
| DeepSeek-V3.2 (thinking) | 30 | 70 | 33 | 67 | 0.48 | 0.30 | 0.37 | 0.48 | 100 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 78 |
| Llama-3.3-70B | 0 | 100 | 57 | 43 | 0.00 | 0.00 | 0.00 | 0.21 | 100 |
| Nemotron-3-Super | 96 | 4 | 81 | 19 | 0.54 | 0.96 | 0.69 | 0.57 | 99 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 11 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 94 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 76 | 24 | 0.00 | 0.00 | 0.00 | 0.12 | 23 |
| DeepSeek-V3.2 | 1 | 99 | 100 | 0 | 0.01 | 0.01 | 0.01 | 0.01 | 100 |
| Llama-3.3-70B | 0 | 100 | 4 | 96 | 0.00 | 0.00 | 0.00 | 0.48 | 100 |
| Nemotron-3-Super | 1 | 99 | 12 | 88 | 0.08 | 0.01 | 0.02 | 0.45 | 87 |
| Gemma-4-31B | 4 | 96 | 100 | 0 | 0.04 | 0.04 | 0.04 | 0.02 | 70 |
| DeepSeek-V3.2 (thinking) | 33 | 67 | 99 | 1 | 0.25 | 0.33 | 0.28 | 0.17 | 100 |

#### All four attacks pooled (Transaction Information)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 300 | 262 | 138 | 0.28 | 0.25 | 0.26 | 0.30 | 115 |
| DeepSeek-V3.2 | 104 | 296 | 398 | 2 | 0.21 | 0.26 | 0.23 | 0.13 | 344 |
| Llama-3.3-70B | 0 | 400 | 61 | 339 | 0.00 | 0.00 | 0.00 | 0.42 | 400 |
| Nemotron-3-Super | 100 | 300 | 108 | 292 | 0.48 | 0.25 | 0.33 | 0.49 | 385 |
| Gemma-4-31B | 112 | 288 | 374 | 26 | 0.23 | 0.28 | 0.25 | 0.17 | 201 |
| DeepSeek-V3.2 (thinking) | 191 | 209 | 251 | 149 | 0.43 | 0.48 | 0.45 | 0.42 | 352 |

## Timing ablation (Transaction Information, timing shown)

The same three traces per attack with step times shown (A1 also with its relay delay and the
normal range). Compare with the Transaction Information tables above, where timing is hidden.

### Flagged

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 89 | 11 | 60 | 40 | 0.60 | 0.89 | 0.71 | 0.65 | 5 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 35 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 29 | 71 | 1 | 99 | 0.97 | 0.29 | 0.45 | 0.64 | 97 |
| Gemma-4-31B | 90 | 10 | 97 | 3 | 0.48 | 0.90 | 0.63 | 0.47 | 100 |
| DeepSeek-V3.2 (thinking) | 70 | 30 | 40 | 60 | 0.64 | 0.70 | 0.67 | 0.65 | 81 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 95 | 5 | 6 | 94 | 0.94 | 0.95 | 0.95 | 0.94 | 99 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 4 | 96 | 16 | 84 | 0.20 | 0.04 | 0.07 | 0.44 | 94 |
| Gemma-4-31B | 100 | 0 | 98 | 2 | 0.51 | 1.00 | 0.67 | 0.51 | 100 |
| DeepSeek-V3.2 (thinking) | 91 | 9 | 37 | 63 | 0.71 | 0.91 | 0.80 | 0.77 | 100 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 2 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 99 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Nemotron-3-Super | 99 | 1 | 92 | 8 | 0.52 | 0.99 | 0.68 | 0.54 | 99 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 35 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 94 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 0 | 100 | 1.00 | 1.00 | 1.00 | 1.00 | 98 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 100 | 0 | 0 | 100 | 1.00 | 1.00 | 1.00 | 1.00 | 100 |
| Nemotron-3-Super | 94 | 6 | 6 | 94 | 0.94 | 0.94 | 0.94 | 0.94 | 86 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 75 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 97 | 3 | 0.51 | 1.00 | 0.67 | 0.52 | 99 |

#### All four attacks pooled (Transaction Information, timing shown)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 384 | 16 | 166 | 234 | 0.70 | 0.96 | 0.81 | 0.77 | 204 |
| DeepSeek-V3.2 | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 334 |
| Llama-3.3-70B | 100 | 300 | 100 | 300 | 0.50 | 0.25 | 0.33 | 0.50 | 400 |
| Nemotron-3-Super | 226 | 174 | 115 | 285 | 0.66 | 0.56 | 0.61 | 0.64 | 376 |
| Gemma-4-31B | 390 | 10 | 395 | 5 | 0.50 | 0.97 | 0.66 | 0.49 | 310 |
| DeepSeek-V3.2 (thinking) | 361 | 39 | 274 | 126 | 0.57 | 0.90 | 0.70 | 0.61 | 374 |

### Diagnosed

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 60 | 40 | 0.00 | 0.00 | 0.00 | 0.20 | 5 |
| DeepSeek-V3.2 | 21 | 79 | 100 | 0 | 0.17 | 0.21 | 0.19 | 0.10 | 35 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 2 | 98 | 1 | 99 | 0.67 | 0.02 | 0.04 | 0.51 | 97 |
| Gemma-4-31B | 1 | 99 | 97 | 3 | 0.01 | 0.01 | 0.01 | 0.02 | 100 |
| DeepSeek-V3.2 (thinking) | 19 | 81 | 40 | 60 | 0.32 | 0.19 | 0.24 | 0.40 | 81 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 6 | 94 | 0.00 | 0.00 | 0.00 | 0.47 | 99 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 0 | 100 | 16 | 84 | 0.00 | 0.00 | 0.00 | 0.42 | 94 |
| Gemma-4-31B | 2 | 98 | 98 | 2 | 0.02 | 0.02 | 0.02 | 0.02 | 100 |
| DeepSeek-V3.2 (thinking) | 24 | 76 | 37 | 63 | 0.39 | 0.24 | 0.30 | 0.43 | 100 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 2 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 99 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Nemotron-3-Super | 99 | 1 | 92 | 8 | 0.52 | 0.99 | 0.68 | 0.54 | 99 |
| Gemma-4-31B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 35 |
| DeepSeek-V3.2 (thinking) | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 94 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 98 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 1 | 99 | 6 | 94 | 0.14 | 0.01 | 0.02 | 0.47 | 86 |
| Gemma-4-31B | 2 | 98 | 100 | 0 | 0.02 | 0.02 | 0.02 | 0.01 | 75 |
| DeepSeek-V3.2 (thinking) | 39 | 61 | 97 | 3 | 0.29 | 0.39 | 0.33 | 0.21 | 99 |

#### All four attacks pooled (Transaction Information, timing shown)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 300 | 166 | 234 | 0.38 | 0.25 | 0.30 | 0.42 | 204 |
| DeepSeek-V3.2 | 121 | 279 | 400 | 0 | 0.23 | 0.30 | 0.26 | 0.15 | 334 |
| Llama-3.3-70B | 0 | 400 | 100 | 300 | 0.00 | 0.00 | 0.00 | 0.38 | 400 |
| Nemotron-3-Super | 102 | 298 | 115 | 285 | 0.47 | 0.26 | 0.33 | 0.48 | 376 |
| Gemma-4-31B | 105 | 295 | 395 | 5 | 0.21 | 0.26 | 0.23 | 0.14 | 310 |
| DeepSeek-V3.2 (thinking) | 182 | 218 | 274 | 126 | 0.40 | 0.46 | 0.43 | 0.39 | 374 |
