
from src.message_authentication import verify_message_tag
from src.sequence_guard import SequenceGuard


class FreshnessPipeline:
    """Authenticate messages before checking sequence freshness."""

    def __init__(self):
        self.sequence_guard = SequenceGuard()

    def process(
        self,
        key: bytes,
        stream_id: str,
        message_id: str,
        sequence_number: int,
        payload: bytes,
        tag: str,
    ) -> dict:
        if not verify_message_tag(
            key,
            stream_id,
            message_id,
            sequence_number,
            payload,
            tag,
        ):
            return {
                "status": "AUTHENTICATION_FAILED",
                "accepted": False,
            }

        if not self.sequence_guard.accept(stream_id, sequence_number):
            return {
                "status": "STALE_OR_REPLAYED",
                "accepted": False,
            }

        return {
            "status": "ACCEPTED",
            "accepted": True,
            "message_id": message_id,
            "sequence_number": sequence_number,
        }
