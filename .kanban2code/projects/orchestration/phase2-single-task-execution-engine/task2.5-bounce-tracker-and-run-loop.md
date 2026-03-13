---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.5: Bounce tracker and run loop

## Goal

Implement the core run loop that processes tasks and tracks audit bounces.

## Definition of Done

- [ ] Run loop processes ordered queue: for each task, execute stages until completed or blocked
- [ ] Bounce tracker counts audit failures per task (stored in task state)
- [ ] Max 2 audit bounces: third cycle triggers handoff stop
- [ ] Transport retry: up to 3 attempts per stage before escalation
- [ ] Handoff writes human-readable readme with context for Dan
- [ ] Run state updated after every stage with current index, task, stage
- [ ] `continue` command resumes from persisted run state

## Files

- `src/orchestrator/dispatcher.py` - modify - add run loop and bounce tracking
- `src/orchestrator/state.py` - modify - add handoff readme generation

## Tests

- [ ] Run loop processes a single task through plan → code → audit → completed
- [ ] Bounce counter increments on audit failure
- [ ] Third audit cycle triggers handoff stop
- [ ] Transport retry exhaustion triggers handoff stop
- [ ] Continue resumes from the correct task and stage
- [ ] Handoff readme contains task context and failure reason

## Context

Phase 2: Single-Task Execution Engine
