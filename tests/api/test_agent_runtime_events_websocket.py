from tests.helpers.websocket import receive_json_with_timeout


class EventingFakeAgentRuntime:
    def __init__(self, publish) -> None:
        self.publish = publish

    def start_agent_session(self, session_id: str, workspace) -> str:
        self.session_id = session_id
        return f"agent-{session_id}"

    def prompt(self, agent_session_id: str, text: str) -> None:
        self.publish(
            self.session_id,
            {"type": "agent_run_started", "session_id": self.session_id},
        )
        self.publish(
            self.session_id,
            {
                "type": "agent_text_delta",
                "session_id": self.session_id,
                "delta": "Hello",
            },
        )
        self.publish(
            self.session_id,
            {"type": "agent_run_finished", "session_id": self.session_id},
        )

    def steer(self, agent_session_id: str, text: str) -> None:
        return None

    def abort(self, agent_session_id: str) -> None:
        return None


class ThreadedEventingFakeAgentRuntime:
    def __init__(self, publish) -> None:
        self.publish = publish

    def start_agent_session(self, session_id: str, workspace) -> str:
        self.session_id = session_id
        return f"agent-{session_id}"

    def prompt(self, agent_session_id: str, text: str) -> None:
        from threading import Thread

        def emit() -> None:
            self.publish(
                self.session_id,
                {"type": "agent_run_started", "session_id": self.session_id},
            )
            self.publish(
                self.session_id,
                {
                    "type": "agent_text_delta",
                    "session_id": self.session_id,
                    "delta": "Hello",
                },
            )
            self.publish(
                self.session_id,
                {"type": "agent_run_finished", "session_id": self.session_id},
            )

        Thread(target=emit, daemon=True).start()

    def steer(self, agent_session_id: str, text: str) -> None:
        return None

    def abort(self, agent_session_id: str) -> None:
        return None


def test_watcher_receives_prompt_submission_before_live_agent_runtime_events_over_websocket(
    store,
    runtime,
    broadcaster,
):
    from fastapi.testclient import TestClient

    from app.container import Container
    from app.domain.services import (
        FileEditingService,
        FileService,
        SessionService,
        WorkspaceReviewService,
    )
    from app.infra.event_publisher import BroadcastingEventPublisher
    from app.infra.git_workspace_review import GitWorkspaceReviewProvider
    from app.main import create_app

    event_publisher = BroadcastingEventPublisher(broadcaster)
    workspace_summary_provider = GitWorkspaceReviewProvider()
    session_service: SessionService | None = None

    def publish_runtime_event(session_id: str, payload: dict) -> None:
        assert session_service is not None
        session_service.record_runtime_event(session_id, payload)
        broadcaster.publish(session_id, payload)

    agent_runtime = EventingFakeAgentRuntime(publish_runtime_event)
    session_service = SessionService(store, runtime, event_publisher, agent_runtime)
    app = create_app(
        container=Container(
            store=store,
            runtime=runtime,
            broadcaster=broadcaster,
            event_publisher=event_publisher,
            agent_runtime=agent_runtime,
            session_service=session_service,
            file_service=FileService(store),
            file_editing_service=FileEditingService(store, event_publisher),
            workspace_review_service=WorkspaceReviewService(store, workspace_summary_provider),
        )
    )
    client = TestClient(app)

    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        client.post(
            f"/sessions/{session_id}/agent/prompt",
            json={"user_id": "user-1", "text": "Summarize this repository"},
        )
        messages = [receive_json_with_timeout(websocket) for _ in range(4)]

    assert messages == [
        {
            "type": "agent_prompt_submitted",
            "session_id": session_id,
            "user_id": "user-1",
            "text": "Summarize this repository",
        },
        {
            "type": "agent_run_started",
            "session_id": session_id,
        },
        {
            "type": "agent_text_delta",
            "session_id": session_id,
            "delta": "Hello",
        },
        {
            "type": "agent_run_finished",
            "session_id": session_id,
        },
    ]


def test_watcher_receives_thread_published_agent_runtime_events_over_websocket(
    store,
    runtime,
    broadcaster,
):
    from fastapi.testclient import TestClient

    from app.container import Container
    from app.domain.services import (
        FileEditingService,
        FileService,
        SessionService,
        WorkspaceReviewService,
    )
    from app.infra.event_publisher import BroadcastingEventPublisher
    from app.infra.git_workspace_review import GitWorkspaceReviewProvider
    from app.main import create_app

    event_publisher = BroadcastingEventPublisher(broadcaster)
    workspace_summary_provider = GitWorkspaceReviewProvider()
    session_service: SessionService | None = None

    def publish_runtime_event(session_id: str, payload: dict) -> None:
        assert session_service is not None
        session_service.record_runtime_event(session_id, payload)
        broadcaster.publish(session_id, payload)

    agent_runtime = ThreadedEventingFakeAgentRuntime(publish_runtime_event)
    session_service = SessionService(store, runtime, event_publisher, agent_runtime)
    app = create_app(
        container=Container(
            store=store,
            runtime=runtime,
            broadcaster=broadcaster,
            event_publisher=event_publisher,
            agent_runtime=agent_runtime,
            session_service=session_service,
            file_service=FileService(store),
            file_editing_service=FileEditingService(store, event_publisher),
            workspace_review_service=WorkspaceReviewService(store, workspace_summary_provider),
        )
    )
    client = TestClient(app)

    session_id = client.post(
        "/sessions",
        json={"repo_url": "https://github.com/example/repo.git"},
    ).json()["id"]
    client.post(f"/sessions/{session_id}/start")
    client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

    with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
        client.post(
            f"/sessions/{session_id}/agent/prompt",
            json={"user_id": "user-1", "text": "Summarize this repository"},
        )
        messages = [receive_json_with_timeout(websocket) for _ in range(4)]

    assert messages == [
        {
            "type": "agent_prompt_submitted",
            "session_id": session_id,
            "user_id": "user-1",
            "text": "Summarize this repository",
        },
        {
            "type": "agent_run_started",
            "session_id": session_id,
        },
        {
            "type": "agent_text_delta",
            "session_id": session_id,
            "delta": "Hello",
        },
        {
            "type": "agent_run_finished",
            "session_id": session_id,
        },
    ]
