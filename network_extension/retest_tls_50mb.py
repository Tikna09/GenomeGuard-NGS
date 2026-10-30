
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

FILE = DATA / "synthetic_50MB.fastq"


def main():
    payload = FILE.read_bytes()
    size_mib = len(payload) / (1024 * 1024)

    context = ssl.create_default_context(cafile=str(CERT))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    rows = []

    for trial in range(1, TRIALS + 1):
        request = urllib.request.Request(
            f"https://{HOST}:{PORT}/transfer",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(payload)),
            },
        )

        start = time.perf_counter()

        with urllib.request.urlopen(
            request, context=context, timeout=180
        ) as response:
            status = response.status
            result = json.loads(response.read())

        elapsed = time.perf_counter() - start
        throughput = size_mib / elapsed

        if status != 200 or result.get("status") != "accepted":
            raise RuntimeError(f"Trial {trial} failed: {result}")

        print(
            f"Trial {trial} | {elapsed:.4f}s | "
            f"{throughput:.2f} MiB/s | ACCEPTED"
        )

        rows.append({
            "configuration": "TLS-only",
            "trial": trial,
            "file": FILE.name,
            "size_mib": size_mib,
            "latency_seconds": elapsed,
            "throughput_mib_s": throughput,
            "http_status": status,
            "result": result["status"],
        })

    output = RESULTS / "tls_50mb_retest.csv"

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {output}")


if __name__ == "__main__":
    main()
