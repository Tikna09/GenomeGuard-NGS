
import ssl
import json
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "192.168.250.133"
PORT = 8444

BASE = Path(__file__).resolve().parent
CERT = BASE / "certs" / "server-cert.pem"
KEY = BASE / "certs" / "server-key.pem"
OUTPUT = BASE / "baseline_received"

MAX_SIZE = 100 * 1024 * 1024
OUTPUT.mkdir(exist_ok=True)


class BaselineReceiver(BaseHTTPRequestHandler):

    def do_POST(self):
        start = time.perf_counter()

        if self.path != "/transfer":
            self.send_error(404)
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))

            if not 1 <= size <= MAX_SIZE:
                self.send_error(413)
                return

            remaining = size
            destination = OUTPUT / "baseline_received.bin"
            temporary = OUTPUT / "baseline_received.tmp"

            with open(temporary, "wb") as f:
                while remaining:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        raise ValueError("Incomplete transfer")
                    f.write(chunk)
                    remaining -= len(chunk)

                f.flush()

            temporary.replace(destination)

            elapsed = time.perf_counter() - start

            body = json.dumps({
                "status": "accepted",
                "received_bytes": size,
                "server_processing_seconds": elapsed
            }).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception:
            self.send_error(400, "transfer_failed")

    def log_message(self, format, *args):
        print(format % args)


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(str(CERT), str(KEY))

    server = ThreadingHTTPServer((HOST, PORT), BaselineReceiver)
    server.socket = context.wrap_socket(
        server.socket, server_side=True
    )

    print(f"TLS-only baseline receiver listening on {HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Baseline receiver stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
