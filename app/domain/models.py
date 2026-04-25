from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class SessionStatus(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"


class AgentStatus(StrEnum):
    NOT_STARTED = "not_started"
    STARTING = "starting"
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"


class AgentOutputStatus(StrEnum):
    EMPTY = "empty"
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETE = "complete"
    FAILED = "failed"


class PromptSuggestionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"


@dataclass
class Note:
    author_id: str
    body: str
    created_at: int


@dataclass
class ChatMessage:
    id: str
    author_id: str
    body: str
    created_at: int


@dataclass
class PromptSuggestion:
    id: str
    text: str
    reason: str
    source_message_ids: list[str]
    status: PromptSuggestionStatus
    created_at: int


@dataclass
class PromptSuggestionDraft:
    text: str
    reason: str
    source_message_ids: list[str]


@dataclass
class WorkspaceSummary:
    changed_files: list[str]
    diff: str


@dataclass
class PromptSuggestionContext:
    transcript: list[ChatMessage]
    agent_status: AgentStatus
    recent_agent_events: list[dict]
    pending_suggestions: list[PromptSuggestion]
    workspace_summary: WorkspaceSummary | None


@dataclass
class Session:
    id: str
    repo_url: str
    branch: str = "main"
    status: SessionStatus = SessionStatus.CREATED
    workspace_path: str | None = None
    agent_session_id: str | None = None
    agent_status: AgentStatus = AgentStatus.NOT_STARTED
    agent_output: str = ""
    agent_output_status: AgentOutputStatus = AgentOutputStatus.EMPTY
    agent_output_error: str | None = None
    viewers: set[str] = field(default_factory=set)
    controller_id: str | None = None
    notes: list[Note] = field(default_factory=list)
    chat_messages: list[ChatMessage] = field(default_factory=list)
    prompt_suggestions: list[PromptSuggestion] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
