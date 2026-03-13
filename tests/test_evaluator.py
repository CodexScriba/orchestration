from __future__ import annotations

from pathlib import Path

from orchestrator.config import load_config
from orchestrator.evaluator import evaluate_stage_result
from orchestrator.models import InvocationResult, TaskSnapshot


def _snapshot(*, stage: str, agent: str, body: str, text: str | None = None) -> TaskSnapshot:
    rendered = text if text is not None else f"---\nstage: {stage}\nagent: {agent}\n---\n{body}"
    return TaskSnapshot(
        path=Path("task.md"),
        task_id="task",
        project="orch",
        stage=stage,
        agent=agent,
        body=body,
        text=rendered,
    )


def test_plan_success_detected() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="plan",
        before=_snapshot(stage="plan", agent="planner", body="# Task"),
        after=_snapshot(
            stage="code",
            agent="coder",
            body="## Refined Prompt\nhello\n## Context\nworld",
        ),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="planner",
        provider_alias="codex-low",
        provider_model="gpt",
    )

    assert result.kind == "success"
    assert result.success is True


def test_plan_blocked_detected_when_questions_added() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="plan",
        before=_snapshot(stage="plan", agent="planner", body="# Task"),
        after=_snapshot(stage="plan", agent="planner", body="# Task\n## Questions\nNeed input"),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="planner",
        provider_alias="codex-low",
        provider_model="gpt",
    )

    assert result.kind == "blocked"


def test_code_success_detected() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="code",
        before=_snapshot(stage="code", agent="coder", body="# Task", text="one"),
        after=_snapshot(stage="audit", agent="auditor", body="## Audit\nsrc/file.py", text="two"),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="coder",
        provider_alias="codex",
        provider_model="gpt",
    )

    assert result.kind == "success"


def test_audit_acceptance_detected() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="audit",
        before=_snapshot(stage="audit", agent="auditor", body="## Review\nRating: 9"),
        after=_snapshot(stage="completed", agent="auditor", body="## Review\nRating: 9"),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="auditor",
        provider_alias="codex-high",
        provider_model="gpt",
    )

    assert result.kind == "success"
    assert result.audit_rating == 9


def test_audit_rework_detected() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="audit",
        before=_snapshot(stage="audit", agent="auditor", body="## Review\nRating: 6"),
        after=_snapshot(stage="code", agent="coder", body="## Review\nRating: 6"),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="auditor",
        provider_alias="codex-high",
        provider_model="gpt",
    )

    assert result.kind == "quality_failure"
    assert result.audit_rating == 6


def test_transport_failure_detected_when_transition_missing() -> None:
    result = evaluate_stage_result(
        config=load_config("config.json"),
        stage="code",
        before=_snapshot(stage="code", agent="coder", body="# Task", text="same"),
        after=_snapshot(stage="code", agent="coder", body="# Task", text="same"),
        invocation=InvocationResult(ok=True, exit_code=0),
        provider_key="coder",
        provider_alias="codex",
        provider_model="gpt",
    )

    assert result.kind == "transport_failure"
