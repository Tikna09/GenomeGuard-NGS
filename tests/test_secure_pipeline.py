
from src.authentication import create_hmac
from src.secure_pipeline import SecurePipeline


TEST_KEY = b"local-test-key-only"
PAYLOAD = b"ACGTACGTACGT"


def test_valid_message_is_accepted():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)

    result = pipeline.process_message(
        "message-001", PAYLOAD, TEST_KEY, tag
    )

    assert result["status"] == "ACCEPTED"
    assert result["accepted"] is True


def test_tampered_payload_is_rejected():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)

    result = pipeline.process_message(
        "message-002", b"ACGTTCGTACGT", TEST_KEY, tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"
    assert result["accepted"] is False


def test_wrong_key_is_rejected():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)

    result = pipeline.process_message(
        "message-003", PAYLOAD, b"wrong-test-key", tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"
    assert result["accepted"] is False


def test_replayed_message_is_rejected():
    pipeline = SecurePipeline()
    tag = create_hmac(TEST_KEY, PAYLOAD)

    first = pipeline.process_message(
        "message-004", PAYLOAD, TEST_KEY, tag
    )
    second = pipeline.process_message(
        "message-004", PAYLOAD, TEST_KEY, tag
    )

    assert first["status"] == "ACCEPTED"
    assert second["status"] == "REPLAY_REJECTED"
    assert second["accepted"] is False


def test_invalid_message_does_not_consume_message_id():
    pipeline = SecurePipeline()
    invalid_tag = "0" * 64
    valid_tag = create_hmac(TEST_KEY, PAYLOAD)

    invalid = pipeline.process_message(
        "message-005", PAYLOAD, TEST_KEY, invalid_tag
    )
    valid = pipeline.process_message(
        "message-005", PAYLOAD, TEST_KEY, valid_tag
    )

    assert invalid["status"] == "AUTHENTICATION_FAILED"
    assert valid["status"] == "ACCEPTED"
