
import tempfile
from pathlib import Path

from src.authentication import create_hmac
from src.message_authentication import create_message_tag
from src.secure_pipeline import SecurePipeline
from src.persistent_freshness_pipeline import PersistentFreshnessPipeline


KEY = b"local-research-key-only"
PAYLOAD = b"ACGTACGTACGT"
TAMPERED_PAYLOAD = b"ACGTACGTAAAA"


def check(name, condition):
    result = "PASS" if condition else "FAIL"
    print(f"[{result}] {name}")
    return condition


def run_baseline_tests():
    print("\n=== BASELINE PIPELINE ===")
    passed = 0
    total = 0

    def test(name, condition):
        nonlocal passed, total
        total += 1
        passed += check(name, condition)

    tag = create_hmac(KEY, PAYLOAD)

    pipeline = SecurePipeline()
    result = pipeline.process_message(
        "baseline-001", PAYLOAD, KEY, tag
    )
    test("Valid message accepted", result["accepted"])

    result = pipeline.process_message(
        "baseline-002", TAMPERED_PAYLOAD, KEY, tag
    )
    test(
        "Tampered payload rejected",
        not result["accepted"]
        and result["status"] == "AUTHENTICATION_FAILED",
    )

    result = pipeline.process_message(
        "baseline-003", PAYLOAD, KEY, "0" * 64
    )
    test("Invalid authentication tag rejected", not result["accepted"])

    replay_pipeline = SecurePipeline()
    replay_tag = create_hmac(KEY, PAYLOAD)
    first = replay_pipeline.process_message(
        "baseline-replay", PAYLOAD, KEY, replay_tag
    )
    second = replay_pipeline.process_message(
        "baseline-replay", PAYLOAD, KEY, replay_tag
    )
    test(
        "Duplicate message ID rejected",
        first["accepted"]
        and not second["accepted"]
        and second["status"] == "REPLAY_REJECTED",
    )

    # A new baseline instance loses its in-memory replay history.
    restarted = SecurePipeline()
    after_restart = restarted.process_message(
        "baseline-replay", PAYLOAD, KEY, replay_tag
    )
    test(
        "Replay after pipeline restart demonstrates limitation",
        after_restart["accepted"],
    )

    print(f"Baseline checks: {passed}/{total} passed")
    return passed, total


def run_persistent_tests(database_path):
    print("\n=== PERSISTENT FRESHNESS PIPELINE ===")
    passed = 0
    total = 0

    def test(name, condition):
        nonlocal passed, total
        total += 1
        passed += check(name, condition)

    def send(pipeline, message_id, sequence, payload=PAYLOAD, tag=None):
        if tag is None:
            tag = create_message_tag(
                KEY, "research-stream", message_id, sequence, payload
            )
        return pipeline.process(
            KEY,
            "research-stream",
            message_id,
            sequence,
            payload,
            tag,
        )

    pipeline = PersistentFreshnessPipeline(database_path)

    result = send(pipeline, "persistent-001", 1)
    test("Valid message accepted", result["accepted"])

    original_tag = create_message_tag(
        KEY, "research-stream", "persistent-tamper", 2, PAYLOAD
    )
    result = send(
        pipeline,
        "persistent-tamper",
        2,
        payload=TAMPERED_PAYLOAD,
        tag=original_tag,
    )
    test(
        "Tampered payload rejected",
        not result["accepted"]
        and result["status"] == "AUTHENTICATION_FAILED",
    )

    result = send(
        pipeline, "persistent-invalid-tag", 2, tag="0" * 64
    )
    test(
        "Invalid authentication tag rejected",
        not result["accepted"]
        and result["status"] == "AUTHENTICATION_FAILED",
    )

    replay_tag = create_message_tag(
        KEY, "research-stream", "persistent-replay", 2, PAYLOAD
    )
    first = send(pipeline, "persistent-replay", 2, tag=replay_tag)
    duplicate = send(pipeline, "persistent-replay", 2, tag=replay_tag)
    test(
        "Duplicate sequence rejected",
        first["accepted"]
        and not duplicate["accepted"]
        and duplicate["status"] == "STALE_OR_REPLAYED",
    )

    # Reconstruct the pipeline while reusing the same SQLite database.
    restarted = PersistentFreshnessPipeline(database_path)
    after_restart = send(
        restarted, "persistent-replay", 2, tag=replay_tag
    )
    test(
        "Replay after restart rejected",
        not after_restart["accepted"]
        and after_restart["status"] == "STALE_OR_REPLAYED",
    )

    higher = send(restarted, "persistent-003", 3)
    test("Higher sequence number accepted", higher["accepted"])

    print(f"Persistent checks: {passed}/{total} passed")
    return passed, total


def main():
    baseline_passed, baseline_total = run_baseline_tests()

    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = str(Path(temp_dir) / "comparison.sqlite3")
        persistent_passed, persistent_total = run_persistent_tests(
            database_path
        )

    print("\n=== OVERALL RESULT ===")
    print(
        f"{baseline_passed + persistent_passed}/"
        f"{baseline_total + persistent_total} checks passed"
    )


if __name__ == "__main__":
    main()
