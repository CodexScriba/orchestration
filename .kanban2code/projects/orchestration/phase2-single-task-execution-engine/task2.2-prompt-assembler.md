---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 2.2: Prompt assembler

## Goal

Build a system that assembles full prompts by injecting actual file contents.

## Definition of Done

- [ ] Assembles full prompt from: role file, ai-guide.md, task file, context files
- [ ] Injects actual file contents — never placeholders or summaries
- [ ] Includes run metadata: run ID, repo root, task path, current stage, expected transition
- [ ] Context files resolved from task frontmatter `contexts:` field
- [ ] Handles missing context files with a clear error rather than silent omission

## Files

- `src/orchestrator/prompts.py` - create - prompt assembly logic

## Tests

- [ ] Prompt includes role file content verbatim
- [ ] Prompt includes ai-guide.md content
- [ ] Prompt includes task file content
- [ ] Prompt includes context file contents from task frontmatter
- [ ] Missing context file raises a clear error
- [ ] Prompt includes expected transition text for each stage

## Context

Phase 2: Single-Task Execution Engine
