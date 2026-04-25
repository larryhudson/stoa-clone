import os
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.container import build_container
from app.main import create_app
from tests.helpers.websocket import receive_json_with_timeout


def _real_pi_bin() -> str | None:
    return os.environ.get("PI_BIN") or shutil.which("pi")


def _create_local_repo(tmp_path):
    repo = tmp_path / "origin"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "README.md").write_text("# Local Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def _terminate_agent_processes(container) -> None:
    for process in container.agent_runtime._processes_by_agent_session_id.values():
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


@pytest.mark.skipif(_real_pi_bin() is None, reason="real pi binary not available")
def test_can_start_session_via_api_with_real_container_and_real_pi(tmp_path, monkeypatch):
    pi_bin = _real_pi_bin()
    assert pi_bin is not None

    monkeypatch.setenv("PI_BIN", pi_bin)
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi-home"))
    monkeypatch.setenv("PI_OFFLINE", "1")

    repo = _create_local_repo(tmp_path)
    container = build_container(base_dir=tmp_path / "appdata")
    client = TestClient(create_app(container=container))

    try:
        created = client.post("/sessions", json={"repo_url": str(repo), "branch": "main"})
        session_id = created.json()["id"]
        started = client.post(f"/sessions/{session_id}/start")

        assert created.status_code == 200
        assert started.status_code == 200
        assert started.json()["status"] == "ready"
        assert started.json()["agent_status"] == "idle"
        assert started.json()["agent_session_id"]
        assert started.json()["workspace_path"]
    finally:
        _terminate_agent_processes(container)


@pytest.mark.skipif(_real_pi_bin() is None, reason="real pi binary not available")
def test_session_started_event_is_streamed_over_websocket_with_real_container_and_real_pi(
    tmp_path,
    monkeypatch,
):
    pi_bin = _real_pi_bin()
    assert pi_bin is not None

    monkeypatch.setenv("PI_BIN", pi_bin)
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi-home"))
    monkeypatch.setenv("PI_OFFLINE", "1")

    repo = _create_local_repo(tmp_path)
    container = build_container(base_dir=tmp_path / "appdata")
    client = TestClient(create_app(container=container))

    try:
        session_id = client.post("/sessions", json={"repo_url": str(repo), "branch": "main"}).json()["id"]

        with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
            started = client.post(f"/sessions/{session_id}/start")
            message = receive_json_with_timeout(websocket)

        assert started.status_code == 200
        assert message == {
            "type": "session_started",
            "session_id": session_id,
            "workspace_path": started.json()["workspace_path"],
            "agent_session_id": started.json()["agent_session_id"],
        }
    finally:
        _terminate_agent_processes(container)


@pytest.mark.skipif(_real_pi_bin() is None, reason="real pi binary not available")
def test_agent_prompt_submission_is_streamed_over_websocket_with_real_container_and_real_pi(
    tmp_path,
    monkeypatch,
):
    pi_bin = _real_pi_bin()
    assert pi_bin is not None

    monkeypatch.setenv("PI_BIN", pi_bin)
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi-home"))
    monkeypatch.setenv("PI_OFFLINE", "1")

    repo = _create_local_repo(tmp_path)
    container = build_container(base_dir=tmp_path / "appdata")
    client = TestClient(create_app(container=container))

    try:
        session_id = client.post("/sessions", json={"repo_url": str(repo), "branch": "main"}).json()["id"]
        client.post(f"/sessions/{session_id}/start")
        client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

        with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
            prompted = client.post(
                f"/sessions/{session_id}/agent/prompt",
                json={"user_id": "user-1", "text": "Summarize this repository"},
            )
            message = receive_json_with_timeout(websocket)

        assert prompted.status_code == 200
        assert message == {
            "type": "agent_prompt_submitted",
            "session_id": session_id,
            "user_id": "user-1",
            "text": "Summarize this repository",
        }
    finally:
        _terminate_agent_processes(container)


@pytest.mark.skipif(_real_pi_bin() is None, reason="real pi binary not available")
def test_agent_prompt_failure_is_streamed_and_persisted_with_real_container_and_real_pi(
    tmp_path,
    monkeypatch,
):
    pi_bin = _real_pi_bin()
    assert pi_bin is not None

    monkeypatch.setenv("PI_BIN", pi_bin)
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi-home"))
    monkeypatch.setenv("PI_OFFLINE", "1")

    repo = _create_local_repo(tmp_path)
    container = build_container(base_dir=tmp_path / "appdata")
    client = TestClient(create_app(container=container))

    try:
        session_id = client.post("/sessions", json={"repo_url": str(repo), "branch": "main"}).json()["id"]
        client.post(f"/sessions/{session_id}/start")
        client.post(f"/sessions/{session_id}/control/claim", json={"user_id": "user-1"})

        with client.websocket_connect(f"/sessions/{session_id}/events/ws") as websocket:
            prompted = client.post(
                f"/sessions/{session_id}/agent/prompt",
                json={"user_id": "user-1", "text": "Summarize this repository"},
            )
            first = receive_json_with_timeout(websocket)
            second = receive_json_with_timeout(websocket, timeout=10.0)

        failed = client.get(f"/sessions/{session_id}")

        assert prompted.status_code == 200
        assert first == {
            "type": "agent_prompt_submitted",
            "session_id": session_id,
            "user_id": "user-1",
            "text": "Summarize this repository",
        }
        assert second["type"] == "agent_run_failed"
        assert second["session_id"] == session_id
        assert second["command"] == "prompt"
        assert isinstance(second["error"], str)
        assert second["error"]
        assert failed.status_code == 200
        assert failed.json()["agent_status"] == "failed"
    finally:
        _terminate_agent_processes(container)
