
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

def test_malformed_tag_is_rejected():
    assert verify_message_tag(
        KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, PAYLOAD, "not-a-valid-tag"
    ) is False


def test_empty_stream_id_is_rejected_when_creating_tag():
    import pytest

    with pytest.raises(ValueError):
        create_message_tag(
            KEY, "", MESSAGE_ID, SEQUENCE, PAYLOAD
        )


def test_negative_sequence_is_rejected_when_creating_tag():
    import pytest

    with pytest.raises(ValueError):
        create_message_tag(
            KEY, STREAM_ID, MESSAGE_ID, -1, PAYLOAD
        )


def test_non_bytes_payload_is_rejected_when_creating_tag():
    import pytest

    with pytest.raises(TypeError):
        create_message_tag(
            KEY, STREAM_ID, MESSAGE_ID, SEQUENCE, "ACGT"
        )


def test_stream_id_with_invalid_unicode_is_rejected():
    import pytest

    with pytest.raises(UnicodeEncodeError):
        create_message_tag(
            KEY, "\ud800", MESSAGE_ID, SEQUENCE, PAYLOAD
        )


def test_message_id_with_invalid_unicode_is_rejected():
    import pytest

    with pytest.raises(UnicodeEncodeError):
        create_message_tag(
            KEY, STREAM_ID, "\ud800", SEQUENCE, PAYLOAD
        )
