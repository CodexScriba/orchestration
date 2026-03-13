---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 4.2: File-level conflict detection

## Goal

Implement conflict detection logic based on the files each task will touch.

## Definition of Done

- [ ] Before dispatching, check which files each task will touch (from task body/context)
- [ ] Two tasks with overlapping file sets must not run concurrently
- [ ] Conflict detected at dispatch time, not after launch
- [ ] Conflict resolution: delay the later task until the earlier one completes
- [ ] Log conflict decisions

## Files

- `src/orchestrator/scheduler.py` - modify - add file-level conflict detection

## Tests

- [ ] Tasks touching different files are allowed concurrently
- [ ] Tasks touching the same file are serialized
- [ ] Conflict detection reads file lists from task body
- [ ] Delayed task is dispatched after conflicting task completes

## Context

Phase 4: Concurrency and Safety
