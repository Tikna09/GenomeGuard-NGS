
import pandas as pd
from pathlib import Path

folder = Path("benchmark_results")

files = {
    "TLS-only original": folder / "tls_baseline_repeated.csv",
    "GenomeGuard": folder / "genomeguard_repeated.csv",
    "TLS-only 50 MiB retest": folder / "tls_50mb_retest.csv"
}

frames = []

for configuration, path in files.items():
    df = pd.read_csv(path)

    df["configuration"] = configuration
    frames.append(df)

data = pd.concat(frames, ignore_index=True)

summary = (
    data.groupby(["configuration", "size_mib"])
    .agg(
        trials=("throughput_mib_s", "count"),
        mean_throughput=("throughput_mib_s", "mean"),
        median_throughput=("throughput_mib_s", "median"),
        std_dev=("throughput_mib_s", "std"),
        mean_latency=("latency_seconds", "mean"),
        median_latency=("latency_seconds", "median")
    )
    .round(3)
    .reset_index()
)

output = folder / "final_benchmark_comparison.csv"
summary.to_csv(output, index=False)

print("\nFINAL BENCHMARK COMPARISON\n")
print(summary.to_string(index=False))
print(f"\nSaved to: {output}")
