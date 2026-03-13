"""JSON configuration loading and validation helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from orchestrator.models import (
    AccountsConfig,
    AuditStageRoutingConfig,
    CodeStageRoutingConfig,
    FallbackChainEntry,
    LoggingConfig,
    NotificationConfig,
    OrchestratorConfig,
    PlanStageRoutingConfig,
    ProviderAliasConfig,
    RetryPolicyConfig,
    StageTimeoutConfig,
    TelegramNotificationConfig,
)


class ConfigError(ValueError):
    """Raised when the orchestrator configuration is missing or invalid."""


def load_config(path: str | Path = "config.json") -> OrchestratorConfig:
    """Load and validate the orchestrator configuration from JSON.

    Args:
        path: Path to the JSON config file.

    Returns:
        A typed orchestrator configuration object.

    Raises:
        ConfigError: If the file is missing, invalid JSON, or fails validation.
    """

    config_path = Path(path)
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc

    try:
        raw_config = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        message = (
            f"Invalid JSON in config file {config_path}: "
            f"{exc.msg} (line {exc.lineno} column {exc.colno})"
        )
        raise ConfigError(message) from exc

    if not isinstance(raw_config, dict):
        raise ConfigError("Invalid config type for <root>: expected object")

    raw_fallback_chains = raw_config.get("fallback_chains")
    fallback_chains = (
        _parse_fallback_chains(raw_fallback_chains)
        if isinstance(raw_fallback_chains, Mapping)
        else {}
    )

    return OrchestratorConfig(
        schema_version=_require_int(raw_config, "schema_version"),
        providers=_parse_providers(_require_mapping(raw_config, "providers")),
        fallback_chains=fallback_chains,
        stage_routing=_parse_stage_routing(_require_mapping(raw_config, "stage_routing")),
        timeouts=_parse_timeouts(_require_mapping(raw_config, "timeouts")),
        retry_policy=_parse_retry_policy(_require_mapping(raw_config, "retry_policy"), "retry_policy"),
        accounts=_parse_accounts(_require_mapping(raw_config, "accounts"), "accounts"),
        notifications=_parse_notifications(
            _require_mapping(raw_config, "notifications"),
            "notifications",
        ),
        logging=_parse_logging(_require_mapping(raw_config, "logging"), "logging"),
    )


def _parse_providers(raw_providers: Mapping[str, object]) -> dict[str, ProviderAliasConfig]:
    providers: dict[str, ProviderAliasConfig] = {}
    for provider_key in ("planner", "coder", "auditor", "auditor_escalation"):
        provider_path = f"providers.{provider_key}"
        provider_mapping = _require_mapping(raw_providers, provider_key, "providers")
        providers[provider_key] = ProviderAliasConfig(
            alias=_require_str(provider_mapping, "alias", provider_path),
            model=_require_optional_str(provider_mapping, "model", provider_path),
            config_overrides=_require_string_key_dict(
                provider_mapping,
                "config_overrides",
                provider_path,
            ),
        )
    return providers


def _parse_fallback_chains(
    raw_chains: Mapping[str, object],
) -> dict[str, list[FallbackChainEntry]]:
    chains: dict[str, list[FallbackChainEntry]] = {}
    for stage_key, raw_list in raw_chains.items():
        if not isinstance(raw_list, list):
            raise ConfigError(
                f"Invalid config type for fallback_chains.{stage_key}: expected list"
            )
        entries: list[FallbackChainEntry] = []
        for i, item in enumerate(raw_list):
            item_path = f"fallback_chains.{stage_key}[{i}]"
            if not isinstance(item, Mapping):
                raise ConfigError(f"Invalid config type for {item_path}: expected object")
            entries.append(
                FallbackChainEntry(
                    alias=_require_str(item, "alias", item_path),
                    model=_require_optional_str(item, "model", item_path) if "model" in item else None,
                    config_overrides=(
                        _require_string_key_dict(item, "config_overrides", item_path)
                        if "config_overrides" in item
                        else {}
                    ),
                )
            )
        chains[stage_key] = entries
    return chains


def _parse_stage_routing(
    raw_stage_routing: Mapping[str, object],
) -> dict[str, PlanStageRoutingConfig | CodeStageRoutingConfig | AuditStageRoutingConfig]:
    return {
        "plan": _parse_plan_stage_routing(
            _require_mapping(raw_stage_routing, "plan", "stage_routing"),
            "stage_routing.plan",
        ),
        "code": _parse_code_stage_routing(
            _require_mapping(raw_stage_routing, "code", "stage_routing"),
            "stage_routing.code",
        ),
        "audit": _parse_audit_stage_routing(
            _require_mapping(raw_stage_routing, "audit", "stage_routing"),
            "stage_routing.audit",
        ),
    }


def _parse_plan_stage_routing(
    raw_stage: Mapping[str, object],
    path: str,
) -> PlanStageRoutingConfig:
    return PlanStageRoutingConfig(
        agent=_require_str(raw_stage, "agent", path),
        success_stage=_require_str(raw_stage, "success_stage", path),
        success_agent=_require_str(raw_stage, "success_agent", path),
        required_sections=_require_string_list(raw_stage, "required_sections", path),
    )


def _parse_code_stage_routing(
    raw_stage: Mapping[str, object],
    path: str,
) -> CodeStageRoutingConfig:
    return CodeStageRoutingConfig(
        agent=_require_str(raw_stage, "agent", path),
        success_stage=_require_str(raw_stage, "success_stage", path),
        success_agent=_require_str(raw_stage, "success_agent", path),
        required_sections=_require_string_list(raw_stage, "required_sections", path),
    )


def _parse_audit_stage_routing(
    raw_stage: Mapping[str, object],
    path: str,
) -> AuditStageRoutingConfig:
    return AuditStageRoutingConfig(
        agent=_require_str(raw_stage, "agent", path),
        accepted_stage=_require_str(raw_stage, "accepted_stage", path),
        accepted_agent=_require_str(raw_stage, "accepted_agent", path),
        rework_stage=_require_str(raw_stage, "rework_stage", path),
        rework_agent=_require_str(raw_stage, "rework_agent", path),
        required_sections=_require_string_list(raw_stage, "required_sections", path),
        accepted_rating=_require_int(raw_stage, "accepted_rating", path),
    )


def _parse_timeouts(raw_timeouts: Mapping[str, object]) -> dict[str, StageTimeoutConfig]:
    return {
        stage_name: _parse_stage_timeout(
            _require_mapping(raw_timeouts, stage_name, "timeouts"),
            f"timeouts.{stage_name}",
        )
        for stage_name in ("plan", "code", "audit")
    }


def _parse_stage_timeout(raw_timeout: Mapping[str, object], path: str) -> StageTimeoutConfig:
    return StageTimeoutConfig(
        wall_seconds=_require_int(raw_timeout, "wall_seconds", path),
        idle_seconds=_require_int(raw_timeout, "idle_seconds", path),
    )


def _parse_retry_policy(raw_retry_policy: Mapping[str, object], path: str) -> RetryPolicyConfig:
    return RetryPolicyConfig(
        transport_max_attempts=_require_int(raw_retry_policy, "transport_max_attempts", path),
        audit_failure_cycles_before_handoff=_require_int(
            raw_retry_policy,
            "audit_failure_cycles_before_handoff",
            path,
        ),
    )


def _parse_accounts(raw_accounts: Mapping[str, object], path: str) -> AccountsConfig:
    return AccountsConfig(
        codex_pool=_require_string_list(raw_accounts, "codex_pool", path),
    )


def _parse_notifications(raw_notifications: Mapping[str, object], path: str) -> NotificationConfig:
    raw_telegram = _require_mapping(raw_notifications, "telegram", path)
    return NotificationConfig(
        telegram=TelegramNotificationConfig(
            enabled=_require_bool(raw_telegram, "enabled", f"{path}.telegram"),
            bot_token_env_var=_require_str(
                raw_telegram,
                "bot_token_env_var",
                f"{path}.telegram",
            ),
            chat_id_env_var=_require_str(
                raw_telegram,
                "chat_id_env_var",
                f"{path}.telegram",
            ),
        )
    )


def _parse_logging(raw_logging: Mapping[str, object], path: str) -> LoggingConfig:
    return LoggingConfig(
        date_folder_format=_require_str(raw_logging, "date_folder_format", path),
        retain_recent_events=_require_int(raw_logging, "retain_recent_events", path),
    )


def _require_mapping(
    data: Mapping[str, object],
    key: str,
    parent_path: str | None = None,
) -> Mapping[str, object]:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if not isinstance(value, Mapping):
        raise ConfigError(f"Invalid config type for {full_path}: expected object")

    return value


def _require_string_key_dict(
    data: Mapping[str, object],
    key: str,
    parent_path: str,
) -> dict[str, object]:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if not isinstance(value, Mapping):
        raise ConfigError(f"Invalid config type for {full_path}: expected object")

    return {str(item_key): item_value for item_key, item_value in value.items()}


def _require_string_list(data: Mapping[str, object], key: str, parent_path: str) -> list[str]:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if not isinstance(value, list):
        raise ConfigError(f"Invalid config type for {full_path}: expected list[str]")
    if not all(isinstance(item, str) for item in value):
        raise ConfigError(f"Invalid config type for {full_path}: expected list[str]")

    return list(value)


def _require_str(data: Mapping[str, object], key: str, parent_path: str | None = None) -> str:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config type for {full_path}: expected str")

    return value


def _require_optional_str(
    data: Mapping[str, object],
    key: str,
    parent_path: str | None = None,
) -> str | None:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"Invalid config type for {full_path}: expected str | null")

    return value


def _require_int(data: Mapping[str, object], key: str, parent_path: str | None = None) -> int:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"Invalid config type for {full_path}: expected int")

    return value


def _require_bool(data: Mapping[str, object], key: str, parent_path: str | None = None) -> bool:
    full_path = _join_path(parent_path, key)
    if key not in data:
        raise ConfigError(f"Missing required config key: {full_path}")

    value = data[key]
    if not isinstance(value, bool):
        raise ConfigError(f"Invalid config type for {full_path}: expected bool")

    return value


def _join_path(parent_path: str | None, key: str) -> str:
    if not parent_path:
        return key
    return f"{parent_path}.{key}"
