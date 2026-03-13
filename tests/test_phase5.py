"""Tests for Phase 5: Communication and Monitoring."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import TelegramError

from orchestrator.config import load_config
from orchestrator.dispatcher import Dispatcher
from orchestrator.models import InvocationResult, StageResult, TaskSnapshot
from orchestrator.notifier import Notifier
from orchestrator.smoke import SmokeTester
from orchestrator.state import build_detailed_board_state, render_board_summary


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.notifications.telegram.enabled = True
    config.notifications.telegram.bot_token_env_var = "TEST_TOKEN"
    config.notifications.telegram.chat_id_env_var = "TEST_CHAT_ID"
    return config


# =============================================================================
# Notifier Tests
# =============================================================================


@patch("orchestrator.notifier.Bot")
@patch("os.environ.get")
def test_notifier_sends_message(mock_env_get, mock_bot_class, mock_config):
    mock_env_get.side_effect = lambda k: "val" if k in ["TEST_TOKEN", "TEST_CHAT_ID"] else None
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_class.return_value = mock_bot
    mock_bot.__aenter__.return_value = mock_bot

    notifier = Notifier(mock_config)
    result = StageResult(
        task_id="task1",
        before_stage="plan",
        after_stage="code",
        after_agent="coder",
        provider_alias="test-provider",
        kind="success"
    )

    notifier.notify_stage_change(result)

    assert mock_bot.send_message.called
    args, kwargs = mock_bot.send_message.call_args
    assert "task1" in kwargs["text"]
    assert "plan" in kwargs["text"]
    assert "code" in kwargs["text"]


@patch("orchestrator.notifier.Bot")
@patch("os.environ.get")
def test_notifier_includes_required_fields(mock_env_get, mock_bot_class, mock_config):
    """Notification includes task ID, stage transition, agent, and provider info."""
    mock_env_get.side_effect = lambda k: "val" if k in ["TEST_TOKEN", "TEST_CHAT_ID"] else None
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_class.return_value = mock_bot
    mock_bot.__aenter__.return_value = mock_bot

    notifier = Notifier(mock_config)
    result = StageResult(
        task_id="task-abc123",
        before_stage="plan",
        after_stage="code",
        after_agent="coder",
        provider_alias="claude-sonnet",
        provider_model="claude-sonnet-4",
        kind="success"
    )

    notifier.notify_stage_change(result)

    args, kwargs = mock_bot.send_message.call_args
    message_text = kwargs["text"]

    # Verify all required fields are present
    assert "task-abc123" in message_text
    assert "plan" in message_text
    assert "code" in message_text
    assert "coder" in message_text
    assert "claude-sonnet" in message_text
    assert "claude-sonnet-4" in message_text


@patch("orchestrator.notifier.Bot")
@patch("os.environ.get")
def test_notifier_failure_does_not_block(mock_env_get, mock_bot_class, mock_config):
    """Notification errors are logged but do not block execution."""
    mock_env_get.side_effect = lambda k: "val" if k in ["TEST_TOKEN", "TEST_CHAT_ID"] else None
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(side_effect=TelegramError("API error"))
    mock_bot_class.return_value = mock_bot
    mock_bot.__aenter__.return_value = mock_bot

    notifier = Notifier(mock_config)
    result = StageResult(
        task_id="task1",
        before_stage="plan",
        after_stage="code",
        after_agent="coder",
        provider_alias="test-provider",
        kind="success"
    )

    # Should not raise, just log the error
    notifier.notify_stage_change(result)

    assert mock_bot.send_message.called


@patch("os.environ.get")
def test_notifier_disabled_when_credentials_missing(mock_env_get, mock_config):
    """Notifier is disabled when bot token or chat ID are missing."""
    mock_env_get.side_effect = lambda k: None  # No credentials

    notifier = Notifier(mock_config)

    assert not notifier._enabled


@patch("os.environ.get")
def test_notifier_uses_config_env_vars(mock_env_get):
    """Bot token and chat ID are loaded from configured env var names."""
    custom_config = MagicMock()
    custom_config.notifications.telegram.enabled = True
    custom_config.notifications.telegram.bot_token_env_var = "CUSTOM_BOT_TOKEN"
    custom_config.notifications.telegram.chat_id_env_var = "CUSTOM_CHAT_ID"

    def env_side_effect(key):
        if key == "CUSTOM_BOT_TOKEN":
            return "my-bot-token"
        if key == "CUSTOM_CHAT_ID":
            return "my-chat-id"
        return None

    mock_env_get.side_effect = env_side_effect

    notifier = Notifier(custom_config)

    assert notifier._enabled
    assert notifier._bot_token == "my-bot-token"
    assert notifier._chat_id == "my-chat-id"


@patch("orchestrator.notifier.Bot")
@patch("os.environ.get")
def test_notifier_sends_escalation_message(mock_env_get, mock_bot_class, mock_config):
    """Escalation notifications include task ID, state, and reason."""
    mock_env_get.side_effect = lambda k: "val" if k in ["TEST_TOKEN", "TEST_CHAT_ID"] else None
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_class.return_value = mock_bot
    mock_bot.__aenter__.return_value = mock_bot

    notifier = Notifier(mock_config)

    notifier.notify_escalation(
        task_id="task-xyz",
        state="blocked",
        reason="Missing dependency: config.json"
    )

    args, kwargs = mock_bot.send_message.call_args
    message_text = kwargs["text"]

    assert "task-xyz" in message_text
    assert "blocked" in message_text
    assert "Missing dependency" in message_text


def test_board_state_generation(tmp_path):
    task_path = tmp_path / "task1.md"
    task_path.write_text("---\nstage: code\nagent: coder\n---\n# Test Task\nBody", encoding="utf-8")
    
    snapshot = TaskSnapshot(
        path=task_path,
        task_id="task1",
        project="proj1",
        stage="code",
        agent="coder",
        body="# Test Task\nBody"
    )
    
    detailed_state = build_detailed_board_state([snapshot])
    
    assert "proj1" in detailed_state
    assert "code" in detailed_state["proj1"]
    task_info = detailed_state["proj1"]["code"][0]
    assert task_info["task_id"] == "task1"
    assert task_info["title"] == "Test Task"
    assert "last_updated" in task_info


def test_board_summary_markdown():
    snapshot = TaskSnapshot(
        path=Path("task1.md"),
        task_id="task1",
        project="proj1",
        stage="code",
        agent="coder",
        body="# Test Task\nBody"
    )
    
    summary = render_board_summary([snapshot])
    assert "# Kanban Board Summary" in summary
    assert "## Project: proj1" in summary
    assert "### Stage: code" in summary
    assert "task1" in summary
    assert "Test Task" in summary


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_runs_all(mock_dispatcher_class):
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="p1")}
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = Path("/tmp")
    
    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(ok=True, final_message="hello world")
    mock_dispatcher._build_provider.return_value = mock_provider
    
    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()
    
    assert "p1" in results
    assert results["p1"] is True
    assert mock_provider.invoke.called
