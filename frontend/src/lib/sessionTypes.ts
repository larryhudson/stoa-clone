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

export type SessionEvent =
  | { type: "agent_prompt_submitted"; session_id: string; user_id: string; text: string }
  | { type: "agent_run_started"; session_id: string }
  | { type: "agent_text_delta"; session_id: string; delta: string }
  | { type: "agent_run_finished"; session_id: string }
  | { type: "agent_run_failed"; session_id: string; command?: string; error: string };
