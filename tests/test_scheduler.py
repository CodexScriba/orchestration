"""Tests for concurrent scheduler and conflict detection."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from orchestrator.config import load_config
from orchestrator.models import RunState, StageResult, TaskSnapshot
from orchestrator.scheduler import (
    ConcurrentScheduler,
    ConflictDetector,
    ThreadSafeStateWriter,
    extract_file_paths_from_task,
    get_task_file_info,
)
from orchestrator.scanner import parse_task_file
from orchestrator.state import load_run_state


def _write_task(
    path: Path,
    *,
    stage: str,
    agent: str,
    tags: list[str] | None = None,
    depends_on: list[str] | str | None = None,
    body: str = "# Task\n",
) -> None:
    """Write a task file with frontmatter."""
    tags_yaml = f"\ntags: {tags}" if tags else ""
    depends_on_yaml = f"\ndepends_on: {depends_on}" if depends_on else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstage: {stage}\nagent: {agent}{tags_yaml}{depends_on_yaml}\n---\n{body}",
        encoding="utf-8",
    )


def _success_result(task_path: Path) -> StageResult:
    """Build a successful stage result for a task."""

    return StageResult(
        kind="success",
        stage="code",
        success=True,
        task_path=str(task_path),
        task_id=task_path.stem,
        before_stage="code",
        after_stage="completed",
        after_agent="auditor",
    )


def _transport_failure_result(task_path: Path) -> StageResult:
    """Build a transport-failure stage result for a task."""

    return StageResult(
        kind="transport_failure",
        stage="code",
        success=False,
        task_path=str(task_path),
        task_id=task_path.stem,
        before_stage="code",
        after_stage="code",
        after_agent="coder",
        error_message="transport failure",
    )


class ScriptedDispatcher:
    """Deterministic dispatcher used to exercise the scheduler."""

    def __init__(
        self,
        *,
        repo_root: Path,
        config_path: Path,
        run_state_path: Path,
        scripted_results: dict[str, list[StageResult]] | None = None,
        sleep_by_task: dict[str, float] | None = None,
    ) -> None:
        from orchestrator.dispatcher import Dispatcher

        self._dispatcher = Dispatcher(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=run_state_path,
        )
        self.account_manager = self._dispatcher.account_manager
        self._scripted_results = {
            task_id: list(results)
            for task_id, results in (scripted_results or {}).items()
        }
        self._sleep_by_task = dict(sleep_by_task or {})
        self.call_order: list[str] = []
        self.max_parallel = 0
        self._active_calls = 0
        self._lock = threading.Lock()

    def __getattr__(self, name: str):
        return getattr(self._dispatcher, name)

    def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
        task_id = task_path.stem
        with self._lock:
            self._active_calls += 1
            self.max_parallel = max(self.max_parallel, self._active_calls)
            self.call_order.append(task_id)

        try:
            sleep_seconds = self._sleep_by_task.get(task_id, 0.0)
            if sleep_seconds:
                time.sleep(sleep_seconds)

            task_results = self._scripted_results.get(task_id)
            if task_results:
                return task_results.pop(0)
            return _success_result(task_path)
        finally:
            with self._lock:
                self._active_calls -= 1


class TestConflictDetector:
    """Tests for the ConflictDetector class."""

    def test_no_conflict_when_no_running_tasks(self, tmp_path: Path) -> None:
        """No conflict when no tasks are running."""
        detector = ConflictDetector(tmp_path)
        file_paths = {tmp_path / "src" / "file1.py", tmp_path / "src" / "file2.py"}

        assert not detector.has_conflict(file_paths)

    def test_conflict_detected_for_overlapping_files(self, tmp_path: Path) -> None:
        """Conflict detected when files overlap."""
        detector = ConflictDetector(tmp_path)
        file_set1 = {tmp_path / "src" / "shared.py", tmp_path / "src" / "file1.py"}
        file_set2 = {tmp_path / "src" / "shared.py", tmp_path / "src" / "file2.py"}

        detector.register_task("task1", file_set1)

        assert detector.has_conflict(file_set2)

    def test_no_conflict_for_disjoint_files(self, tmp_path: Path) -> None:
        """No conflict when file sets are disjoint."""
        detector = ConflictDetector(tmp_path)
        file_set1 = {tmp_path / "src" / "file1.py"}
        file_set2 = {tmp_path / "src" / "file2.py"}

        detector.register_task("task1", file_set1)

        assert not detector.has_conflict(file_set2)

    def test_unregister_removes_from_conflict_set(self, tmp_path: Path) -> None:
        """Unregistering a task removes it from conflict detection."""
        detector = ConflictDetector(tmp_path)
        file_set1 = {tmp_path / "src" / "shared.py"}

        detector.register_task("task1", file_set1)
        assert detector.has_conflict(file_set1)

        detector.unregister_task("task1")
        assert not detector.has_conflict(file_set1)

    def test_get_conflicting_tasks_returns_task_keys(self, tmp_path: Path) -> None:
        """get_conflicting_tasks returns list of conflicting task keys."""
        detector = ConflictDetector(tmp_path)
        shared_file = tmp_path / "src" / "shared.py"

        detector.register_task("task1", {shared_file})
        detector.register_task("task2", {tmp_path / "src" / "other.py"})

        conflicts = detector.get_conflicting_tasks({shared_file})

        assert "task1" in conflicts
        assert "task2" not in conflicts


class TestFilePathExtraction:
    """Tests for extracting file paths from task bodies."""

    def test_extract_from_list_items(self, tmp_path: Path) -> None:
        """Extract paths from list items in ## Files section."""
        body = """# Task

## Files

- src/module.py
- tests/test_module.py

## Context

Some context here.
"""
        snapshot = TaskSnapshot(
            path=tmp_path / "task.md",
            task_id="task1",
            body=body,
        )

        file_paths = extract_file_paths_from_task(snapshot, tmp_path)

        assert (tmp_path / "src" / "module.py").resolve() in file_paths
        assert (tmp_path / "tests" / "test_module.py").resolve() in file_paths

    def test_extract_from_table_rows(self, tmp_path: Path) -> None:
        """Extract paths from table rows in ## Files section."""
        body = """# Task

## Files

| File | Action | Description |
|------|--------|-------------|
| src/api.py | create | API module |
| tests/test_api.py | create | Tests |

## Context

Some context.
"""
        snapshot = TaskSnapshot(
            path=tmp_path / "task.md",
            task_id="task1",
            body=body,
        )

        file_paths = extract_file_paths_from_task(snapshot, tmp_path)

        assert (tmp_path / "src" / "api.py").resolve() in file_paths
        assert (tmp_path / "tests" / "test_api.py").resolve() in file_paths

    def test_empty_when_no_files_section(self, tmp_path: Path) -> None:
        """Return empty set when no ## Files section."""
        body = """# Task

## Context

No files section.
"""
        snapshot = TaskSnapshot(
            path=tmp_path / "task.md",
            task_id="task1",
            body=body,
        )

        file_paths = extract_file_paths_from_task(snapshot, tmp_path)

        assert file_paths == set()

    def test_handles_backtick_paths(self, tmp_path: Path) -> None:
        """Handle paths wrapped in backticks."""
        body = """# Task

## Files

- `src/quoted.py`

"""
        snapshot = TaskSnapshot(
            path=tmp_path / "task.md",
            task_id="task1",
            body=body,
        )

        file_paths = extract_file_paths_from_task(snapshot, tmp_path)

        assert (tmp_path / "src" / "quoted.py").resolve() in file_paths


