
from src.message_authentication import verify_message_tag
from src.persistent_sequence_guard import PersistentSequenceGuard


class PersistentFreshnessPipeline:
    """Authenticate each message before updating persistent sequence state."""

    def __init__(self, database_path: str):
        self.sequence_guard = PersistentSequenceGuard(database_path)

    def process(
        self,
        key: bytes,
        stream_id: str,
        message_id: str,
        sequence_number: int,
        payload: bytes,
        tag: str,
    ) -> dict:
        # Never update sequence state for an unauthenticated message.
        if not verify_message_tag(
            key, message_id, sequence_number, payload, tag
        ):
            return {
                "status": "AUTHENTICATION_FAILED",
                "accepted": False,
            }

        # Accept only a strictly increasing sequence for this stream.
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
