
from src.message_authentication import (
    create_message_tag,
    verify_message_tag,
)


KEY = b"local-test-key-only"
STREAM_ID = "ngs-stream-001"
MESSAGE_ID = "ngs-message-001"
SEQUENCE = 1
PAYLOAD = b"ACGTACGTACGT"


def test_valid_message_passes():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD, tag
    ) is True


def test_modified_payload_fails():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE,
        b"TCGTACGTACGT", tag
    ) is False


def test_modified_message_id_fails():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, "ngs-message-002", SEQUENCE, PAYLOAD, tag
    ) is False


def test_modified_sequence_number_fails():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE + 1, PAYLOAD, tag
    ) is False


def test_modified_stream_id_fails():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, "ngs-stream-002", MESSAGE_ID, SEQUENCE, PAYLOAD, tag
    ) is False
