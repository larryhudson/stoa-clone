import { parseSessionEvent } from "./sessionEventParser";
import type { SessionEvent } from "./sessionEvents";

export function sessionEventsUrl(sessionId: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const path = `${baseUrl.replace(/\/$/, "")}/sessions/${encodeURIComponent(sessionId)}/events/ws`;
  const url = new URL(path, window.location.href);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

export function subscribeToSessionEvents(
  sessionId: string,
  onEvent: (event: SessionEvent) => void,
): () => void {
  const websocket = new WebSocket(sessionEventsUrl(sessionId));

  websocket.addEventListener("message", (message) => {
    try {
      onEvent(parseSessionEvent(JSON.parse(String(message.data))));
    } catch {
      // Ignore malformed websocket messages at the boundary.
    }
  });

  return () => websocket.close();
}
