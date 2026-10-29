
class ReplayGuard:
    """Track accepted message IDs to detect replayed messages."""

    def __init__(self):
        self._seen_message_ids = set()

    def accept(self, message_id: str) -> bool:
        """Return True for a new ID and False for a replay."""
        if not isinstance(message_id, str) or not message_id.strip():
            return False

        if message_id in self._seen_message_ids:
            return False

        self._seen_message_ids.add(message_id)
        return True
