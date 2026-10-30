
import csv
import json
import ssl
import time
import urllib.request
from pathlib import Path

HOST = "192.168.250.133"
PORT = 8444
TRIALS = 5

BASE = Path(__file__).resolve().parent
CERT = BASE / "certs" / "server-cert.pem"
DATA = BASE / "benchmark_data"
RESULTS = BASE / "benchmark_results"

FILES = [
    "synthetic_1MB.fastq",
    "synthetic_10MB.fastq",
    "synthetic_50MB.fastq",
]


def transfer(filename, context, trial):
    file_path = DATA / filename
    payload = file_path.read_bytes()
    size = len(payload)

    request = urllib.request.Request(
        f"https://{HOST}:{PORT}/transfer",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(size),
        },
    )

    start = time.perf_counter()

    with urllib.request.urlopen(
        request, context=context, timeout=180
    ) as response:
        status = response.status
        result = json.loads(response.read())

    elapsed = time.perf_counter() - start
    size_mib = size / (1024 * 1024)
    throughput = size_mib / elapsed

    if status != 200 or result.get("status") != "accepted":
        raise RuntimeError(
            f"Trial {trial}, {filename} failed: {result}"
        )

    print(
        f"Trial {trial} | {filename} | "
        f"{elapsed:.4f}s | {throughput:.2f} MiB/s | ACCEPTED"
    )

    return {
        "configuration": "TLS-only",
        "trial": trial,
        "file": filename,
        "size_mib": round(size_mib, 4),
        "latency_seconds": elapsed,
        "throughput_mib_s": throughput,
        "http_status": status,
        "result": result["status"],
    }


def main():
    RESULTS.mkdir(exist_ok=True)

    context = ssl.create_default_context(cafile=str(CERT))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    rows = []

    for filename in FILES:
        if not (DATA / filename).is_file():
            raise FileNotFoundError(DATA / filename)

    for trial in range(1, TRIALS + 1):
        for filename in FILES:
            rows.append(transfer(filename, context, trial))

    output = RESULTS / "tls_baseline_repeated.csv"

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCompleted {len(rows)} TLS-only transfers.")
    print(f"Results saved to: {output}")


if __name__ == "__main__":
    main()
