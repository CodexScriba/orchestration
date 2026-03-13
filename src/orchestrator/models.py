"""Typed configuration models for the orchestrator scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ProviderAliasConfig:
    """Provider alias settings for a stage-specific provider key."""

    alias: str = ""
    model: str | None = None
    config_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ProviderConfig:
    """Runtime provider configuration loaded from markdown frontmatter."""

    alias: str = ""
    cli: str = ""
    subcommand: str = ""
    model: str | None = None
    provider: str | None = None
    prompt_style: str = "stdin"
    unattended_flags: list[str] = field(default_factory=list)
    output_flags: list[str] = field(default_factory=list)
    config_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class PlanStageRoutingConfig:
    """Routing rules for the plan stage."""

    agent: str = ""
    success_stage: str = ""
    success_agent: str = ""
    required_sections: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CodeStageRoutingConfig:
    """Routing rules for the code stage."""

    agent: str = ""
    success_stage: str = ""
    success_agent: str = ""
    required_sections: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AuditStageRoutingConfig:
    """Routing rules for the audit stage."""

    agent: str = ""
    accepted_stage: str = ""
    accepted_agent: str = ""
    rework_stage: str = ""
    rework_agent: str = ""
    required_sections: list[str] = field(default_factory=list)
    accepted_rating: int = 8


@dataclass(slots=True)
class StageTimeoutConfig:
    """Timeout configuration for a single stage."""

    wall_seconds: int = 0
    idle_seconds: int = 0


@dataclass(slots=True)
class InvocationResult:
    """Outcome of a provider CLI invocation."""

    ok: bool = False
    exit_code: int | None = None
    timeout_type: str | None = None
    final_message: str | None = None
    output_paths: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None
    command: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SessionResult:
    """Result of a tmux-backed session execution."""

    ok: bool = False
    session_name: str = ""
    exit_code: int | None = None
    timeout_type: str | None = None
    output_path: str = ""
    prompt_path: str = ""
    exit_code_path: str = ""
    task_mutated: bool = False
    final_message: str | None = None
    command: list[str] = field(default_factory=list)
    error_message: str | None = None


@dataclass(slots=True)
class RetryPolicyConfig:
    """Retry and bounce limits for stage execution."""

    transport_max_attempts: int = 3
    audit_failure_cycles_before_handoff: int = 2


@dataclass(slots=True)
class AccountsConfig:
    """Account rotation settings."""

    codex_pool: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TelegramNotificationConfig:
    """Telegram notification settings using env var names."""

    enabled: bool = False
    bot_token_env_var: str = "ORCHESTRATOR_TELEGRAM_BOT_TOKEN"
    chat_id_env_var: str = "ORCHESTRATOR_TELEGRAM_CHAT_ID"


@dataclass(slots=True)
class NotificationConfig:
    """Notification settings for the orchestrator."""

    telegram: TelegramNotificationConfig = field(default_factory=TelegramNotificationConfig)


@dataclass(slots=True)
class LoggingConfig:
    """Logging settings for persisted orchestrator artifacts."""

    date_folder_format: str = "%Y-%m-%d"
    retain_recent_events: int = 20


@dataclass(slots=True)
class SchedulerConfig:
    """Concurrency and scheduling settings."""

    max_concurrent: int = 4
    enabled: bool = True


@dataclass(slots=True)
class TaskFileInfo:
    """File set information for a task, used in conflict detection."""

    task_path: Path = field(default_factory=lambda: Path("."))
    task_id: str = ""
    file_paths: set[Path] = field(default_factory=set)
    has_blocking_tag: bool = False
    depends_on: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FallbackChainEntry:
    """A single provider entry in a fallback chain."""

    alias: str = ""
    model: str | None = None
    config_overrides: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class OrchestratorConfig:
    """Top-level typed configuration for the orchestrator."""

    schema_version: int = 1
    providers: dict[str, ProviderAliasConfig] = field(default_factory=dict)
    fallback_chains: dict[str, list[FallbackChainEntry]] = field(default_factory=dict)
    stage_routing: dict[
        str,
        PlanStageRoutingConfig | CodeStageRoutingConfig | AuditStageRoutingConfig,
    ] = field(default_factory=dict)
    timeouts: dict[str, StageTimeoutConfig] = field(default_factory=dict)
    retry_policy: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)
    accounts: AccountsConfig = field(default_factory=AccountsConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)


@dataclass(slots=True)
class TaskSnapshot:
    """Typed snapshot of a Kanban2Code task file."""

    path: Path = field(default_factory=lambda: Path("."))
    task_id: str = ""
    project: str = ""
    stage: str = ""
    agent: str = ""
    bounces: int = 0
    tags: list[str] = field(default_factory=list)
    contexts: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)
    body: str = ""
    text: str = ""

    def __post_init__(self) -> None:
        """Normalize values after dataclass construction."""

        self.path = Path(self.path)
        self.stage = self.stage.strip().lower()
        self.agent = self.agent.strip().lower()
        self.tags = list(self.tags)
        self.contexts = list(self.contexts)
        self.metadata = dict(self.metadata)


@dataclass(slots=True)
class RunEvent:
    """Structured event stored in JSONL logs and run state."""

    timestamp: str = ""
    type: str = ""
    message: str = ""
    extras: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class StageResult:
    """Semantic outcome of a stage execution."""

    kind: str = "transport_failure"
    stage: str = ""
    success: bool = False
    task_path: str = ""
    task_id: str = ""
    provider_key: str = ""
    provider_alias: str = ""
    provider_model: str | None = None
    exit_code: int | None = None
    output_paths: dict[str, str] = field(default_factory=dict)
    error_message: str | None = None
    timeout_type: str | None = None
    final_message: str | None = None
    before_stage: str = ""
    after_stage: str = ""
    after_agent: str = ""
    audit_rating: int | None = None


@dataclass(slots=True)
class TaskRunState:
    """Execution state for a single queued task."""

    status: str = "pending"
    last_stage: str | None = None
    last_error: str | None = None
    audit_failures: int = 0
    transport_attempts: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class RunState:
    """Persisted execution state for an orchestrator run."""

    schema_version: int = 1
    run_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    status: str = ""
    ordered_tasks: list[str] = field(default_factory=list)
    task_states: dict[str, TaskRunState] = field(default_factory=dict)
    recent_events: list[RunEvent] = field(default_factory=list)
    current_index: int = 0
    current_task: str | None = None
    current_stage: str | None = None
    last_error: str | None = None


@dataclass(slots=True)
class TaskExecutionResult:
    """Result of executing a task through all its stages."""

    task_key: str = ""
    stage_result: StageResult | None = None
    task_state: TaskRunState = field(default_factory=TaskRunState)
