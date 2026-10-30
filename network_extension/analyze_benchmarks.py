
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "benchmark_results"

tls = pd.read_csv(RESULTS / "tls_baseline_repeated.csv")
gg = pd.read_csv(RESULTS / "genomeguard_repeated.csv")
retest = pd.read_csv(RESULTS / "tls_50mb_retest.csv")

datasets = {
    "TLS-only original": tls,
    "GenomeGuard": gg,
    "TLS-only 50 MiB retest": retest,
}

rows = []

for configuration, df in datasets.items():
    for size, group in df.groupby("size_mib"):
        values = group["throughput_mib_s"]
        latency = group["latency_seconds"]

        rows.append({
            "configuration": configuration,
            "size_mib": size,
            "trials": len(group),
            "mean_throughput": values.mean(),
            "median_throughput": values.median(),
            "std_dev_throughput": values.std(ddof=1),
            "min_throughput": values.min(),
            "max_throughput": values.max(),
            "mean_latency": latency.mean(),
            "median_latency": latency.median(),
        })

summary = pd.DataFrame(rows)

output = RESULTS / "benchmark_summary.csv"
summary.to_csv(output, index=False)

print("\nBENCHMARK SUMMARY\n")
print(summary.round(3).to_string(index=False))
print(f"\nSaved to: {output}")
