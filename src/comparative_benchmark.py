import csv
import statistics
import tempfile
import time
from pathlib import Path

from src.authentication import create_hmac
from src.message_authentication import create_message_tag
from src.persistent_freshness_pipeline import (
    PersistentFreshnessPipeline,
)
from src.secure_pipeline import SecurePipeline


KEY = b"local-comparison-key"
PAYLOAD = b"ACGT" * 1024
TRIALS = 200
ROUNDS = 5

OUTPUT_PATH = Path("results/comparative_benchmark.csv")


def benchmark_baseline():
    pipeline = SecurePipeline()
    latencies = []
    accepted = 0

    for index in range(TRIALS):
        message_id = f"baseline-{index}"
        tag = create_hmac(KEY, PAYLOAD)

        start = time.perf_counter()
        result = pipeline.process_message(
            message_id, PAYLOAD, KEY, tag
        )
        latencies.append((time.perf_counter() - start) * 1000)
        accepted += int(result["accepted"])

    return accepted, latencies


def benchmark_persistent(database_path):
    pipeline = PersistentFreshnessPipeline(database_path)
    latencies = []
    accepted = 0

    for index in range(TRIALS):
        stream_id = f"stream-{index}"
        message_id = f"persistent-{index}"
        sequence_number = 1

        tag = create_message_tag(
            KEY,
            stream_id,
            message_id,
            sequence_number,
            PAYLOAD,
        )

        start = time.perf_counter()
        result = pipeline.process(
            KEY,
            stream_id,
            message_id,
            sequence_number,
            PAYLOAD,
            tag,
        )
        latencies.append((time.perf_counter() - start) * 1000)
        accepted += int(result["accepted"])

    return accepted, latencies


def summarize(name, round_number, accepted, latencies):
    return {
        "pipeline": name,
        "round": round_number,
        "trials": TRIALS,
        "payload_size_bytes": len(PAYLOAD),
        "accepted": accepted,
        "rejected": TRIALS - accepted,
        "mean_latency_ms": statistics.mean(latencies),
        "median_latency_ms": statistics.median(latencies),
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
    }


def main():
    results = []

    with tempfile.TemporaryDirectory() as temp_dir:
        for round_number in range(1, ROUNDS + 1):
            # Run both implementations in each round.
            baseline_accepted, baseline_latencies = (
                benchmark_baseline()
            )

            database_path = str(
                Path(temp_dir) / f"freshness-{round_number}.sqlite3"
            )
            persistent_accepted, persistent_latencies = (
                benchmark_persistent(database_path)
            )

            results.append(
                summarize(
                    "baseline_in_memory",
                    round_number,
                    baseline_accepted,
                    baseline_latencies,
                )
            )
            results.append(
                summarize(
                    "persistent_freshness",
                    round_number,
                    persistent_accepted,
                    persistent_latencies,
                )
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    print("GenomeGuard-NGS - Comparative Benchmark")
    print("---------------------------------------")
    print(f"Payload size: {len(PAYLOAD)} bytes")
    print(f"Trials per pipeline per round: {TRIALS}")
    print(f"Rounds: {ROUNDS}")
    print(f"Total messages per pipeline: {TRIALS * ROUNDS}")

    for name in ("baseline_in_memory", "persistent_freshness"):
        selected = [
            row for row in results if row["pipeline"] == name
        ]
        means = [row["mean_latency_ms"] for row in selected]
        medians = [row["median_latency_ms"] for row in selected]
        accepted_total = sum(row["accepted"] for row in selected)

        print(f"\nPipeline: {name}")
        print(f"Accepted: {accepted_total}/{TRIALS * ROUNDS}")
        print(f"Rejected: {TRIALS * ROUNDS - accepted_total}")
        print(f"Average of round mean latencies: {statistics.mean(means):.4f} ms")
        print(f"Average of round median latencies: {statistics.mean(medians):.4f} ms")

    print(f"\nCSV results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

