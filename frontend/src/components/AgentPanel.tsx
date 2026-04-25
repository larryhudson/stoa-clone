import type { SessionViewModel } from "../lib/sessionTypes";

type AgentPanelProps = {
  session: SessionViewModel;
};

const STATUS_LABELS: Record<SessionViewModel["agent_output_status"], string> = {
  empty: "Idle",
  pending: "Queued",
  streaming: "Streaming",
  complete: "Complete",
  failed: "Run failed",
};

export function AgentPanel({ session }: AgentPanelProps) {
  const statusLabel = STATUS_LABELS[session.agent_output_status];
  const output = session.agent_output || "No agent output yet.";

  return (
    <section style={panelStyle}>
      <header style={headerStyle}>
        <div>
          <div style={eyebrowStyle}>Agent Output</div>
          <h2 style={titleStyle}>Live Session Transcript</h2>
        </div>
        <span style={badgeStyle(session.agent_output_status)}>{statusLabel}</span>
      </header>

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
