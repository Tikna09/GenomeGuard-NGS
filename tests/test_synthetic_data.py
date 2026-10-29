from pathlib import Path
import pytest

from src.synthetic_data import DNA_ALPHABET, generate_sequence, write_synthetic_payload


def test_sequence_is_reproducible():
    assert generate_sequence(100, seed=42) == generate_sequence(100, seed=42)


def test_sequence_uses_only_dna_alphabet():
    assert set(generate_sequence(1000, seed=4)) <= set(DNA_ALPHABET)


def test_invalid_length_rejected():
    with pytest.raises(ValueError):
        generate_sequence(0)


def test_write_payload_marks_it_synthetic(tmp_path: Path):
    target = write_synthetic_payload(tmp_path / "sample.txt", length=20, seed=1)
    text = target.read_text(encoding="utf-8")
    assert "DATASET_TYPE=SYNTHETIC_TEST_ONLY" in text
    assert "SEQUENCE_LENGTH=20" in text
