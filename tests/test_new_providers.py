"""Tests for ClaudeProvider, GeminiProvider, and QwenProvider."""

from __future__ import annotations

from pathlib import Path

from orchestrator.models import ProviderAliasConfig, SessionResult, StageTimeoutConfig
from orchestrator.providers.claude import ClaudeProvider
from orchestrator.providers.gemini import GeminiProvider
from orchestrator.providers.qwen import QwenProvider


# ---------------------------------------------------------------------------
# Claude Provider Tests
# ---------------------------------------------------------------------------


def _write_claude_config(provider_dir: Path, alias: str = "opus") -> None:
    provider_dir.mkdir(parents=True, exist_ok=True)
    (provider_dir / f"{alias}.md").write_text(
        (
            "---\n"
            "cli: claude\n"
            "model: claude-opus-4-6\n"
            "unattended_flags: ['--dangerously-skip-permissions']\n"
            "output_flags: ['--output-format', 'json']\n"
            "prompt_style: flag\n"
            "provider: anthropic\n"
            "---\n"
        ),
        encoding="utf-8",
    )


def test_claude_provider_builds_correct_command_for_opus(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_claude_config(provider_dir, "opus")
    provider = ClaudeProvider(repo_root=tmp_path, alias="opus", provider_dir=provider_dir)

    command = provider.build_command()

    assert command[0] == "claude"
    assert "--dangerously-skip-permissions" in command
    assert "--output-format" in command
    assert "json" in command
    assert "--model" in command
    assert "claude-opus-4-6" in command


def test_claude_provider_builds_correct_command_for_haiku(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "haiku.md").write_text(
        (
            "---\n"
            "cli: claude\n"
            "model: claude-haiku-4-5\n"
            "unattended_flags: ['--dangerously-skip-permissions']\n"
            "output_flags: ['--output-format', 'json']\n"
            "prompt_style: flag\n"
            "provider: anthropic\n"
            "---\n"
        ),
        encoding="utf-8",
    )
    provider = ClaudeProvider(repo_root=tmp_path, alias="haiku", provider_dir=provider_dir)

    command = provider.build_command()

    assert command[0] == "claude"
    assert "claude-haiku-4-5" in command


def test_claude_provider_flag_style_embeds_prompt_in_command(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_claude_config(provider_dir, "opus")
    provider = ClaudeProvider(repo_root=tmp_path, alias="opus", provider_dir=provider_dir)

    command = provider.build_command(prompt="do the thing")

    assert "--prompt" in command
    idx = command.index("--prompt")
    assert command[idx + 1] == "do the thing"


def test_claude_provider_detects_missing_binary_gracefully(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "missing-claude.md").write_text(
        "---\ncli: missing-claude-binary\nmodel: x\nprompt_style: flag\nprovider: anthropic\n---\n",
        encoding="utf-8",
    )
    provider = ClaudeProvider(repo_root=tmp_path, alias="missing-claude", provider_dir=provider_dir)

    result = provider.invoke(
        prompt="hello",
        task_path=tmp_path / "task.md",
        output_dir=tmp_path / "run",
        timeouts=StageTimeoutConfig(),
    )

    assert result.ok is False
    assert "not available on PATH" in (result.error_message or "")


def test_claude_provider_maps_session_result_to_invocation_result(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_claude_config(provider_dir, "opus")

    class FakeSessionManager:
        def run_command(self, **_kwargs) -> SessionResult:
            return SessionResult(
                ok=True,
                session_name="s",
                exit_code=0,
                output_path="out.log",
                prompt_path="prompt.md",
                exit_code_path="exit.txt",
                final_message="done",
                command=["claude", "--prompt", "x"],
            )

        def create_session_name(self, run_id: str, task_id: str, stage: str) -> str:
            return f"{run_id}-{task_id}-{stage}"

    provider = ClaudeProvider(
        repo_root=tmp_path,
        alias="opus",
        provider_dir=provider_dir,
        session_manager=FakeSessionManager(),
    )

    result = provider.invoke(
        prompt="hello",
        task_path=tmp_path / "task.md",
        output_dir=tmp_path / "run",
        timeouts=StageTimeoutConfig(),
    )

    assert result.ok is True
    assert result.exit_code == 0
    assert result.final_message == "done"
    assert result.output_paths["output"] == "out.log"


# ---------------------------------------------------------------------------
# Gemini Provider Tests
# ---------------------------------------------------------------------------


def _write_gemini_config(provider_dir: Path, alias: str = "gemini") -> None:
    provider_dir.mkdir(parents=True, exist_ok=True)
    (provider_dir / f"{alias}.md").write_text(
        (
            "---\n"
            "cli: gemini\n"
            "model: gemini-3-flash-preview\n"
            "unattended_flags: ['--yolo']\n"
            "output_flags: []\n"
            "prompt_style: stdin\n"
            "provider: google\n"
            "---\n"
        ),
        encoding="utf-8",
    )


def test_gemini_provider_builds_correct_command_with_model_name(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_gemini_config(provider_dir)
    provider = GeminiProvider(repo_root=tmp_path, alias="gemini", provider_dir=provider_dir)

    command = provider.build_command()

    assert command[0] == "gemini"
    assert "--model" in command
    assert "gemini-3-flash-preview" in command


def test_gemini_provider_alias_config_model_overrides_default(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_gemini_config(provider_dir)
    provider = GeminiProvider(
        repo_root=tmp_path,
        alias="gemini",
        alias_config=ProviderAliasConfig(alias="gemini", model="gemini-2.5-pro"),
        provider_dir=provider_dir,
    )

    command = provider.build_command()

    assert "gemini-2.5-pro" in command


def test_gemini_provider_detects_missing_binary_gracefully(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "gemini-missing.md").write_text(
        "---\ncli: missing-gemini-binary\nmodel: x\nprompt_style: stdin\nprovider: google\n---\n",
        encoding="utf-8",
    )
    provider = GeminiProvider(repo_root=tmp_path, alias="gemini-missing", provider_dir=provider_dir)

    result = provider.invoke(
        prompt="hello",
        task_path=tmp_path / "task.md",
        output_dir=tmp_path / "run",
        timeouts=StageTimeoutConfig(),
    )

    assert result.ok is False
    assert "not available on PATH" in (result.error_message or "")


# ---------------------------------------------------------------------------
# Qwen Provider Tests
# ---------------------------------------------------------------------------


def _write_qwen_config(provider_dir: Path, alias: str = "kimi", model: str = "kimi-k2-thinking-turbo") -> None:
    provider_dir.mkdir(parents=True, exist_ok=True)
    (provider_dir / f"{alias}.md").write_text(
        (
            f"---\n"
            f"cli: kimi\n"
            f"model: {model}\n"
            f"unattended_flags: ['--print']\n"
            f"output_flags: ['--quiet']\n"
            f"prompt_style: flag\n"
            f"provider: moonshot\n"
            f"---\n"
        ),
        encoding="utf-8",
    )


def test_qwen_provider_builds_correct_command_with_model_alias(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_qwen_config(provider_dir, alias="kimi", model="kimi-k2.5")
    provider = QwenProvider(repo_root=tmp_path, alias="kimi", provider_dir=provider_dir)

    command = provider.build_command()

    assert command[0] == "kimi"
    assert "--model" in command
    assert "kimi-k2.5" in command


def test_qwen_provider_alias_config_overrides_model(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_qwen_config(provider_dir)
    provider = QwenProvider(
        repo_root=tmp_path,
        alias="kimi",
        alias_config=ProviderAliasConfig(alias="kimi", model="minimax"),
        provider_dir=provider_dir,
    )

    command = provider.build_command()

    assert "minimax" in command


def test_qwen_provider_flag_style_embeds_prompt(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_qwen_config(provider_dir)
    provider = QwenProvider(repo_root=tmp_path, alias="kimi", provider_dir=provider_dir)

    command = provider.build_command(prompt="my task")

    assert "--prompt" in command
    idx = command.index("--prompt")
    assert command[idx + 1] == "my task"


def test_qwen_provider_detects_missing_binary_gracefully(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "qwen-missing.md").write_text(
        "---\ncli: missing-qwen-binary\nmodel: x\nprompt_style: flag\nprovider: moonshot\n---\n",
        encoding="utf-8",
    )
    provider = QwenProvider(repo_root=tmp_path, alias="qwen-missing", provider_dir=provider_dir)

    result = provider.invoke(
        prompt="hello",
        task_path=tmp_path / "task.md",
        output_dir=tmp_path / "run",
        timeouts=StageTimeoutConfig(),
    )

    assert result.ok is False
    assert "not available on PATH" in (result.error_message or "")
