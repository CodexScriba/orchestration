"""Stage transition evaluation for before/after task snapshots."""

from __future__ import annotations

import re

from orchestrator.config import OrchestratorConfig
from orchestrator.models import InvocationResult, StageResult, TaskSnapshot


def evaluate_stage_result(
    *,
    config: OrchestratorConfig,
    stage: str,
    before: TaskSnapshot,
    after: TaskSnapshot,
    invocation: InvocationResult,
    provider_key: str,
    provider_alias: str,
    provider_model: str | None,
) -> StageResult:
    """Evaluate semantic stage outcome from task snapshots."""

    base_result = StageResult(
        kind="transport_failure",
        stage=stage,
        success=False,
        task_path=str(after.path),
        task_id=after.task_id,
        provider_key=provider_key,
        provider_alias=provider_alias,
        provider_model=provider_model,
        exit_code=invocation.exit_code,
        output_paths=dict(invocation.output_paths),
        error_message=invocation.error_message,
        timeout_type=invocation.timeout_type,
        final_message=invocation.final_message,
        before_stage=before.stage,
        after_stage=after.stage,
        after_agent=after.agent,
    )
    if not invocation.ok:
        return base_result

    if stage == "plan":
        return _evaluate_plan(config, before, after, base_result)
    if stage == "code":
        return _evaluate_code(config, before, after, base_result)
    if stage == "audit":
        return _evaluate_audit(config, before, after, base_result)
    return base_result


def _evaluate_plan(
    config: OrchestratorConfig,
    before: TaskSnapshot,
    after: TaskSnapshot,
    result: StageResult,
) -> StageResult:
    route = config.stage_routing["plan"]
    if _has_new_questions(before, after):
        result.kind = "blocked"
        result.error_message = result.error_message or "Planner added questions."
        return result
    if (
        after.stage == route.success_stage
        and after.agent == route.success_agent
        and _has_required_sections(after.body, route.required_sections)
    ):
        result.kind = "success"
        result.success = True
        return result
    return result


def _evaluate_code(
    config: OrchestratorConfig,
    before: TaskSnapshot,
    after: TaskSnapshot,
    result: StageResult,
) -> StageResult:
    route = config.stage_routing["code"]
    if (
        after.stage == route.success_stage
        and after.agent == route.success_agent
        and _has_required_sections(after.body, route.required_sections)
        and before.text != after.text
    ):
        result.kind = "success"
        result.success = True
        return result
    return result


def _evaluate_audit(
    config: OrchestratorConfig,
    _before: TaskSnapshot,
    after: TaskSnapshot,
    result: StageResult,
) -> StageResult:
    route = config.stage_routing["audit"]
    rating = extract_audit_rating(after.body)
    result.audit_rating = rating

    if (
        after.stage == route.accepted_stage
        and after.agent == route.accepted_agent
        and _has_required_sections(after.body, route.required_sections)
        and rating >= route.accepted_rating
    ):
        result.kind = "success"
        result.success = True
        return result

    if (
        after.stage == route.rework_stage
        and after.agent == route.rework_agent
        and _has_required_sections(after.body, route.required_sections)
        and rating < route.accepted_rating
    ):
        result.kind = "quality_failure"
        return result

    return result


def extract_audit_rating(body: str) -> int:
    """Extract an audit rating from markdown or structured markers."""

    patterns = [
        re.compile(r"AUDIT_RATING:\s*(?P<rating>\d+)", re.IGNORECASE),
        re.compile(r"rating\s*[:\-]\s*(?P<rating>\d+)(?:/10)?", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(body)
        if match:
            return int(match.group("rating"))
    return 0


def _has_required_sections(body: str, required_sections: list[str]) -> bool:
    return all(section in body for section in required_sections)


def _has_new_questions(before: TaskSnapshot, after: TaskSnapshot) -> bool:
    return "## Questions" not in before.body and "## Questions" in after.body