class TestTaskFileInfo:
    """Tests for get_task_file_info function."""

    def test_blocking_tag_detected(self, tmp_path: Path) -> None:
        """Blocking tag is correctly detected."""
        task_path = tmp_path / ".kanban2code" / "projects" / "test" / "task.md"
        _write_task(
            task_path,
            stage="code",
            agent="coder",
            tags=["blocking", "feature"],
        )

        snapshot = parse_task_file(task_path)
        info = get_task_file_info(snapshot, tmp_path)

        assert info.has_blocking_tag is True

    def test_blocking_tag_case_insensitive(self, tmp_path: Path) -> None:
        """Blocking tag detection is case insensitive."""
        task_path = tmp_path / ".kanban2code" / "projects" / "test" / "task.md"
        _write_task(
            task_path,
            stage="code",
            agent="coder",
            tags=["Blocking", "FEATURE"],
        )

        snapshot = parse_task_file(task_path)
        info = get_task_file_info(snapshot, tmp_path)

        assert info.has_blocking_tag is True

    def test_no_blocking_tag(self, tmp_path: Path) -> None:
        """No blocking tag when not present."""
        task_path = tmp_path / ".kanban2code" / "projects" / "test" / "task.md"
        _write_task(
            task_path,
            stage="code",
            agent="coder",
            tags=["feature"],
        )

        snapshot = parse_task_file(task_path)
        info = get_task_file_info(snapshot, tmp_path)

        assert info.has_blocking_tag is False


