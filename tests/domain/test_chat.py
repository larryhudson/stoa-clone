from app.domain.events import ChatMessageAdded
from app.domain.services import SessionService
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore


class NoSuggestions:
    def suggest(self, context):
        return []


def test_joined_viewer_can_append_chat_messages_in_timestamp_order(tmp_path):
    service = SessionService(
        InMemorySessionStore(),
        FakeRuntime(tmp_path),
        prompt_suggestion_generator=NoSuggestions(),
    )
    session = service.create_session("https://github.com/example/repo.git")
    service.join_session(session.id, "user-1")

    first = service.post_chat_message(session.id, "user-1", "We need session chat.")
    second = service.post_chat_message(session.id, "user-1", "Then suggest agent prompts.")

    assert first.created_at < second.created_at
    assert [message.body for message in session.chat_messages] == [
        "We need session chat.",
        "Then suggest agent prompts.",
    ]


def test_chat_message_records_and_publishes_event(tmp_path, event_publisher):
    service = SessionService(
        InMemorySessionStore(),
        FakeRuntime(tmp_path),
        event_publisher,
        prompt_suggestion_generator=NoSuggestions(),
    )
    session = service.create_session("https://github.com/example/repo.git")
    service.join_session(session.id, "user-1")

    message = service.post_chat_message(session.id, "user-1", "Let's build this.")

    assert session.events[-1] == {
        "type": "chat_message_added",
        "session_id": session.id,
        "message_id": message.id,
        "author_id": "user-1",
        "body": "Let's build this.",
        "created_at": message.created_at,
    }
    assert event_publisher.published[-1] == ChatMessageAdded(
        session.id,
        message.id,
        "user-1",
        "Let's build this.",
        message.created_at,
    )


def test_non_viewer_cannot_post_chat_message(tmp_path):
    service = SessionService(
        InMemorySessionStore(),
        FakeRuntime(tmp_path),
        prompt_suggestion_generator=NoSuggestions(),
    )
    session = service.create_session("https://github.com/example/repo.git")

    try:
        service.post_chat_message(session.id, "user-1", "hello")
    except PermissionError as exc:
        assert str(exc) == "only joined viewers can post chat messages"
    else:
        raise AssertionError("expected non-viewer chat to be rejected")
