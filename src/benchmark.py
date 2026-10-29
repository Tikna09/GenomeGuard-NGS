
import statistics
import time

from src.authentication import create_hmac
from src.secure_pipeline import SecurePipeline


def run_benchmark(
    message_count: int = 1000,
    payload_size: int = 4096,
) -> None:
    key = b"local-benchmark-key-only"
    payload = b"ACGT" * (payload_size // 4)
    tag = create_hmac(key, payload)

    pipeline = SecurePipeline()
    latencies_ms = []
    accepted = 0

    start = time.perf_counter()

    for index in range(message_count):
        message_id = f"benchmark-{index:06d}"

        message_start = time.perf_counter()
        result = pipeline.process_message(
            message_id, payload, key, tag
        )
        elapsed_ms = (time.perf_counter() - message_start) * 1000

        latencies_ms.append(elapsed_ms)

        if result["accepted"]:
            accepted += 1

    total_seconds = time.perf_counter() - start
    total_bytes = message_count * len(payload)

    print("GenomeGuard NGS - Local Benchmark")
    print("---------------------------------")
    print(f"Messages attempted: {message_count}")
    print(f"Payload size: {len(payload)} bytes")
    print(f"Messages accepted: {accepted}")
    print(f"Messages rejected: {message_count - accepted}")
    print(f"Total elapsed: {total_seconds:.6f} seconds")
    print(f"Throughput: {message_count / total_seconds:.2f} messages/sec")
    print(f"Data rate: {total_bytes / total_seconds / 1024:.2f} KiB/sec")
    print(f"Mean latency: {statistics.mean(latencies_ms):.4f} ms")
    print(f"Median latency: {statistics.median(latencies_ms):.4f} ms")
    print(f"Maximum latency: {max(latencies_ms):.4f} ms")


if __name__ == "__main__":
    run_benchmark()
