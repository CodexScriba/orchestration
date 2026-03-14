"""Tests for the three-layer memory system."""

from __future__ import annotations

from pathlib import Path

from orchestrator.memory import HotMemory, MemoryManager, WarmMemory
from orchestrator.models import MemoryConfig, RunEvent, RunState, TaskRunState


def test_hot_memory_init_from_run_state(tmp_path: Path) -> None:
    """Hot memory is initialized correctly from run state."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md", "task2.md"],
        task_states={
            "task1.md": TaskRunState(status="completed"),
            "task2.md": TaskRunState(status="pending"),
        },
        recent_events=[
            RunEvent(timestamp="2026-03-13T00:00:01Z", type="start", message="Run started"),
        ],
    )

    memory.init_hot_memory(run_state)
    hot = memory._hot

    assert hot is not None
    assert hot.run_id == "test-run"
    assert hot.status == "running"
    assert "task2.md" in hot.active_tasks  # pending task is active
    assert "task1.md" not in hot.active_tasks  # completed task is not active


def test_hot_memory_persisted_to_file(tmp_path: Path) -> None:
    """Hot memory is persisted to hot.json file."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="pending")},
    )

    memory.init_hot_memory(run_state)

    hot_path = tmp_path / ".kanban2code" / "runs" / "test-run" / "hot.json"
    assert hot_path.exists()

    import json

    raw = json.loads(hot_path.read_text(encoding="utf-8"))
    assert raw["run_id"] == "test-run"
    assert raw["status"] == "running"


def test_warm_memory_stores_completed_tasks(tmp_path: Path) -> None:
    """Warm memory stores completed tasks per project."""
    memory = MemoryManager(tmp_path, MemoryConfig(warm_retention_per_project=10))

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=[".kanban2code/projects/myproj/task1.md"],
        task_states={
            ".kanban2code/projects/myproj/task1.md": TaskRunState(
                status="completed",
                last_stage="audit",
            ),
        },
    )

    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    assert warm_path.exists()

    import json

    raw = json.loads(warm_path.read_text(encoding="utf-8"))
    assert len(raw["completed_tasks"]) == 1
    assert raw["completed_tasks"][0]["task_path"] == ".kanban2code/projects/myproj/task1.md"


def test_warm_memory_rotates_old_entries(tmp_path: Path) -> None:
    """Warm memory rotates old entries when limit exceeded."""
    memory = MemoryManager(tmp_path, MemoryConfig(warm_retention_per_project=3))

    # Add 5 tasks (limit is 3)
    for i in range(5):
        run_state = RunState(
            run_id=f"run-{i}",
            created_at=f"2026-03-13T00:0{i}:00Z",
            updated_at=f"2026-03-13T00:0{i}:00Z",
            status="completed",
            ordered_tasks=[f".kanban2code/projects/myproj/task{i}.md"],
            task_states={
                f".kanban2code/projects/myproj/task{i}.md": TaskRunState(status="completed"),
            },
        )
        memory.init_hot_memory(run_state)
        memory.archive_hot_to_warm(run_state)

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    import json

    raw = json.loads(warm_path.read_text(encoding="utf-8"))
    assert len(raw["completed_tasks"]) == 3  # Only last 3 retained


def test_cold_memory_aggregates_stats(tmp_path: Path) -> None:
    """Cold memory aggregates stats from completed runs."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=["task1.md", "task2.md"],
        task_states={
            "task1.md": TaskRunState(status="completed"),
            "task2.md": TaskRunState(status="completed"),
        },
    )

    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    stats_path = tmp_path / ".kanban2code" / "memory" / "cold" / "stats.json"
    assert stats_path.exists()

    import json

    raw = json.loads(stats_path.read_text(encoding="utf-8"))
    assert raw["stats"]["total_runs"] == 1
    assert raw["stats"]["total_tasks"] == 2
    assert raw["stats"]["completed_tasks"] == 2


def test_read_memory_hot_layer(tmp_path: Path) -> None:
    """Read memory returns hot layer contents."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="pending")},
    )

    memory.init_hot_memory(run_state)
    result = memory.read_memory("hot")

    assert result["run_id"] == "test-run"
    assert result["status"] == "running"


def test_read_memory_warm_layer(tmp_path: Path) -> None:
    """Read memory returns warm layer contents."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    # Add a completed task
    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=[".kanban2code/projects/myproj/task1.md"],
        task_states={
            ".kanban2code/projects/myproj/task1.md": TaskRunState(status="completed"),
        },
    )
    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    result = memory.read_memory("warm")

    assert "myproj" in result
    assert len(result["myproj"]["completed_tasks"]) == 1


def test_read_memory_cold_layer(tmp_path: Path) -> None:
    """Read memory returns cold layer contents."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="completed")},
    )
    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    result = memory.read_memory("cold")

    assert "stats" in result
    assert result["stats"]["total_runs"] == 1


