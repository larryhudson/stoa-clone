from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir

from app.domain.ports import AgentRuntime, EventPublisher, Runtime, SessionStore
from app.domain.services import FileEditingService, FileService, SessionService
from app.infra.event_publisher import BroadcastingEventPublisher
from app.infra.git_runtime import GitRuntime
from app.infra.json_store import JsonSessionStore
from app.infra.pi_rpc_agent_runtime import PiRpcAgentRuntime
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
    agent_runtime: AgentRuntime
    session_service: SessionService
    file_service: FileService
    file_editing_service: FileEditingService


def build_container(base_dir: Path | None = None) -> Container:
    root = base_dir or (Path(gettempdir()) / "multiplayer-agent-workspaces")
    store = JsonSessionStore(root / "sessions.json")
    runtime = GitRuntime(root)
    broadcaster = SessionEventBroadcaster()
    event_publisher = BroadcastingEventPublisher(broadcaster)
    session_service = SessionService(store, runtime, event_publisher)

    def handle_runtime_event(session_id: str, payload: dict) -> None:
        session_service.record_runtime_event(session_id, payload)
        broadcaster.publish(session_id, payload)

    pi_bin = os.environ.get("PI_BIN", "pi")
    agent_runtime = PiRpcAgentRuntime(
        command=[pi_bin, "--mode", "rpc", "--no-session"],
        event_handler=handle_runtime_event,
    )
    session_service.agent_runtime = agent_runtime

    return Container(
        store=store,
        runtime=runtime,
        broadcaster=broadcaster,
        event_publisher=event_publisher,
        agent_runtime=agent_runtime,
        session_service=session_service,
        file_service=FileService(store),
        file_editing_service=FileEditingService(store, event_publisher),
    )
