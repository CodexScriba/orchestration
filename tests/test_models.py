from __future__ import annotations

from pathlib import Path

from orchestrator.models import (
    AccountsConfig,
    AuditStageRoutingConfig,
    CodeStageRoutingConfig,
    InvocationResult,
    LoggingConfig,
    NotificationConfig,
    OrchestratorConfig,
    PlanStageRoutingConfig,
    ProviderAliasConfig,
    ProviderConfig,
    RunEvent,
    RunState,
    SessionResult,
    StageResult,
    RetryPolicyConfig,
    StageTimeoutConfig,
    TaskRunState,
    TaskSnapshot,
    TelegramNotificationConfig,
)


def test_config_models_construct_with_expected_defaults() -> None:
    provider = ProviderAliasConfig(alias="codex")
    provider_config = ProviderConfig(alias="codex", cli="codex", subcommand="exec")
    plan_routing = PlanStageRoutingConfig()
    code_routing = CodeStageRoutingConfig()
    audit_routing = AuditStageRoutingConfig()
    timeout = StageTimeoutConfig()
    invocation = InvocationResult()
    session = SessionResult()
    retry_policy = RetryPolicyConfig()
    accounts = AccountsConfig()
    telegram = TelegramNotificationConfig()
    notifications = NotificationConfig()
    logging = LoggingConfig()
    config = OrchestratorConfig()
    task = TaskSnapshot(path=Path("task.md"), task_id="task", project="orchestration")
    event = RunEvent()
    stage_result = StageResult()
    task_state = TaskRunState()
    run_state = RunState()

    assert provider.model is None
    assert provider.config_overrides == {}
    assert provider_config.prompt_style == "stdin"
    assert plan_routing.required_sections == []
    assert code_routing.required_sections == []
    assert audit_routing.accepted_rating == 8
    assert timeout.wall_seconds == 0
    assert invocation.output_paths == {}
    assert session.output_path == ""
    assert retry_policy.transport_max_attempts == 3
    assert accounts.codex_pool == []
    assert telegram.enabled is False
    assert notifications.telegram.bot_token_env_var == "ORCHESTRATOR_TELEGRAM_BOT_TOKEN"
    assert logging.retain_recent_events == 20
    assert config.schema_version == 1
    assert task.stage == ""
    assert task.tags == []
    assert event.extras == {}
    assert stage_result.kind == "transport_failure"
    assert task_state.status == "pending"
    assert run_state.ordered_tasks == []


def test_mutable_defaults_are_not_shared_between_instances() -> None:
    first_provider = ProviderAliasConfig(alias="codex")
    second_provider = ProviderAliasConfig(alias="codex")
    first_provider.config_overrides["mode"] = "medium"

    first_accounts = AccountsConfig()
    second_accounts = AccountsConfig()
    first_accounts.codex_pool.append("personal")

    first_config = OrchestratorConfig()
    second_config = OrchestratorConfig()
    first_config.providers["planner"] = ProviderAliasConfig(alias="codex-low")

    first_task = TaskSnapshot(path=Path("a.md"), task_id="a", project="inbox")
    second_task = TaskSnapshot(path=Path("b.md"), task_id="b", project="inbox")
    first_task.tags.append("feature")
    first_task.metadata["stage"] = "code"

    first_event = RunEvent()
    second_event = RunEvent()
    first_event.extras["provider"] = "codex"

    first_task_state = TaskRunState()
    second_task_state = TaskRunState()
    first_task_state.transport_attempts["plan"] = 1

    first_run_state = RunState()
    second_run_state = RunState()
    first_run_state.ordered_tasks.append("projects/orchestration/task.md")
    first_run_state.task_states["projects/orchestration/task.md"] = TaskRunState()
    first_run_state.recent_events.append(RunEvent(type="run_started"))

    assert second_provider.config_overrides == {}
    assert second_accounts.codex_pool == []
    assert second_config.providers == {}
    assert second_task.tags == []
    assert second_task.metadata == {}
    assert second_event.extras == {}
    assert second_task_state.transport_attempts == {}
    assert second_run_state.ordered_tasks == []
    assert second_run_state.task_states == {}
    assert second_run_state.recent_events == []
