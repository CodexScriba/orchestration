---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 3.4: Model routing with fallback chains

## Goal

Implement model routing and ordered fallback chains in the dispatcher.

## Definition of Done

- [ ] Config defines provider preference per stage with ordered fallback list
- [ ] Planning: Gemini Flash 3.x → Qwen Kimi 2.5 → Haiku
- [ ] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen
- [ ] Auditing: Opus → Codex 5.4 high reasoning
- [ ] On provider failure, automatically try next in fallback chain
- [ ] Log which provider/model was actually used

## Files

- `src/orchestrator/dispatcher.py` - modify - add fallback chain logic
- `config.json` - modify - add fallback chain configuration

## Tests

- [ ] Primary provider selected for each stage
- [ ] Fallback triggered on provider failure
- [ ] All fallbacks exhausted triggers escalation
- [ ] Correct provider/model logged for each invocation

## Context

Phase 3: Account Rotation and Multi-Provider
