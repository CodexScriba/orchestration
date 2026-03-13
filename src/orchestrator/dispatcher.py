"""Stage dispatch and run-loop orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from orchestrator.commits import commit_after_audit
from orchestrator.config import OrchestratorConfig, load_config
from orchestrator.evaluator import evaluate_stage_result
from orchestrator.logger import JsonlLogger
from orchestrator.models import RunState, StageResult, TaskRunState
from orchestrator.prompts import assemble_prompt
from orchestrator.providers.codex import CodexProvider
from orchestrator.scanner import discover_task_files, parse_task_file
from orchestrator.state import append_recent_event, save_run_state, write_handoff_readme

STAGE_PROVIDER_KEYS = {
    "plan": "planner",
    "code": "coder",
    "audit": "auditor",
}


class Dispatcher:
    """Dispatch individual stages and full single-task runs."""

    def __init__(
        self,
        *,
        repo_root: Path,
        config: OrchestratorConfig | None = None,
        logger: JsonlLogger | None = None,
        run_state_path: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.config = config or load_config(self.repo_root / "config.json")
        self.run_state_path = run_state_path or self.repo_root / ".kanban2code" / "runs" / "latest.json"
        self.logger = logger or JsonlLogger(self.repo_root / ".kanban2code" / "runs" / "events.jsonl")

    def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
        """Run one stage for a task and evaluate the outcome."""

        before = parse_task_file(task_path)
        stage = before.stage
        provider_key = STAGE_PROVIDER_KEYS[stage]
        alias_config = self.config.providers[provider_key]
        provider = self._build_provider(alias_config.alias, alias_config)
        output_dir = self.repo_root / ".kanban2code" / "runs" / run_id / before.task_id / stage
        session_name = provider.session_manager.create_session_name(run_id, before.task_id, stage)

        prompt = assemble_prompt(
            repo_root=self.repo_root,
            config=self.config,
            task_snapshot=before,
            run_id=run_id,
            current_stage=stage,
        )
        invocation = provider.invoke(
            prompt=prompt,
            task_path=task_path,
            output_dir=output_dir / session_name,
            timeouts=self.config.timeouts[stage],
        )
        after = parse_task_file(task_path)
        return evaluate_stage_result(
            config=self.config,
            stage=stage,
            before=before,
            after=after,
            invocation=invocation,
            provider_key=provider_key,
            provider_alias=alias_config.alias,
            provider_model=alias_config.model or provider.provider_config.model,
        )

    def run(self, *, ordered_tasks: list[Path] | None = None, run_state: RunState | None = None) -> RunState:
        """Run queued tasks until completion, block, or handoff."""

        active_run_state = run_state or self._new_run_state(ordered_tasks)
        ordered_task_paths = [Path(path) for path in active_run_state.ordered_tasks]

        for index in range(active_run_state.current_index, len(ordered_task_paths)):
            task_path = ordered_task_paths[index]
            task_key = str(task_path)
            task_state = active_run_state.task_states.setdefault(task_key, TaskRunState())

            while True:
                snapshot = parse_task_file(task_path)
                active_run_state.current_index = index
                active_run_state.current_task = task_key
                active_run_state.current_stage = snapshot.stage
                save_run_state(self.run_state_path, active_run_state)

                if snapshot.stage == "completed":
                    task_state.status = "completed"
                    break

                result = self.dispatch_stage(task_path=task_path, run_id=active_run_state.run_id)
                self._record_stage_result(active_run_state, task_key, task_state, result)
                save_run_state(self.run_state_path, active_run_state)

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
                        break
                    continue

                if result.kind == "quality_failure":
                    task_state.audit_failures += 1
                    if (
                        task_state.audit_failures
                        > self.config.retry_policy.audit_failure_cycles_before_handoff
                    ):
                        return self._handoff(
                            active_run_state,
                            task_path,
                            f"Audit bounce limit exceeded for {task_path.name}.",
                        )
                    continue

                if result.kind == "blocked":
                    task_state.status = "blocked"
                    break

                attempts = task_state.transport_attempts.get(result.stage, 0) + 1
                task_state.transport_attempts[result.stage] = attempts
                if attempts >= self.config.retry_policy.transport_max_attempts:
                    return self._handoff(
                        active_run_state,
                        task_path,
                        f"Transport retries exhausted for stage {result.stage}.",
                    )

            if task_state.status != "completed" and task_state.status != "blocked":
                task_state.status = "completed"

        active_run_state.status = "completed"
        active_run_state.current_task = None
        active_run_state.current_stage = None
        save_run_state(self.run_state_path, active_run_state)
        return active_run_state

    def resume(self, run_state: RunState) -> RunState:
        """Resume a persisted run."""

        return self.run(run_state=run_state)

    def discover_ordered_tasks(self) -> list[Path]:
        """Discover runnable tasks from the Kanban root."""

        kanban_root = self.repo_root / ".kanban2code"
        task_files = discover_task_files(kanban_root)
        return [path for path in task_files if parse_task_file(path).stage != "completed"]

    def _build_provider(self, alias: str, alias_config) -> CodexProvider:
        if alias.startswith("codex"):
            return CodexProvider(
                repo_root=self.repo_root,
                alias=alias,
                alias_config=alias_config,
            )
        raise ValueError(f"Unsupported provider alias: {alias}")

    def _new_run_state(self, ordered_tasks: list[Path] | None) -> RunState:
        task_paths = ordered_tasks or self.discover_ordered_tasks()
        now = _utc_now_iso()
        return RunState(
            run_id=f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            created_at=now,
            updated_at=now,
            status="running",
            ordered_tasks=[str(path) for path in task_paths],
            task_states={str(path): TaskRunState() for path in task_paths},
        )

    def _record_stage_result(
        self,
        run_state: RunState,
        task_key: str,
        task_state: TaskRunState,
        result: StageResult,
    ) -> None:
        task_state.last_stage = result.stage
        task_state.last_error = result.error_message
        task_state.status = result.kind
        event = self.logger.append(
            "stage_result",
            f"{Path(task_key).name} {result.stage} -> {result.kind}",
            task=task_key,
            result=result.kind,
            after_stage=result.after_stage,
        )
        append_recent_event(run_state, event, self.config.logging.retain_recent_events)

    def _handoff(self, run_state: RunState, task_path: Path, reason: str) -> RunState:
        run_state.status = "handoff_required"
        run_state.last_error = reason
        handoff_path = self.repo_root / ".kanban2code" / "runs" / run_state.run_id / "HANDOFF.md"
        write_handoff_readme(
            path=handoff_path,
            run_state=run_state,
            task_snapshot=parse_task_file(task_path),
            reason=reason,
        )
        save_run_state(self.run_state_path, run_state)
        return run_state


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
