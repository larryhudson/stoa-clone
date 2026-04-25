import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { claimControl, promptAgent } from "../api/sessionCommands";
import { getSession } from "../api/sessions";
import { subscribeToSessionEvents } from "../api/sessionEventStream";
import type { SessionViewModel } from "../lib/sessionTypes";
import { applySessionEvent } from "../lib/sessionState";
import { sessionFromSnapshot } from "../lib/sessionStateHelpers";
import { AgentPanel } from "./AgentPanel";

type SessionPageProps = {
  sessionId: string;
  userId: string;
};

export function SessionPage({ sessionId, userId }: SessionPageProps) {
  const [session, setSession] = useState<SessionViewModel | null>(null);
  const [commandError, setCommandError] = useState<string | null>(null);
  const [isCommandPending, setIsCommandPending] = useState(false);
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

    return subscribeToSessionEvents(
      sessionId,
      (event) => {
        setSession((current) => (current ? applySessionEvent(current, event) : current));
      },
      {
        onReconnect: async () => {
          setSession(sessionFromSnapshot(await getSession(sessionId)));
        },
      },
    );
  }, [sessionId, sessionQuery.data]);

  if (sessionQuery.isPending) {
    return <div style={messageStyle}>Loading session...</div>;
  }

  if (sessionQuery.error || !session) {
    return <div style={messageStyle}>Failed to load session.</div>;
  }

  async function runCommand(command: () => Promise<unknown>) {
    setCommandError(null);
    setIsCommandPending(true);
    try {
      await command();
    } catch (error) {
      setCommandError(error instanceof Error ? error.message : "Command failed");
    } finally {
      setIsCommandPending(false);
    }
  }

  return (
    <AgentPanel
      session={session}
      userId={userId}
      commandError={commandError}
      isCommandPending={isCommandPending}
      onClaimControl={() => {
        void runCommand(async () => {
          setSession(sessionFromSnapshot(await claimControl(sessionId, userId)));
        });
      }}
      onPromptAgent={(text) => {
        void runCommand(async () => {
          setSession(sessionFromSnapshot(await promptAgent(sessionId, userId, text)));
        });
      }}
    />
  );
}

const messageStyle: React.CSSProperties = {
  padding: "1.25rem",
  borderRadius: "18px",
  background: "rgba(255, 251, 244, 0.86)",
  color: "#56452f",
};
