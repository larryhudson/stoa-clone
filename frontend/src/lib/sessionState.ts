import type { SessionEvent, SessionViewModel } from "./sessionTypes";

type SessionSeed = Pick<SessionViewModel, "id" | "repo_url" | "branch"> &
  Partial<SessionViewModel>;

export function createSessionState(seed: SessionSeed): SessionViewModel {
  return {
    id: seed.id,
    repo_url: seed.repo_url,
    branch: seed.branch,
    status: seed.status ?? "created",
    workspace_path: seed.workspace_path ?? null,
    agent_session_id: seed.agent_session_id ?? null,
    agent_status: seed.agent_status ?? "not_started",
    agent_output: seed.agent_output ?? "",
    agent_output_status: seed.agent_output_status ?? "empty",
    agent_output_error: seed.agent_output_error ?? null,
    controller_id: seed.controller_id ?? null,
    viewers: seed.viewers ?? [],
  };
}

export function applySessionEvent(
  state: SessionViewModel,
  event: SessionEvent,
): SessionViewModel {
  switch (event.type) {
    case "agent_prompt_submitted":
      return {
        ...state,
        agent_status: "running",
        agent_output: "",
        agent_output_status: "pending",
        agent_output_error: null,
      };

    case "agent_run_started":
      return {
        ...state,
        agent_status: "running",
        agent_output: "",
        agent_output_status: "streaming",
        agent_output_error: null,
      };

    case "agent_text_delta":
      return {
        ...state,
        agent_status: "running",
        agent_output: state.agent_output + event.delta,
        agent_output_status: "streaming",
      };

    case "agent_run_finished":
      return {
        ...state,
        agent_status: "idle",
        agent_output_status: "complete",
      };

    case "agent_run_failed":
      return {
        ...state,
        agent_status: "failed",
        agent_output_status: "failed",
        agent_output_error: event.error,
      };
  }
}
