
import hashlib
import json
from pathlib import Path

from src.authentication import create_hmac, verify_hmac
from src.replay_protection import ReplayGuard


class SecurePipeline:
    """Local defensive simulation for synthetic NGS-like messages."""

    def __init__(self):
        self.replay_guard = ReplayGuard()

    def process_message(
        self,
        message_id: str,
        payload: bytes,
        key: bytes,
        tag: str,
    ) -> dict:
        # Authenticate before accepting the message ID.
        if not verify_hmac(key, payload, tag):
            return {
                "message_id": message_id,
                "status": "AUTHENTICATION_FAILED",
                "accepted": False,
            }

        # Reject a message ID that has already been accepted.
        if not self.replay_guard.accept(message_id):
            return {
                "message_id": message_id,
                "status": "REPLAY_REJECTED",
                "accepted": False,
            }

        return {
            "message_id": message_id,
            "status": "ACCEPTED",
            "accepted": True,
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
        }


def write_audit_event(log_path: str, event: dict) -> None:
    """Append one JSON event to a local audit log."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")


if __name__ == "__main__":
    test_key = b"local-test-key-only"
    payload = b"ACGTACGTACGT"
    tag = create_hmac(test_key, payload)

    pipeline = SecurePipeline()
    result = pipeline.process_message(
        "message-001", payload, test_key, tag
    )

    print(result)
    write_audit_event("logs/pipeline_events.jsonl", result)
