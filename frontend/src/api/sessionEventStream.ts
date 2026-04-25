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
  options: {
    onReconnect?: () => Promise<void> | void;
    reconnectDelayMs?: number;
  } = {},
): () => void {
  let closedByClient = false;
  let reconnectTimer: number | null = null;
  let websocket: WebSocket | null = null;

  const reconnectDelayMs = options.reconnectDelayMs ?? 500;

  const connect = () => {
    websocket = new WebSocket(sessionEventsUrl(sessionId));

    websocket.addEventListener("message", (message) => {
      try {
        onEvent(parseSessionEvent(JSON.parse(String(message.data))));
      } catch {
        // Ignore malformed websocket messages at the boundary.
      }
    });

    websocket.addEventListener("close", () => {
      if (closedByClient) {
        return;
      }

      reconnectTimer = window.setTimeout(async () => {
        await options.onReconnect?.();
        if (!closedByClient) {
          connect();
        }
      }, reconnectDelayMs);
    });
  };

  connect();

  return () => {
    closedByClient = true;
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer);
    }
    websocket?.close();
  };
}
