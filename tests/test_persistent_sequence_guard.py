
from concurrent.futures import ThreadPoolExecutor

from src.persistent_sequence_guard import PersistentSequenceGuard


def test_sequence_survives_reopening(tmp_path):
    database = str(tmp_path / "sequences.db")

    first_guard = PersistentSequenceGuard(database)
    assert first_guard.accept("stream-1", 10) is True

    reopened_guard = PersistentSequenceGuard(database)
    assert reopened_guard.accept("stream-1", 10) is False
    assert reopened_guard.accept("stream-1", 9) is False
    assert reopened_guard.accept("stream-1", 11) is True


def test_streams_are_independent(tmp_path):
    guard = PersistentSequenceGuard(str(tmp_path / "sequences.db"))

    assert guard.accept("stream-1", 10) is True
    assert guard.accept("stream-2", 1) is True


def test_invalid_inputs_are_rejected(tmp_path):
    guard = PersistentSequenceGuard(str(tmp_path / "sequences.db"))

    assert guard.accept("", 1) is False
    assert guard.accept("stream-1", -1) is False
    assert guard.accept("stream-1", True) is False


def test_concurrent_duplicate_sequence_is_accepted_once(tmp_path):
    database = str(tmp_path / "sequences.db")

    def attempt():
        return PersistentSequenceGuard(database).accept("stream-1", 5)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: attempt(), range(8)))

    assert results.count(True) == 1
    assert results.count(False) == 7
