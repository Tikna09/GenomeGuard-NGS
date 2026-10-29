"""SHA-256 file-integrity helpers for the local research prototype."""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of a file, reading it in chunks."""
    target = Path(path)
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hashes_match(expected: str, actual: str) -> bool:
    """Compare hex digests without ordinary early-exit string comparison."""
    if len(expected) != 64 or len(actual) != 64:
        return False
    try:
        bytes.fromhex(expected)
        bytes.fromhex(actual)
    except ValueError:
        return False
    return hmac.compare_digest(expected.lower(), actual.lower())


def verify_file(path: str | Path, expected_sha256: str) -> bool:
    """Return True if the file matches a previously trusted SHA-256 digest."""
    try:
        actual = sha256_file(path)
    except OSError:
        return False
    return hashes_match(expected_sha256, actual)
