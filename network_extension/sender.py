
import hashlib
import hmac
import json
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path

HOST = "192.168.250.133"
PORT = 8443
SENDER_ID = "Kali-Sender"
SEQUENCE = 2

BASE = Path(__file__).resolve().parent
KEY_PATH = BASE / "secrets" / "hmac.key"
CERT_PATH = BASE / "certs" / "server-cert.pem"
FILE_PATH = BASE / "data" / "sample.fastq"


def main():

    if not KEY_PATH.exists():
        raise FileNotFoundError("HMAC key not found")

    if not CERT_PATH.exists():
        raise FileNotFoundError("Server certificate not found")

    if not FILE_PATH.is_file():
        raise FileNotFoundError("FASTQ file not found")

    key = KEY_PATH.read_bytes()

    if len(key) != 32:
        raise ValueError("HMAC key must be exactly 32 bytes")

    # Read test file
    payload = FILE_PATH.read_bytes()
    file_size = len(payload)

    # Calculate SHA-256
    digest = hashlib.sha256(payload).hexdigest()

    # Create authenticated metadata
    fields = {
        "version": 1,
        "sender": SENDER_ID,
        "sequence": SEQUENCE,
        "sha256": digest,
        "filename": FILE_PATH.name,
        "file_size": file_size
    }

    signed_bytes = json.dumps(
        fields,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    mac = hmac.new(
        key,
        signed_bytes,
        hashlib.sha256
    ).hexdigest()

    metadata = {
        **fields,
        "hmac": mac
    }

    metadata_bytes = json.dumps(
        metadata,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    # HTTP request body: metadata followed by file bytes
    body = metadata_bytes + payload

    # Verify Ubuntu TLS certificate
    context = ssl.create_default_context(
        cafile=str(CERT_PATH)
    )

    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    request = urllib.request.Request(
        url=f"https://{HOST}:{PORT}/transfer",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "X-Metadata-Length": str(len(metadata_bytes)),
            "X-File-Length": str(file_size),
            "Content-Length": str(len(body))
        }
    )

    print("GenomeGuard-NGS Sender")
    print("----------------------")
    print(f"File: {FILE_PATH.name}")
    print(f"File size: {file_size} bytes")
    print(f"SHA-256: {digest}")
    print(f"Sequence: {SEQUENCE}")
    print("Connecting to Ubuntu receiver...")

    try:

        with urllib.request.urlopen(
            request,
            context=context,
            timeout=30
        ) as response:

            result = json.loads(response.read())

            print("\nServer response:")
            print(f"HTTP status: {response.status}")
            print(f"Result: {result.get('status')}")

            if response.status == 200 and result.get("status") == "accepted":
                print("\nTRANSFER SUCCESSFUL")

            else:
                print("\nTRANSFER NOT ACCEPTED")
                sys.exit(1)

    except urllib.error.HTTPError as error:

        print(f"\nHTTP error: {error.code}")
        print(error.read().decode(errors="replace"))
        sys.exit(1)

    except urllib.error.URLError as error:

        print(f"\nConnection error: {error.reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()

