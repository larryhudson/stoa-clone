import type { SessionEvent, SessionViewModel } from "./sessionTypes";

type SessionSeed = Pick<SessionViewModel, "id" | "repo_url" | "branch"> & Partial<SessionViewModel>;

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

export function applySessionEvent(state: SessionViewModel, event: SessionEvent): SessionViewModel {
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

    case "session_started":
      return {
        ...state,
        status: "ready",
        workspace_path: event.workspace_path,
        agent_session_id: event.agent_session_id,
        agent_status: "idle",
      };

    case "session_failed":
      return {
        ...state,
        status: "failed",
        agent_status: "failed",
        agent_output_status: "failed",
        agent_output_error: event.error,
      };

    case "control_claimed":
      return {
        ...state,
        controller_id: event.user_id,
        viewers: withViewer(state.viewers, event.user_id),
      };

    case "control_released":
      return state.controller_id === event.user_id ? { ...state, controller_id: null } : state;

    case "viewer_joined":
      return {
        ...state,
        viewers: withViewer(state.viewers, event.user_id),
      };

    case "viewer_left":
      return {
        ...state,
        controller_id: state.controller_id === event.user_id ? null : state.controller_id,
        viewers: state.viewers.filter((viewer) => viewer !== event.user_id),
      };

    case "agent_steered":
    case "agent_aborted":
    case "file_edited":
    case "note_added":
      return state;
  }
}

function withViewer(viewers: string[], userId: string): string[] {
  return viewers.includes(userId) ? viewers : [...viewers, userId].sort();
}
