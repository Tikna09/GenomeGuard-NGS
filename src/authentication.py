
import hashlib
import hmac


def create_hmac(key: bytes, message: bytes) -> str:
    """Create an HMAC-SHA-256 authentication tag."""
    return hmac.new(
        key,
        message,
        hashlib.sha256
    ).hexdigest()


def verify_hmac(key: bytes, message: bytes, tag: str) -> bool:
    """Verify an HMAC tag safely."""
    if not isinstance(tag, str) or len(tag) != 64:
        return False

    try:
        bytes.fromhex(tag)
    except ValueError:
        return False

    expected_tag = create_hmac(key, message)

    return hmac.compare_digest(expected_tag, tag.lower())
