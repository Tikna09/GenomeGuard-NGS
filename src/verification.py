"""Baseline creation and verification."""
from __future__ import annotations

from pathlib import Path
from .integrity import sha256_file, verify_file


def create_baseline(path: str | Path) -> dict[str, str]:
    """Create an in-memory baseline record. Protect the record in real systems."""
    target = Path(path)
    return {
        "filename": target.name,
        "sha256": sha256_file(target),
        "status": "BASELINE_CREATED",
    }


def check_against_baseline(path: str | Path, baseline: dict[str, str]) -> dict[str, str | bool]:
    """Verify a file against the trusted baseline record."""
    target = Path(path)
    if not target.is_file():
        return {
            "filename": target.name,
            "verified": False,
            "status": "FILE_MISSING",
        }
    expected_name = baseline.get("filename", "")
    expected_hash = baseline.get("sha256", "")
    if target.name != expected_name:
        return {
            "filename": target.name,
            "verified": False,
            "status": "FILENAME_MISMATCH",
        }
    verified = verify_file(target, expected_hash)
    return {
        "filename": target.name,
        "verified": verified,
        "status": "INTEGRITY_OK" if verified else "INTEGRITY_MISMATCH",
    }
