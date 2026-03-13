---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 3: Account Rotation and Multi-Provider

This task consolidates all Phase 3 tasks into a single comprehensive task for testing AI capabilities with long tasks.

---

## Task 3.1: Account manager with Codex rotation

### Goal

Implement the account manager that rotates Codex auth tokens per task.

### Definition of Done

- [ ] Account pool loaded from config (list of account names)
- [ ] Rotation: pick next account per task, keep same through bounces
- [ ] Switch mechanism: symlink `~/.codex/auth.json` to `~/.codex/accounts/TARGET.json`
- [ ] Health check: run `codex login status` after switch, parse result
- [ ] Round-robin fallback: if account fails, try next; if all fail, escalate
- [ ] Log which account is active for each task

### Files

- `src/orchestrator/accounts.py` - create - account rotation and health checking

### Tests

- [ ] Account rotation picks the next account in pool order
- [ ] Same account persists through bounces of a task
- [ ] Failed account triggers fallback to next
- [ ] All accounts failing triggers escalation
- [ ] Health check parses codex login status output

### Context

Phase 3: Account Rotation and Multi-Provider

---

## Task 3.2: Claude CLI provider

### Goal

Implement the Claude CLI provider for Anthropic models.

### Definition of Done

- [ ] `ClaudeProvider` implements `BaseProvider`
- [ ] Loads config from `.kanban2code/_providers/opus.md`, `sonnet.md`, `haiku.md`
- [ ] Builds correct `claude` CLI command with model, flags, and prompt
- [ ] Supports stdin prompt delivery
- [ ] Captures output for evaluation

### Files

- `src/orchestrator/providers/claude.py` - create - Claude CLI implementation

### Tests

- [ ] ClaudeProvider builds correct command for opus/sonnet/haiku
- [ ] ClaudeProvider handles stdin prompt delivery
- [ ] Missing claude binary detected gracefully

### Context

Phase 3: Account Rotation and Multi-Provider

---

## Task 3.3: Gemini and Qwen CLI providers

### Goal

Implement the Gemini and Qwen CLI providers.

### Definition of Done

- [ ] `GeminiProvider` implements `BaseProvider` for Google Gemini CLI
- [ ] `QwenProvider` implements `BaseProvider` for Qwen CLI
- [ ] Each loads config from its respective `_providers/*.md` file
- [ ] Qwen supports model aliases (kimi-k2.5, minimax, etc.)
- [ ] Gemini supports model name format (`gemini-3-flash-preview`)

### Files

- `src/orchestrator/providers/gemini.py` - create - Gemini CLI implementation
- `src/orchestrator/providers/qwen.py` - create - Qwen CLI implementation

### Tests

- [ ] GeminiProvider builds correct command with model name
- [ ] QwenProvider builds correct command with model alias
- [ ] Both detect missing binary gracefully

### Context

Phase 3: Account Rotation and Multi-Provider

---

## Task 3.4: Model routing with fallback chains

### Goal

Implement model routing and ordered fallback chains in the dispatcher.

### Definition of Done

- [ ] Config defines provider preference per stage with ordered fallback list
- [ ] Planning: Gemini Flash 3.x → Qwen Kimi 2.5 → Haiku
- [ ] Coding: Codex 5.4 medium → Sonnet 4.6 → GLM via Qwen
- [ ] Auditing: Opus → Codex 5.4 high reasoning
- [ ] On provider failure, automatically try next in fallback chain
- [ ] Log which provider/model was actually used

### Files

- `src/orchestrator/dispatcher.py` - modify - add fallback chain logic
- `config.json` - modify - add fallback chain configuration

### Tests

- [ ] Primary provider selected for each stage
- [ ] Fallback triggered on provider failure
- [ ] All fallbacks exhausted triggers escalation
- [ ] Correct provider/model logged for each invocation

### Context

Phase 3: Account Rotation and Multi-Provider