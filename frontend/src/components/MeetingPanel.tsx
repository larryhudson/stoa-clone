import type { SessionViewModel, WorkspaceReview } from "../lib/sessionTypes";

type MeetingPanelProps = {
  session: SessionViewModel;
  userId?: string;
  commandError?: string | null;
  isCommandPending?: boolean;
  onClaimControl?: () => void;
  onPromptAgent?: (text: string) => void;
  onSteerAgent?: (text: string) => void;
  onAbortAgent?: () => void;
  onPostChatMessage?: (body: string) => void;
  onAcceptSuggestion?: (suggestionId: string) => void;
  onDismissSuggestion?: (suggestionId: string) => void;
  workspaceReview?: WorkspaceReview | null;
};

const STATUS_LABELS: Record<SessionViewModel["agent_output_status"], string> = {
  empty: "Idle",
  pending: "Queued",
  streaming: "Streaming",
  complete: "Complete",
  failed: "Run failed",
};

export function MeetingPanel({
  session,
  userId,
  commandError,
  isCommandPending = false,
  onClaimControl,
  onPromptAgent,
  onSteerAgent,
  onAbortAgent,
  onPostChatMessage,
  onAcceptSuggestion,
  onDismissSuggestion,
  workspaceReview,
}: MeetingPanelProps) {
  const statusLabel = STATUS_LABELS[session.agent_output_status];
  const isAgentWorking =
    session.agent_status === "running" ||
    session.agent_output_status === "pending" ||
    session.agent_output_status === "streaming";
  const output =
    session.agent_output ||
    (isAgentWorking ? "Waiting for the first response..." : "No agent output yet.");
  const hasControl = userId !== undefined && session.controller_id === userId;
  const canClaimControl = userId !== undefined && session.controller_id !== userId;
  const canPrompt = hasControl && session.agent_session_id !== null && !isCommandPending;
  const canSteer = canPrompt && session.agent_status === "running";
  const pendingSuggestions = session.prompt_suggestions.filter(
    (suggestion) => suggestion.status === "pending",
  );
  const changedFileCount = workspaceReview?.changed_files.length ?? 0;
  const artifactStatus =
    session.agent_status === "running"
      ? "Agent working"
      : changedFileCount > 0
        ? "Ready for review"
        : "No changes yet";

  return (
    <section style={panelStyle}>
      <header style={headerStyle}>
        <div>
          <div style={eyebrowStyle}>Meeting Session</div>
          <h2 style={titleStyle}>Transcript to Diff</h2>
        </div>
        <span style={badgeStyle(session.agent_output_status)}>{statusLabel}</span>
      </header>

      <div style={controlBarStyle}>
        <div style={controlStatusStyle}>
          Controller: <strong>{session.controller_id ?? "none"}</strong>
        </div>
        <div style={controlActionsStyle}>
          {canSteer ? (
            <button
              type="button"
              onClick={onAbortAgent}
              disabled={isCommandPending || onAbortAgent === undefined}
              style={dangerButtonStyle}
            >
              Abort run
            </button>
          ) : null}
          {canClaimControl ? (
            <button
              type="button"
              onClick={onClaimControl}
              disabled={isCommandPending || onClaimControl === undefined}
              style={buttonStyle}
            >
              Claim control
            </button>
          ) : null}
        </div>
      </div>

      <div style={meetingGridStyle}>
        <section style={surfaceStyle}>
          <h3 style={sectionTitleStyle}>Chat</h3>
          <div aria-label="Meeting transcript" style={transcriptStyle}>
            {session.chat_messages.length ? (
              session.chat_messages.map((message) => (
                <article key={message.id} style={messageStyle}>
                  <strong>{message.author_id}</strong>
                  <p>{message.body}</p>
                </article>
              ))
            ) : (
              <p style={emptyStyle}>No meeting messages yet.</p>
            )}
          </div>

          <form
            style={chatFormStyle}
            onSubmit={(event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const input = new FormData(form).get("chat");
              if (typeof input === "string" && input.trim()) {
                onPostChatMessage?.(input.trim());
                form.reset();
              }
            }}
          >
            <textarea
              name="chat"
              aria-label="Meeting message"
              placeholder="Write a meeting message"
              disabled={isCommandPending || onPostChatMessage === undefined}
              style={promptInputStyle}
            />
            <button
              type="submit"
              disabled={isCommandPending || onPostChatMessage === undefined}
              style={buttonStyle}
            >
              Send message
            </button>
          </form>
        </section>

        <section style={surfaceStyle}>
          <h3 style={sectionTitleStyle}>Suggested Prompts</h3>
          {pendingSuggestions.length ? (
            <div style={suggestionsStyle}>
              {pendingSuggestions.map((suggestion) => (
                <article key={suggestion.id} style={suggestionStyle}>
                  <p style={suggestionTextStyle}>{suggestion.text}</p>
                  <p style={suggestionReasonStyle}>{suggestion.reason}</p>
                  <div style={controlActionsStyle}>
                    <button
                      type="button"
                      onClick={() => onAcceptSuggestion?.(suggestion.id)}
                      disabled={!hasControl || isCommandPending || onAcceptSuggestion === undefined}
                      style={buttonStyle}
                    >
                      Run suggestion
                    </button>
                    <button
                      type="button"
                      onClick={() => onDismissSuggestion?.(suggestion.id)}
                      disabled={
                        !hasControl || isCommandPending || onDismissSuggestion === undefined
                      }
                      style={secondaryButtonStyle}
                    >
                      Dismiss
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p style={emptyStyle}>No pending suggestions.</p>
          )}
        </section>
      </div>

      <form
        style={promptFormStyle}
        onSubmit={(event) => {
          event.preventDefault();
          const form = event.currentTarget;
          const input = new FormData(form).get("prompt");
          if (typeof input === "string" && input.trim()) {
            onPromptAgent?.(input.trim());
            form.reset();
          }
        }}
      >
        <textarea
          name="prompt"
          aria-label="Agent prompt"
          placeholder={hasControl ? "Send a prompt to the agent" : "Claim control to prompt"}
          disabled={!canPrompt}
          style={promptInputStyle}
        />
        <button
          type="submit"
          disabled={!canPrompt || onPromptAgent === undefined}
          style={buttonStyle}
        >
          Send prompt
        </button>
      </form>

      {canSteer ? (
        <form
          style={promptFormStyle}
          onSubmit={(event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const input = new FormData(form).get("steer");
            if (typeof input === "string" && input.trim()) {
              onSteerAgent?.(input.trim());
              form.reset();
            }
          }}
        >
          <textarea
            name="steer"
            aria-label="Steer agent"
            placeholder="Steer the running agent"
            disabled={!canSteer}
            style={promptInputStyle}
          />
          <button
            type="submit"
            disabled={!canSteer || onSteerAgent === undefined}
            style={buttonStyle}
          >
            Send steer
          </button>
        </form>
      ) : null}

      {commandError ? (
        <div role="alert" style={errorStyle}>
          {commandError}
        </div>
      ) : null}

      {session.agent_output_error ? (
        <div role="alert" style={errorStyle}>
          <strong>Runtime error</strong>
          <div>{session.agent_output_error}</div>
        </div>
      ) : null}

      {isAgentWorking && !session.agent_output ? (
        <div role="status" style={workingStyle}>
          <strong>Agent is working</strong>
          <span>Waiting for the first response...</span>
        </div>
      ) : null}

      <pre style={outputStyle}>{output}</pre>

      <section style={artifactStyle}>
        <div>
          <h3 style={sectionTitleStyle}>Session Artifact</h3>
          <p style={emptyStyle}>{artifactStatus}</p>
        </div>
        <div style={artifactStatsStyle}>
          <span style={artifactStatStyle}>
            {pluralize(session.chat_messages.length, "message")}
          </span>
          <span style={artifactStatStyle}>{pluralize(changedFileCount, "changed file")}</span>
          <span style={artifactStatStyle}>
            {pluralize(session.prompt_suggestions.length, "suggestion")}
          </span>
        </div>
      </section>

      <section style={surfaceStyle}>
        <h3 style={sectionTitleStyle}>Reviewable Diff</h3>
        {workspaceReview?.changed_files.length ? (
          <>
            <div style={changedFilesStyle}>
              {workspaceReview.changed_files.map((file) => (
                <span key={file} style={fileBadgeStyle}>
                  {file}
                </span>
              ))}
            </div>
            <pre style={diffStyle}>{workspaceReview.diff}</pre>
          </>
        ) : (
          <p style={emptyStyle}>No workspace changes yet.</p>
        )}
      </section>
    </section>
  );
}

function pluralize(count: number, noun: string): string {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

const panelStyle: React.CSSProperties = {
  display: "grid",
  gap: "1rem",
  padding: "1.25rem",
  borderRadius: "24px",
  border: "1px solid #d7d0c4",
  background: "linear-gradient(180deg, #f7f3ea 0%, #efe6d6 100%)",
  boxShadow: "0 20px 50px rgba(73, 54, 28, 0.12)",
};

const controlBarStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "0.75rem",
  flexWrap: "wrap",
};

const controlStatusStyle: React.CSSProperties = {
  color: "#56452f",
  fontSize: "0.9rem",
};

const controlActionsStyle: React.CSSProperties = {
  display: "flex",
  gap: "0.5rem",
  flexWrap: "wrap",
};

const meetingGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1.2fr) minmax(18rem, 0.8fr)",
  gap: "1rem",
};

const surfaceStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.75rem",
  minWidth: 0,
};

const sectionTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "1rem",
  color: "#2f2416",
};

const transcriptStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.65rem",
  minHeight: "12rem",
  maxHeight: "22rem",
  overflow: "auto",
  padding: "0.75rem",
  border: "1px solid #d7d0c4",
  borderRadius: "14px",
  background: "#fffaf1",
};

const messageStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.2rem",
  color: "#2f2416",
};

const chatFormStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.75rem",
};

const suggestionsStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.75rem",
};

const suggestionStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.65rem",
  padding: "0.85rem",
  border: "1px solid #d7d0c4",
  borderRadius: "8px",
  background: "#fffaf1",
};

const suggestionTextStyle: React.CSSProperties = {
  margin: 0,
  color: "#2f2416",
  fontWeight: 700,
};

const suggestionReasonStyle: React.CSSProperties = {
  margin: 0,
  color: "#6c5a40",
  fontSize: "0.9rem",
};

const emptyStyle: React.CSSProperties = {
  margin: 0,
  color: "#6c5a40",
};

const promptFormStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(0, 1fr) auto",
  gap: "0.75rem",
  alignItems: "stretch",
};

const promptInputStyle: React.CSSProperties = {
  minHeight: "4.5rem",
  resize: "vertical",
  borderRadius: "14px",
  border: "1px solid #cfc3b1",
  padding: "0.75rem",
  font: "inherit",
  color: "#2f2416",
  background: "#fffaf1",
};

