
from src.authentication import create_hmac, verify_hmac


def test_valid_message_is_authenticated():
    key = b"local-test-key-only"
    message = b"ACGTACGTACGT"

    tag = create_hmac(key, message)

    assert verify_hmac(key, message, tag) is True


def test_modified_message_is_rejected():
    key = b"local-test-key-only"
    message = b"ACGTACGTACGT"

    tag = create_hmac(key, message)

    modified_message = b"ACGTTCGTACGT"

    assert verify_hmac(key, modified_message, tag) is False


def test_wrong_key_is_rejected():
    message = b"ACGTACGTACGT"

    tag = create_hmac(b"correct-test-key", message)

    assert verify_hmac(b"wrong-test-key", message, tag) is False


def test_invalid_tag_is_rejected():
    assert verify_hmac(
        b"local-test-key-only",
        b"ACGTACGTACGT",
        "invalid-tag"
    ) is False
