import { useQuery } from "@tanstack/react-query";

import { getSession } from "../api/sessions";
import { sessionFromSnapshot } from "../lib/sessionStateHelpers";
import { AgentPanel } from "./AgentPanel";

type SessionPageProps = {
  sessionId: string;
};

export function SessionPage({ sessionId }: SessionPageProps) {
  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => sessionFromSnapshot(await getSession(sessionId)),
  });

  if (sessionQuery.isPending) {
    return <div style={messageStyle}>Loading session...</div>;
  }

  if (sessionQuery.error || !sessionQuery.data) {
    return <div style={messageStyle}>Failed to load session.</div>;
  }

  return <AgentPanel session={sessionQuery.data} />;
}

const messageStyle: React.CSSProperties = {
  padding: "1.25rem",
  borderRadius: "18px",
  background: "rgba(255, 251, 244, 0.86)",
  color: "#56452f",
};