const buttonStyle: React.CSSProperties = {
  border: "1px solid #7d5d32",
  borderRadius: "12px",
  padding: "0.7rem 0.9rem",
  font: "inherit",
  fontWeight: 700,
  color: "#fffaf1",
  background: "#6f4b22",
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  color: "#563d20",
  background: "#f2ddbc",
};

const dangerButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  borderColor: "#8d3a34",
  background: "#8d3a34",
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "start",
  justifyContent: "space-between",
  gap: "1rem",
};

const eyebrowStyle: React.CSSProperties = {
  fontSize: "0.7rem",
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  color: "#8a6f45",
};

const titleStyle: React.CSSProperties = {
  margin: "0.2rem 0 0",
  fontSize: "1.35rem",
  lineHeight: 1.1,
  color: "#2f2416",
};

function badgeStyle(status: SessionViewModel["agent_output_status"]): React.CSSProperties {
  const colors: Record<SessionViewModel["agent_output_status"], { bg: string; fg: string }> = {
    empty: { bg: "#e7e0d2", fg: "#5e4d36" },
    pending: { bg: "#ece3b5", fg: "#64511e" },
    streaming: { bg: "#cde7db", fg: "#174b35" },
    complete: { bg: "#d8e5f4", fg: "#22415f" },
    failed: { bg: "#f2c8c5", fg: "#6f1f1b" },
  };

  return {
    alignSelf: "start",
    padding: "0.45rem 0.8rem",
    borderRadius: "999px",
    fontSize: "0.8rem",
    fontWeight: 700,
    background: colors[status].bg,
    color: colors[status].fg,
  };
}

const errorStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.35rem",
  padding: "0.85rem 1rem",
  borderRadius: "16px",
  background: "#fff1ef",
  color: "#6f1f1b",
  border: "1px solid #e7a5a0",
};

const workingStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.65rem",
  padding: "0.85rem 1rem",
  borderRadius: "14px",
  background: "#e6f3ed",
  color: "#174b35",
  border: "1px solid #9ccbb8",
};

const artifactStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "1rem",
  flexWrap: "wrap",
  padding: "1rem",
  border: "1px solid #d7d0c4",
  borderRadius: "8px",
  background: "#fffaf1",
};

const artifactStatsStyle: React.CSSProperties = {
  display: "flex",
  gap: "0.5rem",
  flexWrap: "wrap",
};

const artifactStatStyle: React.CSSProperties = {
  padding: "0.35rem 0.55rem",
  borderRadius: "8px",
  background: "#ece3b5",
  color: "#64511e",
  fontSize: "0.85rem",
  fontWeight: 700,
};

const outputStyle: React.CSSProperties = {
  margin: 0,
  minHeight: "14rem",
  padding: "1rem",
  borderRadius: "18px",
  background: "#221a10",
  color: "#f7f2e8",
  fontFamily: '"Iosevka", "SFMono-Regular", monospace',
  fontSize: "0.95rem",
  lineHeight: 1.5,
  whiteSpace: "pre-wrap",
};

const changedFilesStyle: React.CSSProperties = {
  display: "flex",
  gap: "0.5rem",
  flexWrap: "wrap",
};

const fileBadgeStyle: React.CSSProperties = {
  padding: "0.35rem 0.55rem",
  borderRadius: "8px",
  background: "#d8e5f4",
  color: "#22415f",
  fontSize: "0.85rem",
  fontWeight: 700,
};

const diffStyle: React.CSSProperties = {
  ...outputStyle,
  minHeight: "10rem",
};
