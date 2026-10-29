
import pytest

from src.message_authentication import (
    create_message_tag,
    verify_message_tag,
)


KEY = b"test-secret-key"
STREAM_ID = "stream-001"
MESSAGE_ID = "message-001"
SEQUENCE = 1
PAYLOAD = b"ACGT"


def test_valid_message_tag_verifies():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD, tag
    ) is True


def test_modified_payload_is_rejected():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, b"TGCA", tag
    ) is False


def test_modified_message_id_is_rejected():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, "message-002", SEQUENCE, PAYLOAD, tag
    ) is False


def test_modified_sequence_is_rejected():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE + 1, PAYLOAD, tag
    ) is False


def test_modified_stream_id_is_rejected():
    tag = create_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD
    )

    assert verify_message_tag(
        KEY, "stream-002", MESSAGE_ID, SEQUENCE, PAYLOAD, tag
    ) is False


def test_malformed_tag_is_rejected():
    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD, "not-a-valid-tag"
    ) is False


def test_empty_stream_id_is_rejected_when_creating_tag():
    with pytest.raises(ValueError, match="stream_id"):
        create_message_tag(
            KEY, "", MESSAGE_ID, SEQUENCE, PAYLOAD
        )


def test_negative_sequence_is_rejected_when_creating_tag():
    with pytest.raises(ValueError, match="sequence_number"):
        create_message_tag(
            KEY, STREAM_ID, MESSAGE_ID, -1, PAYLOAD
        )


def test_non_bytes_payload_is_rejected_when_creating_tag():
    with pytest.raises(TypeError, match="payload"):
        create_message_tag(
            KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, "ACGT"
        )


def test_stream_id_with_invalid_unicode_is_rejected():
    with pytest.raises(ValueError, match="valid UTF-8 text"):
        create_message_tag(
            KEY, "\ud800", MESSAGE_ID, SEQUENCE, PAYLOAD
        )


def test_message_id_with_invalid_unicode_is_rejected():
    with pytest.raises(ValueError, match="valid UTF-8 text"):
        create_message_tag(
            KEY, STREAM_ID, "\ud800", SEQUENCE, PAYLOAD
        )
