
from src.freshness_pipeline import FreshnessPipeline
from src.message_authentication import create_message_tag


KEY = b"local-test-key-only"
STREAM = "ngs-stream-1"
PAYLOAD = b"ACGTACGT"


def make_tag(message_id, sequence, payload=PAYLOAD):
    return create_message_tag(KEY, message_id, sequence, payload)


def test_valid_message_is_accepted():
    pipeline = FreshnessPipeline()
    tag = make_tag("msg-1", 1)

    result = pipeline.process(
        KEY, STREAM, "msg-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "ACCEPTED"


def test_tampered_payload_is_rejected():
    pipeline = FreshnessPipeline()
    tag = make_tag("msg-1", 1)

    result = pipeline.process(
        KEY, STREAM, "msg-1", 1, b"TCGTACGT", tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"


def test_duplicate_sequence_is_rejected():
    pipeline = FreshnessPipeline()
    tag1 = make_tag("msg-1", 1)
    tag2 = make_tag("msg-2", 1)

    pipeline.process(KEY, STREAM, "msg-1", 1, PAYLOAD, tag1)
    result = pipeline.process(
        KEY, STREAM, "msg-2", 1, PAYLOAD, tag2
    )

    assert result["status"] == "STALE_OR_REPLAYED"


def test_older_sequence_is_rejected():
    pipeline = FreshnessPipeline()
    tag1 = make_tag("msg-1", 3)
    tag2 = make_tag("msg-2", 2)

    pipeline.process(KEY, STREAM, "msg-1", 3, PAYLOAD, tag1)
    result = pipeline.process(
        KEY, STREAM, "msg-2", 2, PAYLOAD, tag2
    )

    assert result["status"] == "STALE_OR_REPLAYED"


def test_invalid_message_does_not_advance_sequence():
    pipeline = FreshnessPipeline()

    invalid = pipeline.process(
        KEY, STREAM, "msg-1", 10, PAYLOAD, "0" * 64
    )

    valid_tag = make_tag("msg-2", 1)
    valid = pipeline.process(
        KEY, STREAM, "msg-2", 1, PAYLOAD, valid_tag
    )

    assert invalid["status"] == "AUTHENTICATION_FAILED"
    assert valid["status"] == "ACCEPTED"
