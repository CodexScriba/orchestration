"""Three-layer operational memory system for context retention across runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path
import threading
from typing import Any

from orchestrator.models import MemoryConfig, RunEvent, RunState, TaskRunState

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HotMemory:
    """Hot layer: current run context (in-memory + state file)."""

    run_id: str = ""
    created_at: str = ""
    status: str = ""
    active_tasks: list[str] = field(default_factory=list)
    in_flight_sessions: list[dict[str, Any]] = field(default_factory=list)
    recent_events: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class WarmMemory:
    """Warm layer: recent project context (file-based)."""

    completed_tasks: list[dict[str, Any]] = field(default_factory=list)
    recent_decisions: list[dict[str, Any]] = field(default_factory=list)
    recent_errors: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ColdMemory:
    """Cold layer: historical patterns (file-based)."""

    stats: dict[str, Any] = field(default_factory=dict)
    failure_patterns: list[dict[str, Any]] = field(default_factory=list)
    model_performance: dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Manage three-layer memory system (hot, warm, cold)."""

    def __init__(
        self,
        repo_root: Path,
        config: MemoryConfig | None = None,
    ) -> None:
        """Initialize the memory manager.

        Args:
            repo_root: The repository root path.
            config: Optional memory configuration.
        """
        self.repo_root = Path(repo_root)
        self.config = config or MemoryConfig()
        self._hot: HotMemory | None = None
        self._lock = threading.Lock()

        # Ensure memory directories exist
        self._warm_dir = self.repo_root / ".kanban2code" / "memory" / "warm"
        self._cold_dir = self.repo_root / ".kanban2code" / "memory" / "cold"
        self._warm_dir.mkdir(parents=True, exist_ok=True)
        self._cold_dir.mkdir(parents=True, exist_ok=True)

    def init_hot_memory(self, run_state: RunState) -> None:
        """Initialize hot memory from a run state.

        Args:
            run_state: The current run state to mirror in hot memory.
        """
        self._hot = HotMemory(
            run_id=run_state.run_id,
            created_at=run_state.created_at,
            status=run_state.status,
            active_tasks=[
                task_path
                for task_path, task_state in run_state.task_states.items()
                if task_state.status not in ("completed", "blocked")
            ],
            in_flight_sessions=[],
            recent_events=[
                {
                    "timestamp": e.timestamp,
                    "type": e.type,
                    "message": e.message,
                    "extras": e.extras,
                }
                for e in run_state.recent_events[-20:]
            ],
        )
        self._persist_hot_memory()

    def update_hot_memory(self, run_state: RunState) -> None:
        """Update hot memory from current run state.

        Args:
            run_state: The current run state to update hot memory from.
        """
        if self._hot is None:
            self.init_hot_memory(run_state)
            return

        self._hot.status = run_state.status
        self._hot.active_tasks = [
            task_path
            for task_path, task_state in run_state.task_states.items()
            if task_state.status not in ("completed", "blocked")
        ]
        self._hot.recent_events = [
            {
                "timestamp": e.timestamp,
                "type": e.type,
                "message": e.message,
                "extras": e.extras,
            }
            for e in run_state.recent_events[-20:]
        ]
        self._persist_hot_memory()

    def _persist_hot_memory(self) -> None:
        """Persist hot memory to disk using the run_id stored in hot memory."""
        if self._hot is None:
            return

        hot_path = self.repo_root / ".kanban2code" / "runs" / self._hot.run_id / "hot.json"
        hot_path.parent.mkdir(parents=True, exist_ok=True)
        hot_path.write_text(
            json.dumps(asdict(self._hot), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def add_in_flight_session(self, session_info: dict[str, Any]) -> None:
        """Add a session to the in-flight sessions list.

        Args:
            session_info: Dict with at minimum a "task_key" field.
        """
        if self._hot is None:
            return
        self._hot.in_flight_sessions.append(session_info)
        self._persist_hot_memory()

    def remove_in_flight_session(self, task_key: str) -> None:
        """Remove a session from the in-flight sessions list by task_key.

        Args:
            task_key: The task path string to remove.
        """
        if self._hot is None:
            return
        self._hot.in_flight_sessions = [
            s for s in self._hot.in_flight_sessions if s.get("task_key") != task_key
        ]
        self._persist_hot_memory()

    def archive_hot_to_warm(self, run_state: RunState) -> None:
        """Archive hot memory to warm layer after run completion.

        Args:
            run_state: The completed run state to archive.
        """
        if self._hot is None:
            return

        # Group completed tasks by project
        project_tasks: dict[str, list[dict[str, Any]]] = {}

        for task_path, task_state in run_state.task_states.items():
            if task_state.status == "completed":
                # Extract project from task path
                # Task paths are like: .kanban2code/projects/{project}/task.md
                path_parts = Path(task_path).parts
                project = "unknown"
                if ".kanban2code" in path_parts:
                    kanban_idx = path_parts.index(".kanban2code")
                    if len(path_parts) > kanban_idx + 2:
                        if path_parts[kanban_idx + 1] == "projects":
                            project = path_parts[kanban_idx + 2]
                        elif path_parts[kanban_idx + 1] == "inbox":
                            project = "inbox"

                entry = {
                    "task_path": task_path,
                    "run_id": run_state.run_id,
                    "completed_at": run_state.updated_at,
                    "last_stage": task_state.last_stage,
                    "audit_failures": task_state.audit_failures,
                }
                project_tasks.setdefault(project, []).append(entry)

        # Append to warm memory for each project
        for project, tasks in project_tasks.items():
            for task in tasks:
                self._append_to_warm_project(project, "completed_tasks", task)

        # Archive errors from hot memory (capture task_error events and failed stage_result events)
        for event in self._hot.recent_events:
            extras = event.get("extras", {})
            is_task_error = event.get("type") == "task_error"
            has_error = bool(extras.get("error") or extras.get("error_message"))
            if is_task_error or has_error:
                error_entry = {
                    "timestamp": event["timestamp"],
                    "type": event["type"],
                    "message": event["message"],
                    "run_id": run_state.run_id,
                }
                # Add to all project warm memories (simplified)
                for project in project_tasks:
                    self._append_to_warm_project(project, "recent_errors", error_entry)

        # Aggregate to cold memory
        self._aggregate_to_cold(run_state)

        # Clear hot memory
        self._hot = None

    def _append_to_warm_project(
        self,
        project: str,
        category: str,
        entry: dict[str, Any],
    ) -> None:
        """Append an entry to warm memory for a project.

        Args:
            project: The project name.
            category: The category (completed_tasks, recent_decisions, recent_errors).
            entry: The entry to append.
        """
        warm_path = self._warm_dir / f"{project}.json"

        # Load existing warm memory
        warm = self._load_warm_memory(warm_path)

        # Append entry
        if category == "completed_tasks":
            warm.completed_tasks.append(entry)
            # Rotate if limit exceeded
            limit = self.config.warm_retention_per_project
            if len(warm.completed_tasks) > limit:
                warm.completed_tasks = warm.completed_tasks[-limit:]
        elif category == "recent_decisions":
            warm.recent_decisions.append(entry)
            if len(warm.recent_decisions) > 20:
                warm.recent_decisions = warm.recent_decisions[-20:]
        elif category == "recent_errors":
            warm.recent_errors.append(entry)
            if len(warm.recent_errors) > 20:
                warm.recent_errors = warm.recent_errors[-20:]

        # Save warm memory
        self._save_warm_memory(warm_path, warm)

    def _load_warm_memory(self, path: Path) -> WarmMemory:
        """Load warm memory from file.

        Args:
            path: Path to the warm memory file.

        Returns:
            WarmMemory instance.
        """
        if not path.exists():
            return WarmMemory()

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return WarmMemory(
                completed_tasks=raw.get("completed_tasks", []),
                recent_decisions=raw.get("recent_decisions", []),
                recent_errors=raw.get("recent_errors", []),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            _logger.warning("Corrupted warm memory file %s: %s", path, exc)
            return WarmMemory()

    def _save_warm_memory(self, path: Path, warm: WarmMemory) -> None:
        """Save warm memory to file.

        Args:
            path: Path to the warm memory file.
            warm: WarmMemory instance to save.
        """
        with self._lock:
            path.write_text(
                json.dumps(asdict(warm), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    def _aggregate_to_cold(self, run_state: RunState) -> None:
        """Aggregate run data to cold memory.

        Stats are always updated; failure patterns and model performance are
        only updated every ``cold_aggregation_interval`` runs.

        Args:
            run_state: The completed run state to aggregate.
        """
        # Load existing cold memory
        cold = self._load_cold_memory()

        # Always update run stats
        cold.stats["total_runs"] = cold.stats.get("total_runs", 0) + 1
        cold.stats["total_tasks"] = cold.stats.get("total_tasks", 0) + len(
            run_state.ordered_tasks
        )

        completed_count = sum(
            1
            for ts in run_state.task_states.values()
            if ts.status == "completed"
        )
        cold.stats["completed_tasks"] = cold.stats.get("completed_tasks", 0) + completed_count

        # Expensive aggregation: only run every cold_aggregation_interval runs
        interval = self.config.cold_aggregation_interval
        total_runs: int = cold.stats["total_runs"]
        if total_runs % interval == 0:
            # Update failure patterns
            for task_path, task_state in run_state.task_states.items():
                if task_state.status == "handoff_required":
                    pattern = {
                        "task_path": task_path,
                        "last_stage": task_state.last_stage,
                        "last_error": task_state.last_error,
                        "run_id": run_state.run_id,
                    }
                    cold.failure_patterns.append(pattern)
                    if len(cold.failure_patterns) > 100:
                        cold.failure_patterns = cold.failure_patterns[-100:]

            # Update model performance from recent events
            for event in run_state.recent_events:
                if event.type != "stage_result":
                    continue
                model = event.extras.get("provider_model")
                result_kind = event.extras.get("result")
                if not model:
                    continue
                perf = cold.model_performance.setdefault(
                    model, {"success": 0, "failure": 0, "total": 0}
                )
                perf["total"] += 1
                if result_kind == "success":
                    perf["success"] += 1
                else:
                    perf["failure"] += 1

        # Save cold memory
        self._save_cold_memory(cold)

    def _load_cold_memory(self) -> ColdMemory:
        """Load cold memory from files.

        Returns:
            ColdMemory instance.
        """
        cold = ColdMemory()

        # Load stats
        stats_path = self._cold_dir / "stats.json"
        if stats_path.exists():
            try:
                raw = json.loads(stats_path.read_text(encoding="utf-8"))
                cold.stats = raw.get("stats", {})
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                _logger.warning("Corrupted cold stats file: %s", exc)

        # Load failure patterns
        errors_path = self._cold_dir / "errors.json"
        if errors_path.exists():
            try:
                raw = json.loads(errors_path.read_text(encoding="utf-8"))
                cold.failure_patterns = raw.get("failure_patterns", [])
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                _logger.warning("Corrupted cold errors file: %s", exc)

        # Load model performance
        perf_path = self._cold_dir / "performance.json"
        if perf_path.exists():
            try:
                raw = json.loads(perf_path.read_text(encoding="utf-8"))
                cold.model_performance = raw.get("model_performance", {})
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                _logger.warning("Corrupted cold performance file: %s", exc)

        return cold

    def _save_cold_memory(self, cold: ColdMemory) -> None:
        """Save cold memory to files.

        Args:
            cold: ColdMemory instance to save.
        """
        with self._lock:
            # Save stats
            stats_path = self._cold_dir / "stats.json"
            stats_path.write_text(
                json.dumps({"stats": cold.stats}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            # Save failure patterns
            errors_path = self._cold_dir / "errors.json"
            errors_path.write_text(
                json.dumps(
                    {"failure_patterns": cold.failure_patterns},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            # Save model performance
            perf_path = self._cold_dir / "performance.json"
            perf_path.write_text(
                json.dumps(
                    {"model_performance": cold.model_performance},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

    def read_memory(
        self,
        layer: str,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Query memory by layer and optional topic.

        Args:
            layer: "hot", "warm", or "cold".
            topic: Optional filter (e.g., "errors", "decisions", "stats").

        Returns:
            dict with memory contents.
        """
        layer = layer.lower()

        if layer == "hot":
            if self._hot is None:
                return {}
            result = asdict(self._hot)
            if topic:
                return {topic: result.get(topic, [])}
            return result

        if layer == "warm":
            # Return warm memory for all projects or specific topic
            result: dict[str, Any] = {}
            for warm_path in self._warm_dir.glob("*.json"):
                project = warm_path.stem
                warm = self._load_warm_memory(warm_path)
                if topic:
                    result[project] = {topic: getattr(warm, topic, [])}
                else:
                    result[project] = asdict(warm)
            return result

        if layer == "cold":
            cold = self._load_cold_memory()
            result = asdict(cold)
            if topic:
                return {topic: result.get(topic, {})}
            return result

        return {}

    def append_to_warm(self, project: str, category: str, entry: dict[str, Any]) -> None:
        """Append an entry to warm memory for a project.

        Args:
            project: The project name.
            category: The category (completed_tasks, recent_decisions, recent_errors).
            entry: The entry to append.
        """
        self._append_to_warm_project(project, category, entry)

    def append_to_cold(self, category: str, entry: dict[str, Any]) -> None:
        """Append an entry to cold memory.

        Args:
            category: The category (stats, failure_patterns, model_performance).
            entry: The entry to append.
        """
        cold = self._load_cold_memory()

        if category == "stats":
            cold.stats.update(entry)
        elif category == "failure_patterns":
            cold.failure_patterns.append(entry)
            if len(cold.failure_patterns) > 100:
                cold.failure_patterns = cold.failure_patterns[-100:]
        elif category == "model_performance":
            cold.model_performance.update(entry)

        self._save_cold_memory(cold)