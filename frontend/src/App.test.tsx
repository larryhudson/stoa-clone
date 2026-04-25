import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";

import App from "./App";
import * as sessionCommandsApi from "./api/sessionCommands";
import * as sessionsApi from "./api/sessions";

vi.mock("./api/sessionCommands", () => ({
  createSession: vi.fn(),
  startSession: vi.fn(),
  joinSession: vi.fn(),
  claimControl: vi.fn(),
  promptAgent: vi.fn(),
  steerAgent: vi.fn(),
  abortAgent: vi.fn(),
  postChatMessage: vi.fn(),
  acceptPromptSuggestion: vi.fn(),
  dismissPromptSuggestion: vi.fn(),
}));

vi.mock("./api/sessions", () => ({
  getSession: vi.fn(),
  getWorkspaceReview: vi.fn(),
}));

class MockWebSocket extends EventTarget {
  constructor(public readonly url: string) {
    super();
  }

  close = vi.fn();
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("WebSocket", MockWebSocket);
    window.history.replaceState(null, "", "/");
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("creates and starts a session from the browser shell", async () => {
    const created = sessionSnapshot({ id: "session-created", status: "created" });
    const started = sessionSnapshot({ id: "session-created", status: "ready" });
    vi.mocked(sessionCommandsApi.createSession).mockResolvedValue(created);
    vi.mocked(sessionCommandsApi.startSession).mockResolvedValue(started);
    vi.mocked(sessionsApi.getSession).mockResolvedValue(started);
    vi.mocked(sessionsApi.getWorkspaceReview).mockResolvedValue({ changed_files: [], diff: "" });
    vi.mocked(sessionCommandsApi.joinSession).mockResolvedValue(started);

    renderWithQueryClient(<App />);

    fireEvent.change(screen.getByLabelText("Repository URL"), {
      target: { value: "https://github.com/example/repo.git" },
    });
    fireEvent.change(screen.getByLabelText("Branch"), {
      target: { value: "main" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create session" }));

    await waitFor(() => {
      expect(sessionCommandsApi.createSession).toHaveBeenCalledWith(
        "https://github.com/example/repo.git",
        "main",
      );
    });
    expect(sessionCommandsApi.startSession).toHaveBeenCalledWith("session-created");
    expect(await screen.findByText("Session: session-created | User: user-1")).toBeInTheDocument();
  });

  it("shows start failures in the browser shell", async () => {
    vi.mocked(sessionCommandsApi.createSession).mockResolvedValue(
      sessionSnapshot({ id: "session-created", status: "created" }),
    );
    vi.mocked(sessionCommandsApi.startSession).mockRejectedValue(
      new Error("Failed to start session"),
    );

    renderWithQueryClient(<App />);

    fireEvent.change(screen.getByLabelText("Repository URL"), {
      target: { value: "https://github.com/example/repo.git" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create session" }));

    expect(await screen.findByText("Failed to start session")).toBeInTheDocument();
    expect(screen.getByText("Session: none | User: user-1")).toBeInTheDocument();
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

function sessionSnapshot(overrides: Partial<Awaited<ReturnType<typeof sessionsApi.getSession>>>) {
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
