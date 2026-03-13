---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 5.3: Smoke test suite

## Goal

Implement a smoke test suite to verify provider health and connectivity.

## Definition of Done

- [ ] `smoke-test` CLI subcommand calls each configured provider once
- [ ] Sends a trivial prompt (e.g., "Say exactly: hello") and checks for a response
- [ ] Reports pass/fail per provider with error details
- [ ] Tests: Codex, Claude, Gemini, Qwen (as configured)
- [ ] Can be run independently before starting real task execution

## Files

- `src/orchestrator/smoke.py` - create - provider health verification

## Tests

- [ ] Smoke test runs all configured providers
- [ ] Pass/fail reported per provider
- [ ] Missing provider binary reported as failure, not crash
- [ ] Auth failure reported clearly

## Context

Phase 5: Communication and Monitoring
