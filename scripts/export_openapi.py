from __future__ import annotations

import json
from pathlib import Path

from app.main import create_app


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    output_path = root / "openapi" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    app = create_app()
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
