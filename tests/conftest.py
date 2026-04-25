from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.container import Container
from app.domain.services import (
    FileEditingService,
    FileService,
    SessionService,
    WorkspaceReviewService,
)
from app.infra.event_publisher import BroadcastingEventPublisher
from app.infra.fake_agent_runtime import FakeAgentRuntime
from app.infra.fake_prompt_suggestions import FakePromptSuggestionGenerator
from app.infra.fake_runtime import FakeRuntime
from app.infra.git_workspace_review import GitWorkspaceReviewProvider
from app.infra.in_memory import InMemorySessionStore
from app.infra.websocket_broadcaster import SessionEventBroadcaster
from app.main import create_app


class ConfigurableFailingRuntime:
    def __init__(
        self,
        *,
        provision_error: Exception | None = None,
        clone_error: Exception | None = None,
    ) -> None:
        self.provision_error = provision_error
        self.clone_error = clone_error

    def provision_workspace(self, session_id: str):
        if self.provision_error is not None:
            raise self.provision_error
        return tmp_path_placeholder(session_id)

    def clone_repo(self, repo_url: str, branch: str, workspace):
        if self.clone_error is not None:
            raise self.clone_error


class ConfigurableFailingAgentRuntime:
    def __init__(self, *, start_error: Exception | None = None) -> None:
        self.start_error = start_error

    def start_agent_session(self, session_id: str, workspace):
        if self.start_error is not None:
            raise self.start_error
        return f"agent-{session_id}"

    def prompt(self, agent_session_id: str, text: str) -> None:
        return None

    def steer(self, agent_session_id: str, text: str) -> None:
        return None

    def abort(self, agent_session_id: str) -> None:
        return None


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


def tmp_path_placeholder(session_id: str) -> str:
    return f"/tmp/{session_id}"


@pytest.fixture
def broadcaster() -> SessionEventBroadcaster:
    return SessionEventBroadcaster()


@pytest.fixture
def event_publisher(broadcaster: SessionEventBroadcaster) -> RecordingEventPublisher:
    return RecordingEventPublisher(broadcaster)


@pytest.fixture
def agent_runtime() -> FakeAgentRuntime:
    return FakeAgentRuntime()


@pytest.fixture
def session_service(
    store: InMemorySessionStore,
    runtime: FakeRuntime,
    event_publisher: RecordingEventPublisher,
    agent_runtime: FakeAgentRuntime,
) -> SessionService:
    workspace_summary_provider = GitWorkspaceReviewProvider()
    return SessionService(
        store,
        runtime,
        event_publisher,
        agent_runtime,
        FakePromptSuggestionGenerator(),
        workspace_summary_provider,
    )


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
def workspace_review_service(store: InMemorySessionStore) -> WorkspaceReviewService:
    return WorkspaceReviewService(store, GitWorkspaceReviewProvider())


@pytest.fixture
def container(
    store: InMemorySessionStore,
    runtime: FakeRuntime,
    broadcaster: SessionEventBroadcaster,
    event_publisher: RecordingEventPublisher,
    session_service: SessionService,
    file_service: FileService,
    file_editing_service: FileEditingService,
    workspace_review_service: WorkspaceReviewService,
    agent_runtime: FakeAgentRuntime,
) -> Container:
    return Container(
        store=store,
        runtime=runtime,
        broadcaster=broadcaster,
        event_publisher=event_publisher,
        session_service=session_service,
        file_service=file_service,
        file_editing_service=file_editing_service,
        workspace_review_service=workspace_review_service,
        agent_runtime=agent_runtime,
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
        agent_start_error: Exception | None = None,
    ):
        store = InMemorySessionStore()
        broadcaster = SessionEventBroadcaster()
        event_publisher = RecordingEventPublisher(broadcaster)
        runtime = ConfigurableFailingRuntime(
            provision_error=provision_error,
            clone_error=clone_error,
        )
        agent_runtime = ConfigurableFailingAgentRuntime(start_error=agent_start_error)
        workspace_summary_provider = GitWorkspaceReviewProvider()
        container = Container(
            store=store,
            runtime=runtime,
            broadcaster=broadcaster,
            event_publisher=event_publisher,
            session_service=SessionService(
                store,
                runtime,
                event_publisher,
                agent_runtime,
                FakePromptSuggestionGenerator(),
                workspace_summary_provider,
            ),
            file_service=FileService(store),
            file_editing_service=FileEditingService(store, event_publisher),
            workspace_review_service=WorkspaceReviewService(store, workspace_summary_provider),
            agent_runtime=agent_runtime,
        )
        client = TestClient(
            create_app(container=container),
            raise_server_exceptions=False,
        )
        return client, store

    return _make_failing_client
