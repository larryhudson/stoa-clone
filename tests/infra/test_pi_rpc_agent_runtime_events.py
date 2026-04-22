import json
import sys
import time

from app.infra.pi_rpc_agent_runtime import PiRpcAgentRuntime



def test_pi_rpc_agent_runtime_reads_stdout_events_and_normalizes_them(tmp_path):
    events: list[tuple[str, dict]] = []
    fake_pi = tmp_path / "fake-pi-events.py"
    fake_pi.write_text(
        """
import json
import sys

for line in sys.stdin:
    command = json.loads(line)
    if command.get("type") == "prompt":
        print(json.dumps({"type": "agent_start"}), flush=True)
        print(json.dumps({
            "type": "message_update",
            "assistantMessageEvent": {"type": "text_delta", "delta": "Hello"}
        }), flush=True)
        print(json.dumps({"type": "agent_end"}), flush=True)
        break
""".strip()
        + "\n"
    )

    runtime = PiRpcAgentRuntime(
        command=[sys.executable, str(fake_pi)],
        event_handler=lambda session_id, payload: events.append((session_id, payload)),
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    agent_session_id = runtime.start_agent_session("session-1", workspace)
    runtime.prompt(agent_session_id, "Summarize this repository")

    deadline = time.time() + 3
    while len(events) < 3 and time.time() < deadline:
        time.sleep(0.05)

    assert events == [
        ("session-1", {"type": "agent_run_started", "session_id": "session-1"}),
        (
            "session-1",
            {"type": "agent_text_delta", "session_id": "session-1", "delta": "Hello"},
        ),
        ("session-1", {"type": "agent_run_finished", "session_id": "session-1"}),
    ]

    runtime._processes_by_agent_session_id[agent_session_id].terminate()
    runtime._processes_by_agent_session_id[agent_session_id].wait(timeout=5)
