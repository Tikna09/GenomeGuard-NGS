import hashlib
import hmac
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE = Path(__file__).resolve().parent

HOST = "192.168.250.133"
PORT = 8443

KEY_PATH = BASE / "secrets" / "hmac.key"
CERT_PATH = BASE / "certs" / "server-cert.pem"
ORIGINAL = BASE / "data" / "sample_original.fastq"
MODIFIED = BASE / "data" / "sample.fastq"

SENDER = "Kali-Sender"
SEQUENCE = 2


def main():
    key = KEY_PATH.read_bytes()

    original = ORIGINAL.read_bytes()
    modified = MODIFIED.read_bytes()

    original_hash = hashlib.sha256(original).hexdigest()
    modified_hash = hashlib.sha256(modified).hexdigest()

    # Generate valid HMAC using ORIGINAL file metadata.
    fields = {
        "version": 1,
        "sender": SENDER,
        "sequence": SEQUENCE,
        "sha256": original_hash,
        "filename": ORIGINAL.name,
        "file_size": len(modified)
    }

    signed = json.dumps(
        fields, sort_keys=True, separators=(",", ":")
    ).encode()

    mac = hmac.new(key, signed, hashlib.sha256).hexdigest()

    metadata = {**fields, "hmac": mac}

    metadata_bytes = json.dumps(
        metadata, sort_keys=True, separators=(",", ":")
    ).encode()

    # Send MODIFIED payload with ORIGINAL authenticated metadata.
    body = metadata_bytes + modified

    request = urllib.request.Request(
        f"https://{HOST}:{PORT}/transfer",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "X-Metadata-Length": str(len(metadata_bytes)),
            "X-File-Length": str(len(modified)),
            "Content-Length": str(len(body))
        }
    )

    context = ssl.create_default_context(cafile=str(CERT_PATH))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    print("GenomeGuard-NGS Tampering Test")
    print("--------------------------------")
    print("Original SHA-256:", original_hash)
    print("Modified SHA-256:", modified_hash)
    print("Sequence:", SEQUENCE)
    print("Sending modified payload with original authenticated metadata...")

    try:
        with urllib.request.urlopen(
            request, context=context, timeout=30
        ) as response:
            print("Unexpected response:", response.status)
            print(response.read().decode())

    except urllib.error.HTTPError as error:
        print("HTTP status:", error.code)
        print("Server response:", error.read().decode())

        if error.code == 400:
            print("\nTAMPERING DETECTION TEST PASSED")
        else:
            print("\nUnexpected rejection reason.")

    except urllib.error.URLError as error:
        print("Connection error:", error.reason)


if __name__ == "__main__":
    main()
