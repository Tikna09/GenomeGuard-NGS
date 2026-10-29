
from src.message_authentication import create_message_tag
from src.persistent_freshness_pipeline import PersistentFreshnessPipeline


KEY = b"local-test-key-only"
STREAM = "ngs-stream-1"
PAYLOAD = b"ACGTACGT"


def make_tag(message_id, sequence):
    return create_message_tag(KEY, message_id, sequence, PAYLOAD)


def test_valid_message_is_accepted(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "state.db")
    )
    tag = make_tag("msg-1", 1)

    result = pipeline.process(
        KEY, STREAM, "msg-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "ACCEPTED"


def test_replay_is_rejected_after_reopening(tmp_path):
    database = str(tmp_path / "state.db")
    first = PersistentFreshnessPipeline(database)

    tag1 = make_tag("msg-1", 1)
    assert first.process(
        KEY, STREAM, "msg-1", 1, PAYLOAD, tag1
    )["accepted"] is True

    reopened = PersistentFreshnessPipeline(database)
    tag2 = make_tag("msg-2", 1)

    result = reopened.process(
        KEY, STREAM, "msg-2", 1, PAYLOAD, tag2
    )

    assert result["status"] == "STALE_OR_REPLAYED"


def test_invalid_authentication_does_not_update_state(tmp_path):
    database = str(tmp_path / "state.db")
    pipeline = PersistentFreshnessPipeline(database)

    invalid = pipeline.process(
        KEY, STREAM, "bad-message", 10, PAYLOAD, "0" * 64
    )

    valid_tag = make_tag("good-message", 1)
    valid = pipeline.process(
        KEY, STREAM, "good-message", 1, PAYLOAD, valid_tag
    )

    assert invalid["status"] == "AUTHENTICATION_FAILED"
    assert valid["status"] == "ACCEPTED"


def test_older_sequence_is_rejected(tmp_path):
    database = str(tmp_path / "state.db")
    pipeline = PersistentFreshnessPipeline(database)

    tag1 = make_tag("msg-5", 5)
    tag2 = make_tag("msg-4", 4)

    pipeline.process(KEY, STREAM, "msg-5", 5, PAYLOAD, tag1)
    result = pipeline.process(
        KEY, STREAM, "msg-4", 4, PAYLOAD, tag2
    )

    assert result["status"] == "STALE_OR_REPLAYED"
