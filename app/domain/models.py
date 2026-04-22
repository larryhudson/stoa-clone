from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SessionStatus(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"


class AgentStatus(str, Enum):
    NOT_STARTED = "not_started"
    STARTING = "starting"
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"


@dataclass
class Note:
    author_id: str
    body: str
    created_at: int


@dataclass
class Session:
    id: str
    repo_url: str
    branch: str = "main"
    status: SessionStatus = SessionStatus.CREATED
    workspace_path: str | None = None
    agent_session_id: str | None = None
    agent_status: AgentStatus = AgentStatus.NOT_STARTED
    viewers: set[str] = field(default_factory=set)
    controller_id: str | None = None
    notes: list[Note] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
