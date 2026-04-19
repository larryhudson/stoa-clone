from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.container import Container
from app.domain.services import FileEditingService, FileService, SessionService
from app.infra.event_publisher import BroadcastingEventPublisher
from app.infra.fake_runtime import FakeRuntime
from app.infra.in_memory import InMemorySessionStore
from app.infra.websocket_broadcaster import SessionEventBroadcaster
from app.main import create_app


class ConfigurableFailingRuntime:
    def __init__(self, *, provision_error: Exception | None = None, clone_error: Exception | None = None) -> None:
        self.provision_error = provision_error
        self.clone_error = clone_error

    def provision_workspace(self, session_id: str):
        if self.provision_error is not None:
            raise self.provision_error
        return f"/tmp/{session_id}"

    def clone_repo(self, repo_url: str, branch: str, workspace):
        if self.clone_error is not None:
            raise self.clone_error


class RecordingEventPublisher(BroadcastingEventPublisher):
    def __init__(self, broadcaster: SessionEventBroadcaster) -> None:
        super().__init__(broadcaster)
        self.published: list[object] = []

    def publish(self, event: object) -> None:
        self.published.append(event)
        super().publish(event)


@pytest.fixture
def store() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture
def runtime(tmp_path) -> FakeRuntime:
    return FakeRuntime(tmp_path)


@pytest.fixture
def broadcaster() -> SessionEventBroadcaster:
    return SessionEventBroadcaster()


@pytest.fixture
def event_publisher(broadcaster: SessionEventBroadcaster) -> RecordingEventPublisher:
    return RecordingEventPublisher(broadcaster)


@pytest.fixture
def session_service(
    store: InMemorySessionStore,
    runtime: FakeRuntime,
    event_publisher: RecordingEventPublisher,
) -> SessionService:
    return SessionService(store, runtime, event_publisher)


@pytest.fixture
def file_service(store: InMemorySessionStore) -> FileService:
    return FileService(store)


@pytest.fixture
def file_editing_service(
    store: InMemorySessionStore,
    event_publisher: RecordingEventPublisher,
) -> FileEditingService:
    return FileEditingService(store, event_publisher)


@pytest.fixture
def container(
    store: InMemorySessionStore,
    runtime: FakeRuntime,
    broadcaster: SessionEventBroadcaster,
    event_publisher: RecordingEventPublisher,
    session_service: SessionService,
    file_service: FileService,
    file_editing_service: FileEditingService,
) -> Container:
    return Container(
        store=store,
        runtime=runtime,
        broadcaster=broadcaster,
        event_publisher=event_publisher,
        session_service=session_service,
        file_service=file_service,
        file_editing_service=file_editing_service,
    )


@pytest.fixture
def app(container: Container):
    return create_app(container=container)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def make_failing_client():
    def _make_failing_client(
        *,
        provision_error: Exception | None = None,
        clone_error: Exception | None = None,
    ):
        store = InMemorySessionStore()
        broadcaster = SessionEventBroadcaster()
        event_publisher = RecordingEventPublisher(broadcaster)
        runtime = ConfigurableFailingRuntime(
            provision_error=provision_error,
            clone_error=clone_error,
        )
        container = Container(
            store=store,
            runtime=runtime,
            broadcaster=broadcaster,
            event_publisher=event_publisher,
            session_service=SessionService(store, runtime, event_publisher),
            file_service=FileService(store),
            file_editing_service=FileEditingService(store, event_publisher),
        )
        client = TestClient(
            create_app(container=container),
            raise_server_exceptions=False,
        )
        return client, store

    return _make_failing_client
