
import hashlib
import hmac
import json
import ssl
import urllib.request
import urllib.error
import secrets
from pathlib import Path

BASE = Path(__file__).resolve().parent
HOST = "192.168.250.133"
PORT = 8443
SENDER = "AutoTest"
KEY = (BASE / "secrets" / "hmac.key").read_bytes()
CERT = BASE / "certs" / "server-cert.pem"

# Fresh sequence numbers for every run
START_SEQUENCE = secrets.randbelow(800000) + 100000

context = ssl.create_default_context(cafile=str(CERT))
context.minimum_version = ssl.TLSVersion.TLSv1_3
context.maximum_version = ssl.TLSVersion.TLSv1_3


def make_mac(fields):
    signed = json.dumps(
        fields, sort_keys=True, separators=(",", ":")
    ).encode()

    return hmac.new(KEY, signed, hashlib.sha256).hexdigest()


def send_test(name, sequence, payload, mode="valid"):
    digest = hashlib.sha256(payload).hexdigest()

    fields = {
        "version": 1,
        "sender": SENDER,
        "sequence": sequence,
        "sha256": digest,
        "filename": "automated_test.fastq",
        "file_size": len(payload)
    }

    metadata = dict(fields)

    if mode == "invalid_metadata":
        metadata = {"version": 1}
        payload_to_send = payload

    elif mode == "tampered_payload":
        payload_to_send = payload + b"TAMPERED"

        # Update file size but preserve original SHA-256 digest.
        fields["file_size"] = len(payload_to_send)

        metadata = dict(fields)
        metadata["hmac"] = make_mac(fields)

    else:
        payload_to_send = payload
        metadata["hmac"] = make_mac(fields)

        if mode == "invalid_hmac":
            metadata["hmac"] = "0" * 64

    metadata_bytes = json.dumps(
        metadata, sort_keys=True, separators=(",", ":")
    ).encode()

    body = metadata_bytes + payload_to_send

    request = urllib.request.Request(
        f"https://{HOST}:{PORT}/transfer",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/octet-stream",
            "X-Metadata-Length": str(len(metadata_bytes)),
            "X-File-Length": str(len(payload_to_send)),
            "Content-Length": str(len(body))
        }
    )

    try:
        with urllib.request.urlopen(
            request, context=context, timeout=30
        ) as response:
            status = response.status
            result = response.read().decode()

    except urllib.error.HTTPError as error:
        status = error.code
        result = error.read().decode()

    print(f"{name}: HTTP {status} | {result}")
    return status


payload = b"@READ001\nATGCGTACGT\n+\nIIIIIIIIII\n"

print("\nGENOMEGUARD-NGS AUTOMATED SECURITY TESTS\n")

send_test("Valid transfer", START_SEQUENCE, payload)
send_test("Invalid HMAC", START_SEQUENCE + 1, payload, "invalid_hmac")
send_test("Payload tampering", START_SEQUENCE + 2, payload, "tampered_payload")
send_test("Invalid metadata", START_SEQUENCE + 3, payload, "invalid_metadata")

send_test("First replay test transfer", START_SEQUENCE + 4, payload)
send_test("Duplicate sequence replay", START_SEQUENCE + 4, payload)

print("\nTEST RUN COMPLETED")

