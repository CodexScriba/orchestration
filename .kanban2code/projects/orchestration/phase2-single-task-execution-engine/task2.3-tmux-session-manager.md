---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.3: tmux session manager

## Goal

Implement programmatic tmux session management for running agent CLIs.

## Definition of Done

- [ ] Creates named tmux sessions for each stage invocation (e.g., `orch-run123-task1.1-plan`)
- [ ] Runs provider CLI command inside the tmux session
- [ ] Monitors session: polls for process exit and task file mutation
- [ ] Enforces wall timeout and idle timeout (configurable per stage)
- [ ] Kills session cleanly on timeout (SIGTERM then SIGKILL)
- [ ] Returns session output path for debugging

## Files

- `src/orchestrator/sessions.py` - create - tmux session lifecycle management

## Tests

- [ ] Session creates with correct name format
- [ ] Session detects process exit
- [ ] Wall timeout triggers session kill
- [ ] Idle timeout triggers session kill
- [ ] Session cleanup removes finished sessions

## Context

Phase 2: Single-Task Execution Engine
