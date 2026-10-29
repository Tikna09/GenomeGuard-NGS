
from src.message_authentication import create_message_tag
from src.persistent_freshness_pipeline import PersistentFreshnessPipeline


KEY = b"local-test-key-only"
STREAM_ID = "stream-1"
PAYLOAD = b"ACGTACGT"


def make_tag(message_id, sequence):
    return create_message_tag(
        KEY, STREAM_ID, message_id, sequence, PAYLOAD
    )


def test_valid_message_is_accepted(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "state.db")
    )
    tag = make_tag("msg-1", 1)

    result = pipeline.process(
        KEY, STREAM_ID, "msg-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "ACCEPTED"
    assert result["accepted"] is True


def test_replay_is_rejected_after_reopening(tmp_path):
    database = str(tmp_path / "state.db")
    first = PersistentFreshnessPipeline(database)

    tag = make_tag("msg-1", 1)
    assert first.process(
        KEY, STREAM_ID, "msg-1", 1, PAYLOAD, tag
    )["accepted"] is True

    reopened = PersistentFreshnessPipeline(database)
    result = reopened.process(
        KEY, STREAM_ID, "msg-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "STALE_OR_REPLAYED"
    assert result["accepted"] is False


def test_invalid_authentication_does_not_update_state(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "state.db")
    )

    invalid = pipeline.process(
        KEY, STREAM_ID, "bad-message", 10, PAYLOAD, "0" * 64
    )

    valid_tag = make_tag("good-message", 1)
    valid = pipeline.process(
        KEY, STREAM_ID, "good-message", 1, PAYLOAD, valid_tag
    )

    assert invalid["status"] == "AUTHENTICATION_FAILED"
    assert valid["status"] == "ACCEPTED"


def test_older_sequence_is_rejected(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "state.db")
    )

    tag5 = make_tag("msg-5", 5)
    tag4 = make_tag("msg-4", 4)

    pipeline.process(
        KEY, STREAM_ID, "msg-5", 5, PAYLOAD, tag5
    )
    result = pipeline.process(
        KEY, STREAM_ID, "msg-4", 4, PAYLOAD, tag4
    )

    assert result["status"] == "STALE_OR_REPLAYED"


def test_message_cannot_be_moved_to_another_stream(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "state.db")
    )
    tag = make_tag("msg-1", 1)

    result = pipeline.process(
        KEY, "different-stream", "msg-1", 1, PAYLOAD, tag
    )

    assert result["status"] == "AUTHENTICATION_FAILED"
    assert result["accepted"] is False

def test_wrong_key_does_not_consume_sequence(tmp_path):
    pipeline = PersistentFreshnessPipeline(
        str(tmp_path / "wrong-key.db")
    )

    wrong_key = b"another-test-key"
    invalid_tag = create_message_tag(
        wrong_key, STREAM_ID, "msg-1", 5, PAYLOAD
    )

    rejected = pipeline.process(
        KEY, STREAM_ID, "msg-1", 5, PAYLOAD, invalid_tag
    )

    assert rejected["status"] == "AUTHENTICATION_FAILED"
    assert rejected["accepted"] is False

    valid_tag = make_tag("msg-2", 1)
    accepted = pipeline.process(
        KEY, STREAM_ID, "msg-2", 1, PAYLOAD, valid_tag
    )

    assert accepted["status"] == "ACCEPTED"
    assert accepted["accepted"] is True
