"""Structured JSONL logger for orchestrator events."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from orchestrator.models import RunEvent


class JsonlLogger:
    """Append structured events to a JSONL file."""

    def __init__(self, path: Path) -> None:
        """Initialize the logger with an output path.

        Args:
            path: Target JSONL file path.
        """

        self.path = path

    def append(self, event_type: str, message: str, **extras: object) -> RunEvent:
        """Append a structured event to the JSONL log.

        Args:
            event_type: Machine-readable event type.
            message: Human-readable event message.
            **extras: Additional serializable event data.

        Returns:
            The appended event model.
        """

        event = RunEvent(
            timestamp=_utc_now_iso(),
            type=event_type,
            message=message,
            extras=dict(extras),
        )
        payload = {
            "timestamp": event.timestamp,
            "type": event.type,
            "message": event.message,
            "extras": event.extras,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(payload, sort_keys=True) + "\n")
        return event


def _utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
