import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import { SessionPage } from "./SessionPage";
import * as sessionsApi from "../api/sessions";
import type { SessionEvent } from "../api/sessionEvents";

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
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("shows a loading state while fetching the session snapshot", () => {
    vi.mocked(sessionsApi.getSession).mockReturnValue(new Promise(() => undefined));

    renderWithQueryClient(<SessionPage sessionId="session-1" />);

    expect(screen.getByText("Loading session...")).toBeInTheDocument();
  });

  it("renders the fetched session in the agent panel", async () => {
    vi.mocked(sessionsApi.getSession).mockResolvedValue({
      id: "session-1",
      repo_url: "https://github.com/example/repo.git",
      branch: "main",
      status: "ready",
      workspace_path: "/tmp/session-1",
      agent_session_id: "agent-session-1",
      agent_status: "idle",
      agent_output: "Fetched session output",
      agent_output_status: "complete",
      agent_output_error: null,
      controller_id: "user-1",
      viewers: ["user-1"],
    });

    renderWithQueryClient(<SessionPage sessionId="session-1" />);

    await waitFor(() => {
      expect(screen.getByText("Fetched session output")).toBeInTheDocument();
    });
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("applies session events received over websocket", async () => {
    vi.mocked(sessionsApi.getSession).mockResolvedValue({
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
    });

    renderWithQueryClient(<SessionPage sessionId="session-1" />);

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
      .mockResolvedValueOnce({
        id: "session-1",
        repo_url: "https://github.com/example/repo.git",
        branch: "main",
        status: "ready",
        workspace_path: "/tmp/session-1",
        agent_session_id: "agent-session-1",
        agent_status: "idle",
        agent_output: "Initial output",
        agent_output_status: "complete",
        agent_output_error: null,
        controller_id: null,
        viewers: [],
      })
      .mockResolvedValueOnce({
        id: "session-1",
        repo_url: "https://github.com/example/repo.git",
        branch: "main",
        status: "ready",
        workspace_path: "/tmp/session-1",
        agent_session_id: "agent-session-1",
        agent_status: "idle",
        agent_output: "Refreshed output",
        agent_output_status: "complete",
        agent_output_error: null,
        controller_id: null,
        viewers: [],
      });

    renderWithQueryClient(<SessionPage sessionId="session-1" />);

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
});

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
