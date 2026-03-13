"""Concurrent task scheduling with file-level conflict detection."""

from __future__ import annotations

from collections.abc import Callable
import logging
import os
import re
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from orchestrator.config import OrchestratorConfig, load_config
from orchestrator.logger import JsonlLogger
from orchestrator.models import (
    RunState,
    StageResult,
    TaskExecutionResult,
    TaskFileInfo,
    TaskRunState,
    TaskSnapshot,
)
from orchestrator.scanner import discover_task_files, parse_task_file
from orchestrator.state import append_recent_event, save_run_state

if TYPE_CHECKING:
    from orchestrator.dispatcher import Dispatcher

_logger = logging.getLogger(__name__)


class ThreadSafeStateWriter:
    """Thread-safe wrapper for run state persistence."""

    def __init__(self, path: Path) -> None:
        """Initialize the state writer.

        Args:
            path: Path to the run state JSON file.
        """
        self._path = path
        self._lock = threading.Lock()

    def save(self, run_state: RunState) -> None:
        """Persist run state under lock.

        Args:
            run_state: The run state to persist.
        """
        with self._lock:
            save_run_state(self._path, run_state)

    def load_and_update(
        self,
        task_key: str,
        updater: Callable[[TaskRunState], None],
    ) -> RunState:
        """Load state, apply update to a specific task, and save.

        Args:
            task_key: The task path string to update.
            updater: Function that receives TaskRunState and modifies it.

        Returns:
            The updated run state.
        """
        from orchestrator.state import load_run_state  # noqa: PLC0415

        with self._lock:
            run_state = load_run_state(self._path) if self._path.exists() else RunState()
            task_state = run_state.task_states.setdefault(task_key, TaskRunState())
            updater(task_state)
            save_run_state(self._path, run_state)
            return run_state


class ConflictDetector:
    """Detect file-level conflicts between tasks."""

    def __init__(self, repo_root: Path) -> None:
        """Initialize the conflict detector.

        Args:
            repo_root: The repository root path for resolving relative paths.
        """
        self._repo_root = Path(repo_root)
        self._running_files: dict[str, set[Path]] = {}
        self._lock = threading.Lock()

    def register_task(self, task_key: str, file_paths: set[Path]) -> None:
        """Register a task's file set as currently running.

        Args:
            task_key: The task path string.
            file_paths: Set of absolute file paths the task touches.
        """
        with self._lock:
            self._running_files[task_key] = file_paths

    def unregister_task(self, task_key: str) -> None:
        """Remove a task from the running set.

        Args:
            task_key: The task path string to remove.
        """
        with self._lock:
            self._running_files.pop(task_key, None)

    def has_conflict(self, file_paths: set[Path]) -> bool:
        """Check if the given file set conflicts with any running task.

        Args:
            file_paths: Set of absolute file paths to check.

        Returns:
            True if there is a conflict with a running task.
        """
        with self._lock:
            for running_files in self._running_files.values():
                if file_paths & running_files:
                    return True
            return False

    def get_conflicting_tasks(self, file_paths: set[Path]) -> list[str]:
        """Get list of running tasks that conflict with the given files.

        Args:
            file_paths: Set of absolute file paths to check.

        Returns:
            List of task keys that have conflicting file sets.
        """
        with self._lock:
            conflicts = []
            for task_key, running_files in self._running_files.items():
                if file_paths & running_files:
                    conflicts.append(task_key)
            return conflicts


