---
stage: plan
tags: [feature, p1]
agent: planner
contexts: [skills/python-core-skills]
---

# Task 1.2: Task scanner and frontmatter parser

## Goal

Build a system that reads .kanban2code/ folders and parses YAML frontmatter into typed TaskSnapshots.

## Definition of Done

- [ ] Scanner reads `.kanban2code/` folders recursively and finds all task `.md` files
- [ ] YAML frontmatter is parsed into `TaskSnapshot` with typed fields (stage, agent, bounces, tags, contexts)
- [ ] Scanner builds a per-project, per-stage index of tasks
- [ ] Tasks in `_archive/`, `_agents/`, `_providers/`, `_context/` are excluded
- [ ] Board state view: JSON object mapping `{project: {stage: [task_id, ...]}}` for Kadee

## Files

- `src/orchestrator/scanner.py` - create - task file discovery and frontmatter parsing
- `src/orchestrator/state.py` - create - board state view builder

## Tests

- [ ] Scanner finds task files in inbox/, projects/*, and nested phase folders
- [ ] Scanner excludes _archive, _agents, _providers, _context
- [ ] Frontmatter parser extracts stage, agent, bounces, tags, contexts correctly
- [ ] Frontmatter parser handles missing optional fields with defaults
- [ ] Board state view produces correct project × stage matrix from sample tasks

## Context

Phase 1: Core Infrastructure
