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
| gpt-oss-120b | 98 | 2 | 51 | 49 | 0.66 | 0.98 | 0.79 | 0.73 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 98 | 2 | 97 | 3 | 0.50 | 0.98 | 0.66 | 0.51 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 67 | 33 | 0.60 | 1.00 | 0.75 | 0.67 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 100 | 0 | 97 | 3 | 0.51 | 1.00 | 0.67 | 0.52 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 61 | 39 | 50 | 50 | 0.55 | 0.61 | 0.58 | 0.56 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 98 | 2 | 94 | 6 | 0.51 | 0.98 | 0.67 | 0.52 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 50 | 50 | 0.67 | 1.00 | 0.80 | 0.75 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 99 | 1 | 99 | 1 | 0.50 | 0.99 | 0.66 | 0.50 |

#### All four attacks pooled (Source Code)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 359 | 41 | 218 | 182 | 0.62 | 0.90 | 0.73 | 0.68 |
| DeepSeek-V3.2 | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 395 | 5 | 387 | 13 | 0.51 | 0.99 | 0.67 | 0.51 |

### Transaction Information

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 99 | 1 | 1 | 99 | 0.99 | 0.99 | 0.99 | 0.99 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 66 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 29 | 71 | 1 | 99 | 0.97 | 0.29 | 0.45 | 0.64 | 100 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 98 | 2 | 85 | 15 | 0.54 | 0.98 | 0.69 | 0.56 | 92 |
| DeepSeek-V3.2 | 100 | 0 | 99 | 1 | 0.50 | 1.00 | 0.67 | 0.51 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 2 | 98 | 14 | 86 | 0.12 | 0.02 | 0.03 | 0.44 | 99 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 78 |
| Llama-3.3-70B | 0 | 100 | 57 | 43 | 0.00 | 0.00 | 0.00 | 0.21 | 100 |
| Nemotron-3-Super | 96 | 4 | 81 | 19 | 0.54 | 0.96 | 0.69 | 0.57 | 99 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 99 | 1 | 76 | 24 | 0.57 | 0.99 | 0.72 | 0.61 | 23 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 100 | 0 | 4 | 96 | 0.96 | 1.00 | 0.98 | 0.98 | 100 |
| Nemotron-3-Super | 99 | 1 | 12 | 88 | 0.89 | 0.99 | 0.94 | 0.94 | 87 |

#### All four attacks pooled (Transaction Information)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 396 | 4 | 262 | 138 | 0.60 | 0.99 | 0.75 | 0.67 | 115 |
| DeepSeek-V3.2 | 400 | 0 | 398 | 2 | 0.50 | 1.00 | 0.67 | 0.50 | 344 |
| Llama-3.3-70B | 100 | 300 | 61 | 339 | 0.62 | 0.25 | 0.36 | 0.55 | 400 |
| Nemotron-3-Super | 226 | 174 | 108 | 292 | 0.68 | 0.56 | 0.62 | 0.65 | 385 |

## Diagnosed

### Source Code

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 96 | 4 | 51 | 49 | 0.65 | 0.96 | 0.78 | 0.72 |
| DeepSeek-V3.2 | 2 | 98 | 100 | 0 | 0.02 | 0.02 | 0.02 | 0.01 |
| Llama-3.3-70B | 5 | 95 | 100 | 0 | 0.05 | 0.05 | 0.05 | 0.03 |
| Nemotron-3-Super | 39 | 61 | 97 | 3 | 0.29 | 0.39 | 0.33 | 0.21 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 67 | 33 | 0.60 | 1.00 | 0.75 | 0.67 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Nemotron-3-Super | 99 | 1 | 97 | 3 | 0.51 | 0.99 | 0.67 | 0.51 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 10 | 90 | 50 | 50 | 0.17 | 0.10 | 0.12 | 0.30 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| Nemotron-3-Super | 5 | 95 | 94 | 6 | 0.05 | 0.05 | 0.05 | 0.06 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 50 | 50 | 0.67 | 1.00 | 0.80 | 0.75 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 |
| Llama-3.3-70B | 83 | 17 | 100 | 0 | 0.45 | 0.83 | 0.59 | 0.41 |
| Nemotron-3-Super | 71 | 29 | 99 | 1 | 0.42 | 0.71 | 0.53 | 0.36 |

#### All four attacks pooled (Source Code)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 306 | 94 | 218 | 182 | 0.58 | 0.77 | 0.66 | 0.61 |
| DeepSeek-V3.2 | 202 | 198 | 400 | 0 | 0.34 | 0.51 | 0.40 | 0.25 |
| Llama-3.3-70B | 188 | 212 | 400 | 0 | 0.32 | 0.47 | 0.38 | 0.23 |
| Nemotron-3-Super | 214 | 186 | 387 | 13 | 0.36 | 0.54 | 0.43 | 0.28 |

