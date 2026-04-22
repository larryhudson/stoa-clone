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



class NullEventPublisher:
    def publish(self, event: object) -> None:
        return None



def test_watcher_receives_live_agent_runtime_event_over_websocket(store, runtime, broadcaster):
    from app.container import Container
    from app.domain.services import FileEditingService, FileService, SessionService
    from app.main import create_app
    from fastapi.testclient import TestClient

    event_publisher = NullEventPublisher()
    agent_runtime = EventingFakeAgentRuntime(broadcaster.publish)
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
        messages = [receive_json_with_timeout(websocket) for _ in range(3)]

    assert messages == [
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