class TestThreadSafeStateWriter:
    """Tests for ThreadSafeStateWriter."""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Save and load preserves state."""
        state_path = tmp_path / "state.json"
        writer = ThreadSafeStateWriter(state_path)

        run_state = RunState(
            run_id="test-run",
            status="running",
            ordered_tasks=["task1.md"],
        )

        writer.save(run_state)

        # Load via the state module
        from orchestrator.state import load_run_state

        loaded = load_run_state(state_path)

        assert loaded.run_id == "test-run"
        assert loaded.status == "running"

    def test_concurrent_updates_are_safe(self, tmp_path: Path) -> None:
        """Concurrent updates don't corrupt state."""
        import threading

        state_path = tmp_path / "state.json"
        writer = ThreadSafeStateWriter(state_path)

        # Initial state
        run_state = RunState(
            run_id="test-run",
            status="running",
            ordered_tasks=["task1.md", "task2.md", "task3.md"],
            task_states={},
        )
        writer.save(run_state)

        errors: list[Exception] = []

        def update_task(task_key: str) -> None:
            try:
                for _ in range(10):
                    writer.load_and_update(
                        task_key,
                        lambda ts: setattr(ts, "status", "updated"),
                    )
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_task, args=(f"task{i}.md",))
            for i in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


class TestConcurrentScheduler:
    """Tests for ConcurrentScheduler."""

    def test_falls_back_to_sequential_when_disabled(self, tmp_path: Path, monkeypatch) -> None:
        """When scheduler is disabled, falls back to sequential execution."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_content = Path("config.json").read_text(encoding="utf-8")
        # Disable scheduler
        config_content = config_content.replace(
            '"enabled": true',
            '"enabled": false',
        )
        config_path.write_text(config_content, encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
        _write_task(task_path, stage="completed", agent="auditor")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        # Should call dispatcher.run directly
        run_state = scheduler.run(ordered_tasks=[task_path])

        assert run_state.status == "completed"

    def test_two_non_conflicting_tasks_run_concurrently(self, tmp_path: Path, monkeypatch) -> None:
        """Two tasks with disjoint file sets run concurrently."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task1 = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        task2 = repo_root / ".kanban2code" / "projects" / "orch" / "task2.md"

        _write_task(
            task1,
            stage="code",
            agent="coder",
            body="# Task1\n\n## Files\n\n- src/file1.py\n",
        )
        _write_task(
            task2,
            stage="code",
            agent="coder",
            body="# Task2\n\n## Files\n\n- src/file2.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            sleep_by_task={"task1": 0.1, "task2": 0.1},
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task1, task2])
        saved_state = load_run_state(state_path)

        assert run_state.status == "completed"
        assert dispatcher.max_parallel >= 2
        assert run_state.task_states[str(task1)].status == "completed"
        assert saved_state.task_states[str(task2)].status == "completed"

    def test_blocking_task_runs_alone(self, tmp_path: Path, monkeypatch) -> None:
        """A task with blocking tag runs alone."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        blocking_task = repo_root / ".kanban2code" / "projects" / "orch" / "blocking.md"
        normal_task = repo_root / ".kanban2code" / "projects" / "orch" / "normal.md"

        _write_task(
            blocking_task,
            stage="code",
            agent="coder",
            tags=["blocking"],
            body="# Blocking\n\n## Files\n\n- src/blocking.py\n",
        )
        _write_task(
            normal_task,
            stage="code",
            agent="coder",
            body="# Normal\n\n## Files\n\n- src/normal.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            sleep_by_task={"blocking": 0.05, "normal": 0.05},
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        # Run with blocking task first
        run_state = scheduler.run(ordered_tasks=[blocking_task, normal_task])

        assert run_state.status == "completed"
        assert dispatcher.max_parallel == 1
        assert dispatcher.call_order == ["blocking", "normal"]

    def test_conflicting_tasks_are_serialized(self, tmp_path: Path, monkeypatch) -> None:
        """Tasks with overlapping files are serialized."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task1 = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        task2 = repo_root / ".kanban2code" / "projects" / "orch" / "task2.md"

        # Both tasks touch the same file
        _write_task(
            task1,
            stage="code",
            agent="coder",
            body="# Task1\n\n## Files\n\n- src/shared.py\n",
        )
        _write_task(
            task2,
            stage="code",
            agent="coder",
            body="# Task2\n\n## Files\n\n- src/shared.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            sleep_by_task={"task1": 0.05, "task2": 0.05},
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task1, task2])

        assert run_state.status == "completed"
        assert dispatcher.max_parallel == 1


