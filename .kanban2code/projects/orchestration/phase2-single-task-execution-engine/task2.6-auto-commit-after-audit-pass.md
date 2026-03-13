---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.6: Auto-commit after audit pass

## Goal

Implement surgical git commits after successful audit passes.

## Definition of Done

- [ ] On audit acceptance, commit immediately
- [ ] Only stage files listed in the task's Audit section + task file + architecture.md if changed
- [ ] Never use `git add .` or `git add -A`
- [ ] Commit message format: `feat(task-id): description\n\nAudited: rating/10 by MODEL\nFiles: N files changed\nBounces: N`
- [ ] Skip commit if no files to stage (log warning)
- [ ] Branch creation after phase/milestone completion (configurable)

## Files

- `src/orchestrator/commits.py` - create - git commit logic

## Tests

- [ ] Commit stages only the specified files
- [ ] Commit message follows the defined format
- [ ] No commit when file list is empty (warning logged)
- [ ] `git add .` and `git add -A` never appear in the code
- [ ] Branch created when configured for milestone

## Context

Phase 2: Single-Task Execution Engine
