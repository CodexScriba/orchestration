---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.1: Provider abstraction and Codex CLI provider

## Goal

Create a BaseProvider abstract class and implement a Codex CLI provider.

## Definition of Done

- [ ] `BaseProvider` abstract class defines: `invoke(prompt, task_path, output_dir, timeouts) → InvocationResult`
- [ ] `CodexProvider` implements `BaseProvider` using subprocess + tmux
- [ ] Provider loads CLI config from `.kanban2code/_providers/*.md` frontmatter
- [ ] InvocationResult captures: ok, exit_code, timeout_type, final_message, output_paths, error_message, command
- [ ] Provider validates that the CLI binary exists on PATH before invocation

## Files

- `src/orchestrator/providers/__init__.py` - create - provider package init
- `src/orchestrator/providers/base.py` - create - abstract provider interface
- `src/orchestrator/providers/codex.py` - create - Codex CLI implementation

## Tests

- [ ] CodexProvider builds correct command line from provider config
- [ ] CodexProvider detects missing binary gracefully
- [ ] InvocationResult correctly reports success/failure/timeout
- [ ] Provider loads config from a sample .md frontmatter file

## Context

Phase 2: Single-Task Execution Engine
