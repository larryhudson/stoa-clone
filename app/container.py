from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir

from app.domain.ports import EventPublisher, Runtime, SessionStore
from app.domain.services import FileEditingService, FileService, SessionService
from app.infra.event_publisher import BroadcastingEventPublisher
from app.infra.git_runtime import GitRuntime
from app.infra.json_store import JsonSessionStore
from app.infra.websocket_broadcaster import SessionEventBroadcaster


class NullEventPublisher:
    def publish(self, event: object) -> None:
        return None


@dataclass
class Container:
    store: SessionStore
    runtime: Runtime
    broadcaster: SessionEventBroadcaster
    event_publisher: EventPublisher
    session_service: SessionService
    file_service: FileService
    file_editing_service: FileEditingService


def build_container(base_dir: Path | None = None) -> Container:
    root = base_dir or (Path(gettempdir()) / "stoa-clone-workspaces")
    store = JsonSessionStore(root / "sessions.json")
    runtime = GitRuntime(root)
    broadcaster = SessionEventBroadcaster()
    event_publisher = BroadcastingEventPublisher(broadcaster)

    return Container(
        store=store,
        runtime=runtime,
        broadcaster=broadcaster,
        event_publisher=event_publisher,
        session_service=SessionService(store, runtime, event_publisher),
        file_service=FileService(store),
        file_editing_service=FileEditingService(store, event_publisher),
    )
