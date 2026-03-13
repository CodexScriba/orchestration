from __future__ import annotations

import json
from pathlib import Path

from orchestrator.logger import JsonlLogger


def test_jsonl_logger_appends_valid_event_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "run.jsonl"
    logger = JsonlLogger(log_path)

    event = logger.append("run_started", "Run started.", run_id="run-123", status="running")

    line = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)

    assert payload["type"] == "run_started"
    assert payload["message"] == "Run started."
    assert payload["extras"] == {"run_id": "run-123", "status": "running"}
    assert payload["timestamp"] == event.timestamp
    assert event.extras == {"run_id": "run-123", "status": "running"}


def test_jsonl_logger_appends_multiple_events(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    logger = JsonlLogger(log_path)

    logger.append("run_started", "Started.")
    logger.append("run_completed", "Completed.", result="ok")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "run_started"
    assert json.loads(lines[1])["extras"] == {"result": "ok"}