def extract_file_paths_from_task(task_snapshot: TaskSnapshot, repo_root: Path) -> set[Path]:
    """Extract file paths from a task's body.

    Parses the ## Files section looking for:
    - List items starting with `-`
    - Table rows with path columns

    Args:
        task_snapshot: The task snapshot to extract files from.
        repo_root: The repository root for resolving relative paths.

    Returns:
        Set of absolute file paths the task touches.
    """
    body = task_snapshot.body
    file_paths: set[Path] = set()

    # Find ## Files section
    files_match = re.search(
        r"^##\s+Files\s*$\n(.*?)(?=^##\s|\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    )
    if not files_match:
        return file_paths

    files_section = files_match.group(1)

    # Parse list items: "- path/to/file.py"
    for match in re.finditer(r"^\s*-\s+(`?)([^`\s|]+)\1", files_section, re.MULTILINE):
        path_str = match.group(2).strip()
        if path_str and not path_str.startswith("#"):
            resolved = _resolve_path(path_str, repo_root)
            if resolved:
                file_paths.add(resolved)

    # Parse table rows: "| path/to/file.py | create | description |"
    for match in re.finditer(r"^\|\s*`?([^`|\s]+)`?\s*\|", files_section, re.MULTILINE):
        path_str = match.group(1).strip()
        if path_str and not path_str.startswith("#") and path_str != "File":
            resolved = _resolve_path(path_str, repo_root)
            if resolved:
                file_paths.add(resolved)

    return file_paths


def _resolve_path(path_str: str, repo_root: Path) -> Path | None:
    """Resolve a path string to an absolute path.

    Args:
        path_str: The path string from the task file.
        repo_root: The repository root.

    Returns:
        Absolute path, or None if the path is invalid.
    """
    # Clean up the path string
    path_str = path_str.strip("`")
    if not path_str or path_str.startswith("http"):
        return None

    try:
        path = Path(path_str)
        if path.is_absolute():
            return path.resolve()
        return (repo_root / path).resolve()
    except (OSError, ValueError):
        return None


def get_task_file_info(task_snapshot: TaskSnapshot, repo_root: Path) -> TaskFileInfo:
    """Get file information for a task including blocking status and dependencies.

    Args:
        task_snapshot: The task snapshot.
        repo_root: The repository root.

    Returns:
        TaskFileInfo with file paths, blocking status, and dependencies.
    """
    file_paths = extract_file_paths_from_task(task_snapshot, repo_root)
    has_blocking_tag = "blocking" in [tag.lower() for tag in task_snapshot.tags]

    # Extract dependencies from metadata
    depends_on: list[str] = []
    deps_value = task_snapshot.metadata.get("depends_on")
    if deps_value is not None:
        if isinstance(deps_value, str):
            depends_on = [deps_value]
        elif isinstance(deps_value, list):
            depends_on = [str(d) for d in deps_value if isinstance(d, str)]

    return TaskFileInfo(
        task_path=task_snapshot.path,
        task_id=task_snapshot.task_id,
        file_paths=file_paths,
        has_blocking_tag=has_blocking_tag,
        depends_on=depends_on,
    )


class ConcurrentScheduler:
    """Manage concurrent task execution with conflict detection."""

    def __init__(
        self,
        *,
        repo_root: Path,
        config: OrchestratorConfig | None = None,
        dispatcher: Dispatcher | None = None,
        logger: JsonlLogger | None = None,
        run_state_path: Path | None = None,
    ) -> None:
        """Initialize the concurrent scheduler.

        Args:
            repo_root: The repository root path.
            config: Optional orchestrator configuration.
            dispatcher: Optional dispatcher instance.
            logger: Optional JSONL logger.
            run_state_path: Optional path for run state file.
        """
        self.repo_root = Path(repo_root)
        self.config = config or load_config(self.repo_root / "config.json")
        self._dispatcher = dispatcher
        self._logger = logger
        self._run_state_path = run_state_path or self.repo_root / ".kanban2code" / "runs" / "latest.json"

        self._state_writer = ThreadSafeStateWriter(self._run_state_path)
        self._conflict_detector = ConflictDetector(self.repo_root)
        self._executor: ThreadPoolExecutor | None = None
        self._futures: dict[str, Future] = {}
        self._blocking_task_keys: set[str] = set()
        self._lock = threading.Lock()

    @property
    def dispatcher(self) -> Dispatcher:
        """Lazy-load the dispatcher if not provided."""
        if self._dispatcher is None:
            from orchestrator.dispatcher import Dispatcher  # noqa: PLC0415

            self._dispatcher = Dispatcher(
                repo_root=self.repo_root,
                config=self.config,
                logger=self._logger,
                run_state_path=self._run_state_path,
            )
        return self._dispatcher

    @property
    def logger(self) -> JsonlLogger:
        """Lazy-load the logger if not provided."""
        if self._logger is None:
            self._logger = JsonlLogger(
                self.repo_root / ".kanban2code" / "runs" / "events.jsonl"
            )
        return self._logger

    def run(
        self,
        *,
        ordered_tasks: list[Path] | None = None,
        run_state: RunState | None = None,
    ) -> RunState:
        """Run tasks concurrently with conflict detection.

        Args:
            ordered_tasks: Optional list of task paths to run.
            run_state: Optional existing run state to resume.

        Returns:
            Final run state after all tasks complete or handoff.
        """
        if not self.config.scheduler.enabled:
            # Fall back to sequential execution
            return self.dispatcher.run(ordered_tasks=ordered_tasks, run_state=run_state)

        active_run_state = run_state or self.dispatcher._new_run_state(ordered_tasks)
        ordered_task_paths = [Path(path) for path in active_run_state.ordered_tasks]
        self._state_writer.save(active_run_state)

        max_workers = self._compute_max_workers(len(ordered_task_paths))
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        try:
            return self._run_concurrent(active_run_state, ordered_task_paths)
        finally:
            self._executor.shutdown(wait=True)
            self._executor = None

    def _run_concurrent(
        self,
        run_state: RunState,
        ordered_task_paths: list[Path],
    ) -> RunState:
        """Execute the concurrent run loop.

        Args:
            run_state: The active run state.
            ordered_task_paths: List of task paths to process.

        Returns:
            Final run state.
        """
        pending_tasks: list[Path] = list(ordered_task_paths)
        completed_task_ids = self._discover_completed_task_ids()

        while pending_tasks or self._futures:
            # Collect completed futures
            self._collect_completed_futures(run_state, completed_task_ids)

            if run_state.status == "handoff_required":
                if self._futures:
                    time.sleep(0.05)
                    continue
                break

            # Submit new tasks if we have capacity
            submitted_count = self._submit_eligible_tasks(
                run_state,
                pending_tasks,
                completed_task_ids,
            )

            # Wait a bit if we're at capacity or waiting for conflicts
            if self._futures and not pending_tasks:
                time.sleep(0.05)
            elif not self._futures and pending_tasks:
                resolved_count = self._resolve_stalled_tasks(
                    run_state,
                    pending_tasks,
                    completed_task_ids,
                )
                if resolved_count == 0 and submitted_count == 0:
                    _logger.warning("Tasks pending but no capacity to run them")
                    time.sleep(0.05)

        if run_state.status != "handoff_required":
            run_state.status = "completed"
        run_state.current_task = None
        run_state.current_stage = None
        self._state_writer.save(run_state)
        return run_state

    def _collect_completed_futures(
        self,
        run_state: RunState,
        completed_task_ids: set[str],
    ) -> None:
        """Collect results from completed futures.

        Args:
            run_state: The run state to update.
            completed_task_ids: Set of completed task IDs.
            running_task_ids: Set of currently running task IDs.
        """
        with self._lock:
            done_futures = []
            for task_key, future in self._futures.items():
                if future.done():
                    done_futures.append(task_key)

            for task_key in done_futures:
                future = self._futures.pop(task_key)
                self._conflict_detector.unregister_task(task_key)

                try:
                    exec_result = future.result()
                    task_id = Path(task_key).stem

                    # Update run_state with the task's final state
                    run_state.task_states[task_key] = exec_result.task_state

                    if exec_result.task_state.status == "completed":
                        completed_task_ids.add(task_id)
                    elif exec_result.task_state.status == "handoff_required":
                        reason = exec_result.task_state.last_error or "Task execution requires handoff."
                        self._trigger_handoff(run_state, Path(task_key), reason)

                    self._handle_task_result(run_state, task_key, exec_result)
                except Exception as exc:
                    _logger.exception("Task %s raised exception", task_key)
                    task_state = run_state.task_states.setdefault(task_key, TaskRunState())
                    task_state.status = "handoff_required"
                    task_state.last_error = str(exc)
                    self._handle_task_error(run_state, task_key, str(exc))
                    self._trigger_handoff(
                        run_state,
                        Path(task_key),
                        f"Concurrent worker failed for {Path(task_key).name}: {exc}",
                    )

            if done_futures:
                self._state_writer.save(run_state)

    def _submit_eligible_tasks(
        self,
        run_state: RunState,
        pending_tasks: list[Path],
        completed_task_ids: set[str],
    ) -> int:
        """Submit tasks that are eligible to run.

        Args:
            run_state: The run state.
            pending_tasks: List of tasks not yet submitted.
            completed_task_ids: Set of completed task IDs.
            running_task_ids: Set of currently running task IDs.
        """
        if not self._executor:
            return 0

        max_concurrent = self._compute_max_workers(len(pending_tasks) + len(self._futures))
        available_slots = max_concurrent - len(self._futures)

        if available_slots <= 0:
            return 0

        submitted = []
        for task_path in pending_tasks:
            if available_slots <= 0:
                break

            task_key = str(task_path)
            task_snapshot = parse_task_file(task_path)
            task_info = get_task_file_info(task_snapshot, self.repo_root)

            # Check for blocking tag
            if task_info.has_blocking_tag:
                if self._futures:
                    # Wait for all running tasks to complete first
                    break
                # Run blocking task alone
                self._submit_task(task_key, task_info, run_state)
                submitted.append(task_path)
                available_slots -= 1
                break

            # Check for explicit dependencies
            if task_info.depends_on:
                unmet_deps = [
                    dep_id
                    for dep_id in task_info.depends_on
                    if dep_id not in completed_task_ids
                ]
                if unmet_deps:
                    _logger.info(
                        "[SCHEDULER:DEP] %s waiting for dependencies: %s",
                        task_snapshot.task_id,
                        unmet_deps,
                    )
                    continue

            # Check for file conflicts
            if self._conflict_detector.has_conflict(task_info.file_paths):
                conflicts = self._conflict_detector.get_conflicting_tasks(task_info.file_paths)
                _logger.info(
                    "[SCHEDULER:CONFLICT] %s blocked by %s",
                    task_snapshot.task_id,
                    [Path(k).stem for k in conflicts],
                )
                continue

            # Submit the task
            self._submit_task(task_key, task_info, run_state)
            submitted.append(task_path)
            available_slots -= 1

        # Remove submitted tasks from pending
        for task_path in submitted:
            pending_tasks.remove(task_path)

        return len(submitted)

    def _submit_task(
        self,
        task_key: str,
        task_info: TaskFileInfo,
        run_state: RunState,
    ) -> None:
        """Submit a task for execution.

        Args:
            task_key: The task path string.
            task_info: File info for conflict tracking.
            run_state: The run state.
            running_task_ids: Set of currently running task IDs.
        """
        if not self._executor:
            return

        task_path = Path(task_key)
        task_snapshot = parse_task_file(task_path)

        # Register files for conflict detection
        self._conflict_detector.register_task(task_key, task_info.file_paths)

        # Log dispatch
        _logger.info(
            "[SCHEDULER:DISPATCH] %s | slot: %d/%d | files: %d",
            task_snapshot.task_id,
            len(self._futures) + 1,
            self._compute_max_workers(0),
            len(task_info.file_paths),
        )

        # Submit to executor
        future = self._executor.submit(
            self._run_task_stages,
            task_path=task_path,
            run_id=run_state.run_id,
        )

        with self._lock:
            self._futures[task_key] = future

    def _run_task_stages(self, *, task_path: Path, run_id: str) -> TaskExecutionResult:
        """Run all stages for a single task.

        This is the worker function executed in a thread.

        Args:
            task_path: Path to the task file.
            run_id: The run ID.

        Returns:
            TaskExecutionResult with final stage result and task state.
        """
        from orchestrator.commits import commit_after_audit  # noqa: PLC0415

        task_key = str(task_path)
        task_state = TaskRunState()
        result: StageResult | None = None

        try:
            while True:
                snapshot = parse_task_file(task_path)

                if snapshot.stage == "completed":
                    task_state.status = "completed"
                    self._persist_task_state(task_key, task_state)
                    break

                result = self.dispatcher.dispatch_stage(
                    task_path=task_path,
                    run_id=run_id,
                )

                # Update local task state.
                task_state.last_stage = result.stage
                task_state.last_error = result.error_message
                task_state.status = result.kind

                if result.kind == "success":
                    if result.stage == "audit" and result.after_stage == "completed":
                        commit_after_audit(
                            repo_root=self.repo_root,
                            task_path=task_path,
                            rating=result.audit_rating or 0,
                            model=result.provider_model,
                            bounces=task_state.audit_failures,
                        )
                    if result.after_stage == "completed":
                        task_state.status = "completed"
                        self._persist_task_state(task_key, task_state)
                        break
                    self._persist_task_state(task_key, task_state)
                    continue

                if result.kind == "quality_failure":
                    task_state.audit_failures += 1
                    if (
                        task_state.audit_failures
                        > self.config.retry_policy.audit_failure_cycles_before_handoff
                    ):
                        task_state.status = "handoff_required"
                        task_state.last_error = (
                            f"Audit bounce limit exceeded for {task_path.name}."
                        )
                        self._persist_task_state(task_key, task_state)
                        break
                    self._persist_task_state(task_key, task_state)
                    continue

                if result.kind == "blocked":
                    task_state.status = "blocked"
                    self._persist_task_state(task_key, task_state)
                    break

                attempts = task_state.transport_attempts.get(result.stage, 0) + 1
                task_state.transport_attempts[result.stage] = attempts
                if attempts >= self.config.retry_policy.transport_max_attempts:
                    task_state.status = "handoff_required"
                    task_state.last_error = (
                        f"Transport retries exhausted for stage {result.stage}."
                    )
                    self._persist_task_state(task_key, task_state)
                    break

                self._persist_task_state(task_key, task_state)
        finally:
            if self.dispatcher.account_manager:
                self.dispatcher.account_manager.release_task(task_path.stem)

        return TaskExecutionResult(
            task_key=task_key,
            stage_result=result or StageResult(kind="completed", stage="completed"),
            task_state=task_state,
        )

    def _persist_task_state(self, task_key: str, task_state: TaskRunState) -> None:
        """Persist the latest task state under lock."""

        self._state_writer.load_and_update(
            task_key,
            lambda persisted: self._copy_task_state(persisted, task_state),
        )

    def _copy_task_state(self, target: TaskRunState, source: TaskRunState) -> None:
        """Copy all task-state fields into a persisted record."""

        target.status = source.status
        target.last_stage = source.last_stage
        target.last_error = source.last_error
        target.audit_failures = source.audit_failures
        target.transport_attempts = dict(source.transport_attempts)

    def _handle_task_result(
        self,
        run_state: RunState,
        task_key: str,
        exec_result: TaskExecutionResult,
    ) -> None:
        """Handle a completed task result.

        Args:
            run_state: The run state.
            task_key: The task path string.
            exec_result: The task execution result.
        """
        result = exec_result.stage_result
        task_status = exec_result.task_state.status
        event = self.logger.append(
            "task_complete",
            f"{Path(task_key).name} -> {task_status}",
            task=task_key,
            result=task_status,
        )
        append_recent_event(run_state, event, self.config.logging.retain_recent_events)

    def _handle_task_error(
        self,
        run_state: RunState,
        task_key: str,
        error_message: str,
    ) -> None:
        """Handle a task that raised an exception.

        Args:
            run_state: The run state.
            task_key: The task path string.
            error_message: The error message.
        """
        event = self.logger.append(
            "task_error",
            f"{Path(task_key).name} -> error: {error_message}",
            task=task_key,
            error=error_message,
        )
        append_recent_event(run_state, event, self.config.logging.retain_recent_events)

    def _discover_completed_task_ids(self) -> set[str]:
        """Discover completed task IDs across the Kanban workspace."""

        completed_task_ids: set[str] = set()
        kanban_root = self.repo_root / ".kanban2code"
        for task_path in discover_task_files(kanban_root):
            if parse_task_file(task_path).stage == "completed":
                completed_task_ids.add(task_path.stem)
        return completed_task_ids

    def _resolve_stalled_tasks(
        self,
        run_state: RunState,
        pending_tasks: list[Path],
        completed_task_ids: set[str],
    ) -> int:
        """Block tasks whose dependencies cannot currently be satisfied."""

        stalled_tasks: list[Path] = []
        for task_path in pending_tasks:
            task_info = get_task_file_info(parse_task_file(task_path), self.repo_root)
            unmet_dependencies = [
                dependency
                for dependency in task_info.depends_on
                if dependency not in completed_task_ids
            ]
            if not unmet_dependencies:
                continue

            task_key = str(task_path)
            task_state = run_state.task_states.setdefault(task_key, TaskRunState())
            task_state.status = "blocked"
            task_state.last_error = (
                "Unresolved dependencies: " + ", ".join(unmet_dependencies)
            )
            stalled_tasks.append(task_path)

            event = self.logger.append(
                "task_blocked",
                f"{task_path.name} blocked by unresolved dependencies",
                task=task_key,
                dependencies=unmet_dependencies,
            )
            append_recent_event(run_state, event, self.config.logging.retain_recent_events)

        for task_path in stalled_tasks:
            pending_tasks.remove(task_path)

        if stalled_tasks:
            self._state_writer.save(run_state)

        return len(stalled_tasks)

    def _trigger_handoff(self, run_state: RunState, task_path: Path, reason: str) -> None:
        """Promote the concurrent run into handoff-required state."""

        if run_state.status == "handoff_required":
            return

        run_state.current_task = str(task_path)
        task_state = run_state.task_states.get(str(task_path), TaskRunState())
        run_state.current_stage = task_state.last_stage
        self.dispatcher._handoff(run_state, task_path, reason)

    def _compute_max_workers(self, pending_count: int) -> int:
        """Compute the maximum number of concurrent workers.

        Args:
            pending_count: Number of pending tasks.

        Returns:
            Maximum number of workers.
        """
        cpu_count = os.cpu_count() or 4
        config_limit = self.config.scheduler.max_concurrent

        # Use minimum of config limit, CPU count, and pending tasks
        return min(config_limit, cpu_count, max(1, pending_count + len(self._futures)))
