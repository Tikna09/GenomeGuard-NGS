
import csv
import hashlib
import hmac
import json
import ssl
import time
import urllib.request
from pathlib import Path

HOST = "192.168.250.133"
PORT = 8443
SENDER = "Kali-Sender"

BASE = Path(__file__).resolve().parent
KEY_PATH = BASE / "secrets" / "hmac.key"
CERT_PATH = BASE / "certs" / "server-cert.pem"
DATA = BASE / "benchmark_data"
RESULTS = BASE / "benchmark_results"

FILES = [
    ("synthetic_1MB.fastq", 3),
    ("synthetic_10MB.fastq", 4),
    ("synthetic_50MB.fastq", 5),
]


def transfer(filename, sequence, context, key):
    path = DATA / filename
    payload = path.read_bytes()
    size = len(payload)

    digest = hashlib.sha256(payload).hexdigest()

    fields = {
        "version": 1,
        "sender": SENDER,
        "sequence": sequence,
        "sha256": digest,
        "filename": filename,
        "file_size": size,
    }

    signed = json.dumps(
        fields, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    mac = hmac.new(key, signed, hashlib.sha256).hexdigest()
    metadata = {**fields, "hmac": mac}

    metadata_bytes = json.dumps(
        metadata, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    body = metadata_bytes + payload

    request = urllib.request.Request(
        f"https://{HOST}:{PORT}/transfer",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "X-Metadata-Length": str(len(metadata_bytes)),
            "X-File-Length": str(size),
            "Content-Length": str(len(body)),
        },
    )

    start = time.perf_counter()

    with urllib.request.urlopen(
        request, context=context, timeout=180
    ) as response:
        result = json.loads(response.read())
        status = response.status

    elapsed = time.perf_counter() - start
    size_mb = size / (1024 * 1024)

    if status != 200 or result.get("status") != "accepted":
        raise RuntimeError(f"Transfer failed: {result}")

    throughput = size_mb / elapsed

    print(f"\nFile: {filename}")
    print(f"Sequence: {sequence}")
    print(f"HTTP status: {status}")
    print(f"Result: {result['status']}")
    print(f"Total time: {elapsed:.4f} seconds")
    print(f"Throughput: {throughput:.2f} MB/s")

    return {
        "configuration": "GenomeGuard",
        "file": filename,
        "size_mb": round(size_mb, 4),
        "latency_seconds": elapsed,
        "throughput_mbps": throughput,
    }


def main():
    RESULTS.mkdir(exist_ok=True)

    key = KEY_PATH.read_bytes()
    if len(key) != 32:
        raise ValueError("Invalid HMAC key length")

    context = ssl.create_default_context(cafile=str(CERT_PATH))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    rows = []

    for filename, sequence in FILES:
        rows.append(transfer(filename, sequence, context, key))

    output = RESULTS / "genomeguard_benchmark.csv"

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults saved to: {output}")


if __name__ == "__main__":
    main()
