---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 6: Memory System

This task consolidates all Phase 6 tasks into a single comprehensive task for testing AI capabilities with long tasks.

---

## Task 6.1: Memory system with hot, warm, and cold layers

### Goal

Implement the three-layer operational memory system for context retention.

### Definition of Done

- [ ] Hot layer: current run context (active tasks, in-flight sessions, recent events) — in-memory + state file
- [ ] Warm layer: recent project context (last N completed tasks per project, recent decisions, recent errors) — file-based
- [ ] Cold layer: historical patterns (aggregated stats, common failure modes, model performance) — file-based
- [ ] Memory read API: Kadee can query memory by layer and topic
- [ ] Memory write API: orchestrator appends to warm/cold after run completion
- [ ] Memory is file-based and human-readable (JSON + markdown)

### Files

- `src/orchestrator/memory.py` - create - three-layer memory system

### Tests

- [ ] Hot memory reflects current run state
- [ ] Warm memory stores last N completed tasks per project
- [ ] Cold memory aggregates stats from completed runs
- [ ] Memory read returns correct data by layer and topic
- [ ] Memory files are valid JSON/markdown

### Context

Phase 6: Memory System