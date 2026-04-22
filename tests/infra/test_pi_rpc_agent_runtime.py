import json
import sys
import time

from app.infra.pi_rpc_agent_runtime import PiRpcAgentRuntime



def test_pi_rpc_agent_runtime_starts_process_in_workspace_and_sends_prompt_and_control_messages(tmp_path):
    log_path = tmp_path / "pi-rpc.log"
    fake_pi = tmp_path / "fake-pi.py"
    fake_pi.write_text(
        """
import json
import os
import sys
import time
from pathlib import Path

log_path = Path(sys.argv[1])
log_path.write_text(json.dumps({"cwd": os.getcwd()}) + "\\n")

for line in sys.stdin:
    with log_path.open("a") as handle:
        handle.write(line)
        handle.flush()
    if json.loads(line).get("type") == "abort":
        break

time.sleep(0.2)
""".strip()
        + "\n"
    )

    runtime = PiRpcAgentRuntime(command=[sys.executable, str(fake_pi), str(log_path)])
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    agent_session_id = runtime.start_agent_session("session-1", workspace)
    runtime.prompt(agent_session_id, "Summarize this repository")
    runtime.steer(agent_session_id, "Focus on tests")
    runtime.abort(agent_session_id)
    time.sleep(0.1)

    lines = log_path.read_text().splitlines()
    assert json.loads(lines[0]) == {"cwd": str(workspace)}
    assert json.loads(lines[1]) == {
        "type": "prompt",
        "message": "Summarize this repository",
    }
    assert json.loads(lines[2]) == {
        "type": "steer",
        "message": "Focus on tests",
    }
    assert json.loads(lines[3]) == {"type": "abort"}

    runtime._processes_by_agent_session_id[agent_session_id].terminate()
    runtime._processes_by_agent_session_id[agent_session_id].wait(timeout=5)
