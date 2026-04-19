from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.domain.models import Session


class SessionStore(Protocol):
    def add(self, session: Session) -> None: ...
    def save(self, session: Session) -> None: ...
    def get(self, session_id: str) -> Session: ...


class Runtime(Protocol):
    def provision_workspace(self, session_id: str) -> Path: ...
    def clone_repo(self, repo_url: str, branch: str, workspace: Path) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...
