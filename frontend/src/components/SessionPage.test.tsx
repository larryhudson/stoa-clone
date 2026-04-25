import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { SessionPage } from "./SessionPage";
import * as sessionCommandsApi from "../api/sessionCommands";
import * as sessionsApi from "../api/sessions";
import type { SessionEvent } from "../api/sessionEvents";

vi.mock("../api/sessionCommands", () => ({
  joinSession: vi.fn(),
  claimControl: vi.fn(),
  promptAgent: vi.fn(),
}));

vi.mock("../api/sessions", () => ({
  getSession: vi.fn(),
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
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(snapshot);

    renderWithQueryClient(<SessionPage sessionId="session-1" userId="user-1" />);

    await waitFor(() => {
      expect(screen.getByText("Fetched session output")).toBeInTheDocument();
    });
    expect(sessionCommandsApi.joinSession).toHaveBeenCalledWith("session-1", "user-1");
    expect(MockWebSocket.instances[0].url).toContain("user_id=user-1");
    expect(screen.getByText("Complete")).toBeInTheDocument();
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
