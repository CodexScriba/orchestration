from __future__ import annotations

from pathlib import Path

from orchestrator.models import RunEvent, RunState, TaskRunState, TaskSnapshot
from orchestrator.state import (
    append_recent_event,
    build_board_state,
    load_run_state,
    render_run_summary,
    save_run_state,
    write_handoff_readme,
)


def test_build_board_state_groups_task_ids_by_project_and_stage() -> None:
    tasks = [
        TaskSnapshot(
            path=Path(".kanban2code/projects/orchestration/task1.md"),
            task_id="task1",
            project="orchestration",
            stage="plan",
        ),
        TaskSnapshot(
            path=Path(".kanban2code/projects/orchestration/task2.md"),
            task_id="task2",
            project="orchestration",
            stage="audit",
        ),
        TaskSnapshot(
            path=Path(".kanban2code/projects/roadmap/roadmap.md"),
            task_id="roadmap",
            project="roadmap",
            stage="completed",
        ),
    ]

    board_state = build_board_state(tasks)

    assert board_state == {
        "orchestration": {
            "plan": ["task1"],
            "audit": ["task2"],
        },
        "roadmap": {
            "completed": ["roadmap"],
        },
    }


def test_run_state_round_trips_through_json(tmp_path: Path) -> None:
    run_state = RunState(
        schema_version=1,
        run_id="run-123",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="running",
        ordered_tasks=[
            ".kanban2code/projects/orchestration/phase1/task1.md",
        ],
        task_states={
            ".kanban2code/projects/orchestration/phase1/task1.md": TaskRunState(
                status="running",
                last_stage="plan",
                audit_failures=1,
                transport_attempts={"plan": 1},
            )
        },
        recent_events=[
            RunEvent(
                timestamp="2026-03-13T00:01:00Z",
                type="run_started",
                message="Run started.",
                extras={"run_id": "run-123"},
            )
        ],
        current_index=0,
        current_task=".kanban2code/projects/orchestration/phase1/task1.md",
        current_stage="plan",
        last_error=None,
    )
    state_path = tmp_path / "state" / "run.json"

    save_run_state(state_path, run_state)
    loaded_state = load_run_state(state_path)

    assert loaded_state == run_state


def test_append_recent_event_respects_cap() -> None:
    run_state = RunState(
        run_id="run-123",
        updated_at="2026-03-13T00:00:00Z",
        recent_events=[
            RunEvent(timestamp="2026-03-13T00:00:01Z", type="run_started", message="Started."),
            RunEvent(timestamp="2026-03-13T00:00:02Z", type="stage_success", message="Planned."),
        ],
    )

    append_recent_event(
        run_state,
        RunEvent(timestamp="2026-03-13T00:00:03Z", type="run_completed", message="Done."),
        max_events=2,
    )

    assert [event.type for event in run_state.recent_events] == [
        "stage_success",
        "run_completed",
    ]
    assert run_state.updated_at == "2026-03-13T00:00:03Z"


def test_render_run_summary_includes_queue_and_recent_events() -> None:
    run_state = RunState(
        schema_version=1,
        run_id="run-123",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:05:00Z",
        status="running",
        ordered_tasks=[
            ".kanban2code/projects/orchestration/phase1/task1.md",
            ".kanban2code/projects/orchestration/phase1/task2.md",
        ],
        task_states={
            ".kanban2code/projects/orchestration/phase1/task1.md": TaskRunState(
                status="completed",
                audit_failures=0,
            ),
            ".kanban2code/projects/orchestration/phase1/task2.md": TaskRunState(
                status="running",
                audit_failures=1,
            ),
        },
        recent_events=[
            RunEvent(
                timestamp="2026-03-13T00:05:00Z",
                type="stage_success",
                message="Task moved to audit.",
            )
        ],
        current_index=1,
        current_task=".kanban2code/projects/orchestration/phase1/task2.md",
        current_stage="audit",
    )

    summary = render_run_summary(run_state)

    assert "# Orchestrator Run run-123" in summary
    assert "- Queue length: 2" in summary
    assert "## Queue" in summary
    assert "status: completed" in summary
    assert "audit_failures: 1" in summary
    assert "## Recent Events" in summary
    assert "stage_success | Task moved to audit." in summary


def test_write_handoff_readme_includes_context_and_reason(tmp_path: Path) -> None:
    handoff_path = tmp_path / "HANDOFF.md"
    run_state = RunState(
        run_id="run-123",
        recent_events=[
            RunEvent(
                timestamp="2026-03-13T00:05:00Z",
                type="handoff",
                message="Manual follow-up required.",
            )
        ],
    )
    snapshot = TaskSnapshot(
        path=tmp_path / "task.md",
        task_id="task1",
        project="orchestration",
        stage="audit",
        agent="auditor",
        contexts=["skills/python-core-skills"],
    )

    write_handoff_readme(
        path=handoff_path,
        run_state=run_state,
        task_snapshot=snapshot,
        reason="Transport retries exhausted.",
    )

    contents = handoff_path.read_text(encoding="utf-8")
    assert "Transport retries exhausted." in contents
    assert "skills/python-core-skills" in contents
    assert "Manual follow-up required." in contents
