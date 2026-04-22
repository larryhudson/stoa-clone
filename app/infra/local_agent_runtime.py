from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class LocalAgentRuntime:
    def __init__(self) -> None:
        self._processes_by_agent_session_id: dict[str, subprocess.Popen[str]] = {}

    def start_agent_session(self, session_id: str, workspace: Path) -> str:
        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-c",
                "import time; print('agent session ready', flush=True); time.sleep(3600)",
            ],
            cwd=workspace,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        agent_session_id = f"local-process-{process.pid}"
        self._processes_by_agent_session_id[agent_session_id] = process
        return agent_session_id

    def prompt(self, agent_session_id: str, text: str) -> None:
        process = self._processes_by_agent_session_id.get(agent_session_id)
        if process is None or process.poll() is not None:
            raise RuntimeError("agent session is not running")
        return None
