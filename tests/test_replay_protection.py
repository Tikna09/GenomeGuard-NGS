
from src.replay_protection import ReplayGuard


def test_new_message_is_accepted():
    guard = ReplayGuard()
    assert guard.accept("message-001") is True


def test_replayed_message_is_rejected():
    guard = ReplayGuard()

    assert guard.accept("message-001") is True
    assert guard.accept("message-001") is False


def test_different_messages_are_accepted():
    guard = ReplayGuard()

    assert guard.accept("message-001") is True
    assert guard.accept("message-002") is True


def test_empty_message_id_is_rejected():
    guard = ReplayGuard()

    assert guard.accept("") is False
    assert guard.accept("   ") is False