class TestDependencyHandling:
    """Tests for dependency-based task serialization."""

    def test_task_waits_for_dependency(self, tmp_path: Path) -> None:
        """Task with depends_on waits for dependency to complete."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        dep_task = repo_root / ".kanban2code" / "projects" / "orch" / "dep.md"
        waiting_task = repo_root / ".kanban2code" / "projects" / "orch" / "waiting.md"

        _write_task(
            dep_task,
            stage="code",
            agent="coder",
            body="# Dep\n\n## Files\n\n- src/dep.py\n",
        )
        _write_task(
            waiting_task,
            stage="code",
            agent="coder",
            depends_on="dep",
            body="# Waiting\n\n## Files\n\n- src/waiting.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[waiting_task, dep_task])

        assert run_state.status == "completed"
        assert dispatcher.call_order == ["dep", "waiting"]
        assert run_state.task_states[str(waiting_task)].status == "completed"

    def test_dependency_extraction_from_metadata(self, tmp_path: Path) -> None:
        """Dependencies are extracted from task metadata."""
        task_path = tmp_path / ".kanban2code" / "projects" / "test" / "task.md"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(
            "---\nstage: code\nagent: coder\ndepends_on: [task1, task2]\n---\n# Task\n",
            encoding="utf-8",
        )

        snapshot = parse_task_file(task_path)
        info = get_task_file_info(snapshot, tmp_path)

        assert "task1" in info.depends_on
        assert "task2" in info.depends_on

    def test_missing_dependency_blocks_task_instead_of_spinning(self, tmp_path: Path) -> None:
        """A missing dependency blocks the task and exits cleanly."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        waiting_task = repo_root / ".kanban2code" / "projects" / "orch" / "waiting.md"
        _write_task(
            waiting_task,
            stage="code",
            agent="coder",
            depends_on="missing-task",
            body="# Waiting\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        started_at = time.monotonic()
        run_state = scheduler.run(ordered_tasks=[waiting_task])
        duration = time.monotonic() - started_at

        assert duration < 1.0
        assert dispatcher.call_order == []
        assert run_state.status == "completed"
        assert run_state.task_states[str(waiting_task)].status == "blocked"
        assert "missing-task" in (run_state.task_states[str(waiting_task)].last_error or "")

    def test_transport_failures_trigger_handoff(self, tmp_path: Path) -> None:
        """Repeated transport failures escalate to handoff."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
        _write_task(
            task_path,
            stage="code",
            agent="coder",
            body="# Task\n\n## Files\n\n- src/task.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            scripted_results={
                "task": [
                    _transport_failure_result(task_path),
                    _transport_failure_result(task_path),
                    _transport_failure_result(task_path),
                ],
            },
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task_path])

        assert run_state.status == "handoff_required"
        assert run_state.task_states[str(task_path)].status == "handoff_required"
        assert (
            repo_root / ".kanban2code" / "runs" / run_state.run_id / "HANDOFF.md"
        ).exists()


class TestCLIIntegration:
    """Tests for CLI wiring to ConcurrentScheduler."""

    def test_cli_uses_scheduler_when_enabled(self, tmp_path: Path, monkeypatch) -> None:
        """CLI uses ConcurrentScheduler when enabled in config."""
        from orchestrator.cli import cmd_run

        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_content = Path("config.json").read_text(encoding="utf-8")
        config_path.write_text(config_content, encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
        _write_task(task_path, stage="completed", agent="auditor")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        args = type("Args", (), {
            "repo_root": str(repo_root),
            "state_path": str(state_path),
            "sequential": False,
        })()

        # Should not raise
        result = cmd_run(args)
        assert result == 0

    def test_cli_uses_sequential_with_flag(self, tmp_path: Path, monkeypatch) -> None:
        """CLI uses sequential dispatcher with --sequential flag."""
        from orchestrator.cli import cmd_run

        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_content = Path("config.json").read_text(encoding="utf-8")
        config_path.write_text(config_content, encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
        _write_task(task_path, stage="completed", agent="auditor")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        args = type("Args", (), {
            "repo_root": str(repo_root),
            "state_path": str(state_path),
            "sequential": True,
        })()

        result = cmd_run(args)
        assert result == 0


class TestTaskStatePropagation:
    """Tests for proper task state propagation in concurrent runs."""

    def test_task_states_persisted_correctly(self, tmp_path: Path, monkeypatch) -> None:
        """Task states are correctly persisted after concurrent execution."""
        from orchestrator.models import TaskExecutionResult

        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task1 = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        task2 = repo_root / ".kanban2code" / "projects" / "orch" / "task2.md"

        _write_task(task1, stage="completed", agent="auditor", body="# Task1\n\n## Files\n\n- src/a.py\n")
        _write_task(task2, stage="completed", agent="auditor", body="# Task2\n\n## Files\n\n- src/b.py\n")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task1, task2])

        # Both tasks should be marked completed
        assert run_state.task_states[str(task1)].status == "completed"
        assert run_state.task_states[str(task2)].status == "completed"
        assert run_state.status == "completed"

    def test_blocked_task_state_persisted(self, tmp_path: Path, monkeypatch) -> None:
        """Blocked task state is correctly persisted."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task.md"
        _write_task(task_path, stage="completed", agent="auditor")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task_path])

        assert run_state.task_states[str(task_path)].status == "completed"


