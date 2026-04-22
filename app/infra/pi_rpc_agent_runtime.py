from __future__ import annotations

import json
import subprocess
from pathlib import Path
from threading import Thread
from typing import Callable


class PiRpcAgentRuntime:
    def __init__(
        self,
        command: list[str] | None = None,
        event_handler: Callable[[str, dict], None] | None = None,
    ) -> None:
        self.command = command or ["pi", "--mode", "rpc", "--no-session"]
        self.event_handler = event_handler
        self._processes_by_agent_session_id: dict[str, subprocess.Popen[str]] = {}

    def start_agent_session(self, session_id: str, workspace: Path) -> str:
        process = subprocess.Popen(
            self.command,
            cwd=workspace,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        agent_session_id = f"pi-rpc-{session_id}-{process.pid}"
        self._processes_by_agent_session_id[agent_session_id] = process
        Thread(
            target=self._read_events,
            args=(session_id, process),
            daemon=True,
        ).start()
        return agent_session_id

    def prompt(self, agent_session_id: str, text: str) -> None:
        self._send_command(agent_session_id, {"type": "prompt", "message": text})

    def steer(self, agent_session_id: str, text: str) -> None:
        self._send_command(agent_session_id, {"type": "steer", "message": text})

    def abort(self, agent_session_id: str) -> None:
        self._send_command(agent_session_id, {"type": "abort"})

    def _send_command(self, agent_session_id: str, command: dict) -> None:
        process = self._require_running_process(agent_session_id)
        assert process.stdin is not None
        process.stdin.write(json.dumps(command) + "\n")
        process.stdin.flush()

    def _require_running_process(self, agent_session_id: str) -> subprocess.Popen[str]:
        process = self._processes_by_agent_session_id.get(agent_session_id)
        if process is None or process.poll() is not None:
            raise RuntimeError("agent session is not running")
        return process

    def _read_events(self, session_id: str, process: subprocess.Popen[str]) -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            normalized = self._normalize_event(session_id, payload)
            if normalized is not None and self.event_handler is not None:
                self.event_handler(session_id, normalized)

    def _normalize_event(self, session_id: str, payload: dict) -> dict | None:
        event_type = payload.get("type")
        if event_type == "agent_start":
            return {"type": "agent_run_started", "session_id": session_id}
        if event_type == "agent_end":
            return {"type": "agent_run_finished", "session_id": session_id}
        if event_type == "message_update":
            assistant_event = payload.get("assistantMessageEvent", {})
            if assistant_event.get("type") == "text_delta":
                return {
                    "type": "agent_text_delta",
                    "session_id": session_id,
                    "delta": assistant_event.get("delta", ""),
                }
        return None
