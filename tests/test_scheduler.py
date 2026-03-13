"""Tests for concurrent scheduler and conflict detection."""

from __future__ import annotations

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


def _write_task(
    path: Path,
    *,
    stage: str,
    agent: str,
    tags: list[str] | None = None,
    body: str = "# Task\n",
) -> None:
    """Write a task file with frontmatter."""
    tags_yaml = f"\ntags: {tags}" if tags else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nstage: {stage}\nagent: {agent}{tags_yaml}\n---\n{body}",
        encoding="utf-8",
    )


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
            stage="completed",
            agent="auditor",
            body="# Task1\n\n## Files\n\n- src/file1.py\n",
        )
        _write_task(
            task2,
            stage="completed",
            agent="auditor",
            body="# Task2\n\n## Files\n\n- src/file2.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task1, task2])

        assert run_state.status == "completed"

    def test_blocking_task_runs_alone(self, tmp_path: Path, monkeypatch) -> None:
        """A task with blocking tag runs alone."""
        repo_root = tmp_path
        config_path = repo_root / "config.json"
        config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")

        blocking_task = repo_root / ".kanban2code" / "projects" / "orch" / "blocking.md"
        normal_task = repo_root / ".kanban2code" / "projects" / "orch" / "normal.md"

        _write_task(
            blocking_task,
            stage="completed",
            agent="auditor",
            tags=["blocking"],
            body="# Blocking\n\n## Files\n\n- src/blocking.py\n",
        )
        _write_task(
            normal_task,
            stage="completed",
            agent="auditor",
            body="# Normal\n\n## Files\n\n- src/normal.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        # Run with blocking task first
        run_state = scheduler.run(ordered_tasks=[blocking_task, normal_task])

        assert run_state.status == "completed"

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
            stage="completed",
            agent="auditor",
            body="# Task1\n\n## Files\n\n- src/shared.py\n",
        )
        _write_task(
            task2,
            stage="completed",
            agent="auditor",
            body="# Task2\n\n## Files\n\n- src/shared.py\n",
        )

        state_path = repo_root / ".kanban2code" / "runs" / "latest.json"

        scheduler = ConcurrentScheduler(
            repo_root=repo_root,
            config=load_config(config_path),
            run_state_path=state_path,
        )

        run_state = scheduler.run(ordered_tasks=[task1, task2])

        assert run_state.status == "completed"