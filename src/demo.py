"""Day 1 demo: verify an original synthetic payload and detect a local change."""
from __future__ import annotations

import shutil
from pathlib import Path

from .audit_log import append_event
from .synthetic_data import write_synthetic_payload
from .verification import create_baseline, check_against_baseline

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data_dir = PROJECT_ROOT / "data"
    logs_dir = PROJECT_ROOT / "logs"
    original = write_synthetic_payload(data_dir / "synthetic_sample.txt", length=4096, seed=7)
    modified = data_dir / "synthetic_sample_modified.txt"
    shutil.copyfile(original, modified)

    baseline = create_baseline(original)
    good_result = check_against_baseline(original, baseline)
    append_event(logs_dir / "events.jsonl", "BASELINE_VERIFICATION", good_result)
    print("Original file:", good_result)

    # Controlled file alteration in a local test copy, not a network attack.
    with modified.open("a", encoding="utf-8") as stream:
        stream.write("CONTROLLED_TEST_MODIFICATION=1\n")
    bad_result = check_against_baseline(modified, baseline)
    # This demo uses a different filename for the copy, so verify the content
    # directly against the baseline digest to demonstrate tampering detection.
    from .integrity import verify_file
    tampered_detected = not verify_file(modified, baseline["sha256"])
    print("Modified copy status:", "INTEGRITY_MISMATCH" if tampered_detected else "UNEXPECTED_MATCH")
    append_event(logs_dir / "events.jsonl", "CONTROLLED_TAMPERING_TEST", {
        "filename": modified.name,
        "tampering_detected": tampered_detected,
        "verification_status": "INTEGRITY_MISMATCH" if tampered_detected else "UNEXPECTED_MATCH",
    })
    print("Audit log:", logs_dir / "events.jsonl")
    print("Note: SHA-256 only helps when the expected digest is trusted; it does not authenticate a sender.")


if __name__ == "__main__":
    main()
