export type SessionStatus = "created" | "starting" | "ready" | "failed";
export type AgentStatus = "not_started" | "starting" | "idle" | "running" | "failed";
export type AgentOutputStatus = "empty" | "pending" | "streaming" | "complete" | "failed";

export type SessionViewModel = {
  id: string;
  repo_url: string;
  branch: string;
  status: SessionStatus;
  workspace_path: string | null;
  agent_session_id: string | null;
  agent_status: AgentStatus;
  agent_output: string;
  agent_output_status: AgentOutputStatus;
  agent_output_error: string | null;
  controller_id: string | null;
  viewers: string[];
};

export type { SessionEvent } from "../api/sessionEvents";
