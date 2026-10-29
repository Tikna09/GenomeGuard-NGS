
class SequenceGuard:
    """Enforce strictly increasing sequence numbers per message stream."""

    def __init__(self):
        self._last_sequence = {}

    def accept(self, stream_id: str, sequence_number: int) -> bool:
        if not isinstance(stream_id, str) or not stream_id.strip():
            return False

        if (
            not isinstance(sequence_number, int)
            or isinstance(sequence_number, bool)
            or sequence_number < 0
        ):
            return False

        last = self._last_sequence.get(stream_id)

        if last is not None and sequence_number <= last:
            return False

        self._last_sequence[stream_id] = sequence_number
        return True
