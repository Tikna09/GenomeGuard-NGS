
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Paths
results = Path("benchmark_results")
output = results / "figures"
output.mkdir(parents=True, exist_ok=True)

# Load existing benchmark summary
df = pd.read_csv(results / "benchmark_summary.csv")

tls = df[df["configuration"] == "TLS-only original"].sort_values("size_mib")
gg = df[df["configuration"] == "GenomeGuard"].sort_values("size_mib")

sizes = [1, 10, 50]
tls = tls.set_index("size_mib").loc[sizes]
gg = gg.set_index("size_mib").loc[sizes]

def plot_comparison(column, ylabel, title, filename):
    x = range(len(sizes))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        [i - width / 2 for i in x],
        tls[column],
        width,
        label="TLS-only (original)"
    )
    ax.bar(
        [i + width / 2 for i in x],
        gg[column],
        width,
        label="GenomeGuard-NGS"
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{s} MiB" for s in sizes])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output / filename, dpi=300)
    plt.close(fig)

# Figure 1: Median throughput
plot_comparison(
    "median_throughput",
    "Throughput (MiB/s)",
    "Median Transfer Throughput",
    "figure1_median_throughput.png"
)

# Figure 2: Median latency
plot_comparison(
    "median_latency",
    "Latency (seconds)",
    "Median End-to-End Transfer Latency",
    "figure2_median_latency.png"
)

# Figure 3: Throughput variability
plot_comparison(
    "std_dev_throughput",
    "Standard Deviation (MiB/s)",
    "Throughput Variability Across Five Trials",
    "figure3_throughput_variability.png"
)

print("Successfully generated 3 figures:")
for file in sorted(output.glob("*.png")):
    print(file)

