
import json
import ssl
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

HOST = "192.168.250.133"
PORT = 8444

BASE = Path(__file__).resolve().parent
CERT = BASE / "certs" / "server-cert.pem"
DATA = BASE / "benchmark_data"
RESULTS = BASE / "benchmark_results"

RESULTS.mkdir(exist_ok=True)


def transfer(file_path):
    payload = file_path.read_bytes()

    context = ssl.create_default_context(cafile=str(CERT))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    request = urllib.request.Request(
        f"https://{HOST}:{PORT}/transfer",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(payload))
        }
    )

    start = time.perf_counter()

    with urllib.request.urlopen(
        request, context=context, timeout=180
    ) as response:
        result = json.loads(response.read())

    elapsed = time.perf_counter() - start
    size_mb = len(payload) / (1024 * 1024)
    throughput = size_mb / elapsed if elapsed else 0

    print(f"\nFile: {file_path.name}")
    print(f"Size: {size_mb:.2f} MB")
    print(f"HTTP status: {response.status}")
    print(f"Server result: {result['status']}")
    print(f"Total transfer time: {elapsed:.4f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")

    return {
        "configuration": "TLS-only",
        "file": file_path.name,
        "size_mb": size_mb,
        "latency_seconds": elapsed,
        "throughput_mbps": throughput
    }


def main():
    files = [
        DATA / "synthetic_1MB.fastq",
        DATA / "synthetic_10MB.fastq",
        DATA / "synthetic_50MB.fastq"
    ]

    rows = []

    for file_path in files:
        if not file_path.is_file():
            print(f"Missing file: {file_path}")
            sys.exit(1)

        rows.append(transfer(file_path))

    import csv

    output = RESULTS / "tls_baseline.csv"

    with output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nBenchmark saved: {output}")


if __name__ == "__main__":

    main()
