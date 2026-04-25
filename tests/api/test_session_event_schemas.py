from pydantic import TypeAdapter, ValidationError

from app.api.event_schemas import SessionEvent
from app.domain.events import (
    AgentAborted,
    AgentPromptSubmitted,
    AgentSteered,
    ControlClaimed,
    ControlReleased,
    FileEdited,
    NoteAdded,
    SessionFailed,
    SessionStarted,
    ViewerJoined,
    ViewerLeft,
    serialize_event,
)


def test_session_event_schema_accepts_domain_and_runtime_events() -> None:
    adapter = TypeAdapter(SessionEvent)

    assert (
        adapter.validate_python(
            {"type": "control_claimed", "session_id": "session-1", "user_id": "user-1"}
        ).type
        == "control_claimed"
    )
    assert (
        adapter.validate_python(
            {"type": "agent_text_delta", "session_id": "session-1", "delta": "Hello"}
        ).type
        == "agent_text_delta"
    )


def test_domain_events_serialize_to_session_event_schema() -> None:
    adapter = TypeAdapter(SessionEvent)
    events = [
        FileEdited("session-1", "README.md", "user-1", "content"),
        NoteAdded("session-1", "user-1", "note", 1),
        ControlClaimed("session-1", "user-1"),
        ControlReleased("session-1", "user-1"),
        ViewerJoined("session-1", "user-1"),
        ViewerLeft("session-1", "user-1"),
        SessionFailed("session-1", "clone failed"),
        SessionStarted("session-1", "/tmp/session-1", "agent-session-1"),
        AgentPromptSubmitted("session-1", "user-1", "hello"),
        AgentSteered("session-1", "user-1", "continue"),
        AgentAborted("session-1", "user-1"),
    ]

    for event in events:
        adapter.validate_python(serialize_event(event))


def test_session_event_schema_rejects_unknown_event_types() -> None:
    adapter = TypeAdapter(SessionEvent)

    try:
        adapter.validate_python({"type": "mystery_event", "session_id": "session-1"})
    except ValidationError as exc:
        assert "mystery_event" in str(exc)
    else:
        raise AssertionError("expected unknown event type to fail validation")


def test_session_event_json_schema_is_discriminated_by_type() -> None:
    schema = TypeAdapter(SessionEvent).json_schema()

    assert schema["discriminator"]["propertyName"] == "type"
    assert "agent_text_delta" in schema["discriminator"]["mapping"]
