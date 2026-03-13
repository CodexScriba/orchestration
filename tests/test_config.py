from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.config import ConfigError, load_config
from orchestrator.models import OrchestratorConfig


def test_load_config_returns_typed_dataclass(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_build_valid_config_data()), encoding="utf-8")

    config = load_config(config_path)

    assert isinstance(config, OrchestratorConfig)
    assert config.schema_version == 1
    assert config.providers["planner"].alias == "codex-low"
    assert config.stage_routing["plan"].success_stage == "code"
    assert config.timeouts["audit"].idle_seconds == 180
    assert config.notifications.telegram.bot_token_env_var == "ORCHESTRATOR_TELEGRAM_BOT_TOKEN"


def test_load_config_reports_missing_required_nested_key(tmp_path: Path) -> None:
    config_data = _build_valid_config_data()
    del config_data["stage_routing"]["plan"]["success_stage"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(
        ConfigError,
        match=r"Missing required config key: stage_routing\.plan\.success_stage",
    ):
        load_config(config_path)


def test_load_config_reports_invalid_json(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ConfigError, match=r"Invalid JSON in config file"):
        load_config(config_path)


def test_shipped_config_json_parses_successfully() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(repo_root / "config.json")

    assert config.providers["coder"].alias == "codex"
    assert config.retry_policy.transport_max_attempts == 3
    assert config.accounts.codex_pool == ["personal", "work", "home"]


def _build_valid_config_data() -> dict[str, object]:
    return {
        "schema_version": 1,
        "providers": {
            "planner": {
                "alias": "codex-low",
                "model": None,
                "config_overrides": {},
            },
            "coder": {
                "alias": "codex",
                "model": None,
                "config_overrides": {},
            },
            "auditor": {
                "alias": "codex-high",
                "model": None,
                "config_overrides": {},
            },
            "auditor_escalation": {
                "alias": "codex-xhigh",
                "model": None,
                "config_overrides": {},
            },
        },
        "stage_routing": {
            "plan": {
                "agent": "planner",
                "success_stage": "code",
                "success_agent": "coder",
                "required_sections": ["## Refined Prompt", "## Context"],
            },
            "code": {
                "agent": "coder",
                "success_stage": "audit",
                "success_agent": "auditor",
                "required_sections": ["## Audit"],
            },
            "audit": {
                "agent": "auditor",
                "accepted_stage": "completed",
                "accepted_agent": "auditor",
                "rework_stage": "code",
                "rework_agent": "coder",
                "required_sections": ["## Review"],
                "accepted_rating": 8,
            },
        },
        "timeouts": {
            "plan": {"wall_seconds": 600, "idle_seconds": 120},
            "code": {"wall_seconds": 1800, "idle_seconds": 300},
            "audit": {"wall_seconds": 1200, "idle_seconds": 180},
        },
        "retry_policy": {
            "transport_max_attempts": 3,
            "audit_failure_cycles_before_handoff": 2,
        },
        "accounts": {
            "codex_pool": ["personal", "work", "home"],
        },
        "notifications": {
            "telegram": {
                "enabled": False,
                "bot_token_env_var": "ORCHESTRATOR_TELEGRAM_BOT_TOKEN",
                "chat_id_env_var": "ORCHESTRATOR_TELEGRAM_CHAT_ID",
            }
        },
        "logging": {
            "date_folder_format": "%Y-%m-%d",
            "retain_recent_events": 20,
        },
    }
