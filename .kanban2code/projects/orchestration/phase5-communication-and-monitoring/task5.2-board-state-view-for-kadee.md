---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 5.2: Board state view for Kadee

## Goal

Implement the JSON and markdown board state view generator.

## Definition of Done

- [ ] Produces a JSON state file mapping `{project: {stage: [{task_id, title, agent, bounces, last_updated}]}}`
- [ ] Updated after every stage transition
- [ ] Also produces a human-readable markdown summary
- [ ] Kadee can read this file to understand board status without scanning every task

## Files

- `src/orchestrator/state.py` - modify - add board state view generation and markdown summary

## Tests

- [ ] Board state JSON matches expected structure from sample tasks
- [ ] Board state updates after stage transition
- [ ] Markdown summary is readable and correctly formatted

## Context

Phase 5: Communication and Monitoring
