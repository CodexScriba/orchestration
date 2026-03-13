---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 3.1: Account manager with Codex rotation

## Goal

Implement the account manager that rotates Codex auth tokens per task.

## Definition of Done

- [ ] Account pool loaded from config (list of account names)
- [ ] Rotation: pick next account per task, keep same through bounces
- [ ] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [ ] Health check: run `codex login status` after switch, parse result
- [ ] Round-robin fallback: if account fails, try next; if all fail, escalate
- [ ] Log which account is active for each task

## Files

- `src/orchestrator/accounts.py` - create - account rotation and health checking

## Tests

- [ ] Account rotation picks the next account in pool order
- [ ] Same account persists through bounces of a task
- [ ] Failed account triggers fallback to next
- [ ] All accounts failing triggers escalation
- [ ] Health check parses codex login status output

## Context

Phase 3: Account Rotation and Multi-Provider
