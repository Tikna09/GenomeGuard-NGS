
import hashlib
import hmac
import struct


def _message_bytes(
    stream_id: str,
    message_id: str,
    sequence_number: int,
    payload: bytes,
) -> bytes:
    """Encode all message fields unambiguously before authentication."""
    for name, value in (
        ("stream_id", stream_id),
        ("message_id", message_id),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")

    if (
        not isinstance(sequence_number, int)
        or isinstance(sequence_number, bool)
        or not 0 <= sequence_number <= 0xFFFFFFFFFFFFFFFF
    ):
        raise ValueError(
            "sequence_number must be a valid unsigned 64-bit integer"
        )

    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")

    try:
        stream_bytes = stream_id.encode("utf-8")
        message_id_bytes = message_id.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "stream_id and message_id must contain valid UTF-8 text"
        ) from exc

    return (
        struct.pack(">I", len(stream_bytes))
        + stream_bytes
        + struct.pack(">I", len(message_id_bytes))
        + message_id_bytes
        + struct.pack(">Q", sequence_number)
        + struct.pack(">Q", len(payload))
        + payload
    )


def create_message_tag(
    key: bytes,
    stream_id: str,
    message_id: str,
    sequence_number: int,
    payload: bytes,
) -> str:
    """Authenticate the stream, message ID, sequence number, and payload."""
    if not isinstance(key, bytes) or not key:
        raise ValueError("key must be non-empty bytes")

    message = _message_bytes(
        stream_id, message_id, sequence_number, payload
    )

    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_message_tag(
    key: bytes,
    stream_id: str,
    message_id: str,
    sequence_number: int,
    payload: bytes,
    tag: str,
) -> bool:
    """Verify the authentication tag for all message fields."""
    if not isinstance(tag, str) or len(tag) != 64:
        return False

    try:
        bytes.fromhex(tag)
        expected = create_message_tag(
            key, stream_id, message_id, sequence_number, payload
        )
    except (ValueError, TypeError, struct.error, UnicodeError):
        return False
    return hmac.compare_digest(expected, tag.lower())
