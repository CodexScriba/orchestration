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
from orchestrator.smoke import REQUIRED_FAMILIES, SmokeTester, _resolve_family_for_alias
from orchestrator.state import CANONICAL_STAGES, build_detailed_board_state, render_board_summary


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


# =============================================================================
# Board State Tests
# =============================================================================


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


def test_board_state_uses_task_id_as_fallback_title(tmp_path):
    """When task has no H1, use task_id as title."""
    task_path = tmp_path / "task2.md"
    task_path.write_text("---\nstage: plan\nagent: planner\n---\nNo heading here", encoding="utf-8")

    snapshot = TaskSnapshot(
        path=task_path,
        task_id="task2",
        project="proj1",
        stage="plan",
        agent="planner",
        body="No heading here"
    )

    detailed_state = build_detailed_board_state([snapshot])

    task_info = detailed_state["proj1"]["plan"][0]
    assert task_info["title"] == "task2"


def test_board_state_includes_bounces(tmp_path):
    """Board state includes bounce count."""
    task_path = tmp_path / "task3.md"
    task_path.write_text("---\nstage: audit\nagent: auditor\n---\n# Task", encoding="utf-8")

    snapshot = TaskSnapshot(
        path=task_path,
        task_id="task3",
        project="proj1",
        stage="audit",
        agent="auditor",
        bounces=3,
        body="# Task"
    )

    detailed_state = build_detailed_board_state([snapshot])

    task_info = detailed_state["proj1"]["audit"][0]
    assert task_info["bounces"] == 3


def test_board_state_groups_by_project_and_stage(tmp_path):
    """Board state correctly groups tasks by project and stage."""
    # Create actual files since build_detailed_board_state reads file mtimes
    task1_path = tmp_path / "task1.md"
    task2_path = tmp_path / "task2.md"
    task3_path = tmp_path / "task3.md"

    task1_path.write_text("# Task 1", encoding="utf-8")
    task2_path.write_text("# Task 2", encoding="utf-8")
    task3_path.write_text("# Task 3", encoding="utf-8")

    snapshots = [
        TaskSnapshot(
            path=task1_path,
            task_id="task1",
            project="alpha",
            stage="plan",
            agent="planner",
            body="# Task 1"
        ),
        TaskSnapshot(
            path=task2_path,
            task_id="task2",
            project="alpha",
            stage="code",
            agent="coder",
            body="# Task 2"
        ),
        TaskSnapshot(
            path=task3_path,
            task_id="task3",
            project="beta",
            stage="plan",
            agent="planner",
            body="# Task 3"
        ),
    ]

    detailed_state = build_detailed_board_state(snapshots)

    assert "alpha" in detailed_state
    assert "beta" in detailed_state
    assert len(detailed_state["alpha"]["plan"]) == 1
    assert len(detailed_state["alpha"]["code"]) == 1
    assert len(detailed_state["beta"]["plan"]) == 1


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


def test_board_summary_empty_board():
    """Empty board produces a summary indicating no tasks."""
    summary = render_board_summary([])

    assert "# Kanban Board Summary" in summary
    assert "*No tasks found.*" in summary


# =============================================================================
# Smoke Test Tests
# =============================================================================


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


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_missing_provider_binary(mock_dispatcher_class):
    """Missing provider binary is reported as failure, not crash."""
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="missing-provider")}
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = Path("/tmp")

    mock_dispatcher._build_provider.side_effect = ValueError("Provider binary not found")

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    assert "missing-provider" in results
    assert results["missing-provider"] is False


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_auth_failure_reported(mock_dispatcher_class):
    """Auth failure is reported clearly."""
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="auth-fail-provider")}
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = Path("/tmp")

    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(
        ok=False,
        error_message="Authentication failed: Invalid API key"
    )
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    assert "auth-fail-provider" in results
    assert results["auth-fail-provider"] is False


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_invocation_crash(mock_dispatcher_class):
    """Provider invocation crash is reported as failure."""
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="crash-provider")}
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = Path("/tmp")

    mock_provider = MagicMock()
    mock_provider.invoke.side_effect = RuntimeError("Unexpected crash")
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    assert "crash-provider" in results
    assert results["crash-provider"] is False


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_unexpected_response(mock_dispatcher_class):
    """Unexpected response (no 'hello') is reported as failure."""
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="wrong-response")}
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = Path("/tmp")

    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(
        ok=True,
        final_message="Goodbye world"
    )
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    assert "wrong-response" in results
    assert results["wrong-response"] is False