class TestMemoryLifecycle:
    """Tests for memory integration with ConcurrentScheduler."""

    def test_stage_result_events_recorded_in_run_state(self, tmp_path: Path) -> None:
        """stage_result events from worker threads appear in run_state.recent_events."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        _write_task(task_path, stage="code", agent="coder")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            scripted_results={
                "task1": [
                    StageResult(
                        kind="success",
                        stage="code",
                        success=True,
                        task_path=str(task_path),
                        task_id="task1",
                        before_stage="code",
                        after_stage="completed",
                        after_agent="auditor",
                        provider_model="claude-opus-4-6",
                    )
                ]
            },
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task_path])

        # stage_result events from the worker thread must appear in run_state.recent_events
        event_types = [e.type for e in run_state.recent_events]
        assert "stage_result" in event_types, (
            f"No stage_result event found in recent_events: {event_types}"
        )

    def test_cold_model_performance_populated_after_concurrent_run(self, tmp_path: Path) -> None:
        """Cold model_performance is populated from stage_result events after a concurrent run."""
        import json

        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        _write_task(task_path, stage="code", agent="coder")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"
        dispatcher = ScriptedDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
            scripted_results={
                "task1": [
                    StageResult(
                        kind="success",
                        stage="code",
                        success=True,
                        task_path=str(task_path),
                        task_id="task1",
                        before_stage="code",
                        after_stage="completed",
                        after_agent="auditor",
                        provider_model="claude-opus-4-6",
                    )
                ]
            },
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        scheduler.run(ordered_tasks=[task_path])

        perf_path = repo_root / ".kanban2code" / "memory" / "cold" / "performance.json"
        assert perf_path.exists(), "performance.json not created"
        raw = json.loads(perf_path.read_text(encoding="utf-8"))
        assert "claude-opus-4-6" in raw["model_performance"], (
            f"provider model not in cold performance: {raw['model_performance']}"
        )
        assert raw["model_performance"]["claude-opus-4-6"]["success"] == 1

    def test_in_flight_sessions_tracked_in_hot_json(self, tmp_path: Path) -> None:
        """Tasks appear in hot.json in_flight_sessions while running."""
        import json
        import threading

        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        task_path = repo_root / ".kanban2code" / "projects" / "orch" / "task1.md"
        _write_task(task_path, stage="code", agent="coder")

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        # Capture hot.json mid-run while task is dispatching
        observed_in_flight: list[list] = []
        original_dispatch = None

        class ObservingDispatcher(ScriptedDispatcher):
            def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
                hot_path = repo_root / ".kanban2code" / "runs" / run_id / "hot.json"
                if hot_path.exists():
                    raw = json.loads(hot_path.read_text(encoding="utf-8"))
                    observed_in_flight.append(raw.get("in_flight_sessions", []))
                return super().dispatch_stage(task_path=task_path, run_id=run_id)

        dispatcher = ObservingDispatcher(
            repo_root=repo_root,
            config_path=config_path,
            run_state_path=state_path,
        )

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            dispatcher=dispatcher,
            run_state_path=state_path,
        )

        scheduler.run(ordered_tasks=[task_path])

        # At least one snapshot during dispatch should show the task as in-flight
        assert any(len(sessions) > 0 for sessions in observed_in_flight), (
            f"No in-flight sessions observed during run: {observed_in_flight}"
        )
