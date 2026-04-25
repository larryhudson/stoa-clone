import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vite-plus/test";

import { SessionPage } from "./SessionPage";
import * as sessionsApi from "../api/sessions";

vi.mock("../api/sessions", () => ({
  getSession: vi.fn(),
}));

describe("SessionPage", () => {
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
