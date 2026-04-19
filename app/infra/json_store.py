from __future__ import annotations

import json
from pathlib import Path

from app.domain.models import Note, Session, SessionStatus


class JsonSessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def add(self, session: Session) -> None:
        sessions = self._load_all()
        sessions[session.id] = self._serialize_session(session)
        self._write_all(sessions)

    def save(self, session: Session) -> None:
        sessions = self._load_all()
        sessions[session.id] = self._serialize_session(session)
        self._write_all(sessions)

    def get(self, session_id: str) -> Session:
        sessions = self._load_all()
        return self._deserialize_session(sessions[session_id])

    def _load_all(self) -> dict[str, dict]:
        return json.loads(self.path.read_text())

    def _write_all(self, sessions: dict[str, dict]) -> None:
        self.path.write_text(json.dumps(sessions, indent=2, sort_keys=True))

    def _serialize_session(self, session: Session) -> dict:
        return {
            "id": session.id,
            "repo_url": session.repo_url,
            "branch": session.branch,
            "status": session.status.value,
            "workspace_path": session.workspace_path,
            "viewers": sorted(session.viewers),
            "controller_id": session.controller_id,
            "notes": [
                {
                    "author_id": note.author_id,
                    "body": note.body,
                    "created_at": note.created_at,
                }
                for note in session.notes
            ],
            "events": list(session.events),
        }

    def _deserialize_session(self, data: dict) -> Session:
        return Session(
            id=data["id"],
            repo_url=data["repo_url"],
            branch=data["branch"],
            status=SessionStatus(data["status"]),
            workspace_path=data["workspace_path"],
            viewers=set(data["viewers"]),
            controller_id=data["controller_id"],
            notes=[Note(**note) for note in data["notes"]],
            events=list(data.get("events", [])),
        )
