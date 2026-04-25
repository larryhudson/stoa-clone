import { apiClient } from "./client";

export async function getSession(sessionId: string) {
  const { data, error } = await apiClient.GET("/sessions/{session_id}", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
  });

  if (error) {
    throw new Error("Failed to fetch session state");
  }

  if (!data) {
    throw new Error("Session response was empty");
  }

  return data;
}
