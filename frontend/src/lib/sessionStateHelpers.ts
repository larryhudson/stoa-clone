import { createSessionState } from "./sessionState";
import type {
  AgentOutputStatus,
  AgentStatus,
  SessionStatus,
  SessionViewModel,
} from "./sessionTypes";

type SessionSnapshot = {
  id: string;
  repo_url: string;
  branch: string;
  status: string;
  workspace_path: string | null;
  agent_session_id: string | null;
  agent_status: string;
  agent_output: string;
  agent_output_status: string;
  agent_output_error: string | null;
  controller_id: string | null;
  viewers: string[];
};

export function sessionFromSnapshot(snapshot: SessionSnapshot): SessionViewModel {
  return createSessionState({
    ...snapshot,
    status: asSessionStatus(snapshot.status),
    agent_status: asAgentStatus(snapshot.agent_status),
    agent_output_status: asAgentOutputStatus(snapshot.agent_output_status),
  });
}

function asSessionStatus(value: string): SessionStatus {
  if (value === "created" || value === "starting" || value === "ready" || value === "failed") {
    return value;
  }
  throw new Error(`Unexpected session status: ${value}`);
}

function asAgentStatus(value: string): AgentStatus {
  if (
    value === "not_started" ||
    value === "starting" ||
    value === "idle" ||
    value === "running" ||
    value === "failed"
  ) {
    return value;
  }
  throw new Error(`Unexpected agent status: ${value}`);
}

function asAgentOutputStatus(value: string): AgentOutputStatus {
  if (
    value === "empty" ||
    value === "pending" ||
    value === "streaming" ||
    value === "complete" ||
    value === "failed"
  ) {
    return value;
  }
  throw new Error(`Unexpected agent output status: ${value}`);
}
