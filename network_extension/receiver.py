
import hashlib
import hmac
import json
import os
import re
import sqlite3
import ssl
import time
import uuid

from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Network configuration
HOST = "192.168.250.133"
PORT = 8443

# Project paths
BASE = Path(__file__).resolve().parent
KEY_PATH = BASE / "secrets" / "hmac.key"
CERT_PATH = BASE / "certs" / "server-cert.pem"
PRIVATE_KEY_PATH = BASE / "certs" / "server-key.pem"

RECEIVED = BASE / "received"
DB_PATH = BASE / "receiver.db"

# Security limits
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_METADATA_SIZE = 16 * 1024
CHUNK_SIZE = 64 * 1024
PROTOCOL_VERSION = 1

RECEIVED.mkdir(exist_ok=True)


def load_key():
    key = KEY_PATH.read_bytes()

    if len(key) != 32:
        raise RuntimeError("HMAC key must be exactly 32 bytes")

    return key


def initialize_database():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                sender TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                digest TEXT NOT NULL,
                filename TEXT NOT NULL DEFAULT '',
                received_at REAL NOT NULL,
                PRIMARY KEY (sender, sequence)
            )
        """)

        columns = {
            row[1] for row in db.execute(
                "PRAGMA table_info(transfers)"
            )
        }

        if "filename" not in columns:
            db.execute("""
                ALTER TABLE transfers
                ADD COLUMN filename TEXT NOT NULL DEFAULT ''
            """)


def read_exact(stream, length):
    """Read exactly the requested number of bytes."""

    chunks = []
    remaining = length

    while remaining:
        chunk = stream.read(min(CHUNK_SIZE, remaining))

        if not chunk:
            raise ValueError("Incomplete request body")

        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def canonical_metadata(sender, sequence, digest, filename, file_size):
    fields = {
        "version": PROTOCOL_VERSION,
        "sender": sender,
        "sequence": sequence,
        "sha256": digest,
        "filename": filename,
        "file_size": file_size
    }

    return json.dumps(
        fields,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")


class Receiver(BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def respond(self, status, message):
        body = json.dumps({
            "status": message
        }).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()

        self.wfile.write(body)
        self.close_connection = True

    def do_POST(self):

        temporary = None

        if self.path != "/transfer":
            self.respond(404, "not_found")
            return

        try:

            # Reject unsupported HTTP transfer encoding
            if self.headers.get("Transfer-Encoding") is not None:
                self.respond(400, "transfer_encoding_not_supported")
                return

            metadata_length = int(
                self.headers.get("X-Metadata-Length", "0")
            )

            file_length = int(
                self.headers.get("X-File-Length", "0")
            )

            content_length = int(
                self.headers.get("Content-Length", "0")
            )

            if not (1 <= metadata_length <= MAX_METADATA_SIZE):
                self.respond(400, "invalid_metadata_length")
                return

            if not (1 <= file_length <= MAX_FILE_SIZE):
                self.respond(413, "invalid_file_size")
                return

            if content_length != metadata_length + file_length:
                self.respond(400, "content_length_mismatch")
                return

            # Read metadata
            metadata_raw = read_exact(
                self.rfile,
                metadata_length
            )

            metadata = json.loads(metadata_raw)

            required_fields = {
                "version",
                "sender",
                "sequence",
                "sha256",
                "filename",
                "file_size",
                "hmac"
            }

            if (
                not isinstance(metadata, dict)
                or set(metadata) != required_fields
            ):
                self.respond(400, "invalid_metadata_fields")
                return

            sender = metadata["sender"]
            sequence = metadata["sequence"]
            expected_digest = metadata["sha256"]
            filename = metadata["filename"]
            received_mac = metadata["hmac"]

            # Protocol validation
            if type(metadata["version"]) is not int or metadata["version"] != PROTOCOL_VERSION:
                self.respond(400, "unsupported_version")
                return

            if not isinstance(sender, str) or not re.fullmatch(
                r"[A-Za-z0-9_-]{1,32}", sender
            ):
                self.respond(400, "invalid_sender")
                return

            if type(sequence) is not int or sequence < 1:
                self.respond(400, "invalid_sequence")
                return

            if type(metadata["file_size"]) is not int:
                self.respond(400, "invalid_file_size")
                return

            if metadata["file_size"] != file_length:
                self.respond(400, "file_size_mismatch")
                return

            if not isinstance(filename, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", filename
            ):
                self.respond(400, "invalid_filename")
                return

            if filename in {".", ".."}:
                self.respond(400, "invalid_filename")
                return

            if not isinstance(expected_digest, str) or not re.fullmatch(
                r"[0-9a-f]{64}", expected_digest
            ):
                self.respond(400, "invalid_digest")
                return

            if not isinstance(received_mac, str) or not re.fullmatch(
                r"[0-9a-f]{64}", received_mac
            ):
                self.respond(400, "invalid_hmac")
                return

            # Verify sender authentication
            signed_bytes = canonical_metadata(
                sender,
                sequence,
                expected_digest,
                filename,
                file_length
            )

            expected_mac = hmac.new(
                load_key(),
                signed_bytes,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(
                expected_mac,
                received_mac
            ):
                self.respond(401, "authentication_failed")
                return

            # Stream the file to a temporary location
            actual_hash = hashlib.sha256()
            temporary = RECEIVED / (
                "." + uuid.uuid4().hex + ".part"
            )

            remaining = file_length

            with open(temporary, "xb") as output:

                while remaining:

                    chunk = self.rfile.read(
                        min(CHUNK_SIZE, remaining)
                    )

                    if not chunk:
                        raise ValueError("Incomplete file payload")

                    output.write(chunk)
                    actual_hash.update(chunk)

                    remaining -= len(chunk)

                output.flush()
                os.fsync(output.fileno())

            # Verify file integrity
            actual_digest = actual_hash.hexdigest()

            if not hmac.compare_digest(
                actual_digest,
                expected_digest
            ):
                self.respond(400, "integrity_failed")
                return

            destination = RECEIVED / (
                f"{sender}_{sequence}_{filename}"
            )

            # Save file and replay record together
            with sqlite3.connect(DB_PATH, timeout=10) as db:

                db.execute("BEGIN IMMEDIATE")

                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO transfers
                    (sender, sequence, digest, filename, received_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sender,
                        sequence,
                        actual_digest,
                        filename,
                        time.time()
                    )
                )

                if cursor.rowcount != 1:
                    db.rollback()
                    self.respond(409, "replay_or_duplicate")
                    return

                os.replace(temporary, destination)
                temporary = None

                db.commit()

            self.respond(200, "accepted")

        except (
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError
        ):
            self.respond(400, "invalid_request")

        except sqlite3.Error:
            self.log_error("Database operation failed")
            self.respond(500, "database_error")

        except Exception:
            self.log_error("Transfer processing failed")
            self.respond(500, "internal_error")

        finally:

            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def log_message(self, format, *args):
        print(
            f"[{self.log_date_time_string()}] "
            f"{self.client_address[0]} - {format % args}"
        )


def main():

    load_key()
    initialize_database()

    # TLS 1.3 configuration
    context = ssl.SSLContext(
        ssl.PROTOCOL_TLS_SERVER
    )

    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    context.load_cert_chain(
        str(CERT_PATH),
        str(PRIVATE_KEY_PATH)
    )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Receiver
    )

    server.daemon_threads = True

    server.socket = context.wrap_socket(
        server.socket,
        server_side=True
    )

    print(
        f"GenomeGuard-NGS receiver listening on {HOST}:{PORT}"
    )

    print("TLS 1.3 enabled. Press Ctrl+C to stop.")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nReceiver stopped.")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()
