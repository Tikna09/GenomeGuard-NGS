
from src.sequence_guard import SequenceGuard


def test_first_sequence_is_accepted():
    guard = SequenceGuard()
    assert guard.accept("stream-1", 1) is True


def test_increasing_sequence_is_accepted():
    guard = SequenceGuard()
    assert guard.accept("stream-1", 1) is True
    assert guard.accept("stream-1", 2) is True


def test_duplicate_sequence_is_rejected():
    guard = SequenceGuard()
    assert guard.accept("stream-1", 4) is True
    assert guard.accept("stream-1", 4) is False


def test_older_sequence_is_rejected():
    guard = SequenceGuard()
    assert guard.accept("stream-1", 5) is True
    assert guard.accept("stream-1", 3) is False


def test_streams_are_tracked_separately():
    guard = SequenceGuard()
    assert guard.accept("stream-1", 5) is True
    assert guard.accept("stream-2", 1) is True


def test_invalid_sequence_is_rejected():
    guard = SequenceGuard()
    assert guard.accept("stream-1", -1) is False
    assert guard.accept("stream-1", True) is False
    assert guard.accept("", 1) is False
