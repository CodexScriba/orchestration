---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 3.3: Gemini and Qwen CLI providers

## Goal

Implement the Gemini and Qwen CLI providers.

## Definition of Done

- [ ] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [ ] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [ ] Each loads config from its respective `_providers/*.md` file
- [ ] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [ ] Gemini supports model name format (`gemini-3-flash-preview`)

## Files

- `src/orchestrator/providers/gemini.py` - create - Gemini CLI implementation
- `src/orchestrator/providers/qwen.py` - create - Qwen CLI implementation

## Tests

- [ ] GeminiProvider builds correct command with model name
- [ ] QwenProvider builds correct command with model alias
- [ ] Both detect missing binary gracefully

## Context

Phase 3: Account Rotation and Multi-Provider
