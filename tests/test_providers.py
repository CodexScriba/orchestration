from __future__ import annotations

from pathlib import Path

from orchestrator.models import ProviderAliasConfig, SessionResult, StageTimeoutConfig
from orchestrator.providers.codex import CodexProvider


def test_load_provider_config_from_frontmatter(tmp_path: Path) -> None:
    provider_path = tmp_path / "codex.md"
    provider_path.write_text(
        (
            "---\n"
            "cli: codex\n"
            "subcommand: exec\n"
            "model: gpt-5.3-codex\n"
            "unattended_flags: ['--yolo']\n"
            "output_flags: ['--json']\n"
            "prompt_style: stdin\n"
            "config_overrides:\n"
            "  model_reasoning_effort: medium\n"
            "---\n"
        ),
        encoding="utf-8",
    )

    config = CodexProvider.load_provider_config(provider_path, "codex")

    assert config.cli == "codex"
    assert config.subcommand == "exec"
    assert config.unattended_flags == ["--yolo"]
    assert config.config_overrides == {"model_reasoning_effort": "medium"}


def test_codex_provider_builds_command_with_alias_overrides(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "codex.md").write_text(
        (
            "---\n"
            "cli: codex\n"
            "subcommand: exec\n"
            "model: gpt-5.3-codex\n"
            "unattended_flags: ['--yolo']\n"
            "output_flags: ['--json']\n"
            "prompt_style: stdin\n"
            "config_overrides:\n"
            "  model_reasoning_effort: medium\n"
            "---\n"
        ),
        encoding="utf-8",
    )
    provider = CodexProvider(
        repo_root=tmp_path,
        alias="codex",
        alias_config=ProviderAliasConfig(
            alias="codex",
            model="gpt-override",
            config_overrides={"temperature": 0},
        ),
        provider_dir=provider_dir,
    )

    command = provider.build_command()

    assert command[:4] == ["codex", "exec", "--yolo", "--json"]
    assert "--model" in command
    assert "gpt-override" in command
    assert "model_reasoning_effort=medium" in command
    assert "temperature=0" in command


def test_codex_provider_detects_missing_binary_gracefully(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "codex.md").write_text(
        "---\ncli: missing-codex\nsubcommand: exec\n---\n",
        encoding="utf-8",
    )
    provider = CodexProvider(repo_root=tmp_path, alias="codex", provider_dir=provider_dir)

    result = provider.invoke(
        prompt="hello",
        task_path=tmp_path / "task.md",
        output_dir=tmp_path / "run",
        timeouts=StageTimeoutConfig(),
    )

    assert result.ok is False
    assert "not available on PATH" in (result.error_message or "")
    assert result.command[:2] == ["missing-codex", "exec"]


def test_codex_provider_maps_session_result_into_invocation_result(tmp_path: Path) -> None:
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    provider_dir.mkdir(parents=True)
    (provider_dir / "codex.md").write_text(
        "---\ncli: python3\nsubcommand: -c\noutput_flags: []\nunattended_flags: []\n---\n",
        encoding="utf-8",
    )

    class FakeSessionManager:
        def run_command(self, **_kwargs):
            return SessionResult(
                ok=True,
                session_name="session",
                exit_code=0,
                output_path="output.log",
                prompt_path="prompt.md",
                exit_code_path="exit.txt",
                final_message="done",
                command=["python3", "-c"],
            )

        def create_session_name(self, run_id: str, task_id: str, stage: str) -> str:
            return f"{run_id}-{task_id}-{stage}"

    provider = CodexProvider(
        repo_root=tmp_path,
        alias="codex",
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
    assert result.output_paths["output"] == "output.log"
