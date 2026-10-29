from pathlib import Path

from src.integrity import sha256_file, hashes_match, verify_file
from src.verification import create_baseline, check_against_baseline


def test_hash_is_repeatable(tmp_path: Path):
    target = tmp_path / "sample.txt"
    target.write_text("synthetic", encoding="utf-8")
    assert sha256_file(target) == sha256_file(target)


def test_verify_passes_for_unchanged_file(tmp_path: Path):
    target = tmp_path / "sample.txt"
    target.write_text("ACGT", encoding="utf-8")
    digest = sha256_file(target)
    assert verify_file(target, digest)


def test_verify_fails_after_modification(tmp_path: Path):
    target = tmp_path / "sample.txt"
    target.write_text("ACGT", encoding="utf-8")
    digest = sha256_file(target)
    target.write_text("ACGA", encoding="utf-8")
    assert not verify_file(target, digest)


def test_hashes_match_rejects_bad_digest():
    assert not hashes_match("bad", "bad")


def test_baseline_verification(tmp_path: Path):
    target = tmp_path / "sample.txt"
    target.write_text("synthetic", encoding="utf-8")
    baseline = create_baseline(target)
    assert check_against_baseline(target, baseline)["status"] == "INTEGRITY_OK"
    target.write_text("modified", encoding="utf-8")
    assert check_against_baseline(target, baseline)["status"] == "INTEGRITY_MISMATCH"
