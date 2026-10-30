
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE = Path(__file__).resolve().parent

HOST = "192.168.250.133"
PORT = 8443

CERT_PATH = BASE / "certs" / "server-cert.pem"
payload = b"TEST"

# Deliberately malformed metadata: missing required fields.
metadata_bytes = b'{"version":1}'

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
        print("Response:", response.read().decode())

except urllib.error.HTTPError as error:
    print("HTTP status:", error.code)
    print("Server response:", error.read().decode())
