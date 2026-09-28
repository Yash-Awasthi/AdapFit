"""CSV and JSON rendering for data exports."""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Any


def to_csv(rows: list[dict]) -> str:
    """Rows with differing keys become one table; nested values are JSON-encoded."""
    if not rows:
        return ""
    fields: list[str] = []
    for row in rows:
        fields += [k for k in row if k not in fields]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    return out.getvalue()


def envelope(user_id: str, data: Any) -> dict:
    return {"export_date": datetime.now(timezone.utc).isoformat(), "app": "AdapFit",
            "format_version": "3", "user_id": user_id, "data": data}