def test_read_memory_with_topic_filter(tmp_path: Path) -> None:
    """Read memory filters by topic when specified."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=[".kanban2code/projects/myproj/task1.md"],
        task_states={
            ".kanban2code/projects/myproj/task1.md": TaskRunState(status="completed"),
        },
    )
    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    result = memory.read_memory("warm", topic="completed_tasks")

    assert "myproj" in result
    assert "completed_tasks" in result["myproj"]
    assert "recent_errors" not in result["myproj"]


def test_append_to_warm_manual(tmp_path: Path) -> None:
    """Manual append to warm memory works."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    entry = {"task_path": "task1.md", "decision": "Use approach A"}
    memory.append_to_warm("myproj", "recent_decisions", entry)

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    assert warm_path.exists()

    import json

    raw = json.loads(warm_path.read_text(encoding="utf-8"))
    assert len(raw["recent_decisions"]) == 1
    assert raw["recent_decisions"][0]["decision"] == "Use approach A"


def test_append_to_cold_manual(tmp_path: Path) -> None:
    """Manual append to cold memory works."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    entry = {"pattern": "timeout_errors", "count": 5}
    memory.append_to_cold("failure_patterns", entry)

    errors_path = tmp_path / ".kanban2code" / "memory" / "cold" / "errors.json"
    assert errors_path.exists()

    import json

    raw = json.loads(errors_path.read_text(encoding="utf-8"))
    assert len(raw["failure_patterns"]) == 1
    assert raw["failure_patterns"][0]["pattern"] == "timeout_errors"


def test_corrupted_warm_file_reinitializes(tmp_path: Path) -> None:
    """Corrupted warm memory file is reinitialized."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    warm_path.parent.mkdir(parents=True, exist_ok=True)
    warm_path.write_text("invalid json", encoding="utf-8")

    # Should not raise, should return empty warm memory
    result = memory.read_memory("warm")
    assert "myproj" in result
    assert result["myproj"]["completed_tasks"] == []


def test_memory_directories_created(tmp_path: Path) -> None:
    """Memory directories are created on initialization."""
    MemoryManager(tmp_path, MemoryConfig())

    warm_dir = tmp_path / ".kanban2code" / "memory" / "warm"
    cold_dir = tmp_path / ".kanban2code" / "memory" / "cold"

    assert warm_dir.exists()
    assert cold_dir.exists()


def test_in_flight_session_tracking(tmp_path: Path) -> None:
    """In-flight sessions are tracked and removed correctly."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="pending")},
    )
    memory.init_hot_memory(run_state)

    memory.add_in_flight_session({"task_key": "task1.md", "task_id": "task1", "status": "running"})
    memory.add_in_flight_session({"task_key": "task2.md", "task_id": "task2", "status": "running"})

    assert len(memory._hot.in_flight_sessions) == 2

    memory.remove_in_flight_session("task1.md")

    assert len(memory._hot.in_flight_sessions) == 1
    assert memory._hot.in_flight_sessions[0]["task_key"] == "task2.md"


def test_in_flight_session_noop_without_hot(tmp_path: Path) -> None:
    """add/remove in_flight_session are no-ops when hot memory is not initialized."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    # Should not raise
    memory.add_in_flight_session({"task_key": "task1.md", "task_id": "task1", "status": "running"})
    memory.remove_in_flight_session("task1.md")


def test_in_flight_session_persisted_to_hot_json(tmp_path: Path) -> None:
    """add_in_flight_session and remove_in_flight_session update hot.json immediately."""
    import json

    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="pending")},
    )
    memory.init_hot_memory(run_state)
    hot_path = tmp_path / ".kanban2code" / "runs" / "test-run" / "hot.json"

    memory.add_in_flight_session({"task_key": "task1.md", "task_id": "task1", "status": "running"})
    raw = json.loads(hot_path.read_text(encoding="utf-8"))
    assert len(raw["in_flight_sessions"]) == 1

    memory.remove_in_flight_session("task1.md")
    raw = json.loads(hot_path.read_text(encoding="utf-8"))
    assert len(raw["in_flight_sessions"]) == 0


