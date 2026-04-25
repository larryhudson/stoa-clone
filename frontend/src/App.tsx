import { useState } from "react";

import { createSession, startSession } from "./api/sessionCommands";
import { SessionPage } from "./components/SessionPage";
import { sessionFromSnapshot } from "./lib/sessionStateHelpers";

export default function App() {
  const searchParams = new URLSearchParams(window.location.search);
  const initialSessionId = searchParams.get("sessionId");
  const userId = searchParams.get("userId") ?? "user-1";
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId);
  const [startError, setStartError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  return (
    <main style={pageStyle}>
      <section style={heroStyle}>
        <div>
          <p style={kickerStyle}>multiplayer-agent</p>
          <h1 style={headlineStyle}>Typed session snapshots with reducer-ready live state</h1>
          <p style={copyStyle}>
            The UI now loads a typed session snapshot over HTTP with TanStack Query. The reducer
            remains the next layer for websocket-driven live event updates.
          </p>
        </div>
        <div style={pillStyle}>
          Session: {sessionId ?? "none"} | User: {userId}
        </div>
      </section>

      {sessionId ? (
        <SessionPage sessionId={sessionId} userId={userId} />
      ) : (
        <form
          style={launcherStyle}
          onSubmit={(event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const data = new FormData(form);
            const repoUrl = String(data.get("repoUrl") ?? "").trim();
            const branch = String(data.get("branch") ?? "main").trim() || "main";
            if (!repoUrl) {
              return;
            }

            setStartError(null);
            setIsStarting(true);
            void createSession(repoUrl, branch)
              .then((created) => startSession(created.id))
              .then((started) => {
                const session = sessionFromSnapshot(started);
                const nextUrl = new URL(window.location.href);
                nextUrl.searchParams.set("sessionId", session.id);
                nextUrl.searchParams.set("userId", userId);
                window.history.pushState(null, "", nextUrl);
                setSessionId(session.id);
              })
              .catch((error) => {
                setStartError(error instanceof Error ? error.message : "Failed to start session");
              })
              .finally(() => {
                setIsStarting(false);
              });
          }}
        >
          <label style={fieldStyle}>
            <span>Repository URL</span>
            <input
              name="repoUrl"
              type="url"
              required
              placeholder="https://github.com/example/repo.git"
              style={inputStyle}
            />
          </label>
          <label style={fieldStyle}>
            <span>Branch</span>
            <input name="branch" defaultValue="main" style={inputStyle} />
          </label>
          <button type="submit" disabled={isStarting} style={buttonStyle}>
            Create session
          </button>
          {startError ? (
            <div role="alert" style={errorStyle}>
              {startError}
            </div>
          ) : null}
        </form>
      )}
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  padding: "3rem 1.5rem",
  background:
    "radial-gradient(circle at top left, rgba(240, 198, 116, 0.35), transparent 30%), linear-gradient(180deg, #f4ead9 0%, #e7dcc8 100%)",
  display: "grid",
  gap: "1.5rem",
  alignContent: "start",
  maxWidth: "960px",
  margin: "0 auto",
};

const heroStyle: React.CSSProperties = {
  display: "grid",
  gap: "1rem",
  padding: "1.5rem",
  borderRadius: "28px",
  background: "rgba(255, 251, 244, 0.86)",
  border: "1px solid rgba(118, 89, 45, 0.16)",
  boxShadow: "0 28px 60px rgba(73, 54, 28, 0.08)",
};

const kickerStyle: React.CSSProperties = {
  margin: 0,
  textTransform: "uppercase",
  letterSpacing: "0.12em",
  fontSize: "0.72rem",
  color: "#85653d",
};

const headlineStyle: React.CSSProperties = {
  margin: "0.25rem 0 0",
  fontSize: "clamp(2rem, 4vw, 3.5rem)",
  lineHeight: 0.98,
  color: "#261a0c",
};

const copyStyle: React.CSSProperties = {
  margin: "0.85rem 0 0",
  maxWidth: "44rem",
  fontSize: "1rem",
  lineHeight: 1.6,
  color: "#56452f",
};

const pillStyle: React.CSSProperties = {
  justifySelf: "start",
  borderRadius: "999px",
  background: "#f2ddbc",
  color: "#734425",
  padding: "0.85rem 1.15rem",
  fontSize: "0.95rem",
  fontWeight: 700,
};

const launcherStyle: React.CSSProperties = {
  display: "grid",
  gap: "1rem",
  padding: "1.25rem",
  borderRadius: "18px",
  background: "rgba(255, 251, 244, 0.86)",
  border: "1px solid rgba(118, 89, 45, 0.16)",
};

const fieldStyle: React.CSSProperties = {
  display: "grid",
  gap: "0.4rem",
  color: "#56452f",
  fontWeight: 700,
};

const inputStyle: React.CSSProperties = {
  border: "1px solid #cfc3b1",
  borderRadius: "12px",
  padding: "0.75rem",
  font: "inherit",
  color: "#2f2416",
  background: "#fffaf1",
};

const buttonStyle: React.CSSProperties = {
  justifySelf: "start",
  border: "1px solid #7d5d32",
  borderRadius: "12px",
  padding: "0.7rem 0.9rem",
  font: "inherit",
  fontWeight: 700,
  color: "#fffaf1",
  background: "#6f4b22",
  cursor: "pointer",
};

const errorStyle: React.CSSProperties = {
  padding: "0.85rem 1rem",
  borderRadius: "14px",
  background: "#fff1ef",
  color: "#6f1f1b",
  border: "1px solid #e7a5a0",
};
