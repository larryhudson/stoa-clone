import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { SessionPage } from "./SessionPage";
import * as sessionCommandsApi from "../api/sessionCommands";
import * as sessionsApi from "../api/sessions";
import type { SessionEvent } from "../api/sessionEvents";

vi.mock("../api/sessionCommands", () => ({
  joinSession: vi.fn(),
  abortAgent: vi.fn(),
  acceptPromptSuggestion: vi.fn(),
  claimControl: vi.fn(),
  dismissPromptSuggestion: vi.fn(),
  promptAgent: vi.fn(),
  postChatMessage: vi.fn(),
  steerAgent: vi.fn(),
}));

vi.mock("../api/sessions", () => ({
  getSession: vi.fn(),
  getWorkspaceReview: vi.fn(),
}));

class MockWebSocket extends EventTarget {
  static instances: MockWebSocket[] = [];

  constructor(public readonly url: string) {
    super();
    MockWebSocket.instances.push(this);
  }

  close = vi.fn();

  receive(event: SessionEvent) {
    this.dispatchEvent(new MessageEvent("message", { data: JSON.stringify(event) }));
  }

  disconnect() {
    this.dispatchEvent(new CloseEvent("close"));
  }
}

describe("SessionPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("shows a loading state while fetching the session snapshot", () => {
    vi.mocked(sessionsApi.getSession).mockReturnValue(new Promise(() => undefined));

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    expect(screen.getByText("Loading session...")).toBeInTheDocument();
  });

  it("renders the fetched session in the agent panel", async () => {
    const snapshot = sessionSnapshot({
      agent_output: "Fetched session output",
      agent_output_status: "complete",
      controller_id: "user-1",
      viewers: ["user-1"],
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(snapshot);
    vi.mocked(sessionsApi.getWorkspaceReview).mockResolvedValue({
      changed_files: ["README.md"],
      diff: "diff --git a/README.md b/README.md",
    });
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(snapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByText("Fetched session output")).toBeInTheDocument();
    });
    expect(sessionCommandsApi.joinSession).toHaveBeenCalledWith("session-1", "user-1");
    expect(MockWebSocket.instances[0].url).toContain("user_id=user-1");
    expect(screen.getByText("Complete")).toBeInTheDocument();
    expect(screen.getByText("README.md")).toBeInTheDocument();
  });

  it("applies session events received over websocket", async () => {
    const snapshot = sessionSnapshot();
    vi.mocked(sessionsApi.getSession).mockResolvedValue(snapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(snapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    MockWebSocket.instances[0].receive({
      type: "agent_text_delta",
      session_id: "session-1",
      delta: "Live output",
    });

    await waitFor(() => {
      expect(screen.getByText("Live output")).toBeInTheDocument();
    });
    expect(screen.getByText("Streaming")).toBeInTheDocument();
  });

  it("refreshes the workspace review when an agent run finishes", async () => {
    const snapshot = sessionSnapshot({
      agent_status: "running",
      agent_output_status: "streaming",
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(snapshot);
    vi.mocked(sessionsApi.getWorkspaceReview)
      .mockResolvedValueOnce({
        changed_files: [],
        diff: "",
      })
      .mockResolvedValueOnce({
        changed_files: ["README.md"],
        diff: "diff --git a/README.md b/README.md",
      });
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(snapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });

    MockWebSocket.instances[0].receive({
      type: "agent_run_finished",
      session_id: "session-1",
    });

    await waitFor(() => {
      expect(sessionsApi.getWorkspaceReview).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText("README.md")).toBeInTheDocument();
  });

  it("renders chat messages and accepts suggested prompts as the controller", async () => {
    const controllerSnapshot = sessionSnapshot({
      controller_id: "user-1",
      viewers: ["user-1"],
      chat_messages: [
        {
          id: "chat-1",
          author_id: "user-1",
          body: "Let's add meeting chat.",
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
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(controllerSnapshot);
    vi.mocked(sessionsApi.getWorkspaceReview).mockResolvedValue({
      changed_files: [],
      diff: "",
    });
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(controllerSnapshot);
    vi.mocked(sessionCommandsApi.acceptPromptSuggestion).mockResolvedValue(
      sessionSnapshot({
        ...controllerSnapshot,
        agent_status: "running",
        agent_output_status: "pending",
        prompt_suggestions: [
          {
            ...controllerSnapshot.prompt_suggestions[0],
            status: "accepted",
          },
        ],
      }),
    );

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByText("Let's add meeting chat.")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Run suggestion" }));

    await waitFor(() => {
      expect(sessionCommandsApi.acceptPromptSuggestion).toHaveBeenCalledWith(
        "session-1",
        "suggestion-1",
        "user-1",
      );
    });
  });

  it("posts meeting chat messages through the session page", async () => {
    const snapshot = sessionSnapshot({ viewers: ["user-1"] });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(snapshot);
    vi.mocked(sessionsApi.getWorkspaceReview).mockResolvedValue({
      changed_files: [],
      diff: "",
    });
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(snapshot);
    vi.mocked(sessionCommandsApi.postChatMessage).mockResolvedValue({
      id: "chat-1",
      author_id: "user-1",
      body: "Let's add meeting chat.",
      created_at: 1,
    });

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Meeting message")).toBeEnabled();
    });

    fireEvent.change(screen.getByLabelText("Meeting message"), {
      target: { value: "Let's add meeting chat." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send message" }));

    await waitFor(() => {
      expect(sessionCommandsApi.postChatMessage).toHaveBeenCalledWith(
        "session-1",
        "user-1",
        "Let's add meeting chat.",
      );
    });
  });

  it("refreshes the session snapshot before reconnecting after websocket disconnect", async () => {
    vi.mocked(sessionsApi.getSession)
      .mockResolvedValueOnce(
        sessionSnapshot({ agent_output: "Initial output", agent_output_status: "complete" }),
      )
      .mockResolvedValueOnce(
        sessionSnapshot({ agent_output: "Refreshed output", agent_output_status: "complete" }),
      );
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(
      sessionSnapshot({ agent_output: "Initial output", agent_output_status: "complete" }),
    );

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByText("Initial output")).toBeInTheDocument();
    });

    vi.useFakeTimers();
    MockWebSocket.instances[0].disconnect();
    await vi.advanceTimersByTimeAsync(500);
    vi.useRealTimers();

    await waitFor(() => {
      expect(screen.getByText("Refreshed output")).toBeInTheDocument();
    });
    expect(MockWebSocket.instances).toHaveLength(2);
  });

  it("claims control and enables prompting from the returned snapshot", async () => {
    vi.mocked(sessionsApi.getSession).mockResolvedValue(sessionSnapshot());
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(sessionSnapshot());
    vi.mocked(sessionCommandsApi.claimControl).mockResolvedValue(
      sessionSnapshot({ controller_id: "user-1", viewers: ["user-1"] }),
    );

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Claim control" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Claim control" }));

    await waitFor(() => {
      expect(sessionCommandsApi.claimControl).toHaveBeenCalledWith("session-1", "user-1");
    });
    expect(await screen.findByText("user-1")).toBeInTheDocument();
    expect(screen.getByLabelText("Agent prompt")).toBeEnabled();
  });

  it("sends prompts as the current controller", async () => {
    const controllerSnapshot = sessionSnapshot({ controller_id: "user-1", viewers: ["user-1"] });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(controllerSnapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(controllerSnapshot);
    vi.mocked(sessionCommandsApi.promptAgent).mockResolvedValue(
      sessionSnapshot({
        agent_status: "running",
        agent_output_status: "pending",
        controller_id: "user-1",
        viewers: ["user-1"],
      }),
    );

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Agent prompt")).toBeEnabled();
    });

    fireEvent.change(screen.getByLabelText("Agent prompt"), {
      target: { value: "Summarize this repository" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send prompt" }));

    await waitFor(() => {
      expect(sessionCommandsApi.promptAgent).toHaveBeenCalledWith(
        "session-1",
        "user-1",
        "Summarize this repository",
      );
    });
    expect(await screen.findByText("Queued")).toBeInTheDocument();
  });

  it("steers a running agent as the current controller", async () => {
    const runningSnapshot = sessionSnapshot({
      agent_status: "running",
      agent_output_status: "streaming",
      controller_id: "user-1",
      viewers: ["user-1"],
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.steerAgent).mockResolvedValue(runningSnapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Steer agent")).toBeEnabled();
    });

    fireEvent.change(screen.getByLabelText("Steer agent"), {
      target: { value: "Focus on tests" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send steer" }));

    await waitFor(() => {
      expect(sessionCommandsApi.steerAgent).toHaveBeenCalledWith(
        "session-1",
        "user-1",
        "Focus on tests",
      );
    });
  });

  it("aborts a running agent as the current controller", async () => {
    const runningSnapshot = sessionSnapshot({
      agent_status: "running",
      agent_output_status: "streaming",
      controller_id: "user-1",
      viewers: ["user-1"],
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.abortAgent).mockResolvedValue(
      sessionSnapshot({
        agent_status: "idle",
        agent_output_status: "complete",
        controller_id: "user-1",
        viewers: ["user-1"],
      }),
    );

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Abort run" })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Abort run" }));

    await waitFor(() => {
      expect(sessionCommandsApi.abortAgent).toHaveBeenCalledWith("session-1", "user-1");
    });
  });

  it("does not show steer or abort controls to non-controllers", async () => {
    const runningSnapshot = sessionSnapshot({
      agent_status: "running",
      agent_output_status: "streaming",
      controller_id: "user-2",
      viewers: ["user-1", "user-2"],
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(runningSnapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByText("user-2")).toBeInTheDocument();
    });

    expect(screen.queryByLabelText("Steer agent")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Abort run" })).not.toBeInTheDocument();
  });

  it("shows command errors from steer failures", async () => {
    const runningSnapshot = sessionSnapshot({
      agent_status: "running",
      agent_output_status: "streaming",
      controller_id: "user-1",
      viewers: ["user-1"],
    });
    vi.mocked(sessionsApi.getSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(runningSnapshot);
    vi.mocked(sessionCommandsApi.steerAgent).mockRejectedValue(new Error("Failed to steer agent"));

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Steer agent")).toBeEnabled();
    });

    fireEvent.change(screen.getByLabelText("Steer agent"), {
      target: { value: "Focus on tests" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send steer" }));

    expect(await screen.findByText("Failed to steer agent")).toBeInTheDocument();
  });
});

function sessionSnapshot(
  overrides: Partial<Awaited<ReturnType<typeof sessionsApi.getSession>>> = {},
): Awaited<ReturnType<typeof sessionsApi.getSession>> {
  return {
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
    controller_id: null,
    viewers: [],
    chat_messages: [],
    prompt_suggestions: [],
    ...overrides,
  };
}

function renderWithQueryClient(element: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{element}</QueryClientProvider>);
}
