export type SessionStatus = "created" | "starting" | "ready" | "failed";
export type AgentStatus = "not_started" | "starting" | "idle" | "running" | "failed";
export type AgentOutputStatus = "empty" | "pending" | "streaming" | "complete" | "failed";
export type PromptSuggestionStatus = "pending" | "accepted" | "dismissed";

export type ChatMessage = {
  id: string;
  author_id: string;
  body: string;
  created_at: number;
};

export type PromptSuggestion = {
  id: string;
  text: string;
  reason: string;
  source_message_ids: string[];
  status: PromptSuggestionStatus;
  created_at: number;
};

export type WorkspaceReview = {
  changed_files: string[];
  diff: string;
};

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
  chat_messages: ChatMessage[];
  prompt_suggestions: PromptSuggestion[];
};

export type { SessionEvent } from "../api/sessionEvents";
