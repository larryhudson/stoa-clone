import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import { MeetingPanel } from "./MeetingPanel";

describe("MeetingPanel", () => {
  it("shows a streaming indicator with the live output buffer", () => {
    render(
      <MeetingPanel
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
          chat_messages: [],
          prompt_suggestions: [],
        }}
      />,
    );

    expect(screen.getByText("Streaming")).toBeInTheDocument();
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("shows an active working state before the first agent output arrives", () => {
    render(
      <MeetingPanel
        session={{
          id: "session-1",
          repo_url: "https://github.com/example/repo.git",
          branch: "main",
          status: "ready",
          workspace_path: "/tmp/session-1",
          agent_session_id: "agent-session-1",
          agent_status: "running",
          agent_output: "",
          agent_output_status: "streaming",
          agent_output_error: null,
          controller_id: "user-1",
          viewers: ["user-1"],
          chat_messages: [],
          prompt_suggestions: [],
        }}
      />,
    );

    expect(screen.getByText("Agent is working")).toBeInTheDocument();
    expect(screen.getAllByText("Waiting for the first response...")).toHaveLength(2);
    expect(screen.queryByText("No agent output yet.")).not.toBeInTheDocument();
  });

  it("shows the runtime error when the current run fails", () => {
    render(
      <MeetingPanel
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
          chat_messages: [],
          prompt_suggestions: [],
        }}
      />,
    );

    expect(screen.getByText("Run failed")).toBeInTheDocument();
    expect(screen.getByText("No API key found")).toBeInTheDocument();
    expect(screen.getByText("Partial answer")).toBeInTheDocument();
  });

  it("shows meeting chat, pending suggestions, and reviewable diff", () => {
    render(
      <MeetingPanel
        userId="user-1"
        session={{
          id: "session-1",
          repo_url: "https://github.com/example/repo.git",
          branch: "main",
          status: "ready",
          workspace_path: "/tmp/session-1",
          agent_session_id: "agent-session-1",
          agent_status: "idle",
          agent_output: "",
          agent_output_status: "empty",
          agent_output_error: null,
          controller_id: "user-1",
          viewers: ["user-1"],
          chat_messages: [
            {
              id: "chat-1",
              author_id: "user-1",
              body: "Let's build meeting chat.",
              created_at: 1,
            },
          ],
          prompt_suggestions: [
            {
              id: "suggestion-1",
              text: "Add hello world to the README.",
              reason: "A meeting message described implementation intent.",
              source_message_ids: ["chat-1"],
              status: "pending",
              created_at: 2,
            },
          ],
        }}
        workspaceReview={{
          changed_files: ["README.md"],
          diff: "diff --git a/README.md b/README.md",
        }}
      />,
    );

    expect(screen.getByText("Let's build meeting chat.")).toBeInTheDocument();
    expect(screen.getByText("Add hello world to the README.")).toBeInTheDocument();
    expect(screen.getByText("README.md")).toBeInTheDocument();
    expect(screen.getByText("diff --git a/README.md b/README.md")).toBeInTheDocument();
    expect(screen.getAllByText("Session Artifact").length).toBeGreaterThan(0);
    expect(screen.getByText("1 message")).toBeInTheDocument();
    expect(screen.getByText("1 changed file")).toBeInTheDocument();
    expect(screen.getByText("Ready for review")).toBeInTheDocument();
  });
});
