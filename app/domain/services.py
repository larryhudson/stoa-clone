from __future__ import annotations

from itertools import count
from pathlib import Path
from uuid import uuid4

from markdown import markdown

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
from app.domain.models import AgentOutputStatus, AgentStatus, Note, Session, SessionStatus
from app.domain.ports import AgentRuntime, EventPublisher, Runtime, SessionStore

HIDDEN_PATH_PARTS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".DS_Store"}


def is_hidden_path(relative_path: Path) -> bool:
    return any(part in HIDDEN_PATH_PARTS for part in relative_path.parts)


class SessionService:
    def __init__(
        self,
        store: SessionStore,
        runtime: Runtime,
        event_publisher: EventPublisher | None = None,
        agent_runtime: AgentRuntime | None = None,
    ) -> None:
        self.store = store
        self.runtime = runtime
        self.event_publisher = event_publisher
        self.agent_runtime = agent_runtime
        self._clock = count(1)

    def create_session(self, repo_url: str, branch: str = "main") -> Session:
        session = Session(id=str(uuid4()), repo_url=repo_url, branch=branch)
        self.store.add(session)
        return session

    def get_session(self, session_id: str) -> Session:
        return self.store.get(session_id)

    def get_presence(self, session_id: str) -> dict[str, object]:
        session = self.store.get(session_id)
        return {
            "controller_id": session.controller_id,
            "viewers": sorted(session.viewers),
        }

    def start_session(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        session.status = SessionStatus.STARTING
        session.agent_status = AgentStatus.STARTING
        self.store.save(session)
        try:
            workspace = self.runtime.provision_workspace(session.id)
            self.runtime.clone_repo(session.repo_url, session.branch, workspace)
            if self.agent_runtime is not None:
                session.agent_session_id = self.agent_runtime.start_agent_session(
                    session.id, workspace
                )
        except Exception as exc:
            session.status = SessionStatus.FAILED
            session.agent_status = AgentStatus.FAILED
            self._publish_event(session, SessionFailed(session_id=session_id, error=str(exc)))
            self.store.save(session)
            raise
        session.workspace_path = str(workspace)
        session.status = SessionStatus.READY
        session.agent_status = AgentStatus.IDLE
        self._publish_event(
            session,
            SessionStarted(
                session_id=session_id,
                workspace_path=session.workspace_path,
                agent_session_id=session.agent_session_id or "",
            ),
        )
        self.store.save(session)
        return session

    def join_session(self, session_id: str, user_id: str) -> Session:
        session = self.store.get(session_id)
        session.viewers.add(user_id)
        self._publish_event(session, ViewerJoined(session_id=session_id, user_id=user_id))
        self.store.save(session)
        return session

    def leave_session(self, session_id: str, user_id: str) -> Session:
        session = self.store.get(session_id)
        if user_id not in session.viewers and session.controller_id != user_id:
            return session
        if session.controller_id == user_id:
            session.controller_id = None
            self._publish_event(session, ControlReleased(session_id=session_id, user_id=user_id))
        session.viewers.discard(user_id)
        self._publish_event(session, ViewerLeft(session_id=session_id, user_id=user_id))
        self.store.save(session)
        return session

    def claim_control(self, session_id: str, user_id: str) -> Session:
        session = self.store.get(session_id)
        if session.controller_id and session.controller_id != user_id:
            raise ValueError("control already held")
        session.viewers.add(user_id)
        session.controller_id = user_id
        self._publish_event(session, ControlClaimed(session_id=session_id, user_id=user_id))
        self.store.save(session)
        return session

    def release_control(self, session_id: str, user_id: str) -> Session:
        session = self.store.get(session_id)
        if session.controller_id == user_id:
            session.controller_id = None
            self._publish_event(session, ControlReleased(session_id=session_id, user_id=user_id))
            self.store.save(session)
        return session

    def add_note(self, session_id: str, author_id: str, body: str) -> Note:
        session = self.store.get(session_id)
        note = Note(author_id=author_id, body=body, created_at=next(self._clock))
        session.notes.append(note)
        self._publish_event(
            session,
            NoteAdded(
                session_id=session_id,
                author_id=author_id,
                body=body,
                created_at=note.created_at,
            ),
        )
        self.store.save(session)
        return note

    def prompt_agent(self, session_id: str, user_id: str, text: str) -> Session:
        session = self.store.get(session_id)
        self._ensure_controller(session, user_id, action="prompt")
        agent_runtime = self.agent_runtime
        agent_session_id = session.agent_session_id
        assert agent_runtime is not None
        assert agent_session_id is not None

        previous_status = session.agent_status
        session.agent_status = AgentStatus.RUNNING
        session.agent_output = ""
        session.agent_output_status = AgentOutputStatus.PENDING
        session.agent_output_error = None
        self._publish_event(
            session,
            AgentPromptSubmitted(session_id=session_id, user_id=user_id, text=text),
        )
        self.store.save(session)
        try:
            agent_runtime.prompt(agent_session_id, text)
        except Exception:
            session = self.store.get(session_id)
            if session.agent_status == AgentStatus.RUNNING:
                # Only roll back our optimistic transition if no runtime event has
                # already moved the session into a later terminal state.
                session.agent_status = previous_status
                self.store.save(session)
            raise

        return self.store.get(session_id)

    def steer_agent(self, session_id: str, user_id: str, text: str) -> Session:
        session = self.store.get(session_id)
        self._ensure_controller(session, user_id, action="steer")
        agent_runtime = self.agent_runtime
        agent_session_id = session.agent_session_id
        assert agent_runtime is not None
        assert agent_session_id is not None

        agent_runtime.steer(agent_session_id, text)
        self._publish_event(
            session,
            AgentSteered(session_id=session_id, user_id=user_id, text=text),
        )
        self.store.save(session)
        return session

    def abort_agent(self, session_id: str, user_id: str) -> Session:
        session = self.store.get(session_id)
        self._ensure_controller(session, user_id, action="abort")
        agent_runtime = self.agent_runtime
        agent_session_id = session.agent_session_id
        assert agent_runtime is not None
        assert agent_session_id is not None

        agent_runtime.abort(agent_session_id)
        self._publish_event(
            session,
            AgentAborted(session_id=session_id, user_id=user_id),
        )
        self.store.save(session)
        return session

    def list_notes(self, session_id: str) -> list[Note]:
        return list(self.store.get(session_id).notes)

    def list_events(self, session_id: str) -> list[dict]:
        return list(self.store.get(session_id).events)

    def record_runtime_event(self, session_id: str, payload: dict) -> Session:
        session = self.store.get(session_id)
        event_type = payload.get("type")
        if event_type == "agent_run_started":
            session.agent_status = AgentStatus.RUNNING
            session.agent_output = ""
            session.agent_output_status = AgentOutputStatus.STREAMING
            session.agent_output_error = None
        elif event_type == "agent_run_finished":
            session.agent_status = AgentStatus.IDLE
            session.agent_output_status = AgentOutputStatus.COMPLETE
        elif event_type == "agent_run_failed":
            session.agent_status = AgentStatus.FAILED
            session.agent_output_status = AgentOutputStatus.FAILED
            session.agent_output_error = str(payload.get("error", "")) or None
        elif event_type == "agent_text_delta":
            session.agent_output += str(payload.get("delta", ""))
            session.agent_output_status = AgentOutputStatus.STREAMING
        session.events.append(dict(payload))
        self.store.save(session)
        return session

    def _ensure_controller(self, session: Session, user_id: str, *, action: str) -> None:
        if session.controller_id != user_id:
            raise PermissionError(f"only controller can {action} agent")
        if session.agent_session_id is None or self.agent_runtime is None:
            raise ValueError("session has no agent")

    def _publish_event(self, session: Session, event: object) -> None:
        session.events.append(serialize_event(event))
        if self.event_publisher is not None:
            self.event_publisher.publish(event)


class FileService:
    def __init__(self, store: SessionStore) -> None:
        self.store = store

    def list_files(self, session_id: str) -> list[str]:
        root = self._workspace(session_id)
        return sorted(
            str(relative_path)
            for path in root.rglob("*")
            if path.is_file()
            for relative_path in [path.relative_to(root)]
            if not is_hidden_path(relative_path)
        )

    def read_file(self, session_id: str, relative_path: str) -> str:
        path = self._resolve(session_id, relative_path)
        return path.read_text()

    def render_preview(self, session_id: str, relative_path: str) -> str:
        path = self._resolve(session_id, relative_path)
        if path.suffix.lower() == ".md":
            return markdown(path.read_text())
        return f"<pre>{path.read_text()}</pre>"

    def _workspace(self, session_id: str) -> Path:
        session = self.store.get(session_id)
        if not session.workspace_path:
            raise ValueError("session has no workspace")
        return Path(session.workspace_path)

    def _resolve(self, session_id: str, relative_path: str) -> Path:
        root = self._workspace(session_id).resolve()
        relative = Path(relative_path)
        if is_hidden_path(relative):
            raise ValueError("path is hidden")
        candidate = (root / relative_path).resolve()
        if root not in candidate.parents and candidate != root:
            raise ValueError("path escapes workspace")
        return candidate


class FileEditingService:
    def __init__(self, store: SessionStore, event_publisher: EventPublisher) -> None:
        self.store = store
        self.event_publisher = event_publisher

    def edit_file(
        self,
        session_id: str,
        user_id: str,
        path: str,
        new_content: str,
    ) -> None:
        session = self.store.get(session_id)
        if session.controller_id != user_id:
            raise PermissionError("only controller can edit files")

        if not session.workspace_path:
            raise ValueError("session has no workspace")

        root = Path(session.workspace_path).resolve()
        relative = Path(path)
        if is_hidden_path(relative):
            raise ValueError("path is hidden")
        candidate = (root / path).resolve()
        if root not in candidate.parents and candidate != root:
            raise ValueError("path escapes workspace")

        candidate.write_text(new_content)
        event = FileEdited(
            session_id=session_id,
            path=path,
            editor_id=user_id,
            content=new_content,
        )
        session.events.append(serialize_event(event))
        self.store.save(session)
        self.event_publisher.publish(event)
