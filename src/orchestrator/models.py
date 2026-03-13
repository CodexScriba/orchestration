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
class OrchestratorConfig:
    """Top-level typed configuration for the orchestrator."""

    schema_version: int = 1
    providers: dict[str, ProviderAliasConfig] = field(default_factory=dict)
    stage_routing: dict[
        str,
        PlanStageRoutingConfig | CodeStageRoutingConfig | AuditStageRoutingConfig,
    ] = field(default_factory=dict)
    timeouts: dict[str, StageTimeoutConfig] = field(default_factory=dict)
    retry_policy: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)
    accounts: AccountsConfig = field(default_factory=AccountsConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


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
