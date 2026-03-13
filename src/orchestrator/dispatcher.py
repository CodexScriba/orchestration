"""Stage dispatch and run-loop orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import logging

from orchestrator.accounts import AccountManager
from orchestrator.commits import commit_after_audit
from orchestrator.config import OrchestratorConfig, load_config
from orchestrator.evaluator import evaluate_stage_result
from orchestrator.logger import JsonlLogger
from orchestrator.models import FallbackChainEntry, ProviderAliasConfig, RunState, StageResult, TaskRunState
from orchestrator.notifier import Notifier
from orchestrator.prompts import assemble_prompt
from orchestrator.providers.base import BaseProvider, ProviderError
from orchestrator.providers.claude import ClaudeProvider
from orchestrator.providers.codex import CodexProvider
from orchestrator.providers.gemini import GeminiProvider
from orchestrator.providers.qwen import QwenProvider
from orchestrator.scanner import discover_task_files, parse_task_file, scan_tasks
from orchestrator.state import (
    append_recent_event,
    build_detailed_board_state,
    render_board_summary,
    save_run_state,
    write_handoff_readme,
)

_logger = logging.getLogger(__name__)

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
        account_manager: AccountManager | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.config = config or load_config(self.repo_root / "config.json")
        self.run_state_path = run_state_path or self.repo_root / ".kanban2code" / "runs" / "latest.json"
        self.logger = logger or JsonlLogger(self.repo_root / ".kanban2code" / "runs" / "events.jsonl")
        self.notifier = Notifier(self.config)
        pool = self.config.accounts.codex_pool
        self.account_manager = account_manager or (
            AccountManager(pool=pool) if pool else None
        )

    def dispatch_stage(self, *, task_path: Path, run_id: str) -> StageResult:
        """Run one stage for a task using fallback chain, evaluate the outcome."""

        before = parse_task_file(task_path)
        stage = before.stage
        provider_key = STAGE_PROVIDER_KEYS[stage]
        output_dir = self.repo_root / ".kanban2code" / "runs" / run_id / before.task_id / stage

        prompt = assemble_prompt(
            repo_root=self.repo_root,
            config=self.config,
            task_snapshot=before,
            run_id=run_id,
            current_stage=stage,
        )

        chain = self._get_fallback_chain(provider_key)
        last_invocation = None

        for entry in chain:
            alias_config = ProviderAliasConfig(
                alias=entry.alias,
                model=entry.model,
                config_overrides=entry.config_overrides,
            )
            try:
                provider = self._build_provider(entry.alias, alias_config)
            except (ValueError, ProviderError) as exc:
                _logger.warning("Skipping provider %r: %s", entry.alias, exc)
                continue

            if isinstance(provider, CodexProvider) and self.account_manager:
                try:
                    account = self.account_manager.get_account_for_task(before.task_id)
                    _logger.info(
                        "Codex account %r active for task %r stage %r",
                        account, before.task_id, stage,
                    )
                except Exception as exc:  # noqa: BLE001
                    _logger.error("Account rotation failed for task %r: %s", before.task_id, exc)
                    from orchestrator.models import InvocationResult  # noqa: PLC0415
                    return evaluate_stage_result(
                        config=self.config,
                        stage=stage,
                        before=before,
                        after=before,
                        invocation=InvocationResult(
                            ok=False,
                            error_message=f"Account rotation failed: {exc}",
                        ),
                        provider_key=provider_key,
                        provider_alias=entry.alias,
                        provider_model=None,
                    )

            session_name = provider.session_manager.create_session_name(
                run_id, before.task_id, stage
            )
            invocation = provider.invoke(
                prompt=prompt,
                task_path=task_path,
                output_dir=output_dir / session_name,
                timeouts=self.config.timeouts[stage],
            )
            last_invocation = invocation
            _logger.info(
                "Provider %r used for stage %r (ok=%s)", entry.alias, stage, invocation.ok
            )

            if invocation.ok:
                after = parse_task_file(task_path)
                return evaluate_stage_result(
                    config=self.config,
                    stage=stage,
                    before=before,
                    after=after,
                    invocation=invocation,
                    provider_key=provider_key,
                    provider_alias=entry.alias,
                    provider_model=entry.model or provider.provider_config.model,
                )

            _logger.warning(
                "Provider %r failed for stage %r: %s — trying next in chain.",
                entry.alias,
                stage,
                invocation.error_message,
            )

        # All providers in chain failed; evaluate with the last invocation result
        if last_invocation is None:
            # No provider could even be built
            from orchestrator.models import InvocationResult  # noqa: PLC0415
            last_invocation = InvocationResult(
                ok=False,
                error_message=f"No provider available for stage {stage!r}.",
            )
        after = parse_task_file(task_path)
        return evaluate_stage_result(
            config=self.config,
            stage=stage,
            before=before,
            after=after,
            invocation=last_invocation,
            provider_key=provider_key,
            provider_alias=chain[-1].alias if chain else "",
            provider_model=None,
        )

    def _get_fallback_chain(self, provider_key: str) -> list[FallbackChainEntry]:
        """Return the fallback chain for a provider key.

        Falls back to the single provider from config.providers when no chain is defined.
        """
        if provider_key in self.config.fallback_chains:
            return self.config.fallback_chains[provider_key]

        alias_config = self.config.providers[provider_key]
        return [
            FallbackChainEntry(
                alias=alias_config.alias,
                model=alias_config.model,
                config_overrides=alias_config.config_overrides,
            )
        ]

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

            if self.account_manager:
                snapshot = parse_task_file(task_path)
                self.account_manager.release_task(snapshot.task_id)

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

    def _build_provider(self, alias: str, alias_config: ProviderAliasConfig) -> BaseProvider:
        """Build the appropriate provider for the given alias.

        Provider type is determined by loading the frontmatter config and
        inspecting the 'provider' field, falling back to alias prefix matching.
        """
        provider_dir = self.repo_root / ".kanban2code" / "_providers"
        config_path = provider_dir / f"{alias}.md"

        # Determine provider type from frontmatter when available
        if config_path.exists():
            from orchestrator.scanner import split_frontmatter  # noqa: PLC0415
            metadata, _ = split_frontmatter(config_path.read_text(encoding="utf-8"))
            provider_type = str(metadata.get("provider", "")).strip().lower()
            cli = str(metadata.get("cli", "")).strip().lower()

            if provider_type == "anthropic" or cli == "claude":
                return ClaudeProvider(
                    repo_root=self.repo_root,
                    alias=alias,
                    alias_config=alias_config,
                )
            if provider_type == "google" or cli == "gemini":
                return GeminiProvider(
                    repo_root=self.repo_root,
                    alias=alias,
                    alias_config=alias_config,
                )
            if provider_type in ("moonshot", "zai") or cli in ("kimi", "kilo"):
                return QwenProvider(
                    repo_root=self.repo_root,
                    alias=alias,
                    alias_config=alias_config,
                )
            if provider_type in ("openai", "codex") or cli == "codex":
                return CodexProvider(
                    repo_root=self.repo_root,
                    alias=alias,
                    alias_config=alias_config,
                )

        # Fall back to alias prefix matching for backward compatibility
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
            provider_alias=result.provider_alias,
            provider_model=result.provider_model,
        )
        append_recent_event(run_state, event, self.config.logging.retain_recent_events)

        # Notify on stage change (success) or blocked
        if result.kind == "success":
            self.notifier.notify_stage_change(result)
        elif result.kind == "blocked":
            self.notifier.notify_escalation(result.task_id, result.kind, result.error_message or "Unknown block")

        self._update_board_state()

    def _update_board_state(self) -> None:
        """Update the global board state JSON and MD files."""
        kanban_root = self.repo_root / ".kanban2code"
        tasks = scan_tasks(kanban_root)

        # Update JSON
        board_state_path = kanban_root / "board_state.json"
        detailed_state = build_detailed_board_state(tasks)
        import json  # noqa: PLC0415
        board_state_path.write_text(
            json.dumps(detailed_state, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Update MD
        board_summary_path = kanban_root / "BOARD.md"
        summary = render_board_summary(tasks)
        board_summary_path.write_text(summary, encoding="utf-8")

    def _handoff(self, run_state: RunState, task_path: Path, reason: str) -> RunState:
        run_state.status = "handoff_required"
        run_state.last_error = reason
        task_snapshot = parse_task_file(task_path)
        handoff_path = self.repo_root / ".kanban2code" / "runs" / run_state.run_id / "HANDOFF.md"
        write_handoff_readme(
            path=handoff_path,
            run_state=run_state,
            task_snapshot=task_snapshot,
            reason=reason,
        )
        save_run_state(self.run_state_path, run_state)
        self.notifier.notify_escalation(task_snapshot.task_id, "handoff_required", reason)
        self._update_board_state()
        return run_state


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
