"""Generate artificial DNA-alphabet payloads for local tests only."""
from __future__ import annotations

import random
from pathlib import Path

DNA_ALPHABET = "ACGT"


def generate_sequence(length: int = 4096, seed: int = 7) -> str:
    """Return a reproducible synthetic string made only of A/C/G/T."""
    if length < 1:
        raise ValueError("length must be at least 1")
    rng = random.Random(seed)
    return "".join(rng.choice(DNA_ALPHABET) for _ in range(length))


def write_synthetic_payload(path: str | Path, length: int = 4096, seed: int = 7) -> Path:
    """Write synthetic payload plus a clear marker; never uses real genomic data."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    sequence = generate_sequence(length=length, seed=seed)
    content = (
        "DATASET_TYPE=SYNTHETIC_TEST_ONLY\n"
        f"SEED={seed}\n"
        f"SEQUENCE_LENGTH={length}\n"
        f"SEQUENCE={sequence}\n"
    )
    target.write_text(content, encoding="utf-8")
    return target
