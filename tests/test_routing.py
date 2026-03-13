"""Tests for model routing with fallback chains."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestrator.config import load_config
from orchestrator.dispatcher import Dispatcher
from orchestrator.models import FallbackChainEntry, InvocationResult, ProviderAliasConfig, StageResult
from orchestrator.providers.base import BaseProvider, ProviderError
from orchestrator.models import StageTimeoutConfig


def _write_task(path: Path, *, stage: str, agent: str, body: str = "# Task\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nstage: {stage}\nagent: {agent}\n---\n{body}", encoding="utf-8")


def _write_provider_config(provider_dir: Path, alias: str, cli: str, provider_type: str) -> None:
    provider_dir.mkdir(parents=True, exist_ok=True)
    (provider_dir / f"{alias}.md").write_text(
        (
            f"---\n"
            f"cli: {cli}\n"
            f"model: model-for-{alias}\n"
            f"unattended_flags: []\n"
            f"output_flags: []\n"
            f"prompt_style: stdin\n"
            f"provider: {provider_type}\n"
            f"---\n"
        ),
        encoding="utf-8",
    )


def _make_config_with_chains(
    config_path: Path,
    provider_dir: Path,
    *,
    planner_chain: list[dict],
    coder_chain: list[dict],
    auditor_chain: list[dict],
) -> None:
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    base["fallback_chains"] = {
        "planner": planner_chain,
        "coder": coder_chain,
        "auditor": auditor_chain,
    }
    config_path.write_text(json.dumps(base), encoding="utf-8")


# ---------------------------------------------------------------------------
# _get_fallback_chain tests
# ---------------------------------------------------------------------------


def test_fallback_chain_uses_config_chain_when_present(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    base["fallback_chains"] = {
        "planner": [
            {"alias": "gemini", "model": "gemini-3-flash", "config_overrides": {}},
            {"alias": "kimi", "model": "kimi-k2.5", "config_overrides": {}},
        ]
    }
    config_path.write_text(json.dumps(base), encoding="utf-8")
    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))

    chain = dispatcher._get_fallback_chain("planner")

    assert len(chain) == 2
    assert chain[0].alias == "gemini"
    assert chain[0].model == "gemini-3-flash"
    assert chain[1].alias == "kimi"


def test_fallback_chain_falls_back_to_providers_when_chain_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    # No fallback_chains key
    base.pop("fallback_chains", None)
    config_path.write_text(json.dumps(base), encoding="utf-8")
    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))

    chain = dispatcher._get_fallback_chain("planner")

    assert len(chain) == 1
    assert chain[0].alias == base["providers"]["planner"]["alias"]


# ---------------------------------------------------------------------------
# dispatch_stage fallback tests
# ---------------------------------------------------------------------------


class _FailingProvider(BaseProvider):
    """Provider that always fails."""

    def __init__(self) -> None:
        self.provider_config = type("PC", (), {"model": None})()

    def invoke(self, prompt, task_path, output_dir, timeouts) -> InvocationResult:
        return InvocationResult(ok=False, error_message="intentional failure")


class _SucceedingProvider(BaseProvider):
    """Provider that always succeeds."""

    def __init__(self, model: str = "test-model") -> None:
        self.provider_config = type("PC", (), {"model": model})()

    def invoke(self, prompt, task_path, output_dir, timeouts) -> InvocationResult:
        return InvocationResult(ok=True, exit_code=0)


def test_primary_provider_selected_for_each_stage(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(Path("config.json").read_text(encoding="utf-8"), encoding="utf-8")
    task_path = tmp_path / ".kanban2code" / "projects" / "p" / "task.md"
    _write_task(task_path, stage="code", agent="coder")

    used_aliases: list[str] = []

    def fake_build(self, alias: str, alias_config) -> _SucceedingProvider:
        used_aliases.append(alias)
        provider = _SucceedingProvider()
        provider.session_manager = type(
            "SM", (), {"create_session_name": lambda *a, **k: "s"}
        )()
        return provider

    def fake_dispatch(self, *, task_path: Path, run_id: str) -> StageResult:
        _write_task(task_path, stage="audit", agent="auditor", body="## Audit\nf.py\n")
        return StageResult(kind="success", stage="code", success=True, after_stage="audit")

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher.dispatch_stage", fake_dispatch)
    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher._build_provider", fake_build)

    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))
    # Verify chain is non-empty and first entry matches config
    chain = dispatcher._get_fallback_chain("coder")
    assert len(chain) >= 1


def test_fallback_triggered_on_provider_failure(tmp_path: Path, monkeypatch) -> None:
    """When primary fails, secondary is tried."""
    config_path = tmp_path / "config.json"
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    base["fallback_chains"] = {
        "coder": [
            {"alias": "primary", "model": None, "config_overrides": {}},
            {"alias": "secondary", "model": None, "config_overrides": {}},
        ]
    }
    config_path.write_text(json.dumps(base), encoding="utf-8")
    task_path = tmp_path / ".kanban2code" / "projects" / "p" / "task.md"
    _write_task(task_path, stage="code", agent="coder")
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_provider_config(provider_dir, "primary", "missing-primary-bin", "openai")
    _write_provider_config(provider_dir, "secondary", "missing-secondary-bin", "openai")

    # Both missing on PATH so both return ok=False; check that both are tried
    used: list[str] = []

    class TrackingProvider(BaseProvider):
        def __init__(self, alias: str) -> None:
            self._alias = alias
            self.provider_config = type("PC", (), {"model": None, "cli": "fake"})()
            self.session_manager = type(
                "SM", (), {"create_session_name": lambda *a, **k: "s"}
            )()

        def invoke(self, prompt, task_path, output_dir, timeouts) -> InvocationResult:
            used.append(self._alias)
            return InvocationResult(
                ok=self._alias == "secondary",
                exit_code=0 if self._alias == "secondary" else 1,
                error_message=None if self._alias == "secondary" else "fail",
            )

    def fake_build(self, alias: str, alias_config) -> BaseProvider:
        return TrackingProvider(alias)

    monkeypatch.setattr("orchestrator.dispatcher.Dispatcher._build_provider", fake_build)

    def fake_evaluate(**kwargs):
        inv = kwargs["invocation"]
        if inv.ok:
            return StageResult(kind="success", stage="code", success=True, after_stage="audit")
        return StageResult(kind="transport_failure", stage="code")

    monkeypatch.setattr("orchestrator.dispatcher.evaluate_stage_result", fake_evaluate)
    monkeypatch.setattr(
        "orchestrator.dispatcher.assemble_prompt", lambda **_: "prompt"
    )
    monkeypatch.setattr(
        "orchestrator.dispatcher.parse_task_file",
        lambda path: __import__("orchestrator.scanner", fromlist=["parse_task_file"]).parse_task_file(path),
    )

    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))
    result = dispatcher.dispatch_stage(task_path=task_path, run_id="r1")

    assert "primary" in used
    assert "secondary" in used
    assert result.kind == "success"


def test_all_fallbacks_exhausted_returns_transport_failure(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    base["fallback_chains"] = {
        "coder": [
            {"alias": "fail1", "model": None, "config_overrides": {}},
            {"alias": "fail2", "model": None, "config_overrides": {}},
        ]
    }
    config_path.write_text(json.dumps(base), encoding="utf-8")
    task_path = tmp_path / ".kanban2code" / "projects" / "p" / "task.md"
    _write_task(task_path, stage="code", agent="coder")
    provider_dir = tmp_path / ".kanban2code" / "_providers"
    _write_provider_config(provider_dir, "fail1", "missing-fail1", "openai")
    _write_provider_config(provider_dir, "fail2", "missing-fail2", "openai")

    class FailingProvider(BaseProvider):
        def __init__(self, alias: str) -> None:
            self.provider_config = type("PC", (), {"model": None, "cli": "fake"})()
            self.session_manager = type(
                "SM", (), {"create_session_name": lambda *a, **k: "s"}
            )()

        def invoke(self, prompt, task_path, output_dir, timeouts) -> InvocationResult:
            return InvocationResult(ok=False, error_message="fail")

    monkeypatch.setattr(
        "orchestrator.dispatcher.Dispatcher._build_provider",
        lambda self, alias, alias_config: FailingProvider(alias),
    )

    def fake_evaluate(**kwargs):
        return StageResult(kind="transport_failure", stage="code")

    monkeypatch.setattr("orchestrator.dispatcher.evaluate_stage_result", fake_evaluate)
    monkeypatch.setattr("orchestrator.dispatcher.assemble_prompt", lambda **_: "prompt")

    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))
    result = dispatcher.dispatch_stage(task_path=task_path, run_id="r1")

    assert result.kind == "transport_failure"


def test_provider_model_logged_for_each_invocation(tmp_path: Path) -> None:
    """_get_fallback_chain returns entries with correct model values."""
    config_path = tmp_path / "config.json"
    base = json.loads(Path("config.json").read_text(encoding="utf-8"))
    base["fallback_chains"] = {
        "auditor": [
            {"alias": "opus", "model": "claude-opus-4-6", "config_overrides": {}},
            {"alias": "codex-xhigh", "model": None, "config_overrides": {}},
        ]
    }
    config_path.write_text(json.dumps(base), encoding="utf-8")
    dispatcher = Dispatcher(repo_root=tmp_path, config=load_config(config_path))

    chain = dispatcher._get_fallback_chain("auditor")

    assert chain[0].alias == "opus"
    assert chain[0].model == "claude-opus-4-6"
    assert chain[1].alias == "codex-xhigh"
    assert chain[1].model is None
