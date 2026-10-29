
from concurrent.futures import ThreadPoolExecutor

from src.message_authentication import create_message_tag
from src.persistent_freshness_pipeline import PersistentFreshnessPipeline


KEY = b"local-test-key-only"
PAYLOAD = b"ACGTACGT"


def test_concurrent_duplicate_sequence_accepted_once(tmp_path):
    database = str(tmp_path / "concurrent.db")
    stream_id = "stream-1"

    def attempt():
        pipeline = PersistentFreshnessPipeline(database)
        tag = create_message_tag(
            KEY, stream_id, "message-1", 7, PAYLOAD
        )

        return pipeline.process(
            KEY, stream_id, "message-1", 7, PAYLOAD, tag
        )["accepted"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: attempt(), range(8)))

    assert results.count(True) == 1
    assert results.count(False) == 7


def test_independent_streams_accept_independent_sequences(tmp_path):
    database = str(tmp_path / "streams.db")
    pipeline = PersistentFreshnessPipeline(database)

    tag1 = create_message_tag(
        KEY, "stream-1", "message-1", 5, PAYLOAD
    )
    tag2 = create_message_tag(
        KEY, "stream-2", "message-2", 1, PAYLOAD
    )

    result1 = pipeline.process(
        KEY, "stream-1", "message-1", 5, PAYLOAD, tag1
    )
    result2 = pipeline.process(
        KEY, "stream-2", "message-2", 1, PAYLOAD, tag2
    )

    assert result1["accepted"] is True
    assert result2["accepted"] is True


def test_tampered_sequence_does_not_consume_sequence_number(tmp_path):
    database = str(tmp_path / "tampered-sequence.db")
    pipeline = PersistentFreshnessPipeline(database)
    stream_id = "stream-1"

    # Tag authenticates sequence 2, but the supplied sequence is changed to 9.
    tag = create_message_tag(
        KEY, stream_id, "message-1", 2, PAYLOAD
    )

    tampered = pipeline.process(
        KEY, stream_id, "message-1", 9, PAYLOAD, tag
    )

    valid_tag = create_message_tag(
        KEY, stream_id, "message-2", 1, PAYLOAD
    )
    valid = pipeline.process(
        KEY, stream_id, "message-2", 1, PAYLOAD, valid_tag
    )

    assert tampered["status"] == "AUTHENTICATION_FAILED"
    assert valid["status"] == "ACCEPTED"
