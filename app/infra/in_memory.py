from __future__ import annotations

from app.domain.models import Session


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def add(self, session: Session) -> None:
        self._sessions[session.id] = session

    def save(self, session: Session) -> None:
        self._sessions[session.id] = session

    def get(self, session_id: str) -> Session:
        return self._sessions[session_id]