@patch("orchestrator.dispatcher.Dispatcher")
def test_smoke_tester_includes_fallback_chain_providers(mock_dispatcher_class):
    """Smoke test includes providers from fallback chains."""
    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.config.providers = {"planner": MagicMock(alias="primary")}
    mock_dispatcher.config.fallback_chains = {
        "planner": [
            MagicMock(alias="fallback1"),
            MagicMock(alias="fallback2"),
        ]
    }
    mock_dispatcher.repo_root = Path("/tmp")

    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(ok=True, final_message="hello")
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    # Should test all unique aliases
    assert "primary" in results
    assert "fallback1" in results
    assert "fallback2" in results


# =============================================================================
# New tests for review findings
# =============================================================================


@patch("orchestrator.notifier.Bot")
@patch("os.environ.get")
def test_notifier_includes_account_when_present(mock_env_get, mock_bot_class, mock_config):
    """Stage-change notification includes the active account."""
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
        provider_alias="codex-primary",
        provider_model="gpt-4.1",
        account="codex-account-2",
        kind="success",
    )

    notifier.notify_stage_change(result)

    args, kwargs = mock_bot.send_message.call_args
    message_text = kwargs["text"]
    assert "codex-account-2" in message_text


def test_board_state_includes_all_canonical_stages(tmp_path):
    """Board state JSON always includes inbox/plan/code/audit/completed keys."""
    task_path = tmp_path / "task1.md"
    task_path.write_text("# Task 1", encoding="utf-8")

    snapshots = [
        TaskSnapshot(
            path=task_path,
            task_id="task1",
            project="proj1",
            stage="code",
            agent="coder",
            body="# Task 1",
        ),
    ]

    detailed_state = build_detailed_board_state(snapshots)

    # Project should have all canonical stages, even those with no tasks
    for stage in CANONICAL_STAGES:
        assert stage in detailed_state["proj1"], f"Missing stage bucket: {stage}"

    # Only "code" should have a task
    assert len(detailed_state["proj1"]["code"]) == 1
    assert len(detailed_state["proj1"]["inbox"]) == 0
    assert len(detailed_state["proj1"]["plan"]) == 0
    assert len(detailed_state["proj1"]["audit"]) == 0
    assert len(detailed_state["proj1"]["completed"]) == 0


def test_smoke_tester_resolves_families_from_metadata(tmp_path):
    """Smoke test resolves families via provider metadata, not alias substrings."""
    # Set up provider metadata files
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "sonnet.md").write_text("---\ncli: claude\nmodel: claude-sonnet-4-5\n---\n")
    (provider_dir / "codex.md").write_text("---\ncli: codex\nmodel: gpt-5\n---\n")
    (provider_dir / "gemini.md").write_text("---\ncli: gemini\nmodel: gemini-2.5\n---\n")
    (provider_dir / "kimi.md").write_text("---\ncli: kimi\nmodel: kimi-k2\n---\n")

    mock_dispatcher = MagicMock()
    # Config only has codex and sonnet — gemini and qwen must be discovered
    mock_dispatcher.config.providers = {
        "planner": MagicMock(alias="codex", model="gpt-5", config_overrides={}),
        "coder": MagicMock(alias="sonnet", model="claude-sonnet-4-5", config_overrides={}),
    }
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = tmp_path

    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(ok=True, final_message="hello")
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    results = tester.run_all()

    # All four families should be covered via metadata resolution
    covered_families: set[str] = set()
    for alias in results:
        family = _resolve_family_for_alias(alias, provider_dir)
        if family:
            covered_families.add(family)

    assert covered_families == set(REQUIRED_FAMILIES)

    # The configured model settings must be preserved for aliases from config
    build_calls = {
        call.args[0]: call.args[1] for call in mock_dispatcher._build_provider.call_args_list
    }
    assert "sonnet" in build_calls
    assert build_calls["sonnet"].model == "claude-sonnet-4-5"


def test_smoke_tester_preserves_configured_model_overrides(tmp_path):
    """Smoke test uses configured ProviderAliasConfig (model + overrides)."""
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "codex.md").write_text("---\ncli: codex\n---\n")

    mock_dispatcher = MagicMock()
    mock_dispatcher.config.providers = {
        "planner": MagicMock(alias="codex", model="gpt-5.3-codex", config_overrides={"temp": 0}),
    }
    mock_dispatcher.config.fallback_chains = {}
    mock_dispatcher.repo_root = tmp_path

    mock_provider = MagicMock()
    mock_provider.invoke.return_value = InvocationResult(ok=True, final_message="hello")
    mock_dispatcher._build_provider.return_value = mock_provider

    tester = SmokeTester(mock_dispatcher)
    tester.run_provider_test("codex", mock_dispatcher.config.providers["planner"])

    # Verify model passed through
    build_call = mock_dispatcher._build_provider.call_args
    assert build_call.args[1].model == "gpt-5.3-codex"


