import { SessionPage } from "./components/SessionPage";

export default function App() {
  const sessionId = new URLSearchParams(window.location.search).get("sessionId") ?? "session-1";

  return (
    <main style={pageStyle}>
      <section style={heroStyle}>
        <div>
          <p style={kickerStyle}>stoa-clone frontend slice</p>
          <h1 style={headlineStyle}>Typed session snapshots with reducer-ready live state</h1>
          <p style={copyStyle}>
            The UI now loads a typed session snapshot over HTTP with TanStack Query. The reducer
            remains the next layer for websocket-driven live event updates.
          </p>
        </div>
        <div style={pillStyle}>Session: {sessionId}</div>
      </section>

      <SessionPage sessionId={sessionId} />
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
