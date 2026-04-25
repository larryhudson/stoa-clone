from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.domain.models import (
    PromptSuggestionContext,
    PromptSuggestionDraft,
    Session,
    WorkspaceSummary,
)


class SessionStore(Protocol):
    def add(self, session: Session) -> None: ...
    def save(self, session: Session) -> None: ...
    def get(self, session_id: str) -> Session: ...


class Runtime(Protocol):
    def provision_workspace(self, session_id: str) -> Path: ...
    def clone_repo(self, repo_url: str, branch: str, workspace: Path) -> None: ...


class AgentRuntime(Protocol):
    def start_agent_session(self, session_id: str, workspace: Path) -> str: ...
    def prompt(self, agent_session_id: str, text: str) -> None: ...
    def steer(self, agent_session_id: str, text: str) -> None: ...
    def abort(self, agent_session_id: str) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...


class PromptSuggestionGenerator(Protocol):
    def suggest(self, context: PromptSuggestionContext) -> list[PromptSuggestionDraft]: ...


class WorkspaceSummaryProvider(Protocol):
    def get_summary(self, session: Session) -> WorkspaceSummary: ...
