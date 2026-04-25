import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getSession } from "../api/sessions";
import { subscribeToSessionEvents } from "../api/sessionEventStream";
import type { SessionViewModel } from "../lib/sessionTypes";
import { applySessionEvent } from "../lib/sessionState";
import { sessionFromSnapshot } from "../lib/sessionStateHelpers";
import { AgentPanel } from "./AgentPanel";

type SessionPageProps = {
  sessionId: string;
};

export function SessionPage({ sessionId }: SessionPageProps) {
  const [session, setSession] = useState<SessionViewModel | null>(null);
  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => sessionFromSnapshot(await getSession(sessionId)),
  });

  useEffect(() => {
    if (sessionQuery.data) {
      setSession(sessionQuery.data);
    }
  }, [sessionQuery.data]);

  useEffect(() => {
    if (!sessionQuery.data) {
      return;
    }

    return subscribeToSessionEvents(sessionId, (event) => {
      setSession((current) => (current ? applySessionEvent(current, event) : current));
    });
  }, [sessionId, sessionQuery.data]);

  if (sessionQuery.isPending) {
    return <div style={messageStyle}>Loading session...</div>;
  }

  if (sessionQuery.error || !session) {
    return <div style={messageStyle}>Failed to load session.</div>;
  }

  return <AgentPanel session={session} />;
}

const messageStyle: React.CSSProperties = {
  padding: "1.25rem",
  borderRadius: "18px",
  background: "rgba(255, 251, 244, 0.86)",
  color: "#56452f",
};
