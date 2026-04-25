import type { SessionViewModel } from "../lib/sessionTypes";

type AgentPanelProps = {
  session: SessionViewModel;
  userId?: string;
  commandError?: string | null;
  isCommandPending?: boolean;
  onClaimControl?: () => void;
  onPromptAgent?: (text: string) => void;
  onSteerAgent?: (text: string) => void;
  onAbortAgent?: () => void;
};

const STATUS_LABELS: Record<SessionViewModel["agent_output_status"], string> = {
  empty: "Idle",
  pending: "Queued",
  streaming: "Streaming",
  complete: "Complete",
  failed: "Run failed",
};

export function AgentPanel({
  session,
  userId,
  commandError,
  isCommandPending = false,
  onClaimControl,
  onPromptAgent,
  onSteerAgent,
  onAbortAgent,
}: AgentPanelProps) {
  const statusLabel = STATUS_LABELS[session.agent_output_status];
  const output = session.agent_output || "No agent output yet.";
  const hasControl = userId !== undefined && session.controller_id === userId;
  const canClaimControl = userId !== undefined && session.controller_id !== userId;
  const canPrompt = hasControl && session.agent_session_id !== null && !isCommandPending;
  const canSteer = canPrompt && session.agent_status === "running";

  return (
    <section style={panelStyle}>
      <header style={headerStyle}>
        <div>
          <div style={eyebrowStyle}>Agent Output</div>
          <h2 style={titleStyle}>Live Session Transcript</h2>
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

      <pre style={outputStyle}>{output}</pre>
    </section>
  );
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
