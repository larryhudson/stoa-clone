import os
import shutil

import pytest

from app.infra.pi_rpc_agent_runtime import PiRpcAgentRuntime


def _real_pi_bin() -> str | None:
    return os.environ.get("PI_BIN") or shutil.which("pi")


@pytest.mark.skipif(_real_pi_bin() is None, reason="real pi binary not available")
def test_real_pi_rpc_agent_runtime_starts_process_and_stays_alive_briefly(tmp_path, monkeypatch):
    pi_bin = _real_pi_bin()
    assert pi_bin is not None

    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path / "pi-home"))
    monkeypatch.setenv("PI_OFFLINE", "1")

    runtime = PiRpcAgentRuntime(
        command=[pi_bin, "--mode", "rpc", "--no-session", "--offline"],
        startup_grace_period=0.2,
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    agent_session_id = runtime.start_agent_session("session-1", workspace)
    process = runtime._processes_by_agent_session_id[agent_session_id]

    try:
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=5)