def test_warm_errors_captured_from_stage_result_events(tmp_path: Path) -> None:
    """Warm recent_errors captures failed stage_result events with error_message."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=[".kanban2code/projects/myproj/task1.md"],
        task_states={
            ".kanban2code/projects/myproj/task1.md": TaskRunState(status="completed"),
        },
        recent_events=[
            # Failed stage_result with error_message in extras
            RunEvent(
                timestamp="2026-03-13T00:00:30Z",
                type="stage_result",
                message="task1.md code -> transport_error",
                extras={"result": "transport_error", "error_message": "Provider timed out"},
            ),
            # Successful stage_result — should NOT be captured as error
            RunEvent(
                timestamp="2026-03-13T00:00:45Z",
                type="stage_result",
                message="task1.md audit -> success",
                extras={"result": "success", "error_message": None},
            ),
        ],
    )

    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    import json

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    raw = json.loads(warm_path.read_text(encoding="utf-8"))

    assert len(raw["recent_errors"]) == 1
    assert "transport_error" in raw["recent_errors"][0]["message"]


def test_warm_errors_captured_from_task_error_events(tmp_path: Path) -> None:
    """Warm recent_errors captures task_error events regardless of extras."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=[".kanban2code/projects/myproj/task1.md"],
        task_states={
            ".kanban2code/projects/myproj/task1.md": TaskRunState(status="completed"),
        },
        recent_events=[
            RunEvent(
                timestamp="2026-03-13T00:00:30Z",
                type="task_error",
                message="task1.md -> error: Worker crashed",
                extras={"error": "Worker crashed"},
            ),
        ],
    )

    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    import json

    warm_path = tmp_path / ".kanban2code" / "memory" / "warm" / "myproj.json"
    raw = json.loads(warm_path.read_text(encoding="utf-8"))

    assert len(raw["recent_errors"]) == 1


def test_cold_model_performance_aggregated(tmp_path: Path) -> None:
    """Cold model_performance is aggregated from stage_result events."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=["task1.md"],
        task_states={"task1.md": TaskRunState(status="completed")},
        recent_events=[
            RunEvent(
                timestamp="2026-03-13T00:00:10Z",
                type="stage_result",
                message="task1.md code -> success",
                extras={"result": "success", "provider_model": "claude-opus-4-6"},
            ),
            RunEvent(
                timestamp="2026-03-13T00:00:20Z",
                type="stage_result",
                message="task1.md audit -> transport_error",
                extras={"result": "transport_error", "provider_model": "claude-opus-4-6"},
            ),
        ],
    )

    memory.init_hot_memory(run_state)
    memory.archive_hot_to_warm(run_state)

    import json

    perf_path = tmp_path / ".kanban2code" / "memory" / "cold" / "performance.json"
    raw = json.loads(perf_path.read_text(encoding="utf-8"))

    assert "claude-opus-4-6" in raw["model_performance"]
    perf = raw["model_performance"]["claude-opus-4-6"]
    assert perf["total"] == 2
    assert perf["success"] == 1
    assert perf["failure"] == 1


def test_cold_aggregation_interval_respected(tmp_path: Path) -> None:
    """Cold failure patterns only aggregated every cold_aggregation_interval runs."""
    # interval=2: patterns only aggregated on run 2, 4, etc. (when total_runs % 2 == 0)
    memory = MemoryManager(tmp_path, MemoryConfig(cold_aggregation_interval=2))

    run_state_1 = RunState(
        run_id="run-1",
        created_at="2026-03-13T00:00:00Z",
        updated_at="2026-03-13T00:01:00Z",
        status="completed",
        ordered_tasks=["task1.md"],
        task_states={
            "task1.md": TaskRunState(status="handoff_required", last_stage="code", last_error="Failed"),
        },
    )
    memory.init_hot_memory(run_state_1)
    memory.archive_hot_to_warm(run_state_1)

    import json

    # After run 1 (total_runs=1, 1 % 2 != 0): no failure patterns aggregated
    errors_path = tmp_path / ".kanban2code" / "memory" / "cold" / "errors.json"
    raw = json.loads(errors_path.read_text(encoding="utf-8"))
    assert len(raw["failure_patterns"]) == 0

    run_state_2 = RunState(
        run_id="run-2",
        created_at="2026-03-13T00:02:00Z",
        updated_at="2026-03-13T00:03:00Z",
        status="completed",
        ordered_tasks=["task2.md"],
        task_states={
            "task2.md": TaskRunState(status="handoff_required", last_stage="audit", last_error="Bounced"),
        },
    )
    memory.init_hot_memory(run_state_2)
    memory.archive_hot_to_warm(run_state_2)

    # After run 2 (total_runs=2, 2 % 2 == 0): failure patterns aggregated
    raw = json.loads(errors_path.read_text(encoding="utf-8"))
    assert len(raw["failure_patterns"]) == 1
    assert raw["failure_patterns"][0]["task_path"] == "task2.md"


def test_update_hot_memory_reflects_state_changes(tmp_path: Path) -> None:
    """update_hot_memory correctly refreshes active_tasks and status."""
    memory = MemoryManager(tmp_path, MemoryConfig())

    run_state = RunState(
        run_id="test-run",
        created_at="2026-03-13T00:00:00Z",
        status="running",
        ordered_tasks=["task1.md", "task2.md"],
        task_states={
            "task1.md": TaskRunState(status="pending"),
            "task2.md": TaskRunState(status="pending"),
        },
    )
    memory.init_hot_memory(run_state)

    assert len(memory._hot.active_tasks) == 2

    # Simulate task1 completing
    run_state.task_states["task1.md"].status = "completed"
    memory.update_hot_memory(run_state)

    assert "task1.md" not in memory._hot.active_tasks
    assert "task2.md" in memory._hot.active_tasks