
import hashlib
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE = Path(__file__).resolve().parent

HOST = "192.168.250.133"
PORT = 8443
SENDER_ID = "Kali-Sender"
SEQUENCE = 1001

FILE_PATH = BASE / "data" / "sample.fastq"
CERT_PATH = BASE / "certs" / "server-cert.pem"

payload = FILE_PATH.read_bytes()
digest = hashlib.sha256(payload).hexdigest()

fields = {
    "version": 1,
    "sender": SENDER_ID,
    "sequence": SEQUENCE,
    "sha256": digest,
    "filename": FILE_PATH.name,
    "file_size": len(payload)
}

# Deliberately incorrect HMAC.
metadata = {
    **fields,
    "hmac": "0" * 64
}

metadata_bytes = json.dumps(
    metadata,
    sort_keys=True,
    separators=(",", ":")
).encode("utf-8")

body = metadata_bytes + payload

context = ssl.create_default_context(cafile=str(CERT_PATH))
context.minimum_version = ssl.TLSVersion.TLSv1_3
context.maximum_version = ssl.TLSVersion.TLSv1_3

request = urllib.request.Request(
    f"https://{HOST}:{PORT}/transfer",
    data=body,
    method="POST",
    headers={
        "Content-Type": "application/octet-stream",
        "X-Metadata-Length": str(len(metadata_bytes)),
        "X-File-Length": str(len(payload)),
        "Content-Length": str(len(body))
    }
)

try:
    with urllib.request.urlopen(
        request, context=context, timeout=30
    ) as response:
        print("HTTP status:", response.status)
        print(response.read().decode())

except urllib.error.HTTPError as error:
    print("HTTP status:", error.code)
    print("Server response:", error.read().decode())
