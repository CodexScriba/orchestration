---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 3.2: Claude CLI provider

## Goal

Implement the Claude CLI provider for Anthropic models.

## Definition of Done

- [ ] `ClaudeProvider` implements `BaseProvider`
- [ ] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [ ] Builds correct `claude` CLI command with model, flags, and prompt
- [ ] Supports stdin prompt delivery
- [ ] Captures output for evaluation

## Files

- `src/orchestrator/providers/claude.py` - create - Claude CLI implementation

## Tests

- [ ] ClaudeProvider builds correct command for opus/sonnet/haiku
- [ ] ClaudeProvider handles stdin prompt delivery
- [ ] Missing claude binary detected gracefully

## Context

Phase 3: Account Rotation and Multi-Provider
