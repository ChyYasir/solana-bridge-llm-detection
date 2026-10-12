export function percentile(sorted: number[], p: number) {
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.min(Math.max(idx, 0), sorted.length - 1)];
}

export function summarize(samples: number[]) {
  const sorted = [...samples].sort((a, b) => a - b);
  const n = sorted.length;
  const mean = sorted.reduce((a, b) => a + b, 0) / n;
  const variance = sorted.reduce((acc, x) => acc + (x - mean) ** 2, 0) / (n - 1);
  const std = Math.sqrt(variance);
  return {
    n,
    min: sorted[0],
    max: sorted[n - 1],
    mean,
    std,
    p95: percentile(sorted, 95),
    p99: percentile(sorted, 99),
    thresholdMean3Std: mean + 3 * std,
  };
}