### Transaction Information

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 1 | 99 | 0.00 | 0.00 | 0.00 | 0.49 | 0 |
| DeepSeek-V3.2 | 3 | 97 | 99 | 1 | 0.03 | 0.03 | 0.03 | 0.02 | 66 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 3 | 97 | 1 | 99 | 0.75 | 0.03 | 0.06 | 0.51 | 100 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 85 | 15 | 0.00 | 0.00 | 0.00 | 0.07 | 92 |
| DeepSeek-V3.2 | 0 | 100 | 99 | 1 | 0.00 | 0.00 | 0.00 | 0.01 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 0 | 100 | 14 | 86 | 0.00 | 0.00 | 0.00 | 0.43 | 99 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 0 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 78 |
| Llama-3.3-70B | 0 | 100 | 57 | 43 | 0.00 | 0.00 | 0.00 | 0.21 | 100 |
| Nemotron-3-Super | 96 | 4 | 81 | 19 | 0.54 | 0.96 | 0.69 | 0.57 | 99 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 76 | 24 | 0.00 | 0.00 | 0.00 | 0.12 | 23 |
| DeepSeek-V3.2 | 1 | 99 | 100 | 0 | 0.01 | 0.01 | 0.01 | 0.01 | 100 |
| Llama-3.3-70B | 0 | 100 | 4 | 96 | 0.00 | 0.00 | 0.00 | 0.48 | 100 |
| Nemotron-3-Super | 1 | 99 | 12 | 88 | 0.08 | 0.01 | 0.02 | 0.45 | 87 |

#### All four attacks pooled (Transaction Information)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 300 | 262 | 138 | 0.28 | 0.25 | 0.26 | 0.30 | 115 |
| DeepSeek-V3.2 | 104 | 296 | 398 | 2 | 0.21 | 0.26 | 0.23 | 0.13 | 344 |
| Llama-3.3-70B | 0 | 400 | 61 | 339 | 0.00 | 0.00 | 0.00 | 0.42 | 400 |
| Nemotron-3-Super | 100 | 300 | 108 | 292 | 0.48 | 0.25 | 0.33 | 0.49 | 385 |

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

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 95 | 5 | 6 | 94 | 0.94 | 0.95 | 0.95 | 0.94 | 99 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 4 | 96 | 16 | 84 | 0.20 | 0.04 | 0.07 | 0.44 | 94 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 2 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 99 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Nemotron-3-Super | 99 | 1 | 92 | 8 | 0.52 | 0.99 | 0.68 | 0.54 | 99 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 0 | 100 | 1.00 | 1.00 | 1.00 | 1.00 | 98 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 100 |
| Llama-3.3-70B | 100 | 0 | 0 | 100 | 1.00 | 1.00 | 1.00 | 1.00 | 100 |
| Nemotron-3-Super | 94 | 6 | 6 | 94 | 0.94 | 0.94 | 0.94 | 0.94 | 86 |

#### All four attacks pooled (Transaction Information, timing shown)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 384 | 16 | 166 | 234 | 0.70 | 0.96 | 0.81 | 0.77 | 204 |
| DeepSeek-V3.2 | 400 | 0 | 400 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 334 |
| Llama-3.3-70B | 100 | 300 | 100 | 300 | 0.50 | 0.25 | 0.33 | 0.50 | 400 |
| Nemotron-3-Super | 226 | 174 | 115 | 285 | 0.66 | 0.56 | 0.61 | 0.64 | 376 |

### Diagnosed

#### A1 mint confusion

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 60 | 40 | 0.00 | 0.00 | 0.00 | 0.20 | 5 |
| DeepSeek-V3.2 | 21 | 79 | 100 | 0 | 0.17 | 0.21 | 0.19 | 0.10 | 35 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 2 | 98 | 1 | 99 | 0.67 | 0.02 | 0.04 | 0.51 | 97 |

#### A2 sysvar spoof

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 6 | 94 | 0.00 | 0.00 | 0.00 | 0.47 | 99 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 0 | 100 | 16 | 84 | 0.00 | 0.00 | 0.00 | 0.42 | 94 |

#### A5 missing signer

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 2 |
| DeepSeek-V3.2 | 100 | 0 | 100 | 0 | 0.50 | 1.00 | 0.67 | 0.50 | 99 |
| Llama-3.3-70B | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Nemotron-3-Super | 99 | 1 | 92 | 8 | 0.52 | 0.99 | 0.68 | 0.54 | 99 |

#### A6 arbitrary CPI

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 98 |
| DeepSeek-V3.2 | 0 | 100 | 100 | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 100 |
| Llama-3.3-70B | 0 | 100 | 0 | 100 | 0.00 | 0.00 | 0.00 | 0.50 | 100 |
| Nemotron-3-Super | 1 | 99 | 6 | 94 | 0.14 | 0.01 | 0.02 | 0.47 | 86 |

#### All four attacks pooled (Transaction Information, timing shown)

|  | TP | FN | FP | TN | Precision | Recall | F1 | Accuracy | Blocked flagged |
|---|---|---|---|---|---|---|---|---|---|
| gpt-oss-120b | 100 | 300 | 166 | 234 | 0.38 | 0.25 | 0.30 | 0.42 | 204 |
| DeepSeek-V3.2 | 121 | 279 | 400 | 0 | 0.23 | 0.30 | 0.26 | 0.15 | 334 |
| Llama-3.3-70B | 0 | 400 | 100 | 300 | 0.00 | 0.00 | 0.00 | 0.38 | 400 |
| Nemotron-3-Super | 102 | 298 | 115 | 285 | 0.47 | 0.26 | 0.33 | 0.48 | 376 |
