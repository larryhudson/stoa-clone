import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import { AgentPanel } from "./AgentPanel";

describe("AgentPanel", () => {
  it("shows a streaming indicator with the live output buffer", () => {
    render(
      <AgentPanel
        session={{
          id: "session-1",
          repo_url: "https://github.com/example/repo.git",
          branch: "main",
          status: "ready",
          workspace_path: "/tmp/session-1",
          agent_session_id: "agent-session-1",
          agent_status: "running",
          agent_output: "Hello world",
          agent_output_status: "streaming",
          agent_output_error: null,
          controller_id: "user-1",
          viewers: ["user-1"],
        }}
      />,
    );

    expect(screen.getByText("Streaming")).toBeInTheDocument();
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("shows the runtime error when the current run fails", () => {
    render(
      <AgentPanel
        session={{
          id: "session-1",
          repo_url: "https://github.com/example/repo.git",
          branch: "main",
          status: "ready",
          workspace_path: "/tmp/session-1",
          agent_session_id: "agent-session-1",
          agent_status: "failed",
          agent_output: "Partial answer",
          agent_output_status: "failed",
          agent_output_error: "No API key found",
          controller_id: "user-1",
          viewers: ["user-1"],
        }}
      />,
    );

    expect(screen.getByText("Run failed")).toBeInTheDocument();
    expect(screen.getByText("No API key found")).toBeInTheDocument();
    expect(screen.getByText("Partial answer")).toBeInTheDocument();
  });
});
