import Ajv from "ajv";

import sessionEventSchema from "../../../openapi/session-event.schema.json";
import type { SessionEvent } from "./sessionEvents";

const ajv = new Ajv({ strict: false });
const validateSessionEvent = ajv.compile<SessionEvent>(sessionEventSchema);

export function parseSessionEvent(payload: unknown): SessionEvent {
  if (validateSessionEvent(payload)) {
    return payload;
  }

  throw new Error("Invalid session event payload");
}
