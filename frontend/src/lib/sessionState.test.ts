import { describe, expect, it } from "vite-plus/test";

import { applySessionEvent, createSessionState } from "./sessionState";

describe("sessionState", () => {
  it("resets output and marks it pending when a prompt is submitted", () => {
    const initial = {
      ...createSessionState({
        id: "session-1",
        repo_url: "https://github.com/example/repo.git",
        branch: "main",
      }),
      controller_id: "user-1",
      agent_output: "Old output",
      agent_output_status: "complete" as const,
      agent_status: "idle" as const,
    };

    const updated = applySessionEvent(initial, {
      type: "agent_prompt_submitted",
      session_id: "session-1",
      user_id: "user-1",
      text: "Summarize this repository",
    });

    expect(updated.agent_output).toBe("");
    expect(updated.agent_output_status).toBe("pending");
    expect(updated.agent_output_error).toBeNull();
    expect(updated.agent_status).toBe("running");
  });

  it("accumulates text deltas and marks the output streaming", () => {
    const initial = createSessionState({
      id: "session-1",
      repo_url: "https://github.com/example/repo.git",
      branch: "main",
    });

    const streaming = applySessionEvent(initial, {
      type: "agent_run_started",
      session_id: "session-1",
    });
    const updated = applySessionEvent(streaming, {
      type: "agent_text_delta",
      session_id: "session-1",
      delta: "Hello",
    });

    expect(updated.agent_output).toBe("Hello");
    expect(updated.agent_output_status).toBe("streaming");
    expect(updated.agent_status).toBe("running");
  });

  it("marks a failed run without dropping prior output", () => {
    const initial = {
      ...createSessionState({
        id: "session-1",
        repo_url: "https://github.com/example/repo.git",
        branch: "main",
      }),
      agent_output: "Partial answer",
      agent_output_status: "streaming" as const,
      agent_status: "running" as const,
    };

    const updated = applySessionEvent(initial, {
      type: "agent_run_failed",
      session_id: "session-1",
      command: "prompt",
      error: "No API key found",
    });

    expect(updated.agent_output).toBe("Partial answer");
    expect(updated.agent_output_status).toBe("failed");
    expect(updated.agent_output_error).toBe("No API key found");
    expect(updated.agent_status).toBe("failed");
  });
});
