from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from app.api.event_schemas import SessionEvent


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    output_path = root / "openapi" / "session-event.schema.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schema = TypeAdapter(SessionEvent).json_schema(
        ref_template="#/$defs/{model}",
        union_format="any_of",
    )
    schema["title"] = "SessionEvent"
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote session event schema to {output_path}")


if __name__ == "__main__":
    main()
