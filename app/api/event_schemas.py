from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SessionEventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FileEditedEvent(SessionEventBase):
    type: Literal["file_edited"]
    session_id: str
    path: str
    editor_id: str
    content: str


class NoteAddedEvent(SessionEventBase):
    type: Literal["note_added"]
    session_id: str
    author_id: str
    body: str
    created_at: int


class ControlClaimedEvent(SessionEventBase):
    type: Literal["control_claimed"]
    session_id: str
    user_id: str


class ControlReleasedEvent(SessionEventBase):
    type: Literal["control_released"]
    session_id: str
    user_id: str


class ViewerJoinedEvent(SessionEventBase):
    type: Literal["viewer_joined"]
    session_id: str
    user_id: str


class ViewerLeftEvent(SessionEventBase):
    type: Literal["viewer_left"]
    session_id: str
    user_id: str


class SessionFailedEvent(SessionEventBase):
    type: Literal["session_failed"]
    session_id: str
    error: str


class SessionStartedEvent(SessionEventBase):
    type: Literal["session_started"]
    session_id: str
    workspace_path: str
    agent_session_id: str


class AgentPromptSubmittedEvent(SessionEventBase):
    type: Literal["agent_prompt_submitted"]
    session_id: str
    user_id: str
    text: str


class AgentSteeredEvent(SessionEventBase):
    type: Literal["agent_steered"]
    session_id: str
    user_id: str
    text: str


class AgentAbortedEvent(SessionEventBase):
    type: Literal["agent_aborted"]
    session_id: str
    user_id: str


class AgentRunStartedEvent(SessionEventBase):
    type: Literal["agent_run_started"]
    session_id: str


class AgentTextDeltaEvent(SessionEventBase):
    type: Literal["agent_text_delta"]
    session_id: str
    delta: str


class AgentRunFinishedEvent(SessionEventBase):
    type: Literal["agent_run_finished"]
    session_id: str


class AgentRunFailedEvent(SessionEventBase):
    type: Literal["agent_run_failed"]
    session_id: str
    error: str
    command: str | None = None


SessionEvent = Annotated[
    FileEditedEvent
    | NoteAddedEvent
    | ControlClaimedEvent
    | ControlReleasedEvent
    | ViewerJoinedEvent
    | ViewerLeftEvent
    | SessionFailedEvent
    | SessionStartedEvent
    | AgentPromptSubmittedEvent
    | AgentSteeredEvent
    | AgentAbortedEvent
    | AgentRunStartedEvent
    | AgentTextDeltaEvent
    | AgentRunFinishedEvent
    | AgentRunFailedEvent,
    Field(discriminator="type"),
]