def test_concurrent_scheduler_notifies_on_stalled_dependencies(tmp_path):
    """Dependency-stalled tasks trigger escalation notification."""
    from orchestrator.scheduler import ConcurrentScheduler
    from orchestrator.models import RunEvent, RunState, TaskFileInfo

    mock_dispatcher = MagicMock()
    mock_dispatcher.config.scheduler.enabled = True
    mock_dispatcher.config.scheduler.max_concurrent = 2
    mock_dispatcher.config.logging.retain_recent_events = 20

    mock_logger = MagicMock()
    mock_logger.append.return_value = RunEvent(
        timestamp="2026-01-01T00:00:00Z", type="task_blocked", message="blocked"
    )

    state_path = tmp_path / "state.json"
    scheduler = ConcurrentScheduler(
        repo_root=tmp_path,
        config=mock_dispatcher.config,
        dispatcher=mock_dispatcher,
        logger=mock_logger,
        run_state_path=state_path,
    )

    run_state = RunState(status="running")

    task_path = Path("/tmp/task_blocked.md")
    pending_tasks = [task_path]
    completed_task_ids: set[str] = set()

    with (
        patch("orchestrator.scheduler.parse_task_file") as mock_parse,
        patch("orchestrator.scheduler.get_task_file_info") as mock_info,
    ):
        mock_parse.return_value = TaskSnapshot(
            path=task_path, task_id="task_blocked", stage="code", agent="coder"
        )
        mock_info.return_value = TaskFileInfo(
            task_path=task_path,
            task_id="task_blocked",
            depends_on=["nonexistent_task"],
        )

        scheduler._resolve_stalled_tasks(run_state, pending_tasks, completed_task_ids)

    # Notification should have been sent for the blocked task
    mock_dispatcher.notifier.notify_escalation.assert_called_once()
    call_args = mock_dispatcher.notifier.notify_escalation.call_args
    assert call_args.args[0] == "task_blocked"
    assert call_args.args[1] == "blocked"
    assert "nonexistent_task" in call_args.args[2]


def test_concurrent_scheduler_fires_post_stage_hook():
    """ConcurrentScheduler calls dispatcher.post_stage_hook after dispatch_stage."""
    from orchestrator.scheduler import ConcurrentScheduler

    mock_dispatcher = MagicMock()
    mock_dispatcher.config.scheduler.enabled = True
    mock_dispatcher.config.scheduler.max_concurrent = 2
    mock_dispatcher.config.retry_policy.audit_failure_cycles_before_handoff = 2
    mock_dispatcher.config.retry_policy.transport_max_attempts = 3
    mock_dispatcher.config.logging.retain_recent_events = 20

    # Simulate a single successful dispatch that leads to "completed"
    first_result = StageResult(
        kind="success",
        stage="code",
        after_stage="completed",
        task_id="task1",
        provider_alias="codex",
    )
    mock_dispatcher.dispatch_stage.return_value = first_result

    scheduler = ConcurrentScheduler(
        repo_root=Path("/tmp"),
        config=mock_dispatcher.config,
        dispatcher=mock_dispatcher,
        run_state_path=Path("/tmp/state.json"),
    )

    # Directly test the _run_task_stages worker (not the full concurrent loop)
    task_path = Path("/tmp/task1.md")

    # parse_task_file needs to return a snapshot with stage="completed" after dispatch
    with (
        patch("orchestrator.scheduler.parse_task_file") as mock_parse,
        patch("orchestrator.commits.commit_after_audit"),
    ):
        # First call: task at "code" stage; second call: "completed"
        mock_parse.side_effect = [
            TaskSnapshot(path=task_path, task_id="task1", stage="code", agent="coder"),
            TaskSnapshot(path=task_path, task_id="task1", stage="completed", agent="coder"),
        ]
        result = scheduler._run_task_stages(task_path=task_path, run_id="run-test")

    # post_stage_hook must have been called
    mock_dispatcher.post_stage_hook.assert_called_once_with(first_result)
