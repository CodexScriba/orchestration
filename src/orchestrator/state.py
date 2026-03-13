"""State helpers for scanner output and persisted run metadata."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path

from orchestrator.models import RunEvent, RunState, TaskRunState, TaskSnapshot
from orchestrator.scanner import index_tasks_by_project_and_stage


def build_board_index(tasks: Sequence[TaskSnapshot]) -> dict[str, dict[str, list[TaskSnapshot]]]:
    """Build a project and stage index for task snapshots.

    Args:
        tasks: Ordered task snapshots.

    Returns:
        Nested mapping of project to stage to ordered task snapshots.
    """

    return index_tasks_by_project_and_stage(tasks)


def build_board_state(tasks: Sequence[TaskSnapshot]) -> dict[str, dict[str, list[str]]]:
    """Build a compact board-state mapping for Kadee.

    Args:
        tasks: Ordered task snapshots.

    Returns:
        Nested mapping of project to stage to ordered task identifiers.
    """

    board_state: dict[str, dict[str, list[str]]] = {}
    for project_name, stage_index in build_board_index(tasks).items():
        board_state[project_name] = {}
        for stage_name, stage_tasks in stage_index.items():
            board_state[project_name][stage_name] = [task.task_id for task in stage_tasks]
    return board_state


def save_run_state(path: Path, run_state: RunState) -> None:
    """Persist a run state to JSON.

    Args:
        path: Output path for the JSON state file.
        run_state: Run-state payload to persist.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(run_state), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_run_state(path: Path) -> RunState:
    """Load a run state from JSON.

    Args:
        path: Input state-file path.

    Returns:
        Parsed run-state model.
    """

    raw_state = json.loads(path.read_text(encoding="utf-8"))
    task_states = {
        task_path: TaskRunState(**task_state)
        for task_path, task_state in raw_state.get("task_states", {}).items()
    }
    recent_events = [RunEvent(**event) for event in raw_state.get("recent_events", [])]

    return RunState(
        schema_version=int(raw_state.get("schema_version", 1)),
        run_id=str(raw_state.get("run_id", "")),
        created_at=str(raw_state.get("created_at", "")),
        updated_at=str(raw_state.get("updated_at", "")),
        status=str(raw_state.get("status", "")),
        ordered_tasks=[str(task_path) for task_path in raw_state.get("ordered_tasks", [])],
        task_states=task_states,
        recent_events=recent_events,
        current_index=int(raw_state.get("current_index", 0)),
        current_task=_optional_str(raw_state.get("current_task")),
        current_stage=_optional_str(raw_state.get("current_stage")),
        last_error=_optional_str(raw_state.get("last_error")),
    )


def append_recent_event(run_state: RunState, event: RunEvent, max_events: int) -> None:
    """Append an event to run state while enforcing a retention cap.

    Args:
        run_state: Mutable run-state model.
        event: Event to append.
        max_events: Maximum number of recent events to retain.
    """

    run_state.recent_events.append(event)
    if max_events >= 0:
        run_state.recent_events = run_state.recent_events[-max_events:]
    run_state.updated_at = event.timestamp


def render_run_summary(run_state: RunState) -> str:
    """Render a markdown summary for a persisted run.

    Args:
        run_state: Run-state model to summarize.

    Returns:
        Markdown summary string.
    """

    lines = [
        f"# Orchestrator Run {run_state.run_id}",
        "",
        f"- Status: {run_state.status}",
        f"- Created: {run_state.created_at}",
        f"- Updated: {run_state.updated_at}",
        f"- Queue length: {len(run_state.ordered_tasks)}",
        f"- Current task: {run_state.current_task or 'none'}",
        f"- Current stage: {run_state.current_stage or 'none'}",
        "",
        "## Queue",
    ]

    if not run_state.ordered_tasks:
        lines.append("- none")
    else:
        for index, task_path in enumerate(run_state.ordered_tasks):
            task_state = run_state.task_states.get(task_path, TaskRunState())
            marker = "x" if task_state.status == "completed" else ">"
            if index > run_state.current_index and marker != "x":
                marker = " "
            lines.append(
                f"- [{marker}] {task_path} | status: {task_state.status} "
                f"| audit_failures: {task_state.audit_failures}"
            )

    lines.extend(["", "## Recent Events"])
    if not run_state.recent_events:
        lines.append("- none")
    else:
        for event in run_state.recent_events:
            lines.append(f"- {event.timestamp} | {event.type} | {event.message}")

    return "\n".join(lines) + "\n"


def write_handoff_readme(
    *,
    path: Path,
    run_state: RunState,
    task_snapshot: TaskSnapshot,
    reason: str,
) -> None:
    """Write a human-readable handoff summary for manual follow-up."""

    lines = [
        "# Handoff Required",
        "",
        f"- Run ID: {run_state.run_id}",
        f"- Task: {task_snapshot.task_id}",
        f"- Task Path: {task_snapshot.path}",
        f"- Current Stage: {task_snapshot.stage}",
        f"- Agent: {task_snapshot.agent}",
        f"- Reason: {reason}",
        "",
        "## Task Contexts",
    ]

    if not task_snapshot.contexts:
        lines.append("- none")
    else:
        for context_name in task_snapshot.contexts:
            lines.append(f"- {context_name}")

    lines.extend(["", "## Recent Events"])
    if not run_state.recent_events:
        lines.append("- none")
    else:
        for event in run_state.recent_events:
            lines.append(f"- {event.timestamp} | {event.type} | {event.message}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _optional_str(value: object) -> str | None:
    """Convert optional JSON scalar values into strings or None."""

    if value is None:
        return None
    return str(value)
