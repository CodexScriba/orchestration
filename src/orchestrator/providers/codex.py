"""Codex CLI provider implementation."""

from __future__ import annotations

from pathlib import Path
import shutil

from orchestrator.models import InvocationResult, ProviderAliasConfig, ProviderConfig, StageTimeoutConfig
from orchestrator.scanner import split_frontmatter
from orchestrator.sessions import SessionError, TmuxSessionManager
from orchestrator.providers.base import BaseProvider, ProviderError


class CodexProvider(BaseProvider):
    """Invoke the Codex CLI using provider markdown frontmatter config."""

    def __init__(
        self,
        repo_root: Path,
        alias: str,
        alias_config: ProviderAliasConfig | None = None,
        *,
        session_manager: TmuxSessionManager | None = None,
        provider_dir: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.alias = alias
        self.alias_config = alias_config or ProviderAliasConfig(alias=alias)
        self.provider_dir = provider_dir or self.repo_root / ".kanban2code" / "_providers"
        self.session_manager = session_manager or TmuxSessionManager(repo_root=self.repo_root)
        self.provider_config = self.load_provider_config(self.provider_dir / f"{alias}.md", alias)

    @staticmethod
    def load_provider_config(path: Path, alias: str | None = None) -> ProviderConfig:
        """Load provider settings from markdown frontmatter."""

        if not path.exists():
            raise ProviderError(f"Provider config not found: {path}")

        metadata, _body = split_frontmatter(path.read_text(encoding="utf-8"))
        cli = str(metadata.get("cli", "")).strip()
        subcommand = str(metadata.get("subcommand", "")).strip()
        if not cli:
            raise ProviderError(f"Provider config missing cli in {path}")
        if not subcommand:
            raise ProviderError(f"Provider config missing subcommand in {path}")

        unattended_flags = _string_list(metadata.get("unattended_flags", []), "unattended_flags", path)
        output_flags = _string_list(metadata.get("output_flags", []), "output_flags", path)
        prompt_style = str(metadata.get("prompt_style", "stdin")).strip() or "stdin"
        config_overrides = _string_dict(metadata.get("config_overrides", {}), "config_overrides", path)

        return ProviderConfig(
            alias=alias or path.stem,
            cli=cli,
            subcommand=subcommand,
            model=_optional_str(metadata.get("model")),
            provider=_optional_str(metadata.get("provider")),
            prompt_style=prompt_style,
            unattended_flags=unattended_flags,
            output_flags=output_flags,
            config_overrides=config_overrides,
        )

    def validate_binary(self) -> str | None:
        """Return the resolved binary path if available."""

        return shutil.which(self.provider_config.cli)

    def build_command(self) -> list[str]:
        """Build the Codex CLI command for execution."""

        command = [
            self.provider_config.cli,
            self.provider_config.subcommand,
            *self.provider_config.unattended_flags,
            *self.provider_config.output_flags,
        ]

        model = self.alias_config.model or self.provider_config.model
        if model:
            command.extend(["--model", model])

        merged_overrides = dict(self.provider_config.config_overrides)
        merged_overrides.update(self.alias_config.config_overrides)
        for key in sorted(merged_overrides):
            command.extend(["--config", f"{key}={merged_overrides[key]}"])

        return command

    def invoke(
        self,
        prompt: str,
        task_path: Path,
        output_dir: Path,
        timeouts: StageTimeoutConfig,
    ) -> InvocationResult:
        """Run a Codex invocation and return its execution result."""

        if self.validate_binary() is None:
            command = self.build_command()
            return InvocationResult(
                ok=False,
                exit_code=None,
                error_message=(
                    f"Provider binary {self.provider_config.cli!r} is not available on PATH."
                ),
                command=command,
            )

        try:
            session_result = self.session_manager.run_command(
                session_name=output_dir.name,
                command=self.build_command(),
                prompt=prompt,
                task_path=task_path,
                output_dir=output_dir,
                timeouts=timeouts,
            )
        except SessionError as exc:
            return InvocationResult(
                ok=False,
                exit_code=None,
                error_message=str(exc),
                command=self.build_command(),
            )

        return InvocationResult(
            ok=session_result.ok,
            exit_code=session_result.exit_code,
            timeout_type=session_result.timeout_type,
            final_message=session_result.final_message,
            output_paths={
                "output": session_result.output_path,
                "prompt": session_result.prompt_path,
                "exit_code": session_result.exit_code_path,
            },
            error_message=session_result.error_message,
            command=session_result.command,
        )


def _string_list(value: object, field_name: str, path: Path) -> list[str]:
    if value in ("", None):
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProviderError(f"Invalid {field_name} in {path}: expected list[str]")
    return list(value)


def _string_dict(value: object, field_name: str, path: Path) -> dict[str, object]:
    if value in ("", None):
        return {}
    if not isinstance(value, dict):
        raise ProviderError(f"Invalid {field_name} in {path}: expected object")
    return {str(key): item for key, item in value.items()}


def _optional_str(value: object) -> str | None:
    if value in ("", None):
        return None
    return str(value)
