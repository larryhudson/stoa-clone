import { apiClient } from "./client";

export async function joinSession(sessionId: string, userId: string) {
  const { data, error } = await apiClient.POST("/sessions/{session_id}/join", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
    body: {
      user_id: userId,
    },
  });

  if (error || !data) {
    throw new Error("Failed to join session");
  }

  return data;
}

export async function claimControl(sessionId: string, userId: string) {
  const { data, error } = await apiClient.POST("/sessions/{session_id}/control/claim", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
    body: {
      user_id: userId,
    },
  });

  if (error || !data) {
    throw new Error("Failed to claim control");
  }

  return data;
}

export async function promptAgent(sessionId: string, userId: string, text: string) {
  const { data, error } = await apiClient.POST("/sessions/{session_id}/agent/prompt", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
    body: {
      user_id: userId,
      text,
    },
  });

  if (error || !data) {
    throw new Error("Failed to prompt agent");
  }

  return data;
}

export async function steerAgent(sessionId: string, userId: string, text: string) {
  const { data, error } = await apiClient.POST("/sessions/{session_id}/agent/steer", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
    body: {
      user_id: userId,
      text,
    },
  });

  if (error || !data) {
    throw new Error("Failed to steer agent");
  }

  return data;
}

export async function abortAgent(sessionId: string, userId: string) {
  const { data, error } = await apiClient.POST("/sessions/{session_id}/agent/abort", {
    params: {
      path: {
        session_id: sessionId,
      },
    },
    body: {
      user_id: userId,
    },
  });

  if (error || !data) {
    throw new Error("Failed to abort agent");
  }

  return data;
}
