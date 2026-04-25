from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, ClassVar, cast


@dataclass
class FileEdited:
    event_type: ClassVar[str] = "file_edited"
    session_id: str
    path: str
    editor_id: str
    content: str


@dataclass
class NoteAdded:
    event_type: ClassVar[str] = "note_added"
    session_id: str
    author_id: str
    body: str
    created_at: int


@dataclass
class ChatMessageAdded:
    event_type: ClassVar[str] = "chat_message_added"
    session_id: str
    message_id: str
    author_id: str
    body: str
    created_at: int


@dataclass
class AgentPromptSuggested:
    event_type: ClassVar[str] = "agent_prompt_suggested"
    session_id: str
    suggestion_id: str
    text: str
    reason: str
    source_message_ids: list[str]
    created_at: int


@dataclass
class AgentPromptSuggestionAccepted:
    event_type: ClassVar[str] = "agent_prompt_suggestion_accepted"
    session_id: str
    suggestion_id: str
    user_id: str


@dataclass
class AgentPromptSuggestionDismissed:
    event_type: ClassVar[str] = "agent_prompt_suggestion_dismissed"
    session_id: str
    suggestion_id: str
    user_id: str


@dataclass
class ControlClaimed:
    event_type: ClassVar[str] = "control_claimed"
    session_id: str
    user_id: str


@dataclass
class ControlReleased:
    event_type: ClassVar[str] = "control_released"
    session_id: str
    user_id: str


@dataclass
class ViewerJoined:
    event_type: ClassVar[str] = "viewer_joined"
    session_id: str
    user_id: str


@dataclass
class SessionFailed:
    event_type: ClassVar[str] = "session_failed"
    session_id: str
    error: str


@dataclass
class SessionStarted:
    event_type: ClassVar[str] = "session_started"
    session_id: str
    workspace_path: str
    agent_session_id: str


@dataclass
class AgentPromptSubmitted:
    event_type: ClassVar[str] = "agent_prompt_submitted"
    session_id: str
    user_id: str
    text: str


@dataclass
class AgentSteered:
    event_type: ClassVar[str] = "agent_steered"
    session_id: str
    user_id: str
    text: str


@dataclass
class AgentAborted:
    event_type: ClassVar[str] = "agent_aborted"
    session_id: str
    user_id: str


@dataclass
class ViewerLeft:
    event_type: ClassVar[str] = "viewer_left"
    session_id: str
    user_id: str


def serialize_event(event: object) -> dict:
    if not is_dataclass(event):
        raise TypeError(f"unsupported event: {type(event)!r}")

    event_type = getattr(event, "event_type", None)
    if not isinstance(event_type, str):
        raise TypeError(f"event has no event_type: {type(event)!r}")

    return {"type": event_type, **asdict(cast(Any, event))}
