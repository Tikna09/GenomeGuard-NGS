
from src.message_authentication import create_message_tag
from src.freshness_pipeline import FreshnessPipeline


KEY = b"local-test-key-only"
STREAM_ID = "stream-1"
PAYLOAD = b"ACGTACGT"


def make_tag(message_id, sequence, payload=PAYLOAD):
    return create_message_tag(
        KEY, STREAM_ID, message_id, sequence, payload
    )


def test_valid_message_is_accepted():
    pipeline = FreshnessPipeline()
    tag = make_tag("message-1", 1)

    result = pipeline.process(
        KEY, STREAM_ID, "message-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "ACCEPTED"


def test_tampered_payload_is_rejected():
    pipeline = FreshnessPipeline()
    tag = make_tag("message-1", 1)

    result = pipeline.process(
        KEY, STREAM_ID, "message-1", 1, b"TCGTACGT", tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"
    assert result["accepted"] is False


def test_duplicate_sequence_is_rejected():
    pipeline = FreshnessPipeline()
    tag = make_tag("message-1", 1)

    first = pipeline.process(
        KEY, STREAM_ID, "message-1", 1, PAYLOAD, tag
    )
    second = pipeline.process(
        KEY, STREAM_ID, "message-1", 1, PAYLOAD, tag
    )

    assert first["accepted"] is True
    assert second["status"] == "STALE_OR_REPLAYED"


def test_invalid_authentication_is_rejected():
    pipeline = FreshnessPipeline()
    tag = make_tag("message-1", 1)

    result = pipeline.process(
        KEY, STREAM_ID, "message-1", 1, b"MODIFIED", tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"


def test_message_cannot_be_moved_to_another_stream():
    pipeline = FreshnessPipeline()
    tag = make_tag("message-1", 1)

    result = pipeline.process(
        KEY, "different-stream", "message-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"


def test_older_sequence_is_rejected():
    pipeline = FreshnessPipeline()

    tag3 = make_tag("message-3", 3)
    first = pipeline.process(
        KEY, STREAM_ID, "message-3", 3, PAYLOAD, tag3
    )
    assert first["accepted"] is True

    tag2 = make_tag("message-2", 2)
    result = pipeline.process(
        KEY, STREAM_ID, "message-2", 2, PAYLOAD, tag2
    )

    assert result["status"] == "STALE_OR_REPLAYED"
    assert result["accepted"] is False
